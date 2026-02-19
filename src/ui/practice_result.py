from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QProgressBar, QScrollArea, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, QCoreApplication, Signal


class PracticeResult(QWidget):
    """Displays practice results with full question review."""

    back_home = Signal()
    retry_wrong = Signal(list)
    start_new = Signal()

    def __init__(self, result_data: dict):
        super().__init__()
        self.result_data = result_data
        self.all_questions = result_data.get('questions', [])
        self.wrong_questions = [q for q in self.all_questions if not q['is_correct']]
        self.explanation_buttons: list[tuple[QPushButton, QTextEdit]] = []
        self.init_ui()

    def tr(self, text):
        return QCoreApplication.translate("PracticeResult", text)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Score overview ---
        score_group = QGroupBox(self.tr("Practice Complete!"))
        score_layout = QVBoxLayout(score_group)

        total = self.result_data.get('total_count', 0)
        correct = self.result_data.get('correct_count', 0)
        pct = int(correct / total * 100) if total > 0 else 0
        duration = self.result_data.get('duration_sec', 0)
        minutes = duration // 60
        seconds = duration % 60
        avg_per_q = duration // total if total > 0 else 0

        self.score_label = QLabel(self.tr("Score: %d / %d (%d%%)") % (correct, total, pct))
        self.score_label.setProperty("heading", "true")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.score_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(pct)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{pct}%")
        score_layout.addWidget(self.progress_bar)

        self.time_label = QLabel(self.tr("Time: %d min %d sec") % (minutes, seconds))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.time_label)

        self.avg_label = QLabel(self.tr("Average per question: %d sec") % avg_per_q)
        self.avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.avg_label)

        # Exam mode: pass/fail
        if self.result_data.get('mode') == 'exam':
            passing = 75
            passed = pct >= passing
            result_text = self.tr("Result: Pass") if passed else self.tr("Result: Fail")
            self.pass_label = QLabel(
                self.tr("Passing Score: 675/900 (75%%)") + "    " + result_text
            )
            self.pass_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            score_layout.addWidget(self.pass_label)

        main_layout.addWidget(score_group)

        # --- Questions review list ---
        wrong_count = len(self.wrong_questions)
        self.review_group = QGroupBox(
            self.tr("Question Review (%d questions, %d wrong)") % (len(self.all_questions), wrong_count)
        )
        review_outer_layout = QVBoxLayout(self.review_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for idx, q in enumerate(self.all_questions):
            item = self._create_question_item(idx + 1, q)
            scroll_layout.addWidget(item)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        review_outer_layout.addWidget(scroll)

        main_layout.addWidget(self.review_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()

        self.retry_btn = QPushButton(self.tr("Retry Wrong Questions"))
        self.retry_btn.clicked.connect(self._on_retry)
        self.retry_btn.setEnabled(wrong_count > 0)

        self.new_btn = QPushButton(self.tr("Start New Practice"))
        self.new_btn.clicked.connect(self.start_new.emit)

        self.home_btn = QPushButton(self.tr("Back to Home"))
        self.home_btn.clicked.connect(self.back_home.emit)

        btn_layout.addWidget(self.retry_btn)
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.home_btn)

        main_layout.addLayout(btn_layout)

    def _create_question_item(self, num: int, q: dict) -> QGroupBox:
        """Create a review item for one question with options and collapsible explanation."""
        is_correct = q.get('is_correct', False)
        status = self.tr("Correct") if is_correct else self.tr("Wrong")
        title = self.tr("Q%d. %s") % (num, status)

        group = QGroupBox(title)
        if not is_correct:
            group.setStyleSheet("QGroupBox { color: #dc3545; font-weight: bold; }")
        else:
            group.setStyleSheet("QGroupBox { color: #28a745; }")

        layout = QVBoxLayout(group)

        # Question text
        q_label = QLabel(q.get('question_text', ''))
        q_label.setWordWrap(True)
        layout.addWidget(q_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Options list
        user_answer_labels = set(q.get('user_answer', '').split(','))
        correct_answer_labels = set(q.get('correct_answer', '').split(','))
        answers = q.get('answers', [])

        for i, ans in enumerate(answers):
            option_label = chr(ord('A') + i)
            option_text = ans.get('option_text', '')
            is_option_correct = ans.get('is_correct', False)
            user_selected = option_label in user_answer_labels

            # Build display text with markers
            prefix = f"{option_label}. "
            markers = []
            if user_selected:
                markers.append(self.tr("Your answer"))
            if is_option_correct:
                markers.append(self.tr("Correct answer"))

            suffix = f"  [{', '.join(markers)}]" if markers else ""

            opt_label = QLabel(f"{prefix}{option_text}{suffix}")
            opt_label.setWordWrap(True)

            # Styling
            if is_option_correct and user_selected:
                opt_label.setStyleSheet("color: #28a745; font-weight: bold;")
            elif is_option_correct:
                opt_label.setStyleSheet("color: #28a745;")
            elif user_selected and not is_option_correct:
                opt_label.setStyleSheet("color: #dc3545; text-decoration: line-through;")

            layout.addWidget(opt_label)

        # Explanation (collapsed by default)
        explanation_text = q.get('explanation', '') or self.tr("No explanation provided")
        exp_btn = QPushButton(self.tr("Show Explanation"))
        exp_display = QTextEdit()
        exp_display.setReadOnly(True)
        exp_display.setMaximumHeight(120)
        exp_display.setText(explanation_text)
        exp_display.hide()

        def toggle_explanation(_btn=exp_btn, _display=exp_display):
            if _display.isVisible():
                _display.hide()
                _btn.setText(self.tr("Show Explanation"))
            else:
                _display.show()
                _btn.setText(self.tr("Hide Explanation"))

        exp_btn.clicked.connect(lambda checked: toggle_explanation())
        layout.addWidget(exp_btn)
        layout.addWidget(exp_display)

        self.explanation_buttons.append((exp_btn, exp_display))

        return group

    def _on_retry(self):
        wrong_ids = [q['question_id'] for q in self.wrong_questions]
        self.retry_wrong.emit(wrong_ids)

    def retranslate_ui(self):
        total = self.result_data.get('total_count', 0)
        correct = self.result_data.get('correct_count', 0)
        pct = int(correct / total * 100) if total > 0 else 0
        duration = self.result_data.get('duration_sec', 0)

        self.score_label.setText(self.tr("Score: %d / %d (%d%%)") % (correct, total, pct))
        self.time_label.setText(self.tr("Time: %d min %d sec") % (duration // 60, duration % 60))
        self.avg_label.setText(
            self.tr("Average per question: %d sec") % (duration // total if total > 0 else 0)
        )
        wrong_count = len(self.wrong_questions)
        self.review_group.setTitle(
            self.tr("Question Review (%d questions, %d wrong)") % (len(self.all_questions), wrong_count)
        )
        self.retry_btn.setText(self.tr("Retry Wrong Questions"))
        self.new_btn.setText(self.tr("Start New Practice"))
        self.home_btn.setText(self.tr("Back to Home"))

        for btn, display in self.explanation_buttons:
            if display.isVisible():
                btn.setText(self.tr("Hide Explanation"))
            else:
                btn.setText(self.tr("Show Explanation"))
