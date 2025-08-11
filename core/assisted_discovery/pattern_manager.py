import streamlit as st
from lxml import etree
import json
from datetime import datetime
from streamlit_tree_select import tree_select
from core.assisted_discovery.gap_analysis_manager import GapAnalysisManager
from core.prompts_manager.gap_analysis_prompt_manager import GapAnalysisPromptManager
from .xml_tree_helper import XMLTreeHelper
import pandas as pd
from core.common.ui_utils import render_custom_table
from core.common.logging_manager import get_logger, log_user_action, log_error, log_performance, PerformanceLogger
from core.database.default_patterns_manager import DefaultPatternsManager


class PatternManager(GapAnalysisManager, GapAnalysisPromptManager):

    def __init__(self, model_name):
        super().__init__(model_name)
        self.logger = get_logger("pattern_manager")
        self.default_patterns_manager = DefaultPatternsManager()
        
    def extract_patterns(self, uploaded_file):
        """
        Enhanced main method to extract patterns from the uploaded XML file with better UX.
        """
        self.logger.info("Starting pattern extraction")
        
        # Handle both string and UploadedFile inputs
        if hasattr(uploaded_file, 'size'):
            # It's an UploadedFile object
            file_size = uploaded_file.size
            log_user_action("pattern_extraction_start", f"XML file size: {file_size} bytes")
        else:
            # It's a string
            log_user_action("pattern_extraction_start", f"XML length: {len(uploaded_file)} characters")
        
        # Show the enhanced XML tree interface
        with PerformanceLogger("xml_tree_parsing"):
            xml_content_map = self.show_xml_as_tree(uploaded_file)
        
        # Pattern extraction section
        if xml_content_map:
            
            # Enhanced controls layout with better visual hierarchy
            extract_col1, extract_col2 = st.columns([3, 1])
            
            with extract_col1:
                # Show readiness status with enhanced styling
                node_count = len(xml_content_map)
                if node_count > 0:
                    st.success("✅ Ready to extract patterns (with insights)")
                else:
                    st.warning("⚠️ No nodes selected for extraction")
                
            # Insights are now automatically included
            include_insights = True
            
            # Enhanced extraction button with modern styling
            extract_button_col1, extract_button_col2 = st.columns([2, 1])
            
            with extract_button_col1:
                extract_clicked = st.button(
                    "Extract Patterns", 
                    key="submit_button_extract",
                    disabled=(node_count == 0),
                    use_container_width=True,
                    help="Begin AI-powered pattern extraction from selected XML nodes",
                    type="primary"
                )
            
            with extract_button_col2:
                if extract_clicked:
                    st.success("Processing started!")
            
            # Process extraction with enhanced progress tracking
            if extract_clicked and node_count > 0:
                with st.status("🔄 **Processing Pattern Extraction...**", expanded=True) as status:
                    # Progress tracking with visual feedback
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    selected_nodes_map = {}
                    for tag, content in xml_content_map.items():
                        selected_nodes_map[tag] = content
                    
                    progress_bar.progress(20)
                    status_text.text("📊 Preparing selected XML nodes...")
                    
                    insights = None
                    if include_insights:
                        if getattr(st.session_state, "insights", None) is None:
                            progress_bar.progress(40)
                            status_text.text("🧠 Genie is analyzing node relationships and patterns...")
                            insights = self._extract_insights(selected_nodes_map)
                        else:
                            progress_bar.progress(40)
                            status_text.text("🧠 Using existing insights...")
                            insights = st.session_state.insights
                    
                    progress_bar.progress(70)
                    status_text.text("🤖 Generating patterns with Genie...")
                    response = self.generate_prompt_from_xml_chunk(selected_nodes_map, insights)
                    reasoning_log = response.get('reasoning_log', '') if response else ''
                    patterns = response.get('patterns', []) if response else []

                    progress_bar.progress(90)
                    # Only update session state if patterns are extracted
                    if patterns:
                        if 'pattern_responses' not in st.session_state:
                            st.session_state.pattern_responses = {}
                        for pattern in patterns:
                            pattern_path = pattern["pattern"]["path"]
                            st.session_state.pattern_responses[pattern_path] = pattern["pattern"]
                        st.session_state.pattern_reasoning_log = reasoning_log
                        
                        progress_bar.progress(100)
                        status_text.text(f"✅ Successfully extracted {len(patterns)} patterns!")
                        status.update(label="✅ **Pattern Extraction Complete!**", state="complete")
                        
                        # Success animation
                        st.success(f"🎉 **Extraction Complete!** Found {len(patterns)} high-quality patterns ready for analysis.")
                    else:
                        progress_bar.progress(100)
                        status_text.text("⚠️ No patterns were extracted.")
                        status.update(label="⚠️ **Pattern Extraction Failed**", state="error")
                        st.warning("⚠️ No patterns were extracted. Try different nodes or check your XML structure.")

        
        # Always display patterns if present with enhanced styling
        if 'pattern_responses' in st.session_state and st.session_state.pattern_responses:
            st.markdown("---")
            # Enhanced patterns section header
            self.display_patterns()
  

    def _get_chunk_method(self):
        """
        Get the chunking method and decode the uploaded XML file.
        """
        chunk_method = st.radio(
            "Please select how you would like to chunk the XML.",
            ["I will select tags by myself 🛒", "Let Genie decide! 🤖"]
        )
        return chunk_method

    def _store_patterns(self, patterns):
        """
        Store the extracted patterns in the session state.
        """
        reasoning_log = patterns.get('reasoning_log', '')
        pattern_list = patterns.get('patterns', [])
        
        for pattern in pattern_list:
            pattern_path = pattern["pattern"]["path"]
            st.session_state.pattern_responses[pattern_path] = {
                'pattern': pattern["pattern"],
                'reasoning_log': reasoning_log
            }

    def _add_patterns_manually(self, xml_text):
        """
        Allow the user to add patterns manually.
        """
        try:
            # Manual pattern addition interface (no expander - called from within expander)
            st.markdown("### ➕ **Add Custom Patterns**")
            st.markdown("Manually add specific patterns to complement the automatically extracted ones.")

            # First row: xml_chunk and tag
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Pattern name", key="name_input")
            with col2:
                tag = st.text_input("Tag name", key="tag_input")

            # Second row: name and description
            col3, col4 = st.columns(2)
            with col3:
                xml_chunk = st.text_area("XML chunk", height=150, key="xml_chunk")
            with col4:
                description = st.text_area("Pattern description", height=150, key="description_input")

            if xml_chunk == "" or tag == "" or name == "" or description == "":
                st.warning("Please fill all the fields to add a pattern.")
                return

            manual_add_pattern_checkbox = st.checkbox("I will provide the prompt")

            # Initialize final_prompt in session state
            if "final_prompt" not in st.session_state:
                st.session_state.final_prompt = None

            if manual_add_pattern_checkbox:
                prompt_input = st.text_area("Enter the prompt", height=100)
                st.session_state.final_prompt = prompt_input
            else:
                if st.button("Generate Prompt", key="generate_manual_prompt"):
                    self._generate_prompt_for_manual_input(xml_chunk, tag, name, description)

            if st.button("Add Pattern", key="add_manual_pattern"):
                self._add_pattern_to_session(tag, name, description)

            self.display_patterns()
        except Exception as e:
            st.error(f"An error occurred while adding patterns manually: {e}")
            raise e

    def _generate_prompt_for_manual_input(self, xml_chunk, tag, name, description):
        """
        Generate a prompt for manual input using the LLM.
        """
        with st.spinner("Generating prompt, please wait!!"):
            is_valid_xml, prompt_from_llm = self.generate_prompt_from_manual_input(xml_chunk, tag, name, description)
            if is_valid_xml:
                st.session_state.final_prompt = prompt_from_llm
                st.info("Prompt generated successfully!")
                st.markdown(f"Prompt: :blue-background[{st.session_state.final_prompt}]")
            else:
                st.warning("Failed to generate prompt, please try again!")

    def _add_pattern_to_session(self, tag, name, description):
        """
        Add a manually created pattern to the session state.
        """
        if st.session_state.final_prompt is None:
            st.warning("No prompt available. Please generate or provide a prompt before adding the pattern.")
        else:
            st.session_state.pattern_responses[tag] = [name, description, st.session_state.final_prompt, False]
            st.success(f"Pattern for tag '{tag}' added successfully.")
            # Reset final_prompt after adding the pattern
            st.session_state.final_prompt = None
        
    def generate_prompt_from_xml_chunk(self, content, insights=None):
        """
        Generate patterns from XML content with optional insights.
        
        Args:
            content (str): The XML content
            insights (dict, optional): Insights about the XML structure and relationships
        """
        self.load_prompts_for_extracting_patterns(content, insights)
        response = self._initiate_conversation()
        try:
            # Try to parse as JSON if it's already in JSON format
            response_json = json.loads(response)
            return response_json
        except json.JSONDecodeError:
            # If not JSON, assume it's a string response and try to parse it
            # This handles cases where the LLM might return a stringified JSON
            if response.startswith('{') and response.endswith('}'):
                response_json = json.loads(response)
                return response_json
            
            # If still not JSON, return None
            st.warning("Could not parse pattern extraction response as JSON. Using default behavior.")
            return None

    def _extract_insights(self, selected_nodes_map):
        """
        Extract insights for the given selected_nodes_map (dict of path to XML string).
        Handles prompt loading, conversation, response parsing, and updates session state.
        Returns the insights dict or None if parsing fails.
        """
        self.load_prompts_for_insights(selected_nodes_map)
        response = self._initiate_conversation()
        try:
            response_json = json.loads(response)
            insights = response_json.get("insights")
            st.session_state.insights = insights
            return insights
        except json.JSONDecodeError:
            if response.startswith('{') and response.endswith('}'):
                response_json = json.loads(response)
                insights = response_json.get("insights")
                st.session_state.insights = insights
                return insights
            st.warning("Could not get insights. Please try again.")
            return None
    
    def generate_prompt_from_manual_input(self, xml_chunk, tag, name, description):
        conversation_params = {
                "xml_chunk": xml_chunk,
                "tag": tag,
                "name": name,
                "description": description,
        }
        self.load_prompts_for_manual_addition(conversation_params)
        response = self._initiate_conversation()
        try:
            # Try to parse as JSON if it's already in JSON format
            response_json = json.loads(response)
            is_valid_xml = response_json.get("valid_xml")
            prompt = response_json.get("generated_prompt")
            return is_valid_xml, prompt
        except json.JSONDecodeError:
            # If not JSON, assume it's a string response and try to parse it
            # This handles cases where the LLM might return a stringified JSON
            if response.startswith('{') and response.endswith('}'):
                response_json = json.loads(response)
                is_valid_xml = response_json.get("valid_xml")
                prompt = response_json.get("generated_prompt")
                return is_valid_xml, prompt
            
            # If still not JSON, return None
            st.warning("Could not parse manual input response as JSON. Using default behavior.")
            return None, None
        return is_valid_xml, prompt

    def show_xml_as_tree(self, uploaded_file):
        selected_nodes_map = {}
        if uploaded_file:
            try:
                # Try to parse the XML with proper error handling
                xml_tree = etree.parse(uploaded_file)
                root = xml_tree.getroot()
            except etree.XMLSyntaxError as e:
                st.error(f"❌ **XML Parsing Error**: {str(e)}")
                st.markdown("""
                **Common XML issues and solutions:**
                
                🔧 **Entity Reference Error** (like yours):
                - Look for unescaped `&` characters that should be `&amp;`
                - Check for incomplete entity references like `&` without a name
                
                🔧 **How to fix**:
                1. Open your XML file in a text editor
                2. Go to line 250, column 85 (mentioned in the error)
                3. Look for `&` characters that aren't part of proper entities
                4. Replace `&` with `&amp;` if it should be a literal ampersand
                5. Or complete the entity reference (e.g., `&nbsp;`, `&lt;`, `&gt;`)
                
                🔧 **Quick Fix**: Use an XML validator or editor to identify and fix syntax issues
                """)
                return {}
            except Exception as e:
                st.error(f"❌ **File Processing Error**: {str(e)}")
                st.info("💡 Please ensure you've uploaded a valid XML file")
                return {}
            
            # If parsing succeeded, continue with tree processing
            tree_data = [XMLTreeHelper.xml_to_tree(root)]

            # Enhanced tree layout with modern styling
            
            col1, col2 = st.columns([1, 2], gap="medium")
            with col1:
                # Tree selection panel with enhanced styling
                with st.container():
                    st.info("💡 **Best Practice:** Select up to 5 nodes for optimal pattern extraction")
                    
                    # Enhanced tree with custom styling
                    selected = tree_select(tree_data)
                    
                    # Selection status and insights button
                    if selected and 'checked' in selected:
                        checked_paths = selected['checked']
                        
                        # Apply the same filtering logic used for extraction
                        checked_paths_sorted = sorted(checked_paths, key=len)
                        filtered_paths = []
                        for path in checked_paths_sorted:
                            if not any(path.startswith(parent + '/') for parent in filtered_paths):
                                filtered_paths.append(path)
                                                
                        st.metric("Selected", len(filtered_paths), "nodes")
                        # Don't automatically extract insights - wait for manual extraction
                        get_insights_button = False
                    else:
                        st.info("👆 **Select XML nodes** from the tree above to begin analysis")
                        get_insights_button = False

            with col2:
                # XML preview panel with enhanced styling
                st.markdown("#### 📄 Selected Node Preview")
                
                if selected and 'checked' in selected:
                    # Filter out children if parent is selected
                    checked_paths = selected['checked']
                    checked_paths = sorted(checked_paths, key=len)  # shortest (highest) first
                    filtered_paths = []
                    for path in checked_paths:
                        if not any(path.startswith(parent + '/') for parent in filtered_paths):
                            filtered_paths.append(path)

                    # Enhanced XML display
                    for i, path in enumerate(filtered_paths):
                        elem = XMLTreeHelper.find_elem_by_path(root, path)
                        if elem is not None:
                            xml_str = etree.tostring(elem, pretty_print=True, encoding='unicode')
                            selected_nodes_map[path] = xml_str
                            
                            # Enhanced expander with better styling
                            with st.expander(f"📄 **Node {i+1}:** `{path}`", expanded=False):
                                # Add node metadata
                                node_info_col1, node_info_col2 = st.columns(2)
                                with node_info_col1:
                                    st.metric("Attributes", len(elem.attrib))
                                with node_info_col2:
                                    st.metric("Children", len(list(elem)))
                                
                                # XML content with syntax highlighting
                                st.code(xml_str, language='xml', line_numbers=True)
                        else:
                            st.error(f"❌ Element not found for path: `{path}`")
                    
                    # Display insights with enhanced styling (if previously generated)
                    if st.session_state.get('insights'):
                        st.markdown("---")
                        st.markdown("#### 🧠 Generated Insights")
                        self.reveal_insights()
                
                else:
                    # Enhanced empty state
                    st.markdown("""
                    <div style="text-align: center; padding: 2rem; color: #6b7280;">
                        <h3 style="color: #9ca3af;">🌱 Ready for Analysis</h3>
                        <p>Select XML nodes from the tree on the left to see their content and structure here.</p>
                    </div>
                    """, unsafe_allow_html=True)

        return selected_nodes_map

    def reveal_insights(self):
        """Enhanced insights display with modern styling and better organization"""
        
        if "error" in st.session_state.insights:
            st.error(f"🚨 **Analysis Error:** {st.session_state.insights['error']}")
            return
            
        if "relations" not in st.session_state.insights:
            st.info("🔍 **Analysis Complete:** No structured insights found in the response.")
            return
            
        relations = st.session_state.insights["relations"]
        
        # Relationships Section
        with st.container():
            if relations:
                st.markdown("##### 🔗 **Node Relationships**")
                
                # Group relationships by type for better organization
                relationship_types = {}
                for rel in relations:
                    rel_type = rel.get('relation', 'General').title()
                    if rel_type not in relationship_types:
                        relationship_types[rel_type] = []
                    relationship_types[rel_type].append(rel)
                
                # Display relationships grouped by type
                for rel_type, type_relations in relationship_types.items():
                    with st.expander(f"**{rel_type} Relationships** ({len(type_relations)})", expanded=True):
                        for rel in type_relations:
                            node1 = rel.get('node1', 'Unknown')
                            node2 = rel.get('node2', 'Unknown')
                            details = rel.get('details', 'No additional details')
                            
                            # Enhanced relationship display
                            st.markdown(f"""
                            <div style="padding: 0.75rem; margin: 0.5rem 0; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1)); border-radius: 8px; border-left: 4px solid #10b981;">
                                <strong style="color: #065f46;">Connection:</strong> <code>{node1}</code> ↔ <code>{node2}</code><br>
                                <strong style="color: #065f46;">Details:</strong> {details}
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("🔍 **No relationships found** between the selected nodes.")
        
        
    def display_patterns(self):
        try:
            # Always display the pattern library
            self.display_pattern_library()

        except Exception as e:
            st.error(f"An error occurred while displaying patterns: {e}")
            raise e
    
    def display_pattern_library(self):
        """Display the complete pattern library including default and user patterns"""
        try:
            # Get all default patterns
            default_patterns = self.default_patterns_manager.get_all_patterns()
            self.logger.info(f"Loaded {len(default_patterns)} default patterns for display")
            
            # Get extracted patterns from session
            extracted_patterns = getattr(st.session_state, 'pattern_responses', {})
            self.logger.info(f"Found {len(extracted_patterns)} extracted patterns in session")
            
            st.markdown("---")
            # Enhanced pattern library header
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; margin: 1rem 0;
                        background: linear-gradient(135deg, rgba(147, 51, 234, 0.1), rgba(168, 85, 247, 0.1));
                        border-radius: 12px; border: 1px solid rgba(147, 51, 234, 0.3);">
                <h3 style="margin: 0; color: #6b21a8;">📚 Extracted Patterns</h3>
                <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.95rem;">Patterns extracted from your current session</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Only show extracted patterns (remove default patterns library)
            self._display_extracted_patterns_tab(extracted_patterns)
                
        except Exception as e:
            st.error(f"Error displaying pattern library: {e}")
            self.logger.error(f"Error in display_pattern_library: {e}")
    
    def _display_default_patterns_tab(self, default_patterns, context="default"):
        """Display default patterns with management options"""
        if not default_patterns:
            st.info("📝 **No default patterns currently available.**")
            st.markdown("""
            This could happen if:
            - All default patterns were deleted
            - No patterns have been added to the library yet
            """)
            
            # Offer to restore initial patterns
            if st.button("🔄 Restore Initial Default Patterns", key=f"restore_initial_patterns_{context}"):
                try:
                    # Force recreation of default patterns
                    self.default_patterns_manager._create_initial_patterns()
                    st.success("✅ Initial default patterns restored!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to reinitialize patterns: {e}")
            return
        
        # Group patterns by category
        categories = {}
        for pattern in default_patterns:
            if pattern.category not in categories:
                categories[pattern.category] = []
            categories[pattern.category].append(pattern)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Default Patterns", len(default_patterns), "available")
        with col2:
            st.metric("📁 Categories", len(categories), "organized")
        with col3:
            active_patterns = len([p for p in default_patterns if p.is_active])
            st.metric("✅ Active", active_patterns, "patterns")
        with col4:
            st.metric("🏷️ Latest Category", list(categories.keys())[-1] if categories else "None", "")
        
        # Category selection and display
        if len(categories) > 1:
            selected_category = st.selectbox("🏷️ Filter by Category", ["All"] + list(categories.keys()))
            if selected_category == "All":
                patterns_to_show = default_patterns
            else:
                patterns_to_show = categories[selected_category]
        else:
            patterns_to_show = default_patterns
        
        # Display patterns with management options
        for pattern in patterns_to_show:
            with st.expander(f"**{pattern.name}** (`{pattern.category}`) - `{pattern.xpath}`"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Description:** {pattern.description}")
                    st.markdown(f"**XPATH:** `{pattern.xpath}`")
                    st.markdown(f"**Category:** {pattern.category}")
                    st.markdown(f"**Example:**")
                    st.code(pattern.example, language='xml')
                    st.markdown(f"**Prompt:** {pattern.prompt}")
                
                with col2:
                    st.markdown("**Actions:**")
                    
                    if st.button(f"🎯 Use Pattern", key=f"use_default_{pattern.pattern_id}"):
                        self._add_default_patterns_to_session([pattern])
                        st.success(f"Added '{pattern.name}' to current session!")
                        st.rerun()
                    
                    # Initialize deletion confirmation state
                    if 'default_pattern_delete_confirm' not in st.session_state:
                        st.session_state.default_pattern_delete_confirm = {}
                    
                    pattern_confirm_key = f"default_{pattern.pattern_id}"
                    
                    if pattern_confirm_key not in st.session_state.default_pattern_delete_confirm:
                        # Show delete button
                        if st.button(f"🗑️ Delete", key=f"delete_default_{pattern.pattern_id}", type="secondary"):
                            st.session_state.default_pattern_delete_confirm[pattern_confirm_key] = True
                            st.rerun()
                    else:
                        # Show confirm button
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"⚠️ Confirm Delete", key=f"confirm_delete_{pattern.pattern_id}", type="secondary"):
                                if self.default_patterns_manager.delete_pattern(pattern.pattern_id):
                                    st.success(f"Deleted pattern '{pattern.name}'")
                                    # Clear confirmation state
                                    del st.session_state.default_pattern_delete_confirm[pattern_confirm_key]
                                    st.rerun()
                                else:
                                    st.error("Failed to delete pattern")
                        with col2:
                            if st.button(f"❌ Cancel", key=f"cancel_delete_{pattern.pattern_id}", type="secondary"):
                                # Clear confirmation state
                                del st.session_state.default_pattern_delete_confirm[pattern_confirm_key]
                                st.rerun()
        
        # Bulk actions
        if patterns_to_show:
            st.markdown("---")
            bulk_col1, bulk_col2 = st.columns(2)
            
            with bulk_col1:
                if st.button(f"➕ Add All to Workspace", key="add_all_default"):
                    self._add_default_patterns_to_session(patterns_to_show)
                    st.success(f"Added {len(patterns_to_show)} patterns to session!")
                    st.rerun()
            
            with bulk_col2:
                st.info("💡 **Tip**: Use the management tabs to import/export patterns")
    
    def _display_extracted_patterns_tab(self, extracted_patterns):
        """Display extracted patterns from current session"""
        if not extracted_patterns:
            st.info("No patterns extracted in current session. Upload XML and extract patterns first.")
            return
        
        self._display_extracted_patterns("extract")
    
    def _display_all_patterns_tab(self, default_patterns, extracted_patterns):
        """Display combined view of all patterns"""
        total_patterns = len(default_patterns) + len(extracted_patterns)
        
        if total_patterns == 0:
            st.info("No patterns available. Add default patterns or extract from XML.")
            return
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Patterns", total_patterns, "combined")
        with col2:
            st.metric("📚 Default", len(default_patterns), "patterns")
        with col3:
            st.metric("🔬 Extracted", len(extracted_patterns), "patterns")
        with col4:
            st.metric("🎯 Ready to Use", total_patterns, "patterns")
        
        # Combined display
        all_data = []
        
        # Add default patterns
        for pattern in default_patterns:
            all_data.append([
                pattern.name,
                pattern.xpath,
                pattern.description,
                pattern.example[:100] + "..." if len(pattern.example) > 100 else pattern.example,
                pattern.category,
                "Default"
            ])
        
        # Add extracted patterns
        for tag, values in extracted_patterns.items():
            if isinstance(values, list):
                name = values[0] if len(values) > 0 else 'Unknown'
                description = values[1] if len(values) > 1 else ''
                example = 'N/A'
            else:
                name = values.get('name', 'Unknown')
                description = values.get('description', '')
                example = values.get('example', 'N/A')
                if len(example) > 100:
                    example = example[:100] + "..."
            
            all_data.append([
                name,
                tag,
                description,
                example,
                values.get('source', 'extracted'),
                "Extracted"
            ])
        
        if all_data:
            df = pd.DataFrame(all_data, columns=['Name', 'XPATH', 'Description', 'Example', 'Category', 'Source'])
            
            # Enhanced table display
            st.markdown("""
            <div style="padding: 1rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
                        border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #10b981;">
                <h4 style="margin: 0; color: #065f46;">📋 Combined Pattern Library</h4>
                <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">All available patterns from default library and current session</p>
            </div>
            """, unsafe_allow_html=True)
            
            from core.common.css_utils import get_css_path
            css_path = get_css_path()
            render_custom_table(df, long_text_cols=['XPATH', 'Description', 'Example'], css_rel_path=css_path)
    
    def _display_extracted_patterns(self, context="default"):
        """Display extracted patterns with delete functionality"""
        extracted_patterns = getattr(st.session_state, 'pattern_responses', {})
        
        if not extracted_patterns:
            st.info("No extracted patterns available.")
            return
        
        data = []
        pattern_count = len(extracted_patterns)
        
        for tag, values in extracted_patterns.items():
            # If values is a list (old format), convert to new format
            if isinstance(values, list):
                values_dict = {
                    'name': values[0],
                    'path': tag,
                    'description': self._format_xml_content(values[1]),
                    'prompt': self._format_xml_content(values[2]),
                    'example': 'N/A'
                }
            else:
                values_dict = {
                    'name': values.get('name', 'Unknown'),
                    'path': tag,
                    'description': self._format_xml_content(values.get('description', '')),
                    'prompt': self._format_xml_content(values.get('prompt', '')),
                    'example': values.get('example', 'N/A')
                }
            data.append([
                values_dict['name'],
                values_dict['path'],
                values_dict['description'],
                values_dict['example']
            ])

        if data:
            # Enhanced metrics display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Patterns Extracted", pattern_count, "ready")
            with col2:
                st.metric("🧠 AI Quality", "High", "confidence")
            with col3:
                st.metric("✅ Status", "Ready", "for verification")
            
            st.markdown("")
            
            df = pd.DataFrame(data, columns=['Name', 'XPATH', 'Description', 'Example'])
            
            
            from core.common.css_utils import get_css_path
            css_path = get_css_path()
            render_custom_table(df, long_text_cols=['XPATH', 'Description', 'Example'], css_rel_path=css_path)
            
            
            # Pattern management actions below the table
            if context != "extract":
                st.markdown("---")
                st.markdown("#### Pattern Actions")
                
                # Add bulk actions or individual pattern management here if needed
                # For now, individual actions are handled in the Save tab
                st.info("💡 **Tip:** Use the **Save** tab to save patterns to your workspace or shared workspace.")
            else:
                st.markdown("---")
                st.info("💡 **Next Steps:** Use the **Verify** tab to validate patterns, then the **Save** tab to save them.")
            
            # Show insights only in extract/pattern_library context, not in save tab
            if context != "save_tab" and hasattr(st.session_state, 'insights') and st.session_state.insights:
                st.markdown("---")
                self.reveal_insights()

    def _format_xml_content(self, content):
        """Format XML content for better display"""
        if not content:
            return content
            
        # Escape XML tags to make them visible
        try:
            # Replace XML tags with HTML entities to make them visible
            formatted_content = content.replace('<', '&lt;').replace('>', '&gt;')
            return formatted_content
        except:
            # If there's any error, just return the content as is
            return content
    
    def auto_select_nodes(self, uploaded_file):
        """
        Automatically select suitable nodes for pattern extraction based on size and complexity.
        """
        from lxml import etree
        
        # Configuration constants
        MAX_NODE_SIZE = 5000  # characters
        MIN_NODE_SIZE = 50    # minimum useful size
        MAX_NODES_PER_BATCH = 15  # prevent overwhelming the LLM
        MAX_RECURSION_DEPTH = 3
        
        try:
            uploaded_file.seek(0)
            xml_tree = etree.parse(uploaded_file)
            root = xml_tree.getroot()
            
            suitable_nodes = {}
            
            def calculate_node_size(node):
                """Calculate node complexity based on multiple factors"""
                xml_string = etree.tostring(node, pretty_print=True, encoding='unicode')
                char_count = len(xml_string)
                child_count = len(list(node))
                depth = self._get_max_depth(node)
                attr_count = len(node.attrib)
                
                # Weighted complexity score
                complexity_score = (
                    char_count * 0.4 +
                    child_count * 100 +
                    depth * 50 +
                    attr_count * 10
                )
                return complexity_score
            
            def calculate_usefulness_score(node):
                """Calculate how useful a node is for pattern extraction"""
                score = 0
                
                # Has text content
                if node.text and node.text.strip():
                    score += 50
                
                # Has attributes
                if node.attrib:
                    score += len(node.attrib) * 20
                
                # Has children but not too many
                child_count = len(list(node))
                if 1 <= child_count <= 10:
                    score += 30
                elif child_count > 10:
                    score -= 10  # too complex
                
                # Prefer nodes that aren't purely structural
                if node.tag and not node.tag.lower() in ['root', 'document', 'wrapper']:
                    score += 20
                
                return score
            
            def analyze_node_recursive(node, path="", depth=0):
                """Recursively analyze nodes and select suitable ones"""
                if depth > MAX_RECURSION_DEPTH:
                    return
                
                tag = str(node.tag)
                current_path = f"{path}/{tag}[0]" if not path else f"{path}/{tag}[{len([p for p in suitable_nodes.keys() if p.startswith(f'{path}/{tag}')])}]"
                
                node_size = calculate_node_size(node)
                usefulness = calculate_usefulness_score(node)
                
                if MIN_NODE_SIZE <= node_size <= MAX_NODE_SIZE and usefulness >= 30:
                    # Node is suitable - add it
                    xml_string = etree.tostring(node, pretty_print=True, encoding='unicode')
                    suitable_nodes[current_path] = xml_string
                elif node_size > MAX_NODE_SIZE:
                    # Node too big - analyze children
                    for child in list(node):
                        analyze_node_recursive(child, current_path, depth + 1)
                else:
                    # Node might be too small but check if it has useful children
                    children = list(node)
                    if children and depth < MAX_RECURSION_DEPTH - 1:
                        for child in children[:5]:  # Limit to first 5 children
                            analyze_node_recursive(child, current_path, depth + 1)
            
            # Start analysis from root
            analyze_node_recursive(root)
            
            # If we have too many nodes, select the most useful ones
            if len(suitable_nodes) > MAX_NODES_PER_BATCH:
                # Score nodes again and take top ones
                scored_nodes = []
                for path, xml_content in suitable_nodes.items():
                    # Parse the XML content to get the node for scoring
                    try:
                        temp_node = etree.fromstring(xml_content)
                        score = calculate_usefulness_score(temp_node)
                        scored_nodes.append((path, xml_content, score))
                    except:
                        scored_nodes.append((path, xml_content, 0))
                
                # Sort by score and take top nodes
                scored_nodes.sort(key=lambda x: x[2], reverse=True)
                suitable_nodes = {path: content for path, content, score in scored_nodes[:MAX_NODES_PER_BATCH]}
            
            return suitable_nodes
            
        except Exception as e:
            st.error(f"Error in auto node selection: {e}")
            return {}
    
    def _get_max_depth(self, node):
        """Calculate maximum depth of XML node"""
        if len(list(node)) == 0:
            return 1
        return 1 + max(self._get_max_depth(child) for child in node)
    
    def _analyze_pattern_relationships(self, patterns):
        """
        Analyze extracted patterns to categorize them as individual or linked.
        Returns a summary with counts and categorization.
        """
        if not patterns:
            return {"total": 0, "individual": 0, "linked": 0, "individual_patterns": [], "linked_patterns": []}
        
        individual_patterns = []
        linked_patterns = []
        
        # Convert patterns to a list for easier analysis
        pattern_list = []
        for pattern_key, pattern_data in patterns.items():
            if isinstance(pattern_data, list):
                # Old format
                pattern_info = {
                    'key': pattern_key,
                    'name': pattern_data[0] if len(pattern_data) > 0 else 'Unknown',
                    'path': pattern_key,
                    'description': pattern_data[1] if len(pattern_data) > 1 else ''
                }
            else:
                # New format
                pattern_info = {
                    'key': pattern_key,
                    'name': pattern_data.get('name', 'Unknown'),
                    'path': pattern_data.get('path', pattern_key),
                    'description': pattern_data.get('description', '')
                }
            pattern_list.append(pattern_info)
        
        # Analyze relationships between patterns
        for i, pattern in enumerate(pattern_list):
            is_linked = False
            
            # Check if this pattern is related to any other pattern
            for j, other_pattern in enumerate(pattern_list):
                if i != j:
                    # Check for path relationships (parent/child or sibling)
                    if self._are_patterns_linked(pattern, other_pattern):
                        is_linked = True
                        break
            
            if is_linked:
                linked_patterns.append(pattern)
            else:
                individual_patterns.append(pattern)
        
        return {
            "total": len(pattern_list),
            "individual": len(individual_patterns),
            "linked": len(linked_patterns),
            "individual_patterns": individual_patterns,
            "linked_patterns": linked_patterns
        }
    
    def _are_patterns_linked(self, pattern1, pattern2):
        """
        Determine if two patterns are linked based on their paths and descriptions.
        """
        path1 = pattern1['path'].lower()
        path2 = pattern2['path'].lower()
        desc1 = pattern1['description'].lower()
        desc2 = pattern2['description'].lower()
        
        # Check if paths suggest hierarchy (parent/child relationship)
        if path1 in path2 or path2 in path1:
            return True
        
        # Check if paths share common parent elements
        path1_parts = path1.split('/')
        path2_parts = path2.split('/')
        
        # If they share multiple path components, they might be related
        common_parts = set(path1_parts) & set(path2_parts)
        if len(common_parts) >= 2:  # At least 2 common path elements
            return True
        
        # Check for semantic relationships in descriptions
        # Look for common keywords that suggest relationships
        relationship_keywords = ['passenger', 'flight', 'booking', 'fare', 'segment', 'itinerary']
        
        desc1_keywords = set(desc1.split()) & set(relationship_keywords)
        desc2_keywords = set(desc2.split()) & set(relationship_keywords)
        
        # If they share domain-specific keywords, they might be related
        if desc1_keywords & desc2_keywords:
            return True
        
        return False
    
    def _display_pattern_extraction_summary(self, patterns):
        """
        Display a summary of extracted patterns with individual/linked categorization.
        """
        analysis = self._analyze_pattern_relationships(patterns)
        
        if analysis["total"] == 0:
            return
        
        # Create an attractive summary box
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(59, 130, 246, 0.1));
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #22c55e;
        ">
            <h4 style="margin: 0 0 1rem 0; color: #065f46; display: flex; align-items: center;">
                🎯 Pattern Extraction Summary
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 Total Patterns",
                analysis["total"],
                help="Total number of patterns extracted from the XML"
            )
        
        with col2:
            st.metric(
                "🔲 Individual Patterns",
                analysis["individual"],
                help="Standalone patterns with no direct relationships to other patterns"
            )
        
        with col3:
            st.metric(
                "🔗 Linked Patterns",
                analysis["linked"],
                help="Patterns that are related to other patterns through hierarchy or semantics"
            )
        
        # Detailed breakdown with collapsible sections using details/summary
        if analysis["individual"] > 0:
            st.markdown("### 🔲 Individual Patterns")
            st.markdown("**These patterns are standalone and don't have direct relationships with other extracted patterns:**")
            
            # Use columns to create a compact view
            for i, pattern in enumerate(analysis["individual_patterns"], 1):
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**{i}.**")
                    with col2:
                        st.markdown(f"`{pattern['name']}` - *{pattern['path']}*")
                        if pattern['description']:
                            st.markdown(f"📝 {pattern['description'][:100]}{'...' if len(pattern['description']) > 100 else ''}")
                    st.markdown("---")
        
        if analysis["linked"] > 0:
            st.markdown("### 🔗 Linked Patterns")
            st.markdown("**These patterns are related to other patterns through hierarchical or semantic relationships:**")
            
            # Use columns to create a compact view
            for i, pattern in enumerate(analysis["linked_patterns"], 1):
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**{i}.**")
                    with col2:
                        st.markdown(f"`{pattern['name']}` - *{pattern['path']}*")
                        if pattern['description']:
                            st.markdown(f"📝 {pattern['description'][:100]}{'...' if len(pattern['description']) > 100 else ''}")
                    st.markdown("---")
        
        # Add helpful tip
        st.info("💡 **Tip:** Linked patterns often represent related data elements (like passenger details and flight segments) while individual patterns are typically standalone elements.")
        
        st.markdown("---")
    
    def _add_default_patterns_to_session(self, patterns: list):
        """Add default patterns to the current session"""
        try:
            if 'pattern_responses' not in st.session_state:
                st.session_state.pattern_responses = {}
            
            for pattern in patterns:
                # Convert default pattern to session format
                pattern_key = f"default_{pattern.pattern_id}"
                st.session_state.pattern_responses[pattern_key] = {
                    'name': pattern.name,
                    'path': pattern.xpath,
                    'description': pattern.description,
                    'prompt': pattern.prompt,
                    'example': pattern.example,
                    'source': 'default_library'
                }
            
            self.logger.info(f"Added {len(patterns)} default patterns to session")
            
        except Exception as e:
            st.error(f"Error adding default patterns: {e}")
            self.logger.error(f"Error in _add_default_patterns_to_session: {e}")
    
            
    def save_user_pattern(self, pattern_data: dict):
        """Save a user-extracted pattern to the default patterns library"""
        try:
            from core.database.default_patterns_manager import DefaultPattern
            
            # Create a new default pattern from user data
            pattern_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pattern_data.get('name', 'pattern').lower().replace(' ', '_')}"
            
            default_pattern = DefaultPattern(
                pattern_id=pattern_id,
                name=pattern_data.get('name', 'User Pattern'),
                description=pattern_data.get('description', ''),
                prompt=pattern_data.get('prompt', ''),
                example=pattern_data.get('example', ''),
                xpath=pattern_data.get('path', ''),
                category='user_created'
            )
            
            if self.default_patterns_manager.save_pattern(default_pattern):
                st.success(f"✅ Pattern '{default_pattern.name}' saved to default library!")
                return True
            else:
                st.error("❌ Failed to save pattern to default library")
                return False
                
        except Exception as e:
            st.error(f"Error saving user pattern: {e}")
            self.logger.error(f"Error in save_user_pattern: {e}")
            return False