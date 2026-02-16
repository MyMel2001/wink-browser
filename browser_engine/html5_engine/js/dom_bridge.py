"""
DOM-JavaScript Bridge for the HTML5 Engine.

This module creates a bidirectional bridge between Python DOM objects
and JavaScript, allowing JS code to manipulate the actual DOM.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


class DOMBridge:
    """
    Bridges Python DOM objects to JavaScript.

    This class creates JavaScript representations of Python DOM elements
    and synchronizes changes between them.
    """

    def __init__(self, js_interpreter, document=None):
        """
        Initialize the DOM bridge.

        Args:
            js_interpreter: The dukpy JS interpreter instance
            document: The Python Document object
        """
        self.js = js_interpreter
        self.document = document
        self._element_map: Dict[int, Any] = {}  # Python id -> Python element
        self._js_element_map: Dict[int, str] = {}  # Python id -> JS element ID
        self._element_counter = 0

    def setup_document(self, document) -> None:
        """
        Set up the JavaScript document object with the Python DOM.

        Args:
            document: The Python Document object
        """
        self.document = document

        # Initialize the element registry in JS
        self.js.evaljs("""
        if (typeof __dom_elements === 'undefined') {
            __dom_elements = {};
            __dom_element_counter = 0;
        }
        """)

        # Create the document object in JS
        doc_js = f"""
        var document = {{
            title: '{self._escape_js(document.title if hasattr(document, 'title') and document.title else '')}',
            URL: '{self._escape_js(document.url if hasattr(document, 'url') and document.url else '')}',
            readyState: 'loading',
            contentType: 'text/html',
            characterSet: 'UTF-8',
            doctype: null,
            documentElement: null,
            head: null,
            body: null,
            _elements: {{}},
            _element_counter: 0
        }};
        """
        self.js.evaljs(doc_js)

        # Set up document methods
        self._setup_document_methods()

        # Build the DOM tree
        if document and hasattr(document, 'document_element') and document.document_element:
            self._build_dom_tree(document.document_element, 'document.documentElement')

        # Set readyState
        self.js.evaljs('document.readyState = "complete";')

    def _escape_js(self, s: str) -> str:
        """Escape a string for use in JavaScript."""
        if not s:
            return ''
        return s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

    def _setup_document_methods(self) -> None:
        """Set up document methods in JavaScript."""
        methods_js = """
        document.getElementById = function(id) {
            return __dom_getElementById(id);
        };

        document.getElementsByTagName = function(tagName) {
            return __dom_getElementsByTagName(tagName);
        };

        document.getElementsByClassName = function(className) {
            return __dom_getElementsByClassName(className);
        };

        document.querySelector = function(selector) {
            return __dom_querySelector(selector);
        };

        document.querySelectorAll = function(selector) {
            return __dom_querySelectorAll(selector);
        };

        document.createElement = function(tagName) {
            return __dom_createElement(tagName);
        };

        document.createTextNode = function(text) {
            return __dom_createTextNode(text);
        };

        document.createDocumentFragment = function() {
            return __dom_createDocumentFragment();
        };

        document.appendChild = function(node) {
            return __dom_appendChild(document, node);
        };

        document.insertBefore = function(node, refNode) {
            return __dom_insertBefore(document, node, refNode);
        };

        document.removeChild = function(node) {
            return __dom_removeChild(document, node);
        };

        document.addEventListener = function(type, listener, useCapture) {
            __dom_addDocumentEventListener(type, listener, useCapture);
        };

        document.removeEventListener = function(type, listener, useCapture) {
            __dom_removeDocumentEventListener(type, listener, useCapture);
        };

        document.dispatchEvent = function(event) {
            return __dom_dispatchDocumentEvent(event);
        };
        """
        self.js.evaljs(methods_js)

    def _build_dom_tree(self, element, js_path: str) -> str:
        """
        Recursively build the DOM tree in JavaScript.

        Args:
            element: Python DOM element
            js_path: JavaScript path to assign the element

        Returns:
            The JS element ID
        """
        if not element:
            return 'null'

        # Create a unique ID for this element
        py_id = id(element)
        self._element_counter += 1
        js_id = f'_el_{self._element_counter}'
        self._element_map[py_id] = element
        self._js_element_map[py_id] = js_id

        # Get element properties
        tag_name = element.tag_name if hasattr(element, 'tag_name') else ''
        node_type = element.node_type if hasattr(element, 'node_type') else 1
        node_value = element.node_value if hasattr(element, 'node_value') else ''

        # Get attributes
        attrs_js = '{}'
        if hasattr(element, 'attributes') and element.attributes:
            attrs = {}
            for name, attr in element.attributes.items():
                attrs[name] = attr.value if hasattr(attr, 'value') else str(attr)
            attrs_js = json.dumps(attrs)

        # Get style
        style_js = '{}'
        if hasattr(element, 'style') and element.style:
            style_js = json.dumps(dict(element.style))

        # Create the element in JS
        element_js = f"""
        var {js_id} = {{
            __py_id: {py_id},
            __js_id: '{js_id}',
            nodeType: {node_type},
            nodeName: '{self._escape_js(tag_name)}',
            tagName: '{self._escape_js(tag_name)}',
            nodeValue: '{self._escape_js(str(node_value) if node_value else '')}',
            textContent: '',
            innerHTML: '',
            outerHTML: '',
            className: '',
            id: '',
            style: {style_js},
            attributes: {attrs_js},
            children: [],
            childNodes: [],
            firstChild: null,
            lastChild: null,
            nextSibling: null,
            previousSibling: null,
            parentNode: null,
            _eventListeners: {{}}
        }};
        __dom_elements['{js_id}'] = {js_id};
        """

        self.js.evaljs(element_js)

        # Set text content
        if hasattr(element, 'text_content'):
            text = element.text_content or ''
            self.js.evaljs(f"{js_id}.textContent = '{self._escape_js(text)}';")

        # Set ID and className from attributes
        if hasattr(element, 'get_attribute'):
            elem_id = element.get_attribute('id')
            if elem_id:
                self.js.evaljs(f"{js_id}.id = '{self._escape_js(elem_id)}';")
            elem_class = element.get_attribute('class')
            if elem_class:
                self.js.evaljs(f"{js_id}.className = '{self._escape_js(elem_class)}';")

        # Set up element methods
        self._setup_element_methods(js_id)

        # Build children
        if hasattr(element, 'children') and element.children:
            child_js_ids = []
            prev_js_id = None

            for i, child in enumerate(element.children):
                child_js_id = self._build_dom_tree(child, f'{js_id}_child_{i}')

                if child_js_id != 'null':
                    child_js_ids.append(child_js_id)

                    # Set sibling relationships
                    if prev_js_id:
                        self.js.evaljs(f"{prev_js_id}.nextSibling = {child_js_id};")
                        self.js.evaljs(f"{child_js_id}.previousSibling = {prev_js_id};")

                    prev_js_id = child_js_id

            # Set children array
            if child_js_ids:
                children_array = '[' + ', '.join(child_js_ids) + ']'
                self.js.evaljs(f"{js_id}.children = {children_array};")
                self.js.evaljs(f"{js_id}.childNodes = {children_array};")

                # Set first/last child
                self.js.evaljs(f"{js_id}.firstChild = {child_js_ids[0]};")
                self.js.evaljs(f"{js_id}.lastChild = {child_js_ids[-1]};")

                # Set parent reference
                for child_id in child_js_ids:
                    self.js.evaljs(f"{child_id}.parentNode = {js_id};")

        # Assign to path
        self.js.evaljs(f"{js_path} = {js_id};")

        # Handle special elements
        if tag_name.lower() == 'html':
            self.js.evaljs('document.documentElement = ' + js_id + ';')
        elif tag_name.lower() == 'head':
            self.js.evaljs('document.head = ' + js_id + ';')
        elif tag_name.lower() == 'body':
            self.js.evaljs('document.body = ' + js_id + ';')

        return js_id

    def _setup_element_methods(self, js_id: str) -> None:
        """Set up DOM element methods in JavaScript."""
        methods_js = f"""
        {js_id}.getAttribute = function(name) {{
            return __dom_getAttribute(this.__py_id, name);
        }};

        {js_id}.setAttribute = function(name, value) {{
            __dom_setAttribute(this.__py_id, name, value);
            this.attributes[name] = value;
            if (name === 'id') this.id = value;
            if (name === 'class') this.className = value;
        }};

        {js_id}.removeAttribute = function(name) {{
            __dom_removeAttribute(this.__py_id, name);
            delete this.attributes[name];
        }};

        {js_id}.hasAttribute = function(name) {{
            return __dom_hasAttribute(this.__py_id, name);
        }};

        {js_id}.appendChild = function(child) {{
            return __dom_appendChild(this.__py_id, child.__py_id);
        }};

        {js_id}.insertBefore = function(child, refChild) {{
            return __dom_insertBefore(this.__py_id, child.__py_id, refChild ? refChild.__py_id : null);
        }};

        {js_id}.removeChild = function(child) {{
            return __dom_removeChild(this.__py_id, child.__py_id);
        }};

        {js_id}.replaceChild = function(newChild, oldChild) {{
            return __dom_replaceChild(this.__py_id, newChild.__py_id, oldChild.__py_id);
        }};

        {js_id}.cloneNode = function(deep) {{
            return __dom_cloneNode(this.__py_id, deep);
        }};

        {js_id}.addEventListener = function(type, listener, useCapture) {{
            __dom_addEventListener(this.__py_id, type, listener, useCapture);
        }};

        {js_id}.removeEventListener = function(type, listener, useCapture) {{
            __dom_removeEventListener(this.__py_id, type, listener, useCapture);
        }};

        {js_id}.dispatchEvent = function(event) {{
            return __dom_dispatchEvent(this.__py_id, event);
        }};

        {js_id}.querySelector = function(selector) {{
            return __dom_element_querySelector(this.__py_id, selector);
        }};

        {js_id}.querySelectorAll = function(selector) {{
            return __dom_element_querySelectorAll(this.__py_id, selector);
        }};

        {js_id}.getElementsByClassName = function(className) {{
            return __dom_element_getElementsByClassName(this.__py_id, className);
        }};

        {js_id}.getElementsByTagName = function(tagName) {{
            return __dom_element_getElementsByTagName(this.__py_id, tagName);
        }};

        {js_id}.getBoundingClientRect = function() {{
            return __dom_getBoundingClientRect(this.__py_id);
        }};

        {js_id}.scrollIntoView = function(options) {{
            __dom_scrollIntoView(this.__py_id, options);
        }};

        {js_id}.focus = function() {{
            __dom_focus(this.__py_id);
        }};

        {js_id}.blur = function() {{
            __dom_blur(this.__py_id);
        }};

        {js_id}.click = function() {{
            __dom_click(this.__py_id);
        }};
        """
        self.js.evaljs(methods_js)

    def register_python_callbacks(self) -> None:
        """Register Python callback functions for JS to call."""
        # Register callbacks for DOM operations
        self.js.export_function('__dom_getElementById', self._js_get_element_by_id)
        self.js.export_function('__dom_getElementsByTagName', self._js_get_elements_by_tag_name)
        self.js.export_function('__dom_getElementsByClassName', self._js_get_elements_by_class_name)
        self.js.export_function('__dom_querySelector', self._js_query_selector)
        self.js.export_function('__dom_querySelectorAll', self._js_query_selector_all)
        self.js.export_function('__dom_createElement', self._js_create_element)
        self.js.export_function('__dom_createTextNode', self._js_create_text_node)
        self.js.export_function('__dom_createDocumentFragment', self._js_create_document_fragment)
        self.js.export_function('__dom_appendChild', self._js_append_child)
        self.js.export_function('__dom_insertBefore', self._js_insert_before)
        self.js.export_function('__dom_removeChild', self._js_remove_child)
        self.js.export_function('__dom_getAttribute', self._js_get_attribute)
        self.js.export_function('__dom_setAttribute', self._js_set_attribute)
        self.js.export_function('__dom_removeAttribute', self._js_remove_attribute)
        self.js.export_function('__dom_hasAttribute', self._js_has_attribute)
        self.js.export_function('__dom_addEventListener', self._js_add_event_listener)
        self.js.export_function('__dom_removeEventListener', self._js_remove_event_listener)
        self.js.export_function('__dom_dispatchEvent', self._js_dispatch_event)
        self.js.export_function('__dom_getBoundingClientRect', self._js_get_bounding_client_rect)
        self.js.export_function('__dom_scrollIntoView', self._js_scroll_into_view)
        self.js.export_function('__dom_focus', self._js_focus)
        self.js.export_function('__dom_blur', self._js_blur)
        self.js.export_function('__dom_click', self._js_click)

    # Python callback implementations
    def _js_get_element_by_id(self, element_id: str) -> Optional[Dict]:
        """Get element by ID."""
        if not self.document:
            return None
        element = self.document.get_element_by_id(element_id) if hasattr(self.document, 'get_element_by_id') else None
        if element:
            return self._element_to_js(element)
        return None

    def _js_get_elements_by_tag_name(self, tag_name: str) -> List[Dict]:
        """Get elements by tag name."""
        if not self.document:
            return []
        elements = self.document.get_elements_by_tag_name(tag_name) if hasattr(self.document, 'get_elements_by_tag_name') else []
        return [self._element_to_js(el) for el in elements]

    def _js_get_elements_by_class_name(self, class_name: str) -> List[Dict]:
        """Get elements by class name."""
        if not self.document:
            return []
        elements = self.document.get_elements_by_class_name(class_name) if hasattr(self.document, 'get_elements_by_class_name') else []
        return [self._element_to_js(el) for el in elements]

    def _js_query_selector(self, selector: str) -> Optional[Dict]:
        """Query selector."""
        if not self.document:
            return None
        element = self.document.query_selector(selector) if hasattr(self.document, 'query_selector') else None
        if element:
            return self._element_to_js(element)
        return None

    def _js_query_selector_all(self, selector: str) -> List[Dict]:
        """Query selector all."""
        if not self.document:
            return []
        elements = self.document.query_selector_all(selector) if hasattr(self.document, 'query_selector_all') else []
        return [self._element_to_js(el) for el in elements]

    def _js_create_element(self, tag_name: str) -> Dict:
        """Create a new element."""
        if not self.document:
            return {}
        element = self.document.create_element(tag_name) if hasattr(self.document, 'create_element') else None
        if element:
            return self._element_to_js(element)
        return {}

    def _js_create_text_node(self, text: str) -> Dict:
        """Create a text node."""
        if not self.document:
            return {}
        node = self.document.create_text_node(text) if hasattr(self.document, 'create_text_node') else None
        if node:
            return self._element_to_js(node)
        return {}

    def _js_create_document_fragment(self) -> Dict:
        """Create a document fragment."""
        if not self.document:
            return {}
        fragment = self.document.create_document_fragment() if hasattr(self.document, 'create_document_fragment') else None
        if fragment:
            return self._element_to_js(fragment)
        return {}

    def _js_append_child(self, parent_id: int, child_id: int) -> Optional[Dict]:
        """Append a child to a parent element."""
        parent = self._element_map.get(parent_id)
        child = self._element_map.get(child_id)
        if parent and child and hasattr(parent, 'append_child'):
            parent.append_child(child)
            # Rebuild the JS DOM for this subtree
            self._update_element_children(parent_id)
            return self._element_to_js(child)
        return None

    def _js_insert_before(self, parent_id: int, child_id: int, ref_id: int) -> Optional[Dict]:
        """Insert a child before a reference element."""
        parent = self._element_map.get(parent_id)
        child = self._element_map.get(child_id)
        ref = self._element_map.get(ref_id) if ref_id else None
        if parent and child and hasattr(parent, 'insert_before'):
            parent.insert_before(child, ref)
            self._update_element_children(parent_id)
            return self._element_to_js(child)
        return None

    def _js_remove_child(self, parent_id: int, child_id: int) -> Optional[Dict]:
        """Remove a child from a parent element."""
        parent = self._element_map.get(parent_id)
        child = self._element_map.get(child_id)
        if parent and child and hasattr(parent, 'remove_child'):
            result = parent.remove_child(child)
            self._update_element_children(parent_id)
            return self._element_to_js(result) if result else None
        return None

    def _js_get_attribute(self, element_id: int, name: str) -> Optional[str]:
        """Get an attribute value."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'get_attribute'):
            return element.get_attribute(name)
        return None

    def _js_set_attribute(self, element_id: int, name: str, value: str) -> None:
        """Set an attribute value."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'set_attribute'):
            element.set_attribute(name, value)

    def _js_remove_attribute(self, element_id: int, name: str) -> None:
        """Remove an attribute."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'remove_attribute'):
            element.remove_attribute(name)

    def _js_has_attribute(self, element_id: int, name: str) -> bool:
        """Check if an attribute exists."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'has_attribute'):
            return element.has_attribute(name)
        return False

    def _js_add_event_listener(self, element_id: int, event_type: str, listener: str, use_capture: bool) -> None:
        """Add an event listener."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'add_event_listener'):
            # Store the JS listener reference
            if not hasattr(element, '_js_listeners'):
                element._js_listeners = {}
            if event_type not in element._js_listeners:
                element._js_listeners[event_type] = []
            element._js_listeners[event_type].append(listener)

            # Add Python event listener that will call the JS listener
            def js_handler(event):
                self._call_js_listener(listener, event)
            element.add_event_listener(event_type, js_handler)

    def _js_remove_event_listener(self, element_id: int, event_type: str, listener: str, use_capture: bool) -> None:
        """Remove an event listener."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'remove_event_listener'):
            if hasattr(element, '_js_listeners') and event_type in element._js_listeners:
                if listener in element._js_listeners[event_type]:
                    element._js_listeners[event_type].remove(listener)

    def _js_dispatch_event(self, element_id: int, event: Dict) -> bool:
        """Dispatch an event."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'dispatch_event'):
            # Create Python event from JS event
            from ..dom.node import Event
            py_event = Event(event.get('type', ''))
            return element.dispatch_event(py_event)
        return False

    def _js_get_bounding_client_rect(self, element_id: int) -> Dict:
        """Get bounding client rect."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'get_bounding_client_rect'):
            return element.get_bounding_client_rect()
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'top': 0, 'right': 0, 'bottom': 0, 'left': 0}

    def _js_scroll_into_view(self, element_id: int, options: Dict) -> None:
        """Scroll element into view."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'scroll_into_view'):
            element.scroll_into_view(options)

    def _js_focus(self, element_id: int) -> None:
        """Focus an element."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'focus'):
            element.focus()

    def _js_blur(self, element_id: int) -> None:
        """Blur an element."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'blur'):
            element.blur()

    def _js_click(self, element_id: int) -> None:
        """Click an element."""
        element = self._element_map.get(element_id)
        if element and hasattr(element, 'click'):
            element.click()

    def _call_js_listener(self, listener: str, event) -> None:
        """Call a JavaScript event listener from Python."""
        try:
            # Create a JS event object
            event_js = self._event_to_js(event)
            self.js.evaljs(f'({listener})({event_js});')
        except Exception as e:
            logger.error(f"Error calling JS listener: {e}")

    def _element_to_js(self, element) -> Dict:
        """Convert a Python element to a JS-friendly dict."""
        if not element:
            return {}

        py_id = id(element)
        if py_id not in self._element_map:
            self._element_map[py_id] = element
            self._element_counter += 1
            self._js_element_map[py_id] = f'_el_{self._element_counter}'

        return {
            '__py_id': py_id,
            '__js_id': self._js_element_map[py_id],
            'nodeType': element.node_type if hasattr(element, 'node_type') else 1,
            'nodeName': element.tag_name if hasattr(element, 'tag_name') else '',
            'tagName': element.tag_name if hasattr(element, 'tag_name') else '',
        }

    def _event_to_js(self, event) -> str:
        """Convert a Python event to a JS object string."""
        event_type = event.type if hasattr(event, 'type') else ''
        return f'{{type: "{self._escape_js(event_type)}"}}'

    def _update_element_children(self, element_id: int) -> None:
        """Update the children array in JS for an element."""
        element = self._element_map.get(element_id)
        if not element:
            return

        js_id = self._js_element_map.get(element_id)
        if not js_id:
            return

        # Rebuild children array
        if hasattr(element, 'children') and element.children:
            child_ids = []
            for child in element.children:
                child_py_id = id(child)
                if child_py_id not in self._element_map:
                    self._element_map[child_py_id] = child
                    self._element_counter += 1
                    self._js_element_map[child_py_id] = f'_el_{self._element_counter}'
                child_ids.append(self._js_element_map[child_py_id])

            children_array = '[' + ', '.join(child_ids) + ']'
            self.js.evaljs(f'{js_id}.children = {children_array};')
            self.js.evaljs(f'{js_id}.childNodes = {children_array};')