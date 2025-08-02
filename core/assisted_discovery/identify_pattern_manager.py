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
    
    def verify_and_confirm_airline(self, unknown_source_xml_content, selected_airlines):
        with st.spinner(":rainbow[Genie is analyzing the API, please wait...]"):
            sections = self.db_utils.list_main_elements(unknown_source_xml_content)
            gap_analysis = {
                "sections": [],
                "matched_airlines": set()
            }

            # Check workspace patterns first
            for section in sections:
                row = self.db_utils.search_in_database(section, selected_airlines)
                if row:
                    section_data = {
                        "sectionName": section,
                        "rules": []
                    }

                    for item in row:
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
            shared_patterns = self._get_shared_patterns_for_identification(unknown_source_xml_content)
            if shared_patterns:
                for pattern_data in shared_patterns:
                    section_data = {
                        "sectionName": pattern_data["xpath"],
                        "rules": [{
                            "airline": "Shared",
                            "apiVersion": "N/A",
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
                        gap_analysis["matched_airlines"].add("Shared")
                    section_data["rules"][0]["reason"] = response_obj_json.get('reason', "")
                    
                    gap_analysis["sections"].append(section_data)

            return gap_analysis

    def _get_shared_patterns_for_identification(self, xml_content):
        """Get shared patterns that might match the XML content"""
        try:
            from core.database.default_patterns_manager import DefaultPatternsManager
            default_patterns_manager = DefaultPatternsManager()
            shared_patterns = default_patterns_manager.get_all_patterns()
            
            # Convert to format expected by identification logic
            pattern_data = []
            for pattern in shared_patterns:
                pattern_data.append({
                    "xpath": pattern.xpath,
                    "description": pattern.description or pattern.name,
                    "prompt": pattern.prompt
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