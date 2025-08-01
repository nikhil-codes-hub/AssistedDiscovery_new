"""
Configuration Page for Assisted Discovery

This page allows users to configure Azure OpenAI settings for GPT-4o or o3-mini models.
"""

import streamlit as st
import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.common.env_manager import EnvManager, EnvVariable

st.set_page_config(
    page_title="Configuration Studio",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load modern CSS styling
def load_css():
    """Load CSS styling for the configuration page."""
    try:
        from core.common.streamlit_css_loader import load_streamlit_css
        load_streamlit_css()
    except ImportError:
        # Fallback styling
        st.markdown("""
        <style>
        .hero-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 0;
        }
        .config-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
            border-left: 4px solid #667eea;
        }
        .status-card {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .status-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        </style>
        """, unsafe_allow_html=True)

def main():
    """Main configuration page."""
    
    # Load CSS
    load_css()
    
    # Page header with hero banner
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-content">
            <h1 class="hero-title">⚙️ Configuration Studio</h1>
            <p class="hero-subtitle">
                🚀 Set up your AI models and get ready to discover patterns
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Model selection card
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    st.markdown("### 🤖 **AI Model Configuration**")
    
    model_choice = st.radio(
        "",
        ["GPT-4o", "o3-mini"],
        horizontal=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Azure OpenAI configuration card
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 **Azure OpenAI Configuration**")
    st.markdown("Enter your Azure OpenAI credentials to connect your AI model")
    
    with st.form("azure_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            azure_key = st.text_input(
                "🔐 Azure OpenAI Key",
                type="password",
                help="Your Azure OpenAI API key",
                placeholder="Enter your API key..."
            )
        
        with col2:
            azure_endpoint = st.text_input(
                "🌐 Azure OpenAI Endpoint",
                placeholder="https://your-resource.openai.azure.com/",
                help="Your Azure OpenAI endpoint URL"
            )
        
        # Auto-fill based on model choice
        if model_choice == "GPT-4o":
            api_version = "2025-01-01-preview"
            model_deployment = "gpt-4o"
        else:  # o3-mini
            api_version = "2024-12-01-preview"
            model_deployment = "o3-mini"
        
        # Auto-configuration info
        st.info(f"**🔧 Auto-configured for {model_choice}:** API Version `{api_version}` | Model `{model_deployment}`")
        
        # Save button
        col_save, col_space = st.columns([1, 3])
        with col_save:
            save_clicked = st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True)
        
        if save_clicked:
            if not azure_key or not azure_endpoint:
                st.error("❌ Please fill in all required fields")
            else:
                # Save configuration
                success = save_azure_config(model_choice, azure_key, azure_endpoint, api_version, model_deployment)
                if success:
                    st.success("✅ Configuration saved successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to save configuration")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Current configuration status card
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    st.markdown("### 📊 **Configuration Status**")
    st.markdown("Check your current AI model configurations")
    
    env_manager = EnvManager()
    env_vars = env_manager.load_env_variables()
    
    # Check what's configured
    gpt4o_configured = all(key in env_vars for key in [
        "GPT4O_AZURE_OPENAI_KEY", "GPT4O_AZURE_OPENAI_ENDPOINT", 
        "GPT4O_AZURE_API_VERSION", "GPT4O_MODEL_DEPLOYMENT_NAME"
    ])
    
    o3_configured = all(key in env_vars for key in [
        "o3_mini_AZURE_OPENAI_KEY", "o3_mini_AZURE_OPENAI_ENDPOINT",
        "o3_mini_AZURE_API_VERSION", "o3_mini_MODEL_DEPLOYMENT_NAME"
    ])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if gpt4o_configured:
            st.markdown(
                '<div class="status-card status-success">✅ <strong>GPT-4o</strong><br/>Configuration Complete</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-card status-warning">⚠️ <strong>GPT-4o</strong><br/>Configuration Incomplete</div>',
                unsafe_allow_html=True
            )
    
    with col2:
        if o3_configured:
            st.markdown(
                '<div class="status-card status-success">✅ <strong>o3-mini</strong><br/>Configuration Complete</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-card status-warning">⚠️ <strong>o3-mini</strong><br/>Configuration Incomplete</div>',
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Test configuration card
    if gpt4o_configured or o3_configured:
        st.markdown('<div class="config-card">', unsafe_allow_html=True)
        st.markdown("### 🧪 **Test Your Configuration**")
        st.markdown("Verify that your AI model is working correctly")
        
        col_test, col_space = st.columns([1, 3])
        with col_test:
            if st.button("🧪 Test Connection", type="secondary", use_container_width=True):
                test_azure_connection(model_choice, env_vars)
        
        st.markdown('</div>', unsafe_allow_html=True)

def save_azure_config(model_choice, azure_key, azure_endpoint, api_version, model_deployment):
    """Save Azure OpenAI configuration to .env file."""
    try:
        env_manager = EnvManager()
        
        # Determine prefix based on model choice
        if model_choice == "GPT-4o":
            prefix = "GPT4O"
        else:
            prefix = "o3_mini"
        
        # Create environment variables
        config_vars = {
            f"{prefix}_AZURE_OPENAI_KEY": EnvVariable(
                key=f"{prefix}_AZURE_OPENAI_KEY",
                value=azure_key,
                comment=f"# Azure OpenAI API Key for {model_choice}",
                is_commented=False,
                group="Azure OpenAI"
            ),
            f"{prefix}_AZURE_OPENAI_ENDPOINT": EnvVariable(
                key=f"{prefix}_AZURE_OPENAI_ENDPOINT",
                value=azure_endpoint,
                comment=f"# Azure OpenAI Endpoint for {model_choice}",
                is_commented=False,
                group="Azure OpenAI"
            ),
            f"{prefix}_AZURE_API_VERSION": EnvVariable(
                key=f"{prefix}_AZURE_API_VERSION",
                value=api_version,
                comment=f"# Azure API Version for {model_choice}",
                is_commented=False,
                group="Azure OpenAI"
            ),
            f"{prefix}_MODEL_DEPLOYMENT_NAME": EnvVariable(
                key=f"{prefix}_MODEL_DEPLOYMENT_NAME",
                value=model_deployment,
                comment=f"# Model Deployment Name for {model_choice}",
                is_commented=False,
                group="Azure OpenAI"
            )
        }
        
        # Load existing variables and update with new ones
        existing_vars = env_manager.load_env_variables()
        existing_vars.update(config_vars)
        
        # Save all variables
        return env_manager.save_env_variables(existing_vars)
        
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False

def create_azure_client(api_key, endpoint, api_version):
    """Create an Azure OpenAI client for testing."""
    try:
        from openai import AzureOpenAI
        import httpx
        
        # Create client with SSL verification disabled (like in llm_utils)
        httpx_client = httpx.Client(verify=False)
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            http_client=httpx_client
        )
        
        return client
    except Exception as e:
        raise Exception(f"Failed to create Azure OpenAI client: {str(e)}")

def test_chat_completion(client, model_name):
    """Test chat completion with the Azure OpenAI client."""
    try:
        # Create test messages
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, test successful!' in exactly 4 words."}
        ]
        
        # Make the API call
        response = client.chat.completions.create(
            model=model_name,
            messages=test_messages,
            temperature=0,
            max_tokens=10
        )
        
        return response
    except Exception as e:
        raise Exception(f"Chat completion failed: {str(e)}")

def test_azure_connection(model_choice, env_vars):
    """Test Azure OpenAI connection using a separate testing method."""
    try:
        # Determine which configuration to test
        if model_choice == "GPT-4o":
            prefix = "GPT4O"
        else:
            prefix = "o3_mini"
        
        key_name = f"{prefix}_AZURE_OPENAI_KEY"
        endpoint_name = f"{prefix}_AZURE_OPENAI_ENDPOINT"
        version_name = f"{prefix}_AZURE_API_VERSION"
        deployment_name = f"{prefix}_MODEL_DEPLOYMENT_NAME"
        
        # Check if required variables exist
        required_vars = [key_name, endpoint_name, version_name, deployment_name]
        missing_vars = [var for var in required_vars if var not in env_vars]
        
        if missing_vars:
            st.error(f"❌ {model_choice} configuration incomplete. Missing: {', '.join(missing_vars)}")
            return
        
        with st.spinner(f"Testing {model_choice} connection..."):
            try:
                # Get configuration values
                api_key = env_vars[key_name].value
                endpoint = env_vars[endpoint_name].value
                api_version = env_vars[version_name].value
                model_name = env_vars[deployment_name].value
                
                # Create Azure OpenAI client
                client = create_azure_client(api_key, endpoint, api_version)
                
                # Test the connection
                response = test_chat_completion(client, model_name)
                
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    st.success(f"✅ {model_choice} connection successful!")
                    st.info(f"**Test Response:** {response.choices[0].message.content}")
                    
                    # Show usage info if available
                    if hasattr(response, 'usage'):
                        usage = response.usage
                        st.caption(f"Tokens used: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
                        
                    # Show model info
                    st.caption(f"Model: {model_name} | API Version: {api_version}")
                else:
                    st.error(f"❌ {model_choice} connection failed: Invalid response format")
                        
            except Exception as e:
                st.error(f"❌ {model_choice} connection failed: {str(e)}")
                
                # Provide helpful error messages
                error_str = str(e).lower()
                if "unauthorized" in error_str or "401" in error_str:
                    st.warning("💡 **Authentication Error**: Please check your API key is correct and active.")
                elif "not found" in error_str or "404" in error_str:
                    st.warning("💡 **Resource Not Found**: Please verify your endpoint URL and model deployment name.")
                elif "quota" in error_str or "rate limit" in error_str:
                    st.warning("💡 **Quota/Rate Limit**: Your Azure OpenAI resource may have reached its limits.")
                elif "timeout" in error_str:
                    st.warning("💡 **Timeout Error**: The connection timed out. Please check your network or try again.")
                else:
                    st.warning("💡 **General Error**: Please verify all your Azure OpenAI configuration details.")
                
    except Exception as e:
        st.error(f"Error testing connection: {str(e)}")

if __name__ == "__main__":
    main()