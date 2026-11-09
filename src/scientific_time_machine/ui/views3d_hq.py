"""High-quality 3D modeling via PyVista (VTK): lit meshes, tubes, spheres, orbit controls."""
import copy
import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QFrame, QHBoxLayout

from ..core.replay import run_simulation

PV_OPTS = dict(
    background="#0b1220",
)

BRANCH_COLORS = ["#38bdf8", "#a78bfa", "#34d399", "#f472b6", "#fbbf24", "#67e8f9"]


def _set_lights(plotter):
    plotter.enable_anti_aliasing("ssaa")
    try:
        plotter.add_light(pv.Light(position=(-2, 3, 6), color="#ffffff", intensity=1.2))
        plotter.add_light(pv.Light(position=(3, -2, 4), color="#38bdf8", intensity=0.6))
    except Exception:
        pass
    try:
        plotter.set_background("#0b1220", top="#0f1b2f")
    except Exception:
        plotter.set_background("#0b1220")


def _polish(plotter):
    plotter.show_axes()
    try:
        plotter.camera.zoom(0.9)
    except Exception:
        pass
    return plotter


class ViewHQ3DTimeline(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.addWidget(QLabel("<b>HQ 3D Branching Timeline</b> — tubes = branches, spheres = experiments. Drag to orbit, scroll to zoom."))
        self.interactor = QtInteractor(self)
        self.layout.addWidget(self.interactor, stretch=1)
        btn = QPushButton("⟳ Rebuild HQ 3D Timeline")
        btn.clicked.connect(self.refresh)
        self.layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        plotter = self.interactor
        plotter.clear()
        exps = self.ctrl.list_experiments()
        branches = {}
        for e in exps:
            branches.setdefault(e.branch_name, []).append(e)
        for bi, (bname, lst) in enumerate(branches.items()):
            pts = []
            for i, e in enumerate(lst):
                z = int(e.snapshot_hash[:4], 16) / 65535.0 * 4.0
                p = np.array([i * 1.5, bi * 2.0, z])
                pts.append(p)
                sphere = pv.Sphere(radius=0.22, center=p)
                plotter.add_mesh(sphere, color=BRANCH_COLORS[bi % len(BRANCH_COLORS)], smooth_shading=True,
                                 show_edges=False, name=f"{bname}_{i}")
                plotter.add_text(f"{e.name[:10]}", position=p + np.array([0, 0, 0.35]), font_size=8, color="#e2e8f0")
            if len(pts) >= 2:
                tube = pv.Line(pts[0], pts[-1]).tube(radius=0.08, run_orientor=True)
                plotter.add_mesh(tube, color=BRANCH_COLORS[bi % len(BRANCH_COLORS)], opacity=0.85, smooth_shading=True,
                                 name=f"line_{bname}")
        plotter.add_axes()
        plotter.view_isometric()
        _polish(plotter)
        _set_lights(plotter)
        plotter.render()


class ViewHQ3DParamSpace(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.addWidget(QLabel("<b>HQ 3D Parameter Space</b> — steps × noise × mean outcome, color = branch. Drag to orbit."))
        self.interactor = QtInteractor(self)
        self.layout.addWidget(self.interactor, stretch=1)
        btn = QPushButton("⟳ Rebuild HQ 3D Param Space")
        btn.clicked.connect(self.refresh)
        self.layout.addWidget(btn)
        self.refresh()

    def refresh(self):
        plotter = self.interactor
        plotter.clear()
        exps = self.ctrl.list_experiments()
        branches = {}
        for e in exps:
            branches.setdefault(e.branch_name, []).append(e)
        for bi, (bname, lst) in enumerate(branches.items()):
            pts = []
            for e in lst:
                res = run_simulation(e)
                pts.append([float(e.params.get("steps", 0)), float(e.params.get("noise", 0)) * 20.0, float(res["mean"]) * 3.0])
            if pts:
                cloud = pv.PolyData(np.array(pts))
                cloud.point_data["branch"] = np.ones(len(pts)) * bi
                sphere = pv.Sphere(radius=0.05, center=(0, 0, 0))
                glyph = cloud.glyph(geom=sphere, scale=40.0, factor=1.0)
                plotter.add_mesh(glyph, color=BRANCH_COLORS[bi % len(BRANCH_COLORS)], smooth_shading=True, name=f"cloud_{bname}")
        plotter.add_axes()
        plotter.view_isometric()
        _polish(plotter)
        _set_lights(plotter)
        plotter.render()


class ViewHQ3DSurface(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.addWidget(QLabel("<b>HQ 3D Simulation Surface</b> — smooth lit mesh over steps × noise. Drag to orbit."))
        self.combo = QComboBox()
        self.layout.addWidget(self.combo)
        self.interactor = QtInteractor(self)
        self.layout.addWidget(self.interactor, stretch=1)
        btn = QPushButton("⟳ Render HQ 3D Surface")
        btn.clicked.connect(self.render)
        self.layout.addWidget(btn)
        self.refresh_list()

    def refresh_list(self):
        self.combo.clear()
        for e in self.ctrl.list_experiments():
            self.combo.addItem(f"{e.name} ({e.id[:8]})", e)

    def render(self):
        e = self.combo.currentData()
        if e is None:
            return
        plotter = self.interactor
        plotter.clear()
        steps_vals = np.linspace(20, 120, 14)
        noise_vals = np.linspace(0.02, 0.5, 10)
        S, N = np.meshgrid(steps_vals, noise_vals)
        Z = np.zeros_like(S)
        for i in range(S.shape[0]):
            for j in range(S.shape[1]):
                ec = copy.deepcopy(e)
                ec.params = dict(e.params)
                ec.params["steps"] = int(S[i, j])
                ec.params["noise"] = float(N[i, j])
                Z[i, j] = run_simulation(ec)["mean"]
        grid = pv.StructuredGrid(S.ravel(), N.ravel() * 20.0, Z.ravel() * 3.0)
        plotter.add_mesh(grid, cmap="turbo", show_edges=False, smooth_shading=True, ambient=0.3, diffuse=0.8, specular=0.6, name="surface")
        plotter.add_axes()
        plotter.view_isometric()
        _polish(plotter)
        _set_lights(plotter)
        plotter.render()
