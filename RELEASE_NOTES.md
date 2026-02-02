# Osprey Framework - Latest Release (v0.10.8)

**Pluggable Simulation Backends**

## What's New in v0.10.8

### Highlights

- **Pluggable simulation backends for soft IOCs** - Runtime backend loading from config.yml, chainable backends, and SimulationBackend protocol for custom physics
- **Improved release workflow skill** - Full step-by-step guidance with CHANGELOG sanitization

### Added
- **Skills**: Improve release workflow skill with full step-by-step guidance and CHANGELOG sanitization
- **Generators**: Add pluggable simulation backends for soft IOCs
  - Runtime backend loading from `config.yml` - change behavior without regenerating IOC code
  - Built-in backends: `passthrough` (no-op) and `mock_style` (archiver-like behavior)
  - `ChainedBackend` for composing multiple backends (base + overrides)
  - `SimulationBackend` protocol for custom physics implementations
  - Documentation guide for custom backend development

### Fixed
- **Templates**: Fix `pyproject.toml` template using wrong package search path
- **Generators**: Fix `config_updater` functions returning wrong type
- **Channel Finder**: Fix string ChannelNames causing character-by-character iteration
- **Skills**: Fix release workflow skill name to follow `osprey-` naming convention

---

## Installation

```bash
pip install --upgrade osprey-framework
```

Or install with all optional dependencies:

```bash
pip install --upgrade "osprey-framework[all]"
```

---

## What's Next?

Check out our [documentation](https://als-apg.github.io/osprey) for:
- Soft IOC simulation backend guide
- Complete tutorial series

## Contributors

Thank you to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/als-apg/osprey/blob/main/CHANGELOG.md
