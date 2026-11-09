"""Style module deprecated - theme lives in main_window.py."""
HIGH_TECH_QSS = """
QMainWindow { background: #070b14; }
QTabWidget::pane { background: #0b1220; border: 1px solid #1e3a5f; border-radius: 8px; }
QTabBar::tab { background: #0d1729; color: #7dd3fc; border: 1px solid #22406d; border-bottom: none; padding: 8px 16px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 11px; font-weight: 600; }
QTabBar::tab:selected { background: #16233f; color: #ffffff; border-bottom: 2px solid #38bdf8; }
QTabBar::tab:hover { color: #e0f2fe; }
QPushButton { background: linear-gradient(#152238, #101a30); color: #7dd3fc; border: 1px solid #2b4c7e; border-radius: 6px; padding: 7px 16px; font-weight: 600; font-size: 12px; }
QPushButton:hover { background: #1b2c4f; color: #ffffff; border-color: #38bdf8; }
QPushButton:pressed { background: #0e2242; }
QPushButton:disabled { color: #475569; border-color: #1e293b; }
QLabel { color: #94a3b8; font-size: 12px; }
QLabel b { color: #e2e8f0; }
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background: #0c1527; color: #e2e8f0; border: 1px solid #2a456e; border-radius: 6px; padding: 5px 10px; font-size: 12px; }
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #38bdf8; outline: none; }
QTextEdit, QListWidget { background: #080d1a; color: #a5f3fc; border: 1px solid #1e3a5f; border-radius: 6px; font-family: Consolas, 'Courier New', monospace; font-size: 11px; selection-background-color: #1e3a5f; }
QGroupBox { color: #7dd3fc; border: 1px solid #22406d; border-radius: 8px; margin-top: 12px; padding-top: 14px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QMenuBar { background: #080d1a; color: #7dd3fc; border-bottom: 1px solid #1e3a5f; }
QMenu { background: #0b1220; color: #e2e8f0; border: 1px solid #22406d; }
QMenu::item:selected { background: #16233f; }
QMessageBox { background: #0b1220; color: #e2e8f0; }
QScrollBar:vertical { background: #0b1220; width: 10px; }
QScrollBar::handle:vertical { background: #1e3a5f; border-radius: 5px; }
"""
