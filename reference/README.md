## Reference Files

This folder contains only the Autoresearch-specific reference implementation.

Included:

- `ui/Autoresearch.tsx`
- `ui/AutoresearchPanel.tsx`
- `runtime/paperclip_autoresearch_runner.py`
- `runtime/autoresearch_orchestrator.py`

These are copied from the working Paperclip fork to document the current feature boundary without bundling unrelated project changes.

The runtime reference is now plan-first and compaction-aware:

- the parent contract carries a `planPath`
- round issues explicitly re-anchor to that plan after compaction
- the UI reference surfaces plan status and rubric visibility
- every round writes a structured result JSON using `docs/RESULT_SCHEMA.md`
