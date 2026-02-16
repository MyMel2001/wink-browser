#!/usr/bin/env python3
"""
Wink Browser - A complete custom browser with privacy focus

Main entry point for the Wink Browser application.
"""

import os
import sys
import logging
import argparse
import tkinter as tk
from tkinter import ttk

# Add the browser engine to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import browser components
from browser_engine.utils.config_manager import ConfigManager
from browser_engine.network.network_manager import NetworkManager
from browser_engine.privacy.ad_blocker import AdBlocker
from browser_engine.extensions.extension_manager import ExtensionManager
from browser_engine.utils.profile_manager import ProfileManager
from browser_engine.ui.browser_window import BrowserWindow
from browser_engine.html5_engine import HTML5Engine

# Configure logging
def setup_logging(debug=False):
    """Set up logging for the application."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_dir = os.path.expanduser("~/.wink_browser/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'wink_browser.log')),
            logging.StreamHandler()
        ]
    )
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized at level %s", logging.getLevelName(log_level))
    return logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Wink Browser - A complete custom browser with privacy focus")
    parser.add_argument('url', nargs='?', default=None, help='URL to open')
    parser.add_argument('--private', action='store_true', help='Start in private browsing mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--profile', type=str, default=None, help='Use specified profile')
    parser.add_argument('--disable-js', action='store_true', help='Disable JavaScript')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(args.debug)
    logger.info("Starting Wink Browser")
    
    # Create configuration manager
    config_manager = ConfigManager()
    if args.private:
        config_manager.private_mode = True
        logger.info("Starting in private browsing mode")
    
    # Create managers
    network_manager = NetworkManager(config_manager)
    ad_blocker = AdBlocker(config_manager)
    profile_manager = ProfileManager(config_manager)
    extension_manager = ExtensionManager(config_manager)
    
    # Switch to specified profile if provided
    if args.profile and not args.private:
        if profile_manager.switch_profile(args.profile):
            logger.info(f"Switched to profile: {args.profile}")
        else:
            logger.warning(f"Failed to switch to profile: {args.profile}")
    
    # Create the main application window
    root = tk.Tk()
    root.title("Wink Browser")
    root.geometry("1024x768")
    
    # Set application icon
    # TODO: Add application icon
    
    # Apply theme
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme as base
    
    # Configure custom styles
    style.configure('TButton', font=('Segoe UI', 10))
    style.configure('TEntry', font=('Segoe UI', 10))
    style.configure('TLabel', font=('Segoe UI', 10))

    # Initialize HTML5 engine
    html5_engine = HTML5Engine(
        width=1024,
        height=768,
        debug=args.debug
    )

    # Create and run browser window
    browser = BrowserWindow(
        root,
        network_manager=network_manager,
        ad_blocker=ad_blocker,
        profile_manager=profile_manager,
        extension_manager=extension_manager,
        config_manager=config_manager,
        html5_engine=html5_engine,
        disable_javascript=args.disable_js,
        private_mode=args.private,
        debug_mode=args.debug
    )
    
    # Navigate to URL if provided
    if args.url:
        browser.navigate_to_url(args.url)
    else:
        # Navigate to homepage
        browser.load_homepage()
    
    # Start the application
    logger.info("Wink Browser started successfully")
    root.mainloop()
    
    # Clean up
    logger.info("Wink Browser shutting down")
    
    # Save configuration
    config_manager.save()
    
    logger.info("Shutdown complete")

if __name__ == "__main__":
    main() 