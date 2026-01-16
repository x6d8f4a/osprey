"""Rich color palette utilities.

Provides functions to convert Rich color names to hex values
using the official Rich library color definitions.

For STANDARD ANSI colors (0-15), can optionally query the terminal's
actual color palette for accurate matching.
"""

from __future__ import annotations

import logging
import sys

_logger = logging.getLogger(__name__)

# Cache for terminal colors (populated at startup if TTY available)
_terminal_colors: dict[int, str] = {}


def query_terminal_color(color_index: int) -> str | None:
    """Query terminal for actual RGB of ANSI color using OSC 4.

    Uses the OSC 4 escape sequence to query the terminal's configured
    color for the given palette index. Only works when running in a
    terminal with TTY access.

    Args:
        color_index: ANSI color index (0-15 for standard colors)

    Returns:
        Hex color string (e.g., '#00cccc') or None if query fails
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    try:
        import select
        import termios
        import tty
    except ImportError:
        # Not available on Windows
        return None

    try:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        # OSC 4 query: \033]4;{index};?\033\\
        sys.stdout.write(f"\033]4;{color_index};?\033\\")
        sys.stdout.flush()

        # Read response with timeout
        response = ""
        while select.select([sys.stdin], [], [], 0.1)[0]:
            char = sys.stdin.read(1)
            response += char
            if char == "\\" or len(response) > 50:
                break

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        # Parse response: \033]4;{n};rgb:{rrrr}/{gggg}/{bbbb}\033\\
        # The values are 16-bit hex (0000-ffff)
        if "rgb:" in response:
            rgb_part = response.split("rgb:")[1].split("\033")[0]
            r, g, b = rgb_part.split("/")
            # Convert 16-bit to 8-bit (take first 2 hex digits)
            r_val = int(r[:2], 16)
            g_val = int(g[:2], 16)
            b_val = int(b[:2], 16)
            return f"#{r_val:02x}{g_val:02x}{b_val:02x}"
    except Exception:
        pass
    return None


def init_terminal_colors() -> None:
    """Query terminal colors for STANDARD range (0-15) at startup.

    Should be called once at application startup when running in a terminal.
    Results are cached for the session. If no TTY is available, this is a no-op.
    """
    global _terminal_colors

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        _logger.debug("No TTY available, using Rich default colors")
        return

    colors_loaded = {}
    for i in range(16):
        color = query_terminal_color(i)
        if color:
            _terminal_colors[i] = color
            colors_loaded[i] = color

    if colors_loaded:
        _logger.debug(f"Loaded {len(colors_loaded)} terminal colors")
    else:
        _logger.debug("Terminal color query not supported, using Rich defaults")


def get_rich_color_hex(color_name: str) -> str | None:
    """Convert a Rich color name to its hex value.

    For STANDARD colors (0-15), uses the terminal's actual palette if
    it was queried at startup. Otherwise uses Rich's truecolor representation.

    Args:
        color_name: Rich color name (e.g., 'sky_blue2', 'cyan')

    Returns:
        Hex color string (e.g., '#87afff') or None if invalid
    """
    try:
        from rich.color import Color, ColorType

        color = Color.parse(color_name)

        # For STANDARD colors, use terminal palette if available
        if color.type == ColorType.STANDARD and color.number in _terminal_colors:
            return _terminal_colors[color.number]

        # Otherwise use Rich's truecolor approximation
        triplet = color.get_truecolor()
        return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
    except Exception:
        return None
