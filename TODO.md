# TODO

Project task list and development roadmap for ReCall.

> **Last Updated:** 2026-02-17
> **Current Version:** 1.0.0

---

## High Priority

### User Preferences Persistence
**Status:** Config system ready, saving not implemented
- [ ] `Config.save_user_preference()` with `config/user_preferences.json`
- [ ] Save window size/position on close
- [ ] Save last selected module/lesson
- [ ] Save review mode settings
- [ ] Settings window (`src/ui/settings_window.py`) with language, theme, review preferences

### Logging System
**Status:** Not started
- [ ] Logger module (`src/core/logger.py`) with file + console output
- [ ] Log rotation (10MB max, keep 5 files)
- [ ] Replace all `print()` statements with logger calls
- [ ] Add `logging` section to `app_config.json`

---

## Medium Priority

### Database Backup
- [ ] Backup manager (`src/core/backup_manager.py`)
- [ ] Auto backup on close, timestamp naming, cleanup old backups
- [ ] Backup/restore UI in Admin menu
- [ ] Configurable backup count and directory

### Test Coverage
**Status:** 1 unit test file exists
- [ ] Unit tests for config, db_manager, md_parser, theme_manager
- [ ] UI tests with pytest-qt (main_window, input_window, practice_window)
- [ ] Integration tests (question flow, import flow, translation switching)
- [ ] Target 80%+ code coverage

### Error Handling
- [ ] Global exception handler (`src/core/error_handler.py`)
- [ ] User-friendly error dialog with copy-to-clipboard
- [ ] Crash recovery (save state, offer recovery on restart)

---

## Low Priority / Future

### Performance
- [ ] Database indexes on frequently queried columns
- [ ] QThreads for long operations (imports)
- [ ] Progress bars for batch operations

### i18n Improvements
- [ ] Audit for hardcoded strings, replace with `tr()` calls
- [ ] Regenerate .ts files and complete translations

### Future Features
- [ ] Question statistics dashboard (performance tracking, weak areas)
- [ ] Export to PDF / CSV
- [ ] Spaced repetition algorithm
- [ ] Cloud sync / multi-device support

---

## Documentation

**Existing:**
- [docs/question_management_design.md](docs/question_management_design.md)
- [docs/user_facing_design.md](docs/user_facing_design.md)

**Planned:**
- [ ] API reference (`docs/api.md`)
- [ ] Architecture overview with DB schema (`docs/architecture.md`)
- [ ] User manual (`docs/user_guide.md`)
- [ ] CHANGELOG.md
