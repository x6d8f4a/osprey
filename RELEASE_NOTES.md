# Osprey Framework - Latest Release (v0.10.7)

**Migration & Simulation**

## What's New in v0.10.7

### Highlights

- **Project migration system** - New `osprey migrate` command for upgrading projects between OSPREY versions with AI-assisted merge guidance
- **Soft IOC generation** - Generate caproto-based EPICS soft IOCs from channel databases for offline development
- **AskSage provider** (#122) - New LLM provider for AskSage API access
- **Local simulation preset** - Easy setup for connecting to local soft IOCs

### Added
- **CLI**: Add `osprey migrate` command for project version migration
  - `migrate init` creates manifest for existing projects (retroactive)
  - `migrate check` compares project version against installed OSPREY
  - `migrate run` performs three-way diff analysis and generates merge guidance
  - Classifies files as AUTO_COPY, PRESERVE, MERGE, NEW, or DATA
- **Templates**: Add manifest generation during `osprey init`
  - `.osprey-manifest.json` records OSPREY version, template, registry style
  - Includes SHA256 checksums for all trackable project files
- **CLI**: Add `osprey generate soft-ioc` command for generating Python soft IOCs
  - Generates caproto-based EPICS soft IOCs from channel databases
  - Supports all 4 channel database types
  - Two simulation backends: `passthrough` and `mock_style`
- **Models**: Add AskSage provider for LLM access (#122)
- **Config**: Add "Local Simulation" preset to EPICS gateway configuration

### Fixed
- **Dependencies**: Pin `claude-agent-sdk>=0.1.26` to fix CBORG proxy beta header incompatibility
- **Security**: Bind docker/podman services to localhost by default (#126)
- **Connectors**: Fix `EPICSArchiverConnector` timestamp handling
- **Connectors**: Fix EPICS connector PV cache to prevent soft IOC crashes
- **Execution**: Fix channel limits database path resolution in subprocess execution
- **Config**: Fix control system type update regex to handle comment lines

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
- Project migration guide
- Soft IOC generation tutorial
- Complete tutorial series

## Contributors

Thank you to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/als-apg/osprey/blob/main/CHANGELOG.md
