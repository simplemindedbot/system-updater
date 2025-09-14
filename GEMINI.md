# Project Overview

This project is a system updater for macOS, designed to automate the process of keeping various package managers and their packages up to date. It is a command-line tool written in Python, featuring a modular, component-based architecture that allows for easy extension to support new package managers.

The core of the system is an orchestrator that iterates through enabled package manager components, checks for updates, and applies them. Each package manager is implemented as a class that inherits from a `PackageManager` base class, ensuring a consistent interface for operations like checking for updates, installing packages, and cleaning up old versions.

The system is configured through YAML files, with a default configuration provided and the ability for users to override settings with their own `config.yaml`.

## Building and Running

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/system-updater.git
    cd system-updater
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize configuration:**
    ```bash
    python -m src.cli.main config --init
    ```

### Running the application

*   **Check for available updates:**
    ```bash
    python -m src.cli.main status
    ```

*   **Update all enabled package managers:**
    ```bash
    python -m src.cli.main update all
    ```

*   **Update a specific package manager (e.g., Homebrew):**
    ```bash
    python -m src.cli.main update homebrew
    ```

*   **Perform a dry run to see what would be updated:**
    ```bash
    python -m src.cli.main update all --dry-run
    ```

### Testing

*   **Run the test suite:**
    ```bash
    pytest tests/
    ```

## Development Conventions

*   **Modular Architecture:** The project is structured into `core`, `managers`, `cli`, and `utils` components. New package managers should be added in the `src/managers/` directory.
*   **Base Classes:** New package managers must inherit from the `PackageManager` abstract base class located in `src/core/base.py`.
*   **Configuration:** Configuration is handled by the `ConfigManager` class in `src/core/config.py`. Default configuration is in `config/default.yaml`.
*   **Command-Line Interface:** The CLI is built using Python's `argparse` library and is defined in `src/cli/main.py`.
*   **Dependencies:** Project dependencies are managed in `requirements.txt`.
*   **Coding Style:** The code follows standard Python conventions (PEP 8). Type hinting is used throughout the codebase.
*   **Error Handling:** The application includes error handling to gracefully manage issues like unavailable package managers or failed updates.
*   **Logging:** The `logging` module is used for logging, with configurable log levels.
