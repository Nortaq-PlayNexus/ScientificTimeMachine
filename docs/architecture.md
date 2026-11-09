# Architecture

Scientific Time Machine is a PySide6 desktop application with a content-addressed experimental history engine.

## Layers

- Core engine (src/scientific_time_machine/core/): storage, experiment data model, snapshots, branches, deterministic replay, comparison, experiment packages, recovery.
- App controller (src/scientific_time_machine/app.py): ties storage, snapshots, branches, replay and comparison together.
- UI (src/scientific_time_machine/ui/main_window.py): PySide6 tabs - Timeline, Experiment Graphs, Simulation Viewer, Snapshot Browser, Comparison Dashboard, Create / Branch.

## Data model

- Experiments: id, name, branch_name, parent_id, seed, params, state, metadata, snapshot_hash.
- Storage: SQLite index + SHA-256 content-addressed blobs.
- Every snapshot create writes an immutable blob and a SQLite record. Restore verifies both hashes.

## Branching

A branch is created from an existing experiment; the new experiment references the parent id, copies seed/params/state, and lives on its own branch. Modifying a branch never mutates the original history.
