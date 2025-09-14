#!/usr/bin/env python3
"""
Abstract base class for package managers.

This module defines the interface that all package managers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import logging


class UpdateStatus(Enum):
    """Status of a package update operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_AVAILABLE = "not_available"


class PackageInfo(dataclass):
    """Information about a package."""
    name: str
    current_version: Optional[str] = None
    available_version: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None
    manager: Optional[str] = None


class UpdateResult(dataclass):
    """Result of an update operation."""
    package: PackageInfo
    status: UpdateStatus
    message: Optional[str] = None
    error: Optional[str] = None


class PackageManager(ABC):
    """
    Abstract base class for all package managers.
    
    Each package manager (homebrew, npm, pip, etc.) must implement this interface.
    """
    
    def __init__(self, name: str, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the package manager.
        
        Args:
            name: Human-readable name of this manager
            config: Configuration dictionary for this manager
            logger: Logger instance to use
        """
        self.name = name
        self.config = config
        self.logger = logger or logging.getLogger(f"system-updater.{name}")
        self.enabled = config.get('enabled', True)
        self.dry_run = config.get('dry_run', False)
        
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this package manager is available on the system.
        
        Returns:
            True if the package manager is installed and usable
        """
        pass
    
    @abstractmethod
    def check_updates(self) -> List[PackageInfo]:
        """
        Check for available package updates.
        
        Returns:
            List of packages that have updates available
        """
        pass
    
    @abstractmethod
    def update_packages(self, packages: Optional[List[str]] = None) -> List[UpdateResult]:
        """
        Update packages.
        
        Args:
            packages: Specific packages to update. If None, update all.
            
        Returns:
            List of update results
        """
        pass
    
    def update_self(self) -> UpdateResult:
        """
        Update the package manager itself.
        
        Returns:
            Result of the self-update operation
        """
        # Default implementation - many managers don't need self-updates
        return UpdateResult(
            package=PackageInfo(name=self.name, manager=self.name),
            status=UpdateStatus.NOT_AVAILABLE,
            message="Self-update not supported"
        )
    
    def get_installed_packages(self) -> List[PackageInfo]:
        """
        Get list of installed packages.
        
        Returns:
            List of installed packages
        """
        # Default implementation returns empty list
        return []
    
    def cleanup(self) -> bool:
        """
        Perform cleanup operations (remove cached files, etc.).
        
        Returns:
            True if cleanup was successful
        """
        # Default implementation does nothing
        return True
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        Get information about this package manager.
        
        Returns:
            Dictionary with manager information
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'available': self.is_available(),
            'config': self.config
        }
    
    def requires_sudo(self) -> bool:
        """
        Check if this manager requires sudo for updates.
        
        Returns:
            True if sudo is required
        """
        return self.config.get('requires_sudo', False)
    
    def get_excluded_packages(self) -> List[str]:
        """
        Get list of packages to exclude from updates.
        
        Returns:
            List of package names to skip
        """
        return self.config.get('exclude_packages', [])
    
    def should_update_package(self, package_name: str) -> bool:
        """
        Check if a package should be updated.
        
        Args:
            package_name: Name of the package
            
        Returns:
            True if package should be updated
        """
        if package_name in self.get_excluded_packages():
            return False
        
        # Additional logic can be added here
        return True
    
    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(f"[{self.name}] {message}")