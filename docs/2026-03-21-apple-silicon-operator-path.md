# Apple Silicon Operator Path & CUDA Separation

**Date:** 2026-03-21
**Author:** Nora (COO)
**Status:** Review Complete

## Objective
Review the runtime and installation story for `paperclip-plugin-autoresearch` on an Apple Silicon MacBook, strictly separating the local operational baseline from remote NVIDIA/CUDA dependencies, and identifying the cleanest execution path.

## The Reality of the Hardware Split
Eric's local machine is an Apple Silicon MacBook. It is excellent for orchestration, planning, text-based LLM agent loops, and reviewing artifacts. It cannot run upstream `karpathy/autoresearch` or heavy CUDA-bound training workloads natively.

If we blur the line between "agent orchestration" and "model training," the plugin will be brittle and un-installable.

## The Cleanest Operator Path: The "Control Tower" Model
The cleanest operational path is to treat the Apple Silicon MacBook as the **Control Tower** and the rented GPU as a **Dumb Worker**. 

1. **Local Apple Silicon (The Control Tower)**
   - Runs the Paperclip plugin UI.
   - Runs the OpenClaw agent and the Autoresearch orchestration loop.
   - Generates the improvement plans, writes the code modifications, and handles compaction recovery.
   - Evaluates the final metrics and manages the `Autoresearch` loop state.

2. **Rented Remote NVIDIA/CUDA (The Dumb Worker)**
   - Only used for heavy execution (e.g., Lambda Labs, RunPod).
   - Does *not* run Paperclip, OpenClaw, or the agent loops.
   - The local agent dispatches the trial to the remote GPU via SSH or API, waits for the `results.tsv` and artifacts, and syncs them back to the local workspace.

## Required Plugin Architecture Changes
To support this operator path natively, the plugin needs to explicitly separate the **Runner** from the **Evaluator**:

### 1. Local Baseline Mode (M-series Local)
- **What it does:** Bypasses heavy ML training. Used for prompt engineering, script debugging, or lightweight CPU/MPS-compatible testing.
- **Operator action:** Agent runs the trial script locally, gathers results, and loops. Zero external dependencies.

### 2. Remote GPU Mode (Actual Upstream CUDA)
- **What it does:** Agent writes the code/plan locally, then uses an executor to run the actual workload on a rented GPU box.
- **Operator action:** 
  1. Agent bundles the trial directory.
  2. Agent pushes it to the remote CUDA instance (via `rsync` or API).
  3. Remote instance executes the trial.
  4. Agent pulls the resulting metrics back to the MacBook.
  5. Agent evaluates the metrics locally.

## Next Actions for Execution
1. **Runner Abstraction:** Update the runtime reference (`paperclip_autoresearch_runner.py`) to include a clean abstraction for `dispatch_trial()`. It should default to `local_subprocess` but support a `remote_ssh` strategy.
2. **Dependency Hygiene:** Ensure the local environment does not attempt to install CUDA bindings.
3. **Settings Update:** If the user enables the remote GPU mode, the plugin settings should only require an SSH host alias or API key, avoiding complex remote Paperclip installations.
