#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from autoresearch_orchestrator import (
    captain_prompt,
    contributor_prompt,
    plan_validation_summary,
    solo_round_prompt,
    validate_plan_file,
)

API_BASE = "http://127.0.0.1:3100/api"
COMPANY_ID = "478acbc9-2644-4c47-bbf4-c384afc0f76a"
LOCAL_TZ = ZoneInfo("America/Chicago")
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_TEAM_ROUND_WALL_CLOCK_MINUTES = 5
STATE_DIR = Path.home() / ".openclaw" / "state"
STATUS_PATH = STATE_DIR / "paperclip-autoresearch-status.json"
EXPERIMENT_ROOT = Path.home() / ".openclaw" / "workspace" / "deliverables" / "paperclip" / "autoresearch"
GATEWAY_ERR_LOG_PATH = Path.home() / ".openclaw" / "logs" / "gateway.err.log"
NORA_AGENT_ID = "a55324bc-32bc-4245-a078-c32fd5601db5"
COMPANY_CACHE: dict = {}
AGENT_NAME_BY_ID: dict[str, str] = {}

RESULTS_HEADER = [
    "round",
    "score",
    "status",
    "description",
    "candidate_path",
    "memo_path",
    "started_at",
    "finished_at",
]


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def isoformat(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
      return None
    try:
      return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
      return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "autoresearch"


def parse_log_timestamp(raw: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(raw)
    except ValueError:
        return None


def request(method: str, path: str, payload: dict | None = None):
    url = API_BASE.rstrip("/") + "/" + path.lstrip("/")
    headers = {}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else None


def list_company_issues() -> list[dict]:
    return request("GET", f"/companies/{COMPANY_ID}/issues?page=1&pageSize=500")


def get_company() -> dict:
    return request("GET", f"/companies/{COMPANY_ID}")


def list_company_agents() -> list[dict]:
    return request("GET", f"/companies/{COMPANY_ID}/agents")


def list_live_runs() -> list[dict]:
    return request("GET", f"/companies/{COMPANY_ID}/live-runs?minCount=100")


def create_issue(payload: dict) -> dict:
    return request("POST", f"/companies/{COMPANY_ID}/issues", payload)


def update_issue(issue_id: str, payload: dict) -> dict:
    return request("PATCH", f"/issues/{issue_id}", payload)


def add_issue_comment(issue_id: str, body: str) -> dict:
    return request("POST", f"/issues/{issue_id}/comments", {"body": body})


def wake_agent(agent_id: str, reason: str) -> dict:
    return request(
        "POST",
        f"/agents/{agent_id}/wakeup?companyId={COMPANY_ID}",
        {
            "source": "on_demand",
            "triggerDetail": "system",
            "reason": reason,
        },
    )


def cancel_run(run_id: str):
    return request("POST", f"/heartbeat-runs/{run_id}/cancel", {})


def default_experiment_dir(issue: dict) -> Path:
    label = issue.get("identifier") or issue.get("title") or issue["id"]
    return EXPERIMENT_ROOT / slugify(label)


def normalize_generation(value: dict) -> dict:
    return {
        "round": int(value.get("round", 0)),
        "issueId": value.get("issueId"),
        "issueIdentifier": value.get("issueIdentifier"),
        "status": value.get("status", "queued"),
        "candidatePath": value.get("candidatePath"),
        "memoPath": value.get("memoPath"),
        "score": value.get("score"),
        "deltaScore": value.get("deltaScore"),
        "summary": value.get("summary"),
        "mvpLabel": value.get("mvpLabel"),
        "missingContributorLabels": value.get("missingContributorLabels") or [],
        "startedAt": value.get("startedAt"),
        "finishedAt": value.get("finishedAt"),
    }


def normalize_contract(issue: dict) -> dict | None:
    contract = issue.get("experimentContract")
    if not isinstance(contract, dict) or contract.get("kind") != "autoresearch":
        return None
    experiment_dir = Path(contract.get("experimentDir") or default_experiment_dir(issue))
    plan_path = Path(contract.get("planPath") or contract.get("programPath") or experiment_dir / "program.md")
    results_path = Path(contract.get("resultsPath") or experiment_dir / "results.tsv")
    current_path = contract.get("currentPath") or contract.get("winnerPath") or contract.get("artifactPath")
    generations = [normalize_generation(item) for item in contract.get("generations", []) if isinstance(item, dict)]
    return {
        "kind": "autoresearch",
        "localStrategy": contract.get("localStrategy") if contract.get("localStrategy") in {"solo_loop", "team_round"} else "solo_loop",
        "sourceMode": contract.get("sourceMode") or "m_series_local",
        "sourceFidelity": contract.get("sourceFidelity") or "local_compatible",
        "sourceRuntime": contract.get("sourceRuntime") or "local_mps",
        "sourceRepoUrl": contract.get("sourceRepoUrl"),
        "sourceTargetPath": contract.get("sourceTargetPath") or "train.py",
        "sourceConfigured": contract.get("sourceConfigured") if contract.get("sourceConfigured") is not None else True,
        "sourceBlockedReason": contract.get("sourceBlockedReason"),
        "artifactLabel": contract.get("artifactLabel") or issue.get("title") or "Autoresearch artifact",
        "artifactPath": contract.get("artifactPath"),
        "baselinePath": contract.get("baselinePath"),
        "winnerPath": contract.get("winnerPath"),
        "reviewMemoPath": contract.get("reviewMemoPath"),
        "planPath": str(plan_path),
        "programPath": str(plan_path),
        "resultsPath": str(results_path),
        "experimentDir": str(experiment_dir),
        "planValidatedAt": contract.get("planValidatedAt"),
        "planSha256": contract.get("planSha256"),
        "planValidationErrors": contract.get("planValidationErrors") or [],
        "planReanchorOnCompaction": True if contract.get("planReanchorOnCompaction") is None else bool(contract.get("planReanchorOnCompaction")),
        "scoreRubricPath": contract.get("scoreRubricPath") or "docs/SCORING_RUBRIC.md",
        "resultSchemaVersion": contract.get("resultSchemaVersion") or "v1",
        "resultSchemaPath": contract.get("resultSchemaPath") or "docs/RESULT_SCHEMA.md",
        "metricLabel": contract.get("metricLabel") or "score",
        "budgetCents": contract.get("budgetCents"),
        "budgetRounds": contract.get("budgetRounds"),
        "budgetMinutes": contract.get("budgetMinutes"),
        "roundWallClockMinutes": contract.get("roundWallClockMinutes"),
        "intervalMinutes": contract.get("intervalMinutes") or DEFAULT_INTERVAL_MINUTES,
        "stopAfterNoImprovement": contract.get("stopAfterNoImprovement"),
        "scorerAgentIds": contract.get("scorerAgentIds") or [],
        "roundCaptainAgentId": contract.get("roundCaptainAgentId"),
        "contributorAgentIds": contract.get("contributorAgentIds") or [],
        "scoreMethod": contract.get("scoreMethod") or "weighted_rubric",
        "keepRule": contract.get("keepRule") or "higher_score_wins",
        "status": contract.get("status") or "draft",
        "roundsCompleted": int(contract.get("roundsCompleted") or 0),
        "bestScore": contract.get("bestScore"),
        "lastScore": contract.get("lastScore"),
        "currentPath": current_path,
        "currentScore": contract.get("currentScore", contract.get("bestScore")),
        "noImprovementStreak": int(contract.get("noImprovementStreak") or 0),
        "loopStartedAt": contract.get("loopStartedAt"),
        "lastRestartedAt": contract.get("lastRestartedAt"),
        "lastRestartReason": contract.get("lastRestartReason"),
        "lastRoundStartedAt": contract.get("lastRoundStartedAt"),
        "lastRoundFinishedAt": contract.get("lastRoundFinishedAt"),
        "nextRoundAt": contract.get("nextRoundAt"),
        "activeRoundIssueId": contract.get("activeRoundIssueId"),
        "activeRoundIssueIdentifier": contract.get("activeRoundIssueIdentifier"),
        "activeRoundNumber": contract.get("activeRoundNumber"),
        "activeRoundDeadlineAt": contract.get("activeRoundDeadlineAt"),
        "activeRoundContributorIssueIds": contract.get("activeRoundContributorIssueIds") or [],
        "activeRoundContributorIssueIdentifiers": contract.get("activeRoundContributorIssueIdentifiers") or [],
        "generations": generations,
        "stopReason": contract.get("stopReason"),
        "lastStoppedAt": contract.get("lastStoppedAt"),
        "lastStopReason": contract.get("lastStopReason"),
    }


def ensure_results_file(path: Path):
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(RESULTS_HEADER)


def default_program(issue: dict, contract: dict) -> str:
    current_path = contract.get("currentPath") or contract.get("artifactPath") or contract.get("baselinePath") or "(set by round issue)"
    if contract.get("localStrategy") == "team_round":
        return f"""# autoresearch

This is a Paperclip team-round implementation of the karpathy/autoresearch loop.

## Setup

Parent issue: {issue.get("identifier") or issue["id"]} — {issue.get("title")}
Mutable artifact label: {contract["artifactLabel"]}
Current champion: {current_path}
Implementation plan: {contract["planPath"]}
Results log: {contract["resultsPath"]}
Scoring rubric: {contract.get("scoreRubricPath") or "docs/SCORING_RUBRIC.md"}
Result schema: {contract.get("resultSchemaPath") or "docs/RESULT_SCHEMA.md"}

## Team-round semantics

Each generation is one shared round with a hard wall-clock deadline.

- One round captain assembles the final candidate
- Contributor agents leave short role-specific notes
- Only one candidate survives the round
- The round still produces exactly one `results.tsv` row

## Constraints

- Do not branch into extra tasks
- Keep contributor notes short and decision-useful
- Prefer one clean improvement over five conflicting drafts
- The captain uses whatever notes arrive before the wall-clock deadline
- If context compaction happens, re-read this plan before continuing
"""
    return f"""# autoresearch

This is a Paperclip implementation of the karpathy/autoresearch loop.

## Setup

Parent issue: {issue.get("identifier") or issue["id"]} — {issue.get("title")}
Mutable artifact label: {contract["artifactLabel"]}
Current champion: {current_path}
Implementation plan: {contract["planPath"]}
Results log: {contract["resultsPath"]}
Scoring rubric: {contract.get("scoreRubricPath") or "docs/SCORING_RUBRIC.md"}
Result schema: {contract.get("resultSchemaPath") or "docs/RESULT_SCHEMA.md"}

## Experimentation

The parent issue owns the loop. Each child round issue is exactly one generation.

For each round:
1. Read the current champion and prior results.
2. Create exactly one new candidate file at the path given in the child issue.
3. Score the candidate with the rubric implied by the parent issue and this artifact.
4. Decide `keep`, `discard`, or `failed`.
5. Append exactly one row to `results.tsv`.
6. Mark the child round issue done.

## Constraints

- Only improve one artifact family at a time.
- Keep changes sharp and reviewable.
- Prefer a small real improvement over a flashy rewrite.
- Do not create extra tasks or branch the strategy.

## Results format

Append one tab-separated row to `results.tsv` with columns:

round\tscore\tstatus\tdescription\tcandidate_path\tmemo_path\tstarted_at\tfinished_at

- `score`: numeric, higher is better
- `status`: `keep`, `discard`, or `failed`
- `description`: one short sentence about the mutation
- `candidate_path`: absolute path to the candidate file for this round
- `memo_path`: absolute path to the short memo for this round

## Loop semantics

The runner will schedule new child round issues every few minutes while the parent loop is active.
You do not need to continue forever inside a single run; just complete one generation cleanly.

## Compaction rule

If context compaction happens, re-read this implementation plan and assess the current state before continuing.
"""


def ensure_program_file(issue: dict, contract: dict):
    path = Path(contract["programPath"])
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_program(issue, contract))


def ensure_experiment_files(issue: dict, contract: dict) -> tuple[dict, bool]:
    changed = False
    experiment_dir = Path(contract["experimentDir"])
    experiment_dir.mkdir(parents=True, exist_ok=True)
    ensure_program_file(issue, contract)
    ensure_results_file(Path(contract["resultsPath"]))
    validation = validate_plan_file(contract["planPath"])
    if contract.get("planValidatedAt") != validation.validated_at:
        contract["planValidatedAt"] = validation.validated_at
        changed = True
    if contract.get("planSha256") != validation.sha256:
        contract["planSha256"] = validation.sha256
        changed = True
    if contract.get("planValidationErrors") != validation.errors:
        contract["planValidationErrors"] = validation.errors
        changed = True
    if contract.get("planValidatedAt") is None and validation.validated_at is not None:
        contract["planValidatedAt"] = validation.validated_at
        changed = True

    if contract.get("currentPath") is None:
        current_path = contract.get("winnerPath") or contract.get("artifactPath") or contract.get("baselinePath")
        if current_path is not None:
            contract["currentPath"] = current_path
            changed = True
    if contract.get("localStrategy") == "team_round" and contract.get("roundWallClockMinutes") is None:
        contract["roundWallClockMinutes"] = DEFAULT_TEAM_ROUND_WALL_CLOCK_MINUTES
        changed = True
    if contract.get("localStrategy") == "team_round" and not contract.get("roundCaptainAgentId"):
        contract["roundCaptainAgentId"] = issue.get("assigneeAgentId")
        changed = True
    if contract.get("status") == "draft":
        contract["status"] = "running"
        changed = True
    if not contract.get("loopStartedAt"):
        contract["loopStartedAt"] = isoformat(now_utc())
        changed = True
    if contract.get("status") == "running" and not contract.get("lastRestartedAt"):
        contract["lastRestartedAt"] = contract["loopStartedAt"]
        contract["lastRestartReason"] = "initial start"
        changed = True
    return contract, changed


def parse_results(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}
    rows: dict[int, dict] = {}
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            try:
                round_number = int(row.get("round") or 0)
            except ValueError:
                continue
            if round_number <= 0:
                continue
            # Accept both the current canonical schema and older rubric-style
            # rows written by earlier captain prompts.
            if row.get("score") in (None, "") and row.get("weighted_score") not in (None, ""):
                row["score"] = row.get("weighted_score")
            if row.get("description") in (None, "") and row.get("notes") not in (None, ""):
                row["description"] = row.get("notes")
            if row.get("status") in (None, ""):
                notes = (row.get("notes") or "").strip().lower()
                if "failed" in notes:
                    row["status"] = "failed"
                elif "discard" in notes:
                    row["status"] = "discard"
                elif "keep" in notes:
                    row["status"] = "keep"
            rows[round_number] = row
    return rows


def child_issues_for(parent_issue_id: str, issues: list[dict]) -> list[dict]:
    rows = [issue for issue in issues if issue.get("parentId") == parent_issue_id]
    rows.sort(key=lambda issue: issue.get("createdAt") or "")
    return rows


def candidate_path_for_round(contract: dict, round_number: int) -> Path:
    return Path(contract["experimentDir"]) / f"round-{round_number:03d}-candidate.md"


def memo_path_for_round(contract: dict, round_number: int) -> Path:
    return Path(contract["experimentDir"]) / f"round-{round_number:03d}-memo.md"


def result_path_for_round(contract: dict, round_number: int) -> Path:
    return Path(contract["experimentDir"]) / f"round-{round_number:03d}-result.json"


def agent_label(agent_id: str | None) -> str:
    if not agent_id:
        return "agent"
    return slugify(AGENT_NAME_BY_ID.get(agent_id, agent_id[:8]))


def contributor_note_path(contract: dict, round_number: int, agent_id: str) -> Path:
    return Path(contract["experimentDir"]) / f"round-{round_number:03d}-{agent_label(agent_id)}-note.md"


def recent_rate_limit_matches(provider_markers: tuple[str, ...], *, hours: int = 6) -> list[dt.datetime]:
    cutoff = dt.datetime.now(LOCAL_TZ) - dt.timedelta(hours=hours)
    matches: list[dt.datetime] = []
    if not GATEWAY_ERR_LOG_PATH.exists():
        return matches
    try:
        lines = GATEWAY_ERR_LOG_PATH.read_text(errors="ignore").splitlines()[-4000:]
    except OSError:
        return matches
    for line in lines:
        lowered = line.lower()
        if not any(marker in lowered for marker in provider_markers):
            continue
        if "rate limit" not in lowered and "reason=rate_limit" not in lowered:
            continue
        ts = parse_log_timestamp(line.split(" ", 1)[0])
        if not ts:
            continue
        ts_local = ts.astimezone(LOCAL_TZ)
        if ts_local >= cutoff:
            matches.append(ts_local)
    matches.sort()
    return matches


def nora_on_provider_cooldown() -> bool:
    now_local = dt.datetime.now(LOCAL_TZ)
    google_matches = recent_rate_limit_matches(("provider=google", "google/gemini-3.1-pro-preview"))
    kimi_matches = recent_rate_limit_matches(("provider=kimi-coding", "kimi-coding/k2p5"))
    if not google_matches or not kimi_matches:
        return False
    last_google = google_matches[-1]
    last_kimi = kimi_matches[-1]
    return (
        (now_local - last_google).total_seconds() <= 45 * 60
        and (now_local - last_kimi).total_seconds() <= 45 * 60
    )


def cancel_issue_and_runs(issue: dict | None, live_runs_by_issue: dict[str, list[dict]], status: str = "cancelled"):
    if not issue:
        return
    issue_id = issue.get("id")
    if not issue_id:
        return
    for run in live_runs_by_issue.get(issue_id, []):
        try:
            cancel_run(run["id"])
        except urllib.error.HTTPError:
            pass
    if not terminal_status(issue):
        update_issue(issue_id, {"status": status})


def update_generation(generations: list[dict], round_number: int, patch: dict) -> list[dict]:
    updated = False
    next_generations = []
    for generation in generations:
        if generation["round"] == round_number:
            next_generations.append({**generation, **patch})
            updated = True
        else:
            next_generations.append(generation)
    if not updated:
        next_generations.append({"round": round_number, **patch})
    next_generations.sort(key=lambda item: item["round"])
    return next_generations


def terminal_status(issue: dict | None) -> bool:
    return issue is not None and issue.get("status") in {"done", "cancelled"}


def parse_score(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def local_mode_enabled(company: dict) -> bool:
    value = company.get("autoresearchEnableMSeriesLocal")
    return True if value is None else bool(value)


def pause_local_contract(
    contract: dict,
    children_by_id: dict[str, dict],
    live_runs_by_issue: dict[str, list[dict]],
    reason: str,
) -> tuple[dict, bool]:
    changed = False
    round_issue_id = contract.get("activeRoundIssueId")
    round_number = contract.get("activeRoundNumber")
    finished_at = isoformat(now_utc())

    if round_issue_id:
        round_issue = children_by_id.get(round_issue_id)
        cancel_issue_and_runs(round_issue, live_runs_by_issue)
        if round_number is not None:
            contract["generations"] = update_generation(
                contract["generations"],
                int(round_number),
                {
                    "issueId": round_issue_id,
                    "issueIdentifier": round_issue.get("identifier") if round_issue else None,
                    "status": "failed",
                    "candidatePath": str(candidate_path_for_round(contract, int(round_number))),
                    "memoPath": str(memo_path_for_round(contract, int(round_number))),
                    "score": None,
                    "deltaScore": None,
                    "summary": reason,
                    "startedAt": contract.get("lastRoundStartedAt"),
                    "finishedAt": finished_at,
                },
            )
            contract["lastRoundFinishedAt"] = finished_at
            contract["noImprovementStreak"] = int(contract.get("noImprovementStreak") or 0) + 1
        contract["activeRoundIssueId"] = None
        contract["activeRoundIssueIdentifier"] = None
        contract["activeRoundNumber"] = None
        contract["activeRoundDeadlineAt"] = None
        contract["nextRoundAt"] = None
        changed = True
    contributor_ids = contract.get("activeRoundContributorIssueIds") or []
    if contributor_ids:
        for contributor_issue_id in contributor_ids:
            cancel_issue_and_runs(children_by_id.get(contributor_issue_id), live_runs_by_issue)
        contract["activeRoundContributorIssueIds"] = []
        contract["activeRoundContributorIssueIdentifiers"] = []
        changed = True

    if contract.get("status") != "paused":
        contract["status"] = "paused"
        changed = True
    if contract.get("stopReason") != reason:
        contract["stopReason"] = reason
        changed = True
    stopped_at = isoformat(now_utc())
    if contract.get("lastStoppedAt") != stopped_at:
        contract["lastStoppedAt"] = stopped_at
        changed = True
    if contract.get("lastStopReason") != reason:
        contract["lastStopReason"] = reason
        changed = True

    return contract, changed


def finalize_active_round(
    parent_issue: dict,
    contract: dict,
    children_by_id: dict[str, dict],
    results_rows: dict[int, dict],
    live_runs_by_issue: dict[str, list[dict]],
) -> tuple[dict, bool]:
    round_issue_id = contract.get("activeRoundIssueId")
    round_number = contract.get("activeRoundNumber")
    if not round_issue_id or round_number is None:
        return contract, False

    round_issue = children_by_id.get(round_issue_id)
    row = results_rows.get(int(round_number))
    live_runs = live_runs_by_issue.get(round_issue_id, [])
    if round_issue and not terminal_status(round_issue) and row is None:
        contract["generations"] = update_generation(
            contract["generations"],
            round_number,
            {
                "issueId": round_issue_id,
                "issueIdentifier": round_issue.get("identifier"),
                "status": "running",
                "startedAt": contract.get("lastRoundStartedAt"),
                "candidatePath": str(candidate_path_for_round(contract, round_number)),
                "memoPath": str(memo_path_for_round(contract, round_number)),
                "score": None,
                "deltaScore": None,
                "summary": None,
                "finishedAt": None,
            },
        )
        return contract, True

    finished_at = isoformat(now_utc())
    for contributor_issue_id in contract.get("activeRoundContributorIssueIds") or []:
        cancel_issue_and_runs(children_by_id.get(contributor_issue_id), live_runs_by_issue)
    cancel_issue_and_runs(round_issue, live_runs_by_issue, status="done")
    if row is None:
      contract["generations"] = update_generation(
          contract["generations"],
          int(round_number),
          {
              "issueId": round_issue_id,
              "issueIdentifier": round_issue.get("identifier") if round_issue else None,
              "status": "failed",
              "candidatePath": str(candidate_path_for_round(contract, int(round_number))),
              "memoPath": str(memo_path_for_round(contract, int(round_number))),
              "score": None,
              "deltaScore": None,
                "summary": "Round completed without a results.tsv row.",
                "mvpLabel": None,
                "missingContributorLabels": [],
                "startedAt": contract.get("lastRoundStartedAt"),
                "finishedAt": finished_at,
            },
      )
      contract["noImprovementStreak"] = int(contract.get("noImprovementStreak") or 0) + 1
      contract["lastRoundFinishedAt"] = finished_at
      contract["activeRoundIssueId"] = None
      contract["activeRoundIssueIdentifier"] = None
      contract["activeRoundNumber"] = None
      contract["activeRoundDeadlineAt"] = None
      contract["activeRoundContributorIssueIds"] = []
      contract["activeRoundContributorIssueIdentifiers"] = []
      return contract, True

    score = parse_score(row.get("score"))
    raw_status = (row.get("status") or "").strip().lower()
    generation_status = {
        "keep": "kept",
        "discard": "discarded",
        "failed": "failed",
        "crash": "failed",
    }.get(raw_status, "discarded")
    started_at = row.get("started_at") or contract.get("lastRoundStartedAt")
    finished_at = row.get("finished_at") or finished_at
    current_score = contract.get("currentScore")
    delta_score = None
    if score is not None and isinstance(current_score, (int, float)):
        delta_score = round(score - float(current_score), 4)

    captain_agent_id = contract.get("roundCaptainAgentId") or parent_issue.get("assigneeAgentId")
    captain_name = AGENT_NAME_BY_ID.get(captain_agent_id, "Captain") if captain_agent_id else "Captain"
    mvp_label = AGENT_NAME_BY_ID.get(parent_issue.get("assigneeAgentId"), captain_name) if contract.get("localStrategy") != "team_round" else captain_name
    missing_contributor_labels: list[str] = []

    if contract.get("localStrategy") == "team_round":
        contributor_agent_ids = [
            agent_id
            for agent_id in (contract.get("contributorAgentIds") or [])
            if isinstance(agent_id, str) and agent_id != captain_agent_id
        ]
        contributor_issue_ids = contract.get("activeRoundContributorIssueIds") or []
        contributed_labels: list[str] = []
        for idx, contributor_agent_id in enumerate(contributor_agent_ids):
            contributor_name = AGENT_NAME_BY_ID.get(contributor_agent_id, contributor_agent_id[:8])
            note_path = contributor_note_path(contract, int(round_number), contributor_agent_id)
            contributor_issue_id = contributor_issue_ids[idx] if idx < len(contributor_issue_ids) else None
            contributor_issue = children_by_id.get(contributor_issue_id) if contributor_issue_id else None
            if note_path.exists():
                contributed_labels.append(contributor_name)
                continue
            issue_status = contributor_issue.get("status") if contributor_issue else None
            issue_description = (contributor_issue.get("description") or "").lower() if contributor_issue else ""
            if issue_status == "blocked" and "provider cooldown: rate-limited" in issue_description:
                missing_contributor_labels.append(f"{contributor_name} (rate-limited)")
                continue
            if issue_status in {"cancelled", "done", "in_progress", "todo", "backlog", "blocked"} or contributor_issue is not None:
                missing_contributor_labels.append(contributor_name)
        if len(contributed_labels) > 1:
            mvp_label = "Team"
        elif len(contributed_labels) == 1:
            mvp_label = contributed_labels[0]
        else:
            mvp_label = captain_name

    contract["generations"] = update_generation(
        contract["generations"],
        int(round_number),
        {
            "issueId": round_issue_id,
            "issueIdentifier": round_issue.get("identifier") if round_issue else None,
            "status": generation_status,
            "candidatePath": row.get("candidate_path") or str(candidate_path_for_round(contract, int(round_number))),
            "memoPath": row.get("memo_path") or str(memo_path_for_round(contract, int(round_number))),
            "score": score,
            "deltaScore": delta_score,
            "summary": row.get("description"),
            "mvpLabel": mvp_label,
            "missingContributorLabels": missing_contributor_labels,
            "startedAt": started_at,
            "finishedAt": finished_at,
        },
    )
    contract["roundsCompleted"] = max(int(contract.get("roundsCompleted") or 0), int(round_number))
    contract["lastScore"] = score
    contract["lastRoundFinishedAt"] = finished_at
    contract["reviewMemoPath"] = row.get("memo_path") or contract.get("reviewMemoPath")
    contract["activeRoundIssueId"] = None
    contract["activeRoundIssueIdentifier"] = None
    contract["activeRoundNumber"] = None
    contract["activeRoundDeadlineAt"] = None
    contract["activeRoundContributorIssueIds"] = []
    contract["activeRoundContributorIssueIdentifiers"] = []

    if generation_status == "kept":
        contract["currentScore"] = score
        contract["currentPath"] = row.get("candidate_path") or contract.get("currentPath")
        contract["winnerPath"] = row.get("candidate_path") or contract.get("winnerPath")
        contract["bestScore"] = score if contract.get("bestScore") is None else max(float(contract["bestScore"]), float(score or 0))
        contract["noImprovementStreak"] = 0
    else:
        contract["noImprovementStreak"] = int(contract.get("noImprovementStreak") or 0) + 1

    return contract, True


def maybe_trigger_team_round_deadline(
    parent_issue: dict,
    contract: dict,
    children_by_id: dict[str, dict],
    live_runs_by_issue: dict[str, list[dict]],
) -> tuple[dict, bool]:
    if contract.get("localStrategy") != "team_round":
        return contract, False
    deadline_at = parse_iso(contract.get("activeRoundDeadlineAt"))
    captain_issue_id = contract.get("activeRoundIssueId")
    if not captain_issue_id or deadline_at is None or now_utc() < deadline_at:
        return contract, False

    changed = False
    for contributor_issue_id in contract.get("activeRoundContributorIssueIds") or []:
        issue = children_by_id.get(contributor_issue_id)
        if issue and not terminal_status(issue):
            cancel_issue_and_runs(issue, live_runs_by_issue)
            changed = True

    captain_issue = children_by_id.get(captain_issue_id)
    if captain_issue and not terminal_status(captain_issue):
        captain_agent_id = contract.get("roundCaptainAgentId") or parent_issue.get("assigneeAgentId")
        if captain_agent_id:
            wake_agent(captain_agent_id, f"Team round deadline reached for {parent_issue.get('identifier')}; finalize with current notes.")
            changed = True

    return contract, changed


def maybe_finish_contract(contract: dict) -> tuple[dict, bool]:
    changed = False
    if contract.get("status") not in {"running", "paused", "draft"}:
        return contract, changed

    def mark_stopped(reason: str):
        contract["lastStoppedAt"] = isoformat(now_utc())
        contract["lastStopReason"] = reason

    rounds_completed = int(contract.get("roundsCompleted") or 0)
    budget_rounds = contract.get("budgetRounds")
    if isinstance(budget_rounds, int) and budget_rounds > 0 and rounds_completed >= budget_rounds:
        contract["status"] = "completed"
        contract["stopReason"] = f"round budget reached ({budget_rounds})"
        mark_stopped(contract["stopReason"])
        changed = True

    if contract.get("status") == "running":
        stop_after_no_improvement = contract.get("stopAfterNoImprovement")
        if (
            isinstance(stop_after_no_improvement, int)
            and stop_after_no_improvement > 0
            and int(contract.get("noImprovementStreak") or 0) >= stop_after_no_improvement
        ):
            contract["status"] = "completed"
            contract["stopReason"] = f"no-improvement streak reached {stop_after_no_improvement}"
            mark_stopped(contract["stopReason"])
            changed = True

    if contract.get("status") == "running":
        budget_minutes = contract.get("budgetMinutes")
        loop_started_at = parse_iso(contract.get("loopStartedAt"))
        if isinstance(budget_minutes, int) and budget_minutes > 0 and loop_started_at is not None:
            elapsed = now_utc() - loop_started_at
            if elapsed.total_seconds() >= budget_minutes * 60:
                contract["status"] = "exhausted"
                contract["stopReason"] = f"time budget reached ({budget_minutes} minutes)"
                mark_stopped(contract["stopReason"])
                changed = True

    return contract, changed


def contributor_role_text(agent_id: str) -> str:
    name = AGENT_NAME_BY_ID.get(agent_id, "")
    if name == "Asher":
        return "Generate one commercial mutation that sharpens the hook without overclaiming."
    if name == "Nora":
        return "Leave one operational truth/risk note so the candidate stays grounded."
    if name == "Charlotte":
        return "Leave one trust/taste note so the candidate stays premium and non-creepy."
    if name == "Quinn":
        return "Leave one implementation-fit note so the candidate matches what can actually be packaged or built."
    if name == "Felix":
        return "Act as the synthesizer and final decision-maker for the round."
    return "Leave one short note from your role that helps the captain decide keep or discard."


def spawn_round(parent_issue: dict, contract: dict) -> tuple[dict, dict, list[dict]]:
    round_number = int(contract.get("roundsCompleted") or 0) + 1
    candidate_path = candidate_path_for_round(contract, round_number)
    memo_path = memo_path_for_round(contract, round_number)
    result_path = result_path_for_round(contract, round_number)
    current_champion = contract.get("currentPath") or contract.get("winnerPath") or contract.get("artifactPath") or contract.get("baselinePath")
    contributor_issues: list[dict] = []
    started_at_dt = now_utc()
    started_at = isoformat(started_at_dt)
    deadline_minutes = int(contract.get("roundWallClockMinutes") or DEFAULT_TEAM_ROUND_WALL_CLOCK_MINUTES)
    deadline_at = isoformat(started_at_dt + dt.timedelta(minutes=deadline_minutes))
    previous_status = contract.get("status")
    last_stopped_at = parse_iso(contract.get("lastStoppedAt"))
    last_restarted_at = parse_iso(contract.get("lastRestartedAt"))
    resumed_from_stop = (
        last_stopped_at is not None
        and (last_restarted_at is None or last_restarted_at <= last_stopped_at)
    )

    if contract.get("localStrategy") == "team_round":
        captain_agent_id = contract.get("roundCaptainAgentId") or parent_issue.get("assigneeAgentId")
        contributor_agent_ids = [
            agent_id for agent_id in (contract.get("contributorAgentIds") or [])
            if isinstance(agent_id, str) and agent_id != captain_agent_id
        ]
        contributor_lines = []
        contributor_issue_ids: list[str] = []
        contributor_issue_identifiers: list[str] = []
        for contributor_agent_id in contributor_agent_ids:
            note_path = contributor_note_path(contract, round_number, contributor_agent_id)
            contributor_name = AGENT_NAME_BY_ID.get(contributor_agent_id, contributor_agent_id[:8])
            if contributor_agent_id == NORA_AGENT_ID and nora_on_provider_cooldown():
                contributor_issue = create_issue(
                    {
                        "projectId": parent_issue.get("projectId"),
                        "parentId": parent_issue["id"],
                        "title": f"Round {round_number} / {contributor_name}: unavailable this round",
                    "description": (
                        "Provider cooldown: rate-limited.\n\n"
                        f"{contributor_name}'s primary and fallback models are both rate-limited right now, "
                        "so this contributor slot is unavailable for this round.\n"
                        f"If the lane recovers later, the next round can include `{note_path}` again.\n"
                        "Do not wake this contributor for the current round."
                        ),
                        "status": "blocked",
                        "priority": parent_issue.get("priority") or "high",
                        "assigneeAgentId": None,
                    }
                )
                contributor_issues.append(contributor_issue)
                contributor_issue_ids.append(contributor_issue["id"])
                contributor_issue_identifiers.append(contributor_issue.get("identifier"))
                contributor_lines.append(f"- {contributor_name}: unavailable this round due provider cooldown; captain should proceed without this note.")
                continue
            contributor_issue = create_issue(
                {
                    "projectId": parent_issue.get("projectId"),
                    "parentId": parent_issue["id"],
                    "title": f"Round {round_number} / {contributor_name}: contribute to {parent_issue['title']}",
                    "description": contributor_prompt(
                        parent_identifier=parent_issue.get("identifier") or parent_issue["id"],
                        plan_path=contract["planPath"],
                        current_champion=current_champion,
                        note_path=str(note_path),
                        deadline_at=deadline_at,
                        role_instruction=contributor_role_text(contributor_agent_id),
                    ),
                    "status": "todo",
                    "priority": parent_issue.get("priority") or "high",
                    "assigneeAgentId": contributor_agent_id,
                }
            )
            contributor_issues.append(contributor_issue)
            contributor_issue_ids.append(contributor_issue["id"])
            contributor_issue_identifiers.append(contributor_issue.get("identifier"))
            contributor_lines.append(f"- {contributor_name}: `{note_path}` ({contributor_issue.get('identifier')})")

        description = captain_prompt(
            parent_identifier=parent_issue.get("identifier") or parent_issue["id"],
            plan_path=contract["planPath"],
            plan_sha256=contract.get("planSha256"),
            current_champion=current_champion,
            candidate_path=str(candidate_path),
            memo_path=str(memo_path),
            result_path=str(result_path),
            result_schema_path=contract.get("resultSchemaPath") or "docs/RESULT_SCHEMA.md",
            results_tsv_path=contract["resultsPath"],
            deadline_at=deadline_at,
            deadline_minutes=deadline_minutes,
            contributor_lines=contributor_lines,
        )
    else:
        captain_agent_id = parent_issue.get("assigneeAgentId")
        contributor_issue_ids = []
        contributor_issue_identifiers = []
        description = solo_round_prompt(
            parent_identifier=parent_issue.get("identifier") or parent_issue["id"],
            plan_path=contract["planPath"],
            plan_sha256=contract.get("planSha256"),
            current_champion=current_champion,
            candidate_path=str(candidate_path),
            memo_path=str(memo_path),
            result_path=str(result_path),
            result_schema_path=contract.get("resultSchemaPath") or "docs/RESULT_SCHEMA.md",
            results_tsv_path=contract["resultsPath"],
        )
    child_issue = create_issue(
        {
            "projectId": parent_issue.get("projectId"),
            "parentId": parent_issue["id"],
            "title": f"Round {round_number}: {parent_issue['title']}",
            "description": description,
            "status": "todo",
            "priority": parent_issue.get("priority") or "high",
            "assigneeAgentId": captain_agent_id,
        }
    )
    contract["status"] = "running"
    if previous_status != "running" or resumed_from_stop:
        contract["lastRestartedAt"] = started_at
        contract["lastRestartReason"] = (
            "initial start"
            if int(contract.get("roundsCompleted") or 0) == 0 and not contract.get("lastStoppedAt")
            else "loop resumed"
        )
        contract["stopReason"] = None
    contract["activeRoundIssueId"] = child_issue["id"]
    contract["activeRoundIssueIdentifier"] = child_issue.get("identifier")
    contract["activeRoundNumber"] = round_number
    contract["activeRoundDeadlineAt"] = deadline_at if contract.get("localStrategy") == "team_round" else None
    contract["activeRoundContributorIssueIds"] = contributor_issue_ids
    contract["activeRoundContributorIssueIdentifiers"] = contributor_issue_identifiers
    contract["lastRoundStartedAt"] = started_at
    contract["nextRoundAt"] = None
    if not contract.get("loopStartedAt"):
        contract["loopStartedAt"] = started_at
    contract["generations"] = update_generation(
        contract["generations"],
        round_number,
        {
            "issueId": child_issue["id"],
            "issueIdentifier": child_issue.get("identifier"),
            "status": "queued",
            "candidatePath": str(candidate_path),
            "memoPath": str(memo_path),
            "score": None,
            "deltaScore": None,
            "summary": None,
            "startedAt": started_at,
            "finishedAt": None,
        },
    )
    return contract, child_issue, contributor_issues


def patch_parent_issue(parent_issue: dict, contract: dict):
    next_status = parent_issue.get("status")
    if contract["status"] in {"completed", "exhausted", "failed"} and parent_issue.get("status") != "done":
        next_status = "done"
    elif (
        contract["status"] in {"draft", "running", "paused"}
        and parent_issue.get("status") != "in_progress"
        and parent_issue.get("assigneeAgentId")
    ):
        next_status = "in_progress"
    payload = {"experimentContract": contract}
    if next_status is not None and next_status != parent_issue.get("status"):
        payload["status"] = next_status
    update_issue(parent_issue["id"], payload)


def process_parent_issue(parent_issue: dict, all_issues: list[dict], live_runs: list[dict]) -> dict:
    summary = {
        "identifier": parent_issue.get("identifier"),
        "title": parent_issue.get("title"),
        "status": "skipped",
        "note": None,
    }
    contract = normalize_contract(parent_issue)
    if contract is None:
        return summary

    contract, changed = ensure_experiment_files(parent_issue, contract)
    children = child_issues_for(parent_issue["id"], all_issues)
    children_by_id = {issue["id"]: issue for issue in children}
    results_rows = parse_results(Path(contract["resultsPath"]))
    live_runs_by_issue: dict[str, list[dict]] = {}
    for run in live_runs:
        issue_id = run.get("issueId")
        if not issue_id:
            continue
        live_runs_by_issue.setdefault(issue_id, []).append(run)

    if contract.get("sourceMode") == "m_series_local" and not local_mode_enabled(COMPANY_CACHE):
        contract, paused = pause_local_contract(
            contract,
            children_by_id,
            live_runs_by_issue,
            "M-series Local disabled in Settings.",
        )
        if paused:
            patch_parent_issue(parent_issue, contract)
        summary["status"] = contract["status"]
        summary["note"] = contract.get("stopReason")
        return summary

    if contract.get("planValidationErrors"):
        validation = validate_plan_file(contract["planPath"])
        reason = f"Plan validation failed: {plan_validation_summary(validation)}"
        contract, paused = pause_local_contract(
            contract,
            children_by_id,
            live_runs_by_issue,
            reason,
        )
        if paused or changed:
            patch_parent_issue(parent_issue, contract)
        summary["status"] = contract["status"]
        summary["note"] = reason
        return summary

    contract, deadline_adjusted = maybe_trigger_team_round_deadline(parent_issue, contract, children_by_id, live_runs_by_issue)
    changed = changed or deadline_adjusted
    contract, finalized = finalize_active_round(parent_issue, contract, children_by_id, results_rows, live_runs_by_issue)
    changed = changed or finalized
    contract, maybe_finished = maybe_finish_contract(contract)
    changed = changed or maybe_finished
    active_round_issue_id = contract.get("activeRoundIssueId")
    if active_round_issue_id and active_round_issue_id in live_runs_by_issue:
        changed = True
    elif contract.get("status") == "running" and active_round_issue_id is None:
        contract, child_issue, contributor_issues = spawn_round(parent_issue, contract)
        changed = True
        # New assigned issues already trigger issue-scoped wakeups via Paperclip's
        # create-issue flow. Do not send an extra generic wake here or agents can
        # receive a second heartbeat with no PAPERCLIP_TASK_ID and fall back to the
        # wrong inbox item.
        summary["status"] = "spawned_round"
        summary["note"] = child_issue.get("identifier")

    if changed:
        patch_parent_issue(parent_issue, contract)
    if summary["status"] == "skipped":
        summary["status"] = contract["status"]
        summary["note"] = contract.get("stopReason")
    return summary


def write_status(payload: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, indent=2))


def main():
    global COMPANY_CACHE
    global AGENT_NAME_BY_ID
    COMPANY_CACHE = get_company()
    AGENT_NAME_BY_ID = {
        agent.get("id"): agent.get("name")
        for agent in list_company_agents()
        if isinstance(agent, dict) and isinstance(agent.get("id"), str) and isinstance(agent.get("name"), str)
    }
    issues = list_company_issues()
    live_runs = list_live_runs()
    parent_issues = [issue for issue in issues if normalize_contract(issue) is not None]
    summaries = []
    for issue in parent_issues:
        try:
            summaries.append(process_parent_issue(issue, issues, live_runs))
        except urllib.error.HTTPError as err:
            summaries.append(
                {
                    "identifier": issue.get("identifier"),
                    "title": issue.get("title"),
                    "status": "error",
                    "note": f"http {err.code}",
                }
            )
        except Exception as err:  # noqa: BLE001
            summaries.append(
                {
                    "identifier": issue.get("identifier"),
                    "title": issue.get("title"),
                    "status": "error",
                    "note": str(err),
                }
            )
    write_status(
        {
            "updatedAt": isoformat(now_utc()),
            "company": {
                "id": COMPANY_CACHE.get("id"),
                "name": COMPANY_CACHE.get("name"),
                "autoresearchEnableActualUpstreamCuda": COMPANY_CACHE.get("autoresearchEnableActualUpstreamCuda"),
                "autoresearchEnableMSeriesLocal": COMPANY_CACHE.get("autoresearchEnableMSeriesLocal"),
            },
            "experimentsSeen": len(parent_issues),
            "summaries": summaries,
        }
    )


if __name__ == "__main__":
    main()
