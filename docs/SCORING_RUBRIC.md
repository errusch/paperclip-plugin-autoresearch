# Scoring Rubric

This rubric exists so operators can understand what a score means before a lane starts running.

## Default dimensions

Score each candidate on a 0-10 scale in these dimensions:

1. **Artifact quality**
   - Is the candidate actually better than the previous winner?
   - Is the change specific, reviewable, and useful?

2. **Plan adherence**
   - Did the round stay inside the implementation plan?
   - Did it drift or start over after compaction?

3. **Verification quality**
   - Are testing notes explicit?
   - Are blockers or staging needs clearly stated?

4. **Operator trust**
   - Is the output understandable by a human reviewer?
   - Are the claims proportional to what the candidate actually did?

## Default weighting

- Artifact quality: 40%
- Plan adherence: 25%
- Verification quality: 20%
- Operator trust: 15%

If you use a different weighting, write it into the plan file before the lane starts.

## Example interpretation

- `9.0+` = keep unless there is an obvious hidden regression
- `7.5 - 8.9` = strong contender, usually worth keeping
- `6.0 - 7.4` = useful but not clearly better yet
- `< 6.0` = usually discard unless it reveals something important

## What the score is not

- It is not a raw model-confidence number.
- It is not a measure of how much work happened.
- It is not proof that the result is production-ready.

The score only answers one question:

> Is this candidate better than the current winner under the stated plan and rubric?
