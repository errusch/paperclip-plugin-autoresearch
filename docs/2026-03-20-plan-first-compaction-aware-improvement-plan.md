# Paperclip Autoresearch Plugin Improvement Plan

Date: 2026-03-20

## Why This Exists

The current `paperclip-plugin-autoresearch` repo has the right instinct, but it still reads more like a strong experiment than a finished Paperclip plugin. The fastest way to improve it is to stop treating long agent runs as self-contained and start treating the plan file as the durable source of truth.

This is the key lesson from Onur Solmaz's recent workflow notes on agent compaction:

- major work should begin with an implementation plan
- the plan should be saved in the repo
- the execution prompt should explicitly tell the agent to re-read the plan after compaction
- testing, review, and final reporting should be part of the execution contract, not optional cleanup

For this plugin, that means the product should become:

- plan-first
- compaction-aware
- Apple Silicon friendly by default
- remote-GPU extensible later

## Product Truth

The plugin should help a user do three things well:

1. Create or validate an autoresearch plan before a long run starts.
2. Re-anchor the agent to that plan whenever context compresses or a new run resumes.
3. Produce a useful final artifact with explicit testing and review notes instead of a vague "research finished" ending.

If it does not solve those three things, it is still a demo.

## Constraints

- The current local machine does not have NVIDIA hardware.
- The first-class path must work on Apple Silicon without CUDA.
- Any GPU-heavy path should be framed as optional remote execution on rented infrastructure later.
- We should not pretend local CUDA is part of the baseline.

## What We Should Improve

### 1. Make plans a first-class input

The plugin should not only run research. It should either:

- create a research plan file up front, or
- require an existing plan file and validate it before execution

The plan should live in the repo under a predictable path such as:

- `docs/YYYY-MM-DD-topic-plan.md`
- `experiments/YYYY-MM-DD-topic-plan.md`

### 2. Add a compaction-safe execution contract

Long runs should always include instructions like:

- re-read the plan if context compaction happens
- assess current state before continuing
- finish to completion
- state explicitly what was tested and what was not tested

This should be built into the plugin workflow, not left to user memory.

### 3. Improve the final artifact

Every run should end with a structured result:

- summary of what was researched
- output locations
- what was validated locally
- what still needs staging, prod, or human review
- clear next actions

### 4. Separate baseline from future acceleration

The plugin should have two clear operating modes:

- baseline: Apple Silicon / local-safe mode
- optional future mode: remote rented GPU execution

The repo should not blur those together.

### 5. Tighten the Paperclip product surface

The plugin needs a clearer story about:

- who it is for
- what it does better than a plain issue assignment
- what inputs it expects
- what outputs it guarantees

## Review Questions For The Team

Each review lane should answer:

1. What is already good and should be preserved?
2. What currently feels experimental or underspecified?
3. What would make this genuinely installable and trustworthy?
4. What should the Apple Silicon baseline be?
5. What remote compute path, if any, is worth designing for later?

## Execution Order

1. Review repo truth, UX, ops, commercial shape, and technical boundaries.
2. Produce one ranked improvement plan.
3. Implement the highest-value fixes first:
   - plan-first workflow
   - compaction-aware prompt/runner behavior
   - better result artifacts
   - clearer baseline docs
4. Only then evaluate optional rented-GPU extensions.

## Definition Of Better

We should consider this improved only if:

- a user can understand the plugin quickly
- a long autoresearch run can survive compaction without drifting
- the result artifact is specific and reviewable
- the baseline works on Apple Silicon
- the future GPU story is honest instead of hand-wavy
