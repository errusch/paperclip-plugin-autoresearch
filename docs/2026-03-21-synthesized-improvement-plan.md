# Synthesized Improvement Plan: paperclip-plugin-autoresearch

Date: 2026-03-21
Status: Synthesis of 7 specialist reviews
Anchored to: docs/2026-03-20-plan-first-compaction-aware-improvement-plan.md

## Executive Summary

The plugin has a strong foundation with clean architecture, honest documentation, and a working Apple Silicon baseline. However, it currently feels like a well-engineered experiment rather than a production-ready product. The gap is primarily in **enforcement** (plan-first workflow), **trust surfaces** (failure modes, scoring rubric), and **operator onboarding** (prerequisites, first-loop walkthrough).

**Overall assessment:** 60% of the way to "better" per the plan document definition. The remaining 40% is achievable through focused implementation of P0 and P1 items without requiring upstream Paperclip work.

---

## Cross-Cutting Themes

All seven specialist reviews converged on these core gaps:

1. **Plan-first workflow is not enforced** - The runner creates program files but does not validate them before execution
2. **Compaction-aware prompts are missing** - No re-read instructions for long runs that survive context compression
3. **New user onboarding is underspecified** - Missing prerequisites, vague install steps, no concrete first-loop walkthrough
4. **Trust surfaces are weak** - Failure modes undocumented, scoring rubric invisible, recovery procedures missing
5. **Product boundaries are fuzzy** - Who should use this? When? What problem does it solve better than a normal issue?

---

## Part 1: Apple Silicon Baseline (Ship Now)

These improvements preserve and strengthen the local Apple Silicon path. Everything in this section works today on an M-series Mac without CUDA or external infrastructure.

### P0 - Critical (Ship This Week)

#### 1. Plan-First Runner Contract
**Source:** Technical architecture review, product truth review
**What:** Add `planPath` to contract schema with validation before execution

```python
# Add to contract schema:
planPath: str  # Required path to implementation plan
planValidatedAt: str | None
planReanchorOnCompaction: bool = True
```

**Implementation:**
- Require `planPath` before starting execution
- Validate plan exists and is readable
- Store plan content hash for change detection
- Auto-re-read plan on compaction/restart events
- Block execution if plan is missing or invalid

**Verification:**
- ✅ Every running lane has a visible plan file
- ✅ Runner logs show plan validation step
- ✅ UI displays plan path with validation status

---

#### 2. Compaction-Safe Prompt Template
**Source:** Product truth review, technical architecture review
**What:** Create a reusable template injected into every round issue

```markdown
# Execution Contract

You are continuing an autoresearch loop.

**CRITICAL: Re-anchor to plan**
1. Read the implementation plan at: `{planPath}`
2. Check current state in: `{resultsPath}`
3. Assess: What was the last completed round?
4. Assess: What is the next logical step?
5. Continue execution from there

**Do NOT:**
- Start from scratch
- Re-implement completed work
- Drift from the plan without explicit reason

**REQUIRED outputs:**
- One candidate artifact
- One round memo
- One TSV row with test/verification notes
```

**Implementation:**
- Add to runner initialization code
- Inject into all round issue descriptions
- Make non-optional for all autoresearch lanes

**Verification:**
- ✅ All round issues include compaction recovery section
- ✅ Agents re-read plan after compaction (visible in logs)
- ✅ No "started from scratch" drift in multi-round runs

---

#### 3. Missing Prerequisites Section
**Source:** Documentation quality review
**What:** Add explicit prerequisites to README

**Required content:**
```markdown
## Prerequisites

Before you start, you need:

- **Node.js** 18+ (for Paperclip UI)
- **pnpm** 8+ (for dependency management)
- **Python** 3.10+ (for the runner)
- **Paperclip source checkout** at `~/paperclip` (or your preferred location)
  - See: https://github.com/paperclip-ai/paperclip
- **macOS with Apple Silicon** (M-series Local mode)
  - Intel Macs work but are untested
  - Linux/Windows: not currently supported
```

**Verification:**
- ✅ New user can verify all prerequisites in < 2 minutes
- ✅ No guessing about versions or sources

---

#### 4. Failure Modes & Recovery Documentation
**Source:** UX/trust surfaces review
**What:** Add "What Can Go Wrong" section to README

**Required content:**
- Timeout handling (what happens if a round takes too long?)
- TSV corruption recovery (how to fix malformed results files?)
- Race conditions (multiple runners writing to same artifacts?)
- Crashed run recovery (how to resume from last known good state?)
- Plan drift detection (what if agent ignores the plan?)

**Verification:**
- ✅ Every known failure mode documented
- ✅ Recovery procedure for each failure mode
- ✅ User knows where to find logs

---

#### 5. Surface the Scoring Rubric
**Source:** UX/trust surfaces review
**What:** Make scoring criteria visible to operators

**Implementation:**
- Add `docs/SCORING_RUBRIC.md` explaining what is measured
- Add tooltip in UI showing what each score dimension means
- Include sample scores with explanations

**Verification:**
- ✅ User can see scoring criteria before starting a run
- ✅ Scores are interpretable without reading source code

---

### P1 - Important (Ship Next Week)

#### 6. Structured Result Artifact Schema
**Source:** Technical architecture review, product truth review
**What:** Define minimum result schema for every round

```typescript
interface AutoresearchResult {
  summary: string;
  outputs: {
    candidatePath: string;
    memoPath: string;
    testResults?: string;
  };
  verification: {
    testedLocally: boolean;
    needsStaging: boolean;
    needsHumanReview: boolean;
    blockers: string[];
  };
  nextActions: string[];
}
```

**Verification:**
- ✅ Every round produces structured result artifact
- ✅ Result includes explicit testing/review notes
- ✅ Next actions are clear and actionable

---

#### 7. "Your First Autoresearch Loop" Walkthrough
**Source:** Documentation quality review
**What:** Add step-by-step tutorial for new users

**Required sections:**
1. Create your first plan file (with template)
2. Set up your first experiment (with screenshots)
3. Run one round (with expected output)
4. Review the results (with interpretation guide)
5. Pick a winner (with promotion steps)

**Verification:**
- ✅ New user completes first loop in < 30 minutes
- ✅ No guessing about file formats or locations

---

#### 8. Better Naming - Remove Jargon
**Source:** UX/trust surfaces review
**What:** Rename confusing terms

| Current | Better |
|---------|--------|
| "M-series Local" | "Apple Silicon (Local)" |
| "Actual Upstream (CUDA)" | "Remote GPU (CUDA)" |
| "experimentContract" | "Loop Config" or "Research Plan" |
| "generations" | "Iterations" or "Rounds" |

**Verification:**
- ✅ All UI labels audited for jargon
- ✅ New user understands terms without AI background

---

#### 9. Display Name & Product Positioning
**Source:** Concept variants review, commercial positioning review
**What:** Clarify product surface

**Implementation:**
- Add display name: "Improvement Loop Workbench"
- Add tagline: "Iterate on AI outputs with visible winner tracking and round history"
- Add "Who Should Use This" section to README
- Add "When To Use This vs Normal Issues" decision guide

**Verification:**
- ✅ New user understands product value in < 30 seconds
- ✅ Clear boundaries between autoresearch and normal workflows

---

#### 10. Extract Orchestration Layer
**Source:** Technical architecture review
**What:** Split runner into cleaner concerns

```python
# autoresearch_orchestrator.py
class AutoresearchOrchestrator:
    def validate_plan(self, plan_path: str) -> bool:
        # Check plan exists, readable, well-formed
        pass
    
    def spawn_round(self, parent_issue, contract):
        # Create round issues
        pass
    
    def finalize_round(self, parent_issue, contract, results):
        # Process round completion
        pass
```

**Verification:**
- ✅ Runner code under 200 lines (orchestration extracted)
- ✅ Core logic testable in isolation

---

#### 11. Plan-Aware UI Indicators
**Source:** Technical architecture review
**What:** Show plan status in UI

```tsx
{experiment.planPath && (
  <div className="flex items-center gap-2">
    <FileText className="h-3.5 w-3.5 text-muted-foreground/70" />
    <span className="text-muted-foreground">Plan:</span>
    <span className="font-medium text-cyan-600" title={experiment.planPath}>
      {pathTail(experiment.planPath)}
    </span>
    {experiment.planValidatedAt && (
      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
    )}
  </div>
)}

{!experiment.planPath && experiment.status === 'running' && (
  <div className="text-xs text-amber-600">
    ⚠️ No plan file - compaction risk
  </div>
)}
```

**Verification:**
- ✅ UI shows plan status for all running lanes
- ✅ Warning visible for lanes without plans

---

### P2 - Nice to Have (Ship When Ready)

#### 12. Empty-State UX Improvements
**Source:** UX/trust surfaces review
**What:** Add CTAs for empty states

- "Create your first experiment" button when no experiments exist
- Guidance text for each empty state
- Links to documentation from empty states

---

#### 13. Architecture Diagram
**Source:** Documentation quality review
**What:** Add visual diagram showing UI → runtime → artifacts flow

---

#### 14. GIF Demo for README
**Source:** Commercial positioning review
**What:** Add animated screenshot showing round completion

---

#### 15. Troubleshooting Section Expansion
**Source:** Documentation quality review
**What:** Expand troubleshooting beyond failure modes

- Common error messages and fixes
- Performance tuning tips
- Log location and interpretation

---

## Part 2: Future Extensions (Clearly Separated)

These items are explicitly deferred to a future phase. They should NOT block the Apple Silicon baseline improvements above.

### Future Phase 1: Remote GPU Support

**Prerequisite:** Real user demand for CUDA workloads

**What:**
- Add "Remote GPU (CUDA)" runtime mode behind feature flag
- Implement Control Tower / Dumb Worker model:
  - Apple Silicon Mac = Control Tower (runs Paperclip UI + Agent)
  - Remote CUDA instance = Dumb Worker (execution target only, no Paperclip/Agent install)
- Add SSH/API-based remote dispatch to runner

**Implementation notes:**
- Clean runner abstraction supporting local execution (baseline) and remote dispatch
- Remote instance does NOT run Paperclip/Agent - strictly dumb execution
- All orchestration happens on Apple Silicon Control Tower

**Verification:**
- ✅ Remote execution works without installing Paperclip on remote instance
- ✅ Control Tower maintains full visibility and control
- ✅ Apple Silicon baseline remains untouched

---

### Future Phase 2: Hosted Compute Service

**Prerequisite:** Validated demand from open-source adoption

**What:**
- Build hosted CUDA runtime as separate service
- Free OSS plugin connects to paid hosted compute
- Charge for convenience and scale, not core loop

**Honest narrative:**
> "The plugin is free and runs locally on your M-series Mac. If you want to skip the CUDA setup and run bigger experiments on rented compute, we offer a hosted runtime that plugs into the same open-source plugin."

---

## What NOT to Do (Avoid Overengineering)

1. **Don't build a plan editor** - Use existing markdown files
2. **Don't create a rigid plan schema** - Keep it flexible markdown
3. **Don't build GPU orchestration yet** - Wait for real demand
4. **Don't over-abstract the runner** - Simple extraction is enough
5. **Don't add plan versioning** - Git handles that

---

## Implementation Order

### Week 1 (P0 Items)
1. Add plan-first runner contract with validation
2. Add compaction-safe prompt template
3. Add prerequisites section to README
4. Add failure modes documentation
5. Surface scoring rubric

**Ship:** Baseline improvements that make the plugin trustworthy for long runs

### Week 2 (P1 Items)
1. Add structured result artifact schema
2. Add "Your First Loop" walkthrough
3. Rename jargon terms
4. Add display name and positioning
5. Extract orchestration layer
6. Add plan-aware UI indicators

**Ship:** Complete onboarding experience for new users

### Week 3+ (P2 Items)
1. Empty-state improvements
2. Architecture diagram
3. GIF demo
4. Expanded troubleshooting

**Ship:** Polish and documentation completeness

### Future (After User Validation)
1. Remote GPU support
2. Hosted compute service

---

## Success Criteria

We will know this is improved when:

- ✅ Every running lane has a visible, validated plan file
- ✅ Compaction events show plan re-read in logs
- ✅ New user completes first loop in < 30 minutes without guessing
- ✅ Failure modes and recovery procedures are documented
- ✅ Scoring rubric is visible and interpretable
- ✅ Round memos include structured testing/verification notes
- ✅ UI clearly shows which lanes are plan-protected
- ✅ Apple Silicon baseline works perfectly without CUDA
- ✅ Remote GPU path is clearly separated and optional

---

## Recommended Move

**Implement all P0 items this week.** These are low-effort, high-trust changes that do not require upstream Paperclip work and directly address the three core gaps: plan-first enforcement, compaction-aware execution, and operator trust.

P1 items can ship the following week once P0 is verified working.

Defer all future extensions (remote GPU, hosted compute) until real user demand is validated through open-source adoption.
