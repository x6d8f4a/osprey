"""Rich color palette utilities.

Provides functions to convert Rich color names to hex values
using the official Rich library color definitions.
"""

from __future__ import annotations


def get_rich_color_hex(color_name: str) -> str | None:
    """Convert a Rich color name to its hex value.

    Uses Rich's Color class to get the exact truecolor representation
    from the 256-color ANSI palette.

    Args:
        color_name: Rich color name (e.g., 'sky_blue2', 'cyan')

    Returns:
        Hex color string (e.g., '#87afff') or None if invalid
    """
    try:
        from rich.color import Color

        color = Color.parse(color_name)
        triplet = color.get_truecolor()
        return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
    except Exception:
        return None
