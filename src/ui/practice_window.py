import time
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QRadioButton, QCheckBox, QScrollArea,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QCoreApplication, Signal, QTimer
from src.core.db_manager import DBManager


class PracticeWindow(QWidget):
    """Answer interface supporting both learning and exam modes."""

    practice_finished = Signal(dict)
    practice_cancelled = Signal()
    no_questions = Signal()

    def __init__(self, db_manager: DBManager, practice_config: dict):
        super().__init__()
        self.db = db_manager
        self.config = practice_config
        self.mode = practice_config.get('mode', 'learn')

        # State
        self.question_ids: list[int] = []
        self.current_index: int = 0
        self.user_answers: dict[int, str] = {}
        self.checked_set: set[int] = set()
        self.results: dict[int, bool] = {}
        self.time_per_question: dict[int, int] = {}
        self.practice_marks: set[int] = set()
        self.question_start_time: float = 0
        self.session_id: int | None = None
        self.question_cache: dict[int, dict] = {}
        self.option_order_cache: dict[int, list] = {}

        # Exam timer
        self.remaining_seconds: int = 0
        self.exam_timer: QTimer | None = None

        self.init_ui()
        # Note: load_questions() is called by MainWindow after signals are connected

    def tr(self, text):
        return QCoreApplication.translate("PracticeWindow", text)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Top bar ---
        top_layout = QHBoxLayout()
        self.progress_label = QLabel()
        self.mode_label = QLabel()
        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top_layout.addWidget(self.progress_label)
        top_layout.addWidget(self.mode_label)
        top_layout.addStretch()
        top_layout.addWidget(self.timer_label)
        main_layout.addLayout(top_layout)

        if self.mode != 'exam':
            self.timer_label.hide()

        # --- Question display ---
        self.question_group = QGroupBox(self.tr("Question"))
        question_layout = QVBoxLayout(self.question_group)

        self.question_display = QTextEdit()
        self.question_display.setReadOnly(True)
        self.question_display.setMinimumHeight(80)
        self.question_display.setMaximumHeight(300)
        question_layout.addWidget(self.question_display)

        main_layout.addWidget(self.question_group)

        # --- Options area ---
        self.options_container = QWidget()
        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.options_container)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(300)
        main_layout.addWidget(scroll_area)

        # --- Explanation area (learning mode only) ---
        self.explanation_group = QGroupBox(self.tr("Explanation"))
        explanation_layout = QVBoxLayout(self.explanation_group)
        self.explanation_display = QTextEdit()
        self.explanation_display.setReadOnly(True)
        self.explanation_display.setMaximumHeight(150)
        explanation_layout.addWidget(self.explanation_display)
        main_layout.addWidget(self.explanation_group)
        self.explanation_group.hide()

        # --- Bottom bar ---
        bottom_layout = QHBoxLayout()

        self.mark_btn = QPushButton(self.tr("Mark"))
        self.mark_btn.clicked.connect(self.toggle_mark)

        self.check_btn = QPushButton(self.tr("Check"))
        self.check_btn.clicked.connect(self.check_answer)

        self.prev_btn = QPushButton(self.tr("Previous"))
        self.prev_btn.clicked.connect(self.go_previous)

        self.next_btn = QPushButton(self.tr("Next"))
        self.next_btn.clicked.connect(self.go_next)

        self.submit_btn = QPushButton(self.tr("Submit"))
        self.submit_btn.clicked.connect(self.finish_practice)

        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.clicked.connect(self.cancel_practice)

        if self.mode == 'exam':
            bottom_layout.addWidget(self.mark_btn)
        if self.mode == 'learn':
            bottom_layout.addWidget(self.check_btn)
        bottom_layout.addWidget(self.prev_btn)
        bottom_layout.addWidget(self.next_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cancel_btn)
        bottom_layout.addWidget(self.submit_btn)
        self.submit_btn.hide()

        main_layout.addLayout(bottom_layout)

        self.option_widgets: list[QRadioButton | QCheckBox] = []

    def load_questions(self):
        """Load question IDs based on practice config and start the session."""
        config = self.config

        if config.get('question_ids'):
            # Retry wrong questions mode
            self.question_ids = config['question_ids']
        else:
            # Normal mode: draw from DB
            module_id = config.get('module_id')
            chapter_numbers = config.get('chapter_numbers')
            count = config.get('count', 20)
            flagged_only = config.get('flagged_only', False)

            if config.get('wrong_only', False):
                self.question_ids = self.db.get_wrong_question_ids(
                    module_id=module_id, chapter_numbers=chapter_numbers, limit=count
                )
            else:
                self.question_ids = self.db.get_random_question_ids(
                    module_id, chapter_numbers, count, flagged_only
                )

            # If a filter produced fewer questions than requested, pad with random ones
            shortage = count - len(self.question_ids)
            if shortage > 0 and (config.get('wrong_only') or flagged_only):
                extra = self.db.get_random_question_ids(
                    module_id, chapter_numbers, shortage,
                    is_flagged=False, exclude_ids=self.question_ids
                )
                self.question_ids = self.question_ids + extra
                random.shuffle(self.question_ids)

        if not self.question_ids:
            self.no_questions.emit()
            return

        # Create DB session
        self.session_id = self.db.create_practice_session(
            module_id=config.get('module_id'),
            mode=self.mode,
            total_count=len(self.question_ids)
        )

        # Start exam timer if needed — 1 minute per actual question loaded
        if self.mode == 'exam':
            time_limit = len(self.question_ids)
            self.remaining_seconds = time_limit * 60
            self.exam_timer = QTimer(self)
            self.exam_timer.timeout.connect(self.tick_timer)
            self.exam_timer.start(1000)
            self.update_timer_display()

        self.current_index = 0
        self.display_question()

    def display_question(self):
        """Display the current question."""
        self.save_time_for_current()

        q_id = self.question_ids[self.current_index]

        # Load from cache or DB
        if q_id not in self.question_cache:
            q_data = self.db.get_question_with_answers(q_id)
            if not q_data:
                self.question_display.setText(self.tr("Error loading question ID %s") % q_id)
                return
            self.question_cache[q_id] = q_data
            # Shuffle and cache option order
            answers = list(q_data['answers'])
            random.shuffle(answers)
            self.option_order_cache[q_id] = answers

        q_data = self.question_cache[q_id]
        answers = self.option_order_cache[q_id]

        # Update top bar
        self.progress_label.setText(
            self.tr("Question %d / %d") % (self.current_index + 1, len(self.question_ids))
        )
        mode_text = self.tr("Learning Mode") if self.mode == 'learn' else self.tr("Exam Simulation")
        self.mode_label.setText(mode_text)

        # Update prev/next/submit button states
        self.prev_btn.setEnabled(self.current_index > 0)
        is_last = self.current_index >= len(self.question_ids) - 1
        self.next_btn.setEnabled(not is_last)
        self.submit_btn.setVisible(is_last)

        # Question text
        type_hint = self.tr("Single Choice") if q_data['question_type'] == 'MC' \
            else self.tr("Multiple Response - select all that apply")
        self.question_display.setText(f"{q_data['question_text']}\n\n({type_hint})")

        # Options
        self.clear_options()
        is_checked = q_id in self.checked_set
        WidgetClass = QRadioButton if q_data['question_type'] == 'MC' else QCheckBox

        for i, answer in enumerate(answers):
            option_label = chr(ord('A') + i)
            option_text = f"{option_label}. {answer['option_text']}"
            widget = WidgetClass(option_text)
            widget.setProperty('answer_id', answer['answer_id'])
            widget.setProperty('is_correct', answer['is_correct'])
            widget.setProperty('option_label', option_label)

            # Restore previous selection
            saved = self.user_answers.get(q_id, '')
            if option_label in saved.split(','):
                widget.setChecked(True)

            # If checked (learning mode), show result styling and disable
            if is_checked:
                widget.setEnabled(False)
                if answer['is_correct']:
                    widget.setProperty("result", "correct")
                elif option_label in saved.split(',') and not answer['is_correct']:
                    widget.setProperty("result", "incorrect")
                widget.style().unpolish(widget)
                widget.style().polish(widget)

            self.options_layout.addWidget(widget)
            self.option_widgets.append(widget)

        # Explanation area
        if is_checked and self.mode == 'learn':
            explanation = q_data.get('explanation') or self.tr("No explanation provided")
            self.explanation_display.setText(explanation)
            self.explanation_group.show()
        else:
            self.explanation_group.hide()

        # Check button state
        if self.mode == 'learn':
            self.check_btn.setEnabled(not is_checked)

        # Mark button
        if q_id in self.practice_marks:
            self.mark_btn.setText(self.tr("Marked"))
        else:
            self.mark_btn.setText(self.tr("Mark"))

        # Record start time for this question
        self.question_start_time = time.time()

    def clear_options(self):
        self.option_widgets = []
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_selected_answer(self) -> str:
        """Get the currently selected answer as a string like 'B' or 'A,C'."""
        selected = []
        for widget in self.option_widgets:
            if widget.isChecked():
                selected.append(widget.property('option_label'))
        return ','.join(sorted(selected))

    def save_current_answer(self):
        """Save current selection to user_answers dict."""
        if not self.question_ids:
            return
        q_id = self.question_ids[self.current_index]
        answer = self.get_selected_answer()
        if answer:
            self.user_answers[q_id] = answer

    def save_time_for_current(self):
        """Save time spent on current question."""
        if self.question_start_time and self.question_ids:
            q_id = self.question_ids[self.current_index]
            elapsed = int(time.time() - self.question_start_time)
            self.time_per_question[q_id] = self.time_per_question.get(q_id, 0) + elapsed
            self.question_start_time = 0

    def check_answer(self):
        """Check the current answer (learning mode only)."""
        q_id = self.question_ids[self.current_index]
        answer = self.get_selected_answer()

        if not answer:
            QMessageBox.information(
                self, self.tr("Notice"),
                self.tr("Please select an answer first")
            )
            return

        self.user_answers[q_id] = answer
        self.save_time_for_current()

        # Determine correctness
        q_data = self.question_cache[q_id]
        correct_labels = []
        for i, ans in enumerate(self.option_order_cache[q_id]):
            if ans['is_correct']:
                correct_labels.append(chr(ord('A') + i))
        correct_answer = ','.join(sorted(correct_labels))
        is_correct = (answer == correct_answer)

        self.results[q_id] = is_correct
        self.checked_set.add(q_id)

        # Save to DB
        if self.session_id:
            self.db.save_answer_record(
                self.session_id, q_id, answer, is_correct,
                self.time_per_question.get(q_id, 0)
            )

        # Update UI: disable options and show result styling
        for widget in self.option_widgets:
            widget.setEnabled(False)
            opt_label = widget.property('option_label')
            if widget.property('is_correct'):
                widget.setProperty("result", "correct")
            elif opt_label in answer.split(',') and not widget.property('is_correct'):
                widget.setProperty("result", "incorrect")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self.check_btn.setEnabled(False)

        # Show explanation
        explanation = q_data.get('explanation') or self.tr("No explanation provided")
        self.explanation_display.setText(explanation)
        self.explanation_group.show()

        # Reset start time for continued viewing
        self.question_start_time = time.time()

    def go_previous(self):
        if self.current_index > 0:
            self.save_current_answer()
            self.current_index -= 1
            self.display_question()

    def go_next(self):
        if self.current_index < len(self.question_ids) - 1:
            self.save_current_answer()
            self.current_index += 1
            self.display_question()

    def toggle_mark(self):
        if not self.question_ids:
            return
        q_id = self.question_ids[self.current_index]
        if q_id in self.practice_marks:
            self.practice_marks.discard(q_id)
            self.mark_btn.setText(self.tr("Mark"))
        else:
            self.practice_marks.add(q_id)
            self.mark_btn.setText(self.tr("Marked"))

    def tick_timer(self):
        """Called every second in exam mode."""
        self.remaining_seconds -= 1
        self.update_timer_display()

        if self.remaining_seconds <= 0:
            if self.exam_timer:
                self.exam_timer.stop()
            reply = QMessageBox.information(
                self, self.tr("Time's Up"),
                self.tr("Time's up! Your answers will be submitted."),
                QMessageBox.StandardButton.Ok
            )
            self.submit_exam()

    def update_timer_display(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(self.tr("Time Remaining: %s") % f"{minutes:02d}:{seconds:02d}")

        # Color changes based on remaining time
        if self.remaining_seconds <= 60:
            self.timer_label.setProperty("timer", "danger")
        elif self.remaining_seconds <= 300:
            self.timer_label.setProperty("timer", "warning")
        else:
            self.timer_label.setProperty("timer", "")
        self.timer_label.style().unpolish(self.timer_label)
        self.timer_label.style().polish(self.timer_label)

    def cancel_practice(self):
        """User clicks Cancel — confirm and abandon the session."""
        reply = QMessageBox.question(
            self, self.tr("Cancel Session"),
            self.tr("Are you sure you want to cancel?\nAll progress will be lost."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.exam_timer:
            self.exam_timer.stop()
        self.practice_cancelled.emit()

    def finish_practice(self):
        """User clicks Submit button — show confirmation with unanswered/marked summary."""
        self.save_current_answer()
        self.save_time_for_current()

        unanswered = sum(1 for qid in self.question_ids if qid not in self.user_answers)
        marked = len(self.practice_marks)

        # Build confirmation message
        lines = []
        if unanswered > 0:
            lines.append(self.tr("%d question(s) unanswered") % unanswered)
        if marked > 0:
            lines.append(self.tr("%d question(s) marked for review") % marked)

        if lines:
            summary = "\n".join(lines)
            msg = self.tr("Are you sure you want to submit?") + "\n\n" + summary
        else:
            msg = self.tr("Are you sure you want to submit?")

        reply = QMessageBox.question(
            self, self.tr("Confirm Submit"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.mode == 'exam':
            self.submit_exam()
        else:
            self.submit_learn()

    def submit_exam(self):
        """Grade all exam answers and emit results."""
        if self.exam_timer:
            self.exam_timer.stop()

        self.save_current_answer()
        self.save_time_for_current()

        # Grade all questions
        for q_id in self.question_ids:
            if q_id in self.results:
                continue  # already graded (shouldn't happen in exam)
            user_answer = self.user_answers.get(q_id, '')
            q_data = self.question_cache.get(q_id)
            if not q_data:
                q_data = self.db.get_question_with_answers(q_id)
                if q_data:
                    self.question_cache[q_id] = q_data

            if q_data:
                # Need option order to determine correct labels
                if q_id not in self.option_order_cache:
                    self.option_order_cache[q_id] = list(q_data['answers'])

                correct_labels = []
                for i, ans in enumerate(self.option_order_cache[q_id]):
                    if ans['is_correct']:
                        correct_labels.append(chr(ord('A') + i))
                correct_answer = ','.join(sorted(correct_labels))
                is_correct = (user_answer == correct_answer) if user_answer else False
            else:
                is_correct = False

            self.results[q_id] = is_correct

            if self.session_id:
                self.db.save_answer_record(
                    self.session_id, q_id, user_answer, is_correct,
                    self.time_per_question.get(q_id, 0)
                )

        self._emit_results()

    def submit_learn(self):
        """Grade unchecked learning mode answers and emit results."""
        # Grade any unchecked questions
        for q_id in self.question_ids:
            if q_id in self.results:
                continue
            user_answer = self.user_answers.get(q_id, '')
            q_data = self.question_cache.get(q_id)
            if not q_data:
                q_data = self.db.get_question_with_answers(q_id)
                if q_data:
                    self.question_cache[q_id] = q_data

            if q_data and q_id in self.option_order_cache:
                correct_labels = []
                for i, ans in enumerate(self.option_order_cache[q_id]):
                    if ans['is_correct']:
                        correct_labels.append(chr(ord('A') + i))
                correct_answer = ','.join(sorted(correct_labels))
                is_correct = (user_answer == correct_answer) if user_answer else False
            else:
                is_correct = False

            self.results[q_id] = is_correct

            if self.session_id and q_id not in self.checked_set:
                self.db.save_answer_record(
                    self.session_id, q_id, user_answer, is_correct,
                    self.time_per_question.get(q_id, 0)
                )

        self._emit_results()

    def _emit_results(self):
        """Build result data and emit practice_finished signal."""
        correct_count = sum(1 for v in self.results.values() if v)
        total_duration = sum(self.time_per_question.values())

        # Update DB session
        if self.session_id:
            self.db.finish_practice_session(self.session_id, correct_count, total_duration)

        # Build per-question detail
        questions_detail = []
        for q_id in self.question_ids:
            q_data = self.question_cache.get(q_id, {})
            answers_ordered = self.option_order_cache.get(q_id, [])

            correct_labels = []
            for i, ans in enumerate(answers_ordered):
                if ans['is_correct']:
                    correct_labels.append(chr(ord('A') + i))

            questions_detail.append({
                'question_id': q_id,
                'question_text': q_data.get('question_text', ''),
                'question_type': q_data.get('question_type', 'MC'),
                'user_answer': self.user_answers.get(q_id, ''),
                'correct_answer': ','.join(sorted(correct_labels)),
                'is_correct': self.results.get(q_id, False),
                'explanation': q_data.get('explanation', ''),
                'time_spent': self.time_per_question.get(q_id, 0),
                'answers': answers_ordered,
            })

        result_data = {
            'session_id': self.session_id,
            'mode': self.mode,
            'total_count': len(self.question_ids),
            'correct_count': correct_count,
            'duration_sec': total_duration,
            'module_name': self.config.get('module_name', ''),
            'questions': questions_detail,
        }

        self.practice_finished.emit(result_data)

    def retranslate_ui(self):
        self.question_group.setTitle(self.tr("Question"))
        self.explanation_group.setTitle(self.tr("Explanation"))
        self.mark_btn.setText(self.tr("Mark"))
        self.check_btn.setText(self.tr("Check"))
        self.cancel_btn.setText(self.tr("Cancel"))
        self.prev_btn.setText(self.tr("Previous"))
        self.next_btn.setText(self.tr("Next"))
        self.submit_btn.setText(self.tr("Submit"))
        if self.question_ids:
            self.progress_label.setText(
                self.tr("Question %d / %d") % (self.current_index + 1, len(self.question_ids))
            )
        mode_text = self.tr("Learning Mode") if self.mode == 'learn' else self.tr("Exam Simulation")
        self.mode_label.setText(mode_text)
