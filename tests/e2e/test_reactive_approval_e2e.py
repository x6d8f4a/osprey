"""E2E test: reactive orchestration with channel_write approval workflow.

Tests the full reactive loop with real LLM calls:
    user query → task extraction → classifier → reactive orchestrator
    → channel_finding (explicit PV fast path) → channel_write (approval interrupt)
    → user approves → write executes on mock connector → respond

Uses the ``control_assistant`` template with ``orchestration_mode=react``.
No mocking — exercises the real framework end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _enable_reactive_mode(config_path: Path):
    """Set orchestration_mode=react in the project config.

    The control_assistant template already ships with:
    - approval.capabilities.python_execution.enabled = true
    - approval.capabilities.python_execution.mode = control_writes
    - control_system.writes_enabled = true

    So the only change needed is switching from plan_first to react.
    """
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config["execution_control"]["agent_control"]["orchestration_mode"] = "react"

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_reactive_channel_write_with_approval(e2e_project_factory):
    """E2E: reactive mode -> channel_finding -> channel_write (approval) -> approve -> respond."""

    # 1. Create control_assistant project
    project = await e2e_project_factory(
        name="reactive-approval-e2e",
        template="control_assistant",
    )

    # 2. Switch to reactive orchestration mode
    _enable_reactive_mode(project.config_path)

    # 3. Initialize (real registry, real graph, real LLM config)
    await project.initialize()

    # 4. First query — should hit approval interrupt
    result1 = await project.query("Set the beam current channel SR:C01-MG:CURRENT to 42.0")
    # Interrupt paused execution; no response yet, but no error either
    graph_state = project.graph.get_state(project.base_config)
    assert graph_state.interrupts, "Expected channel write approval interrupt"

    # 5. Approve — gateway detects interrupt, creates resume command
    result2 = await project.query("yes")
    assert result2.error is None, f"Approval resume failed: {result2.error}"
    assert result2.response, "Expected a response after approval"

    # 6. Verify execution trace shows the reactive flow
    combined_trace = result1.execution_trace + result2.execution_trace
    trace_lower = combined_trace.lower()
    assert "channel_finding" in trace_lower or "channel_find" in trace_lower
    assert "channel_write" in trace_lower
    assert "approval" in trace_lower or "interrupt" in trace_lower
