import streamlit as st
import sys
import os
import pandas as pd

st.set_page_config(
    page_title="Pattern Discovery Studio",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force reload of PatternManager to ensure latest version
import importlib
import core.assisted_discovery.pattern_manager as pm_module
importlib.reload(pm_module)
from core.assisted_discovery.pattern_manager import PatternManager
from core.assisted_discovery.pattern_saver import PatternSaver
from core.assisted_discovery.pattern_verifier import PatternVerifier
from core.assisted_discovery.identify_pattern_manager import PatternIdentifyManager
from core.common.cost_display_manager import CostDisplayManager
from core.common.constants import GPT_4O
# from core.common.api_key_manager import APIKeyManager  # Temporarily disabled for demo
from core.common.logging_manager import (
    get_logger, log_user_action, log_error, log_streamlit_error, log_performance, 
    PerformanceLogger, setup_global_exception_handler, streamlit_error_handler
)
from core.common.usecase_manager import UseCaseManager

# Load modern CSS styling
def load_css():
    """Load CSS with enhanced reliability for different environments."""
    try:
        from core.common.streamlit_css_loader import load_streamlit_css
        load_streamlit_css()
    except ImportError:
        # Fallback to previous method if import fails
        from core.common.css_utils import load_table_styles
        load_table_styles()

class DiscoverPatternsPage:
    def __init__(self):
        # self._api_manager = APIKeyManager()  # Temporarily disabled for demo
        self._usecase_manager = UseCaseManager()
        self._pattern_manager = PatternManager(GPT_4O)
        self._pattern_verifier = PatternVerifier(GPT_4O)
        self._pattern_saver = None  # Will be initialized when use case is selected
        self._cost_display_manager = CostDisplayManager()
        self._chatbot_manager = PatternIdentifyManager(GPT_4O)  # For chatbot functionality

    @streamlit_error_handler
    def run(self):
        # Set up global exception handler for better error logging
        setup_global_exception_handler()
        
        # API key checks temporarily disabled for demo
        # missing_keys = self._api_manager.get_missing_required_keys()
        # if missing_keys:
        #     self._render_api_key_required()
        #     return
        #     
        # # Set environment variables for current session
        # self._api_manager.set_environment_variables()
        load_css()
        
        # Sidebar - always render first
        with st.sidebar:
            # Workspace Selection
            st.markdown("### 🎯 Workspace Selection")
            selected_use_case = self._usecase_manager.render_use_case_selector("discovery_use_case")
            
            st.markdown("---")
            
            # Cost metrics
            self._cost_display_manager.render_cost_metrics()
        
        # Enhanced Page header with blue company theme
        st.markdown("""
        <div class="hero-banner" style="
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 2rem;
            margin: 1rem 0;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        ">
            <div class="hero-content">
                <h1 class="hero-title" style="
                    font-size: 2.5rem;
                    font-weight: 800;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    margin: 0 0 1rem 0;
                    color: white;
                ">🔍 AssistedDiscovery - Pattern Discovery Studio</h1>
                <p class="hero-subtitle" style="
                    font-size: 1.25rem;
                    margin: 0;
                    opacity: 0.95;
                    font-weight: 500;
                ">
                    ⚡ Transform your XML data into intelligent patterns with AI-powered analysis
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if discovery workspace is selected
        current_use_case = self._usecase_manager.get_current_use_case()
        if not current_use_case:
            st.info("👋 **Welcome to Pattern Discovery Studio!**")
            st.warning("📋 **Please select a discovery workspace from the sidebar to get started.**")
            st.markdown("""
            **What you can do:**
            - 🔍 **Extract patterns** from XML files using AI
            - ✅ **Verify patterns** for accuracy
            - 💾 **Save patterns** to your workspace
            - 🛠️ **Manage shared patterns** across your team
            
            **Next step:** Choose a workspace from the sidebar ➡️
            """)
            return
            
        # Initialize pattern saver with use case specific database
        current_db_utils = self._usecase_manager.get_current_db_utils()
        if not self._pattern_saver or self._pattern_saver.db_utils != current_db_utils:
            self._pattern_saver = PatternSaver(GPT_4O, current_db_utils)
            
        # Update chatbot manager with current database
        if not hasattr(self._chatbot_manager, 'db_utils') or self._chatbot_manager.db_utils != current_db_utils:
            self._chatbot_manager = PatternIdentifyManager(GPT_4O, current_db_utils)

        # Enhanced premium tabs
        st.markdown('<div class="premium-tabs"></div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Extract Patterns", "Verify Patterns", "Save Patterns", "Manage Custom Patterns", "Manage Shared Patterns"])

        # Tab 1: Extract patterns with enhanced UI
        with tab1:
            # Modern file upload section with enhanced styling
            st.markdown("#### Pattern Extraction")
        
            # Upload section  
            st.markdown("**Upload XML File**")
            
            uploaded_file = st.file_uploader(
                "Choose your XML file", 
                type=["xml"], 
                key="xml_extract_patterns",
                help="Upload an XML file to analyze its structure and extract meaningful patterns"
            )
            
            if uploaded_file:
                
                # Extraction Mode
                st.markdown("**Extraction Mode**")
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    auto_mode = st.toggle("Auto Mode", value=True, help="Toggle between Auto and Manual extraction")
                
                with col2:
                    if auto_mode:
                        st.info("**Auto Mode Active:** Genie automatically analyzes your XML structure and extracts patterns.")
                    else:
                        st.info("**Manual Mode Active:** You can select specific XML nodes from the tree view.")
                
                st.markdown("---")
                
                # Pattern extraction with mode-based logic
                if auto_mode:
                    self._handle_auto_mode(uploaded_file)
                else:
                    self._handle_manual_mode(uploaded_file)
                    
                # Custom Pattern Addition Section
                with st.expander("Create Custom Patterns", expanded=False):
                    st.info("Advanced users can create custom patterns with full control")
                    self._enhanced_custom_patterns_section(uploaded_file)
                    
            else:
                # Premium empty state
                st.markdown("""
                <div class="enhanced-section-card" style="text-align: center; margin: 3rem 0; padding: 3rem 2rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px;">
                    <h3 style="margin: 0 0 1rem 0; color: #1e40af; font-weight: 700;">Ready to Discover Patterns?</h3>
                    <p style="margin: 0 0 2rem 0; color: #3b82f6; font-size: 1.1rem; line-height: 1.6;">
                        Upload your XML file above to begin intelligent pattern discovery and extraction!
                    </p>
                    <div style="display: flex; justify-content: center; gap: 1rem; margin: 2rem 0;">
                        <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">AI-Powered</span>
                        <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Lightning Fast</span>
                        <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Highly Accurate</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                

        # Tab 2: Verification section
        with tab2:
            st.markdown("#### Pattern Verification Hub")
            st.markdown("Validate and confirm the accuracy of extracted patterns using AI verification.")
            
            self._pattern_verifier.verify_prompts()

        # Tab 3: Save patterns section
        with tab3:
            # Display pattern library first
            self._display_discovery_pattern_library()
            
            # Save patterns functionality
            self._pattern_saver.save_patterns()
        
        # Tab 4: Manage Custom Patterns section
        with tab4:
            st.markdown("#### 🎨 Custom Pattern Management")
            st.markdown("Manage your saved patterns - delete unwanted patterns and organize them by categories.")
            
            # Get saved patterns from database
            saved_patterns = self._get_user_saved_patterns()
            self._display_custom_pattern_management(saved_patterns)

        # Tab 5: Manage Shared Patterns section
        with tab5:
            st.markdown("#### 🛠️ Shared Workspace Management")
            st.markdown("Manage patterns in the shared workspace - view, search, and remove irrelevant patterns.")
            
            # Get default patterns for management
            default_patterns = self._pattern_manager.default_patterns_manager.get_all_patterns()
            self._display_shared_pattern_management(default_patterns)
    
    def _handle_auto_mode(self, uploaded_file):
        """Handle automatic pattern extraction mode"""
        st.markdown("#### Automatic Pattern Extraction")
        
        # Extract button for auto mode
        extract_clicked = st.button("Start Auto Extraction", type="primary", use_container_width=True)
        
        if extract_clicked:
            auto_selected_nodes = self._pattern_manager.auto_select_nodes(uploaded_file)
            
            if auto_selected_nodes:
                with st.status("Auto Processing XML...", expanded=True) as status:
                    st.write(f"Processing {len(auto_selected_nodes)} auto-selected nodes...")
                    
                    # Step 1: Extract insights
                    st.write("Analyzing node relationships...")
                    insights = self._pattern_manager._extract_insights(auto_selected_nodes)
                    
                    # Step 2: Extract patterns
                    st.write("Extracting patterns with AI...")
                    response = self._pattern_manager.generate_prompt_from_xml_chunk(auto_selected_nodes, insights)
                    
                    # Process results
                    if response and response.get('patterns'):
                        patterns = response.get('patterns', [])
                        if 'pattern_responses' not in st.session_state:
                            st.session_state.pattern_responses = {}
                        
                        for pattern in patterns:
                            pattern_path = pattern["pattern"]["path"]
                            st.session_state.pattern_responses[pattern_path] = pattern["pattern"]
                        
                        st.write(f"Successfully extracted {len(patterns)} patterns!")
                        status.update(label="Auto Extraction Complete!", state="complete")
                        
                # Display the extracted patterns in a table (outside the status container)
                if hasattr(st.session_state, 'pattern_responses') and st.session_state.pattern_responses:
                    st.markdown("---")
                    st.markdown("#### 📋 Extracted Patterns")
                    self._pattern_manager._display_extracted_patterns("auto_extract")
                    
                    # Store patterns and XML content persistently for chatbot
                    st.session_state.auto_extracted_patterns = st.session_state.pattern_responses
                    st.session_state.auto_xml_content = uploaded_file.getvalue().decode('utf-8') if uploaded_file else ""
                    
                    # Add chatbot for discussing extraction results
                    st.markdown("---")
                    self._render_discovery_chatbot(st.session_state.pattern_responses, uploaded_file.getvalue().decode('utf-8') if uploaded_file else "")
                else:
                    st.write("No patterns found. The XML structure may not contain extractable patterns.")
                    
                    # Add chatbot even when no patterns found (for guidance)
                    st.markdown("---")
                    self._render_discovery_chatbot({}, uploaded_file.getvalue().decode('utf-8') if uploaded_file else "")
            else:
                st.error("No suitable nodes found for automatic extraction. Try manual mode or check your XML structure.")
        
        # Show chatbot section if patterns were previously extracted (for after page refresh)
        elif hasattr(st.session_state, 'auto_extracted_patterns') and st.session_state.auto_extracted_patterns:
            st.markdown("---")
            st.markdown("#### 📋 Extracted Patterns")
            
            # Temporarily restore pattern_responses to show the table
            original_pattern_responses = st.session_state.get('pattern_responses', {})
            st.session_state.pattern_responses = st.session_state.auto_extracted_patterns
            
            # Display the patterns table
            self._pattern_manager._display_extracted_patterns("auto_extract_preserved")
            
            # Restore original pattern_responses
            st.session_state.pattern_responses = original_pattern_responses
            
            st.markdown("---")
            self._render_discovery_chatbot(
                st.session_state.auto_extracted_patterns,
                st.session_state.get('auto_xml_content', '')
            )
    
    def _handle_manual_mode(self, uploaded_file):
        """Handle manual pattern extraction mode"""
        st.markdown("#### Manual Pattern Selection")
        
        # Use the existing manual extraction logic
        with st.container():
            self._pattern_manager.extract_patterns(uploaded_file)
            
            # Add chatbot for discussing manual extraction results
            if hasattr(st.session_state, 'pattern_responses') and st.session_state.pattern_responses:
                st.markdown("---")
                self._render_discovery_chatbot(st.session_state.pattern_responses, uploaded_file.getvalue().decode('utf-8') if uploaded_file else "")
    
    def _enhanced_custom_patterns_section(self, uploaded_file):
        """Enhanced custom patterns section with validation and styling"""
        
        st.markdown("#### Create Custom Pattern")
        st.markdown("Add your own patterns with custom XML chunks and descriptions")
        
        # Initialize session state for form fields
        if 'custom_pattern_form' not in st.session_state:
            st.session_state.custom_pattern_form = {
                'name': '',
                'tag': '',
                'xml_chunk': '',
                'description': '',
                'prompt': '',
                'provide_own_prompt': False
            }
        
        # Form fields with validation
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="custom-field-label">Pattern Name <span class="required-asterisk">*</span></div>', unsafe_allow_html=True)
            name = st.text_input("", 
                               key="custom_pattern_name",
                               placeholder="e.g., Passenger Details",
                               help="Give your pattern a descriptive name")
            
            st.markdown('<div class="custom-field-label">XML Tag <span class="required-asterisk">*</span></div>', unsafe_allow_html=True)
            tag = st.text_input("", 
                              key="custom_pattern_tag",
                              placeholder="e.g., //Passenger",
                              help="XPath or tag name for this pattern")
        
        with col2:
            st.markdown('<div class="custom-field-label">Description <span class="required-asterisk">*</span></div>', unsafe_allow_html=True)
            description = st.text_area("", 
                                     height=100,
                                     key="custom_pattern_description",
                                     placeholder="Describe what this pattern extracts...",
                                     help="Explain what this pattern is used for")
        
        # XML Chunk field (full width)
        st.markdown('<div class="custom-field-label">XML Sample <span class="required-asterisk">*</span></div>', unsafe_allow_html=True)
        xml_chunk = st.text_area("", 
                                height=120,
                                key="custom_pattern_xml",
                                placeholder="Paste a sample XML chunk here...",
                                help="Provide a sample XML that represents this pattern")
        
        # Calculate completion percentage
        required_fields = [name, tag, description, xml_chunk]
        filled_fields = sum(1 for field in required_fields if field.strip())
        completion_percentage = (filled_fields / len(required_fields)) * 100
        
        # Progress bar
        st.markdown(f"""
        <div class="form-progress">
            <div class="form-progress-bar" style="width: {completion_percentage}%"></div>
        </div>
        <p style="text-align: center; color: #6b7280; font-size: 0.8rem; margin: 0.5rem 0;">
            Form Completion: {completion_percentage:.0f}% ({filled_fields}/{len(required_fields)} fields)
        </p>
        """, unsafe_allow_html=True)
        
        # Prompt section
        st.markdown("---")
        provide_own_prompt = st.checkbox("I'll provide my own prompt", 
                                       help="Check this if you want to write a custom prompt instead of generating one")
        
        if provide_own_prompt:
            st.markdown('<div class="custom-field-label">Custom Prompt</div>', unsafe_allow_html=True)
            custom_prompt = st.text_area("", 
                                       height=100,
                                       key="custom_pattern_prompt",
                                       placeholder="Enter your custom prompt here...",
                                       help="Write a custom prompt for pattern extraction")
            prompt_ready = bool(custom_prompt.strip())
        else:
            custom_prompt = ""
            prompt_ready = True  # Will generate automatically
        
        # Validation logic
        all_required_filled = all(field.strip() for field in required_fields)
        can_submit = all_required_filled and prompt_ready
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if not provide_own_prompt and all_required_filled:
                if st.button("Generate Prompt", 
                           type="secondary", 
                           use_container_width=True,
                           help="Let Genie generate a prompt based on your inputs"):
                    with st.spinner("Generating prompt..."):
                        # Call the existing prompt generation method
                        self._generate_prompt_for_manual_input(xml_chunk, tag, name, description)
        
        with col2:
            # Clear form button
            if st.button("Clear Form", 
                       type="secondary", 
                       use_container_width=True,
                       help="Reset all form fields"):
                # Clear all form fields
                for key in ['custom_pattern_name', 'custom_pattern_tag', 'custom_pattern_description', 'custom_pattern_xml', 'custom_pattern_prompt']:
                    if key in st.session_state:
                        st.session_state[key] = ""
                st.rerun()
        
        with col3:
            # Main submit button
            button_text = "Add Pattern" if can_submit else f"Complete Form ({4-filled_fields} fields left)"
            button_help = "Add this custom pattern to your collection" if can_submit else "Please fill all required fields to continue"
            
            if st.button(button_text, 
                       type="primary" if can_submit else "secondary",
                       disabled=not can_submit,
                       use_container_width=True,
                       help=button_help):
                
                # Set the final prompt
                if provide_own_prompt:
                    st.session_state.final_prompt = custom_prompt
                elif hasattr(st.session_state, 'final_prompt') and st.session_state.final_prompt:
                    # Use the generated prompt
                    pass
                else:
                    st.error("No prompt available. Please generate a prompt or provide your own.")
                    return
                
                # Add the pattern
                self._add_pattern_to_session(tag, name, description)
                
                # Clear form after successful addition
                for key in ['custom_pattern_name', 'custom_pattern_tag', 'custom_pattern_description', 'custom_pattern_xml', 'custom_pattern_prompt']:
                    if key in st.session_state:
                        st.session_state[key] = ""
                
                st.success("Custom pattern added successfully!")
                st.rerun()
        
        # Show current patterns if any exist
        if 'pattern_responses' in st.session_state and st.session_state.pattern_responses:
            st.markdown("---")
            st.markdown("### Current Patterns")
            pattern_count = len(st.session_state.pattern_responses)
            st.info(f"You have **{pattern_count}** pattern{'s' if pattern_count != 1 else ''} ready for verification and export.")
    
    def _generate_prompt_for_manual_input(self, xml_chunk, tag, name, description):
        """Generate a prompt for manual input using the LLM"""
        try:
            is_valid_xml, prompt_from_llm = self._pattern_manager.generate_prompt_from_manual_input(xml_chunk, tag, name, description)
            if is_valid_xml:
                st.session_state.final_prompt = prompt_from_llm
                st.success("Prompt generated successfully!")
                with st.expander("View Generated Prompt", expanded=False):
                    st.code(st.session_state.final_prompt, language="text")
            else:
                st.error("Failed to generate prompt. Please check your XML and try again.")
        except Exception as e:
            st.error(f"Error generating prompt: {str(e)}")
    
    def _add_pattern_to_session(self, tag, name, description):
        """Add a manually created pattern to the session state"""
        try:
            if not hasattr(st.session_state, 'final_prompt') or st.session_state.final_prompt is None:
                st.error("No prompt available. Please generate or provide a prompt first.")
                return
            
            if 'pattern_responses' not in st.session_state:
                st.session_state.pattern_responses = {}
            
            st.session_state.pattern_responses[tag] = [name, description, st.session_state.final_prompt, False]
            
            # Reset final_prompt after adding the pattern
            st.session_state.final_prompt = None
            
        except Exception as e:
            st.error(f"Error adding pattern: {str(e)}")
    
    # API key configuration method temporarily disabled for demo
    # def _render_api_key_required(self):
    #     """
    #     Render API key configuration required message.
    #     """
    #     load_css()
    #     
    #     # Header
    #     st.markdown("""
    #     <div class="hero-banner">
    #         <div class="hero-content">
    #             <h1 class="hero-title">⚙️ Configuration Required</h1>
    #             <p class="hero-subtitle">
    #                 API keys need to be configured before using pattern discovery
    #             </p>
    #         </div>
    #     </div>
    #     """, unsafe_allow_html=True)
    #     
    #     missing_keys = self._api_manager.get_missing_required_keys()
    #     
    #     st.warning(f"""
    #     **Setup Required**: The following required API keys are missing:
    #     
    #     {', '.join([self._api_manager.required_keys[key]['name'] for key in missing_keys])}
    #     
    #     Please configure these keys to use pattern discovery features.
    #     """)
    #     
    #     st.markdown("""
    #     ### 🔐 Next Steps
    #     
    #     1. Navigate to the **Configuration** page using the sidebar
    #     2. Configure your required API keys
    #     3. Return to this page to start discovering patterns
    #     """)
    #     
    #     # Quick access button
    #     st.markdown("---")
    #     col1, col2, col3 = st.columns([1, 2, 1])
    #     with col2:
    #         if st.button("🔧 Go to Configuration Page", type="primary", use_container_width=True):
    #             st.switch_page("0_⚙️_Configuration.py")
    #     
    #     # Sidebar status
    #     with st.sidebar:
    #         self._api_manager.render_api_key_status()
    
    def _display_discovery_pattern_library(self):
        """Display pattern library with custom tab order: Extracted → Default → All"""
        
        # Get patterns for tab organization - ensure we always have the latest
        extracted_patterns = getattr(st.session_state, 'pattern_responses', {})
        
        default_patterns = self._pattern_manager.default_patterns_manager.get_all_patterns()
        
        st.markdown("---")
        # Enhanced pattern library header
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; margin: 1rem 0;
                    background: linear-gradient(135deg, rgba(147, 51, 234, 0.1), rgba(168, 85, 247, 0.1));
                    border-radius: 12px; border: 1px solid rgba(147, 51, 234, 0.3);">
            <h3 style="margin: 0; color: #6b21a8;">📚 Pattern Library</h3>
            <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.95rem;">View extracted patterns, shared patterns, and combined library</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs: Extracted → Shared → Combined
        tab1, tab2, tab3 = st.tabs(["🔬 Extracted Patterns", "🌐 Shared Patterns", "📋 Combined Library"])
        
        # Tab 1: Extracted Patterns (current session only)  
        with tab1:
            # Force refresh of extracted patterns
            fresh_patterns = getattr(st.session_state, 'pattern_responses', {})
            
            if fresh_patterns:
                st.success(f"✅ **{len(fresh_patterns)} extracted patterns** ready for verification and saving")
                self._pattern_manager._display_extracted_patterns("save_tab")
                # Add helpful info with save tip
                st.info("💡 **Tip:** Use 'Save to Shared Workspace' to make these patterns available to all users!")
            else:
                st.info("📝 **No extracted patterns yet.** Upload an XML file and extract patterns to see them here.")
        
        # Tab 2: Shared Patterns (from shared workspace)
        with tab2:
            if default_patterns:
                self._display_shared_patterns_only(default_patterns)
            else:
                st.info("🌐 **No shared patterns yet.** Save patterns to the shared workspace to see them here.")
        
        # Tab 3: Combined Library (extracted + shared patterns together)
        with tab3:
            # Use fresh patterns for combined view
            fresh_extracted = getattr(st.session_state, 'pattern_responses', {})
            
            if fresh_extracted or default_patterns:
                st.info(f"📚 **Showing {len(fresh_extracted)} extracted + {len(default_patterns)} shared patterns**")
                self._pattern_manager._display_all_patterns_tab(default_patterns, fresh_extracted)
                st.info("📚 **This shows all patterns:** extracted patterns from your current session + shared patterns from the workspace.")
            else:
                st.info("📋 **No patterns available.** Extract patterns from XML files or add patterns to the shared workspace.")
    
    def _display_shared_patterns_only(self, default_patterns):
        """Display only shared patterns from the workspace"""
        
        # Show metrics for shared patterns
        categories = {}
        for pattern in default_patterns:
            cat = pattern.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌐 Shared Patterns", len(default_patterns))
        with col2:
            st.metric("📁 Categories", len(categories))
        with col3:
            most_common_cat = max(categories.items(), key=lambda x: x[1]) if categories else ("none", 0)
            st.metric("🏆 Top Category", most_common_cat[0].title())
        with col4:
            st.metric("📊 In Top Category", most_common_cat[1])
        
        st.markdown("---")
        
        # Display shared patterns in organized way
        if categories:
            # Group patterns by category
            for category, count in sorted(categories.items()):
                category_patterns = [p for p in default_patterns if (p.category or "uncategorized") == category]
                
                with st.expander(f"📂 **{category.title()}** ({count} patterns)", expanded=False):
                    for i, pattern in enumerate(category_patterns):
                        # Pattern header
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{pattern.name}**")
                            if pattern.description:
                                st.markdown(f"*{pattern.description}*")
                        with col2:
                            st.markdown(f"`{pattern.xpath or 'N/A'}`")
                        with col3:
                            # Show details button instead of nested expander
                            show_details = st.button("🔍 Details", key=f"details_{category}_{i}", help=f"Show details for {pattern.name}")
                        
                        # Show pattern details when button is clicked
                        if show_details:
                            with st.container():
                                st.markdown("---")
                                if pattern.prompt:
                                    st.markdown("**Prompt:**")
                                    st.code(pattern.prompt, language="text")
                                
                                if pattern.example:
                                    st.markdown("**Example:**")
                                    st.code(pattern.example, language="xml")
                                
                                st.markdown(f"**Created:** {pattern.created_at or 'Unknown'}")
                                st.markdown("---")
                        
                        if i < len(category_patterns) - 1:  # Don't add separator after last item
                            st.markdown("---")
        
        st.success("✅ **These patterns are available to all team members** and can be used across different workspaces.")
    
    def _get_user_saved_patterns(self):
        """Get patterns saved by the user from the database"""
        try:
            current_db_utils = self._usecase_manager.get_current_db_utils()
            if not current_db_utils:
                return {}
            
            # Query to get all saved patterns with their details
            query = """
                SELECT 
                    pd.pattern_id,
                    pd.pattern_name,
                    pd.pattern_description,
                    pd.pattern_prompt,
                    a.api_name,
                    aps.section_name,
                    aps.section_display_name,
                    pd.created_at,
                    pd.updated_at
                FROM pattern_details pd
                LEFT JOIN section_pattern_mapping spm ON pd.pattern_id = spm.pattern_id
                LEFT JOIN api_section aps ON spm.section_id = aps.section_id
                LEFT JOIN api a ON spm.api_id = a.api_id
                ORDER BY pd.created_at DESC
            """
            
            results = current_db_utils.execute_query(query)
            
            patterns = {}
            for row in results:
                pattern_id = row[0]
                pattern_data = {
                    'id': pattern_id,
                    'name': row[1],
                    'description': row[2],
                    'prompt': row[3],
                    'api_name': row[4],
                    'section_name': row[5],
                    'section_display_name': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'category': 'user_created',  # Default category for saved patterns
                    'verified': True,  # Saved patterns are considered verified
                    'path': row[5] if row[5] else f"pattern_{pattern_id}"  # Use section_name as path
                }
                
                # Use pattern_id as key to avoid duplicates
                patterns[f"saved_{pattern_id}"] = pattern_data
            
            return patterns
            
        except Exception as e:
            st.error(f"Error fetching saved patterns: {str(e)}")
            return {}
    
    def _delete_patterns_from_database(self, pattern_ids):
        """Delete patterns from database by their IDs"""
        try:
            current_db_utils = self._usecase_manager.get_current_db_utils()
            if not current_db_utils:
                return 0
            
            deleted_count = 0
            for pattern_id in pattern_ids:
                try:
                    # Delete from section_pattern_mapping first (foreign key constraint)
                    current_db_utils.execute_query(
                        "DELETE FROM section_pattern_mapping WHERE pattern_id = ?",
                        (pattern_id,)
                    )
                    
                    # Delete from pattern_details
                    current_db_utils.execute_query(
                        "DELETE FROM pattern_details WHERE pattern_id = ?",
                        (pattern_id,)
                    )
                    
                    deleted_count += 1
                    
                except Exception as e:
                    st.error(f"Error deleting pattern {pattern_id}: {str(e)}")
                    continue
            
            return deleted_count
            
        except Exception as e:
            st.error(f"Database deletion error: {str(e)}")
            return 0
    
    def _display_custom_pattern_management(self, saved_patterns):
        """Display interface for managing user's saved patterns from database"""
        
        if not saved_patterns:
            st.info("📝 **No saved patterns to manage.** Save some patterns first!")
            st.markdown("""
            **To get started:**
            1. Go to the **Extract Patterns** tab
            2. Upload an XML file and extract patterns
            3. Go to the **Verify Patterns** tab to verify them
            4. Go to the **Save Patterns** tab to save them to database
            5. Return here to manage your saved patterns
            """)
            return
        
        # Statistics summary
        total_patterns = len(saved_patterns)
        verified_patterns = sum(1 for p in saved_patterns.values() if p.get('verified', False))
        categories = {}
        apis = {}
        
        # Count patterns by category and API
        for pattern_data in saved_patterns.values():
            # Category counting
            cat = pattern_data.get('category', 'user_created')
            categories[cat] = categories.get(cat, 0) + 1
            
            # API counting
            api = pattern_data.get('api_name', 'Unknown API')
            apis[api] = apis.get(api, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💾 Saved Patterns", total_patterns)
        with col2:
            st.metric("🏢 APIs", len(apis))
        with col3:
            st.metric("📁 Categories", len(categories))
        with col4:
            most_common_api = max(apis.items(), key=lambda x: x[1]) if apis else ("none", 0)
            st.metric("🏆 Top API", most_common_api[0])
        
        st.markdown("---")
        
        # Bulk operations
        st.markdown("#### 🔧 Bulk Operations")
        bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 2])
        
        with bulk_col1:
            select_all = st.checkbox("Select All Patterns", key="select_all_custom_patterns")
        
        with bulk_col2:
            if st.button("🗑️ Delete Selected", type="secondary", help="Delete selected saved patterns"):
                selected_patterns = []
                for i, (pattern_key, pattern_data) in enumerate(saved_patterns.items()):
                    if st.session_state.get(f"saved_pattern_select_{i}_{pattern_key}", False) or select_all:
                        selected_patterns.append(pattern_data.get('id'))  # Store pattern_id for database deletion
                
                if selected_patterns:
                    st.session_state.show_saved_delete_confirm = True
                    st.session_state.saved_patterns_to_delete = selected_patterns
        
        with bulk_col3:
            if total_patterns > 0:
                st.info(f"💡 **Tip:** Select patterns using checkboxes for bulk operations")
        
        # Handle bulk delete confirmation
        if getattr(st.session_state, 'show_saved_delete_confirm', False):
            patterns_to_delete = getattr(st.session_state, 'saved_patterns_to_delete', [])
            
            st.warning(f"⚠️ **Confirm Deletion**: Are you sure you want to delete {len(patterns_to_delete)} saved patterns from database? This action cannot be undone.")
            
            conf_col1, conf_col2 = st.columns([1, 1])
            with conf_col1:
                if st.button("✅ Confirm Delete", type="primary"):
                    deleted_count = self._delete_patterns_from_database(patterns_to_delete)
                    
                    if deleted_count > 0:
                        st.success(f"✅ Successfully deleted {deleted_count} patterns from database!")
                    else:
                        st.error("❌ Failed to delete patterns from database.")
                    
                    st.session_state.show_saved_delete_confirm = False
                    st.session_state.saved_patterns_to_delete = []
                    st.rerun()
            
            with conf_col2:
                if st.button("❌ Cancel", type="secondary"):
                    st.session_state.show_saved_delete_confirm = False
                    st.session_state.saved_patterns_to_delete = []
                    st.rerun()
        
        st.markdown("---")
        
        # Individual pattern management
        st.markdown("#### 🎯 Individual Pattern Management")
        
        # Available categories for selection
        available_categories = ["flight", "passenger", "fare", "booking", "airline", "user_created", "custom"]
        
        for i, (pattern_key, pattern_data) in enumerate(saved_patterns.items()):
            with st.container():
                # Extract pattern data from database format
                pattern_id = pattern_data.get('id')
                pattern_name = pattern_data.get('name', 'Unknown')
                pattern_desc = pattern_data.get('description', 'No description')
                current_category = pattern_data.get('category', 'user_created')
                api_name = pattern_data.get('api_name', 'Unknown API')
                section_name = pattern_data.get('section_display_name', pattern_data.get('section_name', 'Unknown Section'))
                created_at = pattern_data.get('created_at', 'Unknown')
                verified_status = pattern_data.get('verified', True)  # Saved patterns are considered verified
                
                # Pattern management row
                col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1.5, 1, 0.5])
                
                with col1:
                    pattern_selected = st.checkbox(
                        "",
                        key=f"saved_pattern_select_{i}_{pattern_key}",
                        value=select_all,
                        help=f"Select {pattern_name} for bulk operations"
                    )
                
                with col2:
                    # Pattern info
                    status_icon = "✅" if verified_status else "⏳"
                    st.markdown(f"**{pattern_name}** {status_icon}")
                    st.markdown(f"*{pattern_desc[:80]}{'...' if len(pattern_desc) > 80 else ''}*")
                    st.markdown(f"**API:** {api_name} | **Section:** {section_name}")
                    st.markdown(f"**Created:** {created_at}")
                
                with col3:
                    # Category editor
                    st.markdown("**Category:**")
                    new_category = st.selectbox(
                        "Category",
                        options=available_categories,
                        index=available_categories.index(current_category) if current_category in available_categories else 0,
                        key=f"category_select_{i}_{pattern_key}",
                        label_visibility="collapsed"
                    )
                    
                    # Update category if changed (Note: This would require database update)
                    if new_category != current_category:
                        st.info("💡 Category updates for saved patterns coming soon!")
                
                with col4:
                    # Status and actions
                    if verified_status:
                        st.success("Verified")
                    else:
                        st.warning("Unverified")
                
                with col5:
                    # Individual delete button
                    if st.button("🗑️", key=f"delete_saved_{i}_{pattern_key}", help=f"Delete {pattern_name}"):
                        if st.button(f"⚠️ Confirm", key=f"confirm_delete_saved_{i}_{pattern_key}", help="This action cannot be undone"):
                            deleted_count = self._delete_patterns_from_database([pattern_id])
                            if deleted_count > 0:
                                st.success(f"✅ Deleted pattern: {pattern_name}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete pattern: {pattern_name}")
                
                st.markdown("---")
        
        # Import/Export Section for Custom Patterns
        if total_patterns > 0:
            st.markdown("---")
            st.markdown("#### 📦 Import/Export Custom Patterns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Export Custom Patterns", type="secondary", use_container_width=True):
                    try:
                        # Export custom patterns logic would go here
                        st.success("Custom patterns export functionality coming soon!")
                    except Exception as e:
                        st.error(f"Export failed: {e}")
            
            with col2:
                uploaded_file = st.file_uploader("📥 Import Custom Patterns", type=['json'], key="import_custom")
                if uploaded_file:
                    try:
                        st.success("Custom patterns import functionality coming soon!")
                    except Exception as e:
                        st.error(f"Import failed: {e}")
        
        # Category management tips
        with st.expander("📁 Category Management Tips", expanded=False):
            st.markdown("""
            **Available Categories:**
            - **Flight**: Flight segments, routes, and scheduling information
            - **Passenger**: Passenger details, names, and personal information
            - **Fare**: Pricing, fare rules, and cost-related patterns
            - **Booking**: Booking references, confirmation codes, and reservations
            - **Airline**: Airline codes, carrier information, and airline-specific data
            - **User Created**: Custom patterns created by users
            - **Custom**: For patterns that don't fit other categories
            
            **Why categorize patterns?**
            - Easier to find patterns when saving to shared workspace
            - Better organization in pattern libraries
            - Helps team members discover relevant patterns
            """)
    
    def _display_shared_pattern_management(self, default_patterns):
        """Display interface for managing shared workspace patterns in main tab"""
        
        if not default_patterns:
            st.info("📝 **No patterns in shared workspace.** Save some patterns to the shared workspace first!")
            return
        
        # Statistics summary
        total_patterns = len(default_patterns)
        categories = {}
        for pattern in default_patterns:
            cat = pattern.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Patterns", total_patterns)
        with col2:
            st.metric("📁 Categories", len(categories))
        with col3:
            most_common_cat = max(categories.items(), key=lambda x: x[1]) if categories else ("none", 0)
            st.metric("🏆 Top Category", most_common_cat[0].title())
        with col4:
            st.metric("🔢 In Top Category", most_common_cat[1])
        
        st.markdown("---")
        
        # Search and filter options
        st.markdown("#### 🔍 Search & Filter")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Search patterns", 
                placeholder="Search by name, description, or xpath...",
                help="Search across pattern names, descriptions, and xpath expressions"
            )
        
        with col2:
            filter_category = st.selectbox(
                "Filter by category",
                options=["All Categories"] + sorted(categories.keys()),
                help="Filter patterns by category"
            )
        
        # Filter patterns based on search and category
        filtered_patterns = default_patterns
        
        if search_query:
            search_lower = search_query.lower()
            filtered_patterns = [
                p for p in filtered_patterns 
                if (search_lower in p.name.lower() or 
                    search_lower in (p.description or "").lower() or 
                    search_lower in (p.xpath or "").lower())
            ]
        
        if filter_category != "All Categories":
            filtered_patterns = [p for p in filtered_patterns if p.category == filter_category]
        
        search_text = f'matching "{search_query}"' if search_query else ''
        st.markdown(f"**Found {len(filtered_patterns)} patterns** {search_text}")
        
        if not filtered_patterns:
            st.warning("No patterns match your search criteria.")
            return
        
        st.markdown("---")
        
        # Pattern management interface
        st.markdown("#### 📋 Pattern Management")
        
        # Bulk actions
        st.markdown("**Bulk Actions:**")
        bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 2])
        
        with bulk_col1:
            select_all = st.checkbox("Select All", key="select_all_patterns")
        
        with bulk_col2:
            if st.button("🗑️ Delete Selected", type="secondary", help="Delete all selected patterns"):
                selected_patterns = []
                for i, pattern in enumerate(filtered_patterns):
                    if st.session_state.get(f"pattern_select_{i}_{pattern.pattern_id}", False) or select_all:
                        selected_patterns.append(pattern)
                
                if selected_patterns:
                    # Confirmation dialog
                    st.session_state.show_bulk_delete_confirm = True
                    st.session_state.patterns_to_delete = selected_patterns
        
        with bulk_col3:
            if len(filtered_patterns) > 0:
                st.info(f"💡 **Tip:** Use checkboxes to select patterns for bulk deletion")
        
        # Handle bulk delete confirmation
        if getattr(st.session_state, 'show_bulk_delete_confirm', False):
            patterns_to_delete = getattr(st.session_state, 'patterns_to_delete', [])
            
            st.warning(f"⚠️ **Confirm Deletion**: Are you sure you want to delete {len(patterns_to_delete)} patterns? This action cannot be undone.")
            
            conf_col1, conf_col2, conf_col3 = st.columns([1, 1, 2])
            with conf_col1:
                if st.button("✅ Confirm Delete", type="primary"):
                    deleted_count = 0
                    for pattern in patterns_to_delete:
                        if self._pattern_manager.default_patterns_manager.delete_pattern(pattern.pattern_id):
                            deleted_count += 1
                    
                    st.success(f"✅ Successfully deleted {deleted_count} patterns from shared workspace!")
                    st.session_state.show_bulk_delete_confirm = False
                    st.session_state.patterns_to_delete = []
                    st.rerun()
            
            with conf_col2:
                if st.button("❌ Cancel", type="secondary"):
                    st.session_state.show_bulk_delete_confirm = False
                    st.session_state.patterns_to_delete = []
                    st.rerun()
        
        st.markdown("---")
        
        # Individual pattern management
        st.markdown("**Individual Pattern Actions:**")
        
        for i, pattern in enumerate(filtered_patterns):
            with st.container():
                # Pattern selection checkbox and info
                col1, col2, col3 = st.columns([0.5, 3, 0.5])
                
                with col1:
                    pattern_selected = st.checkbox(
                        "",
                        key=f"pattern_select_{i}_{pattern.pattern_id}",
                        value=select_all,
                        help=f"Select {pattern.name} for bulk actions"
                    )
                
                with col2:
                    # Pattern details in an expander
                    pattern_title = f"**{pattern.name}** ({pattern.category or 'uncategorized'})"
                    
                    with st.expander(pattern_title, expanded=False):
                        st.markdown(f"**Description:** {pattern.description or 'No description provided'}")
                        st.markdown(f"**XPath:** `{pattern.xpath or 'N/A'}`")
                        st.markdown(f"**Category:** {pattern.category or 'uncategorized'}")
                        st.markdown(f"**Created:** {pattern.created_at or 'Unknown'}")
                        
                        if pattern.prompt:
                            st.markdown("**Prompt:**")
                            st.code(pattern.prompt, language="text")
                        
                        if pattern.example:
                            st.markdown("**Example:**")
                            st.code(pattern.example, language="xml")
                
                with col3:
                    # Individual delete button
                    if st.button("🗑️", key=f"delete_{i}_{pattern.pattern_id}", help=f"Delete {pattern.name}"):
                        if st.button(f"⚠️ Confirm", key=f"confirm_delete_{i}_{pattern.pattern_id}", help="This action cannot be undone"):
                            if self._pattern_manager.default_patterns_manager.delete_pattern(pattern.pattern_id):
                                st.success(f"✅ Deleted pattern: {pattern.name}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete pattern: {pattern.name}")
                
                st.markdown("---")
        
        # Import/Export Section for Shared Patterns
        if filtered_patterns:
            st.markdown("---")
            st.markdown("#### 📦 Import/Export Shared Patterns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Export Shared Patterns", type="primary", use_container_width=True):
                    try:
                        file_path = self._pattern_manager.default_patterns_manager.export_patterns()
                        st.success(f"✅ Exported shared patterns to {file_path}")
                    except Exception as e:
                        st.error(f"❌ Export failed: {e}")
            
            with col2:
                uploaded_file = st.file_uploader("📥 Import Shared Patterns", type=['json'], key="import_shared")
                if uploaded_file:
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            count = self._pattern_manager.default_patterns_manager.import_patterns(tmp_file.name)
                            st.success(f"✅ Imported {count} shared patterns!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Import failed: {e}")
            
            st.info("💡 **Tip:** Shared patterns are available to all users in the workspace")
    
    def _render_discovery_chatbot(self, extracted_patterns, xml_content):
        """Render chatbot for discussing extraction results"""
        
        # Initialize chat state
        if 'discovery_chatbot_messages' not in st.session_state:
            st.session_state.discovery_chatbot_messages = []
        if 'discovery_chatbot_open' not in st.session_state:
            st.session_state.discovery_chatbot_open = False
        
        # Enhanced prominent chat toggle button
        st.markdown("""
        <style>
        .chat-toggle-container {
            display: flex;
            justify-content: center;
            margin: 2rem 0;
        }
        .elegant-chat-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 1rem 2rem;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            border: 2px solid rgba(255, 255, 255, 0.2);
            min-width: 280px;
            justify-content: center;
        }
        .elegant-chat-button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        .chat-icon {
            font-size: 1.5rem;
            animation: pulse 2s infinite ease-in-out;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Center the chat toggle button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🤖 Ask Genie About Extraction", key="discovery_chat_toggle_btn", help="Open intelligent chat to discuss extraction results", use_container_width=True):
                st.session_state.discovery_chatbot_open = not st.session_state.get('discovery_chatbot_open', False)
        
        # Show chat interface when open
        if st.session_state.get('discovery_chatbot_open', False):
            with st.container():
                st.markdown("### 🤖 Chat with Genie")
                
                # Quick action buttons for Discovery context
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Extraction Summary", key="discovery_q_summary", use_container_width=True):
                        st.session_state.discovery_quick_question = "Can you summarize the pattern extraction results?"
                
                with col2:
                    if st.button("Pattern Quality", key="discovery_q_quality", use_container_width=True):
                        st.session_state.discovery_quick_question = "How good are the extracted patterns?"
                
                with col3:
                    if st.button("Next Steps", key="discovery_q_next", use_container_width=True):
                        st.session_state.discovery_quick_question = "What should I do next with these patterns?"
                
                # Chat messages display using native Streamlit components
                if st.session_state.discovery_chatbot_messages:
                    # Create a container for messages
                    with st.container():
                        st.markdown("**💬 Conversation History:**")
                        
                        # Display messages using native Streamlit components
                        for i, message in enumerate(st.session_state.discovery_chatbot_messages):
                            if message["role"] == "user":
                                # User message
                                with st.container():
                                    st.markdown(f"**You:** {message['content']}")
                            else:
                                # Bot message - clean the content first
                                content = message['content']
                                # Remove any HTML tags that might be in the content
                                import re
                                content = re.sub(r'<[^>]+>', '', content)
                                
                                with st.container():
                                    st.markdown(f"**🤖 Genie:** {content}")
                            
                            # Add separator between messages
                            if i < len(st.session_state.discovery_chatbot_messages) - 1:
                                st.markdown("---")
                else:
                    st.info("💬 No messages yet. Start a conversation by clicking a quick action or asking a question!")
                
                # Chat input
                chat_input = st.text_input("Ask a question:", key="discovery_chat_input", placeholder="e.g., Are these patterns comprehensive enough?")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("Send", key="discovery_send_chat"):
                        if chat_input:
                            st.session_state.discovery_quick_question = chat_input
                
                with col2:
                    if st.button("Clear", key="discovery_clear_chat"):
                        st.session_state.discovery_chatbot_messages = []
                        st.rerun()
                
                with col3:
                    if st.button("Close Chat", key="discovery_close_chat"):
                        st.session_state.discovery_chatbot_open = False
                        st.rerun()
        
        # Process quick questions
        if hasattr(st.session_state, 'discovery_quick_question'):
            question = st.session_state.discovery_quick_question
            del st.session_state.discovery_quick_question
            
            # Add user message
            st.session_state.discovery_chatbot_messages.append({"role": "user", "content": question})
            
            # Generate response for Discovery context
            response = self._generate_discovery_chatbot_response(question, extracted_patterns, xml_content)
            st.session_state.discovery_chatbot_messages.append({"role": "bot", "content": response})
            
            st.rerun()
    
    def _generate_discovery_chatbot_response(self, question, extracted_patterns, xml_content):
        """Generate chatbot response for Discovery context"""
        try:
            # Convert patterns to a more readable format for context
            patterns_context = ""
            if extracted_patterns:
                patterns_context = f"Extracted {len(extracted_patterns)} patterns from the XML file."
                for i, (name, details) in enumerate(extracted_patterns.items(), 1):
                    patterns_context += f"\n{i}. {name}: {details.get('description', 'No description')[:100]}"
            
            # Use contextual response generation based on question type
            question_lower = question.lower()
            
            # Summary questions
            if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'results']):
                if extracted_patterns:
                    return f"""📊 **Extraction Summary:**

**Total Patterns Found:** {len(extracted_patterns)}

**Key Patterns Extracted:**
{chr(10).join(f"• **{name}**: {details.get('description', 'Pattern extracted successfully')[:80]}{'...' if len(details.get('description', '')) > 80 else ''}" for name, details in list(extracted_patterns.items())[:5])}

**Next Steps:**
• Review patterns for accuracy and completeness
• Save patterns to your workspace for future identification
• Use patterns to identify similar structures in other XML files
• Consider creating custom patterns for specialized needs"""
                else:
                    return "📊 **Extraction Summary:** No patterns were successfully extracted from the XML file. This could mean the XML structure is too simple, doesn't contain repetitive patterns, or the content doesn't match common airline data formats."
            
            # Quality questions
            elif any(word in question_lower for word in ['quality', 'good', 'accurate', 'reliable', 'how good']):
                if extracted_patterns:
                    pattern_count = len(extracted_patterns)
                    quality_assessment = "High" if pattern_count >= 10 else "Medium" if pattern_count >= 5 else "Basic"
                    
                    return f"""🎯 **Pattern Quality Assessment:**

**Overall Quality:** {quality_assessment}
**Pattern Count:** {pattern_count} patterns

**Quality Indicators:**
✅ **Coverage**: Patterns extracted from XML structure
✅ **Diversity**: Multiple pattern types identified  
✅ **Usability**: Patterns ready for identification tasks

**Quality Factors:**
• **Completeness**: {'Good coverage of XML elements' if pattern_count >= 8 else 'Moderate coverage - consider manual patterns for gaps'}
• **Specificity**: Patterns capture specific data structures
• **Reusability**: Can be used to identify similar XML files

**Recommendations:**
• Verify patterns match your expected data elements
• Test patterns on similar XML files to ensure accuracy
• Add custom patterns for any missing important elements"""
                else:
                    return "🎯 **Pattern Quality Assessment:** No patterns were extracted, so quality cannot be assessed. Consider uploading a different XML file with more structured data or try manual pattern creation."
            
            # Next steps questions
            elif any(word in question_lower for word in ['next', 'what to do', 'what should', 'steps', 'recommend']):
                if extracted_patterns:
                    return f"""🚀 **Recommended Next Steps:**

**Immediate Actions:**
1. **Review Patterns**: Check the {len(extracted_patterns)} extracted patterns for accuracy
2. **Save to Workspace**: Save valuable patterns for future use
3. **Test Patterns**: Use the Identify page to test patterns on other XML files

**Advanced Usage:**
• **Custom Patterns**: Create additional patterns for specialized elements
• **Pattern Verification**: Validate patterns against multiple XML samples  
• **Workspace Organization**: Organize patterns by airline, API version, or data type

**Best Practices:**
• Keep pattern descriptions clear and specific
• Save patterns with meaningful names
• Regularly test patterns on new XML files to ensure continued accuracy

**Ready to proceed?** Navigate to the **Identify page** to test your patterns on new XML files!"""
                else:
                    return """🚀 **Recommended Next Steps:**

**Since no patterns were extracted:**
1. **Try Manual Mode**: Use manual pattern selection to identify specific elements
2. **Check XML Structure**: Ensure your XML contains structured, repetitive data
3. **Custom Patterns**: Create custom patterns for your specific data format
4. **Different XML**: Try with a different XML file that has more complex structure

**Alternative Approaches:**
• Upload XML files with more airline-specific data structures
• Use the custom pattern creation tools
• Review the shared pattern library for examples"""
            
            # Default response
            else:
                context_info = f"You have {len(extracted_patterns)} extracted patterns" if extracted_patterns else "No patterns were extracted"
                return f"""I understand you're asking: "{question}"

**Current Context:** {context_info} from your XML file.

**I can help you with:**
🔍 **Extraction Analysis**: Understanding what was found in your XML
📊 **Pattern Quality**: Assessing the completeness and accuracy of patterns  
🚀 **Next Steps**: Recommendations for using your extracted patterns
🛠️ **Improvements**: Suggestions for better pattern extraction

**Try asking:**
• "Can you summarize the extraction results?"
• "How good are these patterns?"
• "What should I do next?"
• "Are there any missing patterns I should add?"
"""
                
        except Exception as e:
            return f"I apologize, but I encountered an issue processing your question: {str(e)}. Please try asking about the extraction results, pattern quality, or next steps."

# Run the application
if __name__ == "__main__":
    app = DiscoverPatternsPage()
    app.run()