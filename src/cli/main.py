#!/usr/bin/env python3
"""
Main CLI interface for system-updater.

Provides command-line access to the system update functionality.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import ConfigManager
from core.orchestrator import SystemUpdater


def setup_logging(log_level: str, log_file: Optional[str] = None):
    """Set up logging configuration."""
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def cmd_update(args):
    """Handle the update command."""
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    
    # Set up logging
    setup_logging(config_manager.config.log_level, config_manager.config.log_file)
    
    logger = logging.getLogger('system-updater.cli')
    
    # Override dry-run if specified
    if args.dry_run:
        config_manager.config.dry_run = True
    
    # Create updater
    updater = SystemUpdater(config_manager)
    
    try:
        if args.manager == 'all':
            # Update all enabled managers
            logger.info("Starting system-wide update")
            results = updater.update_all()
        else:
            # Update specific manager
            logger.info(f"Updating {args.manager}")
            results = updater.update_manager(args.manager)
        
        # Report results
        total_updates = len(results)
        successful = len([r for r in results if r.status.value == 'success'])
        failed = len([r for r in results if r.status.value == 'failed'])
        skipped = len([r for r in results if r.status.value == 'skipped'])
        
        logger.info(f"Update completed: {successful} successful, {failed} failed, {skipped} skipped out of {total_updates} total")
        
        if failed > 0:
            logger.warning("Some updates failed. Check the logs for details.")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return 1


def cmd_list(args):
    """Handle the list command."""
    
    config_manager = ConfigManager(args.config)
    setup_logging(config_manager.config.log_level)
    
    updater = SystemUpdater(config_manager)
    managers = updater.get_available_managers()
    
    print("Available package managers:")
    print()
    
    for manager_name, manager in managers.items():
        status = "✓ Available" if manager.is_available() else "✗ Not available"
        enabled = "Enabled" if manager.enabled else "Disabled"
        
        print(f"  {manager_name:15} - {status:15} ({enabled})")
    
    return 0


def cmd_status(args):
    """Handle the status command."""
    
    config_manager = ConfigManager(args.config)
    setup_logging(config_manager.config.log_level)
    
    updater = SystemUpdater(config_manager)
    
    print("System Update Status")
    print("===================")
    print()
    
    managers = updater.get_available_managers()
    
    for manager_name, manager in managers.items():
        if not manager.enabled:
            continue
            
        if not manager.is_available():
            print(f"{manager_name}: Not available")
            continue
        
        try:
            updates = manager.check_updates()
            if updates:
                print(f"{manager_name}: {len(updates)} updates available")
                if args.verbose:
                    for update in updates[:5]:  # Show first 5
                        version_info = ""
                        if update.current_version and update.available_version:
                            version_info = f" ({update.current_version} -> {update.available_version})"
                        print(f"  - {update.name}{version_info}")
                    
                    if len(updates) > 5:
                        print(f"  ... and {len(updates) - 5} more")
            else:
                print(f"{manager_name}: Up to date")
                
        except Exception as e:
            print(f"{manager_name}: Error checking updates - {e}")
        
        print()
    
    return 0


def cmd_config(args):
    """Handle the config command."""
    
    config_manager = ConfigManager(args.config)
    
    if args.init:
        # Initialize new config file
        config_path = Path.home() / ".config" / "system-updater" / "config.yaml"
        
        if config_path.exists() and not args.force:
            print(f"Configuration file already exists: {config_path}")
            print("Use --force to overwrite")
            return 1
        
        success = config_manager.save_config(config_path)
        if success:
            print(f"Configuration initialized at: {config_path}")
            return 0
        else:
            print("Failed to initialize configuration")
            return 1
    
    elif args.validate:
        # Validate current configuration
        errors = config_manager.validate_config()
        
        if errors:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("Configuration is valid")
            return 0
    
    else:
        # Show current configuration
        config_dict = config_manager._config_to_dict()
        
        import yaml
        print("Current configuration:")
        print(yaml.dump(config_dict, default_flow_style=False, sort_keys=True))
        return 0


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="System package updater with component-based architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s update all              # Update all enabled package managers
  %(prog)s update homebrew         # Update only Homebrew packages
  %(prog)s status                  # Check for available updates
  %(prog)s list                    # List available package managers
  %(prog)s config --init           # Create default configuration file
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update packages')
    update_parser.add_argument(
        'manager',
        choices=['all', 'homebrew', 'mac_app_store', 'npm', 'python', 'ruby', 'r_packages', 'texlive', 'vscode'],
        help='Package manager to update'
    )
    update_parser.set_defaults(func=cmd_update)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available package managers')
    list_parser.set_defaults(func=cmd_list)
    
    # Status command  
    status_parser = subparsers.add_parser('status', help='Check update status')
    status_parser.set_defaults(func=cmd_status)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument('--init', action='store_true', help='Initialize new config file')
    config_group.add_argument('--validate', action='store_true', help='Validate current config')
    config_parser.add_argument('--force', action='store_true', help='Force overwrite existing config')
    config_parser.set_defaults(func=cmd_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())