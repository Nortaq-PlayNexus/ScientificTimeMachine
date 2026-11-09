# SCIENTIFIC TIME MACHINE

Scientific experiment management platform functioning like version control for computational experiments.

## Features
- Persistent experiment snapshots (content-addressed, integrity-checked)
- Branching histories from any prior experiment
- Parameter versioning
- Deterministic random seeds
- Simulation replay
- Branch comparisons
- State restoration
- Reproducible experiment packages (zip export/import)
- Corruption recovery and history reconstruction

## Run
```
python main.py
```
Or use the Windows EXE in dist/ScientificTimeMachine/.

## Tests
```
$env:PYTHONPATH="src"; python -m pytest -q
```

## License
MIT
