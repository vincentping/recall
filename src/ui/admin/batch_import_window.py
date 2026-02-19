from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QFileDialog, QTextEdit,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import QCoreApplication
from src.core.db_manager import DBManager
from src.utils.md_parser import MarkdownQuestionParser


class BatchImportWindow(QWidget):
    """Batch import questions from Markdown files."""

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.questions_data = []
        self.current_file = None
        self.init_ui()

    def tr(self, text):
        return QCoreApplication.translate("BatchImportWindow", text)

    def init_ui(self):
        self.setWindowTitle(self.tr("Batch Import Questions from Markdown"))
        self.setGeometry(200, 200, 800, 600)
        main_layout = QVBoxLayout(self)
        self._setup_ui_widgets()

    def _setup_ui_widgets(self):
        """Create and add all UI widgets to the existing layout."""
        main_layout = self.layout()

        # --- File selection ---
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel(self.tr("Markdown File:")))

        self.file_path_label = QLabel(self.tr("No file selected"))
        self.file_path_label.setStyleSheet("color: gray;")
        file_layout.addWidget(self.file_path_label, stretch=1)

        self.browse_btn = QPushButton(self.tr("Browse..."))
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        main_layout.addLayout(file_layout)

        # --- Module selection ---
        module_layout = QHBoxLayout()
        module_layout.addWidget(QLabel(self.tr("Target Module:")))
        self.module_combo = QComboBox()
        self._load_modules()
        module_layout.addWidget(self.module_combo)
        module_layout.addStretch()
        main_layout.addLayout(module_layout)

        # --- Preview area ---
        main_layout.addWidget(QLabel(self.tr("Import Preview:")))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText(self.tr("Select a Markdown file to preview questions..."))
        main_layout.addWidget(self.preview_text)

        # --- Progress bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()

        self.parse_btn = QPushButton(self.tr("Parse File"))
        self.parse_btn.setEnabled(False)
        self.parse_btn.clicked.connect(self.parse_file)
        btn_layout.addWidget(self.parse_btn)

        self.import_btn = QPushButton(self.tr("Import Questions"))
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self.import_questions)
        btn_layout.addWidget(self.import_btn)

        self.close_btn = QPushButton(self.tr("Close"))
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    def _load_modules(self):
        """Populate the module combo box."""
        try:
            for module_id, module_name in self.db.get_all_modules():
                self.module_combo.addItem(module_name, userData=module_id)
        except Exception as e:
            print(f"Failed to load modules: {e}")

    def browse_file(self):
        """Open file dialog to select a Markdown file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Markdown File"), "",
            self.tr("Markdown Files (*.md);;All Files (*)")
        )
        if file_path:
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("color: black;")
            self.parse_btn.setEnabled(True)
            self.current_file = file_path

    def parse_file(self):
        """Parse the selected Markdown file and show a preview."""
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                md_content = f.read()

            parser = MarkdownQuestionParser()
            self.questions_data = parser.parse_file(md_content)

            if not self.questions_data:
                QMessageBox.warning(self, self.tr("Parse Failed"),
                                    self.tr("No valid questions found in the file!"))
                return

            # Build preview text
            preview = self.tr("Successfully parsed %d questions\n\n") % len(self.questions_data)
            preview += "=" * 60 + "\n"

            for q in self.questions_data[:5]:
                preview += f"\n{self.tr('Question %d:') % q['question_number']}\n"
                preview += f"   {q['question_text'][:80]}...\n"
                preview += f"   {self.tr('Options: %d') % len(q['options'])}\n"
                preview += f"   {self.tr('Correct:')} {', '.join(q['correct_answers'])}\n"
                preview += f"   {self.tr('Chapter:')} {parser.get_chapter_from_content(q['related_content'])}\n"

            if len(self.questions_data) > 5:
                preview += f"\n{self.tr('... and %d more questions') % (len(self.questions_data) - 5)}"

            self.preview_text.setPlainText(preview)
            self.import_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Parse Error"),
                                 self.tr("Failed to parse file:\n%s") % str(e))

    def import_questions(self):
        """Execute batch import into the database."""
        module_id = self.module_combo.currentData()
        if not module_id:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Please select a target module!"))
            return

        reply = QMessageBox.question(
            self, self.tr("Confirm Import"),
            self.tr("Import %d questions to %s?\n\nDuplicate questions will be automatically skipped.") % (
                len(self.questions_data), self.module_combo.currentText()
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.import_btn.setEnabled(False)
        self.parse_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.questions_data))
        self.progress_bar.setValue(0)

        try:
            result = self.db.batch_insert_questions(self.questions_data, module_id)
            self._show_import_result(result)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Import Error"),
                                 self.tr("Import failed:\n%s") % str(e))
        finally:
            self.import_btn.setEnabled(True)
            self.parse_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _show_import_result(self, result):
        """Display import result summary."""
        message = self.tr(
            "Import Complete!\n\n"
            "Successfully imported: %d questions\n"
            "Skipped (duplicates): %d questions\n"
            "Failed: %d questions\n\n"
            "Total processed: %d"
        ) % (result['success'], result['skipped'], result['failed'],
             result['success'] + result['skipped'] + result['failed'])

        if result['failed'] > 0:
            message += "\n\n" + self.tr("Failed questions:\n")
            for detail in result['details']:
                if detail['status'] == 'failed':
                    message += self.tr("  - Question %d: %s\n") % (detail['index'], detail['reason'])

        QMessageBox.information(self, self.tr("Import Result"), message)

        # Reset UI state
        self.preview_text.clear()
        self.file_path_label.setText(self.tr("No file selected"))
        self.file_path_label.setStyleSheet("color: gray;")
        self.parse_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.questions_data = []

    def retranslate_ui(self):
        """Rebuild UI widgets for language switch while preserving state."""
        self.setWindowTitle(self.tr("Batch Import Questions from Markdown"))

        current_file = self.current_file
        current_module_idx = self.module_combo.currentIndex()
        saved_questions = self.questions_data.copy() if self.questions_data else []

        # Clear and rebuild widgets
        layout = self.layout()
        if layout:
            self._clear_layout_widgets(layout)

        self.questions_data = []
        self._setup_ui_widgets()

        # Restore state
        if current_file:
            self.current_file = current_file
            self.file_path_label.setText(current_file)
            self.file_path_label.setStyleSheet("color: black;")
            self.parse_btn.setEnabled(True)

        if 0 <= current_module_idx < self.module_combo.count():
            self.module_combo.setCurrentIndex(current_module_idx)

        if saved_questions:
            self.questions_data = saved_questions
            self.import_btn.setEnabled(True)

    def _clear_layout_widgets(self, layout):
        """Recursively remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout_widgets(item.layout())
