import os
import re
import glob
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QTableWidget, QTableWidgetItem, QPushButton, QComboBox,
    QLabel, QMessageBox, QInputDialog, QDialog, QFormLayout,
    QLineEdit, QCheckBox, QDialogButtonBox, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt, QCoreApplication, Signal
from src.core.db_manager import DBManager


class ExamManager(QWidget):
    """Admin window for managing exams, modules, and chapters."""

    exam_switched = Signal(str)  # emits db_path when switching to a new/different exam
    exam_renamed = Signal()      # emits when the current exam name is changed

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.current_module_id = None
        self._switching_exam = False
        self.init_ui()
        self.load_exam_combo()
        self.load_modules()
        self.resize(900, 600)
        self.setMinimumSize(700, 400)

    def tr(self, text):
        return QCoreApplication.translate("ExamManager", text)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Exam section ---
        exam_group = QGroupBox(self.tr("Exam"))
        exam_layout = QVBoxLayout(exam_group)

        # Exam selector row
        select_layout = QHBoxLayout()
        self.label_select_exam = QLabel(self.tr("Current Exam:"))
        select_layout.addWidget(self.label_select_exam)
        self.exam_combo = QComboBox()
        self.exam_combo.setMinimumWidth(250)
        self.exam_combo.currentIndexChanged.connect(self.on_exam_selected)
        select_layout.addWidget(self.exam_combo, 1)
        exam_layout.addLayout(select_layout)

        # Exam name edit row
        name_layout = QHBoxLayout()
        self.label_exam_name = QLabel(self.tr("Rename:"))
        name_layout.addWidget(self.label_exam_name)
        self.exam_name_edit = QLineEdit()
        self.exam_name_edit.setText(self.db.get_exam_name())
        name_layout.addWidget(self.exam_name_edit)
        self.save_name_btn = QPushButton(self.tr("Save"))
        self.save_name_btn.clicked.connect(self.save_exam_name)
        name_layout.addWidget(self.save_name_btn)
        exam_layout.addLayout(name_layout)

        # Exam action buttons
        exam_btn_layout = QHBoxLayout()
        self.new_exam_btn = QPushButton(self.tr("New Exam"))
        self.new_exam_btn.clicked.connect(self.create_new_exam)
        self.delete_exam_btn = QPushButton(self.tr("Delete Exam"))
        self.delete_exam_btn.clicked.connect(self.delete_exam)
        exam_btn_layout.addWidget(self.new_exam_btn)
        exam_btn_layout.addWidget(self.delete_exam_btn)
        exam_btn_layout.addStretch()
        exam_layout.addLayout(exam_btn_layout)

        main_layout.addWidget(exam_group)

        # --- Splitter: modules on left, chapters on right ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Modules
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.label_modules = QLabel(self.tr("Modules"))
        self.label_modules.setProperty("heading", "true")
        left_layout.addWidget(self.label_modules)

        self.module_list = QListWidget()
        self.module_list.currentRowChanged.connect(self.on_module_selected)
        left_layout.addWidget(self.module_list)

        mod_btn_layout = QHBoxLayout()
        self.add_module_btn = QPushButton(self.tr("Add"))
        self.add_module_btn.clicked.connect(self.add_module)
        self.rename_module_btn = QPushButton(self.tr("Rename"))
        self.rename_module_btn.clicked.connect(self.rename_module)
        self.delete_module_btn = QPushButton(self.tr("Delete"))
        self.delete_module_btn.clicked.connect(self.delete_module)
        mod_btn_layout.addWidget(self.add_module_btn)
        mod_btn_layout.addWidget(self.rename_module_btn)
        mod_btn_layout.addWidget(self.delete_module_btn)
        left_layout.addLayout(mod_btn_layout)

        splitter.addWidget(left_widget)

        # Right panel: Chapters
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.label_chapters = QLabel(self.tr("Chapters / Lessons"))
        self.label_chapters.setProperty("heading", "true")
        right_layout.addWidget(self.label_chapters)

        self.chapter_table = QTableWidget()
        self.chapter_table.setColumnCount(3)
        self.chapter_table.setHorizontalHeaderLabels([
            self.tr("Chapter #"), self.tr("Title"), self.tr("Main Chapter")
        ])
        self.chapter_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.chapter_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.chapter_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.chapter_table)

        ch_btn_layout = QHBoxLayout()
        self.add_chapter_btn = QPushButton(self.tr("Add"))
        self.add_chapter_btn.clicked.connect(self.add_chapter)
        self.edit_chapter_btn = QPushButton(self.tr("Edit"))
        self.edit_chapter_btn.clicked.connect(self.edit_chapter)
        self.delete_chapter_btn = QPushButton(self.tr("Delete"))
        self.delete_chapter_btn.clicked.connect(self.delete_chapter)
        ch_btn_layout.addWidget(self.add_chapter_btn)
        ch_btn_layout.addWidget(self.edit_chapter_btn)
        ch_btn_layout.addWidget(self.delete_chapter_btn)
        right_layout.addLayout(ch_btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

    # --- Exam operations ---

    def _get_data_dir(self) -> str:
        return os.path.dirname(self.db.db_path)

    def _get_available_exams(self) -> list[dict]:
        """Scan data/ folder for .db files and read exam names."""
        data_dir = self._get_data_dir()
        exams = []
        for db_file in sorted(glob.glob(os.path.join(data_dir, "*.db"))):
            name = os.path.splitext(os.path.basename(db_file))[0]
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM UserSettings WHERE key = 'exam_name'")
                row = cursor.fetchone()
                if row and row[0]:
                    name = row[0]
                conn.close()
            except Exception:
                pass
            exams.append({'path': db_file, 'name': name})
        return exams

    def load_exam_combo(self):
        """Populate the exam combo box with all available exams."""
        self.exam_combo.blockSignals(True)
        self.exam_combo.clear()
        self._exam_paths = []
        current_path = os.path.normpath(self.db.db_path)
        current_index = 0

        for i, exam in enumerate(self._get_available_exams()):
            self.exam_combo.addItem(exam['name'])
            self._exam_paths.append(exam['path'])
            if os.path.normpath(exam['path']) == current_path:
                current_index = i

        self.exam_combo.setCurrentIndex(current_index)
        self.exam_combo.blockSignals(False)

    def on_exam_selected(self, index):
        """Handle exam combo box selection change."""
        if index < 0 or index >= len(self._exam_paths) or self._switching_exam:
            return
        selected_path = self._exam_paths[index]
        if os.path.normpath(selected_path) == os.path.normpath(self.db.db_path):
            return
        self._switching_exam = True
        self.exam_switched.emit(selected_path)
        self._switching_exam = False

    def save_exam_name(self):
        name = self.exam_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Exam name cannot be empty."))
            return
        if self.db.set_exam_name(name):
            self.load_exam_combo()
            self.exam_renamed.emit()
            QMessageBox.information(self, self.tr("Saved"),
                                    self.tr("Exam name updated."))
        else:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Failed to save exam name."))

    def create_new_exam(self):
        """Create a new empty exam database and switch to it."""
        name, ok = QInputDialog.getText(
            self, self.tr("New Exam"),
            self.tr("Enter exam name:")
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        safe_name = re.sub(r'[^\w\s-]', '', name).replace(' ', '_')
        if not safe_name:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Invalid exam name."))
            return

        db_path = os.path.join(self._get_data_dir(), f"{safe_name}.db")
        if os.path.exists(db_path):
            QMessageBox.warning(
                self, self.tr("Error"),
                self.tr("An exam with this name already exists.")
            )
            return

        temp_db = DBManager(db_path)
        temp_db.set_exam_name(name)
        temp_db.close()

        self.exam_switched.emit(db_path)

    def delete_exam(self):
        """Delete the currently selected exam in the combo box."""
        index = self.exam_combo.currentIndex()
        if index < 0 or index >= len(self._exam_paths):
            return

        # Can't delete the last exam
        if len(self._exam_paths) <= 1:
            QMessageBox.warning(
                self, self.tr("Delete Exam"),
                self.tr("Cannot delete the only exam. Create another exam first.")
            )
            return

        selected_path = self._exam_paths[index]
        selected_name = self.exam_combo.currentText()
        is_active = os.path.normpath(selected_path) == os.path.normpath(self.db.db_path)

        reply = QMessageBox.warning(
            self, self.tr("Delete Exam"),
            self.tr("Permanently delete '%s'?\n\n"
                     "All questions, practice records, and data will be lost.\n"
                     "This cannot be undone.") % selected_name,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # If deleting the active exam, switch to another one first
        if is_active:
            other_path = next(
                p for p in self._exam_paths
                if os.path.normpath(p) != os.path.normpath(selected_path)
            )
            self.exam_switched.emit(other_path)

        try:
            os.remove(selected_path)
            self.load_exam_combo()
            QMessageBox.information(
                self, self.tr("Delete Exam"),
                self.tr("Exam '%s' has been deleted.") % selected_name
            )
        except OSError as e:
            QMessageBox.critical(
                self, self.tr("Error"),
                self.tr("Failed to delete exam: %s") % str(e)
            )

    # --- Module operations ---

    def load_modules(self):
        self.module_list.clear()
        self._module_data = []
        modules = self.db.get_visible_modules()

        if not modules:
            # Module-less exam: use hidden default module, show chapters directly
            default_id = self.db.get_or_create_default_module()
            self.current_module_id = default_id
            self.load_chapters()
        else:
            for module_id, module_name in modules:
                self.module_list.addItem(module_name)
                self._module_data.append(module_id)
            if self._module_data:
                self.module_list.setCurrentRow(0)

    def on_module_selected(self, row):
        if 0 <= row < len(self._module_data):
            self.current_module_id = self._module_data[row]
            self.load_chapters()
        else:
            self.current_module_id = None
            self.chapter_table.setRowCount(0)

    def add_module(self):
        name, ok = QInputDialog.getText(
            self, self.tr("Add Module"), self.tr("Module name:")
        )
        if not ok or not name.strip():
            return
        result = self.db.add_module(name.strip())
        if result is None:
            QMessageBox.warning(self, self.tr("Error"),
                                self.tr("Module already exists or failed to create."))
        else:
            self.load_modules()

    def rename_module(self):
        row = self.module_list.currentRow()
        if row < 0:
            return
        module_id = self._module_data[row]
        old_name = self.module_list.currentItem().text()
        name, ok = QInputDialog.getText(
            self, self.tr("Rename Module"), self.tr("New name:"), text=old_name
        )
        if ok and name.strip() and name.strip() != old_name:
            self.db.rename_module(module_id, name.strip())
            self.load_modules()

    def delete_module(self):
        row = self.module_list.currentRow()
        if row < 0:
            return
        module_id = self._module_data[row]
        module_name = self.module_list.currentItem().text()
        reply = QMessageBox.warning(
            self, self.tr("Delete Module"),
            self.tr("Delete module '%s'?\n\n"
                     "All chapters and associated question links will be removed.\n"
                     "This cannot be undone.") % module_name,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_module(module_id)
            self.load_modules()

    # --- Chapter operations ---

    def load_chapters(self):
        self.chapter_table.setRowCount(0)
        self._chapter_data = []
        if not self.current_module_id:
            return
        lessons = self.db.get_lessons_by_module(self.current_module_id)
        for lesson_id, chapter_num, chapter_title in lessons:
            row = self.chapter_table.rowCount()
            self.chapter_table.insertRow(row)
            self.chapter_table.setItem(row, 0, QTableWidgetItem(chapter_num))
            self.chapter_table.setItem(row, 1, QTableWidgetItem(chapter_title))

            is_main = chapter_num.endswith('.0')
            check_item = QTableWidgetItem()
            check_item.setCheckState(
                Qt.CheckState.Checked if is_main else Qt.CheckState.Unchecked
            )
            check_item.setFlags(check_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self.chapter_table.setItem(row, 2, check_item)

            self._chapter_data.append(lesson_id)

    def add_chapter(self):
        if not self.current_module_id:
            if not self._module_data:
                # Module-less exam: use default module
                self.current_module_id = self.db.get_or_create_default_module()
            else:
                QMessageBox.warning(self, self.tr("Error"),
                                    self.tr("Please select a module first."))
                return
        dialog = self._chapter_dialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            num = dialog.num_edit.text().strip()
            title = dialog.title_edit.text().strip()
            is_main = dialog.main_check.isChecked()
            if not num or not title:
                QMessageBox.warning(self, self.tr("Error"),
                                    self.tr("Chapter number and title are required."))
                return
            self.db.add_lesson(self.current_module_id, num, title, is_main)
            self.load_chapters()

    def edit_chapter(self):
        row = self.chapter_table.currentRow()
        if row < 0:
            return
        lesson_id = self._chapter_data[row]
        old_num = self.chapter_table.item(row, 0).text()
        old_title = self.chapter_table.item(row, 1).text()

        dialog = self._chapter_dialog(old_num, old_title)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            num = dialog.num_edit.text().strip()
            title = dialog.title_edit.text().strip()
            if not num or not title:
                return
            self.db.update_lesson(lesson_id, num, title)
            self.load_chapters()

    def delete_chapter(self):
        row = self.chapter_table.currentRow()
        if row < 0:
            return
        lesson_id = self._chapter_data[row]
        chapter_num = self.chapter_table.item(row, 0).text()
        chapter_title = self.chapter_table.item(row, 1).text()

        reply = QMessageBox.warning(
            self, self.tr("Delete Chapter"),
            self.tr("Delete chapter '%s %s'?\n\n"
                     "Associated question links will be removed.") % (chapter_num, chapter_title),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_lesson(lesson_id)
            self.load_chapters()

    def _chapter_dialog(self, num='', title='') -> QDialog:
        """Create a dialog for adding/editing a chapter."""
        dialog = QDialog(self)
        dialog.setWindowTitle(
            self.tr("Edit Chapter") if num else self.tr("Add Chapter")
        )
        layout = QFormLayout(dialog)

        dialog.num_edit = QLineEdit(num)
        dialog.num_edit.setPlaceholderText(self.tr("e.g. 1.0, 1.1, 2.3"))
        layout.addRow(self.tr("Chapter Number:"), dialog.num_edit)

        dialog.title_edit = QLineEdit(title)
        layout.addRow(self.tr("Chapter Title:"), dialog.title_edit)

        dialog.main_check = QCheckBox(self.tr("Main chapter (e.g. 1.0, 2.0)"))
        if num and num.endswith('.0'):
            dialog.main_check.setChecked(True)
        layout.addRow(dialog.main_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        return dialog

    def refresh_for_exam(self):
        """Refresh all data after an exam switch."""
        self.load_exam_combo()
        self.exam_name_edit.setText(self.db.get_exam_name())
        self.current_module_id = None
        self.load_modules()

    def retranslate_ui(self):
        self.label_select_exam.setText(self.tr("Current Exam:"))
        self.label_exam_name.setText(self.tr("Rename:"))
        self.save_name_btn.setText(self.tr("Save"))
        self.new_exam_btn.setText(self.tr("New Exam"))
        self.delete_exam_btn.setText(self.tr("Delete Exam"))
        self.label_modules.setText(self.tr("Modules"))
        self.label_chapters.setText(self.tr("Chapters / Lessons"))
        self.add_module_btn.setText(self.tr("Add"))
        self.rename_module_btn.setText(self.tr("Rename"))
        self.delete_module_btn.setText(self.tr("Delete"))
        self.add_chapter_btn.setText(self.tr("Add"))
        self.edit_chapter_btn.setText(self.tr("Edit"))
        self.delete_chapter_btn.setText(self.tr("Delete"))
        self.chapter_table.setHorizontalHeaderLabels([
            self.tr("Chapter #"), self.tr("Title"), self.tr("Main Chapter")
        ])
