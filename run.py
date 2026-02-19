#!/usr/bin/env python
"""
ReCall - Application Entry Point

This is the main entry point for the application.
Run this file to start the application:
    python run.py
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLocale

# Import the main window from the src package
from src.ui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Create the Qt application
    app = QApplication(sys.argv)

    # Set default locale for translation system
    locale = QLocale(QLocale.Language.English, QLocale.Country.AnyCountry)
    QLocale.setDefault(locale)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
