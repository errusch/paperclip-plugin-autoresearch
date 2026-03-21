#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


def isoformat_utc(value: dt.datetime | None = None) -> str:
    value = value or dt.datetime.now(dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class PlanValidation:
    path: str
    exists: bool
    readable: bool
    sha256: str | None
    validated_at: str | None
    errors: list[str]


def validate_plan_file(plan_path: str) -> PlanValidation:
    path = Path(plan_path)
    errors: list[str] = []
    exists = path.exists()
    readable = False
    digest: str | None = None
    validated_at: str | None = None

    if not exists:
        errors.append("plan file does not exist")
    elif not path.is_file():
        errors.append("plan path is not a regular file")
    else:
        try:
            content = path.read_text(encoding="utf-8")
            readable = True
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            validated_at = isoformat_utc()
            if len(content.strip()) < 80:
                errors.append("plan file is too short to anchor a long run")
            lowered = content.lower()
            heading_count = sum(1 for line in content.splitlines() if line.lstrip().startswith("#"))
            bullet_count = sum(
                1
                for line in content.splitlines()
                if line.lstrip().startswith(("- ", "* ")) or re.match(r"^\d+[.)]\s", line.lstrip())
            )
            if heading_count == 0 and bullet_count < 3:
                errors.append("plan file needs more visible structure (headings or bullets)")
            if lowered.count("\n\n") < 2:
                errors.append("plan file needs clearer sections for goal, outputs, and stop rules")
        except OSError as err:
            errors.append(f"plan file could not be read: {err}")

    return PlanValidation(
        path=str(path),
        exists=exists,
        readable=readable,
        sha256=digest,
        validated_at=validated_at,
        errors=errors,
    )


def plan_validation_summary(validation: PlanValidation) -> str:
    if not validation.errors:
        return "plan validated"
    return "; ".join(validation.errors)


def contributor_prompt(
    *,
    parent_identifier: str,
    plan_path: str,
    current_champion: str,
    note_path: str,
    deadline_at: str,
    role_instruction: str,
) -> str:
    return (
        f"This is one contribution to a shared Autoresearch team round for parent {parent_identifier}.\n\n"
        "Execution contract:\n"
        f"1. Re-read the implementation plan at `{plan_path}` before making decisions.\n"
        f"2. Re-read the current champion at `{current_champion}`.\n"
        "3. If context compaction happens, re-read the plan again before continuing.\n"
        f"4. Leave exactly one short role-specific note at `{note_path}` before the round deadline at {deadline_at}.\n"
        "5. Do not create alternate candidates, extra tasks, or parallel branches.\n\n"
        f"Your job: {role_instruction}\n\n"
        "Required output:\n"
        "- one short note only\n"
        "- one concrete recommendation or warning\n"
        "- one sentence if you are blocked\n\n"
        "When done, mark this issue done."
    )


def captain_prompt(
    *,
    parent_identifier: str,
    plan_path: str,
    plan_sha256: str | None,
    current_champion: str,
    candidate_path: str,
    memo_path: str,
    result_path: str,
    result_schema_path: str,
    results_tsv_path: str,
    deadline_at: str,
    deadline_minutes: int,
    contributor_lines: list[str],
) -> str:
    contributor_block = "\n".join(contributor_lines) if contributor_lines else "- no contributor notes configured"
    checksum_line = f"Plan checksum: `{plan_sha256}`\n" if plan_sha256 else ""
    return (
        f"This is the captain issue for one shared Autoresearch team round for parent {parent_identifier}.\n\n"
        "Execution contract:\n"
        f"1. Re-read the implementation plan at `{plan_path}` before doing anything else.\n"
        f"{checksum_line}"
        f"2. Re-read the current champion at `{current_champion}`.\n"
        "3. If context compaction happens, re-read the plan and assess current state before continuing.\n"
        f"4. The round has a hard wall-clock deadline at {deadline_at} ({deadline_minutes} minutes).\n"
        "5. Use whatever contributor notes exist by the deadline; do not wait indefinitely.\n"
        "6. Finish the round completely.\n\n"
        "Contributor notes may arrive here:\n"
        f"{contributor_block}\n\n"
        "Required outputs:\n"
        f"- exactly one candidate at `{candidate_path}`\n"
        f"- exactly one memo at `{memo_path}`\n"
        f"- exactly one structured result JSON at `{result_path}` matching `{result_schema_path}`\n"
        f"- exactly one TSV row appended to `{results_tsv_path}`\n\n"
        "The result JSON must include:\n"
        "- summary\n"
        "- output paths\n"
        "- verification notes with blockers\n"
        "- next actions\n\n"
        "If the candidate should replace the current champion, log `keep`; otherwise log `discard`. Use `failed` if you could not produce a viable result.\n"
        "When you are done, mark this issue done."
    )


def solo_round_prompt(
    *,
    parent_identifier: str,
    plan_path: str,
    plan_sha256: str | None,
    current_champion: str,
    candidate_path: str,
    memo_path: str,
    result_path: str,
    result_schema_path: str,
    results_tsv_path: str,
) -> str:
    checksum_line = f"Plan checksum: `{plan_sha256}`\n" if plan_sha256 else ""
    return (
        f"Run one autoresearch generation for parent {parent_identifier}.\n\n"
        "Execution contract:\n"
        f"1. Re-read the implementation plan at `{plan_path}`.\n"
        f"{checksum_line}"
        f"2. Re-read the current champion at `{current_champion}`.\n"
        "3. If context compaction happens, re-read the plan and assess current state before continuing.\n"
        "4. Finish one clean generation only.\n\n"
        "Required outputs:\n"
        f"- exactly one candidate at `{candidate_path}`\n"
        f"- exactly one memo at `{memo_path}`\n"
        f"- exactly one structured result JSON at `{result_path}` matching `{result_schema_path}`\n"
        f"- exactly one TSV row appended to `{results_tsv_path}`\n\n"
        "The result JSON must include summary, outputs, verification with blockers, and next actions.\n"
        "If the candidate should replace the current champion, log `keep`; otherwise log `discard`. Use `failed` if you could not produce a viable result.\n"
        "When you are done, mark this round issue done."
    )
