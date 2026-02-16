"""
CSS Custom Properties (CSS Variables) Implementation.

This module provides support for CSS custom properties (--name: value)
and the var() function for the HTML5 engine.
"""

import re
import logging
from typing import Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class CSSCustomProperties:
    """
    Manages CSS custom properties (CSS variables).

    Custom properties are defined with -- prefix and accessed via var() function.
    They inherit down the DOM tree and can be overridden at any level.
    """

    # Regex to match var() function
    VAR_PATTERN = re.compile(
        r'var\s*\(\s*(--[a-zA-Z0-9_-]+)\s*(?:,\s*(.+?))?\s*\)',
        re.IGNORECASE
    )

    # Regex to match custom property declarations
    CUSTOM_PROPERTY_PATTERN = re.compile(r'^--[a-zA-Z0-9_-]+$')

    def __init__(self):
        """Initialize the custom properties manager."""
        # Store custom properties per element (element_id -> properties dict)
        self._element_properties: Dict[int, Dict[str, str]] = {}

        # Root level custom properties (for :root selector)
        self._root_properties: Dict[str, str] = {}

    def is_custom_property(self, name: str) -> bool:
        """
        Check if a property name is a custom property.

        Args:
            name: Property name to check

        Returns:
            True if the property name starts with --
        """
        return bool(self.CUSTOM_PROPERTY_PATTERN.match(name))

    def set_property(self, element_id: int, name: str, value: str) -> None:
        """
        Set a custom property for an element.

        Args:
            element_id: The element's unique ID
            name: Custom property name (with -- prefix)
            value: Property value
        """
        if not self.is_custom_property(name):
            logger.warning(f"Invalid custom property name: {name}")
            return

        if element_id not in self._element_properties:
            self._element_properties[element_id] = {}

        self._element_properties[element_id][name] = value

    def set_root_property(self, name: str, value: str) -> None:
        """
        Set a custom property on the root element (:root).

        Args:
            name: Custom property name (with -- prefix)
            value: Property value
        """
        if not self.is_custom_property(name):
            logger.warning(f"Invalid custom property name: {name}")
            return

        self._root_properties[name] = value

    def get_property(self, element_id: int, name: str,
                     inherited_properties: Dict[str, str] = None) -> Optional[str]:
        """
        Get a custom property value for an element.

        Custom properties inherit, so we check the element first,
        then fall back to inherited properties, then root properties.

        Args:
            element_id: The element's unique ID
            name: Custom property name (with -- prefix)
            inherited_properties: Properties inherited from parent

        Returns:
            The property value or None if not found
        """
        # Check element's own properties
        if element_id in self._element_properties:
            if name in self._element_properties[element_id]:
                return self._element_properties[element_id][name]

        # Check inherited properties
        if inherited_properties and name in inherited_properties:
            return inherited_properties[name]

        # Check root properties
        if name in self._root_properties:
            return self._root_properties[name]

        return None

    def resolve_var(self, value: str, element_id: int,
                    inherited_properties: Dict[str, str] = None) -> str:
        """
        Resolve all var() references in a value.

        Args:
            value: The CSS value that may contain var()
            element_id: The element's unique ID
            inherited_properties: Properties inherited from parent

        Returns:
            The value with all var() references resolved
        """
        if 'var(' not in value.lower():
            return value

        def replace_var(match):
            prop_name = match.group(1)
            fallback = match.group(2)

            prop_value = self.get_property(element_id, prop_name, inherited_properties)

            if prop_value is not None:
                # Recursively resolve nested var() in the property value
                return self.resolve_var(prop_value, element_id, inherited_properties)
            elif fallback:
                # Use fallback value
                return fallback.strip()
            else:
                # No value and no fallback - return empty or keep original
                logger.warning(f"CSS variable {prop_name} not found and no fallback provided")
                return match.group(0)  # Return original if not found

        # Replace all var() occurrences
        resolved = self.VAR_PATTERN.sub(replace_var, value)

        return resolved

    def parse_custom_properties(self, style_dict: Dict[str, str], element_id: int) -> Dict[str, str]:
        """
        Extract custom properties from a style dictionary and store them.

        Args:
            style_dict: Dictionary of CSS property names to values
            element_id: The element's unique ID

        Returns:
            Dictionary of non-custom properties (for further processing)
        """
        regular_properties = {}
        custom_properties = {}

        for name, value in style_dict.items():
            if self.is_custom_property(name):
                custom_properties[name] = value
            else:
                regular_properties[name] = value

        # Store custom properties for this element
        if custom_properties:
            if element_id not in self._element_properties:
                self._element_properties[element_id] = {}
            self._element_properties[element_id].update(custom_properties)

        return regular_properties

    def resolve_all_vars(self, style_dict: Dict[str, str], element_id: int,
                         inherited_properties: Dict[str, str] = None) -> Dict[str, str]:
        """
        Resolve all var() references in a style dictionary.

        Args:
            style_dict: Dictionary of CSS property names to values
            element_id: The element's unique ID
            inherited_properties: Properties inherited from parent

        Returns:
            Dictionary with all var() references resolved
        """
        resolved = {}

        for name, value in style_dict.items():
            if isinstance(value, str):
                resolved[name] = self.resolve_var(value, element_id, inherited_properties)
            else:
                resolved[name] = value

        return resolved

    def get_inherited_custom_properties(self, element_id: int) -> Dict[str, str]:
        """
        Get custom properties that should be inherited by children.

        All custom properties inherit by default.

        Args:
            element_id: The element's unique ID

        Returns:
            Dictionary of custom properties to inherit
        """
        if element_id in self._element_properties:
            return dict(self._element_properties[element_id])
        return {}

    def clear_element_properties(self, element_id: int) -> None:
        """
        Clear all custom properties for an element.

        Args:
            element_id: The element's unique ID
        """
        if element_id in self._element_properties:
            del self._element_properties[element_id]

    def clear_all(self) -> None:
        """Clear all stored custom properties."""
        self._element_properties.clear()
        self._root_properties.clear()


# Global instance for convenience
_custom_properties = CSSCustomProperties()


def get_custom_properties() -> CSSCustomProperties:
    """Get the global CSS custom properties manager."""
    return _custom_properties


def resolve_css_value(value: str, element_id: int,
                      inherited_properties: Dict[str, str] = None) -> str:
    """
    Convenience function to resolve var() in a CSS value.

    Args:
        value: The CSS value
        element_id: The element's unique ID
        inherited_properties: Properties inherited from parent

    Returns:
        The resolved value
    """
    return _custom_properties.resolve_var(value, element_id, inherited_properties)