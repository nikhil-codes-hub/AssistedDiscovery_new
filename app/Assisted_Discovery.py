import streamlit as st
import sys
import os

st.set_page_config(
    page_title="Assisted Discovery Hub",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.common.cost_display_manager import CostDisplayManager
# from core.common.api_key_manager import APIKeyManager  # Temporarily disabled for demo
from core.common.logging_manager import (
    get_logger, log_user_action, log_error, log_streamlit_error, 
    setup_global_exception_handler, streamlit_error_handler
)

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

class AssistedDiscoveryHub:
    def __init__(self):
        self._cost_display_manager = CostDisplayManager()
        # self._api_manager = APIKeyManager()  # Temporarily disabled for demo
        self.logger = get_logger("main_hub")

    @streamlit_error_handler
    def render(self):
        """
        Main Assisted Discovery Hub with professional UI/UX.
        """
        self.logger.info("Rendering main discovery hub")
        log_user_action("main_hub_accessed", "User accessed main discovery hub")
        
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
            self.logger.error(f"Failed to load CSS: {e}")
            log_streamlit_error(e, "CSS loading failed")
            # Don't re-raise for CSS loading failure
        
        # Professional header
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-content">
                <h1 class="hero-title">Assisted Discovery Hub</h1>
                <p class="hero-subtitle">
                    XML pattern discovery and analysis platform
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Available Tools
        st.markdown("### Available Tools")
        
        # Create navigation cards
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; padding: 1.5rem;">
                <h3 style="margin: 0 0 1rem 0; color: #1f2937; font-weight: 600;">Pattern Discovery</h3>
                <p style="margin: 0; color: #6b7280; font-size: 0.9rem; line-height: 1.5;">
                    Extract meaningful patterns from XML files using AI-powered discovery engine.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="enhanced-section-card" style="text-align: center; padding: 1.5rem;">
                <h3 style="margin: 0 0 1rem 0; color: #1f2937; font-weight: 600;">Pattern Identification</h3>
                <p style="margin: 0; color: #6b7280; font-size: 0.9rem; line-height: 1.5;">
                    Identify and analyze existing patterns in your XML files.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Features overview section
        st.markdown("---")
        st.markdown("### Platform Features")

        # Feature grid
        col1, col2, col3, col4 = st.columns(4)

        features = [
            ("AI-Powered", "Advanced machine learning algorithms"),
            ("Lightning Fast", "Optimized processing for large files"),
            ("High Accuracy", "Precise pattern extraction"),
            ("Secure", "Enterprise security standards")
        ]

        for i, (title, desc) in enumerate(features):
            with [col1, col2, col3, col4][i]:
                st.markdown(f"""
                <div class="enhanced-section-card" style="text-align: center; padding: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #1f2937; font-weight: 600;">{title}</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 0.8rem; line-height: 1.4;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)

        # Enhanced sidebar metrics
        with st.sidebar:
            self._cost_display_manager.render_cost_metrics()
    
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
    #                 API keys need to be configured before using the application
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
    #     Please configure these keys to use the application.
    #     """)
    #     
    #     st.markdown("""
    #     ### 🔐 Next Steps
    #     
    #     1. Navigate to the **Configuration** page using the sidebar
    #     2. Configure your required API keys
    #     3. Return to this page to start using the application
    #     
    #     The Configuration page provides:
    #     - Secure API key storage with encryption
    #     - Step-by-step setup guides
    #     - API key validation and testing
    #     """)
    #     
    #     # Quick access button
    #     st.markdown("---")
    #     col1, col2, col3 = st.columns([1, 2, 1])
    #     with col2:
    #         if st.button("🔧 Go to Configuration Page", type="primary", use_container_width=True):
    #             st.switch_page("pages/0_⚙️_Configuration.py")
    #     
    #     # Sidebar status
    #     with st.sidebar:
    #         self._api_manager.render_api_key_status()

# Entry point for Streamlit
if __name__ == "__main__":
    # Set up global exception handler for better error logging
    setup_global_exception_handler()
    
    hub = AssistedDiscoveryHub()
    hub.render()
else:
    # For Streamlit multi-page apps
    # Set up global exception handler for better error logging
    setup_global_exception_handler()
    
    hub = AssistedDiscoveryHub()
    hub.render()