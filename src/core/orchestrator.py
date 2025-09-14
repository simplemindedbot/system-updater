#!/usr/bin/env python3
"""
System update orchestrator.

Coordinates updates across all configured package managers.
"""

import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .config import ConfigManager
from .base import PackageManager, UpdateResult, UpdateStatus, PackageInfo

# Import all available managers
from ..managers.homebrew import HomebrewManager


class SystemUpdater:
    """
    Main orchestrator for system updates.
    
    Coordinates updates across all configured package managers.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the system updater.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.logger = logging.getLogger("system-updater.orchestrator")
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize managers
        self.managers = self._initialize_managers()
    
    def _initialize_managers(self) -> Dict[str, PackageManager]:
        """Initialize all available package managers."""
        
        managers = {}
        
        # Homebrew
        if 'homebrew' in self.config.managers:
            config = self.config_manager.get_manager_config('homebrew')
            if config.get('enabled', True):
                try:
                    managers['homebrew'] = HomebrewManager(config, self.logger)
                    self.logger.debug("Initialized Homebrew manager")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Homebrew manager: {e}")
        
        # TODO: Initialize other managers
        # - Mac App Store
        # - npm  
        # - Python (pip/uv)
        # - Ruby gems
        # - R packages
        # - TeX Live
        # - VS Code extensions
        
        self.logger.info(f"Initialized {len(managers)} package managers")
        return managers
    
    def get_available_managers(self) -> Dict[str, PackageManager]:
        """Get all available package managers."""
        return self.managers.copy()
    
    def get_enabled_managers(self) -> Dict[str, PackageManager]:
        """Get only enabled package managers."""
        return {
            name: manager for name, manager in self.managers.items()
            if manager.enabled
        }
    
    def update_all(self) -> List[UpdateResult]:
        """
        Update all enabled package managers.
        
        Returns:
            List of all update results
        """
        results = []
        enabled_managers = self.get_enabled_managers()
        
        if not enabled_managers:
            self.logger.warning("No enabled package managers found")
            return results
        
        self.logger.info(f"Starting updates for {len(enabled_managers)} managers")
        
        # Sequential updates to avoid conflicts
        for manager_name, manager in enabled_managers.items():
            if not manager.is_available():
                self.logger.warning(f"{manager_name} is not available, skipping")
                continue
            
            try:
                self.logger.info(f"Updating {manager_name}")
                
                # Update manager itself first
                if hasattr(manager, 'update_self'):
                    self_result = manager.update_self()
                    if self_result.status != UpdateStatus.NOT_AVAILABLE:
                        results.append(self_result)
                
                # Update packages
                manager_results = manager.update_packages()
                results.extend(manager_results)
                
                self.logger.info(f"Completed {manager_name}: {len(manager_results)} packages processed")
                
            except Exception as e:
                self.logger.error(f"Failed to update {manager_name}: {e}")
                results.append(UpdateResult(
                    package=PackageInfo(name=manager_name, manager=manager_name),
                    status=UpdateStatus.FAILED,
                    error=str(e)
                ))
        
        # Run cleanup for managers that support it
        self._run_cleanup(enabled_managers)
        
        self.logger.info(f"System update completed: {len(results)} total updates")
        return results
    
    def update_manager(self, manager_name: str, packages: Optional[List[str]] = None) -> List[UpdateResult]:
        """
        Update a specific package manager.
        
        Args:
            manager_name: Name of the manager to update
            packages: Specific packages to update, or None for all
            
        Returns:
            List of update results
        """
        results = []
        
        if manager_name not in self.managers:
            error_msg = f"Unknown manager: {manager_name}"
            self.logger.error(error_msg)
            return [UpdateResult(
                package=PackageInfo(name=manager_name, manager=manager_name),
                status=UpdateStatus.FAILED,
                error=error_msg
            )]
        
        manager = self.managers[manager_name]
        
        if not manager.enabled:
            self.logger.warning(f"{manager_name} is disabled")
            return [UpdateResult(
                package=PackageInfo(name=manager_name, manager=manager_name),
                status=UpdateStatus.SKIPPED,
                message="Manager is disabled"
            )]
        
        if not manager.is_available():
            error_msg = f"{manager_name} is not available"
            self.logger.error(error_msg)
            return [UpdateResult(
                package=PackageInfo(name=manager_name, manager=manager_name),
                status=UpdateStatus.NOT_AVAILABLE,
                error=error_msg
            )]
        
        try:
            self.logger.info(f"Updating {manager_name}")
            
            # Update manager itself first
            if hasattr(manager, 'update_self'):
                self_result = manager.update_self()
                if self_result.status != UpdateStatus.NOT_AVAILABLE:
                    results.append(self_result)
            
            # Update packages
            manager_results = manager.update_packages(packages)
            results.extend(manager_results)
            
            # Cleanup if supported
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
            
            self.logger.info(f"Completed {manager_name}: {len(manager_results)} packages processed")
            
        except Exception as e:
            self.logger.error(f"Failed to update {manager_name}: {e}")
            results.append(UpdateResult(
                package=PackageInfo(name=manager_name, manager=manager_name),
                status=UpdateStatus.FAILED,
                error=str(e)
            ))
        
        return results
    
    def check_all_updates(self) -> Dict[str, List[PackageInfo]]:
        """
        Check for updates across all managers without applying them.
        
        Returns:
            Dictionary mapping manager names to available updates
        """
        updates = {}
        enabled_managers = self.get_enabled_managers()
        
        for manager_name, manager in enabled_managers.items():
            if not manager.is_available():
                continue
            
            try:
                manager_updates = manager.check_updates()
                if manager_updates:
                    updates[manager_name] = manager_updates
                    self.logger.info(f"{manager_name}: {len(manager_updates)} updates available")
                else:
                    self.logger.info(f"{manager_name}: Up to date")
                    
            except Exception as e:
                self.logger.error(f"Failed to check updates for {manager_name}: {e}")
        
        return updates
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status information
        """
        status = {
            'managers': {},
            'total_managers': len(self.managers),
            'enabled_managers': len(self.get_enabled_managers()),
            'available_managers': 0,
            'total_updates_available': 0,
        }
        
        for manager_name, manager in self.managers.items():
            manager_status = {
                'enabled': manager.enabled,
                'available': manager.is_available(),
                'updates_available': 0,
                'error': None
            }
            
            if manager.enabled and manager.is_available():
                status['available_managers'] += 1
                
                try:
                    updates = manager.check_updates()
                    manager_status['updates_available'] = len(updates)
                    status['total_updates_available'] += len(updates)
                    
                except Exception as e:
                    manager_status['error'] = str(e)
            
            status['managers'][manager_name] = manager_status
        
        return status
    
    def _run_cleanup(self, managers: Dict[str, PackageManager]):
        """Run cleanup for managers that support it."""
        
        for manager_name, manager in managers.items():
            if not hasattr(manager, 'cleanup'):
                continue
            
            try:
                self.logger.info(f"Running cleanup for {manager_name}")
                success = manager.cleanup()
                
                if success:
                    self.logger.debug(f"Cleanup completed for {manager_name}")
                else:
                    self.logger.warning(f"Cleanup failed for {manager_name}")
                    
            except Exception as e:
                self.logger.error(f"Cleanup error for {manager_name}: {e}")
    
    def dry_run_all(self) -> Dict[str, List[PackageInfo]]:
        """
        Perform a dry run to show what would be updated.
        
        Returns:
            Dictionary mapping manager names to packages that would be updated
        """
        # Set all managers to dry run mode temporarily
        original_dry_run_states = {}
        
        try:
            for manager_name, manager in self.managers.items():
                original_dry_run_states[manager_name] = manager.dry_run
                manager.dry_run = True
            
            # Check for updates (this is what would be updated)
            return self.check_all_updates()
            
        finally:
            # Restore original dry run states
            for manager_name, manager in self.managers.items():
                manager.dry_run = original_dry_run_states.get(manager_name, False)
    
    def get_manager_by_name(self, name: str) -> Optional[PackageManager]:
        """Get a specific manager by name."""
        return self.managers.get(name)