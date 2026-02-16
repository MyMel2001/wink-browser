"""
HTML5 Renderer implementation.
This module provides a Tkinter-based renderer for displaying HTML5 content.
"""

import logging
import os
import re
import tkinter as tk
from tkinter import ttk, Canvas, Text, PhotoImage, TclError, font as tkfont
from typing import Dict, List, Optional, Tuple, Any, Union, Set, Callable
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math
import threading
import queue
import urllib.request
import urllib.parse
import urllib.error
import base64
import time
from io import BytesIO

from browser_engine.html5_engine.dom import element

from ..dom import Document, Element, Node, NodeType
from ..css import LayoutEngine, LayoutBox, CSSParser, DisplayType, BoxType

logger = logging.getLogger(__name__)

# Dictionary of named colors to their hex values
NAMED_COLORS = {
    'black': '#000000',
    'silver': '#c0c0c0',
    'gray': '#808080',
    'white': '#ffffff',
    'maroon': '#800000',
    'red': '#ff0000',
    'purple': '#800080',
    'fuchsia': '#ff00ff',
    'green': '#008000',
    'lime': '#00ff00',
    'olive': '#808000',
    'yellow': '#ffff00',
    'navy': '#000080',
    'blue': '#0000ff',
    'teal': '#008080',
    'aqua': '#00ffff',
    'orange': '#ffa500',
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'blanchedalmond': '#ffebcd',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgreen': '#006400',
    'darkgrey': '#a9a9a9',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'greenyellow': '#adff2f',
    'grey': '#808080',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgray': '#d3d3d3',
    'lightgreen': '#90ee90',
    'lightgrey': '#d3d3d3',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'oldlace': '#fdf5e6',
    'olivedrab': '#6b8e23',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'whitesmoke': '#f5f5f5',
    'yellowgreen': '#9acd32'
}

class HTML5Renderer:
    """
    HTML5 Renderer using Tkinter.
    
    This class renders HTML5 documents with full CSS support.
    """
    
    def __init__(self, parent: ttk.Frame):
        """
        Initialize the renderer.
        
        Args:
            parent: Parent Tkinter frame
        """
        self.parent = parent
        
        # Create the main content frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the canvas for rendering
        self.canvas = tk.Canvas(
            self.main_frame,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            bg='#f5f5f5'  # Light gray background instead of white
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Link scrollbars to canvas
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        
        # Layout and CSS engines
        self.layout_engine = LayoutEngine()
        self.css_parser = CSSParser()
        
        # Initialize JavaScript engine if available
        try:
            from browser_engine.html5_engine.js.engine import JSEngine
            self.js_engine = JSEngine()
            logger.debug("JavaScript engine initialized")
        except ImportError:
            logger.warning("JavaScript engine not available")
            self.js_engine = None
        
        # Document and layout tree
        self.document: Optional[Document] = None
        self.layout_tree: Optional[LayoutBox] = None
        
        # Canvas items (for cleanup)
        self.canvas_items: List[int] = []
        
        # Viewport dimensions
        self.viewport_width = 800
        self.viewport_height = 600
        
        # Zoom level (1.0 = 100%)
        self.zoom_level = 1.0
        
        # Fonts
        self._init_fonts()
        
        # Colors
        self._init_colors()
        
        # Image caches
        self.image_cache: Dict[str, Image.Image] = {}  # PIL Image cache
        self.photo_cache: Dict[str, PhotoImage] = {}  # Tkinter PhotoImage cache
        
        # Network manager (will be set by set_engine)
        self.network_manager = None
        
        # Initialize for drag scrolling
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_scroll_x = 0
        self._drag_scroll_y = 0
        
        # Debug options
        self.draw_debug_boxes = False
        
        # Event bindings
        self._init_event_bindings()
        
        # Link handling callbacks
        self.on_link_click: Optional[Callable[[str], None]] = None
        
        logger.debug("HTML5 Renderer initialized")
        
        # Track processed nodes to prevent duplicates
        self.processed_nodes = set()
        self.processed_rendered_paragraphs = set()
        self.in_progress_paragraphs = set()
    
    def _init_fonts(self) -> None:
        """
        Initialize fonts for rendering.
        """
        # Initialize default fonts
        self.fonts = {
            'default': ('Arial', 12),
            'heading': ('Arial', 16, 'bold'),
            'monospace': ('Courier New', 12),
            'serif': ('Times New Roman', 12),
            'sans-serif': ('Arial', 12),
            'cursive': ('Comic Sans MS', 12),
            'fantasy': ('Impact', 12),
        }
        
        # Font style modifiers
        self.font_styles = {
            'bold': 'bold',
            'italic': 'italic',
            'underline': 'underline',
            'overstrike': 'overstrike'  # For strikethrough
        }
    
    def _init_colors(self) -> None:
        """Initialize colors for rendering."""
        self.colors = {
            'link': '#0000EE',
            'visited_link': '#551A8B',
            'active_link': '#FF0000',
            'selection': '#B5D5FF',
            'default_text': '#000000',
            'border': '#000000',
            'background': '#FFFFFF',
        }
    
    def _init_event_bindings(self) -> None:
        """Initialize event bindings for the canvas."""
        # Mouse click event binding
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        
        # Resize event binding
        self.parent.bind("<Configure>", self._on_resize)
    
    def set_engine(self, engine) -> None:
        """
        Set the HTML5Engine reference.
        
        Args:
            engine: The HTML5Engine instance
        """
        self.html5_engine = engine
        # Get network manager from engine
        self.network_manager = getattr(engine, 'network_manager', None)
        if not self.network_manager:
            logger.warning("No network manager available - image loading may be limited")
        logger.debug("HTML5Engine reference set in renderer")
    
    def clear(self) -> None:
        """
        Clear the renderer and reset all state.
        This is a public method that calls the internal _clear_canvas method.
        """
        self._clear_canvas()
        self.document = None
        self.layout_tree = None
        # Clear image caches
        self.image_cache.clear()
        self.photo_cache.clear()
        logger.debug("Renderer cleared")
    
    def _on_canvas_click(self, event) -> None:
        """
        Handle canvas click events.
        
        Args:
            event: Tkinter event object
        """
        # Find the element at the clicked position
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        element = self._find_element_at_position(x, y)
        
        if element:
            # Check for link
            if element.tag_name.lower() == 'a':
                href = element.get_attribute('href')
                if href and self.on_link_click:
                    self.on_link_click(href)
    
    def _on_resize(self, event) -> None:
        """
        Handle resize events.
        
        Args:
            event: Tkinter event object
        """
        # Update viewport dimensions
        self.viewport_width = event.width
        self.viewport_height = event.height
        
        # Re-render the document if available
        if self.document:
            self.render(self.document)
    
    def _find_element_at_position(self, x: int, y: int) -> Optional[Element]:
        """
        Find the DOM element at a given position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The element at the position, or None if not found
        """
        # Get canvas items at the position
        items = self.canvas.find_overlapping(x, y, x, y)
        
        for item_id in items:
            # Check if the item has an associated element
            element_id = self.canvas.itemcget(item_id, 'tags')
            if element_id and element_id.startswith('element:'):
                # Extract element ID and find in document
                id_parts = element_id.split(':')
                if len(id_parts) >= 2:
                    element_selector = id_parts[1]
                    # Find element in document
                    if self.document:
                        return self.document.query_selector(f"#{element_selector}")
        
        # No element found
        return None
    
    def render(self, document: Document, layout: Optional[LayoutBox] = None) -> None:
        """
        Render the document.
        
        Args:
            document: The document to render
            layout: Optional pre-computed layout to use
        """
        logger.info("Rendering document")
        start_time = time.time()
        
        # Store the document
        self.document = document
        
        # Clear any previous render state
        self._clear_canvas()
        self.processed_nodes = set()
        self.processed_rendered_paragraphs = set()
        
        try:
            # Setup the document title
            title_elements = document.get_elements_by_tag_name('title')
            if title_elements and len(title_elements) > 0 and hasattr(title_elements[0], 'text_content'):
                title = title_elements[0].text_content
                # Update the window title if we can
                try:
                    self.parent.master.title(f"{title} - Wink Browser")
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Error setting up document title: {e}")
        
        # Enhanced debug logging for document state
        logger.debug(f"RENDER DEBUG: document is: {document}")
        logger.debug(f"RENDER DEBUG: document type is: {type(document)}")
        logger.debug(f"RENDER DEBUG: document id: {id(document)}")
        logger.debug(f"RENDER DEBUG: document has url: {hasattr(document, 'url')}")
        logger.debug(f"RENDER DEBUG: document has document_element: {hasattr(document, 'document_element') and document.document_element is not None}")
        logger.debug(f"RENDER DEBUG: self.document before assignment is: {self.document}")
        
        # Store document reference - use direct assignment to avoid reference issues
        old_document = self.document
        self.document = document
        
        # Check if document is valid
        if not document:
            logger.error("Cannot render null document")
            self._show_error_message("No document to render")
            return
            
        # More extensive document validation
        if not hasattr(document, 'document_element') or document.document_element is None:
            logger.error("Document has no document_element")
            self._show_error_message("Document has no structure to render")
            return
            
        # Log document information
        url_str = document.url if hasattr(document, 'url') else 'unknown'
        logger.info(f"Rendering document: {url_str}")
        
        # Count elements with enhanced error handling
        element_count = 0
        try:
            if hasattr(document, 'getElementsByTagName'):
                elements = document.getElementsByTagName('*')
                element_count = len(elements)
                logger.debug(f"Found {element_count} elements using getElementsByTagName")
                
                # Additional validation of the document structure
                if element_count == 0:
                    logger.warning("Document returned 0 elements - checking structure directly")
                    if hasattr(document, 'document_element') and document.document_element is not None:
                        # Try manual counting through traversal
                        def count_elements(node):
                            count = 0
                            if hasattr(node, 'node_type') and node.node_type == getattr(node, 'ELEMENT_NODE', 1):
                                count = 1
                            if hasattr(node, 'child_nodes'):
                                for child in node.child_nodes:
                                    count += count_elements(child)
                            return count
                        
                        manual_count = count_elements(document.document_element)
                        logger.debug(f"Manual traversal found {manual_count} elements")
                        element_count = manual_count
        except Exception as e:
            logger.error(f"Error counting elements: {e}")
            # Continue with rendering
        
        logger.info(f"Document has {element_count} elements")
        
        # Clear any previous content
        self.clear()
        
        # More detailed logging for debugging element detection
        logger.debug(f"RENDER DEBUG: document_element exists: {hasattr(document, 'document_element') and document.document_element is not None}")
        if hasattr(document, 'document_element') and document.document_element is not None:
            logger.debug(f"RENDER DEBUG: document_element tag name: {document.document_element.tag_name}")
            logger.debug(f"RENDER DEBUG: document_element has children: {len(document.document_element.child_nodes) > 0}")
            
            # List all children of document_element for debugging
            if len(document.document_element.child_nodes) > 0:
                logger.debug("Children of document_element:")
                for i, child in enumerate(document.document_element.child_nodes):
                    child_type = getattr(child, 'tag_name', getattr(child, 'node_type', 'unknown'))
                    logger.debug(f"  Child {i}: {child_type}")
        
        # Process all CSS first
        try:
            self._process_all_styles(document)
            logger.debug("CSS styles processed successfully")
        except Exception as e:
            logger.error(f"Error processing CSS styles: {e}")
            # Continue anyway to render what we can
        
        # Execute JavaScript if we have a JS engine
        scripts_executed = False
        if hasattr(self, 'js_engine') and self.js_engine:
            try:
                logger.debug("Executing JavaScript in document")
                self.js_engine.execute_scripts(document)
                scripts_executed = True
                logger.debug("JavaScript executed successfully")
            except Exception as e:
                logger.error(f"Error executing JavaScript: {e}")
        
        # Create layout tree if not provided
        if not layout:
            logger.debug("Creating layout tree")
            try:
                self.layout_tree = self.layout_engine.create_layout(
                    document, 
                    viewport_width=self.viewport_width, 
                    viewport_height=self.viewport_height
                )
                logger.debug("Layout tree created successfully")
            except Exception as e:
                logger.error(f"Error creating layout tree: {e}")
                self._show_error_message(f"Layout error: {str(e)}")
                return
        else:
            logger.debug("Using provided layout tree")
            self.layout_tree = layout
            
        if not self.layout_tree:
            logger.error("Failed to create layout tree")
            self._show_error_message("Failed to create layout")
            return
            
        # Apply the viewport dimensions - use correct method
        try:
            # Try to use layout method if available
            if hasattr(self.layout_tree, 'layout'):
                self.layout_tree.layout(self.viewport_width)
                logger.debug("Applied layout using layout_tree.layout method")
            else:
                # Use the layout engine to layout the tree
                self.layout_engine.layout(self.layout_tree, self.viewport_width, self.viewport_height)
                logger.debug("Applied layout using layout_engine.layout method")
        except Exception as e:
            logger.error(f"Error during layout: {e}")
            # Continue anyway to render what we can
        
        # Render the document
        self._clear_canvas()
        
        # Process the layout tree and sort by z-index before rendering
        try:
            self._prepare_stacking_contexts(self.layout_tree)
            logger.debug("Stacking contexts prepared")
        except Exception as e:
            logger.error(f"Error preparing stacking contexts: {e}")
            # Continue anyway
        
        # Check if we're on the debug page
        is_debug_page = False
        document_url = None
        
        # Try multiple ways to get the document URL
        if hasattr(document, 'url'):
            document_url = document.url
            is_debug_page = document_url == "about:debug"
            logger.debug(f"Document URL from document.url: {document_url}, is_debug_page: {is_debug_page}")
        elif hasattr(self, 'html5_engine') and hasattr(self.html5_engine, 'base_url'):
            document_url = self.html5_engine.base_url
            is_debug_page = document_url == "about:debug"
            logger.debug(f"Document URL from engine.base_url: {document_url}, is_debug_page: {is_debug_page}")
        else:
            logger.debug("Could not determine URL for debug mode check")
            
        # Add direct debugging of document contents
        if document:
            try:
                # Make sure we're using the correct document
                if hasattr(document, 'head') and document.head:
                    logger.debug(f"Document has head element directly: {document.head is not None}")
                    
                if hasattr(document, 'body') and document.body:
                    logger.debug(f"Document has body element directly: {document.body is not None}")
                
                # Try to find title in head
                title_element = None
                if hasattr(document, 'head') and document.head:
                    for child in document.head.child_nodes:
                        if hasattr(child, 'tag_name') and child.tag_name.lower() == 'title':
                            title_element = child
                            break
                
                logger.debug(f"Found title in head: {title_element is not None}")
                if title_element and hasattr(title_element, 'textContent'):
                    logger.debug(f"Title text from head: {title_element.textContent}")
                
                # Try querySelector as fallback
                logger.debug(f"Document has title element: {document.querySelector('title') is not None}")
                title_element = document.querySelector('title')
                if title_element:
                    logger.debug(f"Title element text content: {title_element.textContent if hasattr(title_element, 'textContent') else 'No textContent'}")
                
                # Check for body
                logger.debug(f"Document has body element: {document.querySelector('body') is not None}")
                body_element = document.querySelector('body')
                if body_element:
                    logger.debug(f"Body element has text content: {hasattr(body_element, 'textContent')}")
                    if hasattr(body_element, 'textContent'):
                        logger.debug(f"Body text content sample: {body_element.textContent[:100] if body_element.textContent else 'Empty'}")
                        
                # Attempt to find headings
                for heading in ('h1', 'h2', 'h3'):
                    heading_element = document.querySelector(heading)
                    if heading_element:
                        logger.debug(f"Found {heading} element with text: {heading_element.textContent if hasattr(heading_element, 'textContent') else 'No textContent'}")
            except Exception as e:
                logger.error(f"Error examining document contents: {e}")
        
        # Set a flag for debug mode to be used by other methods
        self.is_debug_mode = is_debug_page
        
        # Render the layout tree using the _render_element method
        try:
            logger.debug("Starting to render layout tree")
            self._render_element(self.layout_tree, 0, 0)
            logger.debug("Layout tree rendered successfully")
        except Exception as e:
            logger.error(f"Error rendering layout tree: {e}")
            self._show_error_message(f"Rendering error: {str(e)}")
        
        # Update scroll region
        try:
            self._update_scroll_region()
            logger.debug("Scroll region updated")
        except Exception as e:
            logger.error(f"Error updating scroll region: {e}")
        
        # Only show debug elements on about:debug page
        if is_debug_page:
            # Add a debug message showing CSS/JS processing status
            if not scripts_executed and self.js_engine:
                debug_text = "⚠️ JavaScript processing issues detected. Scripts may not have executed properly."
                self.canvas.create_text(10, 10, text=debug_text, anchor="nw", fill="red", font=("Arial", 10, "bold"))
            
            # Add a debug rectangle to verify content is being rendered
            debug_rect = self.canvas.create_rectangle(
                150, 150, 300, 300,
                outline="green",
                fill="yellow",
                width=3
            )
            self.canvas_items.append(debug_rect)
            
            # Add some text to verify text rendering works
            debug_text = self.canvas.create_text(
                200, 200,
                text="Example.com content should appear here",
                font=("Arial", 14, "bold"),
                fill="black"
            )
            self.canvas_items.append(debug_text)
            
            # Add a visible header
            header_rect = self.canvas.create_rectangle(
                50, 50, 500, 100,
                outline="blue",
                fill="#d0e0ff",
                width=2
            )
            self.canvas_items.append(header_rect)
            
            header_text = self.canvas.create_text(
                275, 75,
                text="DEBUG MODE",
                font=("Arial", 18, "bold"),
                fill="navy"
            )
            self.canvas_items.append(header_text)
            
            # Display renderer and document information
            debug_info = self.canvas.create_text(
                275, 400,
                text=f"Viewport: {self.viewport_width}x{self.viewport_height}\n"
                     f"Zoom: {self.zoom_level*100}%\n"
                     f"URL: {document.url if hasattr(document, 'url') else 'Unknown'}\n"
                     f"Elements: {self._count_elements(document) if document else 0}",
                font=("Arial", 12),
                fill="black",
                justify="center"
            )
            self.canvas_items.append(debug_info)
            
            logger.debug("Added debug elements in debug mode")
        
        logger.info("Document rendered successfully")
    
    # Helper method to count elements in a document
    def _count_elements(self, document):
        """Count the number of elements in a document."""
        if not document or not hasattr(document, 'getElementsByTagName'):
            return 0
        
        try:
            return len(document.getElementsByTagName('*'))
        except:
            return 0
    
    def _count_elements_manually(self, node):
        """Manually count elements by recursion."""
        if not node:
            return 0
            
        # Start with 1 for this element
        count = 1
        
        # Add count from all child elements
        if hasattr(node, 'child_nodes'):
            for child in node.child_nodes:
                if hasattr(child, 'node_type') and child.node_type == NodeType.ELEMENT_NODE:
                    count += self._count_elements_manually(child)
        
        return count
    
    def _process_all_styles(self, document: Document) -> None:
        """
        Process all CSS styles in the document.
        
        Args:
            document: The document to process styles for
        """
        # Reset the CSS parser first to avoid applying styles from previous documents
        self.css_parser.reset()
        
        # Add default styles (lowest precedence)
        self.css_parser.add_default_styles()
        
        # Process <link> elements for external stylesheets
        if hasattr(document, 'query_selector_all'):
            link_elements = document.query_selector_all('link[rel="stylesheet"]')
            if link_elements:
                for link_element in link_elements:
                    if hasattr(link_element, 'get_attribute'):
                        href = link_element.get_attribute('href')
                        if href:
                            # If we have the stylesheet content already, use it
                            if hasattr(link_element, 'stylesheet_content') and link_element.stylesheet_content:
                                try:
                                    self.css_parser.parse(link_element.stylesheet_content, document.url)
                                except Exception as e:
                                    logger.error(f"Error parsing CSS from linked stylesheet: {e}")
        
        # Process <style> elements (higher precedence than linked stylesheets)
        if hasattr(document, 'query_selector_all'):
            style_elements = document.query_selector_all('style')
            if style_elements:
                for style_element in style_elements:
                    # First check for style_content property, then fallback to text_content
                    css_content = None
                    if hasattr(style_element, 'style_content') and style_element.style_content:
                        css_content = style_element.style_content
                        logger.debug(f"Processing <style> element content: {css_content[:100]}...")
                    elif hasattr(style_element, 'text_content') and style_element.text_content:
                        css_content = style_element.text_content
                        logger.debug(f"Processing <style> element text_content: {css_content[:100]}...")
                    
                    if css_content:
                        try:
                            self.css_parser.parse(css_content)
                        except Exception as e:
                            logger.error(f"Error parsing CSS in style element: {e}")
        
        # Process style attributes on elements (highest precedence except !important)
        if hasattr(document, 'query_selector_all'):
            # Try multiple ways to find elements with style attributes
            elements_with_style = []
            try:
                elements_with_style = document.query_selector_all('[style]')
            except Exception:
                # Fallback: iterate through all elements and check for style attribute
                if hasattr(document, 'get_elements_by_tag_name'):
                    all_elements = document.get_elements_by_tag_name('*')
                    elements_with_style = [el for el in all_elements if el.has_attribute('style')]
            
            if elements_with_style:
                for element in elements_with_style:
                    if hasattr(element, 'get_attribute'):
                        style_attr = element.get_attribute('style')
                        if style_attr:
                            try:
                                # Store the inline styles directly on the element for higher precedence
                                element.inline_styles = self.css_parser.parse_inline_styles(style_attr)
                            except Exception as e:
                                logger.error(f"Error parsing inline style '{style_attr}': {e}")
                                
        # Ensure !important declarations are preserved
        self._process_important_declarations(document)
    
    def _prepare_stacking_contexts(self, layout_box: LayoutBox) -> None:
        """
        Prepare stacking contexts for proper z-index handling.
        This ensures elements are rendered in the correct order based on z-index.
        
        Args:
            layout_box: The root layout box
        """
        if not layout_box:
            return
            
        # Sort children by z-index
        if hasattr(layout_box, 'children') and layout_box.children:
            layout_box.children.sort(key=lambda child: getattr(child, 'z_index', 0))
            
            # Recursively process children
            for child in layout_box.children:
                self._prepare_stacking_contexts(child)
    
    def _clear_canvas(self) -> None:
        """Clear the canvas and reset state."""
        # Delete all canvas items
        for item_id in self.canvas_items:
            try:
                self.canvas.delete(item_id)
            except TclError:
                pass  # Item already deleted
        
        self.canvas_items = []
        
        # Clear the image cache
        self.image_cache.clear()
    
    def _update_scroll_region(self) -> None:
        """Update the scroll region based on the content size."""
        try:
            # Calculate the content bounds
            if not self.layout_tree:
                return
                
            # Get layout tree bounds
            min_x = 0
            min_y = 0
            max_x = self.viewport_width
            max_y = self.viewport_height
            
            # Use layout tree to determine content size
            if hasattr(self.layout_tree, 'box_metrics'):
                # Ensure all values are properly converted to int
                # Handle 'auto' values and other non-numeric values
                def safe_int_convert(value, default=0):
                    """Convert a value to int safely, handling 'auto' and non-numeric values."""
                    if value == 'auto' or value is None:
                        return default
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        logger.debug(f"Converting non-numeric value '{value}' to {default}")
                        return default
                
                # Get box metrics with safe conversion
                x = safe_int_convert(self.layout_tree.box_metrics.x)
                width = safe_int_convert(self.layout_tree.box_metrics.width, self.viewport_width)
                margin_right = safe_int_convert(self.layout_tree.box_metrics.margin_right)
                y = safe_int_convert(self.layout_tree.box_metrics.y)
                height = safe_int_convert(self.layout_tree.box_metrics.height, self.viewport_height)
                margin_bottom = safe_int_convert(self.layout_tree.box_metrics.margin_bottom)
                
                # Width calculation
                total_width = x + width + margin_right
                if total_width > max_x:
                    max_x = total_width

                # Height calculation                
                total_height = y + height + margin_bottom
                if total_height > max_y:
                    max_y = total_height
            
            # Add padding to ensure scrollbar controls are visible
            max_x += 20
            max_y += 20
            
            # Update the scroll region
            self.canvas.configure(scrollregion=(min_x, min_y, max_x, max_y))
            
            # Configure scrollbars
            if hasattr(self, 'frame') and hasattr(self.frame, 'horizontal_scrollbar'):
                if max_x > self.viewport_width:
                    self.frame.horizontal_scrollbar.grid()
                else:
                    self.frame.horizontal_scrollbar.grid_remove()
                    
            if hasattr(self, 'frame') and hasattr(self.frame, 'vertical_scrollbar'):
                if max_y > self.viewport_height:
                    self.frame.vertical_scrollbar.grid()
                else:
                    self.frame.vertical_scrollbar.grid_remove()
                    
            logger.debug(f"Scroll region updated to: ({min_x}, {min_y}, {max_x}, {max_y})")
            
        except Exception as e:
            logger.error(f"Error updating scroll region: {e}")
            
    def _setup_canvas_bindings(self) -> None:
        """Set up canvas event bindings for scrolling and interaction."""
        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
        # Drag scrolling
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)
    
    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        # Determine scroll direction and amount
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # Scroll down
            self.canvas.yview_scroll(1, "units")
    
    def _on_button_press(self, event) -> None:
        """Handle mouse button press for drag scrolling."""
        # Store current coordinates for drag scrolling
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
        # Store current scroll position
        self._drag_scroll_x = self.canvas.canvasx(0)
        self._drag_scroll_y = self.canvas.canvasy(0)
        
        # Change cursor to indicate dragging
        self.canvas.configure(cursor="fleur")
    
    def _on_mouse_drag(self, event) -> None:
        """Handle mouse dragging for scrolling."""
        # Calculate distance moved
        delta_x = event.x - self._drag_start_x
        delta_y = event.y - self._drag_start_y
        
        # Scroll the canvas
        self.canvas.xview_moveto((self._drag_scroll_x - delta_x) / self.canvas.winfo_width())
        self.canvas.yview_moveto((self._drag_scroll_y - delta_y) / self.canvas.winfo_height())
    
    def _on_button_release(self, event) -> None:
        """Handle mouse button release after drag scrolling."""
        # Reset cursor
        self.canvas.configure(cursor="")
    
    def _render_layout_tree(self, layout_tree: LayoutBox) -> None:
        """
        Render a layout tree to the canvas.
        
        Args:
            layout_tree: The layout tree to render
        """
        if not layout_tree:
            logger.error("Cannot render null layout tree")
            
            # Try fallback direct rendering if we have a document but no layout tree
            if self.document and hasattr(self.document, 'document_element') and self.document.document_element is not None:
                logger.warning("Layout tree is null but document exists - attempting fallback direct rendering")
                self._fallback_direct_render(self.document)
            return
        
        # Store the current layout tree for later use
        self.current_layout_tree = layout_tree
            
        # Clear the canvas
        self._clear_canvas()
        
        # Render the layout tree recursively
        self._render_element(layout_tree, 0, 0)
        
        # Update the scroll region
        self._update_scroll_region()
        
        logger.debug("Document rendered")
    
    def _fallback_direct_render(self, document):
        """
        Fallback method to render document content directly when normal rendering fails.
        
        Args:
            document: The document to render
        """
        logger.info("Using fallback direct rendering")
        
        # Clear the canvas
        self._clear_canvas()
        
        # Get document element
        if not hasattr(document, 'document_element') or document.document_element is None:
            self._show_error_message("Document has no content to render")
            return
            
        root = document.document_element
        
        # Extract title
        title = "Untitled"
        if hasattr(document, 'title'):
            title = document.title
        elif hasattr(document, 'getElementsByTagName'):
            try:
                title_elements = document.getElementsByTagName('title')
                if title_elements and len(title_elements) > 0:
                    title = title_elements[0].text_content
            except:
                pass
        
        # Extract body content or use document element if no body
        body = None
        if hasattr(document, 'body') and document.body is not None:
            body = document.body
        elif hasattr(document, 'getElementsByTagName'):
            try:
                body_elements = document.getElementsByTagName('body')
                if body_elements and len(body_elements) > 0:
                    body = body_elements[0]
            except:
                pass
        
        if not body:
            body = root
            
        # Get all visible text content
        text_content = self._extract_text_content(body)
        
        # Render a simple representation of the page
        x, y = 20, 20
        
        # Render title
        title_text = self.canvas.create_text(
            x, y, 
            text=title,
            font=("Arial", 16, "bold"),
            anchor="nw",
            fill="#000000"
        )
        self.canvas_items.append(title_text)
        
        # Update y position
        y += 30
        
        # Render content
        content_text = self.canvas.create_text(
            x, y, 
            text=text_content[:5000],  # Limit text to avoid performance issues
            font=("Arial", 12),
            anchor="nw",
            fill="#000000",
            width=self.viewport_width - 40  # Allow wrapping
        )
        self.canvas_items.append(content_text)
        
        # Update canvas scroll region
        self._update_scroll_region()
    
    def _extract_text_content(self, node):
        """
        Extract visible text content from a node and its descendants.
        
        Args:
            node: The node to extract text from
            
        Returns:
            Extracted text content
        """
        if not node:
            return ""
            
        # Create a unique identifier for this node
        node_id = f"{id(node)}"
        
        # Skip if this node was already processed
        if node_id in self.processed_nodes:
            return ""
        
        # Mark node as processed
        self.processed_nodes.add(node_id)
        
        # Get direct text content
        text = ""
        
        # Get text from this node
        if hasattr(node, 'text_content'):
            text = node.text_content
        elif hasattr(node, 'textContent'):
            text = node.textContent
            
        # Ensure text is not None
        if text is None:
            text = ""
            
        # If node is not a text node itself, recursively get text from children
        if (not text or text.strip() == "") and hasattr(node, 'child_nodes'):
            for child in node.child_nodes:
                # Skip script and style elements
                if hasattr(child, 'tag_name') and child.tag_name.lower() in ['script', 'style']:
                    continue
                    
                child_text = self._extract_text_content(child)
                if child_text is None:
                    child_text = ""
                
                # Add appropriate spacing between elements
                if child_text.strip():
                    if text and not text.endswith('\n'):
                        # Add newline between block elements
                        if hasattr(child, 'tag_name') and child.tag_name.lower() in [
                            'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                            'ul', 'ol', 'li', 'table', 'tr', 'blockquote'
                        ]:
                            text += '\n'
                        # Add space between inline elements
                        elif text and not text.endswith(' '):
                            text += ' '
                    
                    text += child_text
        
        return text
    
    def _render_element_content(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render the content of an element.
        
        Args:
            layout_box: The layout box to render
            x: X coordinate
            y: Y coordinate
            width: Width of the content area
            height: Height of the content area
        """
        element = layout_box.element
        if not element:
            return
            
        # Get tag name
        tag_name = element.tag_name.lower() if hasattr(element, 'tag_name') else ""
        logger.debug(f"Rendering content for element: {tag_name}")
        
        # Skip rendering content of certain elements
        if tag_name == 'script' or tag_name == 'style':
            logger.debug(f"Skipping content rendering for {tag_name} element")
            return
        
        # Handle different element types
        if tag_name == 'img':
            self._render_image(layout_box, x, y, width, height)
        elif tag_name in ('input', 'button', 'textarea', 'select'):
            self._render_form_element(layout_box, x, y, width, height)
        elif tag_name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            # Special handling for headings to ensure they stand out
            self._render_heading_element(layout_box)
        else:
            # For body element, ensure we process all children
            if tag_name == 'body':
                logger.debug(f"Rendering body element with {len(element.child_nodes) if hasattr(element, 'child_nodes') else 0} children")
                
                # If body has no visible content, add a placeholder
                if not self.is_debug_mode and (not hasattr(element, 'child_nodes') or len(element.child_nodes) == 0):
                    logger.debug("Body has no children, adding placeholder text")
                    try:
                        placeholder = self.canvas.create_text(
                            x + 20, y + 20,
                            text="This page has no visible content.",
                            font=("Arial", 14),
                            fill="#666666",
                            anchor="nw"
                        )
                        self.canvas_items.append(placeholder)
                    except Exception as e:
                        logger.error(f"Error adding placeholder text: {e}")
                
                # Process all child nodes to ensure they're rendered
                if hasattr(element, 'child_nodes'):
                    for i, child in enumerate(element.child_nodes):
                        if hasattr(child, 'tag_name'):
                            child_tag = child.tag_name.lower()
                            logger.debug(f"Body child {i}: {child_tag}")
                            
                            # For block elements, ensure they're rendered with proper spacing
                            if child_tag in ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'table'):
                                # These will be rendered by the layout engine through their own layout boxes
                                pass
                        elif hasattr(child, 'nodeType') and child.nodeType == 3:  # Text node
                            # For direct text nodes in the body, render them directly
                            if hasattr(child, 'nodeValue') and child.nodeValue and child.nodeValue.strip():
                                logger.debug(f"Direct text node in body: {child.nodeValue[:50]}...")
                                try:
                                    text_item = self.canvas.create_text(
                                        x + 10, y + 10,
                                        text=child.nodeValue,
                                        font=("Arial", 12),
                                        fill="#000000",
                                        anchor="nw"
                                    )
                                    self.canvas_items.append(text_item)
                                except Exception as e:
                                    logger.error(f"Error rendering direct text node: {e}")
            elif tag_name == 'div':
                # For div elements, ensure we handle them properly
                logger.debug(f"Rendering div element at ({x}, {y}) with dimensions {width}x{height}")
                
                # Check if this is a container div with children but no text
                has_text = False
                if hasattr(element, 'textContent'):
                    has_text = bool(element.textContent.strip())
                
                # If it's a container with no text but with children, we don't need to render text
                if not has_text and hasattr(element, 'child_nodes') and len(element.child_nodes) > 0:
                    logger.debug("Div is a container with no direct text, skipping text rendering")
                    return
            
            # Render text content for all elements
            self._render_text_content(layout_box)
            
            # Special handling for specific elements
            # Check if this is a link element
            if tag_name == 'a':
                # Only use old link implementation if:
                # 1. Link is not inside a paragraph, or
                # 2. Link is inside an empty paragraph
                parent_tag = ""
                parent_element = None
                if hasattr(layout_box.element, 'parent_node') and layout_box.element.parent_node:
                    parent_element = layout_box.element.parent_node
                    if hasattr(parent_element, 'tag_name'):
                        parent_tag = parent_element.tag_name.lower()
                
                use_old_implementation = True
                
                # If parent is a paragraph, check if it has any non-link text content
                if parent_tag == 'p':
                    # First check using the mixed content detection logic used by _render_text_content
                    # to ensure consistency with how paragraphs with links are detected
                    has_links = False
                    has_text = False
                    
                    if hasattr(parent_element, 'child_nodes'):
                        for child in parent_element.child_nodes:
                            if hasattr(child, 'tag_name') and child.tag_name.lower() == 'a':
                                has_links = True
                            elif hasattr(child, 'node_type') and child.node_type == 3:  # Text node
                                if hasattr(child, 'node_value') and child.node_value and child.node_value.strip():
                                    has_text = True
                    
                    # If paragraph has both links and text, don't use old implementation
                    if has_links and has_text:
                        use_old_implementation = False
                    else:
                        # Fallback check - if paragraph has any text content at all
                        has_text_content = False
                        if hasattr(parent_element, 'textContent'):
                            has_text_content = bool(parent_element.textContent.strip())
                        
                        # Only use old implementation if paragraph is empty (no text content)
                        use_old_implementation = not has_text_content
                
                if use_old_implementation:
                    self._make_link_clickable(layout_box, x, y, width, height)
                # Debug logging to help diagnose the issue
                else:
                    logger.debug(f"Skipping old link implementation for link in non-empty paragraph")
            elif tag_name == 'hr':
                self._render_horizontal_rule(layout_box, x, y, width, height)
            elif tag_name == 'br':
                # Nothing to do for <br> - layout engine handles line breaks
                pass
    
    def _render_heading_element(self, layout_box: LayoutBox) -> None:
        """
        Render a heading element (h1-h6).
        
        Args:
            layout_box: The layout box to render
        """
        element = layout_box.element
        if not element or not hasattr(element, 'tag_name'):
            return
            
        tag_name = element.tag_name.lower()
        if not tag_name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            return
            
        # Get text content
        text = ""
        if hasattr(element, 'textContent'):
            text = element.textContent
        elif hasattr(element, 'text_content'):
            text = element.text_content
            
        if not text:
            return
            
        # Get position and dimensions
        x = layout_box.box_metrics.x
        y = layout_box.box_metrics.y
        width = layout_box.box_metrics.width
        
        # Get computed style
        style = layout_box.computed_style if hasattr(layout_box, 'computed_style') else {}
        
        # Determine font size and weight based on heading level
        font_family = style.get('font-family', 'Arial')
        font_size = 0
        
        # Set font size based on heading level
        if tag_name == 'h1':
            font_size = 24
        elif tag_name == 'h2':
            font_size = 22
        elif tag_name == 'h3':
            font_size = 20
        elif tag_name == 'h4':
            font_size = 18
        elif tag_name == 'h5':
            font_size = 16
        elif tag_name == 'h6':
            font_size = 14
        
        # Get text color
        color = style.get('color', '#000000')
        
        # Create font tuple
        font = (font_family, font_size, 'bold')
        
        # Create text with proper wrapping
        try:
            heading_text = self.canvas.create_text(
                x, y,
                text=text,
                font=font,
                fill=color,
                anchor="nw",
                width=width if width != 'auto' and width > 0 else None
            )
            self.canvas_items.append(heading_text)
            
            # No longer adding artificial spacers - rely on natural document flow
            # and the minimal extra spacing in _layout_block_children
            
        except Exception as e:
            logger.error(f"Error rendering heading: {e}")
    
    def _render_media_element(self, layout_box: LayoutBox) -> None:
        """
        Render a media element (audio or video).
        
        Args:
            layout_box: The layout box to render
        """
        element = layout_box.element
        if not element:
            return
            
        # Get media source
        src = element.get_attribute('src') if hasattr(element, 'get_attribute') else None
        
        # Get box dimensions
        x = layout_box.box_metrics.x + layout_box.box_metrics.margin_left + layout_box.box_metrics.border_left_width + layout_box.box_metrics.padding_left
        y = layout_box.box_metrics.y + layout_box.box_metrics.margin_top + layout_box.box_metrics.border_top_width + layout_box.box_metrics.padding_top
        width = layout_box.box_metrics.content_width
        height = layout_box.box_metrics.content_height
        
        # Check if controls should be shown
        has_controls = element.get_attribute('controls') == 'controls' if hasattr(element, 'get_attribute') else False
        
        # Check the element type and call the appropriate renderer
        tag_name = element.tag_name.lower() if hasattr(element, 'tag_name') else ''
        if tag_name == 'audio':
            self._render_audio_element(x, y, width, height, src, has_controls, element)
        elif tag_name == 'video':
            self._render_video_element(x, y, width, height, src, has_controls, element)
    
    def _render_element_box(self, layout_box: LayoutBox) -> None:
        """
        Render a specific element box based on its type.
        
        Args:
            layout_box: The layout box to render
        """
        element = layout_box.element
        if not element or not hasattr(element, 'tag_name'):
            return
            
        # First render the container/background for all elements
        self._render_default_element_box(layout_box)
        
        # Note: We no longer call specific render methods here to avoid duplication
        # The _render_element_content method will handle rendering the specific content
    
    def _render_image_element(self, layout_box: LayoutBox) -> None:
        """
        Render an image element.
        
        Args:
            layout_box: The layout box to render
        """
        element = layout_box.element
        if not element:
            return
            
        # Get image source
        src = element.get_attribute('src') if hasattr(element, 'get_attribute') else None
        if not src:
            return
            
        # Get box dimensions
        x = layout_box.box_metrics.x + layout_box.box_metrics.margin_left + layout_box.box_metrics.border_left_width + layout_box.box_metrics.padding_left
        y = layout_box.box_metrics.y + layout_box.box_metrics.margin_top + layout_box.box_metrics.border_top_width + layout_box.box_metrics.padding_top
        width = layout_box.box_metrics.content_width
        height = layout_box.box_metrics.content_height
        
        # Get parent container dimensions for percentage calculations
        parent_width = layout_box.parent.box_metrics.content_width if layout_box.parent else self.canvas.winfo_width()
        parent_height = layout_box.parent.box_metrics.content_height if layout_box.parent else self.canvas.winfo_height()
        
        # Convert 'auto' to numeric values
        if width == 'auto':
            width = int(parent_width * 0.8)  # Default to 80% of parent width
        elif isinstance(width, str) and width.endswith('%'):
            width = self._convert_percentage_to_pixels(width, parent_width)
        
        if height == 'auto':
            height = int(parent_height * 0.32)  # Default to 32% of parent height
        elif isinstance(height, str) and height.endswith('%'):
            height = self._convert_percentage_to_pixels(height, parent_height)
            
        # Use specified dimensions if provided in element attributes
        if width <= 0 or isinstance(width, str):
            width_attr = element.get_attribute('width') if hasattr(element, 'get_attribute') else None
            if width_attr:
                if width_attr.endswith('%'):
                    width = self._convert_percentage_to_pixels(width_attr, parent_width)
                else:
                    try:
                        width = int(float(width_attr))
                    except (ValueError, TypeError):
                        width = int(parent_width * 0.8)  # Default to 80% of parent width
            else:
                width = int(parent_width * 0.8)  # Default to 80% of parent width
        
        if height <= 0 or isinstance(height, str):
            height_attr = element.get_attribute('height') if hasattr(element, 'get_attribute') else None
            if height_attr:
                if height_attr.endswith('%'):
                    height = self._convert_percentage_to_pixels(height_attr, parent_height)
                else:
                    try:
                        height = int(float(height_attr))
                    except (ValueError, TypeError):
                        height = int(parent_height * 0.32)  # Default to 32% of parent height
            else:
                height = int(parent_height * 0.32)  # Default to 32% of parent height
        
        # Check if we already have the image
        img = self._get_image(src)
        
        if img:
            # Draw the image on the canvas
            try:
                # Create a PhotoImage object
                photo = tk.PhotoImage(data=img)
                
                # Store the photo so it doesn't get garbage collected
                if not hasattr(self, '_photo_cache'):
                    self._photo_cache = {}
                self._photo_cache[src] = photo
                
                # Create the image on the canvas
                image_item = self.canvas.create_image(
                    x, y,
                    image=photo,
                    anchor='nw',
                    tags=f'element:{element.id}' if hasattr(element, 'id') and element.id else ''
                )
                self.canvas_items.append(image_item)
                
                # Add debug rectangle to show image bounds
                if self.draw_debug_boxes:
                    debug_rect = self.canvas.create_rectangle(
                        x, y, x + width, y + height,
                        outline='red',
                        fill='',
                        width=1,
                        tags=f'debug element:{element.id}' if hasattr(element, 'id') and element.id else 'debug'
                    )
                    self.canvas_items.append(debug_rect)
                
                # Log success
                logger.debug(f"Rendered image: {src}")
                return
            except Exception as e:
                logger.error(f"Error rendering image: {e}")
        
        # If we reached here, we couldn't load the image
        # Show a placeholder
        placeholder = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            outline='#CCCCCC',
            fill='#EEEEEE',
            tags=f'element:{element.id}' if hasattr(element, 'id') and element.id else ''
        )
        self.canvas_items.append(placeholder)
        
        # Add a broken image icon
        label = self.canvas.create_text(
            x + width/2, y + height/2,
            text="🖼️",
            font=(self.fonts['default'][0], 14),
            fill='#999999',
            tags=f'element:{element.id}' if hasattr(element, 'id') and element.id else ''
        )
        self.canvas_items.append(label)
        
        # Start loading the image in the background
        self._start_image_loading(src)

    def _start_image_loading(self, src):
        """
        Start loading an image in the background.
        
        Args:
            src: Image source URL
        """
        # Create a thread to load the image
        if not hasattr(self, '_image_loading_threads'):
            self._image_loading_threads = {}
            
        # Skip if already loading
        if src in self._image_loading_threads and self._image_loading_threads[src].is_alive():
            return
            
        # Create a new thread
        thread = threading.Thread(target=self._load_image_in_background, args=(src,))
        thread.daemon = True
        self._image_loading_threads[src] = thread
        thread.start()
        
    def _load_image_in_background(self, src):
        """
        Load an image in the background.

        Args:
            src: Image source URL
        """
        try:
            # Try to load the image synchronously (we're in a background thread)
            image_data = self._get_image(src, async_mode=False)
            if image_data:
                # Schedule a redraw on the main thread
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.after(100, self._redraw_images, src)
        except Exception as e:
            logger.error(f"Error loading image in background: {e}")
    
    def _redraw_images(self, src):
        """
        Redraw images after they've been loaded.
        
        Args:
            src: Image source URL
        """
        # Find all image elements with this source
        if not hasattr(self, 'canvas') or not self.canvas:
            return
            
        # Redraw the entire document for now
        # In a real implementation, would only redraw affected images
        if hasattr(self, 'layout_tree') and self.layout_tree:
            self._clear_canvas()
            self._render_element(self.layout_tree, 0, 0)
            self._update_scroll_region()
    
    def _get_image(self, src, async_mode=True):
        """
        Get an image from a source URL.

        Args:
            src (str): The source URL of the image.
            async_mode (bool): If True, non-cached remote images will be loaded asynchronously.

        Returns:
            PIL.Image.Image: The image object, or None if not in cache and async_mode is True.
        """
        if not src:
            return None

        logger.info(f"Attempting to load image from source: {src}")

        # Check image cache first - always return cached images immediately
        if src in self.image_cache:
            logger.info(f"Found image in cache: {src}")
            return self.image_cache[src]

        # Handle data URLs synchronously (fast, inline data)
        if src.startswith('data:image'):
            try:
                header, encoded = src.split(',', 1)
                is_svg = 'svg+xml' in header.lower()
                decoded = base64.b64decode(encoded)

                if is_svg:
                    try:
                        import cairosvg
                        png_data = cairosvg.svg2png(bytestring=decoded)
                        image = Image.open(BytesIO(png_data))
                    except Exception as e:
                        logger.warning(f"cairosvg not available for SVG: {e}")
                        return None
                else:
                    image = Image.open(BytesIO(decoded))

                self.image_cache[src] = image
                return image
            except Exception as e:
                logger.error(f"Failed to decode data URL: {e}")
                return None

        # Handle local file URLs synchronously (fast)
        if src.startswith('file://') or (not src.startswith(('http://', 'https://')) and os.path.exists(src)):
            try:
                path = src.replace('file://', '') if src.startswith('file://') else src
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        image_data = f.read()

                    is_svg = path.lower().endswith('.svg')
                    if is_svg:
                        try:
                            import cairosvg
                            png_data = cairosvg.svg2png(bytestring=image_data)
                            image = Image.open(BytesIO(png_data))
                        except Exception as e:
                            logger.warning(f"cairosvg not available for SVG: {e}")
                            return None
                    else:
                        image = Image.open(BytesIO(image_data))

                    self.image_cache[src] = image
                    return image
            except Exception as e:
                logger.error(f"Failed to load local image: {e}")
                return None

        # For remote URLs, start async loading if in async mode
        if async_mode and src.startswith(('http://', 'https://')):
            logger.info(f"Image not cached, starting async load: {src}")
            self._start_image_loading(src)
            return None

        # Fallback: try synchronous loading for relative paths and other cases
        try:
                    
            # Get base URL - try multiple sources to ensure we get the correct one
            # Initialize base_url
            base_url = ""
            
            # Try to get the current URL from the document or engine
            current_url = ""
            
            # Check if renderer itself has current_url attribute
            if hasattr(self, 'current_url') and self.current_url:
                current_url = self.current_url
                logger.debug(f"Found current URL from renderer: {current_url}")
            
            # If no URL from renderer, check document
            if not current_url and hasattr(self, 'document') and self.document:
                if hasattr(self.document, 'url') and self.document.url:
                    current_url = self.document.url
                    logger.debug(f"Found current URL from document: {current_url}")
            
            # If no URL from document, try to get from engine
            if not current_url and hasattr(self, 'html5_engine'):
                if hasattr(self.html5_engine, 'current_url') and self.html5_engine.current_url:
                    current_url = self.html5_engine.current_url
                    logger.debug(f"Found current URL from engine.current_url: {current_url}")
                elif hasattr(self.html5_engine, 'base_url') and self.html5_engine.base_url:
                    current_url = self.html5_engine.base_url
                    logger.debug(f"Found current URL from engine.base_url: {current_url}")
            
            # Extract base URL from current URL using regex
            if current_url:
                # Use urllib.parse instead of regex for more robust URL handling
                import urllib.parse
                parsed_url = urllib.parse.urlparse(current_url)
                
                # Get the origin (scheme + netloc)
                origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # For absolute paths, we'll use the origin
                if src.startswith('/'):
                    # Use urljoin to properly handle the path
                    full_url = urllib.parse.urljoin(origin, src)
                    logger.debug(f"Resolved absolute path against origin: {full_url}")
                    
                    # Try to load the image from the full URL
                    try:
                        # Use network manager if available
                        if self.network_manager:
                            logger.info(f"Using network manager to fetch: {full_url}")
                            response = self.network_manager.get(full_url)
                            if response and response.content:
                                # Check if it's an SVG
                                content_type = response.headers.get('Content-Type', '').lower()
                                is_svg = 'svg+xml' in content_type
                                
                                if is_svg:
                                    # Convert SVG to PNG using cairosvg
                                    import cairosvg
                                    png_data = cairosvg.svg2png(bytestring=response.content)
                                    image = Image.open(BytesIO(png_data))
                                else:
                                    # For regular images, use the content directly
                                    image = Image.open(BytesIO(response.content))
                                
                                self.image_cache[src] = image
                                return image
                        
                        # Fallback to direct request
                        logger.info(f"Falling back to direct request: {full_url}")
                        import urllib.request
                        from io import BytesIO
                        
                        with urllib.request.urlopen(full_url) as response:
                            image_data = response.read()
                            content_type = response.headers.get('Content-Type', '').lower()
                            is_svg = 'svg+xml' in content_type
                        
                            if is_svg:
                                # Convert SVG to PNG using cairosvg
                                import cairosvg
                                png_data = cairosvg.svg2png(bytestring=image_data)
                                image = Image.open(BytesIO(png_data))
                            else:
                                # For regular images, use the image data directly
                                image = Image.open(BytesIO(image_data))
                            
                            self.image_cache[src] = image
                            return image
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            logger.info(f"404 error for {full_url}, trying alternative URL formats")
                            # Try alternative URL formats
                            alternative_urls = []
                            
                            # If URL has www, try without it
                            if 'www.' in full_url:
                                alternative_urls.append(full_url.replace('www.', ''))
                            
                            # If URL doesn't have www, try with it
                            if not 'www.' in full_url:
                                scheme, rest = full_url.split('://')
                                alternative_urls.append(f"{scheme}://www.{rest}")
                            
                            # Try removing subdomain if present
                            if '.' in parsed_url.netloc and not parsed_url.netloc.startswith('www.'):
                                netloc_parts = parsed_url.netloc.split('.')
                                if len(netloc_parts) > 2:
                                    alternative_urls.append(f"{parsed_url.scheme}://{'.'.join(netloc_parts[1:])}{parsed_url.path}")
                            
                            # Try each alternative URL
                            for alt_url in alternative_urls:
                                try:
                                    logger.info(f"Trying alternative URL: {alt_url}")
                                    if self.network_manager:
                                        response = self.network_manager.get(alt_url)
                                        if response and response.content:
                                            image_data = response.read()
                                            content_type = response.headers.get('Content-Type', '').lower()
                                            is_svg = 'svg+xml' in content_type
                        
                                            if is_svg:
                                                # Convert SVG to PNG using cairosvg
                                                import cairosvg
                                                png_data = cairosvg.svg2png(bytestring=image_data)
                                                image = Image.open(BytesIO(png_data))
                                            else:
                                                # For regular images, use the image data directly
                                                image = Image.open(BytesIO(image_data))
                                            self.image_cache[src] = image
                                            return image
                                    
                                    with urllib.request.urlopen(alt_url) as response:
                                        image_data = response.read()
                                        content_type = response.headers.get('Content-Type', '').lower()
                                        is_svg = 'svg+xml' in content_type
                        
                                        if is_svg:
                                            # Convert SVG to PNG using cairosvg
                                            import cairosvg
                                            png_data = cairosvg.svg2png(bytestring=image_data)
                                            image = Image.open(BytesIO(png_data))
                                        else:
                                            # For regular images, use the image data directly
                                            image = Image.open(BytesIO(image_data))
                                        self.image_cache[src] = image
                                        return image
                                except Exception as alt_e:
                                    logger.debug(f"Failed to load from alternative URL {alt_url}: {alt_e}")
                                    continue
                            
                            logger.error(f"All alternative URLs failed for {full_url}")
                        else:
                            logger.error(f"HTTP error {e.code} for URL {full_url}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to load image from URL {full_url}: {e}")
                        # Continue with other methods if this fails
                else:
                    # For relative paths, we'll use the directory of the current URL as base
                    path_parts = parsed_url.path.split('/')
                    if '.' in path_parts[-1]:  # If the last part looks like a file
                        path_parts.pop()  # Remove the file part
                    
                    # Reconstruct the base URL for relative paths
                    path = '/'.join(path_parts)
                    if not path.endswith('/'):
                        path += '/'
                        
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
                    full_url = urllib.parse.urljoin(base_url, src)
                    logger.debug(f"Resolved relative path against directory: {full_url}")
                    
                    # Try to load the image from the full URL
                    try:
                        # Use network manager if available
                        if self.network_manager:
                            logger.info(f"Using network manager to fetch: {full_url}")
                            response = self.network_manager.get(full_url)
                            if response and response.content:
                                # Check if it's an SVG
                                content_type = response.headers.get('Content-Type', '').lower()
                                is_svg = 'svg+xml' in content_type
                                
                                if is_svg:
                                    # Convert SVG to PNG using cairosvg
                                    import cairosvg
                                    png_data = cairosvg.svg2png(bytestring=response.content)
                                    image = Image.open(BytesIO(png_data))
                                else:
                                    # For regular images, use the content directly
                                    image = Image.open(BytesIO(response.content))
                                
                                self.image_cache[src] = image
                                return image
                        
                        # Fallback to direct request
                        logger.info(f"Falling back to direct request: {full_url}")
                        import urllib.request
                        from io import BytesIO
                        
                        with urllib.request.urlopen(full_url) as response:
                            image_data = response.read()
                            content_type = response.headers.get('Content-Type', '').lower()
                            is_svg = 'svg+xml' in content_type
                        
                            if is_svg:
                                # Convert SVG to PNG using cairosvg
                                import cairosvg
                                png_data = cairosvg.svg2png(bytestring=image_data)
                                image = Image.open(BytesIO(png_data))
                            else:
                                # For regular images, use the image data directly
                                image = Image.open(BytesIO(image_data))
                            
                            self.image_cache[src] = image
                            return image
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            logger.info(f"404 error for {full_url}, trying alternative URL formats")
                            # Try alternative URL formats
                            alternative_urls = []
                            
                            # If URL has www, try without it
                            if 'www.' in full_url:
                                alternative_urls.append(full_url.replace('www.', ''))
                            
                            # If URL doesn't have www, try with it
                            if not 'www.' in full_url:
                                scheme, rest = full_url.split('://')
                                alternative_urls.append(f"{scheme}://www.{rest}")
                            
                            # Try removing subdomain if present
                            if '.' in parsed_url.netloc and not parsed_url.netloc.startswith('www.'):
                                netloc_parts = parsed_url.netloc.split('.')
                                if len(netloc_parts) > 2:
                                    alternative_urls.append(f"{parsed_url.scheme}://{'.'.join(netloc_parts[1:])}{parsed_url.path}")
                            
                            # Try each alternative URL
                            for alt_url in alternative_urls:
                                try:
                                    logger.info(f"Trying alternative URL: {alt_url}")
                                    if self.network_manager:
                                        response = self.network_manager.get(alt_url)
                                        if response and response.content:
                                            image_data = response.read()
                                            content_type = response.headers.get('Content-Type', '').lower()
                                            is_svg = 'svg+xml' in content_type
                        
                                            if is_svg:
                                                # Convert SVG to PNG using cairosvg
                                                import cairosvg
                                                png_data = cairosvg.svg2png(bytestring=image_data)
                                                image = Image.open(BytesIO(png_data))
                                            else:
                                                # For regular images, use the image data directly
                                                image = Image.open(BytesIO(image_data))
                                            self.image_cache[src] = image
                                            return image
                                    
                                    with urllib.request.urlopen(alt_url) as response:
                                        image_data = response.read()
                                        content_type = response.headers.get('Content-Type', '').lower()
                                        is_svg = 'svg+xml' in content_type
                        
                                        if is_svg:
                                            # Convert SVG to PNG using cairosvg
                                            import cairosvg
                                            png_data = cairosvg.svg2png(bytestring=image_data)
                                            image = Image.open(BytesIO(png_data))
                                        else:
                                            # For regular images, use the image data directly
                                            image = Image.open(BytesIO(image_data))
                                        self.image_cache[src] = image
                                        return image
                                except Exception as alt_e:
                                    logger.debug(f"Failed to load from alternative URL {alt_url}: {alt_e}")
                                    continue
                            
                            logger.error(f"All alternative URLs failed for {full_url}")
                        else:
                            logger.error(f"HTTP error {e.code} for URL {full_url}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to load image from URL {full_url}: {e}")
            
            logger.debug(f"Determined base URL: {base_url}")
            
            # If we haven't already tried to load from a URL above, try now with full_url
            if full_url.startswith(('http://', 'https://')) and full_url != src:
                try:
                    # Try to use the network manager if available
                    if self.network_manager:
                        logger.info(f"Using network manager to fetch: {full_url}")
                        response = self.network_manager.get(full_url)
                        if response and response.content:
                            # Check if it's an SVG
                            content_type = response.headers.get('Content-Type', '').lower()
                            is_svg = 'svg+xml' in content_type
                            
                            if is_svg:
                                # Convert SVG to PNG using cairosvg
                                import cairosvg
                                png_data = cairosvg.svg2png(bytestring=response.content)
                                image = Image.open(BytesIO(png_data))
                            else:
                                # For regular images, use the content directly
                                image = Image.open(BytesIO(response.content))
                            
                            self.image_cache[src] = image
                            return image
                    
                    # Fallback to direct request
                    logger.info(f"Falling back to direct request: {full_url}")
                    import urllib.request
                    from io import BytesIO
                    
                    with urllib.request.urlopen(full_url) as response:
                        image_data = response.read()
                        content_type = response.headers.get('Content-Type', '').lower()
                        is_svg = 'svg+xml' in content_type
                        
                        if is_svg:
                            # Convert SVG to PNG using cairosvg
                            import cairosvg
                            png_data = cairosvg.svg2png(bytestring=image_data)
                            image = Image.open(BytesIO(png_data))
                        else:
                            # For regular images, use the image data directly
                            image = Image.open(BytesIO(image_data))
                        image = Image.open(BytesIO(image_data))
                        self.image_cache[src] = image
                        return image
                except Exception as e:
                    logger.error(f"Failed to load image from URL {full_url}: {e}")
            
            # Last resort: try local files (this is unlikely to work for web pages but might for local files)
            logger.warning("Remote image loading failed, attempting local file paths as last resort")
            try:
                # Try different possible paths
                paths_to_try = [
                    src.replace('file://', ''),  # Remove file:// prefix
                    os.path.join(os.getcwd(), src.lstrip('/')),  # Relative to CWD
                    os.path.normpath(src)  # Normalized path
                ]
                
                # If we have a base URL that's a file path, try relative to that
                if base_url and base_url.startswith('file://'):
                    base_path = base_url.replace('file://', '')
                    base_dir = os.path.dirname(base_path)
                    paths_to_try.insert(0, os.path.join(base_dir, src))
                
                for path in paths_to_try:
                    logger.info(f"Trying path: {path}")
                    if os.path.exists(path):
                        image_data = open(path, 'rb').read()
                        # Check if it's an SVG file by extension
                        is_svg = path.lower().endswith('.svg')
                        
                        if is_svg:
                            # Convert SVG to PNG using cairosvg
                            import cairosvg
                            png_data = cairosvg.svg2png(bytestring=image_data)
                            image = Image.open(BytesIO(png_data))
                        else:
                            # For regular images, use the image data directly
                            image = Image.open(BytesIO(image_data))
                        
                        # Cache and return the image regardless of format
                        self.image_cache[src] = image
                        return image
                
                logger.error(f"No valid path found for image: {src}")
                return None
                
            except Exception as e:
                logger.error(f"Failed to load image from file: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return None
    
    def _render_element(self, layout_box: LayoutBox, x_offset: int = 0, y_offset: int = 0) -> None:
        """
        Render a layout box and its children.
        
        Args:
            layout_box: The layout box to render
            x_offset: X offset for positioning
            y_offset: Y offset for positioning
        """
        if not layout_box or not layout_box.element:
            return
            
        tag_name = layout_box.element.tag_name.lower() if hasattr(layout_box.element, 'tag_name') else 'unknown'
        
        # Calculate dimensions safely
        try:
            # Calculate width
            if isinstance(layout_box.box_metrics.content_width, (int, float)):
                width = layout_box.box_metrics.content_width
            elif isinstance(layout_box.box_metrics.content_width, str):
                if layout_box.box_metrics.content_width == 'auto':
                    # For auto width, use parent's width minus padding and borders
                    if layout_box.parent:
                        parent_width = layout_box.parent.box_metrics.content_width
                        if isinstance(parent_width, (int, float)):
                            width = parent_width - layout_box.box_metrics.padding_left - layout_box.box_metrics.padding_right - layout_box.box_metrics.border_left_width - layout_box.box_metrics.border_right_width
                        else:
                            width = self.viewport_width * 0.8  # Default to 80% of viewport
                    else:
                        width = self.viewport_width * 0.8  # Default to 80% of viewport
                else:
                    try:
                        width = int(layout_box.box_metrics.content_width)
                    except (ValueError, TypeError):
                        width = self.viewport_width * 0.8  # Default to 80% of viewport
            else:
                width = self.viewport_width * 0.8  # Default to 80% of viewport

            # Calculate height
            if isinstance(layout_box.box_metrics.content_height, (int, float)):
                height = layout_box.box_metrics.content_height
            elif isinstance(layout_box.box_metrics.content_height, str):
                if layout_box.box_metrics.content_height == 'auto':
                    # For auto height, calculate based on content or use aspect ratio
                    if layout_box.children:
                        # Calculate based on children's total height
                        total_height = 0
                        for child in layout_box.children:
                            if isinstance(child.box_metrics.margin_box_height, (int, float)):
                                total_height += child.box_metrics.margin_box_height
                        height = total_height if total_height > 0 else int(width * 0.6)  # Use aspect ratio if no height
                    else:
                        height = int(width * 0.6)  # Default aspect ratio
                else:
                    try:
                        height = int(layout_box.box_metrics.content_height)
                    except (ValueError, TypeError):
                        height = int(width * 0.6)  # Default aspect ratio
            else:
                height = int(width * 0.6)  # Default aspect ratio
        except Exception as e:
            logger.error(f"Error calculating dimensions: {e}")
            # Use safe defaults
            width = self.viewport_width * 0.8
            height = int(width * 0.6)
        
        # Get box metrics
        if hasattr(layout_box, 'box_metrics'):
            x = layout_box.box_metrics.x + x_offset
            y = layout_box.box_metrics.y + y_offset
            
            # Log box metrics for debugging
            logger.debug(f"Box metrics for {tag_name}: x={x}, y={y}, width={width}, height={height}")
        else:
            x = getattr(layout_box, 'x', 0) + x_offset
            y = getattr(layout_box, 'y', 0) + y_offset
            logger.debug(f"Using fallback positioning for {tag_name}: x={x}, y={y}, width={width}, height={height}")
            
        # Get computed style
        style = layout_box.computed_style if hasattr(layout_box, 'computed_style') else {}
        
        # Skip rendering if element is not visible
        display = style.get('display', 'block')
        visibility = style.get('visibility', 'visible')
        
        if display == 'none' or visibility == 'hidden':
            logger.debug(f"Skipping invisible element {tag_name}: display={display}, visibility={visibility}")
            return
            
        # Get z-index
        z_index = style.get('z-index', 'auto')
        
        # Render the element's background and border
        self._render_background(layout_box, x, y, width, height)
        self._render_border(layout_box, x, y, width, height)
        
        # Render the element's content
        self._render_element_content(layout_box, x, y, width, height)
        
        # Render children
        if hasattr(layout_box, 'children') and layout_box.children:
            logger.debug(f"Rendering {len(layout_box.children)} children of {tag_name}")
            for child in layout_box.children:
                self._render_element(child, x_offset, y_offset)
        else:
            logger.debug(f"Element {tag_name} has no children to render")
    
    def _render_background(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render the background of an element.
        
        Args:
            layout_box: The layout box to render the background for.
            x: The x coordinate of the top-left corner.
            y: The y coordinate of the top-left corner.
            width: The width of the element.
            height: The height of the element.
        """
        if not layout_box or not layout_box.element:
            return
            
        # Get the computed style for the element
        style = layout_box.computed_style
        if not style:
            return
            
        # Get the background color
        bg_color = style.get('background-color', 'transparent')
        if bg_color == 'transparent':
            return
            
        # Convert the color to a format Tkinter can understand
        try:
            # Handle named colors
            if bg_color in NAMED_COLORS:
                bg_color = NAMED_COLORS[bg_color]
                
            # Handle hex colors
            if bg_color.startswith('#'):
                # Ensure it's a valid hex color
                if len(bg_color) == 4:  # #RGB format
                    r = bg_color[1] * 2
                    g = bg_color[2] * 2
                    b = bg_color[3] * 2
                    bg_color = f"#{r}{g}{b}"
                    
            # Handle rgb() format
            elif bg_color.startswith('rgb('):
                # Extract the RGB values
                rgb_values = bg_color[4:-1].split(',')
                if len(rgb_values) == 3:
                    r = int(rgb_values[0].strip())
                    g = int(rgb_values[1].strip())
                    b = int(rgb_values[2].strip())
                    bg_color = f"#{r:02x}{g:02x}{b:02x}"
                    
            # Create a rectangle for the background
            bg_rect = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=bg_color,
                outline=""  # No outline
            )
            self.canvas_items.append(bg_rect)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error rendering background: {e}")
            # Continue with rendering even if background fails
    
    def _safe_divide(self, a, b):
        """
        Safely divide two values, handling 'auto' strings by converting them to 0.
        Also handles percentage strings by converting them to proportional values.
        
        Args:
            a: The numerator
            b: The denominator
            
        Returns:
            The result of a/b, or 0 if either value is 'auto'
        """
        # Handle 'auto' values
        if a == 'auto':
            a = 0
        if b == 'auto':
            b = 0
        
        # Handle percentage values
        if isinstance(a, str) and a.endswith('%'):
            try:
                percentage = float(a[:-1]) / 100.0
                # If we have a parent value, use it to calculate the actual value
                if isinstance(b, (int, float)) and b > 0:
                    return percentage * b
                return percentage
            except (ValueError, TypeError):
                a = 0
        
        # Ensure both values are numeric
        try:
            a = float(a)
            b = float(b)
            return a / b if b != 0 else 0
        except (ValueError, TypeError):
            return 0

    def _convert_percentage_to_pixels(self, value, parent_dimension):
        """
        Convert a percentage value to pixels based on parent dimension.
        
        Args:
            value: The value to convert, can be int, float, or string with % suffix
            parent_dimension: The parent dimension to base the calculation on
            
        Returns:
            The pixel value as an int
        """
        if not value:
            return 0
            
        if isinstance(value, str):
            # Handle percentage values
            if value.endswith('%'):
                try:
                    percentage = float(value[:-1]) / 100.0
                    return int(percentage * parent_dimension)
                except (ValueError, TypeError):
                    return 0
            
            # Handle 'auto' values
            if value == 'auto':
                return 0
            
            # Handle pixel values
            if value.endswith('px'):
                try:
                    return int(float(value[:-2]))
                except (ValueError, TypeError):
                    return 0
        
        # Try to convert to int directly if it's not a string
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _process_important_declarations(self, document: Document) -> None:
        """
        Process !important declarations and ensure they have highest precedence.
        
        Args:
            document: The document to process
        """
        if not hasattr(document, 'query_selector_all'):
            return
            
        # Process all style rules to find !important declarations
        important_rules = {}
        
        # Check default styles for !important
        for selector, props in self.css_parser.default_style_rules.items():
            important_props = {}
            for prop, value in props.items():
                if isinstance(value, str) and '!important' in value:
                    important_props[prop] = value.replace('!important', '').strip()
            
            if important_props:
                if selector not in important_rules:
                    important_rules[selector] = {}
                important_rules[selector].update(important_props)
        
        # Check site styles for !important (higher precedence than default)
        for stylesheet in self.css_parser.stylesheets:
            for selector, props in stylesheet.items():
                important_props = {}
                for prop, value in props.items():
                    if isinstance(value, str) and '!important' in value:
                        important_props[prop] = value.replace('!important', '').strip()
                
                if important_props:
                    if selector not in important_rules:
                        important_rules[selector] = {}
                    important_rules[selector].update(important_props)
        
        # Store these as a separate collection with highest precedence
        self.css_parser.important_rules = important_rules

    def _show_error_message(self, message: str) -> None:
        """
        Display an error message on the canvas.
        
        Args:
            message: The error message to display
        """
        try:
            # Clear any existing content
            self._clear_canvas()
            
            # Create error container
            error_bg = self.canvas.create_rectangle(
                50, 50, self.viewport_width - 50, 150,
                outline="#ff0000",
                fill="#ffeeee",
                width=2
            )
            self.canvas_items.append(error_bg)
            
            # Create error icon
            error_icon = self.canvas.create_text(
                70, 70,
                text="⚠️",
                font=("Arial", 24),
                fill="#ff0000",
                anchor="nw"
            )
            self.canvas_items.append(error_icon)
            
            # Create error title
            error_title = self.canvas.create_text(
                110, 70,
                text="Rendering Error",
                font=("Arial", 16, "bold"),
                fill="#ff0000",
                anchor="nw"
            )
            self.canvas_items.append(error_title)
            
            # Create error message
            error_text = self.canvas.create_text(
                70, 100,
                text=message,
                font=("Arial", 12),
                fill="#000000",
                anchor="nw",
                width=self.viewport_width - 140
            )
            self.canvas_items.append(error_text)
            
            # Add a suggestion
            suggestion = self.canvas.create_text(
                70, 130,
                text="Try refreshing the page or check the console for more details.",
                font=("Arial", 10, "italic"),
                fill="#666666",
                anchor="nw"
            )
            self.canvas_items.append(suggestion)
            
            logger.error(f"Displayed error message: {message}")
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")

    def render_elements(self, head: Optional[Element], body: Optional[Element], url: Optional[str] = None) -> None:
        """
        Render a page using specific head and body elements.
        
        Args:
            head: The head element containing styles and metadata
            body: The body element containing page content
            url: The URL of the document (optional)
        """
        logger.debug(f"Rendering page with direct head and body elements")
        
        # Log element information
        logger.debug(f"Head element: {head}")
        logger.debug(f"Body element: {body}")
        
        # Clear any previous content
        self.clear()
        
        # Set current URL if provided
        if url:
            logger.debug(f"Setting current_url to: {url}")
            self.current_url = url
        
        # Verify body element exists
        if not body:
            logger.error("Cannot render: Body element is missing")
            self._show_error_message("No body element to render")
            return
        
        # Process CSS from head element
        if head:
            logger.debug("Processing CSS from head element")
            try:
                # Process styles from <style> elements
                style_elements = head.get_elements_by_tag_name('style')
                logger.debug(f"Found {len(style_elements)} style elements in head")
                
                # Reset the CSS parser
                self.css_parser.reset()
                self.css_parser.add_default_styles()
                
                # Process each style element
                for style_element in style_elements:
                    if hasattr(style_element, 'text_content') and style_element.text_content:
                        try:
                            logger.debug(f"Processing style element content")
                            self.css_parser.parse(style_element.text_content, self.current_url if hasattr(self, 'current_url') else None)
                        except Exception as e:
                            logger.error(f"Error parsing style element: {e}")
                
                # Process link elements for external stylesheets
                link_elements = head.get_elements_by_tag_name('link')
                for link in link_elements:
                    if link.get_attribute('rel') == 'stylesheet' and link.get_attribute('href'):
                        href = link.get_attribute('href')
                        logger.debug(f"Found stylesheet link: {href}")
                        if hasattr(link, 'stylesheet_content') and link.stylesheet_content:
                            try:
                                self.css_parser.parse(link.stylesheet_content, self.current_url if hasattr(self, 'current_url') else None)
                            except Exception as e:
                                logger.error(f"Error parsing linked stylesheet: {e}")
                
                logger.debug("CSS styles from head processed successfully")
            except Exception as e:
                logger.error(f"Error processing CSS from head: {e}")
        
        # Create layout tree for body
        try:
            logger.debug("Creating layout tree for body element")
            self.layout_tree = self.layout_engine.create_layout_for_element(
                body, 
                viewport_width=self.viewport_width, 
                viewport_height=self.viewport_height
            )
            logger.debug("Layout tree for body created successfully")
        except Exception as e:
            logger.error(f"Error creating layout tree for body: {e}")
            self._show_error_message(f"Layout error: {str(e)}")
            
            # Fall back to direct rendering of body content
            self._fallback_direct_render_element(body)
            return
        
        # Verify layout tree was created
        if not self.layout_tree:
            logger.error("Failed to create layout tree for body")
            self._fallback_direct_render_element(body)
            return
        
        # Apply layout to the tree
        try:
            if hasattr(self.layout_tree, 'layout'):
                self.layout_tree.layout(self.viewport_width)
                logger.debug("Applied layout using layout_tree.layout method")
            else:
                self.layout_engine.layout(self.layout_tree, self.viewport_width, self.viewport_height)
                logger.debug("Applied layout using layout_engine.layout method")
        except Exception as e:
            logger.error(f"Error during layout: {e}")
            self._fallback_direct_render_element(body)
            return
        
        # Clear the canvas before rendering
        self._clear_canvas()
        
        # Prepare stacking contexts
        try:
            self._prepare_stacking_contexts(self.layout_tree)
            logger.debug("Stacking contexts prepared")
        except Exception as e:
            logger.error(f"Error preparing stacking contexts: {e}")
            
        # Render the body's layout tree
        try:
            logger.debug("Rendering body element layout tree")
            self._render_layout_tree(self.layout_tree)
            logger.debug("Body layout tree rendered successfully")
        except Exception as e:
            logger.error(f"Error rendering layout tree: {e}")
            self._fallback_direct_render_element(body)
            return
        
        logger.info("Page elements rendered successfully")
        
    def _fallback_direct_render_element(self, element: Element) -> None:
        """
        Fallback method to render a single element directly when layout rendering fails.
        
        Args:
            element: The element to render
        """
        logger.info(f"Using fallback direct rendering for element: {element.tag_name if hasattr(element, 'tag_name') else 'unknown'}")
        
        # Clear the canvas
        self._clear_canvas()
        
        # Get title if available from parent document
        title = "Untitled"
        if hasattr(element, 'owner_document') and element.owner_document:
            document = element.owner_document
            if hasattr(document, 'title'):
                title = document.title
        
        # Get text content from the element
        text_content = self._extract_text_content(element)
        
        # Ensure text_content is not None
        if text_content is None:
            text_content = "No content available"
        
        # Render a simple representation of the element
        x, y = 20, 20
        
        # Render title
        title_text = self.canvas.create_text(
            x, y, 
            text=title,
            font=("Arial", 16, "bold"),
            anchor="nw",
            fill="#000000"
        )
        self.canvas_items.append(title_text)
        
        # Update y position
        y += 30
        
        # Render content
        content_text = self.canvas.create_text(
            x, y, 
            text=text_content[:5000],  # Limit text to avoid performance issues
            font=("Arial", 12),
            anchor="nw",
            fill="#000000",
            width=self.viewport_width - 40  # Allow wrapping
        )
        self.canvas_items.append(content_text)
        
        # Update canvas scroll region
        self._update_scroll_region()

    def _render_horizontal_rule(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render a horizontal rule element.
        
        Args:
            layout_box: The layout box for the hr element
            x: X coordinate
            y: Y coordinate
            width: Width of the element
            height: Height of the element
        """
        # Create a horizontal line
        line = self.canvas.create_line(
            x, y + height // 2, 
            x + width, y + height // 2,
            fill="#cccccc",
            width=1
        )
        self.canvas_items.append(line)
        
    def _make_link_clickable(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Make a link element clickable.
        
        Args:
            layout_box: The layout box for the link element
            x: X coordinate
            y: Y coordinate
            width: Width of the element
            height: Height of the element
        """
        if not layout_box.element:
            return
        
        # Create a unique identifier for this element to check if already processed
        element_id = f"{id(layout_box.element)}"
        if element_id in self.processed_nodes:
            logger.debug(f"Skipping already processed link element: {element_id}")
            return
            
        # Get the href attribute
        href = layout_box.element.get_attribute('href') if hasattr(layout_box.element, 'get_attribute') else None
        
        if not href:
            return
        
        # Only check parent node if we're sure the parent has already been rendered
        # with paragraph-style method
        if hasattr(layout_box.element, 'parent_node') and layout_box.element.parent_node:
            parent = layout_box.element.parent_node
            parent_id = f"{id(parent)}"
            
            # Check if parent has been rendered with paragraph style
            if parent_id in self.processed_rendered_paragraphs:
                logger.debug(f"Skipping link in already rendered paragraph: {element_id}")
                self.processed_nodes.add(element_id)
                return
        
        # Mark this element as processed to avoid duplicate rendering
        self.processed_nodes.add(element_id)
        
        # For standalone links, create a clickable text with underline using the paragraph-style approach
        logger.debug(f"Using paragraph-style rendering for standalone link: {href}")
        
        # Get font settings from computed style
        font_family = "Arial"
        font_size = 12
        font_weight = "normal"
        font_style = "normal"
        
        if hasattr(layout_box, 'computed_style'):
            font_family = layout_box.computed_style.get('font-family', font_family)
            font_size_str = layout_box.computed_style.get('font-size', str(font_size))
            font_weight = layout_box.computed_style.get('font-weight', font_weight)
            font_style = layout_box.computed_style.get('font-style', font_style)
            
            # Convert font size to integer
            try:
                if isinstance(font_size_str, str):
                    if font_size_str.endswith('px'):
                        font_size = int(font_size_str[:-2])
                    else:
                        font_size = int(font_size_str)
                else:
                    font_size = int(font_size_str)
            except (ValueError, TypeError):
                font_size = 12  # Fallback to default size
        
        # Create base font configuration
        base_font = (font_family, font_size)
        
        if font_weight == 'bold':
            base_font = (font_family, font_size, 'bold')
        if font_style == 'italic':
            if len(base_font) == 2:
                base_font = (font_family, font_size, 'italic')
            else:
                base_font = (font_family, font_size, 'bold italic')
                
        # Add underline for links
        if len(base_font) == 2:
            link_font = (base_font[0], base_font[1], 'underline')
        else:
            link_font = (base_font[0], base_font[1], base_font[2] + ' underline')
        
        # Get link text
        link_text = ""
        if hasattr(layout_box.element, 'text_content'):
            link_text = layout_box.element.text_content
        elif hasattr(layout_box.element, 'textContent'):
            link_text = layout_box.element.textContent
        elif hasattr(layout_box.element, 'text'):
            link_text = layout_box.element.text
            
        # If no text content, try to get from child nodes
        if not link_text or not link_text.strip():
            link_text = self._extract_text_content(layout_box.element)
            
        if not link_text or not link_text.strip():
            link_text = href  # Use href as fallback text
            
        # Link color
        link_color = self.colors.get('link', '#0000EE')
        
        # Render link text
        link_item = self.canvas.create_text(
            x, y,
            text=link_text,
            font=link_font,
            fill=link_color,
            anchor="nw"
        )
        self.canvas_items.append(link_item)
        
        # Get actual text dimensions
        bbox = self.canvas.bbox(link_item)
        if bbox:
            actual_width = bbox[2] - bbox[0]
            actual_height = bbox[3] - bbox[1]
            
            # Make link clickable
            clickable_area = self.canvas.create_rectangle(
                x, y, 
                x + actual_width, y + actual_height,
                fill='',
                outline='',
                tags=('link', href)
            )
            self.canvas_items.append(clickable_area)
            
            # Bind click event
            self.canvas.tag_bind(clickable_area, '<Button-1>', 
                                 lambda event, url=href: self._on_link_click(event, url))
            self.canvas.tag_bind(clickable_area, '<Enter>', 
                                 lambda event: self.canvas.config(cursor='hand2'))
            self.canvas.tag_bind(clickable_area, '<Leave>', 
                                 lambda event: self.canvas.config(cursor=''))
    
    def _on_link_click(self, event, url: str) -> None:
        """
        Handle link click events.
        
        Args:
            event: The click event
            url: The URL to navigate to
        """
        # Call the link click callback if registered
        if self.on_link_click:
            self.on_link_click(url)
            
    def _render_image(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render an image element.
        
        Args:
            layout_box: The layout box for the image
            x: X coordinate
            y: Y coordinate
            width: Width of the image
            height: Height of the image
        """
        element = layout_box.element
        if not element:
            return
            
        # Get image source
        src = element.get_attribute('src') if hasattr(element, 'get_attribute') else None
        if not src:
            return
            
        # Try to get the image
        img = self._get_image(src)
        
        if img:
            try:
                # Convert PIL Image to PhotoImage if needed
                if src not in self.photo_cache:
                    # Ensure dimensions are integers
                    width = int(width)
                    height = int(height)
                    
                    # Resize image if needed
                    if width != img.width or height != img.height:
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    self.photo_cache[src] = photo
                else:
                    photo = self.photo_cache[src]
                
                # Create the image on the canvas
                image_item = self.canvas.create_image(
                    int(x), int(y),  # Ensure coordinates are integers
                    image=photo,
                    anchor='nw',
                    tags=f'element:{element.id}' if hasattr(element, 'id') and element.id else ''
                )
                self.canvas_items.append(image_item)
                
                # Add debug rectangle if enabled
                if self.draw_debug_boxes:
                    debug_rect = self.canvas.create_rectangle(
                        int(x), int(y), int(x + width), int(y + height),  # Ensure all coordinates are integers
                        outline='red',
                        fill='',
                        width=1,
                        tags=f'debug element:{element.id}' if hasattr(element, 'id') and element.id else 'debug'
                    )
                    self.canvas_items.append(debug_rect)
                
                logger.debug(f"Rendered image: {src}")
                return
                
            except Exception as e:
                logger.error(f"Error rendering image: {e}")
        
        # If we get here, show a placeholder
        self._render_image_placeholder(layout_box, int(x), int(y), int(width), int(height), element)
    
    def _render_button_element(self, x, y, width, height, text, element, is_disabled=False):
        """
        Render a button element.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Width of the button
            height: Height of the button
            text: Button text
            element: The button element
            is_disabled: Whether the button is disabled
        """
        # Determine colors based on disabled state
        if is_disabled:
            bg_color = '#e0e0e0'
            text_color = '#a0a0a0'
            border_color = '#c0c0c0'
        else:
            bg_color = '#f0f0f0'
            text_color = '#000000'
            border_color = '#c0c0c0'
            
        # Create button with rounded corners
        button = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=bg_color,
            outline=border_color,
            width=1
        )
        self.canvas_items.append(button)
        
        # Add text
        text_item = self.canvas.create_text(
            x + width // 2, y + height // 2,
            text=text,
            fill=text_color,
            anchor='center',
            font=('Arial', 10)
        )
        self.canvas_items.append(text_item)
        
        # Make button clickable if not disabled
        if not is_disabled:
            clickable_area = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill='',
                outline='',
                tags=('button', str(id(element)))
            )
            self.canvas_items.append(clickable_area)
            
            # Change cursor to hand when hovering over the button
            self.canvas.tag_bind(clickable_area, '<Enter>', lambda event: self.canvas.config(cursor='hand2'))
            self.canvas.tag_bind(clickable_area, '<Leave>', lambda event: self.canvas.config(cursor=''))
    
    def _render_border(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render the border of an element.
        
        Args:
            layout_box: The layout box to render the border for.
            x: The x coordinate of the top-left corner.
            y: The y coordinate of the top-left corner.
            width: The width of the element.
            height: The height of the element.
        """
        if not layout_box or not layout_box.element:
            return
            
        # Get the computed style for the element
        style = layout_box.computed_style
        if not style:
            return
            
        # Get border properties
        border_top_width = self._parse_size(style.get('border-top-width', '0px'))
        border_right_width = self._parse_size(style.get('border-right-width', '0px'))
        border_bottom_width = self._parse_size(style.get('border-bottom-width', '0px'))
        border_left_width = self._parse_size(style.get('border-left-width', '0px'))
        
        # If no borders, return early
        if border_top_width == 0 and border_right_width == 0 and border_bottom_width == 0 and border_left_width == 0:
            return
            
        # Get border colors
        border_top_color = style.get('border-top-color', 'black')
        border_right_color = style.get('border-right-color', 'black')
        border_bottom_color = style.get('border-bottom-color', 'black')
        border_left_color = style.get('border-left-color', 'black')
        
        # Convert colors to Tkinter format
        border_top_color = self._convert_color(border_top_color)
        border_right_color = self._convert_color(border_right_color)
        border_bottom_color = self._convert_color(border_bottom_color)
        border_left_color = self._convert_color(border_left_color)
        
        # Get border styles
        border_top_style = style.get('border-top-style', 'none')
        border_right_style = style.get('border-right-style', 'none')
        border_bottom_style = style.get('border-bottom-style', 'none')
        border_left_style = style.get('border-left-style', 'none')
        
        # Draw borders if they have width and are not 'none'
        try:
            # Top border
            if border_top_width > 0 and border_top_style != 'none':
                top_border = self.canvas.create_line(
                    x, y, x + width, y,
                    width=border_top_width,
                    fill=border_top_color
                )
                self.canvas_items.append(top_border)
                
            # Right border
            if border_right_width > 0 and border_right_style != 'none':
                right_border = self.canvas.create_line(
                    x + width, y, x + width, y + height,
                    width=border_right_width,
                    fill=border_right_color
                )
                self.canvas_items.append(right_border)
                
            # Bottom border
            if border_bottom_width > 0 and border_bottom_style != 'none':
                bottom_border = self.canvas.create_line(
                    x, y + height, x + width, y + height,
                    width=border_bottom_width,
                    fill=border_bottom_color
                )
                self.canvas_items.append(bottom_border)
                
            # Left border
            if border_left_width > 0 and border_left_style != 'none':
                left_border = self.canvas.create_line(
                    x, y, x, y + height,
                    width=border_left_width,
                    fill=border_left_color
                )
                self.canvas_items.append(left_border)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error rendering border: {e}")
            # Continue with rendering even if border fails
    
    def _convert_color(self, color: str) -> str:
        """
        Convert a CSS color to a format Tkinter can understand.
        
        Args:
            color: The CSS color to convert.
            
        Returns:
            The color in a format Tkinter can understand.
        """
        if not color:
            return 'black'
            
        # Handle named colors
        if color in NAMED_COLORS:
            return NAMED_COLORS[color]
            
        # Handle hex colors
        if color.startswith('#'):
            # Ensure it's a valid hex color
            if len(color) == 4:  # #RGB format
                r = color[1] * 2
                g = color[2] * 2
                b = color[3] * 2
                return f"#{r}{g}{b}"
            return color
            
        # Handle rgb() format
        if color.startswith('rgb('):
            # Extract the RGB values
            rgb_values = color[4:-1].split(',')
            if len(rgb_values) == 3:
                r = int(rgb_values[0].strip())
                g = int(rgb_values[1].strip())
                b = int(rgb_values[2].strip())
                return f"#{r:02x}{g:02x}{b:02x}"
                
        # Default to black if color format is not recognized
        return 'black'
    
    def _parse_size(self, size: str) -> int:
        """
        Parse a CSS size value into pixels.
        
        Args:
            size: The CSS size value to parse.
            
        Returns:
            The size in pixels.
        """
        if not size:
            return 0
            
        # Remove whitespace
        size = size.strip()
        
        # Handle pixel values
        if size.endswith('px'):
            try:
                return int(float(size[:-2]))
            except ValueError:
                return 0
                
        # Handle em values (assume 1em = 16px)
        if size.endswith('em'):
            try:
                return int(float(size[:-2]) * 16)
            except ValueError:
                return 0
                
        # Handle rem values (assume 1rem = 16px)
        if size.endswith('rem'):
            try:
                return int(float(size[:-3]) * 16)
            except ValueError:
                return 0
                
        # Handle percentage values (assume percentage of parent width)
        if size.endswith('%'):
            try:
                # Default to 0 as we don't have parent width information here
                return 0
            except ValueError:
                return 0
                
        # Handle numeric values without units (assume pixels)
        try:
            return int(float(size))
        except ValueError:
            return 0

    def _calculate_dimension(self, value, container_dimension: int, element_type: str = None, dimension_type: str = 'width', layout_box=None) -> int:
        """
        Calculate a dimension value, handling 'auto' and percentages.
        
        Args:
            value: The dimension value to calculate
            container_dimension: The dimension of the containing block
            element_type: Type of element ('block', 'inline', etc.)
            dimension_type: Type of dimension ('width' or 'height')
            layout_box: The layout box being calculated
            
        Returns:
            Calculated dimension in pixels
        """
        try:
            # Handle numeric values
            if isinstance(value, (int, float)):
                return int(value)
            
            # Handle string values
            if isinstance(value, str):
                # Handle 'auto'
                if value == 'auto':
                    if dimension_type == 'width':
                        if element_type == 'block':
                            # Block elements take full container width minus margins, padding, and borders
                            if layout_box:
                                # Get all box model properties
                                margin_left = layout_box.box_metrics.margin_left
                                margin_right = layout_box.box_metrics.margin_right
                                padding_left = layout_box.box_metrics.padding_left
                                padding_right = layout_box.box_metrics.padding_right
                                border_left = layout_box.box_metrics.border_left_width
                                border_right = layout_box.box_metrics.border_right_width
                                
                                # Convert string values to float, handling 'auto' as 0
                                if isinstance(margin_left, str):
                                    margin_left = 0 if margin_left == 'auto' else float(margin_left)
                                if isinstance(margin_right, str):
                                    margin_right = 0 if margin_right == 'auto' else float(margin_right)
                                if isinstance(padding_left, str):
                                    padding_left = 0 if padding_left == 'auto' else float(padding_left)
                                if isinstance(padding_right, str):
                                    padding_right = 0 if padding_right == 'auto' else float(padding_right)
                                if isinstance(border_left, str):
                                    border_left = 0 if border_left == 'auto' else float(border_left)
                                if isinstance(border_right, str):
                                    border_right = 0 if border_right == 'auto' else float(border_right)
                                
                                # Calculate total box model properties
                                total_margin = margin_left + margin_right
                                total_padding = padding_left + padding_right
                                total_border = border_left + border_right
                                
                                # Content width fills available space
                                return int(container_dimension - total_margin - total_padding - total_border)
                            return int(container_dimension * 0.95)  # 95% of container if no metrics
                        else:
                            # Inline elements use percentage of container
                            return int(container_dimension * 0.8)  # 80% of container width
                    else:  # height
                        if layout_box and layout_box.children:
                            # Calculate based on children
                            total_height = 0
                            for child in layout_box.children:
                                if isinstance(child.box_metrics.margin_box_height, (int, float)):
                                    total_height += child.box_metrics.margin_box_height
                            if total_height > 0:
                                return total_height
                        # Default to aspect ratio based on width
                        width = self._calculate_dimension(layout_box.box_metrics.content_width, container_dimension, element_type, 'width', layout_box) if layout_box else container_dimension
                        return int(width * 0.6)  # Default aspect ratio
                
                # Handle percentage values
                if value.endswith('%'):
                    try:
                        percentage = float(value[:-1]) / 100
                        return int(container_dimension * percentage)
                    except (ValueError, TypeError):
                        pass
                
                # Try converting numeric string
                try:
                    return int(value)
                except (ValueError, TypeError):
                    pass
            
            # Fallback values
            if dimension_type == 'width':
                return int(container_dimension * 0.8)  # 80% of container
            else:  # height
                width = self._calculate_dimension(layout_box.box_metrics.content_width, container_dimension, element_type, 'width', layout_box) if layout_box else container_dimension
                return int(width * 0.6)  # Default aspect ratio
                
        except Exception as e:
            logger.error(f"Error calculating {dimension_type}: {e}")
            # Ultimate fallback
            if dimension_type == 'width':
                return int(container_dimension * 0.8)
            return int(container_dimension * 0.5)

    def _render_text_content(self, layout_box):
        """
        Render text content for a layout box.
        
        Args:
            layout_box: The layout box containing text to render
        """
        try:
            if not layout_box or not layout_box.element:
                return
                
            element = layout_box.element
            
            # Skip script and style tags
            if hasattr(element, 'tag_name') and element.tag_name.lower() in ('script', 'style'):
                return
                
            # Create a unique identifier for this element
            element_id = f"{id(element)}"
            
            # Skip if this element was already rendered
            if element_id in self.processed_nodes:
                return
            
            # Mark element as processed
            self.processed_nodes.add(element_id)
            
            # Special handling for link elements - always use paragraph-style rendering
            if hasattr(element, 'tag_name') and element.tag_name.lower() == 'a':
                logger.debug(f"Using paragraph-style rendering for link element: {element.tag_name}")
                # Create a temporary paragraph-like layout box to render this link
                self._render_paragraph_with_links(layout_box)
                return
            
            # Check if this is a container that might contain inline links
            if hasattr(element, 'tag_name') and element.tag_name.lower() in ('p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li') and hasattr(element, 'child_nodes'):
                # Check if container has links or other inline elements
                has_links = False
                has_text = False
                has_other_inline = False
                
                for child in element.child_nodes:
                    if hasattr(child, 'tag_name'):
                        tag = child.tag_name.lower()
                        if tag == 'a':
                            has_links = True
                        elif tag in ('span', 'em', 'strong', 'b', 'i', 'u', 'code', 'small', 'big', 'sub', 'sup'):
                            has_other_inline = True
                    elif hasattr(child, 'node_type') and child.node_type == 3:  # Text node
                        if hasattr(child, 'node_value') and child.node_value and child.node_value.strip():
                            has_text = True
                
                # Use paragraph-style rendering for mixed content or whenever there's a link
                if has_links:  # Simplified condition - always use paragraph style if there are links
                    logger.debug(f"Using paragraph-style rendering for content with links in {element.tag_name}")
                    self._render_paragraph_with_links(layout_box)
                    return
            
            # Standard text rendering for elements without inline links
            
            # Get text content
            text = None
            if hasattr(element, 'text_content'):
                text = element.text_content
            elif hasattr(element, 'textContent'):
                text = element.textContent
            elif hasattr(element, 'text'):
                text = element.text
                
            if not text:
                # Try to get text from child nodes
                text = self._extract_text_content(element)
                
            if not text or not text.strip():
                return
                
            # Get positioning from box metrics
            x = layout_box.box_metrics.x + layout_box.box_metrics.padding_left + layout_box.box_metrics.border_left_width
            y = layout_box.box_metrics.y + layout_box.box_metrics.padding_top + layout_box.box_metrics.border_top_width
            
            # Get font settings from computed style
            font_family = "Arial"  # Default font
            font_size = 12  # Default size
            font_weight = "normal"
            font_style = "normal"
            
            if hasattr(layout_box, 'computed_style'):
                font_family = layout_box.computed_style.get('font-family', font_family)
                font_size_str = layout_box.computed_style.get('font-size', str(font_size))
                font_weight = layout_box.computed_style.get('font-weight', font_weight)
                font_style = layout_box.computed_style.get('font-style', font_style)
                
                # Convert font size to integer
                try:
                    if isinstance(font_size_str, str):
                        if font_size_str.endswith('px'):
                            font_size = int(font_size_str[:-2])
                        else:
                            font_size = int(font_size_str)
                    else:
                        font_size = int(font_size_str)
                except (ValueError, TypeError):
                    font_size = 12  # Fallback to default size
            
            # Create font configuration
            font_config = (font_family, font_size)
            
            if font_weight == 'bold':
                font_config = (font_family, font_size, 'bold')
            if font_style == 'italic':
                if len(font_config) == 2:
                    font_config = (font_family, font_size, 'italic')
                else:
                    font_config = (font_family, font_size, 'bold italic')
            
            # Text color from computed style
            color = "#000000"
            if hasattr(layout_box, 'computed_style'):
                color = layout_box.computed_style.get('color', color)
            
            # Get element tag for specific adjustments
            tag_name = element.tag_name.lower() if hasattr(element, 'tag_name') else ''
            
            # Calculate available width for text wrapping
            element_type = 'block' if layout_box.display == 'block' else 'inline'
            available_width = self._calculate_dimension(
                layout_box.box_metrics.content_width,
                self.viewport_width,
                element_type,
                'width',
                layout_box
            )
            
            if available_width <= 0:
                available_width = None  # Let text flow naturally if no width constraint
            
            # Create text with proper wrapping
            text_item = self.canvas.create_text(
                x, y,
                text=text.strip(),
                font=font_config,
                fill=color,
                anchor="nw",
                width=available_width,
                tags=("text", tag_name)  # Add tags for better management
            )
            
            # Store the text item for later reference
            self.canvas_items.append(text_item)
            
            # Update layout box height based on text dimensions
            bbox = self.canvas.bbox(text_item)
            if bbox:
                text_height = bbox[3] - bbox[1]
                layout_box.box_metrics.content_height = max(layout_box.box_metrics.content_height, text_height)
            
        except Exception as e:
            logger.error(f"Error in text rendering: {e}")
    
    def _render_paragraph_with_links(self, layout_box):
        """
        Render a paragraph with inline links, maintaining proper text flow.
        
        Args:
            layout_box: The layout box for the paragraph element
        """
        try:
            element = layout_box.element
            if not element:
                return
                
            # Create a unique identifier for this element
            element_id = f"{id(element)}"
            
            # Skip if the element has already been processed
            if element_id in self.processed_rendered_paragraphs:
                logger.debug(f"Skipping already rendered paragraph with links: {element_id}")
                return
                
            # Mark this paragraph as being rendered (to avoid duplicate rendering of child links)
            self.in_progress_paragraphs.add(element_id)
            
            element_tag = element.tag_name.lower() if hasattr(element, 'tag_name') else 'unknown'
            logger.debug(f"Rendering with paragraph-style links: {element_tag}")
            
            # Get paragraph position and dimensions
            x = layout_box.box_metrics.x + layout_box.box_metrics.padding_left + layout_box.box_metrics.border_left_width
            y = layout_box.box_metrics.y + layout_box.box_metrics.padding_top + layout_box.box_metrics.border_top_width
            
            # Calculate available width for paragraph
            element_type = 'block' if layout_box.display == 'block' else 'inline'
            available_width = self._calculate_dimension(
                layout_box.box_metrics.content_width,
                self.viewport_width,
                element_type,
                'width',
                layout_box
            )
            
            if available_width <= 0:
                available_width = None  # Let text flow naturally if no width constraint
            
            # Default font settings
            font_family = "Arial"
            font_size = 12
            font_weight = "normal"
            font_style = "normal"
            
            # Get font settings from computed style
            if hasattr(layout_box, 'computed_style'):
                font_family = layout_box.computed_style.get('font-family', font_family)
                font_size_str = layout_box.computed_style.get('font-size', str(font_size))
                font_weight = layout_box.computed_style.get('font-weight', font_weight)
                font_style = layout_box.computed_style.get('font-style', font_style)
                
                # Convert font size to integer
                try:
                    if isinstance(font_size_str, str):
                        if font_size_str.endswith('px'):
                            font_size = int(font_size_str[:-2])
                        else:
                            font_size = int(font_size_str)
                    else:
                        font_size = int(font_size_str)
                except (ValueError, TypeError):
                    font_size = 12  # Fallback to default size
            
            # Text color from computed style
            default_color = "#000000"
            if hasattr(layout_box, 'computed_style'):
                default_color = layout_box.computed_style.get('color', default_color)
            
            # Create font configuration
            base_font = (font_family, font_size)
            
            if font_weight == 'bold':
                base_font = (font_family, font_size, 'bold')
            if font_style == 'italic':
                if len(base_font) == 2:
                    base_font = (font_family, font_size, 'italic')
                else:
                    base_font = (font_family, font_size, 'bold italic')
            
            # Track current position for text flow
            current_x = x
            current_y = y
            line_height = font_size * 1.2  # Estimate line height
            max_width = available_width if available_width else self.viewport_width - x - 20
            current_line_width = 0
            
            # Special handling for standalone link elements
            if element_tag == 'a':
                # Mark this link as processed
                self.processed_nodes.add(element_id)
                
                href = element.get_attribute('href') if hasattr(element, 'get_attribute') else None
                if href:
                    # Get link text
                    link_text = ""
                    if hasattr(element, 'text_content'):
                        link_text = element.text_content
                    elif hasattr(element, 'textContent'):
                        link_text = element.textContent
                    elif hasattr(element, 'text'):
                        link_text = element.text
                        
                    # If no text content, try to get from child nodes
                    if not link_text or not link_text.strip():
                        link_text = self._extract_text_content(element)
                        
                    if not link_text or not link_text.strip():
                        link_text = href  # Use href as fallback text
                    
                    # Create font for link (with underline)
                    link_font = base_font
                    if len(link_font) == 2:
                        link_font = (link_font[0], link_font[1], 'underline')
                    else:
                        link_font = (link_font[0], link_font[1], link_font[2] + ' underline')
                    
                    # Link color
                    link_color = self.colors.get('link', '#0000EE')
                    
                    # Render link text
                    link_item = self.canvas.create_text(
                        current_x, current_y,
                        text=link_text,
                        font=link_font,
                        fill=link_color,
                        anchor="nw"
                    )
                    self.canvas_items.append(link_item)
                    
                    # Get actual text dimensions
                    bbox = self.canvas.bbox(link_item)
                    if bbox:
                        actual_width = bbox[2] - bbox[0]
                        actual_height = bbox[3] - bbox[1]
                        
                        # Make link clickable
                        clickable_area = self.canvas.create_rectangle(
                            current_x, current_y, 
                            current_x + actual_width, current_y + actual_height,
                            fill='',
                            outline='',
                            tags=('link', href)
                        )
                        self.canvas_items.append(clickable_area)
                        
                        # Bind click event
                        self.canvas.tag_bind(clickable_area, '<Button-1>', 
                                            lambda event, url=href: self._on_link_click(event, url))
                        self.canvas.tag_bind(clickable_area, '<Enter>', 
                                            lambda event: self.canvas.config(cursor='hand2'))
                        self.canvas.tag_bind(clickable_area, '<Leave>', 
                                            lambda event: self.canvas.config(cursor=''))
                        
                        # Update the layout box content height
                        layout_box.box_metrics.content_height = max(layout_box.box_metrics.content_height, actual_height)
                
                # Mark paragraph as fully rendered
                self.processed_rendered_paragraphs.add(element_id)
                # Remove from in-progress tracking
                if element_id in self.in_progress_paragraphs:
                    self.in_progress_paragraphs.remove(element_id)
                return
            
            # Set to keep track of rendered link IDs within this paragraph
            rendered_links = set()
            
            # Process mixed content for container elements
            for child in element.child_nodes if hasattr(element, 'child_nodes') else []:
                # Handle link elements
                if hasattr(child, 'tag_name') and child.tag_name.lower() == 'a':
                    # Create a unique ID for this link
                    link_id = f"{id(child)}"
                    
                    # Skip if this link has already been rendered
                    if link_id in rendered_links:
                        logger.debug(f"Skipping already rendered link in paragraph: {link_id}")
                        continue
                    
                    # Mark this link as rendered within this paragraph
                    rendered_links.add(link_id)
                    
                    # Mark the link as processed globally
                    self.processed_nodes.add(link_id)
                    
                    # Get link text and href
                    link_text = ""
                    if hasattr(child, 'text_content'):
                        link_text = child.text_content
                    elif hasattr(child, 'textContent'):
                        link_text = child.textContent
                    elif hasattr(child, 'text'):
                        link_text = child.text
                    
                    # If no direct text, try to extract from child nodes
                    if not link_text or not link_text.strip():
                        link_text = self._extract_text_content(child)
                    
                    href = child.get_attribute('href') if hasattr(child, 'get_attribute') else ""
                    
                    logger.debug(f"Rendering link in paragraph: {link_text} -> {href}")
                    
                    if not link_text.strip():
                        continue
                    
                    # Get the link's computed style if available
                    link_style = getattr(child, 'computed_style', {}) if hasattr(child, 'computed_style') else {}
                    
                    # Use link-specific font if available
                    link_font = base_font
                    
                    # Apply specific styling from the link if available
                    link_font_family = link_style.get('font-family', font_family)
                    link_font_size_str = link_style.get('font-size', str(font_size))
                    link_font_weight = link_style.get('font-weight', font_weight)
                    link_font_style = link_style.get('font-style', font_style)
                    
                    # Convert link font size to integer
                    try:
                        if isinstance(link_font_size_str, str):
                            if link_font_size_str.endswith('px'):
                                link_font_size = int(link_font_size_str[:-2])
                            else:
                                link_font_size = int(link_font_size_str)
                        else:
                            link_font_size = int(link_font_size_str)
                    except (ValueError, TypeError):
                        link_font_size = font_size  # Use parent font size as fallback
                    
                    # Build link font
                    link_font = (link_font_family, link_font_size)
                    
                    if link_font_weight == 'bold':
                        link_font = (link_font_family, link_font_size, 'bold')
                    if link_font_style == 'italic':
                        if len(link_font) == 2:
                            link_font = (link_font_family, link_font_size, 'italic')
                        else:
                            link_font = (link_font_family, link_font_size, 'bold italic')
                    
                    # Estimate text width (rough approximation)
                    char_width = link_font_size * 0.6  # Average character width
                    text_width = len(link_text) * char_width
                    
                    # Check if we need to wrap to next line
                    if current_line_width + text_width > max_width:
                        current_x = x
                        current_y += line_height
                        current_line_width = 0
                    
                    # Create link color
                    link_color = self.colors.get('link', '#0000EE')
                    # Use link's specified color if available
                    if 'color' in link_style:
                        link_color = link_style.get('color')
                    
                    # Add underline for links
                    if len(link_font) == 2:
                        link_font = (link_font[0], link_font[1], 'underline')
                    else:
                        link_font = (link_font[0], link_font[1], link_font[2] + ' underline')
                    
                    # Render link text
                    link_item = self.canvas.create_text(
                        current_x, current_y,
                        text=link_text,
                        font=link_font,
                        fill=link_color,
                        anchor="nw"
                    )
                    self.canvas_items.append(link_item)
                    
                    # Get actual text dimensions
                    bbox = self.canvas.bbox(link_item)
                    if bbox:
                        actual_width = bbox[2] - bbox[0]
                        actual_height = bbox[3] - bbox[1]
                        
                        # Make link clickable
                        clickable_area = self.canvas.create_rectangle(
                            current_x, current_y, 
                            current_x + actual_width, current_y + actual_height,
                            fill='',
                            outline='',
                            tags=('link', href)
                        )
                        self.canvas_items.append(clickable_area)
                        
                        # Bind click event
                        self.canvas.tag_bind(clickable_area, '<Button-1>', 
                                             lambda event, url=href: self._on_link_click(event, url))
                        self.canvas.tag_bind(clickable_area, '<Enter>', 
                                             lambda event: self.canvas.config(cursor='hand2'))
                        self.canvas.tag_bind(clickable_area, '<Leave>', 
                                             lambda event: self.canvas.config(cursor=''))
                        # Update position for next element
                        current_x += actual_width
                        current_line_width += actual_width
                        line_height = max(line_height, actual_height)
                    else:
                        # Fallback if we couldn't get bbox
                        current_x += text_width
                        current_line_width += text_width
                
                # Handle text nodes
                elif hasattr(child, 'node_type') and child.node_type == 3:  # Text node
                    if hasattr(child, 'node_value') and child.node_value:
                        text = child.node_value.strip()
                        
                        if not text:
                            continue
                        
                        # Estimate text width
                        char_width = font_size * 0.6
                        text_width = len(text) * char_width
                        
                        # Check if we need to wrap to next line
                        if current_line_width + text_width > max_width:
                            current_x = x
                            current_y += line_height
                            current_line_width = 0
                        
                        # Create text item
                        text_item = self.canvas.create_text(
                            current_x, current_y,
                            text=text,
                            font=base_font,
                            fill=default_color,
                            anchor="nw"
                        )
                        self.canvas_items.append(text_item)
                        
                        # Get actual text dimensions
                        bbox = self.canvas.bbox(text_item)
                        if bbox:
                            actual_width = bbox[2] - bbox[0]
                            actual_height = bbox[3] - bbox[1]
                            
                            # Update position for next element
                            current_x += actual_width
                            current_line_width += actual_width
                            line_height = max(line_height, actual_height)
                        else:
                            # Fallback if we couldn't get bbox
                            current_x += text_width
                            current_line_width += text_width
                
                # Handle other inline elements
                elif hasattr(child, 'tag_name'):
                    # Handle other inline elements by rendering them at the current position
                    tag_name = child.tag_name.lower()
                    
                    # Get text from this inline element
                    text = ""
                    if hasattr(child, 'text_content'):
                        text = child.text_content
                    elif hasattr(child, 'textContent'):
                        text = child.textContent
                    elif hasattr(child, 'text'):
                        text = child.text
                    
                    # If no direct text, try to extract from child nodes
                    if not text or not text.strip():
                        text = self._extract_text_content(child)
                    
                    if not text.strip():
                        continue
                    
                    # Get element's computed style if available
                    elem_style = getattr(child, 'computed_style', {}) if hasattr(child, 'computed_style') else {}
                    
                    # Create specific font for this inline element
                    inline_font = base_font
                    
                    # Apply element-specific styling
                    inline_font_family = elem_style.get('font-family', font_family)
                    inline_font_size_str = elem_style.get('font-size', str(font_size))
                    inline_font_weight = elem_style.get('font-weight', font_weight)
                    inline_font_style = elem_style.get('font-style', font_style)
                    
                    # Convert inline font size to integer
                    try:
                        if isinstance(inline_font_size_str, str):
                            if inline_font_size_str.endswith('px'):
                                inline_font_size = int(inline_font_size_str[:-2])
                            else:
                                inline_font_size = int(inline_font_size_str)
                        else:
                            inline_font_size = int(inline_font_size_str)
                    except (ValueError, TypeError):
                        inline_font_size = font_size  # Use parent font size as fallback
                    
                    # Build inline element font
                    inline_font = (inline_font_family, inline_font_size)
                    
                    # Apply specific styling for known tags
                    if tag_name in ('b', 'strong'):
                        inline_font = (inline_font_family, inline_font_size, 'bold')
                    elif tag_name in ('i', 'em'):
                        inline_font = (inline_font_family, inline_font_size, 'italic')
                    elif tag_name == 'u':
                        if len(inline_font) == 2:
                            inline_font = (inline_font_family, inline_font_size, 'underline')
                        else:
                            inline_font = (inline_font_family, inline_font_size, inline_font[2] + ' underline')
                    
                    # Apply combined styling
                    if inline_font_weight == 'bold' and 'bold' not in str(inline_font):
                        if len(inline_font) == 2:
                            inline_font = (inline_font_family, inline_font_size, 'bold')
                        else:
                            inline_font = (inline_font_family, inline_font_size, 'bold ' + inline_font[2])
                    
                    if inline_font_style == 'italic' and 'italic' not in str(inline_font):
                        if len(inline_font) == 2:
                            inline_font = (inline_font_family, inline_font_size, 'italic')
                        else:
                            inline_font = (inline_font_family, inline_font_size, inline_font[2] + ' italic')
                    
                    # Estimate text width
                    char_width = inline_font_size * 0.6
                    text_width = len(text) * char_width
                    
                    # Check if we need to wrap to next line
                    if current_line_width + text_width > max_width:
                        current_x = x
                        current_y += line_height
                        current_line_width = 0
                    
                    # Get text color
                    text_color = default_color
                    if 'color' in elem_style:
                        text_color = elem_style.get('color')
                    
                    # Create text item
                    text_item = self.canvas.create_text(
                        current_x, current_y,
                        text=text,
                        font=inline_font,
                        fill=text_color,
                        anchor="nw"
                    )
                    self.canvas_items.append(text_item)
                    
                    # Get actual text dimensions
                    bbox = self.canvas.bbox(text_item)
                    if bbox:
                        actual_width = bbox[2] - bbox[0]
                        actual_height = bbox[3] - bbox[1]
                        
                        # Update position for next element
                        current_x += actual_width
                        current_line_width += actual_width
                        line_height = max(line_height, actual_height)
                    else:
                        # Fallback if we couldn't get bbox
                        current_x += text_width
                        current_line_width += text_width
            
            # Update the layout box content height based on the rendered text
            total_height = current_y + line_height - y
            layout_box.box_metrics.content_height = max(layout_box.box_metrics.content_height, total_height)
            
            # Mark paragraph as completely rendered
            self.processed_rendered_paragraphs.add(element_id)
            # Remove from in-progress tracking
            if element_id in self.in_progress_paragraphs:
                self.in_progress_paragraphs.remove(element_id)
            
        except Exception as e:
            logger.error(f"Error rendering paragraph with links: {e}")
            # Fallback to standard text rendering if there was an error
            self._render_regular_text_content(layout_box)
            # Make sure to remove from in-progress tracking
            if element_id in self.in_progress_paragraphs:
                self.in_progress_paragraphs.remove(element_id)
    
    def _render_regular_text_content(self, layout_box):
        """
        Standard text rendering for layout boxes that don't need special handling.
        This is a fallback method.
        
        Args:
            layout_box: The layout box to render text for
        """
        try:
            element = layout_box.element
            
            # Get text content
            text = None
            if hasattr(element, 'text_content'):
                text = element.text_content
            elif hasattr(element, 'textContent'):
                text = element.textContent
            elif hasattr(element, 'text'):
                text = element.text
                
            if not text:
                # Try to get text from child nodes
                text = self._extract_text_content(element)
                
            if not text or not text.strip():
                return
                
            # Get positioning from box metrics
            x = layout_box.box_metrics.x + layout_box.box_metrics.padding_left + layout_box.box_metrics.border_left_width
            y = layout_box.box_metrics.y + layout_box.box_metrics.padding_top + layout_box.box_metrics.border_top_width
            
            # Get font settings and other styling similar to _render_text_content
            font_family = "Arial"
            font_size = 12
            
            # Create text with proper wrapping
            element_type = 'block' if layout_box.display == 'block' else 'inline'
            available_width = self._calculate_dimension(
                layout_box.box_metrics.content_width,
                self.viewport_width,
                element_type,
                'width',
                layout_box
            )
            
            text_item = self.canvas.create_text(
                x, y,
                text=text.strip(),
                font=(font_family, font_size),
                fill="#000000",
                anchor="nw",
                width=available_width if available_width > 0 else None
            )
            
            self.canvas_items.append(text_item)
            
        except Exception as e:
            logger.error(f"Error in fallback text rendering: {e}")
    
    def _render_image_placeholder(self, layout_box, x, y, width, height, element):
        """Render a placeholder while the image is loading."""
        try:
            # Create placeholder rectangle
            placeholder = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                outline='#CCCCCC',
                fill='#EEEEEE',
                tags=(f'element:{element.id}' if hasattr(element, 'id') and element.id else '',
                      f'loading_{element.get_attribute("src")}')
            )
            self.canvas_items.append(placeholder)
            
            # Add loading indicator
            label = self.canvas.create_text(
                x + width/2, y + height/2,
                text="🖼️",
                font=(self.fonts['default'][0], 14),
                fill='#999999',
                tags=(f'element:{element.id}' if hasattr(element, 'id') and element.id else '',
                      f'loading_{element.get_attribute("src")}')
            )
            self.canvas_items.append(label)
            
            # If alt text is available, display it below the icon
            if hasattr(element, 'get_attribute'):
                alt_text = element.get_attribute('alt')
                if alt_text:
                    alt_label = self.canvas.create_text(
                        x + width/2, y + height/2 + 20,
                        text=alt_text,
                        font=(self.fonts['default'][0], 10),
                        fill='#666666',
                        tags=(f'element:{element.id}' if hasattr(element, 'id') and element.id else '',
                              f'loading_{element.get_attribute("src")}')
                    )
                    self.canvas_items.append(alt_label)
                    
            logger.debug(f"Rendered image placeholder at ({x}, {y}) with dimensions {width}x{height}")
        except Exception as e:
            logger.error(f"Error rendering image placeholder: {e}")

    def _render_form_element(self, layout_box: LayoutBox, x: int, y: int, width: int, height: int) -> None:
        """
        Render a form element (input, button, textarea, select).
        
        Args:
            layout_box: The layout box for the form element
            x: X coordinate
            y: Y coordinate
            width: Width of the element
            height: Height of the element
        """
        try:
            element = layout_box.element
            if not element or not hasattr(element, 'tag_name'):
                return
                
            tag_name = element.tag_name.lower()
            
            # Get attributes
            element_type = element.get_attribute('type') if hasattr(element, 'get_attribute') else None
            element_value = element.get_attribute('value') if hasattr(element, 'get_attribute') else None
            
            # Default values
            if not element_type and tag_name == 'input':
                element_type = 'text'  # Default input type is text
            if not element_value:
                element_value = ''
                
            if tag_name == 'input':
                if element_type in ['text', 'password', 'email', 'number', 'tel', 'url', None]:
                    # Create a text input
                    input_rect = self.canvas.create_rectangle(
                        x, y, x + width, y + height,
                        outline="#cccccc",
                        fill="#ffffff"
                    )
                    self.canvas_items.append(input_rect)
                    
                    # Add text content
                    text_item = self.canvas.create_text(
                        x + 5, y + height/2,
                        text=element_value,
                        font=("Arial", 12),
                        fill="#333333",
                        anchor="w"
                    )
                    self.canvas_items.append(text_item)
                    
                elif element_type == 'checkbox':
                    # Create checkbox
                    checkbox_size = min(16, height)
                    checkbox = self.canvas.create_rectangle(
                        x, y + (height - checkbox_size)/2,
                        x + checkbox_size, y + (height + checkbox_size)/2,
                        outline="#333333",
                        fill="#ffffff"
                    )
                    self.canvas_items.append(checkbox)
                    
                    # Add label if there's text
                    if element_value:
                        label = self.canvas.create_text(
                            x + checkbox_size + 5, y + height/2,
                            text=element_value,
                            font=("Arial", 12),
                            fill="#333333",
                            anchor="w"
                        )
                        self.canvas_items.append(label)
            
            elif tag_name == 'button':
                self._render_button_element(x, y, width, height, element_value or "Button", element)
                
        except Exception as e:
            logger.error(f"Error rendering form element: {e}")
            # Render fallback
            fallback = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                outline="#cccccc",
                fill="#f0f0f0"
            )
            self.canvas_items.append(fallback)

    def _layout_box(self, layout_box: LayoutBox, x: int, y: int, container_width: int) -> None:
        """
        Apply layout to a single box and its children.
        
        Args:
            layout_box: Layout box to apply layout to
            x: X position
            y: Y position
            container_width: Width of containing box
        """
        try:
            # Set position
            layout_box.box_metrics.x = x
            layout_box.box_metrics.y = y
            
            # Calculate width
            if isinstance(layout_box.box_metrics.content_width, str):
                if layout_box.box_metrics.content_width == 'auto':
                    # Default to fill container
                    layout_box.box_metrics.content_width = container_width - layout_box.box_metrics.margin_left - layout_box.box_metrics.margin_right
                else:
                    # Try to convert numeric string to int
                    try:
                        layout_box.box_metrics.content_width = int(layout_box.box_metrics.content_width)
                    except ValueError:
                        # If conversion fails, default to container width
                        layout_box.box_metrics.content_width = container_width - layout_box.box_metrics.margin_left - layout_box.box_metrics.margin_right
            
            # Update box dimensions
            layout_box._update_box_dimensions()
            
            # Layout children
            if layout_box.display == 'block':
                self._layout_block_children(layout_box, container_width)
            elif layout_box.display == 'inline':
                self._layout_inline_children(layout_box, container_width)
            else:
                # Default to block layout
                self._layout_block_children(layout_box, container_width)
            
            # Calculate height based on children
            if isinstance(layout_box.box_metrics.content_height, str):
                if layout_box.box_metrics.content_height == 'auto':
                    height = 0
                    for child in layout_box.children:
                        child_bottom = child.box_metrics.y + child.box_metrics.margin_box_height - layout_box.box_metrics.y
                        height = max(height, child_bottom)
                    layout_box.box_metrics.content_height = height
                else:
                    # Try to convert numeric string to int
                    try:
                        layout_box.box_metrics.content_height = int(layout_box.box_metrics.content_height)
                    except ValueError:
                        # If conversion fails, calculate based on children
                        height = 0
                        for child in layout_box.children:
                            child_bottom = child.box_metrics.y + child.box_metrics.margin_box_height - layout_box.box_metrics.y
                            height = max(height, child_bottom)
                        layout_box.box_metrics.content_height = height
            
            layout_box._update_box_dimensions()
            
        except Exception as e:
            logger.error(f"Error during layout: {e}")
            # Set safe default values
            layout_box.box_metrics.content_width = container_width
            layout_box.box_metrics.content_height = 0
            layout_box._update_box_dimensions()