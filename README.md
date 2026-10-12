# Yukti

Yukti is a local-first research prototype for deciding what information should
become persistent model knowledge. It keeps candidate information separate
from approved long-term memory and records each governance decision.

## Current prototype

The first milestone is a small, inspectable governance and memory core. It uses
only Python's standard library and SQLite, so it can be developed without
downloading a model or consuming the project's 20 GB storage allowance.

- Capture candidate knowledge with source and trust metadata.
- Run transparent, configurable checks for missing evidence, low trust,
  duplicates, and possible contradictions.
- Review candidates explicitly; approval is required before promotion to
  long-term memory.
- Search working and long-term memory and inspect an append-only decision log.

These checks are triage signals, not proof that a claim is true or safe. The
initial contradiction check is deliberately conservative and lexical; human
review remains in the loop. Model adaptation, benchmark gates, model
versioning, and rollback are planned milestones and are not yet implemented.

## Requirements

- Python 3.10 or newer
- No third-party packages for the governance CLI
- Default SQLite database: `data/yukti.sqlite3` (created on first use)

The database can be placed elsewhere with `--db`. Do not put secrets or
sensitive personal data in it unless you have reviewed the storage and backup
requirements for your environment.

## Quick start

From the repository root:

```powershell
py -3 --version
py -3 -m yukti --help
```

The module is under `src`; run it directly without installing:

```powershell
$env:PYTHONPATH = "src"
py -3 -m yukti --help
py -3 -m yukti add --text "Example fact to review" --source "https://example.org/page" --trust 0.8
py -3 -m yukti list
py -3 -m yukti review 1 --decision approve --by "researcher"
py -3 -m yukti promote 1
py -3 -m yukti search "Example fact"
```

Use `--db path\to\file.sqlite3` on every command to choose a database. The
default database and generated data are ignored by Git.

## Disk and hardware budget

The first milestone has no model weights and uses negligible disk space. This
keeps the prototype well below the 20 GB project budget while we establish and
evaluate governance behavior. When adding local models, select and measure
their on-disk footprint before downloading; model caches and duplicate
checkpoints must count toward the same budget. The reported 4 GB GPU memory
also means training should be an optional, later milestone using a small model
and adapter-only updates.

## Roadmap

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for the detailed
10-step plan, deliverables, exit gates, final verification matrix, and report
requirements. Track project actions and observed results in
[LOGBOOK.md](LOGBOOK.md); add an entry as work is performed.
The current requirements baseline and open decisions are in
[REQUIREMENTS.md](REQUIREMENTS.md).

## Governance semantics

An item starts as `pending`. Automatic checks may attach flags but never
approve it. A reviewer can approve or reject it, and only an approved item can
be promoted. Each review and promotion is recorded with a timestamp and actor.
No current command trains a model or deploys an artifact.
