"""CLI Event Handler with Pattern Matching.

This module provides the CLIEventHandler class that processes typed Osprey
events using Python's pattern matching (match/case) for clean console output.

The handler provides focused output for CLI usage - showing status messages,
success confirmations, warnings, errors, and final results. Component colors
are loaded from the logging.logging_colors config for visual consistency.

Output format follows Python logging style: [component] message

Usage:
    from osprey.events import parse_event
    from osprey.interfaces.cli.event_handler import CLIEventHandler

    handler = CLIEventHandler(console)

    async for chunk in graph.astream(..., stream_mode="custom"):
        event = parse_event(chunk)
        if event:
            await handler.handle(event)
"""

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text

from osprey.cli.styles import Styles
from osprey.events import (
    ErrorEvent,
    LLMRequestEvent,
    LLMResponseEvent,
    OspreyEvent,
    ResultEvent,
    StatusEvent,
)
from osprey.utils.config import get_config_value


class CLIEventHandler:
    """Handles typed Osprey events for CLI output using pattern matching.

    This handler provides focused console output suitable for CLI usage.
    It shows status updates, success confirmations, warnings, errors,
    and final results with component-specific colors from config.

    Attributes:
        console: Rich Console for output
        verbose: Whether to show debug-level messages
    """

    ROLE_COLUMN_WIDTH = 18  # Fixed width for role column alignment

    def __init__(
        self,
        console: Console | None = None,
        verbose: bool = False,
        show_timing: bool = True,
    ):
        """Initialize the CLI event handler.

        Args:
            console: Rich Console for output (creates new one if not provided)
            verbose: Whether to show debug-level status messages
            show_timing: Kept for API compatibility (not used currently)
        """
        self.console = console or Console()
        self.verbose = verbose
        self.show_timing = show_timing
        self._color_cache: dict[str, str] = {}
        self._highlighter = ReprHighlighter()  # For data type highlighting

    def _format_component_name(self, component: str) -> str:
        """Format component name to title case.

        Examples:
            "REGISTRY" -> "Registry"
            "task_extraction" -> "Task_Extraction"
            "current_weather" -> "Current_Weather"

        Args:
            component: Raw component name

        Returns:
            Title case formatted name
        """
        parts = component.split("_")
        return "_".join(part.capitalize() for part in parts)

    def _format_role_prefix(self, component: str) -> str:
        """Format role prefix with fixed width for alignment.

        Creates a fixed-width prefix like "[Orchestrator]    " that ensures
        all messages align properly. Long names are truncated with "...".

        Args:
            component: Component name to format

        Returns:
            Fixed-width prefix string
        """
        name = self._format_component_name(component)
        prefix = f"[{name}]"

        # Truncate long names with "..." to ensure at least 1 space after ljust
        # Formula: "[" (1) + truncated_name + "...]" (4) <= ROLE_COLUMN_WIDTH - 1
        max_prefix_len = self.ROLE_COLUMN_WIDTH - 1  # 17 chars max for prefix
        if len(prefix) > max_prefix_len:
            # Truncate name: total = 1 + name_len + 4, so name_len = max - 5
            truncated_name = name[: max_prefix_len - 5]
            prefix = f"[{truncated_name}...]"

        return prefix.ljust(self.ROLE_COLUMN_WIDTH)

    def _get_component_color(self, component: str) -> str:
        """Get component color from config with caching.

        Looks up the color from logging.logging_colors.{component} config.
        Falls back to 'white' if not found or on error.

        Args:
            component: Component name (e.g., 'classifier', 'orchestrator')

        Returns:
            Rich color name (e.g., 'cyan', 'light_salmon1')
        """
        if component not in self._color_cache:
            try:
                color = get_config_value(f"logging.logging_colors.{component}")
                self._color_cache[component] = color or "white"
            except Exception:
                self._color_cache[component] = "white"
        return self._color_cache[component]

    def _format_message(self, prefix: str, msg: str, style: str) -> Text:
        """Format message with component color and data type highlighting.

        Creates a Rich Text object with the component style applied to the entire
        message, then applies ReprHighlighter to add data type highlighting on top.
        Rich renders overlapping spans, with data type colors taking visual precedence.

        Args:
            prefix: Component prefix like "[comp] " or "✓ [comp] "
            msg: The message content
            style: Rich style string for the component color

        Returns:
            Rich Text object with both component style and data type highlighting
        """
        text = Text(f"{prefix}{msg}")
        text.stylize(style)
        self._highlighter.highlight(text)
        return text

    async def handle(self, event: OspreyEvent) -> None:
        """Process a typed event using pattern matching.

        Routes the event to appropriate output based on event type and level.
        StatusEvents are filtered by level (status, info, success, warning,
        error shown; debug only in verbose mode; timing/approval/resume hidden).

        Args:
            event: The typed OspreyEvent to process
        """
        match event:
            # StatusEvent - status level (most common - high-level progress)
            case StatusEvent(message=msg, level="status", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # StatusEvent - key_info level (important info with bold styling)
            case StatusEvent(message=msg, level="key_info", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, f"bold {color}")
                self.console.print(text)

            # StatusEvent - info level (operational info)
            case StatusEvent(message=msg, level="info", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # StatusEvent - success level (completion confirmations)
            case StatusEvent(message=msg, level="success", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"✓ {prefix}", msg, "bold green")
                self.console.print(text)

            # StatusEvent - warning level (warnings)
            case StatusEvent(message=msg, level="warning", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"⚠ {prefix}", msg, "yellow")
                self.console.print(text)

            # StatusEvent - error level (errors)
            case StatusEvent(message=msg, level="error", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"✗ {prefix}", msg, "red")
                self.console.print(text)

            # StatusEvent - debug level (only in verbose mode)
            case StatusEvent(
                message=msg, level="debug", component=comp
            ) if self.verbose:
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"🔍 {prefix}", msg, f"dim {color}")
                self.console.print(text)

            # LLMRequestEvent - "LLM prompt built"
            case LLMRequestEvent(component=comp, prompt_length=length):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                msg = f"LLM prompt built ({length} chars)"
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # LLMResponseEvent - "LLM response received"
            case LLMResponseEvent(
                component=comp, response_length=length, duration_ms=dur
            ):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                dur_sec = dur / 1000 if dur else 0
                msg = f"LLM response received ({length} chars, {dur_sec:.2f}s)"
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # ResultEvent - final response (success)
            case ResultEvent(response=response, success=True):
                self.console.print(f"\n{response}", style=Styles.BOLD_SUCCESS)

            # ResultEvent - final response (failure)
            case ResultEvent(response=response, success=False):
                self.console.print(
                    f"\nExecution failed: {response}",
                    style=Styles.BOLD_ERROR,
                )

            # ErrorEvent - execution errors
            case ErrorEvent(
                error_type=err_type, error_message=msg, component=comp
            ):
                prefix = self._format_role_prefix(comp)
                self.console.print(f"[error]✗ {prefix}{err_type}[/error]")
                indent = " " * (self.ROLE_COLUMN_WIDTH + 2)
                self.console.print(f"[error]{indent}{msg}[/error]")

            case _:
                # All other events silently ignored (timing, approval, resume,
                # PhaseStart/Complete, CapabilityStart/Complete, etc.)
                pass

    def handle_sync(self, event: OspreyEvent) -> None:
        """Synchronous version of handle for non-async contexts.

        Args:
            event: The typed OspreyEvent to process
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._handle_sync_impl(event)
            else:
                loop.run_until_complete(self.handle(event))
        except RuntimeError:
            self._handle_sync_impl(event)

    def _handle_sync_impl(self, event: OspreyEvent) -> None:
        """Direct synchronous implementation of event handling.

        Args:
            event: The typed OspreyEvent to process
        """
        match event:
            # StatusEvent - status level
            case StatusEvent(message=msg, level="status", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # StatusEvent - key_info level (important info with bold styling)
            case StatusEvent(message=msg, level="key_info", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, f"bold {color}")
                self.console.print(text)

            # StatusEvent - info level
            case StatusEvent(message=msg, level="info", component=comp):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # StatusEvent - success level
            case StatusEvent(message=msg, level="success", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"✓ {prefix}", msg, "bold green")
                self.console.print(text)

            # StatusEvent - warning level
            case StatusEvent(message=msg, level="warning", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"⚠ {prefix}", msg, "yellow")
                self.console.print(text)

            # StatusEvent - error level
            case StatusEvent(message=msg, level="error", component=comp):
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"✗ {prefix}", msg, "red")
                self.console.print(text)

            # StatusEvent - debug level (verbose only)
            case StatusEvent(
                message=msg, level="debug", component=comp
            ) if self.verbose:
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                text = self._format_message(f"🔍 {prefix}", msg, f"dim {color}")
                self.console.print(text)

            # LLMRequestEvent - "LLM prompt built"
            case LLMRequestEvent(component=comp, prompt_length=length):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                msg = f"LLM prompt built ({length} chars)"
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # LLMResponseEvent - "LLM response received"
            case LLMResponseEvent(
                component=comp, response_length=length, duration_ms=dur
            ):
                color = self._get_component_color(comp)
                prefix = self._format_role_prefix(comp)
                dur_sec = dur / 1000 if dur else 0
                msg = f"LLM response received ({length} chars, {dur_sec:.2f}s)"
                text = self._format_message(prefix, msg, color)
                self.console.print(text)

            # ResultEvent - success
            case ResultEvent(response=response, success=True):
                self.console.print(f"\n{response}", style=Styles.BOLD_SUCCESS)

            # ResultEvent - failure
            case ResultEvent(response=response, success=False):
                self.console.print(
                    f"\nExecution failed: {response}",
                    style=Styles.BOLD_ERROR,
                )

            # ErrorEvent
            case ErrorEvent(
                error_type=err_type, error_message=msg, component=comp
            ):
                prefix = self._format_role_prefix(comp)
                self.console.print(f"[error]✗ {prefix}{err_type}[/error]")
                indent = " " * (self.ROLE_COLUMN_WIDTH + 2)
                self.console.print(f"[error]{indent}{msg}[/error]")

            case _:
                pass
