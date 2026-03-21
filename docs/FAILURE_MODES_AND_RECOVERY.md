# Failure Modes and Recovery

This is the operator guide for what can go wrong and how to recover without losing the loop.

## 1. Timeout or wall-clock overrun

What it looks like:

- a round stays `executing` too long
- the captain misses the round deadline
- contributor notes arrive late or not at all

What to do:

1. inspect the active round issue and recent logs
2. if the round has clearly stalled, cancel the run
3. re-read the plan file
4. resume from the last completed round instead of starting over

## 2. Missing or invalid plan

What it looks like:

- no plan file exists
- the plan is extremely short or vague
- the run drifts because there is no stable anchor

What to do:

1. stop the lane
2. create or repair the plan file
3. validate that it has:
   - goal
   - outputs
   - stop rule
   - scoring expectation
4. restart the loop only after the plan is in place

## 3. TSV corruption

What it looks like:

- `results.tsv` has malformed rows
- columns shift
- score parsing fails

What to do:

1. copy the broken file first
2. fix the header back to:
   - `round	score	status	description	candidate_path	memo_path	started_at	finished_at`
3. repair or remove malformed rows
4. rerun only the affected round if needed

## 4. Crashed run recovery

What it looks like:

- a run disappears mid-round
- the issue is still open but outputs are partial
- the next agent wake is missing context

What to do:

1. inspect the plan
2. inspect the most recent candidate, memo, and result artifacts
3. determine the last fully completed round
4. restart from the next round, not from scratch

## 5. Plan drift

What it looks like:

- the agent starts inventing new subproblems
- output no longer matches the plan
- candidate changes are flashy but not relevant

What to do:

1. stop the lane
2. comment on the issue with the exact drift
3. tell the next run to re-read the plan and assess current state first
4. tighten the plan if it is underspecified

## 6. Multiple runners touching the same loop

What it looks like:

- duplicate wakeups
- more than one lane trying to own the same artifact
- conflicting candidates or memo paths

What to do:

1. ensure one parent issue owns the loop
2. ensure one active captain issue owns the current round
3. cancel duplicate runs
4. resume from the surviving round state

## 7. Remote GPU confusion

What it looks like:

- someone assumes CUDA is part of the default setup
- the local Mac is treated like a GPU box

What to do:

1. keep Apple Silicon local mode as the baseline
2. treat remote GPU as a future optional executor only
3. do not let remote compute become a hidden prerequisite
