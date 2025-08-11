@echo off
REM Create Portable Distribution for Assisted Discovery
echo 🚀 Creating Portable Assisted Discovery Application
echo Platform: Windows

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist portable_dist rmdir /s /q portable_dist

REM Create distribution directory
echo 📁 Creating distribution structure...
mkdir portable_dist
mkdir portable_dist\app
mkdir portable_dist\core

REM Copy application files
echo 📋 Copying application files...
xcopy /E /I app portable_dist\app
xcopy /E /I core portable_dist\core

REM Copy launcher
copy streamlit_launcher.py portable_dist\

REM Copy .env if it exists
if exist .env copy .env portable_dist\

REM Create requirements file
echo 📦 Creating requirements.txt...
echo streamlit==1.28.1 > portable_dist\requirements.txt
echo openai >> portable_dist\requirements.txt
echo pandas >> portable_dist\requirements.txt
echo streamlit-tree-select >> portable_dist\requirements.txt
echo python-dotenv >> portable_dist\requirements.txt
echo requests >> portable_dist\requirements.txt
echo lxml >> portable_dist\requirements.txt
echo altair >> portable_dist\requirements.txt
echo numpy >> portable_dist\requirements.txt
echo cryptography >> portable_dist\requirements.txt

REM Create setup script with virtual environment
echo 📝 Creating setup script...
echo @echo off > portable_dist\setup.bat
echo echo 🔧 Setting up Assisted Discovery... >> portable_dist\setup.bat
echo echo This will create an isolated Python environment >> portable_dist\setup.bat
echo echo No pollution of your system Python! >> portable_dist\setup.bat
echo pause >> portable_dist\setup.bat
echo. >> portable_dist\setup.bat
echo echo Creating virtual environment... >> portable_dist\setup.bat
echo python -m venv assisted_discovery_env >> portable_dist\setup.bat
echo if errorlevel 1 ^( >> portable_dist\setup.bat
echo     echo ❌ Failed to create virtual environment >> portable_dist\setup.bat
echo     pause >> portable_dist\setup.bat
echo     exit /b 1 >> portable_dist\setup.bat
echo ^) >> portable_dist\setup.bat
echo. >> portable_dist\setup.bat
echo echo Installing dependencies in isolated environment... >> portable_dist\setup.bat
echo assisted_discovery_env\Scripts\pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt >> portable_dist\setup.bat
echo if errorlevel 1 ^( >> portable_dist\setup.bat
echo     echo ❌ Failed to install dependencies >> portable_dist\setup.bat
echo     pause >> portable_dist\setup.bat
echo     exit /b 1 >> portable_dist\setup.bat
echo ^) >> portable_dist\setup.bat
echo. >> portable_dist\setup.bat
echo echo ✅ Setup complete! Isolated environment created. >> portable_dist\setup.bat
echo pause >> portable_dist\setup.bat

REM Create launcher script
echo 📝 Creating launcher script...
echo @echo off > portable_dist\run_assisted_discovery.bat
echo echo 🧞 Starting Assisted Discovery... >> portable_dist\run_assisted_discovery.bat
echo echo 📍 Application will be available at: http://localhost:8501 >> portable_dist\run_assisted_discovery.bat
echo echo 🌐 Opening browser automatically... >> portable_dist\run_assisted_discovery.bat
echo. >> portable_dist\run_assisted_discovery.bat
echo assisted_discovery_env\Scripts\python streamlit_launcher.py >> portable_dist\run_assisted_discovery.bat
echo pause >> portable_dist\run_assisted_discovery.bat

REM Create README
echo 📝 Creating README...
echo # Assisted Discovery Application > portable_dist\README.txt
echo. >> portable_dist\README.txt
echo ## Quick Setup >> portable_dist\README.txt
echo. >> portable_dist\README.txt
echo 1. Ensure Python 3.8+ is installed >> portable_dist\README.txt
echo 2. Run setup.bat to install dependencies (one time only) >> portable_dist\README.txt
echo 3. Run run_assisted_discovery.bat to start the application >> portable_dist\README.txt
echo. >> portable_dist\README.txt
echo ## System Requirements >> portable_dist\README.txt
echo. >> portable_dist\README.txt
echo - Python 3.8 or later >> portable_dist\README.txt
echo - Internet connection for initial setup >> portable_dist\README.txt
echo - 4GB RAM minimum >> portable_dist\README.txt
echo. >> portable_dist\README.txt
echo ## Features >> portable_dist\README.txt
echo. >> portable_dist\README.txt
echo - XML Pattern Discovery and Analysis >> portable_dist\README.txt
echo - AI-Powered Gap Analysis >> portable_dist\README.txt
echo - Interactive Web Interface >> portable_dist\README.txt

REM Create zip archive
echo 🗜️ Creating distribution archive...
powershell -command "Compress-Archive -Path 'portable_dist\*' -DestinationPath 'assisted-discovery-portable.zip' -Force"

echo 🎉 Portable distribution created successfully!
echo 📦 Files created:
echo   - portable_dist\ (distribution folder)
echo   - assisted-discovery-portable.zip (distribution archive)
echo.
echo 📋 User Instructions:
echo   1. Extract ZIP file
echo   2. Run setup.bat (one time only)
echo   3. Run run_assisted_discovery.bat to start app
echo.
echo ✅ Ready for distribution!
pause