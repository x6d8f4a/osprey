# Osprey Framework - Latest Release (v0.10.0)

🎉 **Terminal User Interface & AI Assistant Tasks** - Full-screen TUI experience and new developer tooling

## What's New in v0.10.0

### 🖥️ Terminal User Interface (TUI)

A brand new full-screen terminal interface for interacting with your Osprey agents!

- **Launch with**: `osprey chat --tui` (or select "chat (tui)" from interactive menu)
- **Real-time Streaming**: Watch agent responses appear character-by-character
- **Step Visualization**: See Task Extraction → Classification → Orchestration → Execution in real-time
- **15+ Built-in Themes**: Switch themes instantly with Ctrl+T
- **Command Palette**: Quick access to all actions with Ctrl+P
- **Slash Commands**: `/exit`, `/caps:on`, `/caps:off`, and more
- **Query History**: Navigate previous queries with up/down arrows
- **Content Viewer**: Multi-tab view for prompts and responses with markdown rendering
- **Todo Visualization**: See agent planning progress as it happens

**Install TUI support**: `pip install osprey-framework[tui]`

### 🤖 AI Assistant Integration (Assist System)

New commands for working with AI coding assistants like Claude Code:

#### `osprey tasks` - Browse AI Assistant Tasks
- `osprey tasks` - Interactive task browser
- `osprey tasks list` - List all available tasks
- `osprey tasks show <task>` - Print task instructions
- `osprey tasks copy <task>` - Copy task to project's `.ai-tasks/`

#### `osprey claude` - Claude Code Skill Management
- `osprey claude install <task>` - Install a task as a Claude Code skill
- `osprey claude list` - List installed and available skills

#### Available Tasks
- **pre-commit** - Validate code before commits
- **migrate** - Upgrade downstream OSPREY projects
- **release-workflow** - Guide through releases
- **testing-workflow** - Smart test selection
- **commit-organization** - Create atomic commits
- And more!

### 🔧 Code Generation Enhancements

- **Environment Variables**: `claude_code_generator` now supports custom env vars in config
- **ARGO Support**: Added ARGO endpoint configuration to generator template

### 📋 Changed

- **CLI**: `osprey workflows` deprecated → use `osprey tasks` instead
- **Logging**: Enhanced logging system embeds streaming data for TUI consumption

---

## Installation

```bash
pip install --upgrade osprey-framework
```

Or install with all optional dependencies:

```bash
pip install --upgrade "osprey-framework[all]"
```

## Upgrading from v0.9.9

### Prompt Structure Migration

If you've customized channel finder prompts:

1. **Check your `system.py` files** - They now auto-combine modules
2. **Move facility content** to `facility_description.py`
3. **Move matching rules** to `matching_rules.py` (optional)

The new structure makes future upgrades easier - framework updates won't overwrite your customizations.

### Query Splitting

If you have facility-specific terms being incorrectly split:

```python
# In your pipeline configuration
pipeline = HierarchicalPipeline(
    query_splitting=False  # Disable splitting for your facility
)
```

---

## What's Next?

Check out our [documentation](https://als-apg.github.io/osprey) for:
- Channel Finder prompt customization guide
- AI-assisted development workflows
- Complete tutorial series

## Contributors

Thank you to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/als-apg/osprey/blob/main/CHANGELOG.md
