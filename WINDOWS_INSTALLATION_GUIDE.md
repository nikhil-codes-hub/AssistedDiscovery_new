# AssistedDiscovery - Windows Installation Guide

## System Requirements

Before installing AssistedDiscovery, ensure your Windows system meets these requirements:

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Version 3.8 or later (must be installed)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 1GB free disk space
- **Internet Connection**: Required for setup and AI processing
- **Azure OpenAI**: Active subscription with GPT-4o deployment

---

## Installation Steps

### Step 1: Install Python (Required First)

1. **Download Python**:
   - Go to [python.org](https://www.python.org/downloads/windows/)
   - Download Python 3.8+ (Python 3.11+ recommended)
   - Choose "Windows installer (64-bit)"

2. **Install Python**:
   - Run the downloaded installer
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Select "Install Now"
   - Click "Disable path length limit" when prompted

3. **Verify Python Installation**:
   - Press `Win + R`, type `cmd`, press Enter
   - Run: `python --version` (should show Python 3.x.x)
   - Run: `pip --version` (should show pip version)

### Step 2: Download and Extract AssistedDiscovery

1. **Receive the ZIP file**: You should have received `assisted-discovery-portable.zip`
2. **Choose Installation Location**: Select a folder where you want to install
   ```
   Recommended locations:
   C:\Program Files\AssistedDiscovery\
   C:\Users\%USERNAME%\Documents\AssistedDiscovery\
   C:\AssistedDiscovery\
   ```

3. **Extract the Application**:
   - Right-click on `assisted-discovery-portable.zip`
   - Select "Extract All..."
   - Choose destination folder
   - Click "Extract"

### Step 3: Verify Extraction

After extraction, you should see the application files directly:
```
(Your chosen installation folder)/
├── setup.bat                     # One-time setup script
├── run_assisted_discovery.bat    # Application launcher
├── streamlit_launcher.py          # Python launcher
├── requirements.txt               # Dependencies list
├── app/                          # Application pages
├── core/                         # Application logic
└── README.txt                    # Quick instructions
```

### Step 4: Run One-Time Setup

1. **Navigate to the extracted folder**
2. **Right-click** on `setup.bat`
3. **Select "Run as administrator"** (recommended)
4. **Wait for setup to complete**:
   - Creates isolated Python virtual environment
   - Installs all required dependencies automatically
   - No pollution of your system Python
   - This may take 3-5 minutes depending on internet speed

5. **Setup Complete**: You'll see "✅ Setup complete!" message

### Step 5: Installation Complete!

✅ Your AssistedDiscovery application is now ready to use!

## First Launch

### Step 1: Start AssistedDiscovery

1. **Navigate to Installation Folder**:
   - Open File Explorer
   - Go to where you extracted the ZIP file

2. **Launch the Application**:
   - **Double-click** `run_assisted_discovery.bat`
   - A Command Prompt window will open showing startup messages
   
3. **Wait for Startup**:
   - Application may take 30-60 seconds to start (first launch only)
   - You'll see "🧞 Starting Assisted Discovery..." message
   - The application will automatically open in your default browser
   - You'll see the AssistedDiscovery interface at `http://localhost:8501`

4. **If Browser Doesn't Open Automatically**:
   - Look for the message "📍 Application will be available at: http://localhost:8501"
   - Manually open your browser and go to: `http://localhost:8501`

**Important**: Keep the Command Prompt window open while using the application!

## Troubleshooting

### Common Issues and Solutions

#### Application Launch Issues

**Issue**: `'python' is not recognized as an internal or external command`
- **Solutions**:
  - Python is not installed or not in PATH
  - Reinstall Python and check "Add Python to PATH"
  - Try using `py` instead of `python` in commands

**Issue**: `pip install -r requirements.txt` fails
- **Solutions**:
  - Update pip first: `python -m pip install --upgrade pip`
  - Run Command Prompt as Administrator
  - Install packages individually if bulk install fails

**Issue**: `streamlit: command not found` or similar
- **Solutions**:
  - Install streamlit: `pip install streamlit`
  - Verify installation: `streamlit --version`
  - Use full path: `python -m streamlit run app/Assisted_Discovery.py`

**Issue**: Application starts but browser doesn't open
- **Solution**: Look for the URL in Command Prompt output and open manually
- **Check**: Default browser may be set incorrectly

**Issue**: "Port 8501 is already in use" error
- **Solution**: 
  - Close any other running AssistedDiscovery instances
  - Restart your computer if issue persists
  - Check for other applications using port 8501

#### Performance Issues

**Issue**: Application starts very slowly
- **Solutions**:
  - First launch is always slower (30-60 seconds is normal)
  - Close unnecessary applications to free up RAM
  - Ensure you have stable internet connection
  - Consider moving installation to SSD drive

**Issue**: Browser shows "This site can't be reached"
- **Solutions**:
  - Wait longer - application may still be starting
  - Check if Windows Firewall is blocking the connection
  - Try a different browser (Chrome, Firefox, Edge)
  - Disable VPN temporarily if using one

#### Azure OpenAI Issues

**Issue**: "Test Connection Failed"
- **Solutions**:
  - Verify API key is correct (copy-paste to avoid typos)
  - Check endpoint URL format: `https://your-resource.openai.azure.com/`
  - Ensure GPT-4o model is deployed in Azure OpenAI Studio
  - Verify Azure resource is active and not suspended
  - Check your internet connection

**Issue**: "Model not found" errors
- **Solutions**: 
  - Ensure model deployment name is exactly `gpt-4o`
  - Check that GPT-4o model is deployed and active in Azure
  - Wait a few minutes after model deployment before testing

#### File and Folder Issues

**Issue**: "Permission denied" or "Access denied" errors
- **Solutions**:
  - Run application as administrator
  - Check folder permissions - ensure user has read/write access
  - Move application to a different location (e.g., Documents folder)

**Issue**: Application files corrupted after extraction
- **Solutions**:
  - Re-extract the ZIP file to a new location
  - Ensure ZIP file downloaded completely
  - Try extracting with a different tool (7-Zip, WinRAR)

#### Network and Firewall Issues

**Issue**: Cannot connect to Azure OpenAI
- **Solutions**:
  - Check internet connection
  - Temporarily disable Windows Firewall/antivirus
  - If using corporate network, check with IT about firewall rules
  - Try from a different network to isolate the issue

### Performance Optimization

1. **System Resources**:
   - Close unnecessary applications before running
   - Ensure 4GB+ RAM available
   - Use SSD storage for better performance

2. **Network**:
   - Stable internet connection (minimum 10 Mbps recommended)
   - Avoid VPN if possible during usage
   - Use wired connection if WiFi is unstable

3. **Windows Settings**:
   - Keep Windows updated
   - Ensure Windows Defender real-time protection allows the application
   - Close browser tabs not related to AssistedDiscovery

---

## Application Management

### File Locations

After installation and first run, you'll find:

```
(Your installation folder)/
├── streamlit_launcher.py          # Main launcher
├── assisted_discovery_env/         # Virtual environment (auto-created)
├── app/
│   ├── Assisted_Discovery.py      # Core application
│   └── pages/                     # Application pages
├── core/                          # Application logic
├── requirements.txt               # Dependencies
├── .env                           # Configuration (auto-created)
```

### Data Management

- **Pattern Storage**: All patterns saved in `core/database/data/` folder
- **Configuration**: Settings stored in `.env` file  
- **Application Logs**: Stored in `%APPDATA%\GenieApp\logs\` folder (e.g., `C:\Users\[username]\AppData\Roaming\GenieApp\logs`)
- **Backup**: Copy `core/database/data/` folder and `.env` file to backup your work

### Updates and Maintenance

- **Updates**: You'll receive new ZIP files for updates
- **Backup**: Export your patterns before updating
- **Clean Install**: Delete old folder, extract new ZIP, copy `core/database/data/` folder and `.env` file
- **Logs**: Check `%APPDATA%\GenieApp\logs\` folder if you experience issues

---

## Support Information

### Getting Help

1. **Built-in User Guide**: Most comprehensive help source
2. **Chatbot Feature**: Ask Genie about specific features
3. **Application Logs**: Check `logs/` folder for error details

### Reporting Issues

When reporting problems, please include:
- Windows version (Windows 10/11)
- Error messages (screenshots helpful)
- Steps that caused the issue
- Contents of latest log file

### Best Practices

- **Regular Backups**: Export patterns monthly
- **Stable Internet**: Required for AI processing
- **System Updates**: Keep Windows updated
- **Antivirus**: Ensure AssistedDiscovery is allowed

---

*This installation guide is specifically for the portable Windows distribution of AssistedDiscovery.*