import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, Clock, ListChecks, XCircle } from "lucide-react";
import type { DashboardSummary } from "@/lib/api";

interface Props {
  summary: DashboardSummary | null;
  loading: boolean;
}

const cards = [
  { key: "total_actions" as const, label: "Total Actions", icon: ListChecks, accent: "info" },
  { key: "pending" as const, label: "Pending", icon: Clock, accent: "warning" },
  { key: "approved" as const, label: "Approved", icon: CheckCircle2, accent: "success" },
  { key: "rejected" as const, label: "Rejected", icon: XCircle, accent: "destructive" },
];

const accentMap: Record<string, { bar: string; iconBg: string; iconText: string }> = {
  info: { bar: "bg-info", iconBg: "bg-info-soft", iconText: "text-info" },
  warning: { bar: "bg-warning", iconBg: "bg-warning-soft", iconText: "text-warning" },
  success: { bar: "bg-success", iconBg: "bg-success-soft", iconText: "text-success" },
  destructive: { bar: "bg-destructive", iconBg: "bg-danger-soft", iconText: "text-destructive" },
};

export const DashboardCards = ({ summary, loading }: Props) => {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map(({ key, label, icon: Icon, accent }) => {
        const styles = accentMap[accent];
        return (
          <Card
            key={key}
            className="relative overflow-hidden border-border/60 shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-elevated)]"
          >
            <div className={`absolute inset-y-0 left-0 w-1.5 ${styles.bar}`} />
            <div className="flex items-start justify-between p-5 pl-6">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{label}</p>
                {loading || !summary ? (
                  <Skeleton className="mt-2 h-9 w-16" />
                ) : (
                  <p className="mt-1 text-3xl font-bold tracking-tight text-foreground">
                    {summary[key] ?? 0}
                  </p>
                )}
              </div>
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${styles.iconBg}`}>
                <Icon className={`h-5 w-5 ${styles.iconText}`} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
