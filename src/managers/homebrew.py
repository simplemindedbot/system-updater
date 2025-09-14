#!/usr/bin/env python3
"""
Homebrew package manager implementation.

Handles updating Homebrew formulae and casks.
"""

import subprocess
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.base import PackageManager, PackageInfo, UpdateResult, UpdateStatus


class HomebrewManager(PackageManager):
    """Package manager for Homebrew formulae and casks."""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        super().__init__("homebrew", config, logger)
        self.update_formulae = config.get('update_formulae', True)
        self.update_casks = config.get('update_casks', True)
        self.cleanup_enabled = config.get('cleanup', True)
        
    def is_available(self) -> bool:
        """Check if Homebrew is installed and available."""
        try:
            result = subprocess.run(['brew', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def check_updates(self) -> List[PackageInfo]:
        """Check for available Homebrew updates."""
        updates = []
        
        if not self.is_available():
            self.log_warning("Homebrew not available")
            return updates
        
        # Update Homebrew itself first
        try:
            subprocess.run(['brew', 'update'], capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            self.log_error("Homebrew update timed out")
            return updates
        
        # Check formulae updates
        if self.update_formulae:
            updates.extend(self._check_formulae_updates())
            
        # Check cask updates  
        if self.update_casks:
            updates.extend(self._check_cask_updates())
            
        return updates
    
    def _check_formulae_updates(self) -> List[PackageInfo]:
        """Check for outdated formulae."""
        updates = []
        
        try:
            result = subprocess.run(['brew', 'outdated', '--json=v2'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                for formula in data.get('formulae', []):
                    package = PackageInfo(
                        name=formula['name'],
                        current_version=formula['installed_versions'][0] if formula['installed_versions'] else None,
                        available_version=formula['current_version'],
                        manager='homebrew'
                    )
                    
                    if self.should_update_package(package.name):
                        updates.append(package)
                    else:
                        self.log_info(f"Skipping excluded package: {package.name}")
                        
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.log_error(f"Failed to check formulae updates: {e}")
            
        return updates
    
    def _check_cask_updates(self) -> List[PackageInfo]:
        """Check for outdated casks."""
        updates = []
        
        try:
            result = subprocess.run(['brew', 'outdated', '--cask', '--json=v2'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                for cask in data.get('casks', []):
                    package = PackageInfo(
                        name=cask['name'],
                        current_version=cask['installed_versions'][0] if cask['installed_versions'] else None,
                        available_version=cask['current_version'],
                        manager='homebrew_cask'
                    )
                    
                    if self.should_update_package(package.name):
                        updates.append(package)
                    else:
                        self.log_info(f"Skipping excluded cask: {package.name}")
                        
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.log_error(f"Failed to check cask updates: {e}")
            
        return updates
    
    def update_packages(self, packages: Optional[List[str]] = None) -> List[UpdateResult]:
        """Update Homebrew packages."""
        results = []
        
        if not self.is_available():
            return [UpdateResult(
                package=PackageInfo(name="homebrew", manager="homebrew"),
                status=UpdateStatus.NOT_AVAILABLE,
                error="Homebrew not available"
            )]
        
        # Get packages to update
        if packages is None:
            available_updates = self.check_updates()
            packages = [pkg.name for pkg in available_updates]
        
        if not packages:
            self.log_info("No packages to update")
            return results
        
        # Separate formulae and casks
        formulae = []
        casks = []
        
        for pkg_name in packages:
            if self._is_cask(pkg_name):
                casks.append(pkg_name)
            else:
                formulae.append(pkg_name)
        
        # Update formulae
        if formulae and self.update_formulae:
            results.extend(self._update_formulae(formulae))
            
        # Update casks
        if casks and self.update_casks:
            results.extend(self._update_casks(casks))
            
        # Cleanup if enabled
        if self.cleanup_enabled:
            self.cleanup()
            
        return results
    
    def _update_formulae(self, formulae: List[str]) -> List[UpdateResult]:
        """Update specific formulae."""
        results = []
        
        self.log_info(f"Updating {len(formulae)} formulae")
        
        if self.dry_run:
            for formula in formulae:
                results.append(UpdateResult(
                    package=PackageInfo(name=formula, manager="homebrew"),
                    status=UpdateStatus.SKIPPED,
                    message="Dry run mode"
                ))
            return results
        
        try:
            cmd = ['brew', 'upgrade'] + formulae
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                for formula in formulae:
                    results.append(UpdateResult(
                        package=PackageInfo(name=formula, manager="homebrew"),
                        status=UpdateStatus.SUCCESS,
                        message="Updated successfully"
                    ))
                self.log_info(f"Successfully updated {len(formulae)} formulae")
            else:
                for formula in formulae:
                    results.append(UpdateResult(
                        package=PackageInfo(name=formula, manager="homebrew"),
                        status=UpdateStatus.FAILED,
                        error=result.stderr
                    ))
                self.log_error(f"Failed to update formulae: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            for formula in formulae:
                results.append(UpdateResult(
                    package=PackageInfo(name=formula, manager="homebrew"),
                    status=UpdateStatus.FAILED,
                    error="Update timed out"
                ))
            self.log_error("Formulae update timed out")
            
        return results
    
    def _update_casks(self, casks: List[str]) -> List[UpdateResult]:
        """Update specific casks."""
        results = []
        
        self.log_info(f"Updating {len(casks)} casks")
        
        if self.dry_run:
            for cask in casks:
                results.append(UpdateResult(
                    package=PackageInfo(name=cask, manager="homebrew_cask"),
                    status=UpdateStatus.SKIPPED,
                    message="Dry run mode"
                ))
            return results
        
        # Casks often require sudo, handle appropriately
        requires_sudo = self.requires_sudo()
        
        try:
            cmd = ['brew', 'upgrade', '--cask'] + casks
            
            if requires_sudo:
                # This might prompt for password
                result = subprocess.run(cmd, timeout=600)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                for cask in casks:
                    results.append(UpdateResult(
                        package=PackageInfo(name=cask, manager="homebrew_cask"),
                        status=UpdateStatus.SUCCESS,
                        message="Updated successfully"
                    ))
                self.log_info(f"Successfully updated {len(casks)} casks")
            else:
                for cask in casks:
                    results.append(UpdateResult(
                        package=PackageInfo(name=cask, manager="homebrew_cask"),
                        status=UpdateStatus.FAILED,
                        error="Update failed"
                    ))
                self.log_error("Failed to update casks")
                
        except subprocess.TimeoutExpired:
            for cask in casks:
                results.append(UpdateResult(
                    package=PackageInfo(name=cask, manager="homebrew_cask"),
                    status=UpdateStatus.FAILED,
                    error="Update timed out"
                ))
            self.log_error("Cask update timed out")
            
        return results
    
    def _is_cask(self, package_name: str) -> bool:
        """Check if a package is a cask."""
        try:
            result = subprocess.run(['brew', 'info', '--cask', package_name], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
    
    def cleanup(self) -> bool:
        """Clean up old Homebrew installations."""
        if not self.cleanup_enabled:
            return True
            
        try:
            self.log_info("Running Homebrew cleanup")
            result = subprocess.run(['brew', 'cleanup'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log_info("Homebrew cleanup completed")
                return True
            else:
                self.log_error(f"Cleanup failed: {result.stderr}")
                return False
                
        except subprocess.SubprocessError as e:
            self.log_error(f"Cleanup failed: {e}")
            return False
    
    def update_self(self) -> UpdateResult:
        """Update Homebrew itself."""
        try:
            self.log_info("Updating Homebrew")
            result = subprocess.run(['brew', 'update'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return UpdateResult(
                    package=PackageInfo(name="homebrew", manager="homebrew"),
                    status=UpdateStatus.SUCCESS,
                    message="Homebrew updated successfully"
                )
            else:
                return UpdateResult(
                    package=PackageInfo(name="homebrew", manager="homebrew"),
                    status=UpdateStatus.FAILED,
                    error=result.stderr
                )
                
        except subprocess.SubprocessError as e:
            return UpdateResult(
                package=PackageInfo(name="homebrew", manager="homebrew"),
                status=UpdateStatus.FAILED,
                error=str(e)
            )
    
    def get_installed_packages(self) -> List[PackageInfo]:
        """Get list of installed Homebrew packages."""
        packages = []
        
        if not self.is_available():
            return packages
        
        try:
            # Get formulae
            result = subprocess.run(['brew', 'list', '--versions'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            packages.append(PackageInfo(
                                name=name,
                                current_version=version,
                                manager='homebrew'
                            ))
            
            # Get casks
            result = subprocess.run(['brew', 'list', '--cask', '--versions'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            packages.append(PackageInfo(
                                name=name,
                                current_version=version,
                                manager='homebrew_cask'
                            ))
                            
        except subprocess.SubprocessError as e:
            self.log_error(f"Failed to get installed packages: {e}")
            
        return packages