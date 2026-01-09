"""TUI Event Handler with Pattern Matching.

This module provides the TUIEventHandler class that processes typed Osprey events
using Python's pattern matching (match/case) for clean event routing.

The handler replaces the previous dict-based event processing in app.py with
a type-safe, maintainable approach using the new osprey.events system.

Usage:
    from osprey.events import parse_event
    from osprey.interfaces.tui.event_handler import TUIEventHandler

    handler = TUIEventHandler(display, shared_data)

    async for chunk in graph.astream(..., stream_mode="custom"):
        event = parse_event(chunk)
        if event:
            await handler.handle(event)
"""

from typing import TYPE_CHECKING, Any

from osprey.events import (
    CapabilityCompleteEvent,
    CapabilityStartEvent,
    ErrorEvent,
    OspreyEvent,
    PhaseCompleteEvent,
    PhaseStartEvent,
    ResultEvent,
    StatusEvent,
    parse_event,
)

if TYPE_CHECKING:
    from osprey.interfaces.tui.widgets.chat_display import ChatDisplay


# Phase name mapping for display
PHASE_DISPLAY_NAMES = {
    "task_extraction": "Task Extraction",
    "classification": "Classification",
    "planning": "Planning",
    "execution": "Execution",
    "response": "Response",
}

# Component to phase mapping
COMPONENT_PHASE_MAP = {
    "task_extraction": "task_extraction",
    "classifier": "classification",
    "orchestrator": "planning",
    "router": "execution",
}


class TUIEventHandler:
    """Handles typed Osprey events for TUI display using pattern matching.

    This handler routes events to appropriate TUI widgets based on event type,
    managing block lifecycle, status updates, and result display.

    Attributes:
        display: The ChatDisplay widget for mounting blocks
        shared_data: Dict for sharing data between blocks (task, capabilities, etc.)
        current_blocks: Dict mapping component names to active blocks
        current_phase: Currently active phase name
    """

    def __init__(self, display: "ChatDisplay", shared_data: dict[str, Any] | None = None):
        """Initialize the TUI event handler.

        Args:
            display: ChatDisplay widget for mounting blocks
            shared_data: Optional dict for cross-block data sharing
        """
        self.display = display
        self.shared_data = shared_data or {}
        self.current_blocks: dict[str, Any] = {}
        self.current_phase: str | None = None
        self._phase_start_times: dict[str, float] = {}

    async def handle(self, event: OspreyEvent) -> None:
        """Process a typed event using pattern matching.

        Routes the event to appropriate handler methods based on event type.

        Args:
            event: The typed OspreyEvent to process
        """
        match event:
            # Phase lifecycle events
            case PhaseStartEvent(phase=phase, description=desc):
                await self._handle_phase_start(phase, desc, event.component)

            case PhaseCompleteEvent(phase=phase, success=success, duration_ms=duration):
                await self._handle_phase_complete(phase, success, duration, event.component)

            # Capability execution events
            case CapabilityStartEvent(
                capability_name=name, step_number=step, total_steps=total, description=desc
            ):
                await self._handle_capability_start(name, step, total, desc)

            case CapabilityCompleteEvent(
                capability_name=name, success=success, duration_ms=duration, error_message=err
            ):
                await self._handle_capability_complete(name, success, duration, err)

            # Status updates (logs)
            case StatusEvent(
                component=component, message=msg, level=level, phase=phase, step=step
            ):
                await self._handle_status(component, msg, level, phase, step)

            # Result events
            case ResultEvent(response=response, success=success):
                await self._handle_result(response, success)

            # Error events
            case ErrorEvent(error_type=err_type, error_message=msg, recoverable=recoverable):
                await self._handle_error(err_type, msg, recoverable)

            case _:
                # Unknown event type - log and skip
                pass

    async def _handle_phase_start(self, phase: str, description: str, component: str) -> None:
        """Handle phase start event - create appropriate block.

        Args:
            phase: Phase identifier (task_extraction, classification, etc.)
            description: Human-readable description
            component: Component that emitted the event
        """
        import time

        from osprey.interfaces.tui.widgets.blocks import (
            ClassificationStep,
            OrchestrationStep,
            TaskExtractionStep,
        )

        self.current_phase = phase
        self._phase_start_times[phase] = time.time()

        display_name = PHASE_DISPLAY_NAMES.get(phase, phase.replace("_", " ").title())

        # Create appropriate block based on phase
        block = None
        match phase:
            case "task_extraction":
                block = TaskExtractionStep()
                block.title = display_name
            case "classification":
                block = ClassificationStep()
                block.title = display_name
                # Initialize with shared task if available
                if "task" in self.shared_data:
                    block._data["task"] = self.shared_data["task"]
            case "planning":
                block = OrchestrationStep()
                block.title = display_name
                # Initialize with shared data
                if "task" in self.shared_data:
                    block._data["task"] = self.shared_data["task"]
                if "capability_names" in self.shared_data:
                    block._data["capability_names"] = self.shared_data["capability_names"]

        if block:
            self.current_blocks[phase] = block
            self.display.mount(block)
            block.set_active()

    async def _handle_phase_complete(
        self, phase: str, success: bool, duration_ms: int, component: str
    ) -> None:
        """Handle phase complete event - finalize block.

        Args:
            phase: Phase that completed
            success: Whether phase completed successfully
            duration_ms: Duration in milliseconds
            component: Component that emitted the event
        """
        block = self.current_blocks.get(phase)
        if block:
            status = "success" if success else "error"
            # Get any accumulated output
            output_text = block._data.get("output", "")
            if not output_text:
                output_text = f"Completed in {duration_ms}ms" if success else "Failed"
            block.set_output(output_text, status=status)

    async def _handle_capability_start(
        self, name: str, step: int, total: int, description: str
    ) -> None:
        """Handle capability start event - create execution block.

        Args:
            name: Capability name
            step: Current step number (1-based)
            total: Total number of steps
            description: Step description
        """
        from osprey.interfaces.tui.widgets.blocks import ExecutionStep, TodoUpdateStep

        # Update plan progress display if we have plan steps
        if hasattr(self.display, "_plan_steps") and self.display._plan_steps:
            # Update step states
            if not hasattr(self.display, "_plan_step_states"):
                self.display._plan_step_states = ["pending"] * len(self.display._plan_steps)

            # Mark previous steps as done, current as active
            for i in range(step - 1):
                if i < len(self.display._plan_step_states):
                    self.display._plan_step_states[i] = "done"
            if step - 1 < len(self.display._plan_step_states):
                self.display._plan_step_states[step - 1] = "current"

            # Create TodoUpdateStep to show progress
            update_step = TodoUpdateStep()
            self.display.mount(update_step)
            update_step.set_todos(self.display._plan_steps, self.display._plan_step_states)

        # Create ExecutionStep block
        block = ExecutionStep(capability=name)
        block_key = f"execution_{name}_{step}"
        self.current_blocks[block_key] = block
        self.display.mount(block)
        block.set_active()

    async def _handle_capability_complete(
        self, name: str, success: bool, duration_ms: int, error_message: str | None
    ) -> None:
        """Handle capability complete event - finalize execution block.

        Args:
            name: Capability that completed
            success: Whether execution was successful
            duration_ms: Duration in milliseconds
            error_message: Error message if failed
        """
        # Find the most recent execution block for this capability
        block = None
        for key, b in reversed(list(self.current_blocks.items())):
            if key.startswith(f"execution_{name}_"):
                block = b
                break

        if block:
            status = "success" if success else "error"
            if success:
                output_text = f"Completed in {duration_ms}ms"
            else:
                output_text = error_message or "Execution failed"
            block.set_output(output_text, status=status)

    async def _handle_status(
        self, component: str, message: str, level: str, phase: str | None, step: int | None
    ) -> None:
        """Handle status event - add log to current block.

        Args:
            component: Component that emitted the status
            message: Status message
            level: Log level (info, warning, error, success, etc.)
            phase: Current phase (if available)
            step: Current step number (if available)
        """
        # Determine which block to update
        block = None

        # First try to find by component/phase mapping
        mapped_phase = COMPONENT_PHASE_MAP.get(component)
        if mapped_phase and mapped_phase in self.current_blocks:
            block = self.current_blocks[mapped_phase]

        # Fall back to current phase block
        if not block and self.current_phase:
            block = self.current_blocks.get(self.current_phase)

        # Fall back to any execution block for the component
        if not block:
            for key, b in self.current_blocks.items():
                if component in key:
                    block = b
                    break

        if block and hasattr(block, "add_log"):
            # Map level to status
            status_map = {
                "error": "error",
                "warning": "warning",
                "success": "success",
                "status": "status",
                "info": None,
                "debug": None,
            }
            status = status_map.get(level)
            block.add_log(message, status=status)

            # Update partial output for real-time display
            if hasattr(block, "set_partial_output"):
                block.set_partial_output(message, status=status)

    async def _handle_result(self, response: str, success: bool) -> None:
        """Handle result event - display final response.

        Args:
            response: Final response text
            success: Whether execution was successful
        """
        # This will be handled by the main app to display as assistant message
        pass

    async def _handle_error(
        self, error_type: str, error_message: str, recoverable: bool
    ) -> None:
        """Handle error event - display error in current block.

        Args:
            error_type: Type of error
            error_message: Error message
            recoverable: Whether error is recoverable
        """
        # Find current active block and add error
        for block in reversed(list(self.current_blocks.values())):
            if hasattr(block, "_status") and block._status == "active":
                if hasattr(block, "add_log"):
                    block.add_log(f"{error_type}: {error_message}", status="error")
                if hasattr(block, "set_output"):
                    block.set_output(error_message, status="error")
                break

    def handle_legacy_event(self, chunk: dict[str, Any]) -> OspreyEvent | None:
        """Convert legacy dict event to typed event if possible.

        For backward compatibility during migration, this method attempts
        to reconstruct typed events from legacy dict-based events.

        Args:
            chunk: Legacy event dict

        Returns:
            Typed OspreyEvent if conversion successful, None otherwise
        """
        return parse_event(chunk)

    def extract_shared_data(self, event: OspreyEvent) -> None:
        """Extract data from events for cross-block sharing.

        Args:
            event: Event to extract data from
        """
        match event:
            case StatusEvent(component="task_extraction"):
                # Task extraction might have task data in extra fields
                pass
            case StatusEvent(component="classifier"):
                # Classification might have capability names
                pass
            case _:
                pass
