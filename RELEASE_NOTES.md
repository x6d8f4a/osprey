# Osprey Framework - Latest Release (v0.9.5)

🎉 **Pluggable Code Generator System & Python Executor Refactoring** - Modular Architecture for Extensible Code Generation

## What's New in v0.9.5

### 🚀 Major New Features

#### Python Executor Service - Complete Modular Refactoring
- **Modular Subdirectory Structure**: Reorganized python_executor service into focused subdirectories
  - `analysis/` - Code analysis, pattern detection, and policy enforcement
  - `approval/` - Human approval workflows
  - `execution/` - Container management and code execution
  - `generation/` - Pluggable code generator system
  - Each subdirectory has proper `__init__.py` and dedicated README documentation

#### Pluggable Code Generator System
- **Abstract Interface**: `CodeGenerator` protocol defining standard generator contract
- **Generator Factory**: Dynamic registration and instantiation with `GeneratorFactory`
- **Multiple Implementations**:
  * `BasicGenerator` - Simple template-based generation for straightforward tasks
  * `ClaudeCodeGenerator` - Advanced AI-powered generation with:
    - Full conversation history management
    - Result validation and error recovery
    - Streaming support with callbacks
    - Tool use integration
    - Configurable via `execution.code_generator` and `execution.generators` settings
  * `MockGenerator` - Deterministic generator for testing
- **Registry Integration**: Generator lifecycle managed through framework registry system
- **State Model Extensions**: `PythonExecutorState` enhanced to support generator configuration

#### Generator Configuration
- **Explicit, flexible configuration structure**:
  - New `execution.code_generator` setting specifies active generator
  - Generator-specific config in `execution.generators` with model references or inline config
  - Deprecation warnings for old `models.python_code_generator` approach (backward compatible)
  - Updated project templates with examples for all generator types

#### CLI Commands & Templates
- **New `osprey generate claude-config` command** to generate Claude Code generator configuration files with sensible defaults and auto-detection of provider settings
- **Interactive Menu Enhancements**: Added 'generate' command to project selection submenu
- **Template Improvements**:
  - Generator selection and configuration in interactive menu
  - Claude generator config template (`claude_generator_config.yml.j2`)
  - Example plotting scripts for common use cases (time series, multi-subplot, publication-quality)
  - Improved README templates with generator setup instructions

### 🧪 Comprehensive Test Suite

#### E2E Test Coverage
- **Claude Config Generation Tests** (`test_claude_config_generation.py`): Validates `osprey generate claude-config` command, tests configuration file structure, provider auto-detection, and profile customization
- **Code Generator Workflow Tests** (`test_code_generator_workflows.py`): Tests complete code generation pipeline with basic and Claude Code generators. Validates example script guidance following, instruction adherence, and deterministic assertions for generated code content
- **MCP Capability Generation Tests** (`test_mcp_capability_generation.py`): End-to-end MCP integration testing including server generation/launch, capability generation from live MCP server, registry integration, and query execution with LLM judge verification

#### Unit Test Coverage
- Unit tests for all generator implementations (BasicGenerator, ClaudeCodeGenerator, MockGenerator)
- Integration tests for generator-service interaction
- Pattern detection integration tests
- Result validation test suites
- State reducer tests
- Shared test fixtures and utilities in `tests/services/python_executor/`

### 🔧 Infrastructure Improvements

#### API Call Logging
- **Enhanced with caller context tracking** across all LLM-calling components
- Logging metadata now includes capability/module/operation details for better debugging
- Improved JSON serialization with Pydantic model support (mode='json')
- Better error visibility (warnings instead of silent failures)

#### Claude Code Generator Configuration
- **Major simplification**: Profiles now directly specify phases to run instead of using planning_modes abstraction
- Default profile changed from 'balanced' to 'fast'
- Unified prompt building into single data-driven `_build_phase_prompt()` method
- Reduced codebase by 564 lines through elimination of duplicate prompt builders and dead code

#### Registry Display
- Filtered infrastructure nodes table to exclude capability nodes (avoid duplication with Capabilities table)
- Moved context classes to verbose-only mode
- Improved handling of tuple types in provides/requires fields

#### MCP Generator Error Handling
- Added pre-flight connectivity checks using httpx
- Much clearer error messages when server is not running
- Actionable instructions in error messages

### 🐛 Bug Fixes

#### Registry Import Timing
- **Fixed module-level `get_registry()` calls** that could cause initialization order issues
- Moved registry access to runtime (function/method level) in:
  - python capability
  - time_range_parsing capability
  - generate_from_prompt
  - hello_world_weather template

#### Python Executor Logging
- Replaced deprecated `get_streamer` with unified `get_logger` API in code generator node for consistent streaming support

#### MCP Generator Configuration
- Added proper model configuration validation with clear error messages when provider is not configured
- Improved error handling with unused variable cleanup and better logging integration

#### Test Infrastructure
- **Added auto-reset registry fixtures** in both unit and E2E test conftest files to ensure complete test isolation
- Fixtures now reset registry, clear config caches, and clear CONFIG_FILE env var before/after each test to prevent state leakage
- Removed manual registry reset calls from individual tests

#### Time Range Parsing Tests
- Added mock for `store_output_context` to bypass registry validation
- Allows tests to run independently of registry state
- Removed obsolete decorator integration tests that were duplicating coverage

#### Tutorial E2E Tests
- Relaxed over-strict plot count assertion (1+ PNG files instead of 2+) to accommodate both single-figure and multi-figure plotting approaches

#### Claude Code Generator Tests
- Refactored to skip low-level prompt building tests (implementation details now covered by E2E tests)
- Improved test maintainability by focusing on behavior rather than internal methods

### 📚 Documentation

#### E2E Test Documentation
- **Complete rewrite** of `tests/e2e/README.md` with clearer structure, better isolation guidance, and comprehensive examples
- Added warnings about running E2E tests separately from unit tests

#### Generator Documentation
- Updated all Claude Code generator documentation to reflect simplified configuration model
- Restructured `generator-claude.rst` with improved UX using collapsible dropdowns and tabbed sections
- Updated all examples to use 'fast' as default profile
- New comprehensive documentation for all generator types (basic, claude, mock)

### 🗑️ Removed

#### Claude Code Generator
- Removed 'balanced' profile (consolidated to 'fast' and 'robust' only)
- Removed 'workflow_mode' setting (use direct 'phases' list specification)
- Removed 'planning_modes' abstraction (profiles specify phases directly)
- Removed dead code (_generate_direct, _generate_phased, _build_phase_options, 7 duplicate prompt builders)

## Migration Guide

### For Users with Custom Generator Configuration

If you have a custom Claude Code generator configuration:

1. **Update profile references**: If using 'balanced' profile, switch to 'fast' or 'robust'
2. **Update phase configuration**: Replace `workflow_mode` with direct `phases` list in profiles
3. **Review configuration**: Use `osprey generate claude-config` to see new configuration format

### For Developers Extending Code Generation

1. **Use new generator interface**: Implement `CodeGenerator` protocol for custom generators
2. **Register with factory**: Use `GeneratorFactory.register_generator()` for dynamic loading
3. **Update tests**: Use new mock generator for deterministic testing

## Performance & Quality

- **Test Coverage**: 546 unit tests + 9 e2e tests, all passing
- **Code Quality**: Reduced code duplication by 564 lines in generator system
- **API Cost**: E2E test suite runs in ~5 minutes for ~$0.10-$0.25

## Installation

```bash
pip install osprey-framework==0.9.5
```

## What's Next

Stay tuned for upcoming features:
- Enhanced plotting capabilities
- Additional generator implementations
- Expanded control system connector support
- Production deployment guides

---

**Full Changelog**: https://github.com/als-apg/osprey/compare/v0.9.4...v0.9.5
