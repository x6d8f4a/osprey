# Osprey Framework - Latest Release (v0.10.5)

**Bug Fixes & Provider Extensibility**

## What's New in v0.10.5

### Highlights

- **TUI now works from PyPI installs** (#97) - Fixed missing `styles.tcss` in package
- **LiteLLM provider extensibility** - Custom providers can integrate without modifying adapter code
- **Public config API** (#103) - `load_config()` properly exported for channel finder integration
- **Dev mode fix** (#86) - `osprey deploy up --dev` works when installed from PyPI

### Added
- E2E test for LLM channel naming workflow (#103)

### Changed
- Update ALS Assistant reference to published paper (Phys. Rev. Res. **8**, L012017)
- Decouple LiteLLM adapter from hardcoded provider checks
  - Providers now declare LiteLLM routing via class attributes
  - Structured output detection uses LiteLLM's `supports_response_schema()`

### Fixed
- **Packaging**: Include TUI `styles.tcss` in package data (#97)
- **Channel Finder**: Fix `load_config` not defined error (#103)
- **Deployment**: Fix `--dev` mode for non-editable installs (#86)
- **Models**: Handle Python-style booleans in LLM JSON responses (#102)
- **CLI**: Display full absolute paths for plot files (#96)
- **CI**: Fix deploy-e2e test to test PR code with `--dev` mode

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
- TUI mode guide
- Artifact system API reference
- Complete tutorial series

## Contributors

Thank you to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/als-apg/osprey/blob/main/CHANGELOG.md
