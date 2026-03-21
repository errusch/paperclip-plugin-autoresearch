# Product Truth Review: paperclip-plugin-autoresearch

**Reviewer:** Thomas Mason (CEO Agent)
**Date:** 2026-03-21
**Anchored to:** docs/2026-03-20-plan-first-compaction-aware-improvement-plan.md

---

## Executive Summary

The plugin has the right instincts and a clean architecture, but it still reads more like a strong experiment than a finished product. The most important gap is **plan-first execution**: the runner creates program files, but doesn't enforce plan validation or compaction-safe re-anchoring as part of the execution contract.

**What works:**
- Clean Paperclip boundary
- Apple Silicon baseline is real and operational
- Runtime mode separation is honest
- Round history and winner tracking work
- Team-round orchestration is sophisticated

**What needs work:**
- Plan-first workflow is not enforced
- Compaction-aware prompts are missing
- Final artifacts lack explicit testing/validation notes
- Install story is still "inside a Paperclip source checkout"

---

## 1. Plan-First Assessment

**Current State:** 🟡 Partial

**What exists:**
- The runner creates `program.md` files automatically
- Program files contain loop semantics and constraints
- Experiment directories are structured with predictable paths

**What's missing:**
- No validation that a plan exists before execution starts
- No requirement to re-read the plan after compaction
- No explicit contract that the agent must "anchor to plan" when resuming

**Recommendation:**
The runner should enforce:
1. Either require an existing `program.md` OR validate it before marking the contract as `running`
2. Add explicit instructions in child round issues: "If context compaction occurs, re-read `{programPath}` before continuing"
3. Add a `planValidatedAt` timestamp to the contract to prove the check happened

**Evidence:**
- `ensure_program_file()` in runner creates but doesn't validate
- `spawn_round()` description includes "Read `{contract['programPath']}`" but doesn't mention compaction recovery

---

## 2. Compaction-Aware Assessment

**Current State:** 🔴 Missing

**What exists:**
- None of the round issue descriptions mention compaction recovery
- No instructions to "re-anchor to plan" if context compresses
- No explicit "finish to completion" contract
- No requirement to state what was tested vs not tested

**What's needed:**
Every round issue description should include compaction-safe instructions:

```
## Compaction Recovery
If context compaction occurs:
1. Re-read the plan at `{programPath}`
2. Assess current state before continuing
3. Finish to completion
4. State explicitly what was tested and what was not tested
```

**Evidence:**
- Lines 411-440 in runner: round descriptions mention reading the plan once, but not re-reading after compaction
- No "finish to completion" language anywhere in the runner

---

## 3. Apple Silicon Friendly by Default

**Current State:** 🟢 Strong

**What exists:**
- `M-series Local` mode is the default and works today
- No CUDA dependencies in package.json
- Runner respects `autoresearchEnableMSeriesLocal` setting
- Runtime modes are clearly separated in the UI
- Documentation explicitly states: "the baseline works on Apple Silicon"

**What's good:**
- The plugin doesn't try to install CUDA bindings locally
- `sourceMode` defaults to `m_series_local`
- The runner has a clean abstraction for source modes
- Nora's Apple Silicon operator path doc (2026-03-21) correctly identifies the "Control Tower" model

**Minor improvement:**
- The README could be more explicit: "No CUDA required for M-series Local mode"
- The install instructions still assume a Paperclip source checkout, which is a separate issue

**Evidence:**
- package.json has zero CUDA dependencies
- Runner lines 784-791: pauses local contracts if M-series mode is disabled
- Lines 88-94: defaults to `m_series_local` and `local_mps` runtime

---

## 4. Honest About Future Rented GPU Paths

**Current State:** 🟢 Strong

**What exists:**
- Runtime modes table clearly labels `Actual Upstream (CUDA)` as "Planned"
- Documentation explicitly states: "exact upstream CUDA mode still needs external NVIDIA/CUDA compute"
- No pretense that local CUDA is part of the baseline
- Nora's doc correctly separates Control Tower (local) from Dumb Worker (remote)

**What's good:**
- The honesty is refreshing: "the product experience exists today; the installable plugin package does not yet"
- Clear separation between what works now vs what's future work
- No hand-wavy promises about "just rent a GPU and it works"

**What's needed for the future path:**
- Runner abstraction for `dispatch_trial()` with `local_subprocess` and `remote_ssh` strategies
- Settings UI for SSH host alias or API key (not a full remote Paperclip install)
- Dependency hygiene to ensure no CUDA bindings leak into local environment

**Evidence:**
- README lines 63-66: Runtime Modes table is honest about current vs planned
- Lines 87-90: Known Limitations section is explicit about what's missing
- Nora's doc (2026-03-21) provides the correct architecture for the future path

---

## 5. Final Artifact Quality

**Current State:** 🟡 Partial

**What exists:**
- `results.tsv` with structured columns (round, score, status, description, paths, timestamps)
- Round memos at `round-{N}-memo.md`
- Candidate files at `round-{N}-candidate.md`
- Contributor notes in team-round mode

**What's missing:**
- No explicit "what was validated locally" section
- No "what still needs staging/prod/human review" notes
- No clear next actions at the end of a run
- The loop just stops with status `completed` or `exhausted` without a final summary artifact

**Recommendation:**
Add a `final-report.md` artifact when the loop completes:

```markdown
# Autoresearch Final Report

## Summary
- Rounds completed: X
- Best score: Y
- Winner: {path}

## What Was Tested
- [explicit list of validations performed]

## What Still Needs Review
- [explicit list of gaps]

## Next Actions
- [clear next steps for the human or next agent]
```

---

## 6. Install Reality

**Current State:** 🔴 Not Installable

**The honest truth:**
- The README correctly states: "not yet a standalone installable plugin package"
- Current install requires a full Paperclip source checkout
- The plugin runtime doesn't exist yet upstream

**What needs to happen:**
1. Land the Paperclip plugin runtime
2. Package the Autoresearch UI and contracts as a standalone npm package
3. Publish to npm registry
4. Submit to `awesome-paperclip`

**This is not a criticism of the plugin itself** — it's a dependency on upstream Paperclip work. The plugin is correctly structured to be packaged once the runtime exists.

---

## Ranked Improvement Plan

Based on the plan document and my review, here's the prioritized list:

### P0: Critical for Product Truth
1. **Add compaction-aware instructions to round issues** (missing today)
   - Add "Compaction Recovery" section to all round descriptions
   - Explicitly tell agents to re-read plan after compaction
   - Add "finish to completion" contract

2. **Enforce plan-first validation** (partial today)
   - Validate `program.md` exists before marking contract as `running`
   - Add `planValidatedAt` timestamp to contract

### P1: Important for Trust
3. **Improve final artifacts** (partial today)
   - Add `final-report.md` when loop completes
   - Include explicit "what was tested" and "what needs review" sections
   - Add clear next actions

### P2: Nice to Have
4. **Strengthen Apple Silicon messaging** (already good)
   - Add "No CUDA required" to README for M-series mode
   - Document the Control Tower model more prominently

5. **Prepare remote GPU abstraction** (already honest)
   - Add `dispatch_trial()` runner abstraction
   - Keep it behind a feature flag until tested

---

## What Should Be Preserved

- Clean Paperclip boundary (don't change this)
- Apple Silicon baseline as default (don't change this)
- Honest runtime mode separation (don't change this)
- Team-round orchestration sophistication (this is actually quite good)
- Round history and winner tracking (works well)

---

## What Currently Feels Experimental

- Plan-first enforcement (exists but not enforced)
- Compaction recovery (mentioned but not instructed)
- Final artifact structure (exists but incomplete)
- Install story (honest about not being installable yet)

---

## What Would Make This Genuinely Installable and Trustworthy

1. **Enforce plan-first workflow** — validate plans before execution, require re-read after compaction
2. **Add compaction-safe prompts** — every round issue should tell the agent how to recover from context compression
3. **Produce complete final artifacts** — explicit testing notes, review gaps, and next actions
4. **Wait for Paperclip plugin runtime** — then package and publish

---

## Definition of Better (Revisited)

The plan document defines "better" as:
- ✅ User can understand the plugin quickly (README is good)
- ❌ Long run can survive compaction without drifting (missing explicit instructions)
- 🟡 Result artifact is specific and reviewable (exists but incomplete)
- ✅ Baseline works on Apple Silicon (strong)
- ✅ Future GPU story is honest (strong)

**Overall assessment:** The plugin is 60% of the way to "better." The remaining 40% is primarily about enforcing plan-first behavior and adding compaction-safe prompts, plus waiting for the upstream plugin runtime.

---

## Recommended Move

Implement P0 items (compaction-aware instructions + plan validation) in the next sprint. These are low-effort, high-trust changes that don't require upstream Paperclip work. The P1 and P2 items can wait until after the plugin runtime lands.
