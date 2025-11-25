"""Osprey TUI Application.

A Terminal User Interface for the Osprey Agent Framework built with Textual.
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static


class OspreyTUI(App):
    """Osprey Terminal User Interface.

    A TUI for interacting with the Osprey Agent Framework.
    """

    TITLE = "Osprey TUI"
    SUB_TITLE = "AI Agent Framework"

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, config_path: str = "config.yml"):
        """Initialize the TUI.

        Args:
            config_path: Path to the configuration file.
        """
        super().__init__()
        self.config_path = config_path

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Static("Welcome to Osprey TUI!", id="welcome")
        yield Static("Press 'q' or Ctrl+C to quit.", id="instructions")
        yield Footer()


async def run_tui(config_path: str = "config.yml") -> None:
    """Run the Osprey TUI application.

    Args:
        config_path: Path to the configuration file.
    """
    app = OspreyTUI(config_path=config_path)
    await app.run_async()
