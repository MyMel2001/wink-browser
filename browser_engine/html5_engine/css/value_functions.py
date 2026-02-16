"""
CSS Value Functions Implementation.

This module provides support for CSS math functions like calc(), min(), max(), and clamp().
"""

import re
import logging
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)


class CSSValueFunctions:
    """
    Evaluates CSS math functions like calc(), min(), max(), and clamp().
    """

    # Regex patterns for parsing
    NUMBER_PATTERN = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)')
    UNIT_PATTERN = re.compile(r'(px|em|rem|%|vw|vh|vmin|vmax|cm|mm|in|pt|pc|ch|ex|lh|rlh)?')

    # Pattern to match calc() function
    CALC_PATTERN = re.compile(r'calc\s*\(([^)]+)\)', re.IGNORECASE)

    # Pattern to match min() function
    MIN_PATTERN = re.compile(r'min\s*\(([^)]+)\)', re.IGNORECASE)

    # Pattern to match max() function
    MAX_PATTERN = re.compile(r'max\s*\(([^)]+)\)', re.IGNORECASE)

    # Pattern to match clamp() function
    CLAMP_PATTERN = re.compile(r'clamp\s*\(([^)]+)\)', re.IGNORECASE)

    def __init__(self, root_font_size: float = 16.0, viewport_width: float = 800.0,
                 viewport_height: float = 600.0):
        """
        Initialize the CSS value functions evaluator.

        Args:
            root_font_size: Root font size in pixels (for rem units)
            viewport_width: Viewport width in pixels (for vw units)
            viewport_height: Viewport height in pixels (for vh units)
        """
        self.root_font_size = root_font_size
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.parent_font_size = root_font_size  # Current element's parent font size (for em units)

    def set_viewport(self, width: float, height: float) -> None:
        """
        Update viewport dimensions.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
        """
        self.viewport_width = width
        self.viewport_height = height

    def set_parent_font_size(self, font_size: float) -> None:
        """
        Set the parent font size for em unit conversion.

        Args:
            font_size: Parent element's font size in pixels
        """
        self.parent_font_size = font_size

    def convert_to_px(self, value: float, unit: str) -> float:
        """
        Convert a value with unit to pixels.

        Args:
            value: Numeric value
            unit: CSS unit (px, em, rem, %, vw, vh, etc.)

        Returns:
            Value in pixels
        """
        unit = unit.lower() if unit else 'px'

        if unit == 'px':
            return value
        elif unit == 'em':
            return value * self.parent_font_size
        elif unit == 'rem':
            return value * self.root_font_size
        elif unit == '%':
            # Percentage depends on context; return as-is for now
            # Caller should handle percentage context
            return value  # Return percentage value; context-dependent
        elif unit == 'vw':
            return value * self.viewport_width / 100
        elif unit == 'vh':
            return value * self.viewport_height / 100
        elif unit == 'vmin':
            return value * min(self.viewport_width, self.viewport_height) / 100
        elif unit == 'vmax':
            return value * max(self.viewport_width, self.viewport_height) / 100
        elif unit == 'cm':
            return value * 37.8  # 1cm = 37.8px (at 96dpi)
        elif unit == 'mm':
            return value * 3.78  # 1mm = 3.78px
        elif unit == 'in':
            return value * 96  # 1in = 96px
        elif unit == 'pt':
            return value * 96 / 72  # 1pt = 96/72 px
        elif unit == 'pc':
            return value * 96 / 6  # 1pc = 96/6 px
        elif unit == 'ch':
            # Width of '0' character - approximate as 0.5em
            return value * self.parent_font_size * 0.5
        elif unit == 'ex':
            # x-height - approximate as 0.5em
            return value * self.parent_font_size * 0.5
        elif unit == 'lh':
            # Line height - approximate as 1.2em
            return value * self.parent_font_size * 1.2
        elif unit == 'rlh':
            # Root line height - approximate as 1.2rem
            return value * self.root_font_size * 1.2
        else:
            logger.warning(f"Unknown unit: {unit}")
            return value

    def parse_dimension(self, value_str: str) -> Tuple[float, str]:
        """
        Parse a dimension string into value and unit.

        Args:
            value_str: String like "10px", "2em", "50%"

        Returns:
            Tuple of (numeric_value, unit)
        """
        value_str = value_str.strip()

        # Match number and optional unit
        match = re.match(r'([-+]?(?:\d+\.?\d*|\.\d+))\s*(px|em|rem|%|vw|vh|vmin|vmax|cm|mm|in|pt|pc|ch|ex|lh|rlh)?', value_str, re.IGNORECASE)

        if match:
            value = float(match.group(1))
            unit = match.group(2) or 'px'
            return value, unit

        # Try to parse just a number
        try:
            return float(value_str), 'px'
        except ValueError:
            logger.warning(f"Could not parse dimension: {value_str}")
            return 0.0, 'px'

    def evaluate_calc(self, expression: str) -> float:
        """
        Evaluate a calc() expression.

        Supports: +, -, *, / with proper precedence and parentheses.

        Args:
            expression: The expression inside calc()

        Returns:
            Result in pixels (mixed units converted where possible)
        """
        expression = expression.strip()

        # First, resolve any nested functions
        expression = self.resolve_functions(expression)

        # Tokenize the expression
        # We need to handle units properly
        tokens = self._tokenize_calc(expression)

        # Evaluate using shunting-yard or direct evaluation
        result = self._evaluate_tokens(tokens)

        return result

    def _tokenize_calc(self, expression: str) -> list:
        """
        Tokenize a calc expression.

        Args:
            expression: The expression to tokenize

        Returns:
            List of tokens (numbers with units, operators, parentheses)
        """
        tokens = []
        i = 0
        expression = expression.strip()

        while i < len(expression):
            c = expression[i]

            if c.isspace():
                i += 1
                continue

            if c in '+-*/()':
                tokens.append(c)
                i += 1
            elif c.isdigit() or c == '.' or (c == '-' and (i == 0 or tokens and tokens[-1] in '(+-*/')):
                # Parse a number with optional unit
                j = i
                if c == '-':
                    j += 1

                while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1

                # Check for unit
                while j < len(expression) and expression[j].isalpha():
                    j += 1

                token = expression[i:j].strip()
                tokens.append(token)
                i = j
            else:
                i += 1

        return tokens

    def _evaluate_tokens(self, tokens: list) -> float:
        """
        Evaluate a list of tokens from a calc expression.

        Args:
            tokens: List of tokens

        Returns:
            Result value
        """
        # Simple recursive descent parser for calc expressions
        # Handle multiplication and division first, then addition and subtraction

        # Convert to postfix (shunting-yard)
        output = []
        operators = []

        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}

        for token in tokens:
            if token in '+-*/':
                while (operators and operators[-1] != '(' and
                       operators[-1] in precedence and
                       precedence[operators[-1]] >= precedence[token]):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if operators:
                    operators.pop()  # Remove the '('
            else:
                output.append(token)

        while operators:
            output.append(operators.pop())

        # Evaluate postfix
        stack = []
        for token in output:
            if token in '+-*/':
                if len(stack) < 2:
                    continue
                b = stack.pop()
                a = stack.pop()

                # Get values in px
                if isinstance(a, str):
                    val_a, unit_a = self.parse_dimension(a)
                    a = self.convert_to_px(val_a, unit_a)
                if isinstance(b, str):
                    val_b, unit_b = self.parse_dimension(b)
                    b = self.convert_to_px(val_b, unit_b)

                if token == '+':
                    stack.append(a + b)
                elif token == '-':
                    stack.append(a - b)
                elif token == '*':
                    stack.append(a * b)
                elif token == '/':
                    stack.append(a / b if b != 0 else 0)
            else:
                stack.append(token)

        result = stack[0] if stack else 0
        if isinstance(result, str):
            val, unit = self.parse_dimension(result)
            return self.convert_to_px(val, unit)
        return result

    def evaluate_min(self, args: str) -> float:
        """
        Evaluate a min() function.

        Args:
            args: Comma-separated list of values

        Returns:
            Minimum value in pixels
        """
        values = [v.strip() for v in args.split(',')]
        pixel_values = []

        for v in values:
            # Resolve nested functions first
            v = self.resolve_functions(v)
            val, unit = self.parse_dimension(v)
            pixel_values.append(self.convert_to_px(val, unit))

        return min(pixel_values) if pixel_values else 0

    def evaluate_max(self, args: str) -> float:
        """
        Evaluate a max() function.

        Args:
            args: Comma-separated list of values

        Returns:
            Maximum value in pixels
        """
        values = [v.strip() for v in args.split(',')]
        pixel_values = []

        for v in values:
            # Resolve nested functions first
            v = self.resolve_functions(v)
            val, unit = self.parse_dimension(v)
            pixel_values.append(self.convert_to_px(val, unit))

        return max(pixel_values) if pixel_values else 0

    def evaluate_clamp(self, args: str) -> float:
        """
        Evaluate a clamp() function.

        clamp(min, preferred, max) returns a value between min and max.

        Args:
            args: Three comma-separated values: min, preferred, max

        Returns:
            Clamped value in pixels
        """
        values = [v.strip() for v in args.split(',')]

        if len(values) != 3:
            logger.warning(f"clamp() requires 3 arguments, got {len(values)}")
            return 0

        min_val, pref_val, max_val = values

        # Resolve nested functions
        min_val = self.resolve_functions(min_val)
        pref_val = self.resolve_functions(pref_val)
        max_val = self.resolve_functions(max_val)

        # Convert to pixels
        min_v, min_u = self.parse_dimension(min_val)
        pref_v, pref_u = self.parse_dimension(pref_val)
        max_v, max_u = self.parse_dimension(max_val)

        min_px = self.convert_to_px(min_v, min_u)
        pref_px = self.convert_to_px(pref_v, pref_u)
        max_px = self.convert_to_px(max_v, max_u)

        # Clamp: return value between min and max
        return max(min_px, min(pref_px, max_px))

    def resolve_functions(self, value: str) -> str:
        """
        Resolve all CSS math functions in a value.

        Args:
            value: CSS value that may contain calc(), min(), max(), clamp()

        Returns:
            Resolved value as a pixel string
        """
        original = value

        # Resolve nested functions first (inside out)
        max_iterations = 10
        for _ in range(max_iterations):
            changed = False

            # Check for calc()
            calc_match = self.CALC_PATTERN.search(value)
            if calc_match:
                result = self.evaluate_calc(calc_match.group(1))
                value = self.CALC_PATTERN.sub(f'{result}px', value, count=1)
                changed = True

            # Check for min()
            min_match = self.MIN_PATTERN.search(value)
            if min_match:
                result = self.evaluate_min(min_match.group(1))
                value = self.MIN_PATTERN.sub(f'{result}px', value, count=1)
                changed = True

            # Check for max()
            max_match = self.MAX_PATTERN.search(value)
            if max_match:
                result = self.evaluate_max(max_match.group(1))
                value = self.MAX_PATTERN.sub(f'{result}px', value, count=1)
                changed = True

            # Check for clamp()
            clamp_match = self.CLAMP_PATTERN.search(value)
            if clamp_match:
                result = self.evaluate_clamp(clamp_match.group(1))
                value = self.CLAMP_PATTERN.sub(f'{result}px', value, count=1)
                changed = True

            if not changed:
                break

        return value


# Global instance
_value_functions = CSSValueFunctions()


def get_value_functions() -> CSSValueFunctions:
    """Get the global CSS value functions evaluator."""
    return _value_functions


def resolve_css_value(value: str, viewport_width: float = None,
                      viewport_height: float = None,
                      parent_font_size: float = None) -> str:
    """
    Convenience function to resolve CSS math functions in a value.

    Args:
        value: CSS value that may contain calc(), min(), max(), clamp()
        viewport_width: Optional viewport width override
        viewport_height: Optional viewport height override
        parent_font_size: Optional parent font size override

    Returns:
        Resolved value
    """
    vf = get_value_functions()

    if viewport_width is not None or viewport_height is not None:
        vf.set_viewport(
            viewport_width or vf.viewport_width,
            viewport_height or vf.viewport_height
        )

    if parent_font_size is not None:
        vf.set_parent_font_size(parent_font_size)

    return vf.resolve_functions(value)