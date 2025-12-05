"""Welcome screen widgets for the TUI."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.content import Content
from textual.style import Style
from textual.widgets import Static

from osprey.interfaces.tui.widgets.input import (
    ChatInput,
    CommandDropdown,
    StatusPanel,
)

# Banner lines for two-tone styling ("os" muted, "prey" normal)
OSPREY_BANNER_LINES = [
    "█▀▀█ █▀▀▀ █▀▀█ █▀▀▀ █▀▀█ █  █",
    "█░░█ ▀▀▀▀ █░░█ █░░░ █▀▀▀ █░░█",
    "▀▀▀▀ ▀▀▀▀ █▀▀▀ ▀    ▀▀▀▀ ▀▀▀█",
]


class WelcomeBanner(Static):
    """Welcome banner with ASCII art and version number."""

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "banner--muted",   # for "os"
        "banner--normal",  # for "prey"
    }

    def __init__(self, version: str = "", **kwargs):
        """Initialize the welcome banner.

        Args:
            version: Version string to display below the banner.
        """
        super().__init__(**kwargs)
        self.version = version

    def compose(self) -> ComposeResult:
        """Compose the banner with art and version."""
        yield Static("", id="banner-art")
        if self.version:
            yield Static(self.version, id="banner-version")

    def on_mount(self) -> None:
        """Build styled banner after mount when CSS is available."""
        muted = Style.from_styles(self.get_component_styles("banner--muted"))
        normal = Style.from_styles(self.get_component_styles("banner--normal"))

        parts = []
        for i, line in enumerate(OSPREY_BANNER_LINES):
            if i > 0:
                parts.append(("\n", normal))
            # First 10 chars = "os", rest = "prey"
            parts.append((line[:10], muted))
            parts.append((line[10:], normal))

        self.query_one("#banner-art", Static).update(Content.assemble(*parts))


class WelcomeScreen(Static):
    """Full welcome screen with banner, input, and tips.

    Displayed on app launch, hidden after first user input.
    """

    def __init__(self, version: str = "", **kwargs):
        """Initialize the welcome screen.

        Args:
            version: Version string to display.
        """
        super().__init__(**kwargs)
        self.version = version

    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout."""
        yield Vertical(
            Center(
                Vertical(
                    WelcomeBanner(version=self.version, id="welcome-banner"),
                    id="banner-container",
                ),
            ),
            Center(
                Vertical(
                    # Dropdown FIRST - with overlay:screen, floats at top of container
                    # Its bottom aligns with input's top (opens upward effect)
                    CommandDropdown(id="welcome-dropdown"),
                    ChatInput(
                        id="welcome-input",
                        placeholder="Ask anything...",
                        dropdown_id="#welcome-dropdown",
                        status_id="#welcome-status",
                    ),
                    StatusPanel(id="welcome-status"),
                    id="input-container",
                ),
            ),
            id="welcome-content",
        )
