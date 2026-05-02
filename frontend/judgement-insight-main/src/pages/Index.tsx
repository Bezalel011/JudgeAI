import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/court/Header";
import { UploadSection } from "@/components/court/UploadSection";
import { DashboardCards } from "@/components/court/DashboardCards";
import { ActionsTable } from "@/components/court/ActionsTable";
import { type Action, type DashboardSummary } from "@/lib/api";
import { getActions, getDashboard } from "@/services/services";
import { toast } from "sonner";

const Index = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [actionsLoading, setActionsLoading] = useState(true);

  const refreshSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      setSummary(await getDashboard());
    } catch (e) {
      toast.error(e instanceof Error ? `Dashboard: ${e.message}` : "Failed to load dashboard.");
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  const refreshActions = useCallback(async () => {
    setActionsLoading(true);
    try {
      setActions(await getActions());
    } catch (e) {
      toast.error(e instanceof Error ? `Actions: ${e.message}` : "Failed to load actions.");
    } finally {
      setActionsLoading(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    refreshSummary();
    refreshActions();
  }, [refreshSummary, refreshActions]);

  useEffect(() => { refreshAll(); }, [refreshAll]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto space-y-6 px-6 py-8">
        <UploadSection onProcessed={refreshAll} />
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">Overview</h2>
          <DashboardCards summary={summary} loading={summaryLoading} />
        </section>
        <ActionsTable actions={actions} loading={actionsLoading} onChanged={refreshAll} />
        <footer className="pb-4 pt-2 text-center text-xs text-muted-foreground">
          Connected to <code className="rounded bg-muted px-1 py-0.5">http://127.0.0.1:8000</code>
        </footer>
      </main>
    </div>
  );
};

export default Index;
