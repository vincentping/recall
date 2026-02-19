import sys
import os
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QDialog, QVBoxLayout, QTextBrowser
from PySide6.QtCore import QCoreApplication, QTranslator, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QIcon

from src.core.db_manager import DBManager
from src.core.config import Config, get_project_root
from src.core.theme_manager import ThemeManager
from src.ui.admin.input_window import InputWindow
from src.ui.admin.batch_import_window import BatchImportWindow
from src.ui.admin.question_manager_window import QuestionManagerWindow
from src.ui.admin.exam_manager import ExamManager
from src.ui.home_page import HomePage
from src.ui.practice_window import PracticeWindow
from src.ui.practice_result import PracticeResult


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = Config()

        # Database
        self.db_manager = None
        if not self.init_database():
            sys.exit(1)

        # Theme
        self.theme_manager = ThemeManager()
        self.current_theme = self.config.get('theme.default', 'default')
        self.current_font_size = self.config.get('theme.font_size', 10)
        self.theme_manager.load_theme(self.current_theme)
        self.theme_manager.set_font_size(self.current_font_size)
        self.theme_manager.apply_theme()

        # Translation
        self.translator = QTranslator()
        self.current_lang = self.config.get('language.default', 'en_US')
        self.load_translator(self.current_lang)

        # Window setup
        icon_path = os.path.join(get_project_root(), 'resources', 'icons', 'app.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self._update_window_title()
        window_config = self.config.get_section('window')
        if window_config:
            self.setGeometry(
                window_config.get('default_x', 100),
                window_config.get('default_y', 100),
                window_config.get('default_width', 1000),
                window_config.get('default_height', 700)
            )
        else:
            self.setGeometry(100, 100, 1000, 700)

        # Page navigation via QStackedWidget
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        self.home_page = HomePage(self.db_manager)
        self.home_page.start_practice.connect(self.on_start_practice)
        self.home_page.open_exam_manager.connect(self.show_exam_manager)
        self.stacked.addWidget(self.home_page)

        self.practice_window = None
        self.practice_result = None

        # Admin windows (created on demand)
        self.input_window = None
        self.batch_import_window = None
        self.question_manager_window = None
        self.exam_manager = None

        self.create_menus()

    def init_database(self) -> bool:
        try:
            self.db_manager = DBManager()
            return True
        except Exception as e:
            reply = QMessageBox.critical(
                self,
                self.tr("Database Error"),
                self.tr("Failed to initialize database:\n\n{0}\n\nWould you like to retry?").format(str(e)),
                QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close,
                QMessageBox.StandardButton.Retry
            )
            if reply == QMessageBox.StandardButton.Retry:
                return self.init_database()
            return False

    def tr(self, text: str) -> str:
        return QCoreApplication.translate("MainWindow", text)

    # --- Page navigation ---

    def on_start_practice(self, practice_config: dict):
        """HomePage emits start_practice signal."""
        self._remove_practice_pages()
        self.practice_window = PracticeWindow(self.db_manager, practice_config)
        self.practice_window.practice_finished.connect(self.on_practice_finished)
        self.practice_window.practice_cancelled.connect(self.go_home)
        self.practice_window.no_questions.connect(self.on_no_questions)
        self.stacked.addWidget(self.practice_window)
        self.stacked.setCurrentWidget(self.practice_window)
        self.practice_window.load_questions()  # Call after signals are connected

    def on_practice_finished(self, result_data: dict):
        """PracticeWindow emits practice_finished signal."""
        self.practice_result = PracticeResult(result_data)
        self.practice_result.back_home.connect(self.go_home)
        self.practice_result.start_new.connect(self.go_home)
        self.practice_result.retry_wrong.connect(self.on_retry_wrong)
        self.stacked.addWidget(self.practice_result)
        self.stacked.setCurrentWidget(self.practice_result)

    def on_retry_wrong(self, question_ids: list):
        """PracticeResult emits retry_wrong signal with wrong question IDs."""
        self._remove_practice_pages()
        retry_config = {
            'mode': 'learn',
            'question_ids': question_ids,
            'module_id': None,
            'module_name': '',
            'count': len(question_ids),
        }
        self.practice_window = PracticeWindow(self.db_manager, retry_config)
        self.practice_window.practice_finished.connect(self.on_practice_finished)
        self.practice_window.practice_cancelled.connect(self.go_home)
        self.practice_window.no_questions.connect(self.on_no_questions)
        self.stacked.addWidget(self.practice_window)
        self.stacked.setCurrentWidget(self.practice_window)
        self.practice_window.load_questions()  # Call after signals are connected

    def on_no_questions(self):
        """PracticeWindow emits no_questions when no matching questions found."""
        self.go_home()
        QMessageBox.warning(
            self, self.tr("No Questions"),
            self.tr("No matching questions found.\n\n"
                     "Please check your filter settings or add more questions.")
        )

    def go_home(self):
        """Navigate back to home page and refresh stats."""
        self._remove_practice_pages()
        self.home_page.reset_filters()
        self.home_page.refresh_stats()
        self.stacked.setCurrentWidget(self.home_page)

    def _remove_practice_pages(self):
        """Remove practice and result pages from stack."""
        for attr in ('practice_window', 'practice_result'):
            widget = getattr(self, attr)
            if widget:
                self.stacked.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)

    # --- Menus ---

    def create_menus(self) -> None:
        menu_bar = self.menuBar()

        # File
        file_menu = menu_bar.addMenu(self.tr("&File"))

        exit_action = QAction(self.tr("E&xit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Language
        lang_menu = menu_bar.addMenu(self.tr("&Language"))
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for label, locale in [(self.tr("English"), 'en_US'), (self.tr("Chinese"), 'zh_CN')]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(locale == self.current_lang)
            action.triggered.connect(lambda _=None, loc=locale: self.change_language(loc))
            lang_group.addAction(action)
            lang_menu.addAction(action)

        # View
        view_menu = menu_bar.addMenu(self.tr("&View"))

        theme_submenu = view_menu.addMenu(self.tr("Theme"))
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for theme in self.theme_manager.get_available_themes():
            theme_name = self.tr(theme['name_key']) if theme.get('name_key') else theme['name']
            theme_action = QAction(theme_name, self)
            theme_action.setCheckable(True)
            theme_action.setChecked(theme['id'] == self.current_theme)
            tid = theme['id']
            theme_action.triggered.connect(lambda checked=False, t=tid: self.change_theme(t))
            theme_group.addAction(theme_action)
            theme_submenu.addAction(theme_action)

        view_menu.addSeparator()

        font_submenu = view_menu.addMenu(self.tr("Font Size"))
        font_group = QActionGroup(self)
        font_group.setExclusive(True)
        for label, size in [
            (self.tr("Small (8pt)"), 8),
            (self.tr("Normal (10pt)"), 10),
            (self.tr("Large (12pt)"), 12),
            (self.tr("Extra Large (14pt)"), 14),
            (self.tr("Huge (16pt)"), 16),
        ]:
            font_action = QAction(label, self)
            font_action.setCheckable(True)
            font_action.setChecked(size == self.current_font_size)
            font_action.triggered.connect(lambda checked=False, s=size: self.change_font_size(s))
            font_group.addAction(font_action)
            font_submenu.addAction(font_action)

        # Admin
        admin_menu = menu_bar.addMenu(self.tr("&Admin"))
        for label, slot in [
            (self.tr("Exam Manager"), self.show_exam_manager),
            (self.tr("New Question Entry"), self.show_input_window),
            (self.tr("Batch Import from Markdown"), self.show_batch_import_window),
            (self.tr("Manage Questions (Edit/Delete)"), self.show_question_manager_window),
        ]:
            action = QAction(label, self)
            action.triggered.connect(slot)
            admin_menu.addAction(action)

        admin_menu.addSeparator()
        reset_stats_action = QAction(self.tr("Reset Statistics"), self)
        reset_stats_action.triggered.connect(self.reset_statistics)
        admin_menu.addAction(reset_stats_action)

        # Help
        help_menu = menu_bar.addMenu(self.tr("&Help"))
        guide_action = QAction(self.tr("User Guide"), self)
        guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(guide_action)
        help_menu.addSeparator()
        about_action = QAction(self.tr("About"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # --- Admin windows ---

    def _refresh_home(self):
        """Refresh home page and window title (called when admin windows close)."""
        if self.stacked.currentWidget() is self.home_page:
            self.home_page.refresh_stats()
            self.home_page.load_filter_data()
        self._update_window_title()

    def _show_admin_window(self, attr: str, cls, title: str):
        """Generic helper to show an admin window (create on first use)."""
        window = getattr(self, attr)
        if window is None:
            window = cls(self.db_manager)
            window.setWindowTitle(title)
            window.destroyed.connect(lambda: setattr(self, attr, None))
            window.destroyed.connect(self._refresh_home)
            setattr(self, attr, window)
        window.show()
        window.activateWindow()

    def show_input_window(self) -> None:
        self._show_admin_window('input_window', InputWindow, self.tr("Question Entry Form"))

    def show_batch_import_window(self) -> None:
        self._show_admin_window('batch_import_window', BatchImportWindow, self.tr("Batch Import from Markdown"))

    def show_question_manager_window(self) -> None:
        self._show_admin_window('question_manager_window', QuestionManagerWindow, self.tr("Question Manager"))

    def show_exam_manager(self) -> None:
        if self.exam_manager is None:
            self.exam_manager = ExamManager(self.db_manager)
            self.exam_manager.setWindowTitle(self.tr("Exam Manager"))
            self.exam_manager.destroyed.connect(
                lambda: setattr(self, 'exam_manager', None)
            )
            self.exam_manager.destroyed.connect(self._refresh_home)
            self.exam_manager.exam_switched.connect(self.switch_exam)
            self.exam_manager.exam_renamed.connect(self._update_window_title)
        self.exam_manager.show()
        self.exam_manager.activateWindow()

    # --- Exam management ---

    def _update_window_title(self):
        """Update window title with current exam name."""
        app_name = self.tr('ReCall')
        if self.db_manager.get_question_count() == 0:
            self.setWindowTitle(app_name)
        else:
            exam_name = self.db_manager.get_exam_name()
            self.setWindowTitle(f"{exam_name} - {app_name}")

    def switch_exam(self, db_path: str):
        """Switch to a different exam database."""
        if os.path.normpath(db_path) == os.path.normpath(self.db_manager.db_path):
            return

        # Close admin windows (except exam_manager which stays open)
        for attr in ('input_window', 'batch_import_window',
                     'question_manager_window'):
            window = getattr(self, attr)
            if window:
                window.close()
                setattr(self, attr, None)

        # Navigate home and discard practice
        self._remove_practice_pages()

        # Swap database
        self.db_manager.reopen(db_path)

        # Recreate home page
        self.stacked.removeWidget(self.home_page)
        self.home_page.deleteLater()
        self.home_page = HomePage(self.db_manager)
        self.home_page.start_practice.connect(self.on_start_practice)
        self.home_page.open_exam_manager.connect(self.show_exam_manager)
        self.stacked.addWidget(self.home_page)
        self.stacked.setCurrentWidget(self.home_page)

        self._update_window_title()

        # Refresh structure manager if open
        if self.exam_manager:
            self.exam_manager.refresh_for_exam()

    def show_user_guide(self):
        """Show the user guide (HELP.md) in a dialog."""
        help_path = os.path.join(get_project_root(), 'docs', 'HELP.md')
        try:
            with open(help_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, self.tr("User Guide"),
                                self.tr("Help file not found."))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("User Guide"))
        dialog.setWindowFlags(
            dialog.windowFlags() |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        dialog.resize(750, 600)
        layout = QVBoxLayout(dialog)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(content)
        layout.addWidget(browser)

        dialog.exec()

    def show_about(self):
        """Show the About dialog."""
        version = self.config.get('app.version', '1.0.0')
        QMessageBox.about(
            self, self.tr("About"),
            self.tr("<h3>ReCall</h3>"
                     "<p><i>Know it when it counts.</i></p>"
                     "<p>A personal question bank for focused study and exam prep.</p>"
                     "<p>Version: %s</p>"
                     "<p>Developed by Vincent Ping</p>"
                     '<p>GitHub: <a href="https://github.com/vincentping/recall" '
                     'style="color: #0078D7;">github.com/vincentping/recall</a></p>') % version
        )

    def reset_statistics(self):
        """Reset all practice statistics after double confirmation."""
        reply = QMessageBox.warning(
            self, self.tr("Reset Statistics"),
            self.tr("This will permanently delete ALL practice sessions and answer records.\n\n"
                     "This action cannot be undone. Are you sure?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.db_manager.reset_practice_stats():
            self.home_page.refresh_stats()
            QMessageBox.information(self, self.tr("Reset Statistics"),
                                    self.tr("All practice statistics have been reset."))
        else:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Failed to reset statistics. Check console for details."))

    # --- Theme & Language ---

    def change_theme(self, theme_id: str) -> None:
        if self.theme_manager.load_theme(theme_id):
            self.current_theme = theme_id
            self.theme_manager.apply_theme()

    def change_font_size(self, size: int) -> None:
        self.current_font_size = size
        self.theme_manager.set_font_size(size)
        self.theme_manager.apply_theme()

    def load_translator(self, lang_code: str) -> None:
        QCoreApplication.removeTranslator(self.translator)
        if lang_code == 'en_US':
            return
        translation_file = os.path.join(
            get_project_root(), "resources", "translations", lang_code, f"app_{lang_code}.qm"
        )
        if not self.translator.load(translation_file):
            print(f"Translation file not found: {translation_file}")
        else:
            QCoreApplication.installTranslator(self.translator)

    def change_language(self, lang_code: str) -> None:
        self.current_lang = lang_code
        self.load_translator(lang_code)
        self._update_window_title()

        # Retranslate active pages
        self.home_page.retranslate_ui()
        if self.practice_window:
            self.practice_window.retranslate_ui()
        if self.practice_result:
            self.practice_result.retranslate_ui()

        # Retranslate open admin windows
        admin_windows = [
            (self.exam_manager, self.tr("Exam Manager")),
            (self.input_window, self.tr("Question Entry Form")),
            (self.batch_import_window, self.tr("Batch Import from Markdown")),
            (self.question_manager_window, self.tr("Question Manager")),
        ]
        for window, title in admin_windows:
            if window:
                window.retranslate_ui()
                window.setWindowTitle(title)

        # Rebuild menus with new language
        self.menuBar().clear()
        self.create_menus()

    def closeEvent(self, event: QCloseEvent) -> None:
        for window in (self.input_window, self.batch_import_window,
                       self.question_manager_window, self.exam_manager):
            if window:
                window.close()

        if self.db_manager:
            self.db_manager.close()

        super().closeEvent(event)
