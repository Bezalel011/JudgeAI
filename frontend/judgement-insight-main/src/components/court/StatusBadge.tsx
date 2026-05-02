import { cn } from "@/lib/utils";

export const StatusBadge = ({ status }: { status?: string }) => {
  const s = (status ?? "PENDING").toUpperCase();
  const map: Record<string, string> = {
    APPROVED: "bg-success-soft text-success ring-success/20",
    REJECTED: "bg-danger-soft text-destructive ring-destructive/20",
    PENDING: "bg-warning-soft text-warning ring-warning/20",
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
