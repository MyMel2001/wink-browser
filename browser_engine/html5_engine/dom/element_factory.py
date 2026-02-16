"""
Element Factory Module

Provides factory methods for creating HTML element instances.
"""

from typing import Dict, Optional, Any
from .element import Element


"""
Element Factory for creating HTML elements.

This module provides a factory class for creating appropriate Element
subclasses based on HTML tag names.
"""

from typing import Dict, Optional, Any
from .element import Element


class ElementFactory:
    """
    Factory class for creating HTML elements.
    """
    
    @classmethod
    def create_element(cls, tag_name: str, attributes: Dict[str, str] = None, document=None) -> Element:
        """
        Create an element based on tag name.
        
        Args:
            tag_name: HTML tag name
            attributes: Element attributes
            document: Parent document
            
        Returns:
            Appropriate Element subclass instance
        """
        tag_name = tag_name.lower()
        attributes = attributes or {}
        
        # Block elements
        if tag_name == 'div':
            return DivElement(tag_name, attributes, document)
        elif tag_name == 'p':
            return ParagraphElement(tag_name, attributes, document)
        elif tag_name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            return HeadingElement(tag_name, attributes, document)
        elif tag_name in ('ul', 'ol'):
            return ListElement(tag_name, attributes, document)
        elif tag_name == 'li':
            return ListItemElement(tag_name, attributes, document)
        elif tag_name == 'table':
            return TableElement(tag_name, attributes, document)
        elif tag_name in ('tr', 'thead', 'tbody', 'tfoot'):
            return TableRowElement(tag_name, attributes, document)
        elif tag_name in ('td', 'th'):
            return TableCellElement(tag_name, attributes, document)
        
        # Inline elements
        elif tag_name == 'a':
            return AnchorElement(tag_name, attributes, document)
        elif tag_name == 'img':
            return ImageElement(tag_name, attributes, document)
        elif tag_name in ('strong', 'b'):
            return StrongElement(tag_name, attributes, document)
        elif tag_name in ('em', 'i'):
            return EmphasisElement(tag_name, attributes, document)
        elif tag_name == 'u':
            return UnderlineElement(tag_name, attributes, document)
        elif tag_name in ('s', 'strike', 'del'):
            return StrikethroughElement(tag_name, attributes, document)
        elif tag_name == 'span':
            return SpanElement(tag_name, attributes, document)
        elif tag_name == 'br':
            return LineBreakElement(tag_name, attributes, document)
        
        # Form elements
        elif tag_name == 'form':
            return FormElement(tag_name, attributes, document)
        elif tag_name == 'input':
            return InputElement(tag_name, attributes, document)
        elif tag_name == 'button':
            return ButtonElement(tag_name, attributes, document)
        elif tag_name == 'textarea':
            return TextAreaElement(tag_name, attributes, document)
        elif tag_name == 'select':
            return SelectElement(tag_name, attributes, document)
        elif tag_name == 'option':
            return OptionElement(tag_name, attributes, document)
        
        # Media elements
        elif tag_name == 'audio':
            return AudioElement(tag_name, attributes, document)
        elif tag_name == 'video':
            return VideoElement(tag_name, attributes, document)
        elif tag_name == 'source':
            return SourceElement(tag_name, attributes, document)
        
        # Default
        return Element(tag_name, attributes, document)

class DivElement(Element):
    """
    HTML <div> element representation.
    
    A generic block-level container for content.
    """
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize a div element.
        
        Args:
            tag_name: The tag name (should be 'div')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'

class SpanElement(Element):
    """
    HTML <span> element representation.
    
    A generic inline container for content.
    """
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize a span element.
        
        Args:
            tag_name: The tag name (should be 'span')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'

class StrongElement(Element):
    """
    HTML <strong> or <b> element representation.
    
    Represents strong importance, seriousness, or urgency.
    """
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize a strong element.
        
        Args:
            tag_name: The tag name ('strong' or 'b')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'
        self.style['font-weight'] = 'bold'

class EmphasisElement(Element):
    """
    HTML <em> or <i> element representation.
    
    Marks text that has stress emphasis.
    """
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize an emphasis element.
        
        Args:
            tag_name: The tag name ('em' or 'i')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'
        self.style['font-style'] = 'italic'

class UnderlineElement(Element):
    """
    HTML <u> element representation.
    
    Represents text that should be stylistically different,
    such as misspelled words or proper nouns in Chinese.
    """
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize an underline element.
        
        Args:
            tag_name: The tag name (should be 'u')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'
        self.style['text-decoration'] = 'underline'

class StrikethroughElement(Element):
    """
    HTML <s>, <strike>, or <del> element representation.

    Represents text that is no longer correct, accurate or relevant.
    """

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        """
        Initialize a strikethrough element.

        Args:
            tag_name: The tag name ('s', 'strike', or 'del')
            attributes: Element attributes
            document: Parent document
        """
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'
        self.style['text-decoration'] = 'line-through'


class ParagraphElement(Element):
    """HTML <p> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'
        self.style['margin-top'] = '1em'
        self.style['margin-bottom'] = '1em'


class HeadingElement(Element):
    """HTML <h1>-<h6> element representation."""

    FONT_SIZES = {
        'h1': '2em', 'h2': '1.5em', 'h3': '1.17em',
        'h4': '1em', 'h5': '0.83em', 'h6': '0.67em'
    }

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'
        self.style['font-weight'] = 'bold'
        self.style['font-size'] = self.FONT_SIZES.get(tag_name, '1em')
        self.style['margin-top'] = '0.67em'
        self.style['margin-bottom'] = '0.67em'


class ListElement(Element):
    """HTML <ul> or <ol> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'
        self.style['margin-top'] = '1em'
        self.style['margin-bottom'] = '1em'
        self.style['padding-left'] = '40px'
        self.style['list-style-type'] = 'disc' if tag_name == 'ul' else 'decimal'


class ListItemElement(Element):
    """HTML <li> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'list-item'


class TableElement(Element):
    """HTML <table> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'table'
        self.style['border-collapse'] = 'separate'
        self.style['border-spacing'] = '2px'
        self.style['border-color'] = 'gray'


class TableRowElement(Element):
    """HTML <tr>, <thead>, <tbody>, <tfoot> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'table-row-group' if tag_name in ('thead', 'tbody', 'tfoot') else 'table-row'


class TableCellElement(Element):
    """HTML <td> or <th> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'table-cell'
        self.style['padding'] = '1px'
        if tag_name == 'th':
            self.style['font-weight'] = 'bold'
            self.style['text-align'] = 'center'


class AnchorElement(Element):
    """HTML <a> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'
        self.style['color'] = '#0000EE'
        self.style['text-decoration'] = 'underline'
        self.style['cursor'] = 'pointer'

    @property
    def href(self) -> str:
        """Get the href attribute."""
        return self.get_attribute('href') or ''

    @href.setter
    def href(self, value: str):
        """Set the href attribute."""
        self.set_attribute('href', value)


class ImageElement(Element):
    """HTML <img> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def src(self) -> str:
        """Get the src attribute."""
        return self.get_attribute('src') or ''

    @src.setter
    def src(self, value: str):
        """Set the src attribute."""
        self.set_attribute('src', value)

    @property
    def alt(self) -> str:
        """Get the alt attribute."""
        return self.get_attribute('alt') or ''

    @alt.setter
    def alt(self, value: str):
        """Set the alt attribute."""
        self.set_attribute('alt', value)


class LineBreakElement(Element):
    """HTML <br> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline'


class FormElement(Element):
    """HTML <form> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'

    @property
    def action(self) -> str:
        """Get the action attribute."""
        return self.get_attribute('action') or ''

    @property
    def method(self) -> str:
        """Get the method attribute."""
        return self.get_attribute('method') or 'GET'

    def submit(self):
        """Submit the form."""
        # TODO: Implement form submission
        pass

    def reset(self):
        """Reset the form."""
        # TODO: Implement form reset
        pass


class InputElement(Element):
    """HTML <input> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def type(self) -> str:
        """Get the input type."""
        return self.get_attribute('type') or 'text'

    @property
    def value(self) -> str:
        """Get the input value."""
        return self.get_attribute('value') or ''

    @value.setter
    def value(self, val: str):
        """Set the input value."""
        self.set_attribute('value', val)

    @property
    def name(self) -> str:
        """Get the input name."""
        return self.get_attribute('name') or ''

    @property
    def placeholder(self) -> str:
        """Get the placeholder text."""
        return self.get_attribute('placeholder') or ''

    @property
    def disabled(self) -> bool:
        """Check if input is disabled."""
        return self.has_attribute('disabled')

    @property
    def checked(self) -> bool:
        """Check if checkbox/radio is checked."""
        return self.has_attribute('checked')


class ButtonElement(Element):
    """HTML <button> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'
        self.style['cursor'] = 'pointer'

    @property
    def type(self) -> str:
        """Get the button type."""
        return self.get_attribute('type') or 'submit'

    @property
    def disabled(self) -> bool:
        """Check if button is disabled."""
        return self.has_attribute('disabled')


class TextAreaElement(Element):
    """HTML <textarea> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def value(self) -> str:
        """Get the textarea value."""
        return self.get_attribute('value') or self.text_content or ''

    @value.setter
    def value(self, val: str):
        """Set the textarea value."""
        self.set_attribute('value', val)

    @property
    def rows(self) -> int:
        """Get the number of rows."""
        return int(self.get_attribute('rows') or '2')

    @property
    def cols(self) -> int:
        """Get the number of columns."""
        return int(self.get_attribute('cols') or '20')


class SelectElement(Element):
    """HTML <select> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def value(self) -> str:
        """Get the selected value."""
        # Find selected option
        for child in self.children:
            if hasattr(child, 'has_attribute') and child.has_attribute('selected'):
                return child.get_attribute('value') or child.text_content or ''
        return ''

    @property
    def options(self) -> list:
        """Get all option elements."""
        return [child for child in self.children if hasattr(child, 'tag_name') and child.tag_name.lower() == 'option']


class OptionElement(Element):
    """HTML <option> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'block'

    @property
    def value(self) -> str:
        """Get the option value."""
        return self.get_attribute('value') or self.text_content or ''

    @property
    def selected(self) -> bool:
        """Check if option is selected."""
        return self.has_attribute('selected')

    @selected.setter
    def selected(self, val: bool):
        """Set the selected state."""
        if val:
            self.set_attribute('selected', 'selected')
        else:
            self.remove_attribute('selected')


class AudioElement(Element):
    """HTML <audio> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def src(self) -> str:
        """Get the audio source."""
        return self.get_attribute('src') or ''

    @property
    def autoplay(self) -> bool:
        """Check if autoplay is enabled."""
        return self.has_attribute('autoplay')

    @property
    def controls(self) -> bool:
        """Check if controls are shown."""
        return self.has_attribute('controls')

    @property
    def loop(self) -> bool:
        """Check if looping is enabled."""
        return self.has_attribute('loop')

    def play(self):
        """Start playback."""
        # TODO: Implement audio playback
        pass

    def pause(self):
        """Pause playback."""
        # TODO: Implement audio pause
        pass


class VideoElement(Element):
    """HTML <video> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'inline-block'

    @property
    def src(self) -> str:
        """Get the video source."""
        return self.get_attribute('src') or ''

    @property
    def poster(self) -> str:
        """Get the poster image URL."""
        return self.get_attribute('poster') or ''

    @property
    def autoplay(self) -> bool:
        """Check if autoplay is enabled."""
        return self.has_attribute('autoplay')

    @property
    def controls(self) -> bool:
        """Check if controls are shown."""
        return self.has_attribute('controls')

    @property
    def loop(self) -> bool:
        """Check if looping is enabled."""
        return self.has_attribute('loop')

    @property
    def muted(self) -> bool:
        """Check if audio is muted."""
        return self.has_attribute('muted')

    def play(self):
        """Start playback."""
        # TODO: Implement video playback
        pass

    def pause(self):
        """Pause playback."""
        # TODO: Implement video pause
        pass


class SourceElement(Element):
    """HTML <source> element representation."""

    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, document=None):
        super().__init__(tag_name, attributes, document)
        self.style['display'] = 'none'

    @property
    def src(self) -> str:
        """Get the source URL."""
        return self.get_attribute('src') or ''

    @property
    def type(self) -> str:
        """Get the media type."""
        return self.get_attribute('type') or ''

    @property
    def media(self) -> str:
        """Get the media query."""
        return self.get_attribute('media') or '' 