"""Theme management: loading, applying, and managing application themes."""

import os
import json
from PySide6.QtWidgets import QApplication
from src.core.config import get_project_root


class ThemeManager:
    """Singleton manager for application themes and styling."""

    _instance = None
    _current_theme = None
    _font_size_multiplier = 1.0
    _available_themes: dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_available_themes()
        return cls._instance

    def _load_available_themes(self) -> None:
        """Load all theme JSON files from resources/themes/."""
        themes_dir = os.path.join(get_project_root(), 'resources', 'themes')

        if not os.path.exists(themes_dir):
            print(f"Warning: Themes directory not found: {themes_dir}")
            return

        for filename in os.listdir(themes_dir):
            if filename.endswith('.json'):
                theme_path = os.path.join(themes_dir, filename)
                try:
                    with open(theme_path, 'r', encoding='utf-8') as f:
                        theme_id = os.path.splitext(filename)[0]
                        self._available_themes[theme_id] = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load theme {filename}: {e}")

    def get_available_themes(self) -> list[dict[str, str]]:
        """Get list of available themes with id, name, name_key, description, description_key."""
        return [{
            'id': tid,
            'name': data.get('name', tid),
            'name_key': data.get('name_key', ''),
            'description': data.get('description', ''),
            'description_key': data.get('description_key', '')
        } for tid, data in self._available_themes.items()]

    def load_theme(self, theme_id: str) -> bool:
        """Load a theme by ID. Returns True on success."""
        if theme_id not in self._available_themes:
            print(f"Warning: Theme '{theme_id}' not found")
            return False
        self._current_theme = self._available_themes[theme_id]
        return True

    def apply_theme(self, app: QApplication | None = None) -> None:
        """Apply current theme to the application."""
        if self._current_theme is None:
            print("Warning: No theme loaded")
            return

        app = app or QApplication.instance()
        if app is None:
            print("Warning: No QApplication instance found")
            return

        self._generate_arrow_icons()
        app.setStyleSheet(self._generate_stylesheet())

    def set_font_size(self, size: int) -> None:
        """Set font size (clamped to 8-20pt)."""
        size = max(8, min(20, size))
        base_size = self._current_theme.get('fonts', {}).get('size_base', 10) if self._current_theme else 10
        self._font_size_multiplier = size / base_size

    # --- Icon generation ---

    def _generate_arrow_icons(self) -> None:
        """Generate SVG arrow icons based on current theme colors."""
        if self._current_theme is None:
            return

        colors = self._current_theme.get('colors', {})
        components = self._current_theme.get('components', {})
        arrow_color = components.get('input', {}).get('text', colors.get('text', '#000000'))

        icons_dir = os.path.join(get_project_root(), 'resources', 'icons')
        os.makedirs(icons_dir, exist_ok=True)

        arrows = {
            'spinbox_up.svg': f'<svg width="10" height="6" viewBox="0 0 10 6" xmlns="http://www.w3.org/2000/svg">'
                              f'<path d="M5 0L0 6H10L5 0Z" fill="{arrow_color}"/></svg>',
            'spinbox_down.svg': f'<svg width="10" height="6" viewBox="0 0 10 6" xmlns="http://www.w3.org/2000/svg">'
                                f'<path d="M5 6L0 0H10L5 6Z" fill="{arrow_color}"/></svg>',
        }
        for filename, svg_content in arrows.items():
            with open(os.path.join(icons_dir, filename), 'w', encoding='utf-8') as f:
                f.write(svg_content)

    # --- Stylesheet generation ---

    def _generate_stylesheet(self) -> str:
        """Generate QSS stylesheet from current theme data."""
        if self._current_theme is None:
            return ""

        colors = self._current_theme.get('colors', {})
        fonts = self._current_theme.get('fonts', {})
        spacing = self._current_theme.get('spacing', {})
        components = self._current_theme.get('components', {})

        # Arrow icon paths
        icons_dir = os.path.join(get_project_root(), 'resources', 'icons')
        up_arrow = os.path.join(icons_dir, 'spinbox_up.svg').replace('\\', '/')
        down_arrow = os.path.join(icons_dir, 'spinbox_down.svg').replace('\\', '/')

        # Font sizes with multiplier
        base_size = int(fonts.get('size_base', 10) * self._font_size_multiplier)
        title_size = int(fonts.get('size_title', 14) * self._font_size_multiplier)
        font_family = fonts.get('family', 'Arial')

        # Shorthand accessors
        c = colors
        border_w = spacing.get('border_width', 1)
        border_r = spacing.get('border_radius', 4)
        btn = components.get('button', {})
        btn_p = components.get('button_primary', {})
        inp = components.get('input', {})
        menu = components.get('menu', {})
        table = components.get('table', {})
        scroll = components.get('scrollbar', {})
        tip = components.get('tooltip', {})
        practice = components.get('practice', {})
        win_bg = components.get('window', {}).get('background', c.get('background', '#FFFFFF'))

        qss = f"""
        /* Global */
        QWidget {{
            font-family: {font_family};
            font-size: {base_size}pt;
            color: {c.get('text', '#000000')};
            background-color: {win_bg};
        }}

        QMainWindow {{
            background-color: {win_bg};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {btn.get('background', c.get('button_bg', '#E1E1E1'))};
            color: {btn.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {btn.get('border', c.get('border', '#CCCCCC'))};
            border-radius: {btn.get('border_radius', border_r)}px;
            padding: {btn.get('padding', '6px 12px')};
            min-height: {btn.get('min_height', 28)}px;
        }}
        QPushButton:hover {{
            background-color: {btn.get('background_hover', c.get('button_hover', '#D0D0D0'))};
        }}
        QPushButton:pressed {{
            background-color: {btn.get('background_pressed', c.get('button_pressed', '#B0B0B0'))};
        }}
        QPushButton:disabled {{
            color: {c.get('text_disabled', '#AAAAAA')};
            background-color: {c.get('secondary', '#F0F0F0')};
        }}

        /* Primary Button */
        QPushButton[primary="true"] {{
            background-color: {btn_p.get('background', c.get('primary', '#0078D7'))};
            color: {btn_p.get('text', '#FFFFFF')};
            border-color: {btn_p.get('border', c.get('primary', '#0078D7'))};
        }}
        QPushButton[primary="true"]:hover {{
            background-color: {btn_p.get('background_hover', c.get('primary_hover', '#005A9E'))};
        }}
        QPushButton[primary="true"]:pressed {{
            background-color: {btn_p.get('background_pressed', c.get('primary_pressed', '#004578'))};
        }}

        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {inp.get('background', c.get('input_bg', '#FFFFFF'))};
            color: {inp.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            border-radius: {inp.get('border_radius', border_r)}px;
            padding: {inp.get('padding', '6px 8px')};
            min-height: {inp.get('min_height', 28)}px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {inp.get('border_focus', c.get('input_focus', '#0078D7'))};
        }}

        /* SpinBox */
        QSpinBox, QDoubleSpinBox {{
            background-color: {inp.get('background', c.get('input_bg', '#FFFFFF'))};
            color: {inp.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            border-radius: {inp.get('border_radius', border_r)}px;
            padding: 6px 8px;
            padding-right: 28px;
            min-height: {inp.get('min_height', 28)}px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {inp.get('border_focus', c.get('input_focus', '#0078D7'))};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            width: 24px;
            border-left: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            background-color: {btn.get('background', c.get('button_bg', '#E1E1E1'))};
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background-color: {btn.get('background_hover', c.get('button_hover', '#D0D0D0'))};
        }}
        QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{
            background-color: {btn.get('background_pressed', c.get('button_pressed', '#B0B0B0'))};
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 24px;
            border-left: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            border-top: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            background-color: {btn.get('background', c.get('button_bg', '#E1E1E1'))};
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {btn.get('background_hover', c.get('button_hover', '#D0D0D0'))};
        }}
        QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
            background-color: {btn.get('background_pressed', c.get('button_pressed', '#B0B0B0'))};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            width: 10px; height: 6px;
            image: url({up_arrow});
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            width: 10px; height: 6px;
            image: url({down_arrow});
        }}

        /* ComboBox */
        QComboBox {{
            background-color: {inp.get('background', c.get('input_bg', '#FFFFFF'))};
            color: {inp.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            border-radius: {inp.get('border_radius', border_r)}px;
            padding: 6px 8px;
            min-height: {inp.get('min_height', 28)}px;
        }}
        QComboBox:focus {{
            border-color: {inp.get('border_focus', c.get('input_focus', '#0078D7'))};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {inp.get('background', c.get('input_bg', '#FFFFFF'))};
            color: {inp.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {inp.get('border', c.get('input_border', '#CCCCCC'))};
            selection-background-color: {c.get('primary', '#0078D7')};
            selection-color: #FFFFFF;
        }}

        /* Labels */
        QLabel {{
            color: {c.get('text', '#000000')};
            background-color: transparent;
        }}
        QLabel[heading="true"] {{
            font-size: {title_size}pt;
            font-weight: bold;
        }}

        /* MenuBar */
        QMenuBar {{
            background-color: {menu.get('background', c.get('menu_bg', '#F0F0F0'))};
            color: {menu.get('text', c.get('text', '#000000'))};
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
        }}
        QMenuBar::item:selected {{
            background-color: {menu.get('item_hover', c.get('menu_hover', '#E5E5E5'))};
        }}

        /* Menu */
        QMenu {{
            background-color: {menu.get('background', c.get('menu_bg', '#F0F0F0'))};
            color: {menu.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {c.get('border', '#CCCCCC')};
        }}
        QMenu::item {{
            padding: 6px 20px 6px 8px;
        }}
        QMenu::indicator {{
            width: 14px; height: 14px;
            margin-left: 4px; margin-right: 2px;
        }}
        QMenu::item:selected {{
            background-color: {menu.get('item_hover', c.get('menu_hover', '#E5E5E5'))};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {menu.get('separator', c.get('border', '#CCCCCC'))};
            margin: 4px 0px;
        }}

        /* Tables */
        QTableWidget, QTableView {{
            background-color: {table.get('background', c.get('background', '#FFFFFF'))};
            alternate-background-color: {table.get('alternate_row', c.get('surface', '#F9F9F9'))};
            color: {c.get('text', '#000000')};
            gridline-color: {table.get('grid', c.get('border', '#E0E0E0'))};
            border: {border_w}px solid {c.get('border', '#CCCCCC')};
        }}
        QHeaderView::section {{
            background-color: {table.get('header_bg', c.get('secondary', '#E1E1E1'))};
            color: {table.get('header_text', c.get('text', '#000000'))};
            padding: 6px;
            border: none;
            border-right: 1px solid {c.get('border', '#CCCCCC')};
            border-bottom: 1px solid {c.get('border', '#CCCCCC')};
        }}
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {table.get('selection', c.get('primary', '#CCE8FF'))};
        }}

        /* ScrollBar - Vertical */
        QScrollBar:vertical {{
            background-color: {scroll.get('background', c.get('scroll_bg', '#F0F0F0'))};
            width: {scroll.get('width', 12)}px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {scroll.get('handle', c.get('scroll_handle', '#C0C0C0'))};
            border-radius: {scroll.get('border_radius', 6)}px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {scroll.get('handle_hover', c.get('scroll_handle_hover', '#A0A0A0'))};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* ScrollBar - Horizontal */
        QScrollBar:horizontal {{
            background-color: {scroll.get('background', c.get('scroll_bg', '#F0F0F0'))};
            height: {scroll.get('width', 12)}px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {scroll.get('handle', c.get('scroll_handle', '#C0C0C0'))};
            border-radius: {scroll.get('border_radius', 6)}px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {scroll.get('handle_hover', c.get('scroll_handle_hover', '#A0A0A0'))};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* Checkboxes and Radio Buttons */
        QCheckBox, QRadioButton {{
            color: {c.get('text', '#000000')};
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px; height: 18px;
            border: 2px solid {c.get('border', '#CCCCCC')};
            background-color: {inp.get('background', c.get('input_bg', '#FFFFFF'))};
        }}
        QCheckBox::indicator {{
            border-radius: 3px;
        }}
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {c.get('primary', '#0078D7')};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {c.get('primary', '#0078D7')};
            border-color: {c.get('primary', '#0078D7')};
        }}
        QCheckBox::indicator:checked {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgOUw3LjUgMTMuNUwxNSA0LjUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }}
        QRadioButton::indicator:checked {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iOSIgY3k9IjkiIHI9IjQiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=);
        }}
        QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
            border-color: {c.get('text_disabled', '#AAAAAA')};
            background-color: {c.get('secondary', '#F0F0F0')};
        }}

        /* Tooltips */
        QToolTip {{
            background-color: {tip.get('background', c.get('tooltip_bg', '#FFFFE1'))};
            color: {tip.get('text', c.get('text', '#000000'))};
            border: {border_w}px solid {tip.get('border', c.get('tooltip_border', '#767676'))};
            padding: 4px;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {c.get('secondary', '#F0F0F0')};
            color: {c.get('text', '#000000')};
        }}

        /* Group Box */
        QGroupBox {{
            border: {border_w}px solid {c.get('border', '#CCCCCC')};
            border-radius: {border_r}px;
            margin-top: 12px;
            padding-top: 8px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: {c.get('text', '#000000')};
        }}

        /* Progress Bar */
        QProgressBar {{
            border: {border_w}px solid {c.get('border', '#CCCCCC')};
            border-radius: {border_r}px;
            text-align: center;
            background-color: {c.get('secondary', '#F0F0F0')};
        }}
        QProgressBar::chunk {{
            background-color: {c.get('primary', '#0078D7')};
            border-radius: {border_r}px;
        }}

        /* Practice: answer feedback */
        QRadioButton[result="correct"], QCheckBox[result="correct"] {{
            background-color: {practice.get('correct_bg', '#e6f4ea')};
            border: 2px solid {practice.get('correct_border', '#34a853')};
            border-radius: 4px;
            padding: 5px;
        }}
        QRadioButton[result="incorrect"], QCheckBox[result="incorrect"] {{
            background-color: {practice.get('incorrect_bg', '#fce8e6')};
            border: 2px solid {practice.get('incorrect_border', '#ea4335')};
            border-radius: 4px;
            padding: 5px;
        }}

        /* Practice: timer states */
        QLabel[timer="warning"] {{
            color: {practice.get('timer_warning', '#e37400')};
            font-weight: bold;
        }}
        QLabel[timer="danger"] {{
            color: {practice.get('timer_danger', '#dc3545')};
            font-weight: bold;
        }}
        """

        return qss
