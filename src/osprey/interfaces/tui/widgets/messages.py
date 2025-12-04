"""Message widgets for the TUI."""

from textual.app import ComposeResult
from textual.widgets import Markdown, Static


class ChatMessage(Static):
    """A single chat message widget styled as a card/block."""

    def __init__(self, content: str, role: str = "user", **kwargs):
        """Initialize a chat message.

        Args:
            content: The message content.
            role: The role (user or assistant).
        """
        super().__init__(**kwargs)
        self.message_content = content
        self.role = role
        self.border_title = role.capitalize()
        self.add_class(f"message-{role}")

    def compose(self) -> ComposeResult:
        """Compose the message with content."""
        yield Markdown(self.message_content, classes="message-content")
