# Configuration Directory

This directory contains configuration files for ReCall.

## Configuration Files

### app_config.json
The main application configuration file containing default settings.

**Sections:**
- `app`: Application metadata (name, version)
- `window`: Default window size and position
- `language`: Language settings (default and available languages)
- `database`: Database file path and backup directory
- `resources`: Resource directories (translations, themes)
- `review`: Review mode settings (question count, shuffling)
- `ui`: UI behavior settings

### user_preferences.json (Auto-generated)
User-specific preferences that override default settings. This file is:
- Created automatically when user changes settings
- Ignored by Git (in .gitignore)
- Not version controlled

**Note:** If you want to reset to defaults, simply delete this file.

## Usage

The configuration system is loaded automatically by the application:

```python
from src.core.config import Config

config = Config()
width = config.get('window.default_width')  # Returns 1000
```

## Configuration Priority

1. User preferences (`user_preferences.json`) - highest priority
2. Default config (`app_config.json`)
3. Hardcoded fallbacks in code - lowest priority

## Modifying Configuration

To change default settings:
1. Edit `app_config.json`
2. Restart the application

To change user preferences:
- Use the application's settings UI (when implemented)
- Or manually edit `user_preferences.json`

## Adding New Configuration

When adding new configuration options:
1. Add the setting to `app_config.json` with a sensible default
2. Update this README with a description
3. Access via `Config().get('section.key')`
