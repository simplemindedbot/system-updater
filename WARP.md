# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

System Updater is a component-based package manager automation system written in Python. It migrated from a collection of bash scripts to a modular Python architecture with YAML configuration.

## Key Architecture Components

### Core Framework
- **`src/core/base.py`**: Abstract base class `PackageManager` that all package managers must implement
- **`src/core/config.py`**: YAML configuration system with `ConfigManager` and `SystemUpdaterConfig`
- **`src/core/orchestrator.py`**: `SystemUpdater` class that coordinates updates across all managers
- **`src/managers/`**: Individual package manager implementations (currently Homebrew is implemented)
- **`src/cli/main.py`**: Command-line interface using argparse

### Configuration System
- **`config/default.yaml`**: Default configuration template
- **User configs**: `~/.config/system-updater/config.yaml` or `~/.system-updater.yaml`
- **Validation**: Built-in configuration validation with error reporting
- **Manager-specific settings**: Each manager has its own configuration section

### Package Manager Interface
Each manager must implement:
- `is_available()`: Check if the manager is installed
- `check_updates()`: Return list of available updates
- `update_packages()`: Perform actual updates
- `cleanup()`: Clean up old versions/cache (optional)
- `update_self()`: Update the manager itself (optional)

## Common Development Commands

### Running the Application
```bash
# Direct execution
./system-updater --help
./system-updater list
./system-updater status
./system-updater update homebrew --dry-run

# Python module execution (alternative)
python -m src.cli.main status
```

### Testing
```bash
# Run basic functionality tests
./system-updater list                    # Should show available managers
./system-updater status                  # Should check for updates
./system-updater config                  # Should show current config
./system-updater update homebrew --dry-run  # Should show what would be updated
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Validate configuration
./system-updater config --validate

# Initialize user configuration
./system-updater config --init
```

## Project Structure Patterns

### Adding New Package Managers
1. Create new file in `src/managers/` (e.g., `npm.py`)
2. Import `PackageManager` base class: `from core.base import PackageManager, PackageInfo, UpdateResult, UpdateStatus`
3. Implement all abstract methods
4. Add to orchestrator imports in `src/core/orchestrator.py`
5. Add configuration section to `config/default.yaml`
6. Update CLI choices in `src/cli/main.py`

### Configuration Pattern
- All managers get configuration via `config_manager.get_manager_config(manager_name)`
- Global settings (dry_run, exclude_packages) are automatically merged
- Manager-specific settings are defined in the YAML under `managers.{name}`

### Error Handling Pattern
- Use the logging system: `self.log_info()`, `self.log_warning()`, `self.log_error()`
- Return `UpdateResult` objects with appropriate status
- Handle subprocess timeouts and errors gracefully
- Never fail silently - always log what happened

### Import Pattern
All imports use absolute paths from the `src/` directory:
```python
from core.base import PackageManager
from core.config import ConfigManager
from managers.homebrew import HomebrewManager
```

## Legacy Integration

### Original Bash Scripts
The original bash scripts are preserved in `legacy/bash_scripts/`:
- `update-system.sh` - Main update script with comprehensive package manager support
- `check-updates.sh` - Status checking across all package managers  
- `setup-passwordless-sudo.sh` - Sudo configuration for unattended operation
- `com.user.systemupdater.plist` - LaunchAgent for scheduled updates

### Migration Notes
- The bash scripts supported 10 package managers: Homebrew, Mac App Store, npm, Python (pip/uv), Ruby gems, R packages, TeX Live, VS Code extensions, plus package manager self-updates
- Python version currently implements only Homebrew - other managers need to be ported
- The bash scripts had sophisticated sudo handling for unattended 3 AM updates
- Configuration was hardcoded in bash - Python version uses YAML configuration

## Development Priorities

### Immediate Tasks
1. Port remaining package managers from bash scripts to Python
2. Implement sudo handling strategies from the original scripts
3. Add comprehensive test coverage
4. Implement the plugin system for easy extension

### Code Quality Guidelines
- Follow the existing patterns established in `homebrew.py`
- Use type hints throughout
- Comprehensive error handling with logging
- Support dry-run mode in all managers
- Honor exclude_packages configuration
- Implement reasonable timeouts for external commands

### Key Design Principles
- Component-based: Each manager is independent and pluggable
- Configuration-driven: Behavior controlled via YAML files
- User-safe: Dry-run support, comprehensive logging, graceful failures
- Extensible: Plugin system for adding custom managers
- Backward-compatible: Can coexist with or replace the original bash scripts

This project represents a significant architecture upgrade from bash scripts to a maintainable, type-safe Python system while preserving all the functionality of the original comprehensive package management automation.