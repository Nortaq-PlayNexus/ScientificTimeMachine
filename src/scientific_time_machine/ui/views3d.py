"""3D modeling displays: 3D branching timeline, 3D parameter space, 3D simulation surface."""
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel
from PySide6.QtCore import Qt

from ..core.replay import run_simulation

CM = {"bg": "#0b1220", "fg": "#e2e8f0", "accent": "#38bdf8", "accent2": "#a78bfa", "accent3": "#34d399"}


def _style_fig(fig):
    fig.patch.set_facecolor(CM["bg"])
    for ax in fig.axes:
        ax.set_facecolor(CM["bg"])
        try:
            ax.title.set_color("#e2e8f0")
            ax.xaxis.label.set_color("#cbd5e1")
            ax.yaxis.label.set_color("#cbd5e1")
            if hasattr(ax, "zaxis"):
                ax.zaxis.label.set_color("#cbd5e1")
            ax.tick_params(colors="#94a3b8", labelsize=8)
        except Exception:
            pass
    return fig


class View3DTimeline(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("3D Branching Timeline — depth = branch, x = step, z = hash entropy"))
        self.canvas = FigureCanvas(Figure(figsize=(9, 6)))
        self.layout.addWidget(self.canvas)
        btn = QPushButton("⟳ Refresh 3D Timeline")
        btn.clicked.connect(self.refresh)
        self.layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111, projection="3d")
        exps = self.ctrl.list_experiments()
        branches = {}
        for e in exps:
            branches.setdefault(e.branch_name, []).append(e)
        colors = [CM["accent"], CM["accent2"], CM["accent3"], "#f472b6", "#fbbf24"]
        for bi, (bname, lst) in enumerate(branches.items()):
            for i, e in enumerate(lst):
                z = int(e.snapshot_hash[:4], 16) / 65535.0
                ax.scatter([i], [bi], [z], s=90, c=colors[bi % len(colors)], label=bname if i == 0 else None)
                ax.text(i, bi, z, e.name[:8], fontsize=6, color="#cbd5e1")
            if len(lst) > 1:
                zs = [int(e.snapshot_hash[:4], 16) / 65535.0 for e in lst]
                ax.plot(list(range(len(lst))), [bi] * len(lst), zs, color=colors[bi % len(colors)], alpha=0.6)
        ax.set_xlabel("step")
        ax.set_ylabel("branch")
        ax.set_zlabel("snapshot entropy")
        ax.set_title("3D BRANCHING TIMELINE")
        ax.set_yticks(range(len(branches)))
        ax.set_yticklabels(list(branches.keys()))
        ax.legend()
        ax.view_init(elev=22, azim=-58)
        _style_fig(fig)
        self.canvas.draw()


class View3DParamSpace(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("3D Parameter Space — x = steps, y = noise, z = mean outcome (color = branch)"))
        self.canvas = FigureCanvas(Figure(figsize=(9, 6)))
        self.layout.addWidget(self.canvas)
        btn = QPushButton("⟳ Refresh 3D Parameter Space")
        btn.clicked.connect(self.refresh)
        self.layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111, projection="3d")
        exps = self.ctrl.list_experiments()
        branches = {}
        for e in exps:
            branches.setdefault(e.branch_name, []).append(e)
        colors = [CM["accent"], CM["accent2"], CM["accent3"], "#f472b6", "#fbbf24"]
        for bi, (bname, lst) in enumerate(branches.items()):
            pts = []
            for e in lst:
                res = run_simulation(e)
                pts.append((e.params.get("steps", 0), e.params.get("noise", 0), res["mean"]))
            if pts:
                arr = np.array(pts)
                ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2], s=70, c=colors[bi % len(colors)], label=bname, depthshade=True)
        ax.set_xlabel("steps")
        ax.set_ylabel("noise")
        ax.set_zlabel("mean outcome")
        ax.set_title("3D PARAMETER SPACE")
        ax.legend()
        ax.view_init(elev=20, azim=-135)
        _style_fig(fig)
        self.canvas.draw()


class View3DSurface(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("3D Simulation Surface — parameter sweep surface (steps x noise -> mean)"))
        self.combo = QComboBox()
        self.layout.addWidget(self.combo)
        self.canvas = FigureCanvas(Figure(figsize=(9, 6)))
        self.layout.addWidget(self.canvas)
        row = QVBoxLayout()
        btn = QPushButton("⟳ Render 3D Surface")
        btn.clicked.connect(self.render)
        self.layout.addWidget(btn)
        self.refresh_list()

    def refresh_list(self):
        self.combo.clear()
        for e in self.ctrl.list_experiments():
            self.combo.addItem(f"{e.name} ({e.id[:8]})", e)

    def render(self):
        e = self.combo.currentData()
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111, projection="3d")
        steps_vals = np.linspace(20, 120, 12)
        noise_vals = np.linspace(0.02, 0.5, 8)
        S, N = np.meshgrid(steps_vals, noise_vals)
        Z = np.zeros_like(S)
        import copy
        for i in range(S.shape[0]):
            for j in range(S.shape[1]):
                ec = copy.deepcopy(e)
                ec.params = dict(e.params)
                ec.params["steps"] = int(S[i, j])
                ec.params["noise"] = float(N[i, j])
                Z[i, j] = run_simulation(ec)["mean"]
        surf = ax.plot_surface(S, N, Z, cmap="turbo", alpha=0.9, linewidth=0.3, antialiased=True)
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
        ax.set_xlabel("steps")
        ax.set_ylabel("noise")
        ax.set_zlabel("mean")
        ax.set_title(f"3D SIMULATION SURFACE — {e.name if e else ''}")
        ax.view_init(elev=28, azim=-122)
        _style_fig(fig)
        self.canvas.draw()
