"""PySide6 main window with tabs."""
import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTextEdit, QFileDialog,
    QMessageBox, QComboBox, QLineEdit,
    QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("QtAgg")

from ..core.experiment import Experiment
from ..core.replay import run_simulation
from ..app import AppController
from .theme import HIGH_TECH_QSS
from .views3d_hq import ViewHQ3DTimeline, ViewHQ3DParamSpace, ViewHQ3DSurface


class TimelineView(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.info = QLabel("Branching Timeline")
        self.layout.addWidget(self.info)
        self.canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.layout.addWidget(self.canvas)
        self.refresh()

    def refresh(self):
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        exps = self.ctrl.list_experiments()
        branches = {}
        for e in exps:
            branches.setdefault(e.branch_name, []).append(e)
        y = 0
        for bname, lst in branches.items():
            xs = list(range(len(lst)))
            ys = [y] * len(lst)
            ax.plot(xs, ys, "o-", label=bname)
            for i, e in enumerate(lst):
                ax.annotate(e.name[:12], (i, y), fontsize=7)
            y += 1
        ax.set_yticks(range(len(branches)))
        ax.set_yticklabels(list(branches.keys()))
        ax.set_xlabel("step")
        ax.set_title("Branching Timeline")
        ax.legend()
        self.canvas.draw()


class ExperimentGraphView(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.layout.addWidget(self.combo)
        self.canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.layout.addWidget(self.canvas)
        btn = QPushButton("Plot Selected")
        btn.clicked.connect(self.plot)
        self.layout.addWidget(btn)
        self.refresh_list()

    def refresh_list(self):
        self.combo.clear()
        for e in self.ctrl.list_experiments():
            self.combo.addItem(f"{e.name} ({e.id[:8]})", e)

    def plot(self):
        e = self.combo.currentData()
        if e is None:
            return
        res = run_simulation(e)
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.plot(res["values"])
        ax.set_title(f"{e.name} (mean={res['mean']:.3f})")
        ax.set_xlabel("step")
        ax.set_ylabel("value")
        self.canvas.draw()


class SimulationViewer(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.layout.addWidget(self.combo)
        self.text = QTextEdit()
        self.layout.addWidget(self.text)
        btn = QPushButton("Replay")
        btn.clicked.connect(self.replay)
        self.layout.addWidget(btn)
        self.refresh_list()

    def refresh_list(self):
        self.combo.clear()
        for e in self.ctrl.list_experiments():
            self.combo.addItem(f"{e.name} ({e.id[:8]})", e)

    def replay(self):
        e = self.combo.currentData()
        if e is None:
            return
        res = self.ctrl.run(e)
        self.text.setText(json.dumps(res, indent=2, default=str)[:5000])


class SnapshotBrowser(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.listw = QListWidget() if False else None
        from PySide6.QtWidgets import QListWidget
        self.listw = QListWidget()
        self.layout.addWidget(self.listw)
        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        self.layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        self.listw.clear()
        for e in self.ctrl.list_experiments():
            self.listw.addItem(f"{e.name} | {e.branch_name} | hash={e.snapshot_hash[:12]} | seed={e.seed}")


class ComparisonDashboard(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.ca = QComboBox()
        self.cb = QComboBox()
        row.addWidget(QLabel("A:"))
        row.addWidget(self.ca)
        row.addWidget(QLabel("B:"))
        row.addWidget(self.cb)
        self.layout.addLayout(row)
        btn = QPushButton("Compare")
        btn.clicked.connect(self.compare)
        self.layout.addWidget(btn)
        self.text = QTextEdit()
        self.layout.addWidget(self.text)
        self.refresh_list()

    def refresh_list(self):
        self.ca.clear(); self.cb.clear()
        for e in self.ctrl.list_experiments():
            self.ca.addItem(f"{e.name} ({e.id[:8]})", e)
            self.cb.addItem(f"{e.name} ({e.id[:8]})", e)

    def compare(self):
        a = self.ca.currentData(); b = self.cb.currentData()
        if a is None or b is None:
            return
        r = self.ctrl.compare(a, b)
        self.text.setText(json.dumps(r, indent=2, default=str))


class MainWindow(QMainWindow):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.setWindowTitle("SCIENTIFIC TIME MACHINE — 3D")
        self.resize(1250, 780)
        self.setStyleSheet(HIGH_TECH_QSS)
        tabs = QTabWidget()
        self.timeline = TimelineView(ctrl)
        self.graph = ExperimentGraphView(ctrl)
        self.sim = SimulationViewer(ctrl)
        self.snaps = SnapshotBrowser(ctrl)
        self.cmp = ComparisonDashboard(ctrl)
        tabs.addTab(self.timeline, "Timeline")
        tabs.addTab(self.graph, "Experiment Graphs")
        tabs.addTab(self.sim, "Simulation Viewer")
        tabs.addTab(self.snaps, "Snapshot Browser")
        tabs.addTab(self.cmp, "Comparison Dashboard")
        self.timeline3d = ViewHQ3DTimeline(ctrl)
        self.param3d = ViewHQ3DParamSpace(ctrl)
        self.surface3d = ViewHQ3DSurface(ctrl)
        tabs.addTab(self.timeline3d, "3D Timeline")
        tabs.addTab(self.param3d, "3D Param Space")
        tabs.addTab(self.surface3d, "3D Surface")
        self.create_tab = self._build_create_tab()
        tabs.addTab(self.create_tab, "Create / Branch")
        self.setCentralWidget(tabs)
        self._build_menu()

    def _build_create_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()
        self.name_edit = QLineEdit("New Experiment")
        self.seed_spin = QSpinBox(); self.seed_spin.setRange(0, 2**31-1); self.seed_spin.setValue(42)
        self.steps_spin = QSpinBox(); self.steps_spin.setRange(1, 10000); self.steps_spin.setValue(50)
        self.noise_spin = QDoubleSpinBox(); self.noise_spin.setRange(0, 10); self.noise_spin.setValue(0.1); self.noise_spin.setSingleStep(0.01)
        self.base_spin = QDoubleSpinBox(); self.base_spin.setRange(-1000, 1000); self.base_spin.setValue(1.0)
        form.addRow("Name", self.name_edit)
        form.addRow("Seed", self.seed_spin)
        form.addRow("Steps", self.steps_spin)
        form.addRow("Noise", self.noise_spin)
        form.addRow("Base", self.base_spin)
        layout.addLayout(form)
        btn = QPushButton("Create Experiment")
        btn.clicked.connect(self._create)
        layout.addWidget(btn)
        gb = QGroupBox("Branch from selected experiment")
        bl = QVBoxLayout(gb)
        self.branch_name = QLineEdit("branch-1")
        bl.addWidget(self.branch_name)
        self.branch_src = QComboBox()
        bl.addWidget(self.branch_src)
        bbtn = QPushButton("Create Branch")
        bbtn.clicked.connect(self._branch)
        bl.addWidget(bbtn)
        layout.addWidget(gb)
        self._refresh_sources()
        return w

    def _refresh_sources(self):
        self.branch_src.clear()
        for e in self.ctrl.list_experiments():
            self.branch_src.addItem(f"{e.name} ({e.id[:8]})", e)

    def _create(self):
        params = {"steps": self.steps_spin.value(), "noise": self.noise_spin.value(), "base": self.base_spin.value()}
        e = self.ctrl.new_experiment(self.name_edit.text(), seed=self.seed_spin.value(), params=params)
        QMessageBox.information(self, "Created", f"Experiment {e.id}")
        self._refresh_all()

    def _branch(self):
        src = self.branch_src.currentData()
        if src is None:
            return
        try:
            ne = self.ctrl.branch_from(src, self.branch_name.text())
            QMessageBox.information(self, "Branched", f"New experiment {ne.id} on branch {ne.branch_name}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))
        self._refresh_all()

    def _refresh_all(self):
        self.timeline.refresh()
        self.timeline3d.refresh()
        self.param3d.refresh()
        self.surface3d.refresh_list()
        self.graph.refresh_list()
        self.sim.refresh_list()
        self.snaps.refresh()
        self.cmp.refresh_list()
        self._refresh_sources()

    def _build_menu(self):
        mb = self.menuBar()
        filem = mb.addMenu("File")
        act_export = filem.addAction("Export Selected Experiment Package")
        act_export.triggered.connect(self._export)
        act_import = filem.addAction("Import Experiment Package")
        act_import.triggered.connect(self._import)
        act_integ = filem.addAction("Check Integrity")
        act_integ.triggered.connect(self._integrity)
        filem.addAction("Exit").triggered.connect(self.close)

    def _export(self):
        exps = self.ctrl.list_experiments()
        if not exps:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export", "experiment.zip", "Zip (*.zip)")
        if path:
            self.ctrl.export(exps[-1], Path(path))
            QMessageBox.information(self, "Exported", path)

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "Zip (*.zip)")
        if path:
            try:
                e = self.ctrl.import_package(Path(path))
                QMessageBox.information(self, "Imported", e.id)
                self._refresh_all()
            except Exception as ex:
                QMessageBox.critical(self, "Error", str(ex))

    def _integrity(self):
        r = self.ctrl.integrity()
        QMessageBox.information(self, "Integrity", str(r))
