import tempfile
from pathlib import Path
from scientific_time_machine.app import AppController
from scientific_time_machine.ui.main_window import MainWindow


def test_ui_smoke(qtbot):
    d = tempfile.mkdtemp()
    ctrl = AppController(Path(d))
    win = MainWindow(ctrl)
    qtbot.addWidget(win)
    win.show()
    assert win.windowTitle() == "SCIENTIFIC TIME MACHINE"
    ctrl.close()
