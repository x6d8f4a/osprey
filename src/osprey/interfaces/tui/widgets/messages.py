"""Message widgets for the TUI."""

from textual.app import ComposeResult
from textual.widgets import Markdown, Static


class ChatMessage(Static):
    """A single chat message widget styled as a card/block."""

    def __init__(self, content: str, role: str = "user", message_type: str = "", **kwargs):
        """Initialize a chat message.

        Args:
            content: The message content.
            role: The role (user or assistant).
            message_type: Type of message (instant, agent) for styling.
        """
        super().__init__(**kwargs)
        self.message_content = content
        self.role = role
        self.border_title = role.capitalize()
        self.add_class(f"message-{role}")
        if message_type:
            self.add_class(f"message-type-{message_type}")

    def compose(self) -> ComposeResult:
        """Compose the message with content."""
        yield Markdown(self.message_content, classes="message-content")


class StreamingChatMessage(ChatMessage):
    """A chat message that supports incremental streaming updates.

    This widget displays LLM response tokens as they arrive, providing
    real-time feedback to users during response generation. Uses MarkdownStream
    for efficient buffered token handling (see chat_display.py).
    """

    def __init__(self, role: str = "assistant", **kwargs):
        """Initialize a streaming chat message.

        Args:
            role: The role (typically 'assistant' for streaming responses).
        """
        # Initialize with empty content and 'streaming' message type
        super().__init__("", role, message_type="streaming", **kwargs)
        self._content_buffer: list[str] = []

    def compose(self) -> ComposeResult:
        """Compose the message with an empty Markdown widget for streaming updates."""
        yield Markdown("", classes="message-content")

    def finalize(self) -> None:
        """Mark streaming as complete and update styling.

        Removes the 'streaming' style class and adds the 'agent' class
        for final message appearance.
        """
        self.remove_class("message-type-streaming")
        self.add_class("message-type-agent")
