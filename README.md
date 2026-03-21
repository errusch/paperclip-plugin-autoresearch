# paperclip-plugin-autoresearch

Autoresearch for Paperclip: a focused work surface for bounded improvement loops, winner tracking, round history, and clear runtime-mode visibility.

## Current Status

This repo is a **plugin candidate**, not a published standalone plugin.

What is true today:

- the Autoresearch feature works today inside a Paperclip source checkout
- the Paperclip-facing boundary is clean enough to package
- the standalone plugin runtime is still the missing piece

If you want the honest one-line version: **the product experience exists today; the installable plugin package does not yet.**

## Screenshots

### Live lane

![Autoresearch lane](./assets/autoresearch-lane.png)

### Live agents

![Autoresearch live agents](./assets/autoresearch-live-agents.png)

### Winner and history

![Autoresearch winner and history](./assets/autoresearch-history.png)

## Why It Exists

Autoresearch gives Paperclip a native place to run bounded improvement work on a single mutable artifact.

Instead of spreading this across ad hoc scripts and notes, it keeps the loop visible in the same system where teams already manage issues, runs, budgets, and review.

## What You Get

- an `Autoresearch` page inside `Work`
- bounded local team-round loops
- round history and timeline
- current winner preview
- contributor notes and why-it-won context
- runtime-mode labels and controls
- explicit local-vs-upstream status

## What Works Today

- `Autoresearch` page
- live badges in the main Paperclip UI
- `Apple Silicon (Local)` mode on Apple Silicon
- winner tracking
- keep/discard round history
- round-level contributor notes
- Settings controls for runtime modes
- plan-first contract in the reference runner
- compaction-aware round prompts in the reference runner
- operator docs for scoring, recovery, and first-loop setup

## Reference Implementation

This repo is intentionally scoped to the Autoresearch feature only.

The current reference files are included here:

- `reference/ui/Autoresearch.tsx`
- `reference/ui/AutoresearchPanel.tsx`
- `reference/runtime/paperclip_autoresearch_runner.py`
- `reference/runtime/autoresearch_orchestrator.py`

They show the current page/runtime shape without dragging in unrelated Paperclip work.

## Runtime Modes

| Mode | Meaning | Current state |
| --- | --- | --- |
| `Apple Silicon (Local)` | Paperclip-native local mode for Apple Silicon testing. | Working now |
| `Remote GPU (CUDA)` | Exact upstream `karpathy/autoresearch` on external rented NVIDIA/CUDA compute, synced back into Paperclip. | Planned |

## Prerequisites

Before you start, you need:

- **Node.js** 18+ for Paperclip UI development
- **pnpm** 8+ for dependency management
- **Python** 3.10+ for the reference runner
- **A Paperclip source checkout** to host the feature in a real app surface
- **macOS on Apple Silicon** for the baseline local path

What is not required for the baseline:

- local NVIDIA hardware
- CUDA on your MacBook
- a hosted runtime service

Those belong to a future remote GPU path, not the baseline.

## Install Story Today

Until the Paperclip plugin runtime lands, Autoresearch runs inside a Paperclip source checkout:

```bash
pnpm install
pnpm -r typecheck
pnpm --filter @paperclipai/server prepare:ui-dist
pnpm --filter @paperclipai/server dev --port 3100
```

Then open:

- `Work -> Autoresearch`
- `Settings -> Scheduler Heartbeats -> Autoresearch`

## Who Should Use This

Use this when:

- one mutable artifact needs repeated bounded improvement
- you want visible keep/discard history instead of ad hoc experiments
- you need the work to stay inside Paperclip governance and review
- you want a plan-first loop that can survive long runs and context compaction

Do not use this when:

- a normal issue with one assignee is enough
- there is no clear mutable artifact to improve
- you do not need iteration history or winner tracking
- the task is really just research notes with no ratchet toward a better candidate

## Configuration

Current runtime controls live in Paperclip Settings.

| Setting | Description |
| --- | --- |
| `Enable Remote GPU (CUDA)` | Allows lanes that read real upstream CUDA-backed Autoresearch state from rented compute. |
| `Enable Apple Silicon (Local)` | Allows the Apple Silicon-compatible local mode on this machine. |

## How The Loop Works

1. choose one mutable artifact
2. run a bounded round
3. collect contributor notes
4. keep one surviving candidate
5. write round history
6. continue until the stop rule or time budget is reached

The local implementation already writes the same classes of artifacts you would want to inspect in a real Autoresearch lane:

- `program.md` or another explicit implementation plan file
- `results.tsv`
- round candidates
- round memos
- round result JSON files
- contributor notes

Every serious loop should start from a plan file in the repo and tell the agent to re-read that file after compaction.

## Trust Surfaces

The repo now includes the core operator docs needed to trust the loop:

- [Scoring rubric](./docs/SCORING_RUBRIC.md)
- [Failure modes and recovery](./docs/FAILURE_MODES_AND_RECOVERY.md)
- [Your first autoresearch loop](./docs/YOUR_FIRST_LOOP.md)
- [Implementation plan template](./docs/IMPLEMENTATION_PLAN_TEMPLATE.md)
- [Result schema](./docs/RESULT_SCHEMA.md)

## Packaging Boundary

The intended split is:

- **plugin-owned UI**
  - `Autoresearch` Work page
  - Autoresearch panel and display components
- **shared Paperclip contracts**
  - autoresearch display state
  - dashboard summary payloads
  - issue experiment contracts
- **host/core responsibilities**
  - issue lifecycle
  - heartbeat persistence
  - approvals
  - budgets
  - routing
- **local-only runtime glue**
  - local runner scripts
  - local wake/orchestration logic
  - Apple Silicon fallback harnesses

More detail is in [docs/BOUNDARY.md](./docs/BOUNDARY.md).

## Known Limitations

- not yet a standalone installable plugin package
- exact upstream CUDA mode still needs external NVIDIA/CUDA compute
- local Apple Silicon mode proves the control surface and workflow, not the full upstream training runtime
- final packaging still depends on the Paperclip plugin runtime landing upstream
- the reference files show the contract and operator story; they are not yet a packaged runtime module

## Why This Could Belong In `awesome-paperclip`

The case for this project is simple:

- it extends Paperclip without creating a second system
- it keeps issues, governance, and review in the same surface
- it already has a truthful working story today
- it has a clear path from candidate to real plugin once the runtime exists

## Road To A Real Standalone Plugin

1. land the Paperclip plugin runtime
2. split the Autoresearch UI and shared contracts into a standalone package
3. keep local runner glue outside the reusable plugin
4. publish the repo
5. submit it to `awesome-paperclip`

## License

MIT

## Related Docs

- [docs/BOUNDARY.md](./docs/BOUNDARY.md)
- [docs/AWESOME_PAPERCLIP.md](./docs/AWESOME_PAPERCLIP.md)
- [docs/BENCHMARK.md](./docs/BENCHMARK.md)
- [docs/SCORING_RUBRIC.md](./docs/SCORING_RUBRIC.md)
- [docs/FAILURE_MODES_AND_RECOVERY.md](./docs/FAILURE_MODES_AND_RECOVERY.md)
- [docs/YOUR_FIRST_LOOP.md](./docs/YOUR_FIRST_LOOP.md)
- [docs/IMPLEMENTATION_PLAN_TEMPLATE.md](./docs/IMPLEMENTATION_PLAN_TEMPLATE.md)
- [docs/RESULT_SCHEMA.md](./docs/RESULT_SCHEMA.md)
