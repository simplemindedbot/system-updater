#!/usr/bin/env python3
"""
System Updater - Component-based package manager automation.

A Python-based system for updating packages across multiple package managers
on macOS with YAML configuration and modular architecture.
"""

__version__ = "0.1.0"
__author__ = "System Updater"
__description__ = "Component-based package manager automation system"

from .core.config import ConfigManager, SystemUpdaterConfig
from .core.orchestrator import SystemUpdater
from .core.base import PackageManager, PackageInfo, UpdateResult, UpdateStatus

__all__ = [
    "ConfigManager",
    "SystemUpdaterConfig", 
    "SystemUpdater",
    "PackageManager",
    "PackageInfo",
    "UpdateResult",
    "UpdateStatus",
]