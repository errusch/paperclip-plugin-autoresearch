# Plugin Boundary

This is the clean boundary for turning the current Autoresearch work into a real Paperclip plugin once the plugin runtime exists.

## Plugin-Owned Surface

These pieces should belong to the standalone plugin:

- the `Autoresearch` Work page
- Autoresearch panel components
- runtime-mode display
- round history
- winner preview
- loop contract display

## Shared Contracts

These contracts should stay stable between Paperclip core and the plugin:

- autoresearch display state
- issue experiment contract shape
- dashboard summary payload for autoresearch lanes
- artifact references and round metadata

## What Stays In Paperclip Core

Paperclip core should keep control of:

- issue lifecycle
- heartbeat persistence
- approvals
- budgets
- routing
- canonical summary APIs

## What Stays Local

These parts are real but should not be confused with the reusable plugin:

- local runner scripts
- OpenClaw wake logic
- local workspace conventions
- Apple Silicon-specific fallback harnesses
- OESS-specific team assumptions

## Honest Packaging Story

The right message is:

- the feature is real
- the Paperclip-facing boundary is now clean
- the plugin runtime still needs to exist before this becomes a true installable package
