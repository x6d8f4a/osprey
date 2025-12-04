"""Debug widget for the TUI."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static


class DebugBlock(Static):
    """Debug block to show streaming events for debugging."""

    def __init__(self, **kwargs):
        """Initialize debug block."""
        super().__init__(**kwargs)
        self.add_class("debug-block")
        self._events: list[str] = []
        self._mounted = False

    def compose(self) -> ComposeResult:
        """Compose the debug block with header and scrollable content."""
        yield Static("Debug Events:", classes="debug-header")
        yield ScrollableContainer(
            Static("", classes="debug-content", id="debug-content"),
            id="debug-scroll",
            classes="debug-scroll",
        )

    def on_mount(self) -> None:
        """Apply pending state after widget is mounted."""
        self._mounted = True
        self._update_display()

    def add_event(self, chunk: dict) -> None:
        """Add an event to the debug display."""
        component = chunk.get("component", "?")
        phase = chunk.get("phase", "?")
        event_type = chunk.get("event_type", "?")
        complete = chunk.get("complete", False)
        msg = chunk.get("message", "")[:40]

        # success event or explicit complete flag = DONE
        is_done = (event_type == "success") or complete
        status = "DONE" if is_done else "START"
        line = f"[{component}] {status} | {phase} | {msg}"
        self._events.append(line)

        if self._mounted:
            self._update_display()

    def _update_display(self) -> None:
        """Update the display with ALL events (scrollable)."""
        content = self.query_one("#debug-content", Static)
        content.update("\n".join(self._events))  # Show ALL events
        # Auto-scroll to bottom
        scroll = self.query_one("#debug-scroll", ScrollableContainer)
        scroll.scroll_end(animate=False)

    def clear(self) -> None:
        """Clear all events."""
        self._events = []
        if self._mounted:
            self._update_display()
