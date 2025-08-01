"""
Streamlit CSS loader with enhanced reliability for different environments.
"""
import os
import streamlit as st


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_css_content():
    """
    Get CSS content with caching to improve performance.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(current_dir, "../../app/css/table_styles.css"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "app/css/table_styles.css"),
        "app/css/table_styles.css",
        "./app/css/table_styles.css",
    ]
    
    for css_path in possible_paths:
        if os.path.exists(css_path):
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(css_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except:
                    continue
            except:
                continue
    
    # Return fallback CSS if file not found
    return get_fallback_css()


def get_fallback_css():
    """
    Return essential CSS as a fallback when external file is not found.
    """
    return """
    /* Essential fallback CSS for tables and UI components */
    
    /* Global styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: linear-gradient(135deg, rgba(248, 250, 252, 0.8) 0%, rgba(241, 245, 249, 0.6) 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Enhanced page header */
    .main .block-container::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 50%, #3b82f6 100%);
        z-index: 1000;
    }
    
    /* Table styling */
    .custom-table-wrapper {
        border-radius: 8px;
        overflow: hidden;
        overflow-x: auto;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
        margin: 1rem 0;
        max-width: 100%;
        border: 1px solid #e5e7eb;
    }
    
    .custom-table-wrapper table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        min-width: 100%;
    }
    
    .custom-table-wrapper th {
        background: #3b82f6 !important;
        color: white !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.875rem;
        padding: 12px 16px;
        border: none;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    /* Force all text content in table headers to be white */
    .custom-table-wrapper th *,
    .custom-table-wrapper thead th *,
    table th *,
    [data-testid="stMarkdownContainer"] th *,
    .stMarkdown th * {
        color: white !important;
        -webkit-text-fill-color: white !important;
        text-shadow: none !important;
    }
    
    .custom-table-wrapper td {
        background-color: #ffffff;
        border-bottom: 1px solid #f3f4f6;
        padding: 12px 16px;
        color: #1f2937;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        line-height: 1.6;
    }
    
    .custom-table-wrapper tbody tr:hover td {
        background: rgba(59, 130, 246, 0.05) !important;
        color: #1f2937 !important;
    }
    
    /* Button styling */
    .stButton > button,
    button[kind="primary"],
    button[data-testid="baseButton-primary"],
    [data-testid="stButton"] button,
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: white !important;
        font-weight: 500 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px rgba(96, 165, 250, 0.25), 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        font-size: 0.875rem !important;
        letter-spacing: 0.025em !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
        color: #1e40af !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab"],
    .stTabs button[role="tab"],
    .stTabs div[role="tab"] {
        padding: 12px 24px !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        color: white !important;
        font-weight: 500 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        font-size: 0.875rem !important;
        letter-spacing: 0.025em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin: 0 5px !important;
    }
    
    .stTabs [data-baseweb="tab"] span,
    .stTabs button[role="tab"] span,
    .stTabs div[role="tab"] span {
        color: white !important;
    }
    
    .stTabs [aria-selected="true"],
    .stTabs button[aria-selected="true"],
    .stTabs div[aria-selected="true"] {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: white !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 4px 16px rgba(96, 165, 250, 0.4), 0 2px 8px rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border-radius: 16px !important;
        border: 2px dashed rgba(59, 130, 246, 0.3) !important;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.04) 0%, rgba(147, 197, 253, 0.04) 100%) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        padding: 2rem !important;
    }
    
    .stFileUploader > div:hover {
        border-color: rgba(59, 130, 246, 0.6) !important;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(147, 197, 253, 0.08) 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"], 
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.2) !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.02) !important;
    }
    
    /* Metrics styling */
    .stMetric {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%) !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(59, 130, 246, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stMetric:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15), 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Input styling */
    .stTextInput input,
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.05) !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), 0 4px 16px rgba(59, 130, 246, 0.1) !important;
        background: white !important;
        transform: translateY(-1px) !important;
    }
    """


def load_streamlit_css():
    """
    Load CSS for Streamlit with enhanced reliability.
    This function ensures CSS is loaded regardless of environment.
    """
    # Get CSS content (cached)
    css_content = get_css_content()
    
    # Apply CSS
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    
    # Mark as loaded in session state
    st.session_state.css_loaded = True