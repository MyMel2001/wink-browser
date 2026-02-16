import re
import math
from typing import Dict, List, Optional, Tuple, Union

from .box_metrics import BoxMetrics
from ..css.custom_properties import get_custom_properties
from ..css.custom_properties import CSSCustomProperties, resolve_css_value
from ..css.value_functions import get_value_functions, resolve_css_value as resolve_math_functions


class LayoutBox:
    """
    Represents a box in the layout tree.

    Contains information about an element's layout, including position, size, and margins.
    """

    # Default spacing constants
    DEFAULT_BLOCK_MARGIN = 20  # Increased spacing between block elements
    DEFAULT_HEADING_MARGIN = 24  # Larger spacing for headings
    DEFAULT_PARAGRAPH_MARGIN = 16  # Standard paragraph spacing
    DEFAULT_LIST_ITEM_MARGIN = 8  # Spacing between list items
    DEFAULT_INLINE_MARGIN = 12  # Significantly increased spacing between inline elements to prevent merging
    DEFAULT_DIV_MIN_HEIGHT = 20  # Minimum height for empty div elements
    DEFAULT_TEXT_ELEMENT_MARGIN = 5  # Margin for text formatting elements
    DEFAULT_FOOTER_MARGIN = 25  # Larger margin for footer elements
    DEFAULT_MARQUEE_MARGIN = 15  # Margin for marquee elements
    DEFAULT_COPYRIGHT_MARGIN = 20  # Margin for copyright elements

    # Global custom properties manager
    _custom_properties = CSSCustomProperties()

    def __init__(self, element=None, display: str = 'block', parent=None):
        """
        Initialize a layout box.

        Args:
            element: The DOM element
            display: Initial display property
            parent: Parent layout box
        """
        self.element = element
        self.parent = parent
        self.children: List['LayoutBox'] = []
        self.computed_style: Dict[str, str] = {}
        self.display = display
        self.box_metrics = BoxMetrics()
        self.z_index = 0  # Default z-index
        self._inherited_custom_properties: Dict[str, str] = {}  # Inherited CSS variables
        
        # Set default margins based on element type
        if element and hasattr(element, 'tag_name'):
            tag_name = element.tag_name.lower()
            
            # Initialize default margins as 0
            self.box_metrics.margin_top = 0
            self.box_metrics.margin_bottom = 0
            self.box_metrics.margin_left = 0
            self.box_metrics.margin_right = 0
            
            # Set margins based on element type
            if tag_name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                self.box_metrics.margin_top = self.DEFAULT_HEADING_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_HEADING_MARGIN
            elif tag_name == 'p':
                self.box_metrics.margin_top = self.DEFAULT_PARAGRAPH_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_PARAGRAPH_MARGIN
            elif tag_name == 'footer':
                # Footer gets larger top margin to separate it from content
                self.box_metrics.margin_top = self.DEFAULT_FOOTER_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_BLOCK_MARGIN
            elif tag_name == 'marquee':
                # Marquee element (obsolete but still supported by some browsers)
                self.box_metrics.margin_top = self.DEFAULT_MARQUEE_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_MARQUEE_MARGIN
            elif tag_name == 'copyright' or (hasattr(element, 'class_name') and 'copyright' in element.class_name):
                # Custom copyright element or elements with copyright class
                self.box_metrics.margin_top = self.DEFAULT_COPYRIGHT_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_COPYRIGHT_MARGIN
            elif tag_name in ('div', 'section', 'article', 'header', 'nav', 'aside'):
                self.box_metrics.margin_top = self.DEFAULT_BLOCK_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_BLOCK_MARGIN
            elif tag_name in ('li'):
                self.box_metrics.margin_top = self.DEFAULT_LIST_ITEM_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_LIST_ITEM_MARGIN
                self.box_metrics.margin_left = self.DEFAULT_LIST_ITEM_MARGIN * 2  # Indent list items
            # Set margins for inline text elements
            elif tag_name in ('a'):
                # Links get slightly larger margins
                self.box_metrics.margin_left = self.DEFAULT_INLINE_MARGIN
                self.box_metrics.margin_right = self.DEFAULT_INLINE_MARGIN
                self.box_metrics.margin_top = self.DEFAULT_TEXT_ELEMENT_MARGIN
                self.box_metrics.margin_bottom = self.DEFAULT_TEXT_ELEMENT_MARGIN
            elif tag_name in ('span', 'strong', 'em', 'b', 'i', 'u', 's', 'strike', 'del', 'ins',
                            'small', 'sub', 'sup', 'code', 'kbd', 'mark', 'q', 'cite', 'dfn',
                            'abbr', 'time', 'var', 'samp'):
                # Text formatting elements
                self.box_metrics.margin_left = self.DEFAULT_TEXT_ELEMENT_MARGIN
                self.box_metrics.margin_right = self.DEFAULT_TEXT_ELEMENT_MARGIN
        
        # Set default display based on element tag if present
        if element and hasattr(element, 'tag_name'):
            # Block elements
            if element.tag_name.lower() in ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                         'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                                         'form', 'fieldset', 'hr', 'pre', 'blockquote',
                                         'article', 'section', 'header', 'footer', 'nav', 'aside'):
                self.display = 'block'
            # Inline elements
            elif element.tag_name.lower() in ('span', 'a', 'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del',
                                           'small', 'sub', 'sup', 'code', 'kbd', 'samp', 'var', 'cite', 'q', 'dfn',
                                           'abbr', 'time', 'mark', 'ruby', 'rt', 'rp', 'bdi', 'bdo', 'br', 'wbr'):
                self.display = 'inline'
            # Inline-block elements
            elif element.tag_name.lower() in ('img', 'input', 'button', 'textarea', 'select', 'label'):
                self.display = 'inline-block'
            # Default to inheriting from parent or block
            else:
                if parent:
                    self.display = parent.display
                else:
                    self.display = 'block'
    
    def add_child(self, child: 'LayoutBox') -> None:
        """
        Add a child layout box.
        
        Args:
            child: The child layout box to add
        """
        self.children.append(child)
        child.parent = self
    
    def compute_styles(self, parent_styles: Dict[str, str] = None) -> None:
        """
        Compute styles for this layout box and its children.

        Args:
            parent_styles: Inherited styles from parent element
        """
        if parent_styles is None:
            parent_styles = {}

        # Get custom properties manager
        custom_props = get_custom_properties()

        # Inherit parent styles for relevant properties
        inherited_properties = [
            'color', 'font-family', 'font-size', 'font-weight', 'line-height',
            'text-align', 'text-indent', 'visibility'
        ]

        self.computed_style = {}

        # Inherit styles from parent
        for prop in inherited_properties:
            if prop in parent_styles:
                self.computed_style[prop] = parent_styles[prop]

        # Apply element's own styles if it has any
        if self.element and hasattr(self.element, 'style'):
            element_id = id(self.element) if self.element else 0

            # First, extract and store any custom properties (--name: value)
            for prop, value in list(self.element.style.items()):
                if custom_props.is_custom_property(prop):
                    custom_props.set_property(element_id, prop, value)
                    # Store inherited custom properties
                    self._custom_properties[prop] = value

            # Then apply regular styles, resolving var() references
            inherited_custom = parent_styles.get('_custom_properties', {})
            for prop, value in self.element.style.items():
                if not custom_props.is_custom_property(prop):
                    # Resolve any var() references in the value
                    resolved_value = custom_props.resolve_var(
                        value, element_id, {**inherited_custom, **self._custom_properties}
                    )
                    self.computed_style[prop] = resolved_value

        # Store custom properties for children to inherit
        self.computed_style['_custom_properties'] = self._custom_properties

        # Update display property from computed styles
        if 'display' in self.computed_style:
            self.display = self.computed_style['display']

        # Process z-index
        if 'z-index' in self.computed_style:
            try:
                self.z_index = int(self.computed_style['z-index'])
            except ValueError:
                # If z-index is not a valid integer, default to 0
                self.z_index = 0
        elif self.parent:
            # Inherit parent's z-index for stacking context
            self.z_index = self.parent.z_index

        # Compute box metrics based on styles
        self._compute_box_metrics()

        # Recursively compute styles for children
        for child in self.children:
            child.compute_styles(self.computed_style)
    
    def _compute_box_metrics(self) -> None:
        """
        Compute box metrics based on computed styles.
        """
        # Default values
        self.box_metrics.width = self._parse_dimension_value(self.computed_style.get('width', 'auto'))
        self.box_metrics.height = self._parse_dimension_value(self.computed_style.get('height', 'auto'))
        
        # Parse margin properties
        self.box_metrics.margin_top = self._parse_dimension_value(self.computed_style.get('margin-top', '0'))
        self.box_metrics.margin_right = self._parse_dimension_value(self.computed_style.get('margin-right', '0'))
        self.box_metrics.margin_bottom = self._parse_dimension_value(self.computed_style.get('margin-bottom', '0'))
        self.box_metrics.margin_left = self._parse_dimension_value(self.computed_style.get('margin-left', '0'))
        
        # Parse padding properties
        self.box_metrics.padding_top = self._parse_dimension_value(self.computed_style.get('padding-top', '0'))
        self.box_metrics.padding_right = self._parse_dimension_value(self.computed_style.get('padding-right', '0'))
        self.box_metrics.padding_bottom = self._parse_dimension_value(self.computed_style.get('padding-bottom', '0'))
        self.box_metrics.padding_left = self._parse_dimension_value(self.computed_style.get('padding-left', '0'))
        
        # Parse border properties
        self.box_metrics.border_top_width = self._parse_dimension_value(self.computed_style.get('border-top-width', '0'))
        self.box_metrics.border_right_width = self._parse_dimension_value(self.computed_style.get('border-right-width', '0'))
        self.box_metrics.border_bottom_width = self._parse_dimension_value(self.computed_style.get('border-bottom-width', '0'))
        self.box_metrics.border_left_width = self._parse_dimension_value(self.computed_style.get('border-left-width', '0'))
        
        # If there's a border shorthand, parse it
        if 'border-width' in self.computed_style:
            width = self._parse_dimension_value(self.computed_style.get('border-width', '0'))
            self.box_metrics.border_top_width = width
            self.box_metrics.border_right_width = width
            self.box_metrics.border_bottom_width = width
            self.box_metrics.border_left_width = width
        
        # If there's a border shorthand, it takes precedence
        if 'border' in self.computed_style:
            # Extract border width from the shorthand (simplified approach)
            border_value = self.computed_style['border']
            match = re.search(r'(\d+)(px|em|rem|%)?', border_value)
            if match:
                border_width = int(match.group(1))
                self.box_metrics.border_top_width = border_width
                self.box_metrics.border_right_width = border_width
                self.box_metrics.border_bottom_width = border_width
                self.box_metrics.border_left_width = border_width
        
        # Compute content dimensions
        if self.box_metrics.width != 'auto':
            self.box_metrics.content_width = self.box_metrics.width
        else:
            # For now, default to auto width handling during layout
            self.box_metrics.content_width = 'auto'
        
        if self.box_metrics.height != 'auto':
            self.box_metrics.content_height = self.box_metrics.height
        else:
            # For now, default to auto height handling during layout
            self.box_metrics.content_height = 'auto'
        
        # Update box dimensions
        self._update_box_dimensions()
    
    def _update_box_dimensions(self) -> None:
        """
        Update box dimensions based on content, padding, border, and margin.
        """
        # Get all values before arithmetic operations
        content_width = self.box_metrics.content_width
        content_height = self.box_metrics.content_height
        padding_left = self.box_metrics.padding_left
        padding_right = self.box_metrics.padding_right
        padding_top = self.box_metrics.padding_top
        padding_bottom = self.box_metrics.padding_bottom
        border_left = self.box_metrics.border_left_width
        border_right = self.box_metrics.border_right_width
        border_top = self.box_metrics.border_top_width
        border_bottom = self.box_metrics.border_bottom_width
        margin_left = self.box_metrics.margin_left
        margin_right = self.box_metrics.margin_right
        margin_top = self.box_metrics.margin_top
        margin_bottom = self.box_metrics.margin_bottom
        
        # Convert all string values to float, handling 'auto' as 0
        if isinstance(content_width, str):
            content_width = 0 if content_width == 'auto' else float(content_width)
        if isinstance(content_height, str):
            content_height = 0 if content_height == 'auto' else float(content_height)
        if isinstance(padding_left, str):
            padding_left = 0 if padding_left == 'auto' else float(padding_left)
        if isinstance(padding_right, str):
            padding_right = 0 if padding_right == 'auto' else float(padding_right)
        if isinstance(padding_top, str):
            padding_top = 0 if padding_top == 'auto' else float(padding_top)
        if isinstance(padding_bottom, str):
            padding_bottom = 0 if padding_bottom == 'auto' else float(padding_bottom)
        if isinstance(border_left, str):
            border_left = 0 if border_left == 'auto' else float(border_left)
        if isinstance(border_right, str):
            border_right = 0 if border_right == 'auto' else float(border_right)
        if isinstance(border_top, str):
            border_top = 0 if border_top == 'auto' else float(border_top)
        if isinstance(border_bottom, str):
            border_bottom = 0 if border_bottom == 'auto' else float(border_bottom)
        if isinstance(margin_left, str):
            margin_left = 0 if margin_left == 'auto' else float(margin_left)
        if isinstance(margin_right, str):
            margin_right = 0 if margin_right == 'auto' else float(margin_right)
        if isinstance(margin_top, str):
            margin_top = 0 if margin_top == 'auto' else float(margin_top)
        if isinstance(margin_bottom, str):
            margin_bottom = 0 if margin_bottom == 'auto' else float(margin_bottom)
        
        # Padding box dimensions
        self.box_metrics.padding_box_width = int(
            content_width + padding_left + padding_right
        )
        self.box_metrics.padding_box_height = int(
            content_height + padding_top + padding_bottom
        )
        
        # Border box dimensions
        self.box_metrics.border_box_width = int(
            self.box_metrics.padding_box_width + border_left + border_right
        )
        self.box_metrics.border_box_height = int(
            self.box_metrics.padding_box_height + border_top + border_bottom
        )
        
        # Margin box dimensions
        self.box_metrics.margin_box_width = int(
            self.box_metrics.border_box_width + margin_left + margin_right
        )
        self.box_metrics.margin_box_height = int(
            self.box_metrics.border_box_height + margin_top + margin_bottom
        )
    
    def _parse_dimension_value(self, value: str) -> Union[int, str]:
        """
        Parse a CSS dimension value.
        
        Args:
            value: CSS dimension value (e.g., "10px", "50%", "auto")
            
        Returns:
            Integer pixel value or 'auto'
        """
        if not value or value == 'auto':
            return 'auto'
        
        # Handle percentage values - calculate based on parent container
        if value.endswith('%'):
            try:
                percentage = float(value[:-1]) / 100.0
                if self.parent:
                    # Use parent's content width for horizontal percentages
                    parent_width = self.parent.box_metrics.content_width
                    if isinstance(parent_width, str):
                        parent_width = 0 if parent_width == 'auto' else float(parent_width)
                    return int(parent_width * percentage)
                else:
                    # If no parent, use viewport width
                    return int(self.viewport_width * percentage)
            except ValueError:
                return 0
        
        # Handle pixel values
        if value.endswith('px'):
            try:
                return int(float(value[:-2]))
            except ValueError:
                return 0
        
        # Handle em values - calculate based on parent's font size
        if value.endswith('em'):
            try:
                em_value = float(value[:-2])
                if self.parent:
                    # Get parent's font size
                    parent_font_size = self._parse_dimension_value(self.parent.computed_style.get('font-size', '16px'))
                    if isinstance(parent_font_size, str):
                        parent_font_size = 16 if parent_font_size == 'auto' else float(parent_font_size)
                    return int(em_value * parent_font_size)
                else:
                    # Default to 16px if no parent
                    return int(em_value * 16)
            except ValueError:
                return 0
        
        # Handle rem values - calculate based on root font size
        if value.endswith('rem'):
            try:
                rem_value = float(value[:-3])
                # Always use root font size (16px) for rem
                return int(rem_value * 16)
            except ValueError:
                return 0
        
        # Handle viewport units
        if value.endswith('vw'):
            try:
                vw_value = float(value[:-2]) / 100.0
                return int(self.viewport_width * vw_value)
            except ValueError:
                return 0
        if value.endswith('vh'):
            try:
                vh_value = float(value[:-2]) / 100.0
                return int(self.viewport_height * vh_value)
            except ValueError:
                return 0
        
        # Handle CSS math functions: calc(), min(), max(), clamp()
        if any(value.startswith(fn) for fn in ('calc(', 'min(', 'max(', 'clamp(')):
            try:
                from ..css.value_functions import get_value_functions
                vf = get_value_functions()
                # Set current context
                vf.set_viewport(self.viewport_width, self.viewport_height)
                if self.parent:
                    parent_font_size = self._parse_dimension_value(
                        self.parent.computed_style.get('font-size', '16px')
                    )
                    if isinstance(parent_font_size, str):
                        parent_font_size = 16
                    vf.set_parent_font_size(parent_font_size)
                # Resolve the function
                resolved = vf.resolve_functions(value)
                # Parse the resolved pixel value
                if resolved.endswith('px'):
                    return int(float(resolved[:-2]))
                else:
                    return int(float(resolved))
            except Exception as e:
                logger.debug(f"Error resolving CSS function {value}: {e}")
                return 0
        
        # Handle unitless values as pixels
        try:
            return int(float(value))
        except ValueError:
            return 0
    
    def layout(self, container_width: int, x: int = 0, y: int = 0) -> None:
        """
        Layout this box and its children.
        
        Args:
            container_width: Width of the containing block
            x: X position in parent
            y: Y position in parent
        """
        # Set position
        self.box_metrics.x = x
        self.box_metrics.y = y
        
        # Layout based on display type
        if self.display == 'block':
            # Block elements take full width of their container by default
            if self.box_metrics.width is None or self.box_metrics.width == 'auto':
                self.box_metrics.width = container_width
                
            # Calculate content width
            self._calculate_width(container_width)
            
            # Layout as block
            self._layout_block(container_width)
            
            # Calculate height
            self._calculate_height()
            
        elif self.display == 'inline-block':
            # Inline-block elements behave like inline elements externally
            # but like block elements internally
            self._calculate_width(container_width)
            self._layout_inline_block(container_width)
            self._calculate_height()
            
        elif self.display == 'inline':
            # Inline elements are sized to their content
            self._calculate_width(container_width)
            self._layout_inline(container_width)
            self._calculate_height()
            
        elif self.display == 'flex':
            # Flexbox layout
            self._calculate_width(container_width)
            self._layout_flex(container_width)
            self._calculate_height()
            
        else:
            # Default to block layout
            if self.box_metrics.width is None or self.box_metrics.width == 'auto':
                self.box_metrics.width = container_width
                
            self._calculate_width(container_width)
            self._layout_block(container_width)
            self._calculate_height()
    
    def _calculate_width(self, container_width: int) -> None:
        """
        Calculate the width of this box based on CSS properties and container width.
        
        Args:
            container_width: Width of the containing block
        """
        # Handle width based on display type
        if self.display == 'block' or self.display == 'flex':
            if isinstance(self.box_metrics.content_width, str) and self.box_metrics.content_width == 'auto':
                # For block elements, default to full width of container minus margins
                # Convert all values to float before arithmetic operations
                margin_left = self.box_metrics.margin_left
                margin_right = self.box_metrics.margin_right
                padding_left = self.box_metrics.padding_left
                padding_right = self.box_metrics.padding_right
                border_left = self.box_metrics.border_left_width
                border_right = self.box_metrics.border_right_width
                
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
                
                # Calculate totals after conversion
                total_margin = margin_left + margin_right
                total_padding = padding_left + padding_right
                total_border = border_left + border_right
                
                # Content width fills available space
                self.box_metrics.content_width = int(container_width - total_margin - total_padding - total_border)
        
        elif self.display == 'inline' or self.display == 'inline-block':
            if isinstance(self.box_metrics.content_width, str) and self.box_metrics.content_width == 'auto':
                # For inline elements, content determines width
                # For simplicity, use a default width based on content
                if self.element and hasattr(self.element, 'text_content') and self.element.text_content:
                    # Approximate width based on text length (very simple approach)
                    text_length = len(self.element.text_content)
                    font_size = self._parse_dimension_value(self.computed_style.get('font-size', '16px'))
                    if isinstance(font_size, str):
                        font_size = 16 if font_size == 'auto' else float(font_size)
                        
                    # Rough estimate: each character is about 0.6 times the font size width
                    self.box_metrics.content_width = int(text_length * font_size * 0.6)
                else:
                    # Default minimum width for empty inline elements
                    self.box_metrics.content_width = 10
        
        # Update box dimensions after calculating content width
        self._update_box_dimensions()
    
    def _calculate_height(self) -> None:
        """
        Calculate the height of this box based on CSS properties and content.
        """
        if isinstance(self.box_metrics.content_height, str) and self.box_metrics.content_height == 'auto':
            # Calculate height based on children
            if self.children:
                max_child_bottom = 0
                
                for child in self.children:
                    # Get all values before arithmetic operations
                    child_y = child.box_metrics.y
                    child_margin_top = child.box_metrics.margin_top
                    child_margin_bottom = child.box_metrics.margin_bottom
                    child_border_top = child.box_metrics.border_top_width
                    child_border_bottom = child.box_metrics.border_bottom_width
                    child_padding_top = child.box_metrics.padding_top
                    child_padding_bottom = child.box_metrics.padding_bottom
                    child_content_height = child.box_metrics.content_height
                    
                    # Convert all string values to float, handling 'auto' as 0
                    if isinstance(child_y, str):
                        child_y = 0 if child_y == 'auto' else float(child_y)
                    if isinstance(child_margin_top, str):
                        child_margin_top = 0 if child_margin_top == 'auto' else float(child_margin_top)
                    if isinstance(child_margin_bottom, str):
                        child_margin_bottom = 0 if child_margin_bottom == 'auto' else float(child_margin_bottom)
                    if isinstance(child_border_top, str):
                        child_border_top = 0 if child_border_top == 'auto' else float(child_border_top)
                    if isinstance(child_border_bottom, str):
                        child_border_bottom = 0 if child_border_bottom == 'auto' else float(child_border_bottom)
                    if isinstance(child_padding_top, str):
                        child_padding_top = 0 if child_padding_top == 'auto' else float(child_padding_top)
                    if isinstance(child_padding_bottom, str):
                        child_padding_bottom = 0 if child_padding_bottom == 'auto' else float(child_padding_bottom)
                    if isinstance(child_content_height, str):
                        child_content_height = 0 if child_content_height == 'auto' else float(child_content_height)
                    
                    # Calculate child's total height
                    child_height = (child_content_height + 
                                  child_padding_top + child_padding_bottom +
                                  child_border_top + child_border_bottom +
                                  child_margin_top + child_margin_bottom)
                    
                    child_bottom = child_y + child_height
                    max_child_bottom = max(max_child_bottom, child_bottom)
                
                # Get all values for content top calculation
                content_y = self.box_metrics.y
                margin_top = self.box_metrics.margin_top
                border_top = self.box_metrics.border_top_width
                padding_top = self.box_metrics.padding_top
                
                # Convert all string values to float, handling 'auto' as 0
                if isinstance(content_y, str):
                    content_y = 0 if content_y == 'auto' else float(content_y)
                if isinstance(margin_top, str):
                    margin_top = 0 if margin_top == 'auto' else float(margin_top)
                if isinstance(border_top, str):
                    border_top = 0 if border_top == 'auto' else float(border_top)
                if isinstance(padding_top, str):
                    padding_top = 0 if padding_top == 'auto' else float(padding_top)
                
                # Calculate content top
                content_top = content_y + margin_top + border_top + padding_top
                self.box_metrics.content_height = int(max(0, max_child_bottom - content_top))
            else:
                # For elements with text content but no children
                if self.element and hasattr(self.element, 'text_content') and self.element.text_content:
                    # Approximate height based on text content and line height
                    font_size = self._parse_dimension_value(self.computed_style.get('font-size', '16px'))
                    if isinstance(font_size, str):
                        font_size = 16 if font_size == 'auto' else float(font_size)
                    
                    line_height_value = self.computed_style.get('line-height', '1.2')
                    
                    try:
                        line_height_multiplier = float(line_height_value)
                        line_height = int(font_size * line_height_multiplier)
                    except ValueError:
                        # If line-height has units, parse it as a dimension
                        line_height = self._parse_dimension_value(line_height_value)
                        if isinstance(line_height, str):
                            try:
                                float(line_height)
                            except:
                                line_height = int(font_size * 1.2)
                    
                    # Calculate how many lines the text might need
                    content_width = self.box_metrics.content_width
                    if isinstance(content_width, str):
                        try:
                            content_width = float(content_width)
                        except:
                            content_width = 0
                    
                    if content_width > 0:
                        # Rough estimate: each character is about 0.6 times the font size width
                        chars_per_line = int(content_width / (font_size * 0.6))
                        if chars_per_line < 1:
                            chars_per_line = 1
                        
                        text_length = len(self.element.text_content)
                        num_lines = max(1, math.ceil(text_length / chars_per_line))
                        
                        self.box_metrics.content_height = int(num_lines * line_height)
                    else:
                        # Default to one line if we can't calculate width
                        self.box_metrics.content_height = int(line_height)
                else:
                    # Empty element with no explicit height
                    # Ensure a minimum height based on tag type
                    tag_name = self.element.tag_name.lower() if hasattr(self.element, 'tag_name') else ''
                    
                    # Form elements should have a minimum height even if empty
                    if tag_name in ['input', 'button', 'select', 'textarea']:
                        self.box_metrics.content_height = 20  # Increased minimum height for form elements
                    elif tag_name == 'div':
                        # Ensure substantial height for div containers
                        self.box_metrics.content_height = self.DEFAULT_DIV_MIN_HEIGHT
                    elif tag_name in ['span', 'p', 'a', 'section', 'article', 'header', 'footer', 'nav', 'aside']:
                        # Ensure non-zero height for containers
                        self.box_metrics.content_height = 15  # Increased from 8
                    else:
                        # Default minimum height for any element
                        self.box_metrics.content_height = 10  # Increased from 4
        
        # Update box dimensions after calculating content height
        self._update_box_dimensions()
    
    def _layout_block(self, container_width: int) -> None:
        """
        Perform layout for block elements.
        
        Args:
            container_width: Width of the containing block
        """
        # Convert padding to numeric values first
        padding_left = self._parse_dimension_value(self.box_metrics.padding_left)
        padding_right = self._parse_dimension_value(self.box_metrics.padding_right)
        padding_top = self._parse_dimension_value(self.box_metrics.padding_top)
        
        # Convert string values to float for safety
        if isinstance(padding_left, str):
            padding_left = 0 if padding_left == 'auto' else float(padding_left)
        if isinstance(padding_right, str):
            padding_right = 0 if padding_right == 'auto' else float(padding_right)
        if isinstance(padding_top, str):
            padding_top = 0 if padding_top == 'auto' else float(padding_top)
        
        # Calculate content width
        if isinstance(self.box_metrics.content_width, str) and self.box_metrics.content_width == 'auto':
            # For auto width, use container width minus padding
            self.box_metrics.content_width = container_width - padding_left - padding_right
            self._update_box_dimensions()
        
        # Ensure block elements take the full width available to them
        # This is crucial for proper vertical stacking
        if self.box_metrics.width is None or self.box_metrics.width == 'auto':
            self.box_metrics.width = container_width
            
        # Process children
        content_x = self.box_metrics.x + padding_left
        content_y = self.box_metrics.y + padding_top  # Using converted padding_top
        
        # Layout children in a block formation (stacked vertically)
        for child in self.children:
            # Always position block children at the left edge of content box
            child_x = content_x
            
            # Layout the child
            child.layout(self.box_metrics.content_width, child_x, content_y)
            
            # Move down by the child's height for vertical stacking
            if child.box_metrics.margin_box_height is not None:
                if isinstance(child.box_metrics.margin_box_height, str):
                    if child.box_metrics.margin_box_height == 'auto':
                        child_height = 0  # Default height if auto
                    else:
                        try:
                            child_height = float(child.box_metrics.margin_box_height)
                        except (ValueError, TypeError):
                            child_height = 0
                else:
                    child_height = float(child.box_metrics.margin_box_height)
                
                # Get tag name for specific element handling
                child_tag = child.element.tag_name.lower() if hasattr(child.element, 'tag_name') else ''
                
                # Add extra spacing for div elements
                extra_spacing = 15 if child_tag == 'div' else 10
                    
                # Move content_y down by the child's height to stack next child
                content_y += child_height + extra_spacing  # Increased spacing between block children
            
        # Update height based on children if auto
        if self.box_metrics.height is None or self.box_metrics.height == 'auto':
            if content_y > self.box_metrics.y + self.box_metrics.padding_top:
                self.box_metrics.height = content_y - self.box_metrics.y
    
    def _layout_inline(self, container_width: int) -> None:
        """
        Perform layout for inline elements.
        
        Args:
            container_width: Width of the containing block
        """
        # Get all values before arithmetic operations
        margin_left = self.box_metrics.margin_left
        margin_top = self.box_metrics.margin_top
        border_left = self.box_metrics.border_left_width
        border_top = self.box_metrics.border_top_width
        padding_left = self.box_metrics.padding_left
        padding_top = self.box_metrics.padding_top
        
        # Convert string values to float, handling 'auto' as 0
        if isinstance(margin_left, str):
            margin_left = 0 if margin_left == 'auto' else float(margin_left)
        if isinstance(margin_top, str):
            margin_top = 0 if margin_top == 'auto' else float(margin_top)
        if isinstance(border_left, str):
            border_left = 0 if border_left == 'auto' else float(border_left)
        if isinstance(border_top, str):
            border_top = 0 if border_top == 'auto' else float(border_top)
        if isinstance(padding_left, str):
            padding_left = 0 if padding_left == 'auto' else float(padding_left)
        if isinstance(padding_top, str):
            padding_top = 0 if padding_top == 'auto' else float(padding_top)
        
        # Current x position for laying out children
        content_x = self.box_metrics.x + margin_left + border_left + padding_left
        content_y = self.box_metrics.y + margin_top + border_top + padding_top
        
        # Minimum space between inline elements
        min_inline_spacing = self.DEFAULT_INLINE_MARGIN
        
        # Layout children (simplified for now)
        for child in self.children:
            child.layout(container_width, content_x, content_y)
            
            # Get child's margin box width
            child_margin_box_width = child.box_metrics.margin_box_width
            if isinstance(child_margin_box_width, str):
                child_margin_box_width = 0 if child_margin_box_width == 'auto' else float(child_margin_box_width)
            
            # Calculate spacing (margins or minimum inline spacing)
            child_margins = 0
            if hasattr(child.box_metrics, 'margin_left') and hasattr(child.box_metrics, 'margin_right'):
                # Get numeric values for margins
                left_margin = child.box_metrics.margin_left
                right_margin = child.box_metrics.margin_right
                
                # Convert to numbers if needed
                if isinstance(left_margin, str):
                    left_margin = 0 if left_margin == 'auto' else float(left_margin)
                if isinstance(right_margin, str):
                    right_margin = 0 if right_margin == 'auto' else float(right_margin)
                    
                child_margins = left_margin + right_margin
                
            # Apply minimum spacing if the element doesn't have sufficient margins
            spacing = max(child_margins, min_inline_spacing)
            
            # Move right for next child - ensure additional spacing between elements
            # Make sure we're working with numeric values
            if isinstance(child_margin_box_width, (int, float)) and isinstance(spacing, (int, float)):
                content_x += child_margin_box_width + (spacing - child_margins) + 5  # Add 5px extra spacing to prevent merging
            else:
                # Fallback if types are mixed
                content_x += 5  # Minimum safe spacing
    
    def _layout_inline_block(self, container_width: int) -> None:
        """
        Perform layout for inline-block elements.
        
        Args:
            container_width: Width of the containing block
        """
        # Get all values before arithmetic operations
        margin_left = self.box_metrics.margin_left
        margin_top = self.box_metrics.margin_top
        border_left = self.box_metrics.border_left_width
        border_top = self.box_metrics.border_top_width
        padding_left = self.box_metrics.padding_left
        padding_top = self.box_metrics.padding_top
        content_width = self.box_metrics.content_width
        
        # Convert string values to float, handling 'auto' as 0
        if isinstance(margin_left, str):
            margin_left = 0 if margin_left == 'auto' else float(margin_left)
        if isinstance(margin_top, str):
            margin_top = 0 if margin_top == 'auto' else float(margin_top)
        if isinstance(border_left, str):
            border_left = 0 if border_left == 'auto' else float(border_left)
        if isinstance(border_top, str):
            border_top = 0 if border_top == 'auto' else float(border_top)
        if isinstance(padding_left, str):
            padding_left = 0 if padding_left == 'auto' else float(padding_left)
        if isinstance(padding_top, str):
            padding_top = 0 if padding_top == 'auto' else float(padding_top)
        if isinstance(content_width, str):
            content_width = 0 if content_width == 'auto' else float(content_width)
        
        # Adjust for content area
        content_x = self.box_metrics.x + margin_left + border_left + padding_left
        content_y = self.box_metrics.y + margin_top + border_top + padding_top
        
        # Available width for children
        if isinstance(self.box_metrics.content_width, str) and self.box_metrics.content_width == 'auto':
            # Default to a reasonable width if not specified
            child_container_width = 100  # A default value
            self.box_metrics.content_width = child_container_width
            self._update_box_dimensions()
        else:
            child_container_width = content_width
        
        # Current y within the content box
        current_y = content_y
        
        # Layout children
        for child in self.children:
            child.layout(child_container_width, content_x, current_y)
            
            # Get child's margin box height
            child_margin_box_height = child.box_metrics.margin_box_height
            if isinstance(child_margin_box_height, str):
                child_margin_box_height = 0 if child_margin_box_height == 'auto' else float(child_margin_box_height)
            
            # Move down for next child (block layout)
            current_y += child_margin_box_height
    
    def _layout_flex(self, container_width: int) -> None:
        """
        Perform layout for flex container elements.
        
        Args:
            container_width: Width of the containing block
        """
        # Get flex properties
        flex_direction = self.computed_style.get('flex-direction', 'row')
        justify_content = self.computed_style.get('justify-content', 'flex-start')
        align_items = self.computed_style.get('align-items', 'stretch')
        flex_wrap = self.computed_style.get('flex-wrap', 'nowrap')
        
        # Adjust for content area
        content_x = self.box_metrics.x + self.box_metrics.margin_left + self.box_metrics.border_left_width + self.box_metrics.padding_left
        content_y = self.box_metrics.y + self.box_metrics.margin_top + self.box_metrics.border_top_width + self.box_metrics.padding_top
        
        # Available width and height for children
        child_container_width = self.box_metrics.content_width
        
        # Current positions for layout
        current_x = content_x
        current_y = content_y
        
        # For row layout, calculate total flex grow factor and total width used
        if flex_direction == 'row':
            # First pass: layout children and collect flex information
            total_flex_grow = 0
            total_fixed_width = 0
            
            for child in self.children:
                # Get flex properties
                flex_grow = float(self.computed_style.get('flex-grow', '0'))
                
                # Layout child with temporary width
                child.layout(child_container_width, current_x, current_y)
                
                # Collect information for flexible sizing
                if 'flex-grow' in child.computed_style:
                    total_flex_grow += float(child.computed_style['flex-grow'])
                
                if child.box_metrics.content_width != 'auto':
                    total_fixed_width += child.box_metrics.margin_box_width
            
            # Calculate available space for flexible items
            available_space = max(0, child_container_width - total_fixed_width)
            
            # Second pass: adjust sizes and positions based on flex properties
            current_x = content_x
            
            for child in self.children:
                # Adjust width for flexible items
                if 'flex-grow' in child.computed_style and total_flex_grow > 0:
                    flex_grow = float(child.computed_style['flex-grow'])
                    flex_width = int(available_space * (flex_grow / total_flex_grow))
                    
                    if child.box_metrics.content_width == 'auto':
                        child.box_metrics.content_width = flex_width
                        child._update_box_dimensions()
                
                # Position child
                child.box_metrics.x = current_x
                
                # Move to next position
                current_x += child.box_metrics.margin_box_width
        
        elif flex_direction == 'column':
            # Similar logic for column layout
            # First pass: layout children and collect flex information
            total_flex_grow = 0
            total_fixed_height = 0
            
            for child in self.children:
                # Layout child with temporary height
                child.layout(child_container_width, current_x, current_y)
                
                # Collect information for flexible sizing
                if 'flex-grow' in child.computed_style:
                    total_flex_grow += float(child.computed_style['flex-grow'])
                
                if child.box_metrics.content_height != 'auto':
                    total_fixed_height += child.box_metrics.margin_box_height
            
            # For now, we don't know the container height, so we can't calculate available space accurately
            # In a real implementation, we would need to handle this better
            
            # Second pass: just position children
            current_y = content_y
            
            for child in self.children:
                # Position child
                child.box_metrics.x = content_x
                child.box_metrics.y = current_y
                
                # Move to next position
                current_y += child.box_metrics.margin_box_height 

class LayoutEngine:
    """
    Engine for calculating layout of HTML documents.
    
    Handles creating a layout tree from a DOM tree and computing positions and sizes.
    """
    
    def __init__(self, viewport_width: int = 800, viewport_height: int = 600):
        """
        Initialize the layout engine.
        
        Args:
            viewport_width: Width of the viewport
            viewport_height: Height of the viewport
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.layout_root = None
    
    def create_layout(self, document, viewport_width: int = None, viewport_height: int = None) -> Optional[LayoutBox]:
        """
        Create a layout tree from a document.
        
        Args:
            document: The document to create layout for
            viewport_width: Optional viewport width override
            viewport_height: Optional viewport height override
            
        Returns:
            Root of the layout tree
        """
        if viewport_width is not None:
            self.viewport_width = viewport_width
        if viewport_height is not None:
            self.viewport_height = viewport_height
            
        if not document or not document.document_element:
            return None
            
        # Create the layout tree
        self.layout_root = self._build_layout_tree(document.document_element)
        
        # Compute styles
        self.layout_root.compute_styles()
        
        # Perform layout
        self.layout_root.layout(self.viewport_width)
        
        return self.layout_root
    
    def _build_layout_tree(self, element) -> LayoutBox:
        """
        Build a layout tree from an element tree.
        
        Args:
            element: The root element
            
        Returns:
            Root of the layout tree
        """
        # Create a layout box for this element
        layout_box = LayoutBox(element)
        
        # Recursively add children
        for child in element.child_nodes:
            # Skip non-element nodes for now (like text, comments, etc.)
            if hasattr(child, 'node_type') and child.node_type == 1:  # ELEMENT_NODE
                child_box = self._build_layout_tree(child)
                layout_box.add_child(child_box)
            elif hasattr(child, 'node_type') and child.node_type == 3:  # TEXT_NODE
                # Handle text nodes specially
                # In a real browser, we would create anonymous boxes for text
                # For simplicity, we'll just include the text in the parent's content
                if hasattr(layout_box.element, 'text_content'):
                    layout_box.element.text_content += child.node_value
        
        return layout_box
    
    def _calculate_box_dimensions(self, layout_box: LayoutBox) -> None:
        """
        Calculate dimensions for a layout box.
        
        Args:
            layout_box: Layout box to calculate dimensions for
        """
        # Check if content dimensions are specified in the style
        styles = layout_box.computed_style
        
        # Get width and height from styles
        width = self._parse_dimension(styles.get('width', 'auto'))
        height = self._parse_dimension(styles.get('height', 'auto'))
        
        # Calculate box model properties
        margin_top = self._parse_dimension(styles.get('margin-top', '0'))
        margin_right = self._parse_dimension(styles.get('margin-right', '0'))
        margin_bottom = self._parse_dimension(styles.get('margin-bottom', '0'))
        margin_left = self._parse_dimension(styles.get('margin-left', '0'))
        
        padding_top = self._parse_dimension(styles.get('padding-top', '0'))
        padding_right = self._parse_dimension(styles.get('padding-right', '0'))
        padding_bottom = self._parse_dimension(styles.get('padding-bottom', '0'))
        padding_left = self._parse_dimension(styles.get('padding-left', '0'))
        
        border_top = self._parse_dimension(styles.get('border-top-width', '0'))
        border_right = self._parse_dimension(styles.get('border-right-width', '0'))
        border_bottom = self._parse_dimension(styles.get('border-bottom-width', '0'))
        border_left = self._parse_dimension(styles.get('border-left-width', '0'))
        
        # Update the box metrics
        layout_box.box_metrics.width = width
        layout_box.box_metrics.height = height
        
        layout_box.box_metrics.margin_top = margin_top
        layout_box.box_metrics.margin_right = margin_right
        layout_box.box_metrics.margin_bottom = margin_bottom
        layout_box.box_metrics.margin_left = margin_left
        
        layout_box.box_metrics.padding_top = padding_top
        layout_box.box_metrics.padding_right = padding_right
        layout_box.box_metrics.padding_bottom = padding_bottom
        layout_box.box_metrics.padding_left = padding_left
        
        layout_box.box_metrics.border_top_width = border_top
        layout_box.box_metrics.border_right_width = border_right
        layout_box.box_metrics.border_bottom_width = border_bottom
        layout_box.box_metrics.border_left_width = border_left
        
        # Update box dimensions
        layout_box._update_box_dimensions()
    
    def _parse_dimension(self, value: str) -> Union[int, str]:
        """
        Parse a CSS dimension value.
        
        Args:
            value: CSS dimension value (e.g., "10px", "50%", "auto")
            
        Returns:
            Integer pixel value or 'auto'
        """
        if not value or value == 'auto':
            return 'auto'
        
        # Handle percentage values - calculate based on parent container
        if value.endswith('%'):
            try:
                percentage = float(value[:-1]) / 100.0
                if self.parent:
                    # Use parent's content width for horizontal percentages
                    parent_width = self.parent.box_metrics.content_width
                    if isinstance(parent_width, str):
                        parent_width = 0 if parent_width == 'auto' else float(parent_width)
                    return int(parent_width * percentage)
                else:
                    # If no parent, use viewport width
                    return int(self.viewport_width * percentage)
            except ValueError:
                return 0
        
        # Handle pixel values
        if value.endswith('px'):
            try:
                return int(float(value[:-2]))
            except ValueError:
                return 0
        
        # Handle em values - calculate based on parent's font size
        if value.endswith('em'):
            try:
                em_value = float(value[:-2])
                if self.parent:
                    # Get parent's font size
                    parent_font_size = self._parse_dimension(self.parent.computed_style.get('font-size', '16px'))
                    if isinstance(parent_font_size, str):
                        parent_font_size = 16 if parent_font_size == 'auto' else float(parent_font_size)
                    return int(em_value * parent_font_size)
                else:
                    # Default to 16px if no parent
                    return int(em_value * 16)
            except ValueError:
                return 0
        
        # Handle rem values - calculate based on root font size
        if value.endswith('rem'):
            try:
                rem_value = float(value[:-3])
                # Always use root font size (16px) for rem
                return int(rem_value * 16)
            except ValueError:
                return 0
        
        # Handle viewport units
        if value.endswith('vw'):
            try:
                vw_value = float(value[:-2]) / 100.0
                return int(self.viewport_width * vw_value)
            except ValueError:
                return 0
        if value.endswith('vh'):
            try:
                vh_value = float(value[:-2]) / 100.0
                return int(self.viewport_height * vh_value)
            except ValueError:
                return 0
        
        # Handle calc() expressions
        if value.startswith('calc(') and value.endswith(')'):
            try:
                # Extract the expression inside calc()
                expr = value[5:-1].strip()
                # For now, handle simple arithmetic with px and %
                # This is a simplified version - in a real browser, we'd need a full CSS calc() parser
                if '+' in expr:
                    parts = expr.split('+')
                    total = 0
                    for part in parts:
                        total += self._parse_dimension(part.strip())
                    return total
                elif '-' in expr:
                    parts = expr.split('-')
                    total = self._parse_dimension(parts[0].strip())
                    for part in parts[1:]:
                        total -= self._parse_dimension(part.strip())
                    return total
                elif '*' in expr:
                    parts = expr.split('*')
                    total = 1
                    for part in parts:
                        total *= self._parse_dimension(part.strip())
                    return total
                elif '/' in expr:
                    parts = expr.split('/')
                    total = self._parse_dimension(parts[0].strip())
                    for part in parts[1:]:
                        divisor = self._parse_dimension(part.strip())
                        if divisor != 0:
                            total /= divisor
                    return int(total)
            except Exception:
                return 0
        
        # Handle unitless values as pixels
        try:
            return int(float(value))
        except ValueError:
            return 0 