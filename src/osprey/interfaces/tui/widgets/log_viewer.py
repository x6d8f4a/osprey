"""Log Viewer modal for displaying step logs."""

import textwrap

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static


class LogViewer(ModalScreen[None]):
    """Modal screen for viewing step logs.

    Displays formatted log messages in a scrollable container.
    Similar to CommandPalette but simpler - just displays logs.
    """

    BINDINGS = [
        ("escape", "dismiss_viewer", "Close"),
    ]

    def __init__(self, title: str, logs: list[tuple[str, str]]):
        """Initialize the log viewer.

        Args:
            title: The title to display (e.g., "Task Extraction - Logs").
            logs: List of (status, message) tuples.
        """
        super().__init__()
        self.log_title = title
        self.logs = logs

    def compose(self) -> ComposeResult:
        """Compose the log viewer layout."""
        with Container(id="log-viewer-container"):
            with Horizontal(id="log-viewer-header"):
                yield Static(self.log_title, id="log-viewer-title")
                yield Static("esc", id="log-viewer-dismiss-hint")
            with ScrollableContainer(id="log-viewer-content"):
                yield Static(self._format_logs(), id="log-viewer-logs")

    def _format_logs(self) -> str:
        """Format log messages with status indicators and colors.

        Returns:
            Formatted string with Rich markup for colors.
        """
        if not self.logs:
            return "[dim]No logs available[/dim]"

        # Same indicators as ProcessingStep/ProcessingBlock
        INDICATOR_PENDING = "·"
        INDICATOR_SUCCESS = "✓"
        INDICATOR_ERROR = "✗"
        INDICATOR_WARNING = "⚠"

        lines = []
        for status, msg in self.logs:
            # Map status to color and indicator
            color_map = {
                "error": "$error",
                "warning": "$warning",
                "success": "$success",
                "key_info": "$text",
                "info": "",
                "debug": "$text-muted",
                "timing": "$accent",
                "status": "",
                "approval": "$warning",
                "resume": "$success",
            }
            indicator_map = {
                "error": INDICATOR_ERROR,
                "warning": INDICATOR_WARNING,
                "success": INDICATOR_SUCCESS,
                "key_info": INDICATOR_SUCCESS,
                "approval": INDICATOR_WARNING,
            }

            color = color_map.get(status, "")
            indicator = indicator_map.get(status, INDICATOR_PENDING)

            # Wrap long messages
            wrapped = textwrap.fill(
                msg,
                width=100,
                initial_indent="",
                subsequent_indent="  ",
            )

            if color:
                lines.append(f"[{color}]{indicator} {wrapped}[/{color}]")
            else:
                lines.append(f"{indicator} {wrapped}")

        return "\n".join(lines)

    def action_dismiss_viewer(self) -> None:
        """Dismiss the log viewer."""
        self.dismiss(None)
