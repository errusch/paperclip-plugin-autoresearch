# Implementation Plan Template

Use this as the starting point for any serious autoresearch lane.

## Goal

What is the exact improvement goal for this loop?

## Current artifact

- path:
- current winner or baseline:
- why this artifact matters:

## Outputs required each round

- candidate file
- memo file
- result JSON
- one TSV row in `results.tsv`

## Constraints

- what must not change:
- what would count as drift:
- what the loop must stay focused on:

## Scoring rubric

Use the default rubric or define a custom one here.

## Stop rule

Stop when:

- round budget reached
- no-improvement streak reached
- time budget reached
- operator stops the lane

## Verification rule

Each round must explicitly state:

- what was tested locally
- what still needs staging or human review
- blockers

## Notes for compaction recovery

If context compaction happens:

1. re-read this plan
2. assess the latest completed round
3. inspect the last candidate, memo, and result row
4. continue from there instead of starting over
