from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QTextEdit,
    QCheckBox, QRadioButton, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QColor
from src.core.db_manager import DBManager


class QuestionEditDialog(QDialog):
    """Dialog for editing an existing question."""

    def __init__(self, db_manager: DBManager, question_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.question_id = question_id
        self.option_widgets = []

        self.setWindowTitle(self.tr("Edit Question") if question_id else self.tr("New Question"))
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.resize(700, 600)
        self.setMinimumSize(600, 500)
        self.setSizeGripEnabled(True)

        self.init_ui()
        if question_id:
            self.load_question_data()
        else:
            for _ in range(4):
                self.add_option()

    def tr(self, text):
        return QCoreApplication.translate("QuestionEditDialog", text)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Question text
        layout.addWidget(QLabel(self.tr("Question Text:")))
        self.question_text = QTextEdit()
        self.question_text.setMinimumHeight(120)
        self.question_text.setMaximumHeight(300)
        layout.addWidget(self.question_text)

        # Question type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel(self.tr("Question Type:")))
        self.type_mc = QRadioButton(self.tr("Single Choice (MC)"))
        self.type_mr = QRadioButton(self.tr("Multiple Choice (MR)"))
        self.type_mc.setChecked(True)
        type_layout.addWidget(self.type_mc)
        type_layout.addWidget(self.type_mr)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Options area
        options_group = QGroupBox(self.tr("Answer Options"))
        options_layout = QVBoxLayout(options_group)
        self.options_container = QVBoxLayout()
        options_layout.addLayout(self.options_container)

        btn_layout = QHBoxLayout()
        self.add_option_btn = QPushButton(self.tr("+ Add Option"))
        self.add_option_btn.clicked.connect(self.add_option)
        btn_layout.addWidget(self.add_option_btn)
        btn_layout.addStretch()
        options_layout.addLayout(btn_layout)
        layout.addWidget(options_group)

        # Explanation
        layout.addWidget(QLabel(self.tr("Explanation:")))
        self.explanation_text = QTextEdit()
        self.explanation_text.setMinimumHeight(100)
        self.explanation_text.setMaximumHeight(200)
        layout.addWidget(self.explanation_text)

        # Flag checkbox
        self.flagged_check = QCheckBox(self.tr("Mark as Important/Flagged"))
        layout.addWidget(self.flagged_check)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(self.tr("Save"))
        self.save_btn.clicked.connect(self.save_question)
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def add_option(self):
        """Add an option row."""
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 0, 0, 0)

        check = QCheckBox(self.tr("Correct"))
        text = QLineEdit()
        text.setPlaceholderText(self.tr("Enter option text..."))
        remove_btn = QPushButton(self.tr("Remove"))
        remove_btn.clicked.connect(lambda: self.remove_option(option_widget))

        option_layout.addWidget(check)
        option_layout.addWidget(text, 1)
        option_layout.addWidget(remove_btn)

        self.options_container.addWidget(option_widget)
        self.option_widgets.append({'widget': option_widget, 'check': check, 'text': text})

    def remove_option(self, widget):
        """Remove an option row."""
        for item in self.option_widgets:
            if item['widget'] == widget:
                self.option_widgets.remove(item)
                widget.deleteLater()
                break

    def load_question_data(self):
        """Load question data into the form."""
        question = self.db.get_question_with_answers(self.question_id)
        if not question:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to load question data."))
            self.reject()
            return

        self.question_text.setPlainText(question['question_text'])
        (self.type_mr if question['question_type'] == 'MR' else self.type_mc).setChecked(True)
        self.explanation_text.setPlainText(question.get('explanation', ''))
        self.flagged_check.setChecked(question['is_flagged'])

        # Clear default options and load actual ones
        for item in self.option_widgets[:]:
            item['widget'].deleteLater()
        self.option_widgets.clear()

        for answer in question['answers']:
            self.add_option()
            last = self.option_widgets[-1]
            last['text'].setText(answer['option_text'])
            last['check'].setChecked(answer['is_correct'])

    def save_question(self):
        """Validate and save question to database."""
        question_text = self.question_text.toPlainText().strip()
        if not question_text:
            QMessageBox.warning(self, self.tr("Validation Error"),
                                self.tr("Question text cannot be empty."))
            return

        answers_data = []
        has_correct = False
        for item in self.option_widgets:
            option_text = item['text'].text().strip()
            if not option_text:
                continue
            is_correct = item['check'].isChecked()
            if is_correct:
                has_correct = True
            answers_data.append({
                'option_text': option_text,
                'is_correct': 1 if is_correct else 0
            })

        if len(answers_data) < 2:
            QMessageBox.warning(self, self.tr("Validation Error"),
                                self.tr("At least 2 options are required."))
            return
        if not has_correct:
            QMessageBox.warning(self, self.tr("Validation Error"),
                                self.tr("At least one correct answer must be marked."))
            return

        question_data = {
            'question_text': question_text,
            'explanation': self.explanation_text.toPlainText().strip(),
            'question_type': 'MR' if self.type_mr.isChecked() else 'MC',
            'is_flagged': 1 if self.flagged_check.isChecked() else 0
        }

        if self.question_id:
            success = self.db.update_question(self.question_id, question_data, answers_data)
            if success:
                QMessageBox.information(self, self.tr("Success"),
                                        self.tr("Question updated successfully."))
                self.accept()
            else:
                QMessageBox.critical(self, self.tr("Error"),
                                     self.tr("Failed to update question."))
        else:
            QMessageBox.information(self, self.tr("Info"),
                                    self.tr("Creating new questions should use the dedicated entry form."))


class QuestionManagerWindow(QWidget):
    """Question list management with search, filter, edit, and delete."""

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        self.init_ui()
        self.load_filter_data()
        self.refresh_table()

    def tr(self, text):
        return QCoreApplication.translate("QuestionManagerWindow", text)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Filter area ---
        self.filter_group = QGroupBox(self.tr("Filter Options"))
        filter_layout = QGridLayout(self.filter_group)

        self.label_module = QLabel(self.tr("Module:"))
        filter_layout.addWidget(self.label_module, 0, 0)
        self.module_combo = QComboBox()
        self.module_combo.currentIndexChanged.connect(self.on_module_changed)
        filter_layout.addWidget(self.module_combo, 0, 1)

        self.label_chapter = QLabel(self.tr("Chapter:"))
        filter_layout.addWidget(self.label_chapter, 0, 2)
        self.chapter_combo = QComboBox()
        filter_layout.addWidget(self.chapter_combo, 0, 3)

        self.label_search = QLabel(self.tr("Search:"))
        filter_layout.addWidget(self.label_search, 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Enter keywords to search in question text..."))
        filter_layout.addWidget(self.search_input, 1, 1, 1, 3)

        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton(self.tr("Search"))
        self.search_btn.clicked.connect(self.refresh_table)
        self.reset_btn = QPushButton(self.tr("Reset Filters"))
        self.reset_btn.clicked.connect(self.reset_filters)
        btn_layout.addWidget(self.search_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        filter_layout.addLayout(btn_layout, 2, 0, 1, 4)

        layout.addWidget(self.filter_group)

        # --- Question table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Question Preview"), self.tr("Type"),
            self.tr("Flagged"), self.tr("Module"), self.tr("Chapter"), self.tr("Actions")
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3, 4, 5, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # --- Pagination ---
        bottom_layout = QHBoxLayout()
        self.info_label = QLabel()
        bottom_layout.addWidget(self.info_label)
        bottom_layout.addStretch()

        self.prev_btn = QPushButton(self.tr("Previous Page"))
        self.prev_btn.clicked.connect(self.prev_page)
        bottom_layout.addWidget(self.prev_btn)

        self.page_label = QLabel()
        bottom_layout.addWidget(self.page_label)

        self.next_btn = QPushButton(self.tr("Next Page"))
        self.next_btn.clicked.connect(self.next_page)
        bottom_layout.addWidget(self.next_btn)

        layout.addLayout(bottom_layout)

    def load_filter_data(self):
        """Load module and chapter filter dropdowns."""
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        self.module_combo.addItem(self.tr("--- All Modules ---"), userData=None)
        for module_id, module_name in self.db.get_all_modules():
            self.module_combo.addItem(module_name, userData=module_id)
        self.module_combo.blockSignals(False)
        self.load_chapters()

    def load_chapters(self):
        """Load chapter dropdown based on selected module."""
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.addItem(self.tr("--- All Chapters ---"), userData=None)

        module_id = self.module_combo.currentData()
        if module_id:
            for _, chapter_num, chapter_title in self.db.get_lessons_by_module(module_id):
                self.chapter_combo.addItem(f"{chapter_num}: {chapter_title}", userData=chapter_num)

        self.chapter_combo.blockSignals(False)

    def on_module_changed(self):
        self.load_chapters()
        self.refresh_table()

    def reset_filters(self):
        self.module_combo.setCurrentIndex(0)
        self.chapter_combo.setCurrentIndex(0)
        self.search_input.clear()
        self.current_page = 0
        self.refresh_table()

    def refresh_table(self):
        self.current_page = 0
        self.load_table_data()

    def load_table_data(self):
        """Fetch and display question data in the table."""
        module_id = self.module_combo.currentData()
        chapter_num = self.chapter_combo.currentData()
        search_text = self.search_input.text().strip() or None
        offset = self.current_page * self.page_size

        questions = self.db.get_questions_list(
            module_id=module_id, chapter_num=chapter_num,
            search_text=search_text, offset=offset, limit=self.page_size
        )
        self.total_count = self.db.get_total_questions_count(
            module_id=module_id, chapter_num=chapter_num, search_text=search_text
        )

        self.table.setRowCount(len(questions))
        for row, q in enumerate(questions):
            self.table.setItem(row, 0, QTableWidgetItem(str(q['question_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(q['question_text']))

            type_text = self.tr("Multiple") if q['question_type'] == 'MR' else self.tr("Single")
            self.table.setItem(row, 2, QTableWidgetItem(type_text))

            flag_item = QTableWidgetItem("*" if q['is_flagged'] else "")
            flag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if q['is_flagged']:
                flag_item.setForeground(QColor(255, 165, 0))
            self.table.setItem(row, 3, flag_item)

            self.table.setItem(row, 4, QTableWidgetItem(q['module_name']))
            self.table.setItem(row, 5, QTableWidgetItem(q['chapter_num']))

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton(self.tr("Edit"))
            edit_btn.setFixedSize(70, 28)
            edit_btn.clicked.connect(lambda checked, qid=q['question_id']: self.edit_question(qid))

            delete_btn = QPushButton(self.tr("Delete"))
            delete_btn.setFixedSize(70, 28)
            delete_btn.clicked.connect(lambda checked, qid=q['question_id']: self.delete_question(qid))

            actions_layout.addStretch()
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            self.table.setCellWidget(row, 6, actions_widget)

        self.update_pagination_info()

    def update_pagination_info(self):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        current_display = self.current_page + 1 if self.total_count > 0 else 0

        self.info_label.setText(self.tr("Total: %s questions") % self.total_count)
        self.page_label.setText(self.tr("Page %s / %s") % (current_display, total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled((self.current_page + 1) * self.page_size < self.total_count)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_table_data()

    def next_page(self):
        if (self.current_page + 1) * self.page_size < self.total_count:
            self.current_page += 1
            self.load_table_data()

    def edit_question(self, question_id: int):
        dialog = QuestionEditDialog(self.db, question_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data()

    def delete_question(self, question_id: int):
        reply = QMessageBox.question(
            self, self.tr("Confirm Deletion"),
            self.tr("Are you sure you want to delete question ID %s?\n"
                     "This action cannot be undone.") % question_id,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_question(question_id):
                QMessageBox.information(self, self.tr("Success"),
                                        self.tr("Question deleted successfully."))
                self.load_table_data()
            else:
                QMessageBox.critical(self, self.tr("Error"),
                                     self.tr("Failed to delete question."))

    def retranslate_ui(self):
        """Update all widget texts for language switch."""
        self.filter_group.setTitle(self.tr("Filter Options"))
        self.label_module.setText(self.tr("Module:"))
        self.label_chapter.setText(self.tr("Chapter:"))
        self.label_search.setText(self.tr("Search:"))
        self.search_input.setPlaceholderText(self.tr("Enter keywords to search in question text..."))
        self.search_btn.setText(self.tr("Search"))
        self.reset_btn.setText(self.tr("Reset Filters"))

        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Question Preview"), self.tr("Type"),
            self.tr("Flagged"), self.tr("Module"), self.tr("Chapter"), self.tr("Actions")
        ])

        self.prev_btn.setText(self.tr("Previous Page"))
        self.next_btn.setText(self.tr("Next Page"))

        self.load_filter_data()
        self.load_table_data()
