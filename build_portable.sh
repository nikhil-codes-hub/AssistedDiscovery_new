#!/bin/bash

# Create Portable Distribution for Assisted Discovery
set -e

echo "🚀 Creating Portable Assisted Discovery Application"
echo "Platform: $(uname -s) $(uname -m)"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf portable_dist

# Create distribution directory
echo "📁 Creating distribution structure..."
mkdir -p portable_dist/app
mkdir -p portable_dist/core

# Copy application files
echo "📋 Copying application files..."
cp -r app/* portable_dist/app/
cp -r core/* portable_dist/core/

# Copy launcher
cp streamlit_launcher.py portable_dist/

# Copy .env if it exists
if [ -f ".env" ]; then
    cp .env portable_dist/
fi

# Create requirements file
echo "📦 Creating requirements.txt..."
cat > portable_dist/requirements.txt << EOF
streamlit==1.28.1
openai
pandas
streamlit-tree-select
python-dotenv
requests
lxml
altair
numpy
tornado
click
urllib3
certifi
charset-normalizer
idna
cryptography
EOF

# Create setup script with virtual environment
echo "📝 Creating setup script..."
cat > portable_dist/setup.sh << 'EOF'
#!/bin/bash
echo "🔧 Setting up Assisted Discovery..."
echo "This will create an isolated Python environment"
echo "No pollution of your system Python!"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv assisted_discovery_env
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "Installing dependencies in isolated environment..."
assisted_discovery_env/bin/pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Setup complete! Isolated environment created."
echo "Run ./run_gap_analyser.sh to start the application"
EOF

chmod +x portable_dist/setup.sh

# Create launcher script
echo "📝 Creating launcher script..."
cat > portable_dist/run_gap_analyser.sh << 'EOF'
#!/bin/bash
echo "🧞 Starting Assisted Discovery..."
echo "📍 Application will be available at: http://localhost:8501"
echo "🌐 Opening browser automatically..."

# Start the application in background
assisted_discovery_env/bin/python streamlit_launcher.py &
APP_PID=$!

# Wait a moment for the app to start
sleep 3

# Try to open browser
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://localhost:8501
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open http://localhost:8501
else
    echo "Please open http://localhost:8501 in your browser"
fi

# Wait for user to stop the application
echo "Press Ctrl+C to stop the application"
wait $APP_PID
EOF

chmod +x portable_dist/run_gap_analyser.sh

# Create README
echo "📝 Creating README..."
cat > portable_dist/README.txt << EOF
# Assisted Discovery Application

## Quick Setup

1. Ensure Python 3.8+ is installed
2. Run ./setup.sh to install dependencies (one time only)
3. Run ./run_assisted_discovery.sh to start the application

## System Requirements

- Python 3.8 or later
- pip3 (Python package manager)
- Internet connection for initial setup
- 4GB RAM minimum
- Browser: Chrome, Firefox, Safari, or Edge

## Features

- XML Pattern Discovery and Analysis
- AI-Powered Gap Analysis
- Interactive Web Interface

## Troubleshooting

### Python Not Found
- Install Python 3.8+ from python.org
- Ensure python3 command is available

### Permission Issues (macOS)
- Run: chmod +x setup.sh run_gap_analyser.sh
- May need to allow execution in System Preferences > Security

### Dependencies Install Failed
- Ensure internet connection
- Try: pip3 install --upgrade pip
- Then run setup.sh again

## File Structure

- setup.sh - One-time dependency installer
- run_gap_analyser.sh - Application launcher
- streamlit_launcher.py - Main launcher
- app/ - Application code
- core/ - Core libraries
- requirements.txt - Python dependencies

Platform: $(uname -s) $(uname -r)
Build Date: $(date)
EOF

# Create zip archive for distribution
echo "🗜️ Creating distribution archive..."
cd portable_dist
zip -r "../assisted-discovery-portable-$(uname -s)-$(uname -m).zip" .
cd ..

echo "🎉 Portable distribution created successfully!"
echo "📦 Files created:"
echo "  - portable_dist/ (distribution folder)"
echo "  - assisted-discovery-portable-$(uname -s)-$(uname -m).zip (distribution archive)"
echo ""
echo "📋 User Instructions:"
echo "  1. Extract ZIP file"
echo "  2. Run ./setup.sh (one time only)"
echo "  3. Run ./run_assisted_discovery.sh to start app"
echo ""
echo "✅ Ready for distribution!"