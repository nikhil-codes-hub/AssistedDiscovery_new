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
        self._pattern_identify_manager = PatternIdentifyManager(GPT_4O)
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
            # Discovery Workspace Selection
            st.markdown("### 🎯 Discovery Workspace Selection")
            selected_use_case = self._usecase_manager.render_use_case_selector("identify_use_case")
            
            st.markdown("---")
            
            # Cost metrics
            self._cost_display_manager.render_cost_metrics()
        
        # Professional header
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-content">
                <h1 class="hero-title">📊 Pattern Identification Studio</h1>
                <p class="hero-subtitle">
                    🎯 Identify and analyze XML patterns using Genie recognition
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
            self._pattern_identify_manager = PatternIdentifyManager(GPT_4O, self.db_utils)

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
            # File info display
            st.success("File Ready for Analysis")
            
            # File metrics
            col1, col2, col3 = st.columns(3)
            
            file_name = unknown_source_xml.name[:20] + "..." if len(unknown_source_xml.name) > 20 else unknown_source_xml.name
            file_size = f"{unknown_source_xml.size / 1024:.1f} KB"
            
            with col1:
                st.metric("File Name", file_name)
            with col2:
                st.metric("File Size", file_size)
            with col3:
                st.metric("Analysis Status", "Ready")

            # Analysis section
            st.markdown("#### Genie Pattern Analysis")
            st.markdown("Click the button below to start pattern identification and structural analysis.")

            # Analysis button
            analysis_col1, analysis_col2 = st.columns([2, 1])
            with analysis_col1:
                analysis_clicked = st.button("Start Pattern Analysis", type="primary", use_container_width=True)
            
            with analysis_col2:
                if unknown_source_xml:
                    st.success("Ready for Analysis")
                else:
                    st.info("Upload XML first")
            
            if analysis_clicked:
                    
                    with st.status("**Analyzing XML Patterns...**", expanded=True) as status:
                        st.write("Reading XML structure...")
                        
                        unknown_source_xml_content = unknown_source_xml.read().decode("utf-8")
                        
                        st.write("Genie is analyzing patterns...")
                        analysis = self._pattern_identify_manager.verify_and_confirm_airline(unknown_source_xml_content, None)
                        
                        st.write("Generating insights...")
                        
                        if analysis:
                            status.update(label="**Analysis Complete!**", state="complete")
                            
                            # Store analysis in session state for display outside status block
                            st.session_state.current_analysis = analysis
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
        """Render all patterns in a single unified view"""
        # Count all patterns
        total_extracted = len(extracted_patterns)
        total_shared = len(shared_patterns)
        total_database = len(database_results) if database_results else 0
        total_patterns = total_extracted + total_shared + total_database
        
        if total_patterns > 0:
            st.markdown("### 📚 Pattern Library")
            st.info(f"**All Patterns:** {total_patterns} patterns from extracted, shared, and saved sources")
            
            # Combined metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Patterns", total_patterns)
            with col2:
                st.metric("Extracted", total_extracted)
            with col3:
                st.metric("Shared", total_shared)
            with col4:
                st.metric("Saved to DB", total_database)
            
            # Create combined DataFrame for filtering and display
            combined_data = []
            
            # Add extracted patterns
            for tag, pattern_data in extracted_patterns.items():
                combined_data.append({
                    "Source": "Extracted",
                    "Name": pattern_data.get('name', 'Unnamed Pattern'),
                    "Category": pattern_data.get('category', 'user_created').replace('_', ' ').title(),
                    "XPath": tag,
                    "Description": pattern_data.get('description', 'No description'),
                    "Status": "✅ Verified" if pattern_data.get('verified', False) else "⏳ Unverified"
                })
            
            # Add shared patterns
            for pattern in shared_patterns:
                combined_data.append({
                    "Source": "Shared",
                    "Name": pattern.name,
                    "Category": (pattern.category or 'uncategorized').replace('_', ' ').title(),
                    "XPath": pattern.xpath,
                    "Description": pattern.description or "No description",
                    "Status": "🌐 Shared"
                })
            
            # Add database patterns with proper category mapping
            if database_results:
                for result in database_results:
                    api_name, api_version, section_name, pattern_desc, pattern_prompt = result
                    # Convert section_name (XPath) to a more readable category
                    category = self._xpath_to_category(section_name)
                    combined_data.append({
                        "Source": f"Database ({api_name})",
                        "Name": f"Pattern from {section_name}",
                        "Category": category,
                        "XPath": section_name,
                        "Description": pattern_desc or "No description",
                        "Status": f"💾 Saved (v{api_version})"
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
                    statuses = st.multiselect("📊 Filter by Status", 
                                            options=df['Status'].unique(), 
                                            default=df['Status'].unique())
                
                # Apply filters
                filtered_df = df[
                    (df['Source'].isin(sources)) & 
                    (df['Category'].isin(categories)) & 
                    (df['Status'].isin(statuses))
                ]
                
                st.info(f"Showing {len(filtered_df)} of {len(df)} patterns")
                
                # Display filtered results
                long_text_cols = ["Description", "XPath"]
                from core.common.css_utils import get_css_path
                css_path = get_css_path()
                render_custom_table(filtered_df, long_text_cols, css_path)
                
                # Export options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📄 Export Filtered Results", type="primary", use_container_width=True):
                        csv_data = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name="pattern_library.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col2:
                    if st.button("🔄 Refresh Library", type="primary", use_container_width=True):
                        st.rerun()
        else:
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; padding: 3rem 2rem;">
                <h3 style="margin: 0 0 1rem 0; color: #374151; font-weight: 700;">Pattern Library is Empty</h3>
                <p style="margin: 0 0 2rem 0; color: #6b7280; font-size: 1.1rem; line-height: 1.6;">
                    Start by extracting patterns in the Discovery page to build your library.
                </p>
                <div style="display: flex; justify-content: center; gap: 1rem;">
                    <span style="background: #3b82f6; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);">Extract Patterns</span>
                    <span style="background: #60a5fa; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);">Save to Shared</span>
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