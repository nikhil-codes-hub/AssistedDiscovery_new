import streamlit as st
import pandas as pd
import os
import sys
import re
import json
from core.assisted_discovery.gap_analysis_manager import GapAnalysisManager
from core.common.ui_utils import render_custom_table
from core.prompts_manager.gap_analysis_prompt_manager import GapAnalysisPromptManager
from core.database.sql_db_utils import SQLDatabaseUtils

class PatternIdentifyManager(GapAnalysisManager, GapAnalysisPromptManager):

    def __init__(self, model_name, db_utils=None):
        super().__init__(model_name)
        self.db_utils = db_utils if db_utils else SQLDatabaseUtils()
    
    def verify_and_confirm_airline(self, unknown_source_xml_content, filter_info):
        with st.spinner(":rainbow[Genie is analyzing the API, please wait...]"):
            sections = self.db_utils.list_main_elements(unknown_source_xml_content)
            gap_analysis = {
                "sections": [],
                "matched_airlines": set()
            }

            # Extract filter criteria
            selected_airlines = None
            selected_versions = None
            if filter_info and isinstance(filter_info, dict):
                selected_airlines = filter_info.get('airlines')
                selected_versions = filter_info.get('versions')
            
            # Check workspace patterns first
            # Get all workspace patterns and check them against XML content
            all_workspace_patterns = self.db_utils.get_all_patterns()
            workspace_pattern_data = []
            
            for pattern in all_workspace_patterns:
                # Handle tuple format: (api_name, api_version, section_name, pattern_description, pattern_prompt)
                if isinstance(pattern, tuple) and len(pattern) >= 5:
                    api_name, api_version, section_name, pattern_description, pattern_prompt = pattern[:5]
                    
                    # Apply airline filter if specified
                    if selected_airlines and api_name not in selected_airlines:
                        continue
                        
                    # Apply version filter if specified  
                    if selected_versions and api_version not in selected_versions:
                        continue
                    
                    workspace_pattern_data.append({
                        "xpath": section_name,
                        "airline": api_name or "Custom",
                        "apiVersion": api_version or "N/A",
                        "verificationRule": pattern_description or "Custom Pattern",
                        "prompt": pattern_prompt
                    })
                else:
                    # Fallback for object-based patterns (if any)
                    pattern_airline = getattr(pattern, 'airline', None) or getattr(pattern, 'api_name', None)
                    if selected_airlines and pattern_airline not in selected_airlines:
                        continue
                        
                    # Apply version filter if specified  
                    pattern_version = getattr(pattern, 'api_version', None) or getattr(pattern, 'version_number', None)
                    if selected_versions and pattern_version not in selected_versions:
                        continue
                    
                    # Check if pattern's xpath/section might be relevant to the XML
                    pattern_xpath = getattr(pattern, 'xpath', None) or getattr(pattern, 'section_name', None)
                    if pattern_xpath:
                        workspace_pattern_data.append({
                            "xpath": pattern_xpath,
                            "airline": pattern_airline or "Custom",
                            "apiVersion": pattern_version or "N/A",
                            "verificationRule": getattr(pattern, 'pattern_description', None) or getattr(pattern, 'description', None) or "Custom Pattern",
                            "prompt": getattr(pattern, 'pattern_prompt', None) or getattr(pattern, 'prompt', None)
                        })
            
            # Process workspace patterns
            for pattern_data in workspace_pattern_data:
                if pattern_data["prompt"]:  # Only process if prompt exists
                    section_data = {
                        "sectionName": pattern_data["xpath"],
                        "rules": [{
                            "airline": pattern_data["airline"],
                            "apiVersion": pattern_data["apiVersion"], 
                            "verificationRule": pattern_data["verificationRule"],
                            "matched": False,
                            "reason": ""
                        }]
                    }
                    
                    # Use pattern prompt for identification
                    search_prompt = pattern_data["prompt"]
                    response_obj_json = self.identify_patterns_in_unknown_source_xml(unknown_source_xml_content, search_prompt)
                    confirmation = response_obj_json.get('confirmation')
                    section_data["rules"][0]["matched"] = confirmation == "YES"
                    if section_data["rules"][0]["matched"]:
                        gap_analysis["matched_airlines"].add(pattern_data["airline"])
                    section_data["rules"][0]["reason"] = response_obj_json.get('reason', "")
                    
                    gap_analysis["sections"].append(section_data)
                else:
                    # Add patterns even without prompts so they show up in results (with appropriate reason)
                    section_data = {
                        "sectionName": pattern_data["xpath"],
                        "rules": [{
                            "airline": pattern_data["airline"],
                            "apiVersion": pattern_data["apiVersion"], 
                            "verificationRule": pattern_data["verificationRule"],
                            "matched": False,
                            "reason": "No validation prompt available for this custom pattern"
                        }]
                    }
                    gap_analysis["sections"].append(section_data)
            
            # Legacy section-based search (keep for backward compatibility)
            for section in sections:
                row = self.db_utils.search_in_database(section, selected_airlines)
                if row:
                    section_data = {
                        "sectionName": section,
                        "rules": []
                    }

                    for item in row:
                        # Apply version filter if specified
                        if selected_versions and item[1] not in selected_versions:
                            continue
                            
                        rule = {
                            "airline": item[0],
                            "apiVersion": item[1],
                            "verificationRule": item[2],
                            "matched": False,
                            "reason": ""
                        }

                        search_prompt = item[3]
                        response_obj_json = self.identify_patterns_in_unknown_source_xml(unknown_source_xml_content, search_prompt)
                        confirmation = response_obj_json.get('confirmation')
                        rule["matched"] = confirmation == "YES"
                        if rule["matched"] == True:
                            gap_analysis["matched_airlines"].add(item[0])
                        rule["reason"] = response_obj_json.get('reason', "")

                        section_data["rules"].append(rule)

                    gap_analysis["sections"].append(section_data)

            # Also check shared patterns from default patterns database
            shared_patterns = self._get_shared_patterns_for_identification(unknown_source_xml_content, selected_airlines, selected_versions)
            if shared_patterns:
                for pattern_data in shared_patterns:
                    section_data = {
                        "sectionName": pattern_data["xpath"],
                        "rules": [{
                            "airline": pattern_data["api"],
                            "apiVersion": pattern_data["api_version"],
                            "verificationRule": pattern_data["description"],
                            "matched": False,
                            "reason": ""
                        }]
                    }
                    
                    # Use pattern prompt for identification
                    search_prompt = pattern_data["prompt"]
                    response_obj_json = self.identify_patterns_in_unknown_source_xml(unknown_source_xml_content, search_prompt)
                    confirmation = response_obj_json.get('confirmation')
                    section_data["rules"][0]["matched"] = confirmation == "YES"
                    if section_data["rules"][0]["matched"]:
                        gap_analysis["matched_airlines"].add(pattern_data["api"])
                    section_data["rules"][0]["reason"] = response_obj_json.get('reason', "")
                    
                    gap_analysis["sections"].append(section_data)

            return gap_analysis

    def _get_shared_patterns_for_identification(self, xml_content, selected_airlines=None, selected_versions=None):
        """Get shared patterns that might match the XML content"""
        try:
            from core.database.default_patterns_manager import DefaultPatternsManager
            default_patterns_manager = DefaultPatternsManager()
            shared_patterns = default_patterns_manager.get_all_patterns()
            
            # Convert to format expected by identification logic
            pattern_data = []
            for pattern in shared_patterns:
                api_name = pattern.api or "Shared"
                api_version = pattern.api_version or "N/A"
                
                # Apply airline filter
                if selected_airlines and api_name not in selected_airlines:
                    continue
                    
                # Apply version filter
                if selected_versions and api_version not in selected_versions:
                    continue
                
                pattern_data.append({
                    "xpath": pattern.xpath,
                    "description": pattern.description or pattern.name,
                    "prompt": pattern.prompt,
                    "api": api_name,
                    "api_version": api_version
                })
            
            return pattern_data
            
        except Exception as e:
            st.error(f"Error loading shared patterns: {e}")
            return []

    def identify_patterns_in_unknown_source_xml(self, unknown_source_xml_content, search_prompt):
        self.load_prompts_for_pattern_identification(unknown_source_xml_content, search_prompt)
        response = self._initiate_conversation()
        response_obj = re.sub(r'[\x00-\x1F\x7F]', '', response)
        response_obj_json = json.loads(response_obj)
        return response_obj_json

    def display_api_analysis(self, data):
        sections = data.get('sections', [])
        matched_airlines = data.get('matched_airlines', [])
        rows = []
        matched_airline_versions = set()
        
        for section in sections:
            section_name = section.get('sectionName')
            rules = section.get('rules', [])
            for rule in rules:
                airline = rule.get('airline', 'Unknown')
                api_version = rule.get('apiVersion', 'N/A')
                
                # Create airline+version combination for matched airlines
                if rule.get('matched'):
                    if api_version and api_version != 'N/A':
                        matched_airline_versions.add(f"{airline}{api_version}")
                    else:
                        matched_airline_versions.add(airline)
                
                rows.append({
                    'Airline': airline,
                    'API Version': api_version,
                    'Section': section_name,
                    'Validation Rule': rule.get('verificationRule'),
                    'Verified': 'Yes' if rule.get('matched') else 'No',
                    'Reason': rule.get('reason')
                })
        df = pd.DataFrame(rows)
        
        # Sort to show verified "Yes" entries first
        if not df.empty:
            df = df.sort_values('Verified', ascending=False)

        if df.empty:
            st.markdown("""
            <div style="padding: 1.5rem; background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(248, 113, 113, 0.1));
                        border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.3); margin: 1rem 0;">
                <h4 style="color: #dc2626; margin: 0 0 0.5rem 0;">❌ No Validation Rules Found</h4>
                <p style="color: #7f1d1d; margin: 0 0 1rem 0;">
                    No patterns exist in the current workspace to identify against your XML file.
                </p>
                <div style="background: rgba(239, 68, 68, 0.05); padding: 1rem; border-radius: 6px; margin-top: 1rem;">
                    <p style="color: #991b1b; margin: 0; font-weight: 500;">💡 To use pattern identification:</p>
                    <ol style="color: #7f1d1d; margin: 0.5rem 0 0 1.2rem; padding: 0;">
                        <li>Go to the <strong>Discovery page</strong></li>
                        <li>Extract patterns from XML files</li>
                        <li>Save patterns to your workspace</li>
                        <li>Return here to identify patterns in new XML files</li>
                    </ol>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            df = df.reset_index(drop=True)
            long_text_cols = ['Validation Rule', 'Reason']
            from core.common.css_utils import get_css_path
            css_path = get_css_path()
            render_custom_table(df, long_text_cols, css_path)
        
        st.subheader("Matched Airline(s):")
        if matched_airline_versions:
            st.markdown(
                f'<span style="background-color:#ffe066; color:#222; font-weight:bold; padding:4px 8px; border-radius:5px;">'
                + ", ".join(sorted(matched_airline_versions)) + '</span>', unsafe_allow_html=True
            )
        else:
            st.markdown(":red[No airline(s) matched.]", unsafe_allow_html=True)
    
    def generate_chatbot_response(self, question, analysis_results, xml_content):
        """
        Generate intelligent chatbot responses based on the analysis results and user questions.
        """
        try:
            # Prepare context for LLM-based response generation
            context = {
                "user_question": question,
                "analysis_results": str(analysis_results)[:1500] if analysis_results else "No analysis results available",
                "xml_snippet": xml_content[:800] if xml_content else "No XML content available"
            }
            
            # Generate a simple context-aware response without using the complex LLM chain
            return self._generate_contextual_response(question, analysis_results, xml_content)
                
        except Exception as e:
            # Return a helpful fallback response
            return f"I apologize, but I encountered an issue processing your question: {str(e)}. Please try asking a more specific question about the analysis results, such as 'Which airlines were identified?' or 'What patterns matched successfully?'"
    
    def _generate_contextual_response(self, question, analysis_results, xml_content):
        """
        Generate a contextual response based on question analysis and available data.
        """
        question_lower = question.lower()
        
        # Convert analysis results to string for processing
        results_str = str(analysis_results) if analysis_results else ""
        xml_str = str(xml_content) if xml_content else ""
        
        # Airline-related questions
        if any(word in question_lower for word in ['airline', 'carrier', 'airlines', 'matched']):
            return self._analyze_airlines_in_context(results_str, xml_str)
        
        # Pattern-related questions  
        elif any(word in question_lower for word in ['pattern', 'patterns', 'found', 'identified']):
            return self._analyze_patterns_in_context(results_str, analysis_results)
        
        # Summary questions
        elif any(word in question_lower for word in ['summary', 'overview', 'results', 'what happened']):
            return self._generate_summary_from_context(results_str, analysis_results)
        
        # Data quality questions
        elif any(word in question_lower for word in ['quality', 'complete', 'missing', 'data', 'good', 'bad']):
            return self._analyze_data_quality_from_context(results_str, xml_str)
        
        # Confidence/accuracy questions
        elif any(word in question_lower for word in ['confidence', 'accurate', 'sure', 'certain']):
            return self._analyze_confidence_from_context(results_str, analysis_results)
        
        # Count/number questions
        elif any(word in question_lower for word in ['how many', 'count', 'number', 'total']):
            return self._analyze_counts_from_context(results_str, analysis_results)
        
        # Default contextual response
        else:
            return f"""I understand you're asking: "{question}"

Based on the analysis results available, I can help you with information about:

🏢 **Airlines & Carriers**: Which airlines were identified in your XML
📊 **Pattern Matches**: What patterns were successfully matched  
📈 **Analysis Summary**: Overview of the identification results
🔍 **Data Quality**: Assessment of completeness and accuracy
📋 **Match Counts**: Number of patterns and matches found

Could you please ask a more specific question about one of these areas? For example:
- "Which airlines were found?"
- "How many patterns matched?"
- "What's the overall analysis summary?"
"""

    def _analyze_airlines_in_context(self, results_str, xml_str):
        """Analyze airline information from the context"""
        airlines_found = []
        airline_codes = []
        
        # Common airline patterns
        airline_patterns = {
            'american': ['AA', 'American Airlines'],
            'delta': ['DL', 'Delta Air Lines'], 
            'united': ['UA', 'United Airlines'],
            'southwest': ['WN', 'Southwest Airlines'],
            'jetblue': ['B6', 'JetBlue Airways'],
            'alaska': ['AS', 'Alaska Airlines'],
            'spirit': ['NK', 'Spirit Airlines'],
            'frontier': ['F9', 'Frontier Airlines'],
            'lufthansa': ['LH', 'Lufthansa'],
            'british': ['BA', 'British Airways'],
            'air france': ['AF', 'Air France'],
            'klm': ['KL', 'KLM']
        }
        
        # Search in results and XML
        search_text = (results_str + " " + xml_str).lower()
        
        for airline, codes in airline_patterns.items():
            if airline in search_text:
                airlines_found.append(airline.title())
            for code in codes:
                if code.lower() in search_text:
                    airline_codes.append(code)
        
        if airlines_found or airline_codes:
            response = "🏢 **Airlines Identified:**\n\n"
            if airlines_found:
                response += f"**Airline Names Found:** {', '.join(set(airlines_found))}\n"
            if airline_codes:
                response += f"**Airline Codes Found:** {', '.join(set(airline_codes))}\n"
            response += "\nThese airlines were detected in your XML data through pattern matching."
            return response
        else:
            return "🔍 **Airline Analysis:** I couldn't identify specific airline names or codes in the analysis results. This could mean:\n\n• The XML contains airline data in a different format\n• The patterns focused on structural elements rather than airline identifiers\n• The airline information might be in abbreviated or coded form\n\nYou might want to check the raw XML data for airline references."

    def _analyze_patterns_in_context(self, results_str, analysis_results):
        """Analyze pattern information from the context"""
        try:
            if isinstance(analysis_results, dict):
                sections = analysis_results.get('sections', [])
                total_patterns = len(sections)
                matched_patterns = sum(1 for section in sections 
                                     for rule in section.get('rules', []) 
                                     if rule.get('matched', False))
                
                return f"""📊 **Pattern Analysis:**

**Total Sections Analyzed:** {total_patterns}
**Successful Matches:** {matched_patterns}
**Match Rate:** {(matched_patterns/max(total_patterns, 1)*100):.1f}%

The analysis processed your XML against the available pattern library and identified {matched_patterns} successful pattern matches. These patterns represent different structural elements and data points that align with your saved patterns."""
            
            elif results_str:
                # Count mentions of success/match indicators
                match_indicators = ['matched', 'found', 'identified', 'success']
                match_count = sum(results_str.lower().count(indicator) for indicator in match_indicators)
                
                return f"""📊 **Pattern Analysis:**

The pattern identification process completed with {match_count} match indicators in the results.

**Analysis Summary:**
{results_str[:300]}{'...' if len(results_str) > 300 else ''}

The patterns represent structural elements in your XML that were successfully recognized by the system."""
            
            else:
                return "📊 **Pattern Analysis:** The pattern identification process completed, but detailed pattern information isn't available in the current results format."
                
        except Exception as e:
            return f"📊 **Pattern Analysis:** I encountered an issue analyzing the pattern details: {str(e)}"

    def _generate_summary_from_context(self, results_str, analysis_results):
        """Generate a summary from the available context"""
        return f"""📋 **Analysis Summary:**

**Process:** Your XML file was analyzed against the pattern library in your workspace.

**Results Overview:**
{results_str[:400] if results_str else 'Analysis completed successfully'}{'...' if len(results_str) > 400 else ''}

**Key Points:**
• Pattern identification process completed
• XML structure was analyzed for known patterns  
• Results show matches against your saved pattern library
• You can use these results to understand your data structure

**Next Steps:**
• Review the detailed results above
• Check which specific patterns matched
• Consider adding new patterns if coverage is incomplete"""

    def _analyze_data_quality_from_context(self, results_str, xml_str):
        """Analyze data quality from the available context"""
        quality_score = 0
        quality_notes = []
        
        # Check XML size
        xml_size = len(xml_str) if xml_str else 0
        if xml_size > 1000:
            quality_score += 2
            quality_notes.append("✅ Good data volume")
        elif xml_size > 500:
            quality_score += 1  
            quality_notes.append("⚠️ Moderate data volume")
        else:
            quality_notes.append("❌ Limited data volume")
        
        # Check for key XML elements
        if xml_str and any(tag in xml_str.lower() for tag in ['<flight', '<passenger', '<booking', '<fare']):
            quality_score += 2
            quality_notes.append("✅ Contains key business elements")
        
        # Check results completeness
        if results_str and len(results_str) > 100:
            quality_score += 1
            quality_notes.append("✅ Comprehensive analysis results")
        
        quality_level = "High" if quality_score >= 4 else "Medium" if quality_score >= 2 else "Basic"
        
        return f"""📈 **Data Quality Assessment:**

**Overall Quality:** {quality_level}

**Quality Indicators:**
{chr(10).join(quality_notes)}

**Analysis Completeness:**
The pattern matching process {'provided detailed results' if results_str else 'completed successfully'} based on your XML structure and available patterns.

**Recommendations:**
• Ensure XML follows standard formats for better recognition
• Consider adding more patterns to improve coverage
• Review unmatched sections for new pattern opportunities"""

    def _analyze_confidence_from_context(self, results_str, analysis_results):
        """Analyze confidence levels from the context"""
        return f"""🎯 **Confidence Analysis:**

**Pattern Matching Confidence:** The analysis used your saved patterns as reference templates, providing high confidence for exact matches.

**Result Reliability:** {'High - detailed analysis results available' if results_str else 'Medium - basic results available'}

**Factors Affecting Confidence:**
• Quality and completeness of your pattern library
• How well your XML structure matches saved patterns  
• Consistency of data formats in your XML

**Improving Confidence:**
• Add more representative patterns to your library
• Ensure XML follows consistent formatting
• Review and validate pattern matches manually"""

    def _analyze_counts_from_context(self, results_str, analysis_results):
        """Analyze counts and numbers from the context"""
        try:
            if isinstance(analysis_results, dict):
                sections = analysis_results.get('sections', [])
                total_sections = len(sections)
                total_rules = sum(len(section.get('rules', [])) for section in sections)
                matched_rules = sum(1 for section in sections 
                                  for rule in section.get('rules', []) 
                                  if rule.get('matched', False))
                
                return f"""📊 **Count Analysis:**

**XML Sections Analyzed:** {total_sections}
**Total Pattern Rules Applied:** {total_rules}  
**Successful Matches:** {matched_rules}
**Unmatched Patterns:** {total_rules - matched_rules}

**Match Rate:** {(matched_rules/max(total_rules, 1)*100):.1f}%

This gives you a quantitative view of how well your XML aligns with your saved patterns."""
            
            else:
                # Try to extract numbers from results string
                import re
                numbers = re.findall(r'\b\d+\b', results_str) if results_str else []
                
                return f"""📊 **Count Analysis:**

Based on the analysis results, I found {len(numbers)} numeric values: {', '.join(numbers[:10])}{'...' if len(numbers) > 10 else ''}

The exact count details depend on the specific analysis results format. For more precise counts, you might want to ask about specific elements like "How many flight segments?" or "How many passengers?"."""
                
        except Exception as e:
            return f"📊 **Count Analysis:** I encountered an issue analyzing the counts: {str(e)}"
    
    def load_chatbot_prompts(self, context):
        """
        Load prompts for chatbot conversation based on the provided context.
        """
        system_prompt = f"""You are Genie, an AI assistant specializing in XML pattern analysis and airline data processing. 
        You are helping a user understand their XML pattern identification results.

        CONTEXT:
        - User Question: {context['user_question']}
        - Analysis Results: {context['analysis_results']}
        - XML Sample: {context['xml_snippet']}

        INSTRUCTIONS:
        1. Answer the user's question directly and concisely
        2. Use the analysis results to provide specific information
        3. If asked about airlines, look for airline codes, names, or carrier information in the results
        4. If asked about patterns, explain which patterns were matched and their significance
        5. Provide actionable insights when possible
        6. Keep responses friendly but professional
        7. If you cannot find specific information, acknowledge this and suggest alternatives

        RESPONSE FORMAT:
        Provide a clear, helpful response that directly addresses the user's question. Use emojis sparingly for visual appeal but focus on informative content.
        """
        
        user_prompt = f"Based on the XML pattern analysis results provided, please answer this question: {context['user_question']}"
        
        # Set the conversation context
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]