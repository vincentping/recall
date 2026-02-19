"""Configuration management: loading and accessing app config from JSON files."""

import os
import sys
import json
from typing import Any


def get_project_root() -> str:
    """Get absolute path to project root directory.

    When running from source: resolves via __file__ (src/core/config.py -> project root).
    When frozen by PyInstaller: uses sys._MEIPASS (temp extraction folder).
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(script_dir))


class Config:
    """Singleton configuration manager with default and user preference support."""

    _instance = None
    _config_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from default and user preference files."""
        project_root = get_project_root()

        # Load default configuration
        default_config_path = os.path.join(project_root, 'config', 'app_config.json')
        try:
            with open(default_config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            self._config_data = self._get_fallback_config()

        # Override with user preferences if available
        user_config_path = os.path.join(project_root, 'config', 'user_preferences.json')
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    self._deep_merge(self._config_data, json.load(f))
            except Exception as e:
                print(f"Warning: Could not load user preferences: {e}")

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """Recursively merge override dict into base dict in-place."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _get_fallback_config() -> dict:
        """Return hardcoded fallback configuration."""
        return {
            'app': {'name': 'ReCall', 'version': '1.0.0'},
            'window': {
                'default_width': 1000, 'default_height': 700,
                'default_x': 100, 'default_y': 100
            },
            'language': {'default': 'en_US', 'available': ['en_US', 'zh_CN']},
            'database': {'path': 'data/default.db', 'backup_dir': 'data/backups'},
            'resources': {
                'translations_dir': 'resources/translations',
                'themes_dir': 'resources/themes'
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation (e.g. 'window.default_width')."""
        value = self._config_data
        for k in key.split('.'):
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_section(self, section: str) -> dict | None:
        """Get an entire configuration section by name."""
        return self._config_data.get(section)

    def reload(self) -> None:
        """Reload configuration from files."""
        self._load_config()

    @staticmethod
    def get_project_root() -> str:
        """Get absolute path to project root directory."""
        return get_project_root()

    def get_absolute_path(self, relative_path: str) -> str:
        """Convert a path relative to project root into an absolute path."""
        return os.path.join(get_project_root(), relative_path)
