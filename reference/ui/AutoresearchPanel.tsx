import { useEffect, useState } from "react";
import { Link } from "@/lib/router";
import {
  FlaskConical,
  FileCode2,
  FileText,
  GitBranch,
  GitCommitHorizontal,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Zap,
} from "lucide-react";
import type { DashboardSummary } from "@paperclipai/shared";
import { cn, formatCents } from "../lib/utils";
import { timeAgo } from "../lib/timeAgo";

/* ── Status helpers ─────────────────────────────────────────────── */

function statusTone(status: string) {
  if (status === "executing") return "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-300";
  if (status === "queued") return "bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300";
  if (status === "waiting") return "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300";
  if (status === "completed") return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300";
  if (status === "degraded") return "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300";
  if (status === "blocked") return "bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300";
  if (status === "failed") return "bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300";
  if (status === "exhausted") return "bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300";
  return "bg-muted text-muted-foreground";
}

function statusLabel(status: string) {
  if (status === "executing") return "executing";
  if (status === "queued") return "queued";
  if (status === "waiting") return "waiting";
  if (status === "degraded") return "degraded";
  if (status === "blocked") return "blocked";
  return status;
}

function sourceModeLabel(mode: "actual_upstream" | "m_series_local") {
  return mode === "actual_upstream" ? "Actual Upstream (CUDA)" : "M-series Local";
}

function sourceModeTone(mode: "actual_upstream" | "m_series_local") {
  return mode === "actual_upstream"
    ? "bg-violet-100 text-violet-700 dark:bg-violet-900/50 dark:text-violet-300"
    : "bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300";
}

function localStrategyLabel(strategy: "solo_loop" | "team_round") {
  return strategy === "team_round" ? "Team Round" : "Fallback Mode";
}

function localStrategyTone(strategy: "solo_loop" | "team_round") {
  return strategy === "team_round"
    ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
    : "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
}

function outcomeIcon(status: string) {
  if (status === "kept") return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />;
  if (status === "discarded") return <XCircle className="h-3.5 w-3.5 text-rose-400" />;
  if (status === "failed") return <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />;
  if (status === "running") return <Zap className="h-3.5 w-3.5 text-cyan-500 animate-pulse" />;
  if (status === "queued") return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
  return null;
}

function generationPillTone(status: string) {
  if (status === "kept") return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300";
  if (status === "discarded") return "bg-muted text-muted-foreground";
  if (status === "failed") return "bg-amber-500/15 text-amber-600 dark:text-amber-300";
  if (status === "running" || status === "queued") return "bg-cyan-500/15 text-cyan-600 dark:text-cyan-300";
  return "bg-muted text-muted-foreground";
}

function pathTail(value: string | null) {
  if (!value) return null;
  const parts = value.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? value;
}

function metricFmt(value: number | null) {
  return value == null ? "—" : value.toFixed(2);
}

function formatTimerMs(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatMeteringNote({
  spendCents,
  budgetCents,
  emptyLabel = "no Paperclip cost events recorded yet",
  noBudgetLabel = "no configured cap",
}: {
  spendCents: number;
  budgetCents: number | null;
  emptyLabel?: string;
  noBudgetLabel?: string;
}) {
  if (spendCents === 0) {
    return budgetCents != null
      ? `${formatCents(budgetCents)} configured cap · ${emptyLabel}`
      : emptyLabel;
  }

  return budgetCents != null
    ? `${formatCents(budgetCents)} configured cap`
    : noBudgetLabel;
}

function contractBudgetLabel(experiment: Experiment) {
  const parts: string[] = [];
  if (experiment.budgetMinutes != null) parts.push(`${experiment.budgetMinutes}m total`);
  if (experiment.budgetRounds != null) parts.push(`${experiment.budgetRounds} round cap`);
  if (parts.length === 0) return "unbounded";
  return parts.join(" · ");
}

/* ── Types ──────────────────────────────────────────────────────── */

type Experiment = DashboardSummary["autoresearch"]["experiments"][number];
type Generation = Experiment["generations"][number];

/* ── Generation row (keep/discard history) ──────────────────────── */

function GenerationRow({ gen }: { gen: Generation }) {
  return (
    <div className="px-3 py-2 text-xs">
      <div className="grid grid-cols-[3rem_5.5rem_5rem_5rem_1fr_5rem] items-center gap-2">
        <span className="font-mono text-muted-foreground">#{gen.round}</span>
        <span className="flex items-center gap-1.5">
          {outcomeIcon(gen.status)}
          <span className={cn(
            gen.status === "kept" && "font-medium text-emerald-600 dark:text-emerald-400",
            gen.status === "discarded" && "text-muted-foreground",
          )}>
            {gen.status}
          </span>
        </span>
        <span className="tabular-nums">
          {gen.score != null ? gen.score.toFixed(2) : "—"}
          {gen.deltaScore != null && (
            <span className={cn(
              "ml-1",
              gen.deltaScore > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-500",
            )}>
              {gen.deltaScore >= 0 ? "+" : ""}{gen.deltaScore.toFixed(2)}
            </span>
          )}
        </span>
        <span className="truncate text-muted-foreground" title={gen.mvpLabel ?? undefined}>
          {gen.mvpLabel ?? "—"}
        </span>
        <span className="truncate text-muted-foreground" title={gen.candidatePath ?? undefined}>
          {pathTail(gen.candidatePath) ?? "—"}
        </span>
        <span className="text-muted-foreground text-right">
          {gen.finishedAt ? timeAgo(gen.finishedAt) : "—"}
        </span>
      </div>
      {gen.missingContributorLabels.length > 0 && (
        <div className="mt-1 text-[11px] text-amber-600 dark:text-amber-300">
          Missing: {gen.missingContributorLabels.join(", ")}
        </div>
      )}
    </div>
  );
}

/* ── Single experiment lane ─────────────────────────────────────── */

function ExperimentLane({ experiment }: { experiment: Experiment }) {
  const [expanded, setExpanded] = useState(true);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const recentGens = experiment.generations.slice(-8);
  const keptCount = experiment.generations.filter((g) => g.status === "kept").length;
  const discardedCount = experiment.generations.filter((g) => g.status === "discarded").length;

  useEffect(() => {
    if (!["executing", "queued", "waiting"].includes(experiment.displayStatus)) return;
    const timerId = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(timerId);
  }, [experiment.displayStatus]);

  const activeDeadlineMs = experiment.activeRoundDeadlineAt
    ? new Date(experiment.activeRoundDeadlineAt).getTime()
    : null;
  const activeStartedMs = experiment.lastRoundStartedAt
    ? new Date(experiment.lastRoundStartedAt).getTime()
    : null;
  const countdownMs = activeDeadlineMs != null ? activeDeadlineMs - nowMs : null;
  const elapsedMs = activeStartedMs != null ? nowMs - activeStartedMs : null;
  const hasCountdown = ["executing", "queued", "waiting"].includes(experiment.displayStatus) && countdownMs != null;
  const isOverdue = hasCountdown && countdownMs! < 0;
  const timerLabel = hasCountdown
    ? isOverdue
      ? `${formatTimerMs(Math.abs(countdownMs!))} overdue`
      : `${formatTimerMs(countdownMs!)} left`
    : ["executing", "queued", "waiting"].includes(experiment.displayStatus) && elapsedMs != null
      ? `${formatTimerMs(elapsedMs)} elapsed`
      : null;

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      {/* ── Lane header ─────────────────────────────────────── */}
      <div className="border-b border-border bg-card">
        <div className="p-4 sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Link
                  to={`/issues/${experiment.identifier ?? experiment.issueId}`}
                  className="text-xs font-mono text-muted-foreground hover:text-foreground no-underline"
                >
                  {experiment.identifier ?? experiment.issueId.slice(0, 8)}
                </Link>
                <span
                  className={cn(
                    "inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium",
                    localStrategyTone(experiment.localStrategy),
                  )}
                >
                  {localStrategyLabel(experiment.localStrategy)}
                </span>
                <span
                  className={cn(
                    "inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium",
                    sourceModeTone(experiment.sourceMode),
                  )}
                >
                  {sourceModeLabel(experiment.sourceMode)}
                </span>
                <span className={cn(
                  "inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium",
                  statusTone(experiment.displayStatus),
                )}>
                  {statusLabel(experiment.displayStatus)}
                </span>
                {experiment.assigneeAgentName && (
                  <span className="text-xs text-muted-foreground">
                    {experiment.assigneeAgentName}
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm font-medium leading-5">{experiment.title}</p>
              {experiment.displayReason && (
                <p className="mt-2 text-xs text-muted-foreground leading-5">
                  {experiment.displayReason}
                </p>
              )}
            </div>
            <div className="shrink-0 text-xs text-muted-foreground">
              {timeAgo(experiment.updatedAt)}
            </div>
          </div>
        </div>

      {/* ── Loop contract ─────────────────────────────────── */}
      <div className="border-t border-border/50 px-4 pt-3 sm:px-5">
        <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Loop Contract
        </div>
      </div>
      <div className="px-4 pb-3 sm:px-5 grid gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
          <div className="flex items-center gap-2">
            <FileCode2 className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
            <span className="text-muted-foreground">Mutable artifact:</span>
            <span className="font-medium truncate" title={experiment.artifactPath ?? undefined}>
              {pathTail(experiment.artifactPath) ?? experiment.artifactLabel}
            </span>
          </div>
          {experiment.programPath && (
            <div className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Program:</span>
              <span className="truncate" title={experiment.programPath}>
                {pathTail(experiment.programPath)}
              </span>
            </div>
          )}
          {experiment.resultsPath && (
            <div className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Results:</span>
              <span className="truncate" title={experiment.resultsPath}>
                {pathTail(experiment.resultsPath)}
              </span>
            </div>
          )}
          {experiment.sourceTargetPath && (
            <div className="flex items-center gap-2">
              <GitCommitHorizontal className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Target file:</span>
              <span className="truncate" title={experiment.sourceTargetPath}>
                {pathTail(experiment.sourceTargetPath)}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Zap className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
            <span className="text-muted-foreground">Rules:</span>
            <span className="truncate">
              {experiment.metricLabel ?? "score"} · higher score wins
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
            <span className="text-muted-foreground">Budget:</span>
            <span className="truncate">{contractBudgetLabel(experiment)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
            <span className="text-muted-foreground">Cadence:</span>
            <span className="truncate">
              {experiment.localStrategy === "team_round"
                ? `${experiment.roundWallClockMinutes ?? 5}m team round`
                : `every ${experiment.intervalMinutes ?? 5}m`}
            </span>
          </div>
          {experiment.currentPath && (
            <div className="flex items-center gap-2">
              <GitBranch className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">
                {experiment.sourceKind === "karpathy_autoresearch" ? "Live branch:" : "Current winner:"}
              </span>
              <span className="font-medium text-emerald-600 dark:text-emerald-400 truncate" title={experiment.currentPath}>
                {pathTail(experiment.currentPath)}
              </span>
            </div>
          )}
          {experiment.currentCommit && (
            <div className="flex items-center gap-2">
              <GitCommitHorizontal className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Commit:</span>
              <span className="font-mono truncate" title={experiment.currentCommit}>
                {experiment.currentCommit}
              </span>
            </div>
          )}
          {experiment.localStrategy === "team_round" && experiment.roundCaptainAgentName && (
            <div className="flex items-center gap-2">
              <Zap className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Round captain:</span>
              <span className="truncate" title={experiment.roundCaptainAgentName}>
                {experiment.roundCaptainAgentName}
              </span>
            </div>
          )}
          {experiment.localStrategy === "team_round" && experiment.contributorAgentNames.length > 0 && (
            <div className="flex items-center gap-2 sm:col-span-2 lg:col-span-3">
              <FileText className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
              <span className="text-muted-foreground">Contributors:</span>
              <span className="truncate" title={experiment.contributorAgentNames.join(", ")}>
                {experiment.contributorAgentNames.join(", ")}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Metric strip ────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-6 border-b border-border divide-x divide-border">
        <div className="p-3 sm:p-4">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wide">
            {experiment.metricLabel ?? "Score"}
          </div>
          <div className="mt-1 text-lg font-semibold tabular-nums">
            {metricFmt(experiment.currentScore)}
          </div>
          <div className="text-[11px] text-muted-foreground">
            Best: {metricFmt(experiment.bestScore)}
          </div>
        </div>
        <div className="p-3 sm:p-4">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wide">Rounds Completed</div>
          <div className="mt-1 text-lg font-semibold tabular-nums">
            {experiment.roundsCompleted}
            {experiment.budgetRounds != null && (
              <span className="text-sm text-muted-foreground font-normal"> / {experiment.budgetRounds}</span>
            )}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {experiment.localStrategy === "team_round"
              ? `${experiment.roundWallClockMinutes ?? 5}m wall-clock per round`
              : (experiment.budgetRounds != null ? "round cap enabled" : `every ${experiment.intervalMinutes ?? 5}m`)}
          </div>
        </div>
        <div className="p-3 sm:p-4">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wide">Keep / Discard</div>
          <div className="mt-1 text-lg font-semibold tabular-nums">
            <span className="text-emerald-600 dark:text-emerald-400">{keptCount}</span>
            <span className="text-muted-foreground mx-1">/</span>
            <span className="text-rose-500">{discardedCount}</span>
          </div>
          <div className="text-[11px] text-muted-foreground">
            streak: {experiment.noImprovementStreak} without improvement
          </div>
        </div>
        <div className="p-3 sm:p-4">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wide">Tracked Spend</div>
          <div className="mt-1 text-lg font-semibold tabular-nums">
            {formatCents(experiment.spendCents)}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {formatMeteringNote({
              spendCents: experiment.spendCents,
              budgetCents: experiment.budgetCents,
            })}
          </div>
        </div>
        {(experiment.activeRoundIssueIdentifier || experiment.liveRoundStatus || experiment.activeRoundContributorIssueIdentifiers.length > 0) && (
          <div className="p-3 sm:p-4">
            <div className="text-[11px] text-muted-foreground uppercase tracking-wide">Live Round</div>
            <div className="mt-1 text-sm font-medium flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-cyan-500 animate-pulse" />
              #{experiment.activeRoundNumber ?? "—"}
            </div>
            <div className="text-[11px] text-muted-foreground">
              {experiment.activeRoundIssueIdentifier ?? experiment.liveRoundStatus ?? "running"}
            </div>
            {experiment.activeRoundDeadlineAt && (
              <div className="mt-1">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  Round Timer
                </div>
                <div
                  className={cn(
                    "text-sm font-semibold tabular-nums",
                    isOverdue ? "text-amber-500" : "text-cyan-600 dark:text-cyan-300",
                  )}
                >
                  {timerLabel ?? "—"}
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Deadline {timeAgo(experiment.activeRoundDeadlineAt)}
                </div>
              </div>
            )}
            {!experiment.activeRoundDeadlineAt && timerLabel && (
              <div className="mt-1">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  Round Timer
                </div>
                <div className="text-sm font-semibold tabular-nums text-cyan-600 dark:text-cyan-300">
                  {timerLabel}
                </div>
              </div>
            )}
            {experiment.localStrategy === "team_round" && experiment.activeRoundContributorIssueIdentifiers.length > 0 && (
              <div className="mt-1 text-[11px] text-muted-foreground line-clamp-2">
                Contributors: {experiment.activeRoundContributorIssueIdentifiers.join(", ")}
              </div>
            )}
            {experiment.liveRoundSummary && (
              <div className="mt-1 text-[11px] text-muted-foreground line-clamp-2">
                {experiment.liveRoundSummary}
              </div>
            )}
            {experiment.displayReason && (
              <div className="mt-1 text-[11px] text-muted-foreground line-clamp-2">
                {experiment.displayReason}
              </div>
            )}
          </div>
        )}
        {(experiment.lastRoundFinishedAt || experiment.nextRoundAt) && (
          <div className="p-3 sm:p-4">
            <div className="text-[11px] text-muted-foreground uppercase tracking-wide">Timing</div>
            {experiment.lastRoundFinishedAt && (
              <div className="mt-1 text-xs text-muted-foreground">
                Last: {timeAgo(experiment.lastRoundFinishedAt)}
              </div>
            )}
            {experiment.nextRoundAt && (
              <div className="text-xs text-muted-foreground">
                Next: {timeAgo(experiment.nextRoundAt)}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-b border-border px-4 py-3 sm:px-5 space-y-3">
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Current Winner</div>
          <div className="mt-1 text-sm font-medium text-emerald-600 dark:text-emerald-400">
            {pathTail(experiment.currentPath) ?? "No winner yet"}
          </div>
          {experiment.currentPreview && (
            <p className="mt-2 text-sm text-muted-foreground leading-6">
              {experiment.currentPreview}
            </p>
          )}
        </div>
        {experiment.winnerSummary && (
          <div>
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Why It Won</div>
            <p className="mt-1 text-sm text-muted-foreground leading-6">
              {experiment.winnerSummary}
            </p>
          </div>
        )}
      </div>

      {/* ── Loop state / outputs ───────────────────────────── */}
      {(experiment.winnerPath ||
        experiment.reviewMemoPath ||
        experiment.stopReason ||
        experiment.lastStoppedAt ||
        experiment.lastRestartedAt ||
        experiment.sourceUnavailableReason) && (
        <div className="border-b border-border px-4 py-3 sm:px-5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Loop State
          </div>
          <div className="mt-2 grid gap-3 sm:grid-cols-2 xl:grid-cols-4 text-xs">
            {experiment.lastRestartedAt && (
              <div className="rounded-md border border-border/70 bg-muted/10 px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Last Restart</div>
                <div className="mt-1 font-medium">{timeAgo(experiment.lastRestartedAt)}</div>
                <div className="mt-1 text-muted-foreground">
                  {experiment.lastRestartReason ?? "loop resumed"}
                </div>
              </div>
            )}
            {(experiment.lastStoppedAt || experiment.stopReason || experiment.lastStopReason) && (
              <div className="rounded-md border border-border/70 bg-muted/10 px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Last Stop</div>
                <div className="mt-1 font-medium">
                  {experiment.lastStoppedAt ? timeAgo(experiment.lastStoppedAt) : "still active"}
                </div>
                <div className="mt-1 text-muted-foreground">
                  {experiment.stopReason ?? experiment.lastStopReason ?? "none recorded"}
                </div>
              </div>
            )}
            {experiment.winnerPath && (
              <div className="rounded-md border border-border/70 bg-muted/10 px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Winner</div>
                <div className="mt-1 flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  {pathTail(experiment.winnerPath)}
                </div>
              </div>
            )}
            {experiment.reviewMemoPath && (
              <div className="rounded-md border border-border/70 bg-muted/10 px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Morning Memo</div>
                <div className="mt-1 flex items-center gap-1.5 font-medium">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground/70" />
                  {pathTail(experiment.reviewMemoPath)}
                </div>
              </div>
            )}
          </div>
          {experiment.sourceUnavailableReason && experiment.displayStatus !== "completed" && (
            <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-300">
              <AlertTriangle className="h-3.5 w-3.5" />
              Unavailable: {experiment.sourceUnavailableReason}
            </div>
          )}
        </div>
      )}

      {experiment.generations.length > 0 && (
        <div className="border-b border-border px-4 py-3 sm:px-5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Round Timeline</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {experiment.generations.map((generation) => (
              <span
                key={`${experiment.issueId}-timeline-${generation.round}`}
                className={cn(
                  "inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium",
                  generationPillTone(generation.status),
                )}
                title={generation.summary ?? undefined}
              >
                R{generation.round}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── Keep/discard history (generations) ──────────────── */}
      {recentGens.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center gap-2 px-4 py-2.5 sm:px-5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            Keep / Discard History
            <span className="text-[11px] font-normal">
              (last {recentGens.length} of {experiment.generations.length})
            </span>
          </button>

          {expanded && (
            <div className="border-t border-border/50">
              <div className="grid grid-cols-[3rem_5.5rem_5rem_5rem_1fr_5rem] gap-2 px-3 py-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground bg-muted/20 border-b border-border/50">
                <span>Round</span>
                <span>Outcome</span>
                <span>Score</span>
                <span>Round Credit</span>
                <span>Candidate</span>
                <span className="text-right">When</span>
              </div>
              <div className="divide-y divide-border/40">
                {recentGens.map((gen) => (
                  <GenerationRow key={`${experiment.issueId}-${gen.round}`} gen={gen} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main panel ─────────────────────────────────────────────────── */

interface AutoresearchPanelProps {
  autoresearch: DashboardSummary["autoresearch"];
  title?: string;
  subtitle?: string;
}

export function AutoresearchOverviewCard({
  autoresearch,
  title = "Autoresearch",
  subtitle = "Team-round optimization lanes — one mutable artifact, fixed-budget iterations, keep/discard ratchet.",
}: AutoresearchPanelProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <div className="border-b border-border p-4 sm:p-5">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-muted-foreground/70" />
          <p className="text-sm font-medium">{title}</p>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      </div>

      <div className="grid gap-0 divide-y divide-border sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
        <div className="p-4 sm:p-5">
          <div className="text-xs text-muted-foreground">Active Lanes</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{autoresearch.active}</div>
          <div className="mt-1 text-xs text-muted-foreground">{autoresearch.running} looping now</div>
        </div>
        <div className="p-4 sm:p-5">
          <div className="text-xs text-muted-foreground">Generations Today</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{autoresearch.generationsToday}</div>
          <div className="mt-1 text-xs text-muted-foreground">keep/discard rounds completed</div>
        </div>
        <div className="p-4 sm:p-5">
          <div className="text-xs text-muted-foreground">Tracked Spend Today</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {formatCents(autoresearch.spendTodayCents)}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {formatMeteringNote({
              spendCents: autoresearch.spendTodayCents,
              budgetCents: autoresearch.budgetTodayCents,
              emptyLabel: "no metered spend recorded yet",
              noBudgetLabel: "no configured cap",
            })}
          </div>
        </div>
        <div className="p-4 sm:p-5">
          <div className="text-xs text-muted-foreground">Completed Today</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{autoresearch.completedToday}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {autoresearch.blocked} paused/failed
            {autoresearch.utilizationPercent != null &&
              autoresearch.spendTodayCents > 0 &&
              ` · ${autoresearch.utilizationPercent}% of configured cap`}
          </div>
        </div>
      </div>
    </div>
  );
}

export function AutoresearchPanel({
  autoresearch,
}: {
  autoresearch: DashboardSummary["autoresearch"];
}) {
  const primaryExperiments = autoresearch.experiments.filter(
    (experiment) => experiment.localStrategy === "team_round",
  );
  const fallbackExperiments = autoresearch.experiments.filter(
    (experiment) => experiment.localStrategy !== "team_round",
  );
  const visibleExperiments =
    primaryExperiments.length > 0 ? primaryExperiments : autoresearch.experiments;

  return (
    <div className="space-y-4">
      {autoresearch.experiments.length === 0 ? (
        <div className="rounded-lg border border-border p-6 text-center">
          <FlaskConical className="h-8 w-8 mx-auto text-muted-foreground/40" />
          <p className="mt-3 text-sm text-muted-foreground">
            No autoresearch lanes yet.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Create an issue with an experiment contract to start a bounded improvement loop.
          </p>
        </div>
      ) : (
        <>
          {visibleExperiments.map((experiment) => (
            <ExperimentLane key={experiment.issueId} experiment={experiment} />
          ))}

          {primaryExperiments.length > 0 && fallbackExperiments.length > 0 && (
            <details className="rounded-lg border border-border overflow-hidden">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-muted-foreground hover:text-foreground">
                Fallback / Legacy Lanes ({fallbackExperiments.length})
              </summary>
              <div className="border-t border-border bg-muted/10 p-4 space-y-4">
                {fallbackExperiments.map((experiment) => (
                  <ExperimentLane key={experiment.issueId} experiment={experiment} />
                ))}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
}
