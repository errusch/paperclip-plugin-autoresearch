# Result Schema

Every round should leave one structured result JSON next to the candidate and memo.

Default path:

- `round-###-result.json`

## Required shape

```json
{
  "summary": "One short paragraph about what changed and why it matters.",
  "outputs": {
    "candidatePath": "/absolute/path/to/round-003-candidate.md",
    "memoPath": "/absolute/path/to/round-003-memo.md",
    "testResults": "Optional one-line summary of local checks"
  },
  "verification": {
    "testedLocally": true,
    "needsStaging": false,
    "needsHumanReview": true,
    "blockers": []
  },
  "nextActions": [
    "If kept, promote this candidate to the current winner.",
    "If discarded, tighten the plan around the weakest scoring dimension."
  ]
}
```

## Field rules

- `summary`
  - required
  - one short paragraph
  - explain the candidate, not the whole project history

- `outputs.candidatePath`
  - required
  - absolute path to the candidate file for this round

- `outputs.memoPath`
  - required
  - absolute path to the memo file for this round

- `outputs.testResults`
  - optional
  - short text only
  - name the check that ran or say why nothing ran

- `verification.testedLocally`
  - required boolean
  - `true` only if the round actually ran a meaningful local check

- `verification.needsStaging`
  - required boolean
  - `true` if the result still needs staging or hosted verification

- `verification.needsHumanReview`
  - required boolean
  - `true` if a human should inspect the candidate before promotion

- `verification.blockers`
  - required array
  - list concrete blockers only; use `[]` when clear

- `nextActions`
  - required array
  - 1-3 concrete next steps

## What good looks like

- the JSON is enough for a human reviewer to understand the round without reading the full transcript
- testing claims are specific
- blockers are honest
- next actions are immediately actionable
