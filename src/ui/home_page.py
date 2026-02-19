from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QSpinBox,
    QGroupBox, QRadioButton, QProgressBar

)
from PySide6.QtCore import Qt, QCoreApplication, Signal
from src.core.db_manager import DBManager


class HomePage(QWidget):
    """Home page with learning stats and practice setup."""

    start_practice = Signal(dict)
    open_exam_manager = Signal()

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.stats_expanded = False
        self.init_ui()
        self.load_filter_data()
        self.refresh_stats()

    def tr(self, text):
        return QCoreApplication.translate("HomePage", text)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Empty state (no questions) ---
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.addStretch()
        self.empty_label = QLabel(self.tr("Set up your first exam to get started!"))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 16px;")
        empty_layout.addWidget(self.empty_label)
        self.setup_exam_btn = QPushButton(self.tr("Open Exam Manager"))
        self.setup_exam_btn.setFixedWidth(250)
        self.setup_exam_btn.clicked.connect(self.open_exam_manager.emit)
        empty_layout.addWidget(self.setup_exam_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()
        self.empty_state.hide()
        main_layout.addWidget(self.empty_state)

        # --- Stats area (collapsible) ---
        self.stats_group = QGroupBox(self.tr("Learning Progress"))
        stats_layout = QVBoxLayout(self.stats_group)

        self.stats_summary = QLabel()
        self.stats_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.stats_summary)

        self.toggle_btn = QPushButton(self.tr("Show Details"))
        self.toggle_btn.clicked.connect(self.toggle_stats)
        stats_layout.addWidget(self.toggle_btn)

        # Detail area (hidden by default)
        self.stats_detail = QWidget()
        detail_layout = QVBoxLayout(self.stats_detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        self.module_stats_label = QLabel(self.tr("Module Mastery"))
        self.module_stats_label.setProperty("heading", "true")
        detail_layout.addWidget(self.module_stats_label)

        self.module_stats_container = QVBoxLayout()
        detail_layout.addLayout(self.module_stats_container)

        self.weak_label = QLabel()
        detail_layout.addWidget(self.weak_label)

        stats_layout.addWidget(self.stats_detail)
        self.stats_detail.hide()

        main_layout.addWidget(self.stats_group)
        main_layout.addSpacing(10)

        # --- Practice setup area ---
        self.setup_group = QGroupBox(self.tr("Practice Settings"))
        setup_layout = QVBoxLayout(self.setup_group)

        # Mode selection
        mode_layout = QHBoxLayout()
        self.mode_label = QLabel(self.tr("Practice Mode:"))
        self.learn_radio = QRadioButton(self.tr("Learning Mode"))
        self.exam_radio = QRadioButton(self.tr("Exam Simulation"))
        self.learn_radio.setChecked(True)
        self.learn_radio.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.learn_radio)
        mode_layout.addWidget(self.exam_radio)
        mode_layout.addStretch()
        setup_layout.addLayout(mode_layout)

        # Filters
        filter_layout = QGridLayout()

        self.label_module = QLabel(self.tr("Module:"))
        filter_layout.addWidget(self.label_module, 0, 0)
        self.module_combo = QComboBox()
        filter_layout.addWidget(self.module_combo, 0, 1)

        self.label_chapter = QLabel(self.tr("Chapter:"))
        filter_layout.addWidget(self.label_chapter, 0, 2)
        self.chapter_combo = QComboBox()
        filter_layout.addWidget(self.chapter_combo, 0, 3)

        self.label_count = QLabel(self.tr("Number of Questions:"))
        filter_layout.addWidget(self.label_count, 1, 0)
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 500)
        self.count_spinbox.setValue(20)
        filter_layout.addWidget(self.count_spinbox, 1, 1)

        setup_layout.addLayout(filter_layout)

        # Checkboxes
        check_layout = QHBoxLayout()
        self.flagged_check = QCheckBox(self.tr("Flagged Questions First"))
        self.wrong_check = QCheckBox(self.tr("Wrong Questions First"))
        check_layout.addWidget(self.flagged_check)
        check_layout.addWidget(self.wrong_check)
        check_layout.addStretch()
        setup_layout.addLayout(check_layout)

        # Exam time limit (hidden by default, auto-calculated from question count)
        self.time_widget = QWidget()
        time_layout = QHBoxLayout(self.time_widget)
        time_layout.setContentsMargins(0, 8, 0, 8)
        self.time_label = QLabel(self.tr("Time Limit (minutes):"))
        self.time_value_label = QLabel(str(self.count_spinbox.value()))
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_value_label)
        time_layout.addStretch()
        self.time_widget.hide()
        setup_layout.addWidget(self.time_widget)

        self.count_spinbox.valueChanged.connect(lambda v: self.time_value_label.setText(str(v)))

        # Start button
        self.start_btn = QPushButton(self.tr("Start Practice"))
        self.start_btn.setProperty("primary", "true")
        self.start_btn.clicked.connect(self.on_start)
        setup_layout.addWidget(self.start_btn)

        main_layout.addWidget(self.setup_group)
        main_layout.addStretch()

        self.module_combo.currentIndexChanged.connect(self.load_chapter_data)

    # --- Stats ---

    def on_mode_changed(self, checked):
        """Show/hide exam time settings based on mode."""
        self.time_widget.setVisible(self.exam_radio.isChecked())

    def reset_filters(self):
        """Reset filter checkboxes to default (called when returning home after a session)."""
        self.flagged_check.setChecked(False)
        self.wrong_check.setChecked(False)

    def toggle_stats(self):
        self.stats_expanded = not self.stats_expanded
        self.stats_detail.setVisible(self.stats_expanded)
        self.toggle_btn.setText(
            self.tr("Hide Details") if self.stats_expanded else self.tr("Show Details")
        )

    def refresh_stats(self):
        """Refresh statistics from database."""
        # Check if database has any questions at all
        has_questions = self.db.get_question_count() > 0
        self.empty_state.setVisible(not has_questions)
        self.stats_group.setVisible(has_questions)
        self.setup_group.setVisible(has_questions)
        if not has_questions:
            return

        total_practiced = self.db.get_total_practiced_count()
        accuracy = self.db.get_overall_accuracy()

        if total_practiced == 0:
            self.stats_summary.setText(
                self.tr("No practice records yet. Start your first practice!")
            )
            self.toggle_btn.hide()
            return

        self.toggle_btn.show()

        recent = self.db.get_recent_sessions(limit=1)
        last_score = 0
        if recent:
            r = recent[0]
            last_score = int(r['correct_count'] / r['total_count'] * 100) if r['total_count'] > 0 else 0

        self.stats_summary.setText(
            self.tr("Practiced: %d questions") % total_practiced + "    " +
            self.tr("Accuracy: %.1f%%") % accuracy + "    " +
            self.tr("Last Score: %d%%") % last_score
        )

        self._refresh_module_stats()

    def _refresh_module_stats(self):
        """Refresh per-module accuracy display."""
        self._clear_layout(self.module_stats_container)

        module_stats = self.db.get_module_accuracy()
        # Filter out hidden default module
        module_stats = [ms for ms in module_stats if ms['module_name'] != '_default']
        weak_areas = []

        if not module_stats:
            self.module_stats_label.hide()
            self.weak_label.hide()
            return

        self.module_stats_label.show()
        self.weak_label.show()

        for ms in module_stats:
            row = QHBoxLayout()
            name_label = QLabel(ms['module_name'])
            name_label.setMinimumWidth(150)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(ms['accuracy']))
            bar.setFormat(f"{int(ms['accuracy'])}%")
            bar.setMinimumWidth(200)

            count_label = QLabel(self.tr("practiced %d times") % ms['session_count'])

            row.addWidget(name_label)
            row.addWidget(bar)
            row.addWidget(count_label)
            row.addStretch()

            container = QWidget()
            container.setLayout(row)
            self.module_stats_container.addWidget(container)

            if ms['accuracy'] < 60 and ms['session_count'] > 0:
                weak_areas.append(ms['module_name'])

        self.weak_label.setText(
            (self.tr("Weak Areas") + ": " + ", ".join(weak_areas)) if weak_areas else ""
        )

    @staticmethod
    def _clear_layout(layout):
        """Recursively remove all items from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                HomePage._clear_layout(child.layout())

    # --- Filters ---

    def load_filter_data(self):
        """Load module data for filter combos."""
        self.module_combo.clear()

        try:
            modules = self.db.get_visible_modules()
        except Exception as e:
            print(f"Failed to load modules: {e}")
            modules = []

        if len(modules) <= 1:
            # No modules or single module: hide module filter
            self.label_module.hide()
            self.module_combo.hide()
            if modules:
                self.module_combo.addItem(modules[0][1], userData=modules[0][0])
            else:
                self.module_combo.addItem("", userData=None)
        else:
            self.label_module.show()
            self.module_combo.show()
            self.module_combo.addItem(self.tr("--- All Modules ---"), userData=None)
            for module_id, module_name in modules:
                self.module_combo.addItem(module_name, userData=module_id)

        self.load_chapter_data(0)

    def load_chapter_data(self, index):
        """Load chapter data based on selected module."""
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()

        module_id = self.module_combo.currentData()

        self.chapter_combo.addItem(
            self.tr("--- All Chapters/Lessons ---"),
            userData={'type': 'ALL_LESSONS'}
        )

        try:
            if module_id:
                lessons = self.db.get_lessons_by_module(module_id)
            elif not self.module_combo.isVisible():
                # Module-less exam: load all lessons
                lessons = self.db.get_all_lessons()
            else:
                lessons = []
            for lesson_id, chapter_num, chapter_title in lessons:
                display_text = f"Chapter {chapter_num}: {chapter_title}"
                self.chapter_combo.addItem(
                    display_text, userData={'type': 'LESSON', 'chapters': chapter_num}
                )
        except Exception as e:
            print(f"Failed to load lessons: {e}")

        self.chapter_combo.blockSignals(False)

    def _get_chapter_numbers(self) -> list[str] | None:
        """Extract chapter numbers from chapter combo selection."""
        data = self.chapter_combo.currentData()
        if not data or data.get('type') == 'ALL_LESSONS':
            return None

        chapters = data.get('chapters')
        if not chapters:
            return None

        num = str(chapters)
        if '.' not in num:
            return [f"{num}.0"]
        return [num]

    # --- Start practice ---

    def on_start(self):
        """Build practice config and emit start signal."""
        module_id = self.module_combo.currentData()

        config = {
            'mode': 'exam' if self.exam_radio.isChecked() else 'learn',
            'module_id': module_id,
            'module_name': self.module_combo.currentText() if module_id else '',
            'chapter_numbers': self._get_chapter_numbers(),
            'count': self.count_spinbox.value(),
            'flagged_only': self.flagged_check.isChecked(),
            'wrong_only': self.wrong_check.isChecked(),
        }

        self.start_practice.emit(config)

    def retranslate_ui(self):
        self.empty_label.setText(self.tr("Set up your first exam to get started!"))
        self.setup_exam_btn.setText(self.tr("Open Exam Manager"))
        self.stats_group.setTitle(self.tr("Learning Progress"))
        self.toggle_btn.setText(
            self.tr("Hide Details") if self.stats_expanded else self.tr("Show Details")
        )
        self.module_stats_label.setText(self.tr("Module Mastery"))
        self.setup_group.setTitle(self.tr("Practice Settings"))
        self.mode_label.setText(self.tr("Practice Mode:"))
        self.learn_radio.setText(self.tr("Learning Mode"))
        self.exam_radio.setText(self.tr("Exam Simulation"))
        self.label_module.setText(self.tr("Module:"))
        self.label_chapter.setText(self.tr("Chapter:"))
        self.label_count.setText(self.tr("Number of Questions:"))
        self.flagged_check.setText(self.tr("Flagged Questions First"))
        self.wrong_check.setText(self.tr("Wrong Questions First"))
        self.time_label.setText(self.tr("Time Limit (minutes):"))
        self.start_btn.setText(self.tr("Start Practice"))
        self.refresh_stats()
        self.load_filter_data()
