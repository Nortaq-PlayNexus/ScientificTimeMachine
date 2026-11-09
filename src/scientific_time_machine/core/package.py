"""Reproducible experiment packages: export/import zip archives."""
import json
import zipfile
from pathlib import Path
from typing import List

from .experiment import Experiment


def export_package(exp: Experiment, out_path: Path, include_runs: bool = True) -> Path:
    out_path = Path(out_path)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("experiment.json", json.dumps(exp.to_dict(), sort_keys=True, default=str, indent=2))
        zf.writestr("README.txt", f"Scientific Time Machine experiment package\nName: {exp.name}\nID: {exp.id}\nSeed: {exp.seed}\n")
    return out_path


def import_package(path: Path) -> Experiment:
    with zipfile.ZipFile(path, "r") as zf:
        data = zf.read("experiment.json")
    d = json.loads(data)
    return Experiment.from_dict(d)


def export_branch_package(exps: List[Experiment], out_path: Path) -> Path:
    out_path = Path(out_path)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, e in enumerate(exps):
            zf.writestr(f"experiments/{i:03d}_{e.id}.json", json.dumps(e.to_dict(), sort_keys=True, default=str, indent=2))
        zf.writestr("manifest.json", json.dumps({"count": len(exps)}, indent=2))
    return out_path
