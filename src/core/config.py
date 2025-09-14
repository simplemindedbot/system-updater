#!/usr/bin/env python3
"""
Configuration management for system-updater.

Handles loading and validating YAML configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, field


@dataclass
class SystemUpdaterConfig:
    """System updater configuration."""
    
    # Global settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    dry_run: bool = False
    sudo_mode: str = "prompt"  # prompt, cache, skip, homebrew_only
    
    # Scheduling
    auto_update: bool = True
    schedule: str = "weekly"  # daily, weekly, monthly
    
    # Manager configurations
    managers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Global exclusions
    exclude_packages: List[str] = field(default_factory=list)


class ConfigManager:
    """Manages configuration loading and validation."""
    
    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".config" / "system-updater" / "config.yaml",
        Path.home() / ".system-updater.yaml",
        Path("config") / "default.yaml",
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Explicit path to configuration file
        """
        self.logger = logging.getLogger("system-updater.config")
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> SystemUpdaterConfig:
        """
        Load configuration from YAML file.
        
        Returns:
            SystemUpdaterConfig instance
        """
        config_data = {}
        
        # Try to find and load configuration file
        config_file = self._find_config_file()
        
        if config_file:
            self.logger.info(f"Loading configuration from {config_file}")
            config_data = self._load_yaml_file(config_file)
        else:
            self.logger.info("No configuration file found, using defaults")
        
        # Create config with defaults
        config = SystemUpdaterConfig()
        
        # Override with loaded data
        if config_data:
            config = self._merge_config(config, config_data)
        
        return config
    
    def _find_config_file(self) -> Optional[Path]:
        """Find the configuration file to use."""
        
        # Use explicit path if provided
        if self.config_path:
            if self.config_path.exists():
                return self.config_path
            else:
                self.logger.warning(f"Specified config file not found: {self.config_path}")
                return None
        
        # Try default locations
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path
        
        return None
    
    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file {path}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error reading config file {path}: {e}")
            return {}
    
    def _merge_config(self, base_config: SystemUpdaterConfig, data: Dict[str, Any]) -> SystemUpdaterConfig:
        """Merge loaded data into configuration."""
        
        # Update global settings
        if 'log_level' in data:
            base_config.log_level = data['log_level']
        if 'log_file' in data:
            base_config.log_file = data['log_file']
        if 'dry_run' in data:
            base_config.dry_run = data['dry_run']
        if 'sudo_mode' in data:
            base_config.sudo_mode = data['sudo_mode']
        
        # Update scheduling
        if 'auto_update' in data:
            base_config.auto_update = data['auto_update']
        if 'schedule' in data:
            base_config.schedule = data['schedule']
        
        # Update managers
        if 'managers' in data:
            base_config.managers.update(data['managers'])
        
        # Update exclusions
        if 'exclude_packages' in data:
            base_config.exclude_packages.extend(data['exclude_packages'])
        
        return base_config
    
    def get_manager_config(self, manager_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific manager.
        
        Args:
            manager_name: Name of the package manager
            
        Returns:
            Configuration dictionary for the manager
        """
        manager_config = self.config.managers.get(manager_name, {})
        
        # Add global settings
        manager_config.setdefault('dry_run', self.config.dry_run)
        manager_config.setdefault('exclude_packages', [])
        manager_config['exclude_packages'].extend(self.config.exclude_packages)
        
        # Set sudo requirements based on manager type
        if manager_name in ['homebrew_casks', 'macos_system']:
            manager_config.setdefault('requires_sudo', True)
        
        return manager_config
    
    def save_config(self, path: Optional[Path] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            path: Path to save to, uses default if None
            
        Returns:
            True if saved successfully
        """
        save_path = path or self.config_path or self.DEFAULT_CONFIG_PATHS[0]
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dict
        config_dict = self._config_to_dict()
        
        try:
            with open(save_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=True)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'log_level': self.config.log_level,
            'log_file': self.config.log_file,
            'dry_run': self.config.dry_run,
            'sudo_mode': self.config.sudo_mode,
            'auto_update': self.config.auto_update,
            'schedule': self.config.schedule,
            'managers': self.config.managers,
            'exclude_packages': self.config.exclude_packages,
        }
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.log_level not in valid_log_levels:
            errors.append(f"Invalid log_level: {self.config.log_level}")
        
        # Validate sudo mode
        valid_sudo_modes = ['prompt', 'cache', 'skip', 'homebrew_only']
        if self.config.sudo_mode not in valid_sudo_modes:
            errors.append(f"Invalid sudo_mode: {self.config.sudo_mode}")
        
        # Validate schedule
        valid_schedules = ['daily', 'weekly', 'monthly']
        if self.config.schedule not in valid_schedules:
            errors.append(f"Invalid schedule: {self.config.schedule}")
        
        # Validate manager configurations
        for manager_name, manager_config in self.config.managers.items():
            if not isinstance(manager_config, dict):
                errors.append(f"Manager config for {manager_name} must be a dictionary")
        
        return errors


def load_default_config() -> Dict[str, Any]:
    """Load the default configuration template."""
    return {
        'log_level': 'INFO',
        'dry_run': False,
        'sudo_mode': 'prompt',
        'auto_update': True,
        'schedule': 'weekly',
        
        'managers': {
            'homebrew': {
                'enabled': True,
                'update_formulae': True,
                'update_casks': True,
                'cleanup': True,
            },
            'mac_app_store': {
                'enabled': True,
            },
            'npm': {
                'enabled': True,
                'global_only': True,
            },
            'python': {
                'enabled': True,
                'pip_user_only': True,
                'update_pip': True,
                'use_uv': True,
            },
            'ruby': {
                'enabled': True,
                'user_install': True,
                'update_system': False,
            },
            'r_packages': {
                'enabled': True,
                'cran_mirror': 'https://cran.rstudio.com',
                'update_bioconductor': True,
            },
            'texlive': {
                'enabled': True,
                'update_all': True,
            },
            'vscode': {
                'enabled': True,
                'auto_update_extensions': True,
            },
        },
        
        'exclude_packages': [],
    }