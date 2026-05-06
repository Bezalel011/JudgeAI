import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Bell, CheckCheck, Loader2, MailOpen } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import type { AlertEntry } from "@/lib/api";
import { getAlerts, markAlertRead } from "@/services/services";
import { toast } from "sonner";

interface Props {
  onUnreadCountChange?: (count: number) => void;
  refreshKey?: number;
}

const filterLabels: Record<string, string> = {
  all: "All",
  unread: "Unread",
  overdue: "Overdue",
};

export const AlertPanel = ({ onUnreadCountChange, refreshKey = 0 }: Props) => {
  const [filter, setFilter] = useState<"all" | "unread" | "overdue">("all");
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const unreadCount = useMemo(() => alerts.filter((alert) => !alert.is_read).length, [alerts]);

  useEffect(() => {
    onUnreadCountChange?.(unreadCount);
  }, [onUnreadCountChange, unreadCount]);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      setLoading(true);
      try {
        const data = await getAlerts(filter);
        if (alive) setAlerts(data);
      } catch (e) {
        if (alive) {
          setAlerts([]);
          toast.error(e instanceof Error ? e.message : "Failed to load alerts.");
        }
      } finally {
        if (alive) setLoading(false);
      }
    };

    load();
    return () => {
      alive = false;
    };
  }, [filter, refreshKey]);

  const handleRead = async (id: number) => {
    setBusyId(id);
    try {
      await markAlertRead(id);
      setAlerts((prev) => prev.map((alert) => (alert.id === id ? { ...alert, is_read: true } : alert)));
      toast.success("Alert marked as read.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update alert.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Card className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
      <div className="flex flex-col gap-3 border-b border-border/60 bg-muted/30 px-6 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-warning-soft text-warning">
            <Bell className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">Deadline Alerts</h2>
            <p className="text-sm text-muted-foreground">
              Upcoming and overdue reminders generated in the background.
            </p>
          </div>
        </div>
        <Select value={filter} onValueChange={(value) => setFilter(value as typeof filter)}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Filter alerts" />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(filterLabels).map(([value, label]) => (
              <SelectItem key={value} value={value}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="px-6 py-4">
        <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="secondary">Unread {unreadCount}</Badge>
          <Badge variant="outline">{alerts.filter((a) => a.type === "OVERDUE").length} overdue</Badge>
          <Badge variant="outline">{alerts.filter((a) => a.type === "UPCOMING").length} upcoming</Badge>
        </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-lg border border-dashed border-border/60 py-12 text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/60 py-12 text-center text-sm text-muted-foreground">
            <MailOpen className="mx-auto mb-3 h-6 w-6" />
            No alerts yet. Deadlines will appear here automatically.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, index) => {
              const overdue = alert.type === "OVERDUE";
              return (
                <div key={alert.id}>
                  <div className="flex flex-col gap-3 rounded-xl border border-border/60 bg-background p-4 shadow-sm md:flex-row md:items-start md:justify-between">
                    <div className="flex gap-3">
                      <div className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${overdue ? "bg-danger-soft text-destructive" : "bg-warning-soft text-warning"}`}>
                        <AlertTriangle className="h-4 w-4" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-semibold text-foreground">
                            Action #{alert.action_id}
                          </p>
                          <Badge variant={overdue ? "destructive" : "secondary"}>
                            {alert.type}
                          </Badge>
                          {!alert.is_read && <Badge variant="outline">Unread</Badge>}
                        </div>
                        <p className="text-sm text-muted-foreground">{alert.message}</p>
                        {alert.action ? (
                          <div className="text-xs text-muted-foreground">
                            <span className="font-medium text-foreground">Task:</span> {alert.action.task ?? "—"}
                            {alert.action.deadline ? (
                              <span className="ml-3"><span className="font-medium text-foreground">Deadline:</span> {alert.action.deadline}</span>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 self-start md:self-center">
                      <div className="text-right text-xs text-muted-foreground">
                        {alert.created_at}
                      </div>
                      {!alert.is_read && (
                        <Button size="sm" variant="outline" onClick={() => handleRead(alert.id)} disabled={busyId === alert.id}>
                          {busyId === alert.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCheck className="h-3.5 w-3.5" />}
                        </Button>
                      )}
                    </div>
                  </div>
                  {index < alerts.length - 1 ? <Separator className="my-3" /> : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};