#!/usr/bin/env python3
"""
Wink Browser - Main Entry Point

A modern, privacy-focused web browser built in Python.
"""

import os
import sys
import argparse
import logging
import tkinter as tk
from tkinter import ttk

# Import browser components
from browser_engine.html5_engine import HTML5Engine
from browser_engine.ui.browser_window import BrowserWindow
from browser_engine.privacy.ad_blocker import AdBlocker
from browser_engine.network.network_manager import NetworkManager
from browser_engine.extensions.extension_manager import ExtensionManager
from browser_engine.utils.config_manager import ConfigManager
from browser_engine.utils.profile_manager import ProfileManager

# Version info
__version__ = '1.0.0'

def setup_logging(debug_mode=False):
    """Configure logging for the browser."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Ensure log directory exists
    log_dir = os.path.expanduser("~/.wink_browser/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup file logging
    log_file = os.path.join(log_dir, "wink_browser.log")
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Log startup info
    logger = logging.getLogger("WinkBrowser")
    logger.info(f"Starting Wink Browser v{__version__}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Operating system: {sys.platform}")
    
    return logger

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Wink Browser - A modern, privacy-focused web browser")
    
    parser.add_argument("url", nargs="?", help="URL to open on startup", default=None)
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--text-only", action="store_true", help="Disable JavaScript")
    parser.add_argument("--private", action="store_true", help="Use private browsing mode")
    parser.add_argument("--version", action="version", version=f"Wink Browser {__version__}")
    
    return parser.parse_args()

def main():
    """Main entry point for the browser."""
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    try:
        # Create the root Tk window
        root = tk.Tk()
        root.title("Wink Browser")
        root.geometry("1200x800")
        
        # Set app icon if available
        if os.path.exists("browser_engine/resources/icons/wink_icon.png"):
            icon = tk.PhotoImage(file="browser_engine/resources/icons/wink_icon.png")
            root.iconphoto(True, icon)
        
        # Initialize configuration
        config_manager = ConfigManager(private_mode=args.private)
        
        # Initialize components
        profile_manager = ProfileManager(config_manager)
        network_manager = NetworkManager(config_manager)
        ad_blocker = AdBlocker(config_manager)
        extension_manager = ExtensionManager(config_manager)
        
        # Initialize HTML5 engine
        html5_engine = HTML5Engine(
            width=1200,
            height=800,
            debug=args.debug
        )
        
        # Create main browser window
        browser = BrowserWindow(
            root,
            network_manager,
            ad_blocker,
            extension_manager,
            profile_manager,
            config_manager,
            html5_engine=html5_engine,
            disable_javascript=args.text_only,
            private_mode=args.private,
            debug_mode=args.debug
        )
        
        # Load initial URL if provided
        if args.url:
            browser.navigate_to_url(args.url)
        else:
            # Load homepage from config
            browser.load_homepage()
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        # Show error dialog if UI is available
        try:
            from tkinter import messagebox
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")
        except:
            print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 