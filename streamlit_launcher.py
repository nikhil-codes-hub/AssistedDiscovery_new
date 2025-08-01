#!/usr/bin/env python3
"""
Streamlit Launcher for Genie Application
This script properly initializes the environment and starts Streamlit
"""

import os
import sys
from pathlib import Path

# Initialize logging early
try:
    from core.common.logging_manager import get_logging_manager, log_user_action, log_error
    logging_manager = get_logging_manager()
    logger = logging_manager.get_logger("launcher")
except ImportError:
    # Fallback if logging manager is not available
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("launcher")
    logging_manager = None

def setup_environment():
    """Set up the environment for the bundled application."""
    logger.info("Setting up application environment")
    
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - use the temp dir created by PyInstaller
        app_dir = Path(sys._MEIPASS)
        working_dir = Path(sys.executable).parent
        logger.info(f"Running as executable - App dir: {app_dir}, Working dir: {working_dir}")
        os.chdir(working_dir)
    else:
        # Running as script
        app_dir = Path(__file__).parent
        logger.info(f"Running as script - App dir: {app_dir}")
        os.chdir(app_dir)
    
    # Add app directory to Python path
    sys.path.insert(0, str(app_dir))
    logger.info(f"Added to Python path: {app_dir}")
    
    # Set environment variables for Streamlit
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    
    logger.info("Streamlit environment variables set")
    
    if logging_manager:
        logger.info(f"Logs will be saved to: {logging_manager.get_log_file_path()}")
    
    return app_dir

def start_streamlit_app(app_dir):
    """Start the Streamlit application."""
    logger.info("Starting Streamlit application")
    
    # Path to the main Streamlit app
    app_path = app_dir / "app" / "Assisted_Discovery.py"
    
    if not app_path.exists():
        error_msg = f"Application file not found at {app_path}"
        logger.error(error_msg)
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"App directory: {app_dir}")
        print(f"Error: {error_msg}")
        print(f"Current directory: {os.getcwd()}")
        print(f"App directory: {app_dir}")
        sys.exit(1)
    
    logger.info(f"Application path: {app_path}")
    logger.info(f"Working directory: {app_dir}")
    
    print("🧞 Starting Genie Application...")
    print(f"📍 Application will be available at: http://localhost:8501")
    print(f"📁 Working directory: {app_dir}")
    print(f"🎯 App path: {app_path}")
    
    if logging_manager:
        print(f"📋 Logs: {logging_manager.get_log_file_path()}")
        log_user_action("application_start", f"App path: {app_path}")
    
    # Import and start Streamlit
    try:
        logger.info("Importing Streamlit")
        import streamlit.web.cli as stcli
        
        # Set up sys.argv for Streamlit
        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.port=8501",
            "--server.address=localhost"
        ]
        
        logger.info("Starting Streamlit with args: " + " ".join(sys.argv))
        
        # Start Streamlit
        stcli.main()
        
    except ImportError as e:
        error_msg = f"Error importing Streamlit: {e}"
        logger.error(error_msg)
        if logging_manager:
            log_error(e, "Streamlit import failed")
        print(error_msg)
        print("Please ensure Streamlit is properly bundled.")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Error starting application: {e}"
        logger.error(error_msg)
        if logging_manager:
            log_error(e, "Application startup failed")
        print(error_msg)
        sys.exit(1)

def main():
    """Main entry point."""
    try:
        logger.info("Application starting up")
        app_dir = setup_environment()
        start_streamlit_app(app_dir)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        if logging_manager:
            log_user_action("application_stop", "User interrupted")
        print("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if logging_manager:
            log_error(e, "Fatal application error")
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()