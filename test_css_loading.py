#!/usr/bin/env python3
"""
Test script to debug CSS loading issues.
Run this from the project root directory.
"""

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_css_paths():
    """Test if CSS file can be found using the utility function paths."""
    print("=== CSS Loading Debug Test ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    print()
    
    # Test the CSS utility function paths
    from core.common.css_utils import get_css_path
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test the same paths as in css_utils.py
    possible_paths = [
        os.path.join(current_dir, "core/common/../../app/css/table_styles.css"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "app/css/table_styles.css"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "app/css/table_styles.css"),
        "app/css/table_styles.css",
        "./app/css/table_styles.css"
    ]
    
    print("Testing CSS file paths:")
    for i, css_path in enumerate(possible_paths):
        abs_path = os.path.abspath(css_path)
        exists = os.path.exists(css_path)
        print(f"{i+1:2d}. {css_path}")
        print(f"    -> {abs_path}")
        print(f"    -> EXISTS: {exists}")
        if exists:
            try:
                with open(css_path, 'r') as f:
                    content_size = len(f.read())
                    print(f"    -> SIZE: {content_size} characters")
            except Exception as e:
                print(f"    -> ERROR reading file: {e}")
        print()
    
    # Test the utility function
    print("Testing get_css_path() function:")
    css_path = get_css_path()
    if css_path:
        print(f"✅ Found CSS at: {css_path}")
        print(f"   Absolute path: {os.path.abspath(css_path)}")
    else:
        print("❌ CSS file not found by utility function")

if __name__ == "__main__":
    test_css_paths()