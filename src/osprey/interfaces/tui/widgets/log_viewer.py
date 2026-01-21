"""Log Viewer modal for displaying step logs with live updates."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Static

if TYPE_CHECKING:
    from osprey.interfaces.tui.widgets.blocks import ProcessingStep


class LogEntry(Horizontal):
    """A single log entry with message and timestamp columns.

    Uses horizontal layout for proper column alignment regardless of
    emoji or special character content in the message.
    """

    def __init__(self, message: str, timestamp_str: str, style_class: str = "") -> None:
        """Initialize the log entry.

        Args:
            message: The styled log message (with Rich markup).
            timestamp_str: The styled timestamp string (with Rich markup).
            style_class: Optional CSS class for additional styling.
        """
        super().__init__(classes=style_class if style_class else None)
        self._message = message
        self._timestamp_str = timestamp_str

    def compose(self) -> ComposeResult:
        """Compose the log entry with message and timestamp."""
        yield Static(self._message, classes="log-message")
        yield Static(self._timestamp_str, classes="log-timestamp")


class LogViewer(ModalScreen[None]):
    """Modal screen for viewing step logs with live updates.

    Displays formatted log messages in a scrollable container.
    Supports live updates via message-based push when given a ProcessingStep reference.
    """

    BINDINGS = [
        ("escape", "dismiss_viewer", "Close"),
        ("enter", "dismiss_viewer", "Close"),
    ]

    def __init__(
        self,
        title: str,
        log_source: list[tuple[str, str, datetime | None]] | ProcessingStep,
    ):
        """Initialize the log viewer.

        Args:
            title: The title to display (e.g., "Task Extraction - Logs").
            log_source: Either a list of (status, message, timestamp) tuples (static),
                       or a ProcessingStep reference (live updates via messages).
        """
        super().__init__()
        self.log_title = title
        self._log_source = log_source

    def _get_logs(self) -> list[tuple[str, str, datetime | None]]:
        """Get current logs from the source.

        Returns:
            List of (status, message, timestamp) tuples.
        """
        if isinstance(self._log_source, list):
            return self._log_source
        # It's a ProcessingStep - read from its _log_messages
        return getattr(self._log_source, "_log_messages", [])

    def _is_live_source(self) -> bool:
        """Check if log source supports live updates."""
        return not isinstance(self._log_source, list)

    def compose(self) -> ComposeResult:
        """Compose the log viewer layout."""
        with Container(id="log-viewer-container"):
            with Horizontal(id="log-viewer-header"):
                yield Static(self.log_title, id="log-viewer-title")
                yield Static("", id="log-header-spacer")
                yield Static("esc", id="log-viewer-dismiss-hint")
            with VerticalScroll(id="log-viewer-content"):
                yield from self._build_log_entries()
            yield Static(
                "[$text bold]␣[/$text bold] to pg down · "
                "[$text bold]b[/$text bold] to pg up · "
                "[$text bold]⏎[/$text bold] to close",
                id="log-viewer-footer",
            )

    def on_processing_step_log_added(self, event: ProcessingStep.LogAdded) -> None:
        """Handle new log from the source ProcessingStep.

        Only processes logs from our specific log source to avoid
        cross-contamination between multiple open log viewers.
        """
        # Import here to avoid circular import
        from osprey.interfaces.tui.widgets.blocks import ProcessingStep

        # Only process if this log came from our source
        if self._is_live_source() and isinstance(self._log_source, ProcessingStep):
            # Check if the message came from our log source
            # Messages bubble up, so we check the sender
            if event._sender is self._log_source:
                ts_str = (
                    f"[$text-disabled]{event.timestamp.strftime('%b %d %H:%M:%S')}[/$text-disabled]"
                    if event.timestamp
                    else ""
                )
                styled_msg = self._style_message(event.message, event.status)
                try:
                    content = self.query_one("#log-viewer-content", VerticalScroll)
                    content.mount(LogEntry(styled_msg, ts_str))
                except Exception:
                    pass  # Widget may not exist during transitions

    def _build_log_entries(self) -> list[LogEntry]:
        """Build LogEntry widgets from log data.

        Returns:
            List of LogEntry widgets to display.
        """
        logs = self._get_logs()
        if not logs:
            return [LogEntry("[dim]No logs available[/dim]", "")]

        entries = []
        for entry in logs:
            status, msg = entry[0], entry[1]
            timestamp = entry[2] if len(entry) > 2 else None

            # Format timestamp with date: "Jan 20 14:30:45"
            ts_str = (
                f"[$text-disabled]{timestamp.strftime('%b %d %H:%M:%S')}[/$text-disabled]"
                if timestamp
                else ""
            )

            # Apply message styling
            styled_msg = self._style_message(msg, status)

            entries.append(LogEntry(styled_msg, ts_str))

        return entries

    def _style_message(self, msg: str, status: str) -> str:
        """Apply Rich markup to message based on status.

        Args:
            msg: The raw log message.
            status: The log status/level.

        Returns:
            Message with Rich markup for styling.
        """
        # Info types use bold
        if status in ("info", "status", "key_info"):
            return f"[bold]{msg}[/bold]"

        # Color types
        color_map = {
            "error": "$error",
            "warning": "$warning",
            "success": "$success",
            "debug": "$text-muted",
            "timing": "$accent",
            "approval": "$warning",
            "resume": "$success",
        }
        color = color_map.get(status)
        return f"[{color}]{msg}[/{color}]" if color else msg

    def on_key(self, event: Key) -> None:
        """Handle key events - Space/b to scroll."""
        if event.key == "space":
            content = self.query_one("#log-viewer-content", VerticalScroll)
            content.scroll_page_down(animate=False)
            event.stop()
        elif event.key == "b":
            content = self.query_one("#log-viewer-content", VerticalScroll)
            content.scroll_page_up(animate=False)
            event.stop()

    def action_dismiss_viewer(self) -> None:
        """Dismiss the log viewer."""
        self.dismiss(None)
