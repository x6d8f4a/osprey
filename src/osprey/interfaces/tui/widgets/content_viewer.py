"""Content Viewer modal for displaying text content with markdown toggle and tabs."""

from __future__ import annotations

import math

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static


class ContentViewer(ModalScreen[None]):
    """Modal screen for viewing text content with markdown rendering and tab support.

    Supports two rendering modes:
    - Raw: Plain text (default)
    - Markdown: Textual's Markdown widget with code fence wrapping (toggle with 'm')

    Supports tabbed content when given a dict with multiple items.
    """

    BINDINGS = [
        ("escape", "dismiss_viewer", "Close"),
    ]

    AUTO_FOCUS = "#content-viewer-content"

    def __init__(
        self, title: str, content: str | dict[str, str], language: str | None = None
    ):
        """Initialize the content viewer.

        Args:
            title: The title to display (e.g., "Task Extraction - Prompt").
            content: The text content to display (str) or dict of {tab_name: content}.
            language: Optional language for code fence (e.g., "json", "python").
        """
        super().__init__()
        self.viewer_title = title
        self.language = language
        self._markdown_mode = False

        # Handle both str and dict content
        if isinstance(content, str):
            self._content_dict: dict[str, str] = {"": content}
            self._tabs: list[str] = []
            self._is_tabbed = False
        elif len(content) == 1:
            # Single item dict - no tabs needed
            self._content_dict = content
            self._tabs = []
            self._is_tabbed = False
        else:
            # Multiple items - enable tabs (sorted alphabetically for consistency)
            self._content_dict = content
            self._tabs = sorted(content.keys())
            self._is_tabbed = True

        self._current_tab_index = 0
        # For backward compat
        self.content = self._get_current_content()

        # Base height will be calculated in on_mount() when we have screen access
        self._base_height = 0
        # Markdown base height - captured on first markdown render
        self._markdown_base_height: int | None = None

    def _get_current_content(self) -> str:
        """Get content for currently selected tab."""
        if not self._tabs:
            return list(self._content_dict.values())[0] if self._content_dict else ""
        return self._content_dict.get(self._tabs[self._current_tab_index], "")

    def _format_as_markdown(self) -> str:
        """Format content as markdown.

        Returns:
            Markdown string. If language is "markdown", returns content as-is.
            If language is a code language (e.g., "json"), wraps in code fence.
        """
        content = self._get_current_content()
        if not content:
            return "*No content available*"

        if self.language == "markdown":
            # Content is already markdown - render directly
            return content
        elif self.language:
            # Wrap in code fence for JSON/code content
            return f"```{self.language}\n{content}\n```"
        return content

    def _calculate_visual_height(self, content: str) -> int:
        """Calculate visual height accounting for soft-wrap.

        Args:
            content: The text content to measure.

        Returns:
            Estimated visual line count.
        """
        # Get container width (approximate - container padding is 4 on each side)
        try:
            container_width = self.screen.size.width - 16  # Conservative estimate
        except Exception:
            container_width = 80  # Fallback

        if container_width <= 0:
            container_width = 80

        total_lines = 0
        for line in content.split("\n"):
            if len(line) == 0:
                total_lines += 1
            else:
                total_lines += math.ceil(len(line) / container_width)
        return total_lines

    def _get_max_content_height(self) -> int:
        """Get the maximum visual height across all tab contents."""
        max_height = 0
        for content in self._content_dict.values():
            if content:
                height = self._calculate_visual_height(content)
                max_height = max(max_height, height)
        return max_height

    def _compose_footer(self) -> Static:
        """Compose footer with appropriate hints."""
        hints = [
            "[$text bold]␣[/$text bold] to pg down",
            "[$text bold]b[/$text bold] to pg up",
        ]
        if self._is_tabbed:
            hints.append("[$text bold]tab[/$text bold] to switch")
        if self.language:
            hints.append("[$text bold]m[/$text bold] to toggle markdown")
        hints.append("[$text bold]⏎[/$text bold] to close")
        return Static(" · ".join(hints), id="content-viewer-footer")

    def compose(self) -> ComposeResult:
        """Compose the content viewer layout."""
        with Container(id="content-viewer-container"):
            with Horizontal(id="content-viewer-header"):
                yield Static(self.viewer_title, id="content-viewer-title")
                yield Static("", id="header-spacer")
                yield Static("esc", id="content-viewer-dismiss-hint")

            # Tab bar (only if multiple tabs)
            if self._is_tabbed:
                with Horizontal(id="content-viewer-tabs"):
                    for i, tab_name in enumerate(self._tabs):
                        cls = "tab-active" if i == 0 else "tab-inactive"
                        yield Static(
                            tab_name, id=f"tab-{i}", classes=f"content-tab {cls}"
                        )

            with ScrollableContainer(id="content-viewer-content"):
                yield Static(
                    self._get_current_content() or "[dim]No content available[/dim]"
                )

            yield self._compose_footer()

    def on_mount(self) -> None:
        """Set initial height for tabbed content to prevent jumping when switching tabs."""
        if self._is_tabbed:
            container = self.query_one("#content-viewer-content", ScrollableContainer)
            # Calculate base height now that we have screen access
            self._base_height = self._get_max_content_height()
            container.styles.height = self._base_height

    def _refresh_content(self) -> None:
        """Refresh content based on current markdown mode."""
        container = self.query_one("#content-viewer-content", ScrollableContainer)
        for child in list(container.children):
            child.remove()

        if self._markdown_mode:
            container.mount(Markdown(self._format_as_markdown()))
            if self._is_tabbed:
                if self._markdown_base_height is None:
                    # First markdown render (toggle) - just auto size, don't capture yet
                    container.styles.height = "auto"
                else:
                    # Tab switch in markdown mode - use captured height
                    container.styles.height = self._markdown_base_height
        else:
            container.mount(
                Static(
                    self._get_current_content() or "[dim]No content available[/dim]"
                )
            )
            if self._is_tabbed:
                container.styles.height = self._base_height
                # Reset markdown height when leaving markdown mode
                self._markdown_base_height = None

    def _refresh_tab_display(self) -> None:
        """Update tab highlighting and content after tab switch."""
        # If in markdown mode and height not yet captured, capture it before refresh
        if self._markdown_mode and self._is_tabbed and self._markdown_base_height is None:
            container = self.query_one("#content-viewer-content", ScrollableContainer)
            self._markdown_base_height = container.size.height

        for i in range(len(self._tabs)):
            try:
                tab = self.query_one(f"#tab-{i}", Static)
                tab.remove_class("tab-active", "tab-inactive")
                if i == self._current_tab_index:
                    tab.add_class("tab-active")
                else:
                    tab.add_class("tab-inactive")
            except Exception:
                pass
        self.content = self._get_current_content()
        self._refresh_content()

    def on_key(self, event: Key) -> None:
        """Handle key events - Enter to close, Tab to switch, Space/b to scroll."""
        if event.key == "enter":
            self.dismiss(None)
            event.stop()
        elif event.key == "tab" and self._is_tabbed:
            self._current_tab_index = (self._current_tab_index + 1) % len(self._tabs)
            self._refresh_tab_display()
            event.stop()
        elif event.key == "shift+tab" and self._is_tabbed:
            self._current_tab_index = (self._current_tab_index - 1) % len(self._tabs)
            self._refresh_tab_display()
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
