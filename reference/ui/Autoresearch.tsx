import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";
import { dashboardApi } from "../api/dashboard";
import { ActiveAgentsPanel } from "../components/ActiveAgentsPanel";
import { EmptyState } from "../components/EmptyState";
import { AutoresearchOverviewCard, AutoresearchPanel } from "../components/AutoresearchPanel";
import { PageSkeleton } from "../components/PageSkeleton";
import { useBreadcrumbs } from "../context/BreadcrumbContext";
import { useCompany } from "../context/CompanyContext";
import { queryKeys } from "../lib/queryKeys";

export function Autoresearch() {
  const { selectedCompanyId } = useCompany();
  const { setBreadcrumbs } = useBreadcrumbs();

  useEffect(() => {
    setBreadcrumbs([{ label: "Autoresearch" }]);
  }, [setBreadcrumbs]);

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.dashboard(selectedCompanyId!),
    queryFn: () => dashboardApi.summary(selectedCompanyId!),
    enabled: !!selectedCompanyId,
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
  });

  const experimentIssueIds = useMemo(
    () =>
      new Set(
        (data?.autoresearch.experiments ?? []).map(
          (experiment) => experiment.issueId,
        ),
      ),
    [data],
  );

  if (!selectedCompanyId) {
    return (
      <EmptyState
        icon={FlaskConical}
        message="Select a company to view autoresearch."
      />
    );
  }

  if (isLoading) {
    return <PageSkeleton variant="dashboard" />;
  }

  return (
    <div className="space-y-6">
      {error && (
        <p className="text-sm text-destructive">{error.message}</p>
      )}

      {data && (
        <AutoresearchOverviewCard autoresearch={data.autoresearch} />
      )}

      <ActiveAgentsPanel
        companyId={selectedCompanyId}
        title="Live Agents"
        emptyMessage="No live autoresearch iterations right now."
        minRuns={12}
        showTranscript={false}
        compact={true}
        activeOnly={true}
        issueFilter={(issue) =>
          Boolean(
            issue &&
              (issue.experimentContract ||
                (issue.parentId &&
                  experimentIssueIds.has(issue.parentId))),
          )
        }
      />

      {data && (
        <AutoresearchPanel autoresearch={data.autoresearch} />
      )}
    </div>
  );
}
