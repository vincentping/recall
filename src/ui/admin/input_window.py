from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTextEdit, QLineEdit, QComboBox, QPushButton,
    QLabel, QCheckBox, QRadioButton, QMessageBox,
    QSpinBox
)
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from src.core.db_manager import DBManager


class InputWindow(QWidget):
    """Manual question entry form."""

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.answers_widgets = []
        self.init_ui()
        self.load_metadata()
        self.resize(850, 700)
        self.setMinimumSize(800, 650)

    def tr(self, text):
        return QCoreApplication.translate("InputWindow", text)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Metadata area ---
        meta_group = QWidget()
        meta_layout = QGridLayout(meta_group)

        self.label_module = QLabel(self.tr("Knowledge Module:"))
        meta_layout.addWidget(self.label_module, 0, 0)
        self.module_combo = QComboBox()
        meta_layout.addWidget(self.module_combo, 0, 1)

        self.label_lesson = QLabel(self.tr("Chapter/Lesson:"))
        meta_layout.addWidget(self.label_lesson, 0, 2)
        self.lesson_combo = QComboBox()
        meta_layout.addWidget(self.lesson_combo, 0, 3)

        self.label_type = QLabel(self.tr("Question Type:"))
        meta_layout.addWidget(self.label_type, 1, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems([self.tr('MC (Single Choice)'), self.tr('MR (Multiple Choice)')])
        self.type_combo.currentIndexChanged.connect(self.update_answer_widgets)
        meta_layout.addWidget(self.type_combo, 1, 1)

        self.label_option_count = QLabel(self.tr("Number of Options:"))
        meta_layout.addWidget(self.label_option_count, 1, 2)
        self.option_count_spin = QSpinBox()
        self.option_count_spin.setRange(2, 8)
        self.option_count_spin.setValue(4)
        self.option_count_spin.valueChanged.connect(self.update_answer_widgets)
        meta_layout.addWidget(self.option_count_spin, 1, 3)

        self.module_combo.currentIndexChanged.connect(self.load_lessons)

        self.flag_check = QCheckBox(self.tr("Flag for Review"))
        meta_layout.addWidget(self.flag_check, 2, 3, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(meta_group)
        main_layout.addSpacing(10)

        # --- Question text and explanation ---
        self.label_question = QLabel(self.tr("Question Text:"))
        main_layout.addWidget(self.label_question)
        self.question_text = QTextEdit()
        self.question_text.setMinimumHeight(100)
        self.question_text.setMaximumHeight(200)
        self.question_text.installEventFilter(self)
        main_layout.addWidget(self.question_text)

        self.label_explanation = QLabel(self.tr("Explanation:"))
        main_layout.addWidget(self.label_explanation)
        self.explanation_text = QTextEdit()
        self.explanation_text.setMinimumHeight(60)
        self.explanation_text.setMaximumHeight(150)
        main_layout.addWidget(self.explanation_text)
        main_layout.addSpacing(10)

        # --- Options input area ---
        self.label_options = QLabel(self.tr("Option Input:"))
        main_layout.addWidget(self.label_options)
        self.options_group = QWidget()
        self.options_layout = QGridLayout(self.options_group)
        self.options_layout.setColumnStretch(0, 0)
        self.options_layout.setColumnStretch(1, 1)
        self.options_layout.setColumnStretch(2, 0)
        self.options_layout.setHorizontalSpacing(8)
        self.setup_answer_fields(num=4)
        main_layout.addWidget(self.options_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(self.tr("Save Question (Ctrl+S)"))
        self.clear_btn = QPushButton(self.tr("Clear Form"))
        self.save_btn.clicked.connect(self.save_question)
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(btn_layout)

        self.save_btn.setShortcut("Ctrl+S")

    def setup_answer_fields(self, num=4):
        """Create option input fields, preserving existing content."""
        # Save existing content
        old_data = [
            {'text': ws['text'].text(), 'correct': ws['correct'].isChecked()}
            for ws in self.answers_widgets
        ]

        # Clear existing widgets
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.answers_widgets.clear()

        is_mc = self.type_combo.currentText().startswith(self.tr('MC'))

        for i in range(num):
            label = QLabel(f"{chr(65 + i)}.")
            label.setFixedWidth(20)

            text_edit = QLineEdit()
            text_edit.setPlaceholderText(self.tr("Option %s...") % chr(65 + i))

            correct_widget = QRadioButton() if is_mc else QCheckBox()
            correct_widget.setFixedWidth(30)

            # Restore previous content if available
            if i < len(old_data):
                text_edit.setText(old_data[i]['text'])
                correct_widget.setChecked(old_data[i]['correct'])

            self.options_layout.addWidget(label, i, 0)
            self.options_layout.addWidget(text_edit, i, 1)
            self.options_layout.addWidget(correct_widget, i, 2)

            self.answers_widgets.append({'text': text_edit, 'correct': correct_widget})

    def update_answer_widgets(self, _index=None):
        """Rebuild answer widgets when type or count changes."""
        self.setup_answer_fields(num=self.option_count_spin.value())

    def clear_form(self):
        self.question_text.clear()
        self.explanation_text.clear()
        self.flag_check.setChecked(False)
        self.type_combo.setCurrentIndex(0)

        for ws in self.answers_widgets:
            ws['text'].clear()
            if isinstance(ws['correct'], QRadioButton):
                ws['correct'].setAutoExclusive(False)
                ws['correct'].setChecked(False)
                ws['correct'].setAutoExclusive(True)
            else:
                ws['correct'].setChecked(False)

        QMessageBox.information(
            self, self.tr("Operation Success"),
            self.tr("Form content has been cleared. Start entering the next question."),
            QMessageBox.StandardButton.Ok
        )

    def load_metadata(self):
        self.module_combo.clear()
        try:
            for module_id, module_name in self.db.get_all_modules():
                self.module_combo.addItem(module_name, userData=module_id)
        except Exception as e:
            print(f"Failed to load modules: {e}")
        self.load_lessons(0)

    def load_lessons(self, index):
        self.lesson_combo.clear()
        module_id = self.module_combo.currentData()
        if not module_id:
            return
        try:
            for lesson_id, chapter_num, chapter_title in self.db.get_lessons_by_module(module_id):
                self.lesson_combo.addItem(f"{chapter_num} {chapter_title}", userData=lesson_id)
        except Exception as e:
            print(f"Failed to load lessons: {e}")

    def save_question(self):
        question_text_raw = self.question_text.toPlainText().strip()
        if not question_text_raw:
            QMessageBox.warning(self, self.tr("Input Error"),
                                self.tr("Question text cannot be empty!"))
            return

        selected_lesson_id = self.lesson_combo.currentData()
        if not selected_lesson_id:
            QMessageBox.warning(self, self.tr("Input Error"),
                                self.tr("Please select a valid chapter/lesson affiliation!"))
            return

        a_data = []
        correct_count = 0
        all_options_empty = True

        for ws in self.answers_widgets:
            option_text = ws['text'].text().strip()
            is_correct = 1 if ws['correct'].isChecked() else 0
            if option_text:
                all_options_empty = False
                a_data.append({'option_text': option_text, 'is_correct': is_correct})
                correct_count += is_correct

        if all_options_empty:
            QMessageBox.warning(self, self.tr("Input Error"),
                                self.tr("Please enter at least one option."))
            return
        if correct_count == 0:
            QMessageBox.warning(self, self.tr("Input Error"),
                                self.tr("You must mark at least one correct answer."))
            return

        q_data = {
            'question_text': question_text_raw,
            'explanation': self.explanation_text.toPlainText().strip(),
            'question_type': self.type_combo.currentText()[:2],
            'is_flagged': 1 if self.flag_check.isChecked() else 0
        }

        new_id = self.db.insert_full_question(q_data, a_data, selected_lesson_id)
        if new_id:
            QMessageBox.information(self, self.tr("Entry Success"),
                                    self.tr("Question ID: %s has been successfully saved!") % new_id)
            self.clear_form()
        else:
            QMessageBox.critical(self, self.tr("Entry Failed"),
                                 self.tr("Database operation failed. Check console for error details."))

    def eventFilter(self, obj, event):
        """Check for duplicate questions when question_text loses focus."""
        if obj == self.question_text and event.type() == QEvent.Type.FocusOut:
            question_text = self.question_text.toPlainText().strip()
            if question_text and self.db.check_duplicate_question(question_text):
                QMessageBox.warning(
                    self,
                    self.tr("Potential Duplicate Question Found"),
                    self.tr("A question with exactly the same text already exists in the database!\n"
                            "Please verify before proceeding."))
        return super().eventFilter(obj, event)

    def retranslate_ui(self):
        """Update all widget texts for language switch."""
        self.label_module.setText(self.tr("Knowledge Module:"))
        self.label_lesson.setText(self.tr("Chapter/Lesson:"))
        self.label_type.setText(self.tr("Question Type:"))
        self.label_option_count.setText(self.tr("Number of Options:"))
        self.label_question.setText(self.tr("Question Text:"))
        self.label_explanation.setText(self.tr("Explanation:"))
        self.label_options.setText(self.tr("Option Input:"))
        self.flag_check.setText(self.tr("Flag for Review"))
        self.save_btn.setText(self.tr("Save Question (Ctrl+S)"))
        self.clear_btn.setText(self.tr("Clear Form"))

        # Refresh type combo while preserving selection
        current_type_index = self.type_combo.currentIndex()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        self.type_combo.addItems([self.tr('MC (Single Choice)'), self.tr('MR (Multiple Choice)')])
        self.type_combo.setCurrentIndex(current_type_index)
        self.type_combo.blockSignals(False)

        # Reload modules/lessons while preserving selection
        current_module_data = self.module_combo.currentData()
        self.load_metadata()
        if current_module_data:
            index = self.module_combo.findData(current_module_data)
            if index != -1:
                self.module_combo.setCurrentIndex(index)

        self.setup_answer_fields(num=len(self.answers_widgets) if self.answers_widgets else 4)
