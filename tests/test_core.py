import tempfile, os
from pathlib import Path
import pytest

from scientific_time_machine.core.storage import Storage
from scientific_time_machine.core.experiment import Experiment
from scientific_time_machine.core.snapshot import SnapshotManager
from scientific_time_machine.core.branch import BranchManager
from scientific_time_machine.core.replay import run_simulation, ReplayEngine
from scientific_time_machine.core.compare import compare_experiments
from scientific_time_machine.core.package import export_package, import_package
from scientific_time_machine.core.recovery import check_integrity, rebuild_index
from scientific_time_machine.app import AppController


def tmp_storage():
    d = tempfile.mkdtemp()
    return Storage(Path(d)), d


def test_snapshot_integrity():
    storage, d = tmp_storage()
    snaps = SnapshotManager(storage)
    exp = Experiment.new("e1", seed=7, params={"steps": 10, "noise": 0.2, "base": 1.0})
    h = snaps.create(exp)
    assert storage.verify_blob(h)
    assert snaps.verify(h)
    restored = snaps.restore(h)
    assert restored.id == exp.id
    assert restored.compute_hash() == exp.snapshot_hash
    storage.close()


def test_branch_independence():
    storage, d = tmp_storage()
    snaps = SnapshotManager(storage)
    branches = BranchManager(storage, snaps)
    exp = Experiment.new("root", seed=5, params={"steps": 10})
    snaps.create(exp)
    storage.conn.execute("INSERT INTO branches (name, head_experiment_id, created_at, description) VALUES (?,?,?,?)",
                        ("main", exp.id, exp.created_at, "m"))
    storage.conn.commit()
    bid = branches.create_branch("alt", exp)
    cur = storage.conn.execute("SELECT state_blob FROM experiments WHERE id=?", (bid,)).fetchone()
    alt = snaps.restore(cur["state_blob"])
    alt.params["steps"] = 999
    alt.snapshot_hash = alt.compute_hash()
    snaps.create(alt)
    cur2 = storage.conn.execute("SELECT state_blob FROM experiments WHERE id=?", (exp.id,)).fetchone()
    orig2 = snaps.restore(cur2["state_blob"])
    assert orig2.params["steps"] == 10
    assert alt.params["steps"] == 999
    storage.close()


def test_replay_reproducibility():
    exp = Experiment.new("r", seed=123, params={"steps": 50, "noise": 0.1, "base": 1.0})
    storage = Storage(Path(tempfile.mkdtemp()))
    re = ReplayEngine(storage)
    assert re.verify_reproducibility(exp, n=5)
    r1 = run_simulation(exp)
    r2 = run_simulation(exp)
    assert r1 == r2
    storage.close()


def test_corruption_recovery():
    storage, d = tmp_storage()
    snaps = SnapshotManager(storage)
    exp = Experiment.new("c", seed=9, params={"steps": 5})
    h = snaps.create(exp)
    p = storage.blob_path(h)
    p.write_bytes(b"corrupted data!!!!")
    assert not snaps.verify(h)
    exp2 = Experiment.from_dict(exp.to_dict())
    exp2.metadata['backup'] = True
    exp2.snapshot_hash = exp2.compute_hash()
    h2 = snaps.create(exp2)
    recovered = snaps.recover_corrupt(h)
    assert recovered is not None
    assert recovered.id == exp.id
    storage.close()


def test_history_reconstruction():
    d = tempfile.mkdtemp()
    ctrl = AppController(Path(d))
    e1 = ctrl.new_experiment("e1", seed=1, params={"steps": 5})
    e2 = ctrl.branch_from(e1, "b1")
    e3 = ctrl.new_experiment("e3", seed=2, params={"steps": 5}, parent_id=e1.id, branch_name="main")
    exps = ctrl.list_experiments()
    assert len(exps) >= 3
    ctrl.close()
    storage2 = Storage(Path(d))
    n = rebuild_index(storage2)
    assert n >= 3
    storage2.close()


def test_package_roundtrip():
    exp = Experiment.new("pkg", seed=42, params={"steps": 5})
    p = Path(tempfile.mkdtemp()) / "out.zip"
    export_package(exp, p)
    e2 = import_package(p)
    assert e2.id == exp.id
    assert e2.seed == exp.seed


def test_compare():
    a = Experiment.new("a", seed=1, params={"steps": 10, "noise": 0.1, "base": 1.0})
    b = Experiment.new("b", seed=2, params={"steps": 10, "noise": 0.5, "base": 2.0})
    r = compare_experiments(a, b)
    assert "param_diffs" in r
    assert "noise" in r["param_diffs"]
    assert r["seed_diff"] is True

