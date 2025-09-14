# System Updater

A component-based package manager automation system for macOS that keeps your development environment up to date across multiple package ecosystems.

## Features

- **Multi-package manager support**: Homebrew, Mac App Store, npm, Python (pip/uv), Ruby gems, R packages, TeX Live, VS Code extensions
- **YAML Configuration**: Flexible configuration system with user overrides
- **Component-based Architecture**: Modular design with plugin system for easy extension
- **Intelligent sudo handling**: Multiple strategies for unattended operation
- **Dry-run support**: Preview updates before applying them
- **Comprehensive logging**: Full audit trail of all operations
- **CLI interface**: Simple command-line interface for all operations

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/system-updater.git
cd system-updater

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m src.cli.main config --init
```

### Basic Usage

```bash
# Check what updates are available
python -m src.cli.main status

# Update all package managers
python -m src.cli.main update all

# Update only Homebrew packages
python -m src.cli.main update homebrew

# Dry run to see what would be updated
python -m src.cli.main update all --dry-run
```

## Configuration

The system uses YAML configuration files with sensible defaults. Configuration locations (in order of precedence):

1. `~/.config/system-updater/config.yaml`
2. `~/.system-updater.yaml` 
3. `config/default.yaml` (in project directory)

### Example Configuration

```yaml
# Global settings
log_level: INFO
dry_run: false
sudo_mode: prompt

# Package manager settings
managers:
  homebrew:
    enabled: true
    update_formulae: true
    update_casks: true
    cleanup: true
    exclude_packages: []
    
  python:
    enabled: true
    pip_user_only: true
    use_uv: true
    exclude_packages: []

# Global exclusions
exclude_packages: []
```

## Supported Package Managers

- **Homebrew**: Command-line tools (formulae) and GUI applications (casks)
- **Mac App Store**: Applications from Apple's app store via `mas`
- **npm**: Node.js global packages
- **Python**: pip user packages and uv tools
- **Ruby**: Gems with user installation
- **R**: CRAN and Bioconductor packages
- **TeX Live**: LaTeX packages via tlmgr
- **VS Code**: Editor extensions

## Architecture

The system is built with a component-based architecture:

- **Core**: Base classes and configuration management
- **Managers**: Individual package manager implementations
- **CLI**: Command-line interface
- **Utils**: Shared utilities and helpers

Each package manager implements the `PackageManager` abstract base class, making it easy to add new managers.

## Migration from Bash Scripts

This project evolved from a set of bash scripts. The legacy scripts are preserved in `legacy/bash_scripts/` for reference.

Key improvements in the Python version:
- Type safety and better error handling
- Structured configuration instead of hardcoded values
- Modular architecture for easy extension
- Better logging and status reporting
- Dry-run capabilities
- Plugin system for custom managers

## Development

### Adding a New Package Manager

1. Create a new file in `src/managers/`
2. Implement the `PackageManager` abstract base class
3. Add the manager to the orchestrator
4. Update the CLI choices
5. Add configuration options to the default YAML

See `src/managers/homebrew.py` for a complete example.

### Running Tests

```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Legacy Scripts

The original bash scripts that inspired this project are preserved in `legacy/bash_scripts/` and include:

- `update-system.sh` - Main update orchestrator
- `check-updates.sh` - Status checking
- `setup-passwordless-sudo.sh` - Sudo configuration
- `com.user.systemupdater.plist` - LaunchAgent configuration

These scripts are still functional but the Python version provides better structure and extensibility.