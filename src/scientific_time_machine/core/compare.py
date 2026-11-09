"""Branch / experiment comparison."""
from typing import Any, Dict, List

from .experiment import Experiment
from .replay import run_simulation


def compare_experiments(a: Experiment, b: Experiment) -> Dict[str, Any]:
    ra = run_simulation(a)
    rb = run_simulation(b)
    diff_params = {}
    all_keys = set(a.params) | set(b.params)
    for k in all_keys:
        va, vb = a.params.get(k), b.params.get(k)
        if va != vb:
            diff_params[k] = (va, vb)
    metrics_diff = {}
    for m in ("mean", "variance", "min", "max"):
        metrics_diff[m] = (ra[m], rb[m], rb[m] - ra[m])
    seed_diff = a.seed != b.seed
    return {
        "a_id": a.id, "b_id": b.id,
        "a_name": a.name, "b_name": b.name,
        "param_diffs": diff_params,
        "metric_diffs": metrics_diff,
        "seed_diff": seed_diff,
        "a_seed": a.seed, "b_seed": b.seed,
        "same_seed": not seed_diff,
    }


def compare_branches(exp_list_a: List[Experiment], exp_list_b: List[Experiment]) -> Dict[str, Any]:
    pairs = []
    n = min(len(exp_list_a), len(exp_list_b))
    for i in range(n):
        pairs.append(compare_experiments(exp_list_a[i], exp_list_b[i]))
    return {"pairs": pairs, "count_a": len(exp_list_a), "count_b": len(exp_list_b)}
