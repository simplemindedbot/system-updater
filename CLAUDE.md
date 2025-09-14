# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

System Updater is a Python-based modular package manager orchestration system that migrated from bash scripts. It automates updates across multiple package ecosystems on macOS.

## Common Development Commands

### Running the Application
```bash
# Main CLI execution
./system-updater --help                    # Show help
./system-updater list                      # List available managers
./system-updater status                    # Check for updates across all managers
./system-updater update homebrew           # Update specific manager
./system-updater update all                # Update all enabled managers
./system-updater update homebrew --dry-run # Dry run mode

# Alternative Python module execution
python -m src.cli.main status
python -m src.cli.main update homebrew
```

### Configuration Management
```bash
./system-updater config                    # Show current configuration
./system-updater config --init             # Initialize user config file
./system-updater config --validate         # Validate configuration
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Testing (when implemented)
```bash
pytest tests/                               # Run all tests
pytest tests/ -v                           # Verbose test output
pytest tests/ --cov=src                    # With coverage report
```

## Architecture Overview

### Core Components
- **`src/core/base.py`**: Defines `PackageManager` abstract base class that all managers must implement
- **`src/core/config.py`**: YAML configuration system with validation
- **`src/core/orchestrator.py`**: `SystemUpdater` class that coordinates across all managers
- **`src/cli/main.py`**: CLI interface using argparse

### Package Manager Implementation Pattern
Each manager must implement these methods from `PackageManager`:
- `is_available()`: Check if the manager is installed
- `check_updates()`: Return list of available updates
- `update_packages()`: Perform actual updates
- `cleanup()`: Clean up old versions (optional)
- `update_self()`: Update the manager itself (optional)

### Configuration Hierarchy
1. `config/default.yaml` - Default configuration template
2. `~/.config/system-updater/config.yaml` - User configuration (priority)
3. `~/.system-updater.yaml` - Alternative user configuration location

### Import Pattern
All imports use absolute paths from `src/`:
```python
from core.base import PackageManager, PackageInfo, UpdateResult, UpdateStatus
from core.config import ConfigManager
from managers.homebrew import HomebrewManager
```

## Adding New Package Managers

To implement a new package manager (npm, python, ruby, etc.):

1. Create new file in `src/managers/{name}.py`
2. Import and implement the `PackageManager` base class
3. Add to imports in `src/core/orchestrator.py:17` and initialization in `_initialize_managers()`
4. Update CLI choices in `src/cli/main.py:251`
5. Add configuration section to `config/default.yaml`

Reference `src/managers/homebrew.py` for implementation patterns.

## Currently Implemented vs Planned

**Implemented:**
- Homebrew (formulae and casks)

**To Be Ported from Legacy Bash Scripts:**
- Mac App Store (via `mas`)
- npm global packages
- Python (pip user packages, uv tools)
- Ruby gems
- R packages (CRAN/Bioconductor)
- TeX Live (via `tlmgr`)
- VS Code extensions

## Key Design Principles

- **Component-based**: Each manager is independent and pluggable
- **Dry-run support**: All managers must support `--dry-run` mode
- **Comprehensive logging**: Use `self.log_info()`, `self.log_warning()`, `self.log_error()`
- **Error handling**: Return `UpdateResult` objects with appropriate status
- **Configuration-driven**: Honor exclude_packages and manager-specific settings
- **Subprocess timeouts**: Set reasonable timeouts for external commands