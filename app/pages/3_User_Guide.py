import streamlit as st
import os

# Set page configuration
st.set_page_config(
    page_title="User Guide - AssistedDiscovery",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better formatting
st.markdown("""
<style>
    .user-guide-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .guide-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .guide-section {
        background: #f8f9fa;
        border-left: 4px solid #1e40af;
        padding: 20px;
        margin: 20px 0;
        border-radius: 5px;
    }
    
    .code-block {
        background: #f1f3f4;
        border: 1px solid #d1d5da;
        border-radius: 6px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        overflow-x: auto;
        margin: 10px 0;
    }
    
    .feature-list {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.1), rgba(59, 130, 246, 0.1));
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .toc-container {
        background: #ffffff;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .section-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 20px 0;
    }
    
    .nav-button {
        background: #1e40af;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        text-decoration: none;
        font-size: 14px;
        border: none;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: #1d4ed8;
        color: white;
        text-decoration: none;
    }
    
    .highlight-box {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(21, 128, 61, 0.1));
        border-left: 4px solid #22c55e;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1));
        border-left: 4px solid #f59e0b;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }
    
    .step-number {
        background: #1e40af;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="guide-header">
        <h1 style="color: white !important;">📖 AssistedDiscovery User Guide</h1>
        <p style="color: white !important;">Comprehensive documentation for AI-powered XML pattern analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Getting Started", 
        "🔍 Discovery", 
        "📊 Identification", 
        "⚙️ Advanced", 
        "❓ Help & FAQ"
    ])
    
    with tab1:
        render_getting_started()
    
    with tab2:
        render_discovery_guide()
    
    with tab3:
        render_identification_guide()
    
    with tab4:
        render_advanced_features()
    
    with tab5:
        render_help_faq()

def render_getting_started():
    st.markdown("## 🚀 Getting Started")
    
    # Introduction
    st.markdown("""
    <div class="guide-section">
        <h3>What is AssistedDiscovery?</h3>
        <p><strong>AssistedDiscovery</strong> is an intelligent XML pattern analysis application that leverages AI-powered pattern extraction and identification capabilities. The system uses GPT-4o to automatically discover, extract, verify, and manage XML patterns from various airline API responses.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Features
    st.markdown("""
    <div class="feature-list">
        <h3>🌟 Key Features</h3>
        <ul>
            <li><strong>🔍 AI-Powered Pattern Discovery</strong>: Automatically extract patterns from XML files using GPT-4o</li>
            <li><strong>⚡ Dual Extraction Modes</strong>: Choose between Auto Mode (fully automated) or Manual Mode (user-controlled targeting)</li>
            <li><strong>✅ Pattern Verification</strong>: Validate extracted patterns with AI assistance</li>
            <li><strong>💾 Dual Storage System</strong>: Save patterns to personal workspaces or shared team libraries</li>
            <li><strong>📊 Pattern Identification</strong>: Identify patterns in unknown XML files with airline/version filtering</li>
            <li><strong>🏢 Multi-API Support</strong>: Work with LATAM, LH, LHG, and AFKL airline APIs</li>
            <li><strong>📚 Pattern Library Management</strong>: Organize and filter patterns efficiently</li>
            <li><strong>🎯 Workspace-Based Organization</strong>: Separate patterns by use cases and projects</li>
            <li><strong>🤖 Interactive Chatbot</strong>: Ask Genie questions about analysis results and get intelligent responses</li>
            <li><strong>🎨 Modern UI</strong>: Clean, professional interface with enhanced user experience</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # System Requirements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="guide-section">
            <h3>💻 System Requirements</h3>
            <ul>
                <li><strong>Python</strong>: 3.8 or higher</li>
                <li><strong>Streamlit</strong>: 1.28.0 or higher</li>
                <li><strong>Azure OpenAI</strong>: Active subscription with GPT-4o deployment</li>
                <li><strong>Storage</strong>: Minimum 100MB for database files</li>
                <li><strong>Memory</strong>: 4GB RAM recommended</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="guide-section">
            <h3>🎯 Target Users</h3>
            <ul>
                <li><strong>Airline API Developers</strong>: Working with complex XML responses</li>
                <li><strong>Data Analysts</strong>: Analyzing XML structure patterns</li>
                <li><strong>QA Engineers</strong>: Validating XML data consistency</li>
                <li><strong>Integration Teams</strong>: Understanding API response formats</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Start Steps
    st.markdown("""
    <div class="highlight-box">
        <h3>⚡ Quick Start Steps</h3>
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <span class="step-number">1</span>
            <span>Configure Azure OpenAI credentials in the Configuration page</span>
        </div>
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <span class="step-number">2</span>
            <span>Create a workspace for your project</span>
        </div>
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <span class="step-number">3</span>
            <span>Upload XML files in the Discovery page to extract patterns</span>
        </div>
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <span class="step-number">4</span>
            <span>Use the Identify page to analyze unknown XML files</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_discovery_guide():
    st.markdown("## 🔍 Discovery Module Guide")
    
    st.markdown("""
    <div class="guide-section">
        <h3>Overview</h3>
        <p>The Discovery module is the core feature for extracting patterns from XML files using AI assistance. It provides five main tabs for a complete pattern extraction workflow.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto/Manual Mode Section
    st.markdown("""
    <div class="highlight-box">
        <h3>⚡ Pattern Extraction Modes</h3>
        <p>AssistedDiscovery offers two powerful extraction modes to suit different use cases:</p>
        
        <div style="margin: 20px 0;">
            <h4 style="color: #059669; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🚀</span> Auto Mode (Recommended)
            </h4>
            <ul>
                <li><strong>Fully Automated</strong>: AI automatically analyzes your XML and extracts all relevant patterns</li>
                <li><strong>Intelligent Detection</strong>: Uses GPT-4o to identify meaningful data structures and elements</li>
                <li><strong>Quick Results</strong>: Fast processing with comprehensive pattern discovery</li>
                <li><strong>Best For</strong>: New XML files, complete analysis, time-efficient workflows</li>
                <li><strong>Output</strong>: Complete set of patterns with AI-generated names and descriptions</li>
            </ul>
        </div>
        
        <div style="margin: 20px 0;">
            <h4 style="color: #3b82f6; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🎯</span> Manual Mode (Targeted)
            </h4>
            <ul>
                <li><strong>User-Controlled</strong>: You specify exactly which patterns to extract</li>
                <li><strong>Precise Targeting</strong>: Define custom XPath expressions for specific elements</li>
                <li><strong>Custom Descriptions</strong>: Provide your own pattern names and descriptions</li>
                <li><strong>Best For</strong>: Specific pattern extraction, custom requirements, expert users</li>
                <li><strong>Output</strong>: Targeted patterns based on your specifications</li>
            </ul>
        </div>
        
        <div style="background: rgba(245, 158, 11, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-top: 15px;">
            <p style="margin: 0; font-weight: 500; color: #92400e;"><strong>💡 Pro Tip:</strong> Start with Auto Mode to get a comprehensive overview, then use Manual Mode to extract specific patterns you need for your use case.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs explanation
    tab_col1, tab_col2 = st.columns(2)
    
    with tab_col1:
        st.markdown("""
        <div class="guide-section">
            <h4>📁 Extract Tab</h4>
            <ul>
                <li>Upload XML files</li>
                <li>Select API context (LATAM, LH, LHG, AFKL)</li>
                <li>Choose API version</li>
                <li>Start AI pattern extraction</li>
            </ul>
        </div>
        
        <div class="guide-section">
            <h4>✅ Verify Tab</h4>
            <ul>
                <li>Review extracted patterns</li>
                <li>Individual pattern verification</li>
                <li>Batch verification for multiple patterns</li>
                <li>Quality assurance checks</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tab_col2:
        st.markdown("""
        <div class="guide-section">
            <h4>💾 Save Tab</h4>
            <ul>
                <li>Save to personal workspace</li>
                <li>Save to shared team workspace</li>
                <li>Category assignment</li>
                <li>API configuration</li>
            </ul>
        </div>
        
        <div class="guide-section">
            <h4>⚙️ Manage Tabs</h4>
            <ul>
                <li>Manage Custom Patterns (personal)</li>
                <li>Manage Shared Patterns (team)</li>
                <li>Import/Export functionality</li>
                <li>Pattern organization</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Interactive Chatbot Feature
    st.markdown("""
    <div class="highlight-box">
        <h3>🤖 Genie Chatbot</h3>
        <p>After pattern extraction, use the <strong>"🤖 Ask Genie About Extraction"</strong> button to:</p>
        <ul>
            <li><strong>Extraction Summary</strong>: Get detailed summaries of extracted patterns</li>
            <li><strong>Pattern Quality Analysis</strong>: Understand extraction effectiveness</li>
            <li><strong>Next Steps Guidance</strong>: Get recommendations for verification and saving</li>
        </ul>
        <p><strong>Quick Actions:</strong></p>
        <ul>
            <li>"Can you summarize the pattern extraction results?"</li>
            <li>"How good are the extracted patterns?"</li>
            <li>"What should I do next with these patterns?"</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Best Practices
    st.markdown("""
    <div class="warning-box">
        <h4>📋 Best Practices</h4>
        <ul>
            <li><strong>File Size</strong>: Optimal XML files are 10KB-1MB</li>
            <li><strong>Structure</strong>: Well-formed XML produces better results</li>
            <li><strong>Content</strong>: Rich data yields more meaningful patterns</li>
            <li><strong>API Context</strong>: Correct API selection improves accuracy</li>
            <li><strong>Verification</strong>: Always verify patterns before saving</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_identification_guide():
    st.markdown("## 📊 Pattern Identification Guide")
    
    st.markdown("""
    <div class="guide-section">
        <h3>Overview</h3>
        <p>The Identify module helps you analyze unknown XML files by comparing them against your saved patterns using AI-powered analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Process Steps
    st.markdown("""
    <div class="highlight-box">
        <h3>🔄 Analysis Process</h3>
        <div style="display: flex; align-items: center; margin: 15px 0;">
            <span class="step-number">1</span>
            <span><strong>Select Workspace</strong>: Choose workspace containing relevant patterns</span>
        </div>
        <div style="display: flex; align-items: center; margin: 15px 0;">
            <span class="step-number">2</span>
            <span><strong>Upload XML</strong>: Select your unknown XML file for analysis</span>
        </div>
        <div style="display: flex; align-items: center; margin: 15px 0;">
            <span class="step-number">3</span>
            <span><strong>Apply Filters</strong>: Optionally filter by airline and API version</span>
        </div>
        <div style="display: flex; align-items: center; margin: 15px 0;">
            <span class="step-number">4</span>
            <span><strong>Run Analysis</strong>: Start AI-powered pattern matching</span>
        </div>
        <div style="display: flex; align-items: center; margin: 15px 0;">
            <span class="step-number">5</span>
            <span><strong>Review Results</strong>: Analyze matches and use chatbot for insights</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtering Feature
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="guide-section">
            <h4>🎯 Airline Filter</h4>
            <ul>
                <li>Select specific airlines from dropdown</li>
                <li>Choose "All Airlines" to test all patterns</li>
                <li>Reduces analysis time by focusing on relevant patterns</li>
                <li>Examples: "American Airlines", "Delta", "United"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="guide-section">
            <h4>📊 API Version Filter</h4>
            <ul>
                <li>Select specific API versions</li>
                <li>Choose "All Versions" to test all available versions</li>
                <li>Helps target specific API implementations</li>
                <li>Examples: "v1.0", "v2.1", "18.2"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Results Understanding
    st.markdown("""
    <div class="guide-section">
        <h3>📈 Understanding Results</h3>
        <p>The analysis table shows:</p>
        <ul>
            <li><strong>Airline</strong>: Actual airline name or API source</li>
            <li><strong>API Version</strong>: Specific version information</li>
            <li><strong>Section</strong>: XML section or XPath where pattern was found</li>
            <li><strong>Validation Rule</strong>: Description of what was matched</li>
            <li><strong>Verified</strong>: Yes/No indicating if pattern matched</li>
            <li><strong>Reason</strong>: AI explanation of match/non-match</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Interactive Chatbot
    st.markdown("""
    <div class="highlight-box">
        <h3>🤖 Results Chatbot</h3>
        <p>After analysis completes, use the <strong>"🤖 Ask Genie About Results"</strong> button to:</p>
        <ul>
            <li>Ask questions about the analysis results</li>
            <li>Get summaries of matched patterns</li>
            <li>Understand data quality assessments</li>
            <li>Receive recommendations for next steps</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_advanced_features():
    st.markdown("## ⚙️ Advanced Features")
    
    # Workspace Management
    st.markdown("""
    <div class="guide-section">
        <h3>🎯 Workspace Management</h3>
        <p>Workspaces organize your patterns by project, use case, or team structure.</p>
        <ul>
            <li><strong>Enhanced Management</strong>: Color-coded Add (green) and Delete (red) workspace buttons</li>
            <li><strong>Context Switching</strong>: Easy switching between projects</li>
            <li><strong>Import/Export</strong>: Pattern import/export functionality in Discovery page management tabs</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # API Management
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="guide-section">
            <h4>🏢 Supported APIs</h4>
            <ul>
                <li><strong>LATAM</strong>: LATAM Airlines API</li>
                <li><strong>LH</strong>: Lufthansa API</li>
                <li><strong>LHG</strong>: Lufthansa Group API</li>
                <li><strong>AFKL</strong>: Air France-KLM API</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="guide-section">
            <h4>📚 Pattern Categories</h4>
            <ul>
                <li><strong>Flight</strong>: Segments, routes, schedules</li>
                <li><strong>Passenger</strong>: Names, contact info, preferences</li>
                <li><strong>Fare</strong>: Pricing, taxes, fare basis</li>
                <li><strong>Booking</strong>: PNR, confirmations, reservations</li>
                <li><strong>Airline</strong>: Carrier codes, names</li>
                <li><strong>Custom</strong>: User-defined patterns</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Data Export/Import
    st.markdown("""
    <div class="guide-section">
        <h3>📁 Data Export and Import</h3>
        <h4>Export Options:</h4>
        <ul>
            <li><strong>CSV Export</strong>: Pattern Library export for data analysis and reporting</li>
            <li><strong>JSON Export</strong>: Raw pattern data for integration and migration</li>
        </ul>
        <h4>Export Process:</h4>
        <ol>
            <li>Filter data in Pattern Library</li>
            <li>Click "📄 Export Saved Patterns"</li>
            <li>Click "⬇️ Download CSV" button</li>
            <li>Check browser downloads folder</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Database Architecture
    st.markdown("""
    <div class="warning-box">
        <h4>🗄️ Database Architecture</h4>
        <p><strong>Storage Structure:</strong></p>
        <ul>
            <li><strong>SQLite Databases</strong>: Local storage for reliability</li>
            <li><strong>Multi-Database</strong>: Separate workspace and shared databases</li>
            <li><strong>Relational Design</strong>: Normalized structure for efficiency</li>
        </ul>
        <p><strong>Key Tables:</strong></p>
        <ul>
            <li><code>api</code>: API definitions and metadata</li>
            <li><code>apiversion</code>: Version tracking per API</li>
            <li><code>pattern_details</code>: Pattern information and prompts</li>
            <li><code>default_patterns</code>: Shared workspace patterns</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_help_faq():
    st.markdown("## ❓ Help & FAQ")
    
    # FAQ sections
    faq_categories = {
        "🏠 General Questions": [
            ("What is AssistedDiscovery?", "AssistedDiscovery is an AI-powered XML pattern analysis tool that helps developers understand, extract, and manage patterns from airline API XML responses using GPT-4o."),
            ("Do I need programming knowledge?", "No, the tool is designed with a user-friendly interface. Basic understanding of XML structure is helpful but not required."),
            ("Can I use this tool offline?", "The tool requires internet connection for AI processing (Azure OpenAI API calls), but pattern storage and management work locally.")
        ],
        "⚙️ Configuration": [
            ("What Azure OpenAI subscription do I need?", "You need an active Azure OpenAI subscription with GPT-4o model deployment. Standard pay-as-you-go pricing applies."),
            ("Can I use regular OpenAI instead of Azure OpenAI?", "Currently, the tool is configured specifically for Azure OpenAI. Regular OpenAI API is not supported."),
            ("How much does it cost to run pattern analysis?", "Costs depend on Azure OpenAI usage. Typical pattern extraction costs $0.01-0.10 per XML file, depending on size and complexity.")
        ],
        "🔍 Pattern Questions": [
            ("What types of XML files work best?", "Well-formed XML files from airline APIs work best. Files should be 10KB-1MB in size with representative data structures."),
            ("What's the difference between Auto and Manual extraction modes?", "Auto Mode automatically analyzes your entire XML and extracts all relevant patterns using AI, perfect for comprehensive discovery. Manual Mode lets you specify exact XPath expressions for targeted pattern extraction, ideal for specific requirements."),
            ("Which extraction mode should I choose?", "Start with Auto Mode for complete analysis and overview of your XML structure. Use Manual Mode when you need specific patterns or have exact XPath requirements. You can use both modes on the same XML file."),
            ("How accurate is the AI pattern extraction?", "GPT-4o provides highly accurate pattern extraction. Always verify patterns before saving for best results."),
            ("Can I edit extracted patterns?", "Currently, patterns cannot be edited after extraction. Re-extract with different prompts or contexts if changes are needed.")
        ],
        "🎯 Workspace Questions": [
            ("How many workspaces can I create?", "There's no hard limit on workspaces. Performance may be affected with very large numbers of workspaces."),
            ("Can I share workspaces with team members?", "Workspaces are local to each installation. Use the shared workspace feature for team collaboration."),
            ("What happens if I delete a workspace?", "Workspace deletion removes all associated patterns and data. Always export important data before deletion.")
        ]
    }
    
    for category, questions in faq_categories.items():
        st.markdown(f"""
        <div class="guide-section">
            <h3>{category}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for question, answer in questions:
            with st.expander(f"❓ {question}"):
                st.markdown(f"**Answer:** {answer}")
    
    # Troubleshooting
    st.markdown("""
    <div class="warning-box">
        <h3>🔧 Common Issues</h3>
        <h4>Configuration Problems:</h4>
        <ul>
            <li><strong>"Configuration Incomplete"</strong>: Go to Configuration page and enter all required fields</li>
            <li><strong>"Test Connection Failed"</strong>: Verify API key and endpoint URL format</li>
        </ul>
        <h4>Pattern Extraction Issues:</h4>
        <ul>
            <li><strong>"No Patterns Extracted"</strong>: Verify XML file is valid and well-formed</li>
            <li><strong>"Extraction Takes Too Long"</strong>: Use smaller XML files (< 1MB recommended)</li>
        </ul>
        <h4>Pattern Identification Issues:</h4>
        <ul>
            <li><strong>"No Validation Rules Found"</strong>: Save patterns from Discovery page first</li>
            <li><strong>"Analysis Shows No Matches"</strong>: Verify XML is from expected API</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Contact Information
    st.markdown("""
    <div class="highlight-box">
        <h3>📞 Getting Support</h3>
        <p>For additional support:</p>
        <ul>
            <li>Check this user guide first</li>
            <li>Review troubleshooting sections</li>
            <li>Check application logs and error messages</li>
            <li>Use the built-in chatbots for contextual help</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()