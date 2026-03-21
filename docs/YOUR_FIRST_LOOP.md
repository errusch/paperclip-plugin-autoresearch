# Your First Autoresearch Loop

This is the fastest honest path to a first useful loop.

## Step 1: Pick one mutable artifact

Good first artifacts:

- a README
- one landing page
- one system prompt
- one short product brief

Bad first artifacts:

- an entire codebase
- a vague product strategy
- three unrelated documents at once

## Step 2: Create the plan file

Start from:

- [IMPLEMENTATION_PLAN_TEMPLATE.md](./IMPLEMENTATION_PLAN_TEMPLATE.md)

Put the file in the repo, for example:

- `docs/2026-03-21-readme-improvement-plan.md`

The plan should include:

- goal
- current artifact
- desired outputs
- rubric
- stop rule

## Step 3: Create the parent issue

The parent issue should clearly state:

- what artifact is being improved
- where the plan file lives
- what counts as a win
- what should not change

## Step 4: Start one round

For a good first loop:

- keep the budget small
- run one round
- inspect the candidate, memo, and result row

Do not run five rounds before you trust the loop.

## Step 5: Review the outputs

After one round, you should be able to inspect:

- the candidate file
- the memo file
- the result row in `results.tsv`
- the result JSON file following [RESULT_SCHEMA.md](./RESULT_SCHEMA.md)

If you cannot understand what happened from those artifacts, the loop is not trustworthy yet.

## Step 6: Decide keep or discard

Use the rubric, not vibes.

Ask:

- is the candidate actually better?
- did it follow the plan?
- is the verification honest?
- would I trust another round built on top of this?

## Step 7: Continue or stop

Continue only if:

- the loop is producing understandable artifacts
- the plan is still the right plan
- the score means something

Stop if:

- the plan is drifting
- the outputs are noisy
- the artifact choice was too broad
