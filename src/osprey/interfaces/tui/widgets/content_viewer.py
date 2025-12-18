"""Content Viewer modal for displaying text content with markdown toggle."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static


class ContentViewer(ModalScreen[None]):
    """Modal screen for viewing text content with markdown rendering option.

    Supports two rendering modes:
    - Raw: Plain text (default)
    - Markdown: Textual's Markdown widget with code fence wrapping (toggle with 'm')
    """

    BINDINGS = [
        ("escape", "dismiss_viewer", "Close"),
    ]

    AUTO_FOCUS = "#content-viewer-content"

    def __init__(self, title: str, content: str, language: str | None = None):
        """Initialize the content viewer.

        Args:
            title: The title to display (e.g., "Task Extraction - Prompt").
            content: The text content to display.
            language: Optional language for code fence (e.g., "json", "python").
        """
        super().__init__()
        self.viewer_title = title
        self.content = content
        self.language = language
        self._markdown_mode = False

    def _format_as_markdown(self) -> str:
        """Format content as markdown.

        Returns:
            Markdown string. If language is "markdown", returns content as-is.
            If language is a code language (e.g., "json"), wraps in code fence.
        """
        if not self.content:
            return "*No content available*"

        if self.language == "markdown":
            # Content is already markdown - render directly
            return self.content
        elif self.language:
            # Wrap in code fence for JSON/code content
            return f"```{self.language}\n{self.content}\n```"
        return self.content

    def compose(self) -> ComposeResult:
        """Compose the content viewer layout."""
        with Container(id="content-viewer-container"):
            with Horizontal(id="content-viewer-header"):
                yield Static(self.viewer_title, id="content-viewer-title")
                yield Static("", id="header-spacer")
                yield Static("esc", id="content-viewer-dismiss-hint")
            with ScrollableContainer(id="content-viewer-content"):
                yield Static(self.content or "[dim]No content available[/dim]")
            # Show "m" command only if language is set (can toggle markdown)
            if self.language:
                yield Static(
                    "[$text bold]␣[/$text bold] to pg down · "
                    "[$text bold]b[/$text bold] to pg up · "
                    "[$text bold]m[/$text bold] to toggle markdown · "
                    "[$text bold]⏎[/$text bold] to close",
                    id="content-viewer-footer",
                )
            else:
                yield Static(
                    "[$text bold]␣[/$text bold] to pg down · "
                    "[$text bold]b[/$text bold] to pg up · "
                    "[$text bold]⏎[/$text bold] to close",
                    id="content-viewer-footer",
                )

    def _refresh_content(self) -> None:
        """Refresh content based on current markdown mode."""
        container = self.query_one("#content-viewer-content", ScrollableContainer)
        for child in list(container.children):
            child.remove()
        if self._markdown_mode:
            container.mount(Markdown(self._format_as_markdown()))
        else:
            container.mount(
                Static(self.content or "[dim]No content available[/dim]")
            )

    def on_key(self, event: Key) -> None:
        """Handle key events - Enter to close, Space/b to scroll, m to toggle."""
        if event.key == "enter":
            self.dismiss(None)
            event.stop()
        elif event.key == "space":
            container = self.query_one("#content-viewer-content", ScrollableContainer)
            container.scroll_page_down(animate=False)
            event.stop()
        elif event.key == "b":
            container = self.query_one("#content-viewer-content", ScrollableContainer)
            container.scroll_page_up(animate=False)
            event.stop()
        elif event.key == "m" and self.language:
            self._markdown_mode = not self._markdown_mode
            self._refresh_content()
            event.stop()

    def action_dismiss_viewer(self) -> None:
        """Dismiss the content viewer."""
        self.dismiss(None)
