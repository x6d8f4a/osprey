"""TUI Constants and Patterns."""

import re

# Pattern to detect router execution step messages
EXEC_STEP_PATTERN = re.compile(r"Executing step (\d+)/(\d+) - capability: (\w+)")

# Components that create Task Preparation blocks (allowlist)
TASK_PREP_COMPONENTS = {"task_extraction", "classifier", "orchestrator"}
