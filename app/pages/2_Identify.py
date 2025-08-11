import streamlit as st
import sys
import os
import pandas as pd

st.set_page_config(
    page_title="Pattern Identification Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.database.sql_db_utils import SQLDatabaseUtils
from core.common.ui_utils import render_custom_table
from core.common.constants import GPT_4O
from core.assisted_discovery.identify_pattern_manager import PatternIdentifyManager
from core.common.cost_display_manager import CostDisplayManager

# Force reload of PatternIdentifyManager to ensure latest version
import importlib
import core.assisted_discovery.identify_pattern_manager as ipm_module
importlib.reload(ipm_module)
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

class EnhancedIdentifyPatternsPage:
    def __init__(self):
        # self._api_manager = APIKeyManager()  # Temporarily disabled for demo
        self._usecase_manager = UseCaseManager()
        self._pattern_identify_manager = ipm_module.PatternIdentifyManager(GPT_4O)
        self._cost_display_manager = CostDisplayManager()
        self.db_utils = None  # Will be set based on selected use case

    @streamlit_error_handler
    def render(self):
        """
        Enhanced pattern identification application with premium UI/UX.
        """
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
        
        try:
            load_css()
        except Exception as e:
            log_streamlit_error(e, "CSS loading failed in Identify page")
        
        # Sidebar - always render first
        with st.sidebar:
            # Workspace Selection
            st.markdown("### 🎯 Workspace Selection")
            selected_use_case = self._usecase_manager.render_use_case_selector("identify_use_case")
            
            st.markdown("---")
            
            # Cost metrics
            self._cost_display_manager.render_cost_metrics()
        
        # Enhanced Professional header with blue company theme
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
                ">📊 AssistedDiscovery - Pattern Identification Studio</h1>
                <p class="hero-subtitle" style="
                    font-size: 1.25rem;
                    margin: 0;
                    opacity: 0.95;
                    font-weight: 500;
                ">
                    🎯 Identify and analyze XML patterns using AI-powered Genie recognition
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if use case is selected
        current_use_case = self._usecase_manager.get_current_use_case()
        if not current_use_case:
            st.warning("⚠️ Please select a use case from the sidebar to continue with pattern identification.")
            return
            
        # Set database utils based on current use case
        self.db_utils = self._usecase_manager.get_current_db_utils()
        if not self.db_utils:
            st.error("❌ Failed to initialize database for the selected use case.")
            return
            
        # Update pattern identify manager with use case specific database
        if not hasattr(self._pattern_identify_manager, 'db_utils') or self._pattern_identify_manager.db_utils != self.db_utils:
            self._pattern_identify_manager = ipm_module.PatternIdentifyManager(GPT_4O, self.db_utils)

        # Enhanced premium tabs
        st.markdown('<div class="premium-tabs"></div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Identify Patterns", "Pattern Library"])

        # Tab 1: Enhanced Pattern Identification
        with tab1:
            self._render_identification_section()

        # Tab 2: Enhanced Pattern Library
        with tab2:
            self._render_pattern_library()


    def _render_identification_section(self):
        """Enhanced pattern identification section"""
        
        # Upload section
        st.markdown("#### Upload XML for Pattern Analysis")

        # File uploader
        unknown_source_xml = st.file_uploader(
            "Choose your XML file for analysis", 
            type=["xml"], 
            key="unknown_source_xml",
            help="Upload any XML file to identify patterns and analyze structure"
        )

        if unknown_source_xml:

            # Check workspace status before analysis
            workspace_patterns_count = len(self.db_utils.get_all_patterns()) if self.db_utils else 0
            
            # Also check shared patterns
            try:
                from core.database.default_patterns_manager import DefaultPatternsManager
                default_patterns_manager = DefaultPatternsManager()
                shared_patterns_count = len(default_patterns_manager.get_all_patterns())
            except:
                shared_patterns_count = 0
            
            total_patterns = workspace_patterns_count + shared_patterns_count
            
            if total_patterns == 0:
                st.warning("""
                ⚠️ **No Saved Patterns Available**: No patterns exist in your workspace or shared library. 
                Pattern identification requires existing patterns to compare against. 
                Please save some patterns from the Discovery page first.
                """)
            
            # Pattern Filtering Section
            if total_patterns > 0:
                st.markdown("#### 🎯 Pattern Selection Filters")
                st.markdown("Choose specific airlines and API versions to test against (optional)")
                
                # Get available airlines and versions from patterns
                available_airlines, available_versions = self._get_available_airlines_and_versions()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_airlines = st.multiselect(
                        "Select Airlines",
                        options=["All Airlines"] + available_airlines,
                        default=["All Airlines"],
                        help="Choose specific airlines to test patterns against. Leave 'All Airlines' selected to test all patterns."
                    )
                
                with col2:
                    selected_versions = st.multiselect(
                        "Select API Versions", 
                        options=["All Versions"] + available_versions,
                        default=["All Versions"],
                        help="Choose specific API versions to test. Leave 'All Versions' selected to test all versions."
                    )
                
                # Process selections
                airline_filter = None if "All Airlines" in selected_airlines else selected_airlines
                version_filter = None if "All Versions" in selected_versions else selected_versions
                
                # Show filter summary
                if airline_filter or version_filter:
                    filter_summary = []
                    if airline_filter:
                        filter_summary.append(f"Airlines: {', '.join(airline_filter)}")
                    if version_filter:
                        filter_summary.append(f"Versions: {', '.join(version_filter)}")
                    st.info(f"🎯 **Active Filters:** {' | '.join(filter_summary)}")
                else:
                    st.info("🌐 **Testing against all available patterns**")
                
                st.markdown("---")
            
            # Analysis section
            st.markdown("#### Genie Pattern Analysis")
            if total_patterns > 0:
                pattern_sources = []
                if workspace_patterns_count > 0:
                    pattern_sources.append(f"{workspace_patterns_count} workspace patterns")
                if shared_patterns_count > 0:
                    pattern_sources.append(f"{shared_patterns_count} shared patterns")
                
                sources_text = " and ".join(pattern_sources)
                st.markdown(f"Click the button below to identify patterns using **{total_patterns} patterns** ({sources_text}).")
            else:
                st.markdown("Pattern identification will be available once you save patterns to your workspace or shared library.")

            # Analysis button
            analysis_col1, analysis_col2 = st.columns([2, 1])
            with analysis_col1:
                analysis_clicked = st.button(
                    "Start Pattern Analysis", 
                    type="primary", 
                    use_container_width=True,
                    disabled=(total_patterns == 0),
                    help="Requires saved patterns in workspace or shared library" if total_patterns == 0 else "Analyze XML against saved patterns"
                )
            
            with analysis_col2:
                if total_patterns == 0:
                    st.error("No Patterns Available")
                elif unknown_source_xml:
                    st.success(f"Ready for Analysis ({total_patterns} patterns)")
                else:
                    st.info("Upload XML first")
            
            # Initialize XML content variable
            unknown_source_xml_content = None
            
            if analysis_clicked:
                    
                    with st.status("**Analyzing XML Patterns...**", expanded=True) as status:
                        st.write("Reading XML structure...")
                        
                        unknown_source_xml_content = unknown_source_xml.read().decode("utf-8")
                        
                        # Apply filters if specified
                        filter_info = {"airlines": airline_filter, "versions": version_filter} if total_patterns > 0 else {"airlines": None, "versions": None}
                        
                        st.write("Genie is analyzing patterns...")
                        analysis = self._pattern_identify_manager.verify_and_confirm_airline(unknown_source_xml_content, filter_info)
                        
                        if analysis:
                            status.update(label="**Analysis Complete!**", state="complete")
                            
                            # Store analysis and XML content in session state for display outside status block
                            st.session_state.current_analysis = analysis
                            st.session_state.current_xml_content = unknown_source_xml_content
                        else:
                            status.update(label="**Analysis Issues**", state="error")
                            st.warning("Unable to complete pattern analysis. Please check your XML file.")
            
            # Display the analysis results outside the status block for full width
            if hasattr(st.session_state, 'current_analysis') and st.session_state.current_analysis:
                st.markdown("---")
                
                # Display results header with full width
                st.markdown("""
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0;">
                    <h3 style="margin: 0; color: #1f2937; font-weight: 700; font-size: 1.5rem;">Pattern Analysis Results</h3>
                    <span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600;">Genie Generated</span>
                </div>
                """, unsafe_allow_html=True)
                
                if self._pattern_identify_manager:
                    self._pattern_identify_manager.display_api_analysis(st.session_state.current_analysis)
                else:
                    st.success(f"**Analysis Complete:** {st.session_state.current_analysis}")
                
                # Get XML content from session state (with fallback)
                xml_content = getattr(st.session_state, 'current_xml_content', None)
                
                # Add floating chatbot dialog
                self._render_floating_chatbot(st.session_state.current_analysis, xml_content)

        else:
            # Premium empty state
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; margin: 3rem 0; padding: 3rem 2rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px;">
                <h3 style="margin: 0 0 1rem 0; color: #1e40af; font-weight: 700;">Ready to Identify Patterns?</h3>
                <p style="margin: 0 0 2rem 0; color: #3b82f6; font-size: 1.1rem; line-height: 1.6;">
                    Upload your XML file above to begin intelligent pattern identification and analysis!
                </p>
                <div style="display: flex; justify-content: center; gap: 1rem; margin: 2rem 0;">
                    <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Smart Detection</span>
                    <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Detailed Analysis</span>
                    <span style="background: #60a5fa !important; color: white !important; color: #ffffff !important; -webkit-text-fill-color: white !important; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Instant Results</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_pattern_library(self):
        """Pattern library showing all patterns in a single view"""
        
        # Add animated background
        st.markdown('<div class="animated-bg-pattern"></div>', unsafe_allow_html=True)

        try:
            # Get extracted patterns from session state
            extracted_patterns = getattr(st.session_state, 'pattern_responses', {})
            
            # Get shared patterns from default patterns manager
            from core.database.default_patterns_manager import DefaultPatternsManager
            default_patterns_manager = DefaultPatternsManager()
            shared_patterns = default_patterns_manager.get_all_patterns()
            
            # Get database patterns (user saved patterns)
            database_results = self.db_utils.get_all_patterns()
            
            # Render all patterns in single view
            self._render_all_patterns_view(extracted_patterns, shared_patterns, database_results)

        except Exception as e:
            st.error(f"Error loading pattern library: {str(e)}")
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; padding: 2rem;">
                <h4 style="margin: 0 0 1rem 0; color: #ef4444;">Database Connection Issue</h4>
                <p style="margin: 0; color: #6b7280;">Please check your database connection and try again.</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_all_patterns_view(self, extracted_patterns, shared_patterns, database_results):
        """Render saved patterns only (shared and database patterns)"""
        # Count only saved patterns (exclude extracted/session patterns)
        total_shared = len(shared_patterns)
        total_database = len(database_results) if database_results else 0
        total_patterns = total_shared + total_database
        
        if total_patterns > 0:
            st.markdown("### 📚 Saved Pattern Library")
            st.info(f"**Saved Patterns:** {total_patterns} patterns from shared workspace and saved databases")
            
            # Saved patterns metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Saved", total_patterns)
            with col2:
                st.metric("Shared Workspace", total_shared)
            with col3:
                st.metric("Custom Patterns", total_database)
            
            # Create combined DataFrame for filtering and display (saved patterns only)
            combined_data = []
            
            # Add shared patterns (these are saved)
            for pattern in shared_patterns:
                # Use API and API Version if available, otherwise use fallback values
                airline = pattern.api or "Shared"
                api_version = pattern.api_version or "N/A"
                
                combined_data.append({
                    "Source": "Shared Workspace",
                    "Name": pattern.name,
                    "Category": (pattern.category or 'uncategorized').replace('_', ' ').title(),
                    "Airline": airline,
                    "API Version": api_version,
                    "XPath": pattern.xpath,
                    "Description": pattern.description or "No description"
                })
            
            # Add database patterns (these are saved)
            if database_results:
                for result in database_results:
                    api_name, api_version, section_name, pattern_desc, pattern_prompt = result
                    # Convert section_name (XPath) to a more readable category
                    category = self._xpath_to_category(section_name)
                    combined_data.append({
                        "Source": f"Custom ({api_name})",
                        "Name": f"Pattern from {section_name}",
                        "Category": category,
                        "Airline": api_name,
                        "API Version": api_version or "N/A",
                        "XPath": section_name,
                        "Description": pattern_desc or "No description"
                    })
            
            if combined_data:
                df = pd.DataFrame(combined_data)
                
                # Filtering widgets
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sources = st.multiselect("🔍 Filter by Source", 
                                           options=df['Source'].unique(), 
                                           default=df['Source'].unique())
                
                with col2:
                    categories = st.multiselect("📁 Filter by Category", 
                                              options=sorted(df['Category'].unique()), 
                                              default=sorted(df['Category'].unique()))
                
                with col3:
                    airlines = st.multiselect("✈️ Filter by Airline", 
                                            options=sorted(df['Airline'].unique()), 
                                            default=sorted(df['Airline'].unique()))
                
                # Apply filters
                filtered_df = df[
                    (df['Source'].isin(sources)) & 
                    (df['Category'].isin(categories)) & 
                    (df['Airline'].isin(airlines))
                ]
                
                st.info(f"Showing {len(filtered_df)} of {len(df)} saved patterns")
                
                # Reorder columns for better display
                column_order = ["Source", "Name", "Category", "Airline", "API Version", "XPath", "Description"]
                filtered_df = filtered_df[column_order]
                
                # Display filtered results
                long_text_cols = ["Description", "XPath"]
                from core.common.css_utils import get_css_path
                css_path = get_css_path()
                render_custom_table(filtered_df, long_text_cols, css_path)
                
                # Export options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📄 Export Saved Patterns", type="primary", use_container_width=True):
                        csv_data = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name="saved_pattern_library.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col2:
                    if st.button("🔄 Refresh Library", type="primary", use_container_width=True):
                        st.rerun()
        else:
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; padding: 3rem 2rem;">
                <h3 style="margin: 0 0 1rem 0; color: #374151; font-weight: 700;">No Saved Patterns Found</h3>
                <p style="margin: 0 0 2rem 0; color: #6b7280; font-size: 1.1rem; line-height: 1.6;">
                    Save patterns from the Discovery page to see them in this library.
                </p>
                <div style="display: flex; justify-content: center; gap: 1rem;">
                    <span style="background: #3b82f6; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);">Extract & Save Patterns</span>
                    <span style="background: #60a5fa; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Use Discovery Page</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _xpath_to_category(self, xpath):
        """Convert XPath to a more readable category name"""
        if not xpath:
            return "Unknown"
        
        xpath_lower = xpath.lower()
        
        # Map common XPath patterns to categories
        if any(term in xpath_lower for term in ['passenger', 'pax', 'traveler']):
            return "Passenger"
        elif any(term in xpath_lower for term in ['flight', 'segment', 'itinerary']):
            return "Flight"
        elif any(term in xpath_lower for term in ['fare', 'price', 'cost', 'fee']):
            return "Fare"
        elif any(term in xpath_lower for term in ['booking', 'reservation', 'pnr']):
            return "Booking"
        elif any(term in xpath_lower for term in ['airline', 'carrier']):
            return "Airline"
        else:
            # Extract the main element name from XPath
            parts = xpath.strip('/').split('/')
            if parts:
                main_element = parts[-1] if parts[-1] else (parts[-2] if len(parts) > 1 else "Unknown")
                return main_element.replace('_', ' ').title()
            return "Custom"
    
    def _get_available_airlines_and_versions(self):
        """Get available airlines and API versions from workspace and shared patterns"""
        airlines = set()
        versions = set()
        
        try:
            # Get workspace patterns
            if self.db_utils:
                workspace_patterns = self.db_utils.get_all_patterns()
                for pattern in workspace_patterns:
                    if hasattr(pattern, 'airline') and pattern.airline:
                        airlines.add(pattern.airline)
                    if hasattr(pattern, 'api_version') and pattern.api_version:
                        versions.add(pattern.api_version)
            
            # Get shared patterns
            from core.database.default_patterns_manager import DefaultPatternsManager
            default_patterns_manager = DefaultPatternsManager()
            shared_patterns = default_patterns_manager.get_all_patterns()
            
            for pattern in shared_patterns:
                if pattern.api and pattern.api != "Shared":
                    airlines.add(pattern.api)
                if pattern.api_version and pattern.api_version != "N/A":
                    versions.add(pattern.api_version)
            
        except Exception as e:
            st.error(f"Error loading pattern options: {e}")
            
        # Convert to sorted lists, removing empty values
        airlines_list = sorted([a for a in airlines if a and a.strip()])
        versions_list = sorted([v for v in versions if v and v.strip()])
        
        return airlines_list, versions_list
    
    def _render_floating_chatbot(self, analysis_results, xml_content):
        """Render floating chatbot dialog in bottom right corner - DISABLED, using Streamlit fallback"""
        
        # Initialize chat state
        if 'chatbot_messages' not in st.session_state:
            st.session_state.chatbot_messages = []
        if 'chatbot_open' not in st.session_state:
            st.session_state.chatbot_open = False
        
        # Use Streamlit fallback instead of floating dialog to avoid HTML rendering issues
        self._handle_streamlit_chat_logic(analysis_results, xml_content)
        return
        
        # Floating chat CSS and HTML
        st.markdown("""
        <style>
        .floating-chat-toggle {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            color: white;
            border: none;
            border-radius: 20px;
            width: 250px;
            height: 70px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 8px 40px rgba(139, 69, 19, 0.5);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .floating-chat-toggle:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 50px rgba(139, 69, 19, 0.6);
            background: linear-gradient(135deg, #A0522D 0%, #CD853F 100%);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .floating-chat-toggle:active {
            transform: translateY(-1px) scale(1.01);
        }
        
        .floating-chat-toggle::before {
            content: '🤖';
            font-size: 24px;
            animation: pulse 2s infinite ease-in-out;
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.1);
            }
        }
        
        .floating-chat-dialog {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 400px;
            max-width: 90vw;
            height: 500px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 999;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #e5e7eb;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-close {
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 16px;
            background: #f9fafb;
            max-height: 350px;
            min-height: 200px;
            scroll-behavior: smooth;
        }
        
        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        
        .chat-input-area {
            padding: 16px;
            border-top: 1px solid #e5e7eb;
            background: white;
        }
        
        .user-message {
            background: #e0f2fe;
            color: #0f172a;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 12px 0;
            margin-left: 2rem;
            font-size: 14px;
            border-left: 3px solid #0ea5e9;
        }
        
        .bot-message {
            background: #f0f9ff;
            color: #1e293b;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 12px 0;
            margin-right: 2rem;
            border-left: 3px solid #0ea5e9;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .message-label {
            font-weight: 600;
            margin-bottom: 4px;
            display: block;
        }
        
        .user-label {
            color: #0369a1;
        }
        
        .bot-label {
            color: #0369a1;
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }
        
        .quick-btn {
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 16px;
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-btn:hover {
            background: #e5e7eb;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Chat toggle button
        chat_toggle_html = f"""
        <button class="floating-chat-toggle" onclick="toggleChat()" id="chatToggle">
            Ask Genie About Results
        </button>
        """
        
        # Chat dialog HTML
        chat_dialog_html = f"""
        <div class="floating-chat-dialog" id="chatDialog" style="display: {'block' if st.session_state.chatbot_open else 'none'};">
            <div class="chat-header">
                <span>🤖 Ask Genie About Results</span>
                <button class="chat-close" onclick="toggleChat()">×</button>
            </div>
            <div class="chat-messages" id="chatMessages">
                {self._render_chat_messages()}
            </div>
            <div class="chat-input-area">
                <div class="quick-actions">
                    <button class="quick-btn" onclick="askQuickQuestion('Analysis summary?')">Summary</button>
                    <button class="quick-btn" onclick="askQuickQuestion('Data quality?')">Quality</button>
                </div>
            </div>
        </div>
        """
        
        # JavaScript for chat functionality
        chat_js = """
        <script>
        function toggleChat() {
            const dialog = document.getElementById('chatDialog');
            const isVisible = dialog.style.display !== 'none';
            dialog.style.display = isVisible ? 'none' : 'block';
            
            // Scroll to bottom when opening chat
            if (!isVisible) {
                setTimeout(() => {
                    scrollToBottom();
                }, 100);
            }
            
            // Update Streamlit session state
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                key: 'chatbot_open',
                value: !isVisible
            }, '*');
        }
        
        function askQuickQuestion(question) {
            // Send quick question to Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue', 
                key: 'quick_question_asked',
                value: question
            }, '*');
            
            // Scroll to bottom after asking question
            setTimeout(() => {
                scrollToBottom();
            }, 500);
        }
        
        function scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
        
        // Auto-scroll to bottom when new messages are added
        function observeMessages() {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                const observer = new MutationObserver(() => {
                    scrollToBottom();
                });
                observer.observe(chatMessages, { childList: true, subtree: true });
            }
        }
        
        // Initialize message observer when dialog is ready
        document.addEventListener('DOMContentLoaded', function() {
            observeMessages();
        });
        
        // Also initialize after a short delay for dynamic content
        setTimeout(() => {
            observeMessages();
        }, 1000);
        </script>
        """
        
        # Render the floating chat
        st.components.v1.html(
            chat_toggle_html + chat_dialog_html + chat_js,
            height=0,
            scrolling=False
        )
        
        # Handle Streamlit-based chat functionality
        self._handle_streamlit_chat_logic(analysis_results, xml_content)
    
    def _render_chat_messages(self):
        """Render chat messages as HTML with improved styling"""
        messages_html = ""
        for message in st.session_state.chatbot_messages:
            if message["role"] == "user":
                # Escape HTML in user messages to prevent issues
                content = message["content"].replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                messages_html += f'''
                <div class="user-message">
                    <span class="message-label user-label">You:</span>
                    {content}
                </div>
                '''
            else:
                # For bot messages, convert markdown-style formatting to HTML but escape dangerous HTML
                content = message["content"]
                # Convert **bold** to <strong> using regex for proper pairing
                import re
                content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
                # Convert line breaks
                content = content.replace('\n', '<br>')
                # Only escape dangerous HTML tags, not formatting ones
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.IGNORECASE | re.DOTALL)
                # Remove div tags and other HTML elements that should not be displayed as raw HTML
                content = re.sub(r'<div[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'</div>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'<h[1-6][^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'</h[1-6]>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'<p[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'</p>', '', content, flags=re.IGNORECASE)
                # Remove any remaining unmatched ** or other problematic characters
                content = content.replace('**', '')
                
                messages_html += f'''
                <div class="bot-message">
                    <span class="message-label bot-label">🤖 Genie:</span>
                    {content}
                </div>
                '''
        
        if not st.session_state.chatbot_messages:
            messages_html = '''
            <div style="text-align: center; color: #6b7280; padding: 30px; font-style: italic;">
                <div style="font-size: 24px; margin-bottom: 10px;">💬</div>
                Start a conversation by clicking a quick action button or asking your own question!
            </div>
            '''
        
        return messages_html
    
    def _handle_streamlit_chat_logic(self, analysis_results, xml_content):
        """Handle chat logic using Streamlit components"""
        
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
            if st.button("🤖 Ask Genie About Results", key="chat_toggle_btn", help="Open intelligent chat to discuss analysis results", use_container_width=True):
                st.session_state.chatbot_open = not st.session_state.get('chatbot_open', False)
        
        # Show chat interface when open
        if st.session_state.get('chatbot_open', False):
            with st.container():
                st.markdown("### 🤖 Chat with Genie")
                
                # Quick action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Summary", key="q_summary", use_container_width=True):
                        st.session_state.quick_question = "Analysis summary?"
                
                with col2:
                    if st.button("Quality", key="q_quality", use_container_width=True):
                        st.session_state.quick_question = "Data quality?"
                
                # Chat messages display using native Streamlit components (no HTML)
                if st.session_state.chatbot_messages:
                    # Create a container for messages with custom styling
                    with st.container():
                        st.markdown("**💬 Conversation History:**")
                        
                        # Display messages using native Streamlit components
                        for i, message in enumerate(st.session_state.chatbot_messages):
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
                                # Convert **bold** to Streamlit markdown
                                # Keep **bold** as is since Streamlit handles it natively
                                
                                with st.container():
                                    st.markdown(f"**🤖 Genie:** {content}")
                            
                            # Add separator between messages
                            if i < len(st.session_state.chatbot_messages) - 1:
                                st.markdown("---")
                else:
                    st.info("💬 No messages yet. Start a conversation by clicking a quick action or asking a question!")
                
                # Chat input
                chat_input = st.text_input("Ask a question:", key="chat_input", placeholder="e.g., Which airlines were found?")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("Send", key="send_chat"):
                        if chat_input:
                            st.session_state.quick_question = chat_input
                
                with col2:
                    if st.button("Clear", key="clear_chat"):
                        st.session_state.chatbot_messages = []
                        st.rerun()
                
                with col3:
                    if st.button("Close Chat", key="close_chat"):
                        st.session_state.chatbot_open = False
                        st.rerun()
        
        # Process quick questions
        if hasattr(st.session_state, 'quick_question'):
            question = st.session_state.quick_question
            del st.session_state.quick_question
            
            # Add user message
            st.session_state.chatbot_messages.append({"role": "user", "content": question})
            
            # Generate response
            response = self._generate_chatbot_response(question, analysis_results, xml_content)
            st.session_state.chatbot_messages.append({"role": "bot", "content": response})
            
            st.rerun()
    
    def _generate_chatbot_response(self, question, analysis_results, xml_content):
        """Generate chatbot response based on the question and analysis results"""
        try:
            # Prepare context for the chatbot
            context = {
                "question": question,
                "analysis_results": str(analysis_results)[:2000],  # Limit context size
                "xml_sample": xml_content[:1000] if xml_content else "No XML content available"  # First 1000 chars
            }
            
            # Use the pattern identify manager to generate a contextual response
            if self._pattern_identify_manager:
                response = self._pattern_identify_manager.generate_chatbot_response(
                    question, 
                    analysis_results, 
                    xml_content
                )
                
                if response:
                    return response
            
            # Fallback response generation based on question analysis
            return self._generate_fallback_response(question, analysis_results, xml_content)
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
    
    def _generate_fallback_response(self, question, analysis_results, xml_content):
        """Generate a fallback response when the main chatbot fails"""
        question_lower = question.lower()
        
        # Airline-related questions
        if any(word in question_lower for word in ['airline', 'carrier', 'airlines', 'matched']):
            return self._analyze_airlines_in_results(analysis_results)
        
        # Pattern-related questions
        elif any(word in question_lower for word in ['pattern', 'patterns', 'found', 'identified']):
            return self._analyze_patterns_in_results(analysis_results)
        
        # Summary questions
        elif any(word in question_lower for word in ['summary', 'overview', 'results']):
            return self._generate_summary_response(analysis_results)
        
        # Data quality questions
        elif any(word in question_lower for word in ['quality', 'complete', 'missing', 'data']):
            return self._analyze_data_quality(analysis_results, xml_content)
        
        # Default response
        else:
            return f"""I understand you're asking: "{question}"

Based on the analysis results available, I can help you with:
- Information about airlines and carriers identified
- Details about patterns that were matched
- Summary of the analysis results
- Data quality and completeness assessment

Could you please rephrase your question to be more specific about what aspect of the results you'd like to know about?"""

    def _analyze_airlines_in_results(self, analysis_results):
        """Analyze and return information about airlines in the results"""
        try:
            result_str = str(analysis_results).lower()
            
            # Look for common airline indicators
            airlines_found = []
            
            # Common airline codes and names to search for
            airline_indicators = [
                'american', 'delta', 'united', 'southwest', 'jetblue', 
                'alaska', 'spirit', 'frontier', 'hawaiian', 'allegiant',
                'lufthansa', 'british airways', 'air france', 'klm',
                'aa', 'dl', 'ua', 'wn', 'b6', 'as', 'nk', 'f9', 'ha', 'g4'
            ]
            
            for indicator in airline_indicators:
                if indicator in result_str:
                    airlines_found.append(indicator.upper())
            
            if airlines_found:
                unique_airlines = list(set(airlines_found))
                return f"Based on the analysis results, I found references to these airlines: {', '.join(unique_airlines)}. The pattern matching identified these carriers in your XML data."
            else:
                return "I couldn't identify specific airline names or codes in the current analysis results. The patterns may have matched structural elements rather than specific airline identifiers. You might want to check if your XML contains airline codes or carrier information in the raw data."
                
        except Exception as e:
            return f"I encountered an issue analyzing airline information: {str(e)}"

    def _analyze_patterns_in_results(self, analysis_results):
        """Analyze and return information about patterns in the results"""
        try:
            if isinstance(analysis_results, dict):
                pattern_count = len(analysis_results.get('matches', []))
                return f"The analysis found {pattern_count} pattern matches in your XML. These patterns represent different structural elements and data points that were successfully identified and categorized."
            else:
                return f"Pattern analysis completed. The results show various structural patterns were identified in your XML data: {str(analysis_results)[:200]}..."
                
        except Exception as e:
            return f"I encountered an issue analyzing pattern information: {str(e)}"

    def _generate_summary_response(self, analysis_results):
        """Generate a summary of the analysis results"""
        try:
            return f"""Here's a summary of your XML analysis:

📊 **Analysis Overview:**
The pattern identification process has completed and analyzed your XML structure against the available pattern library.

🎯 **Key Findings:**
{str(analysis_results)[:300]}...

💡 **Next Steps:**
- Review the detailed results above
- Check which patterns matched successfully  
- Consider saving successful patterns to your library
- Use the identified patterns for future XML processing

Would you like me to elaborate on any specific aspect of these results?"""
            
        except Exception as e:
            return f"I encountered an issue generating the summary: {str(e)}"

    def _analyze_data_quality(self, analysis_results, xml_content):
        """Analyze data quality and completeness"""
        try:
            xml_size = len(xml_content) if xml_content else 0
            
            quality_indicators = []
            
            if xml_size > 1000:
                quality_indicators.append("✅ Good data volume")
            elif xml_size > 500:
                quality_indicators.append("⚠️ Moderate data volume")
            else:
                quality_indicators.append("❌ Limited data volume")
            
            # Check for common completeness indicators
            if xml_content and any(tag in xml_content.lower() for tag in ['<passenger', '<flight', '<booking']):
                quality_indicators.append("✅ Contains key business entities")
            
            return f"""**Data Quality Assessment:**

📈 **Quality Indicators:**
{chr(10).join(quality_indicators)}

📊 **Analysis Results Quality:**
The pattern matching process completed and provided structured results. The quality of matches depends on how well your XML structure aligns with the saved patterns in your library.

💡 **Recommendations:**
- Ensure your XML follows standard airline industry formats
- Consider adding more patterns to your library for better coverage
- Review any unmatched sections for potential new pattern opportunities"""
            
        except Exception as e:
            return f"I encountered an issue analyzing data quality: {str(e)}"
    
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
    #                 API keys need to be configured before using pattern identification
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
    #     Please configure these keys to use pattern identification features.
    #     """)
    #     
    #     st.markdown("""
    #     ### 🔐 Next Steps
    #     
    #     1. Navigate to the **Configuration** page using the sidebar
    #     2. Configure your required API keys
    #     3. Return to this page to start identifying patterns
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

# Entry point for Streamlit
if __name__ == "__main__" or "streamlit" in sys.argv[0]:
    page = EnhancedIdentifyPatternsPage()
    page.render()
else:
    # For Streamlit multi-page apps
    page = EnhancedIdentifyPatternsPage()
    page.render()