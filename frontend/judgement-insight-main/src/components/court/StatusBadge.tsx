import { cn } from "@/lib/utils";

export const StatusBadge = ({ status }: { status?: string }) => {
  const s = (status ?? "PENDING").toUpperCase();
  const map: Record<string, string> = {
    APPROVED: "bg-success-soft text-success ring-success/20",
    REJECTED: "bg-danger-soft text-destructive ring-destructive/20",
    PENDING: "bg-warning-soft text-warning ring-warning/20",
    OVERDUE: "bg-destructive/10 text-destructive ring-destructive/30",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset",
        map[s] ?? "bg-muted text-muted-foreground ring-border"
      )}
    >
      {s}
    </span>
  );
};

export const PriorityBadge = ({ priority }: { priority?: string }) => {
  const p = (priority ?? "Medium").toLowerCase();
  const map: Record<string, string> = {
    high: "bg-destructive/10 text-destructive ring-destructive/30",
    medium: "bg-warning-soft text-warning ring-warning/20",
    low: "bg-success-soft text-success ring-success/20",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset capitalize",
        map[p] ?? "bg-muted text-muted-foreground ring-border"
      )}
    >
      {p}
    </span>
  );
};

export const ConfidenceBadge = ({ confidence }: { confidence?: string | number }) => {
  let conf = typeof confidence === "string" ? parseFloat(confidence) : confidence;
  if (isNaN(conf)) return <span className="text-xs text-muted-foreground">N/A</span>;
  
  // Normalize: if value is < 1, assume it's decimal (0.0-1.0), multiply by 100
  if (conf < 1) conf = conf * 100;
  
  let color = "bg-success-soft text-success ring-success/20"; // green > 80%
  if (conf < 50) color = "bg-destructive/10 text-destructive ring-destructive/30"; // red < 50%
  else if (conf < 80) color = "bg-warning-soft text-warning ring-warning/20"; // yellow 50-80%
  
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset", color)}>
      {Math.round(conf)}%
    </span>
  );
};
