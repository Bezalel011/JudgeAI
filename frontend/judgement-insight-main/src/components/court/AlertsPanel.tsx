import { useCallback, useEffect, useState } from "react";
import { Bell, BellRing, Clock3, Loader2, PauseCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Action, NotificationItem } from "@/lib/api";
import { acknowledgeAlert, getAlerts, snoozeAlert } from "@/services/services";
import { toast } from "sonner";

interface Props {
  refreshToken?: number;
}

export const AlertsPanel = ({ refreshToken = 0 }: Props) => {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<{ due_actions: Action[]; notifications: NotificationItem[] }>({
    due_actions: [],
    notifications: [],
  });
  const [busy, setBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAlerts(await getAlerts());
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshToken]);

  const handleAck = async (id: number) => {
    setBusy(id);
    try {
      await acknowledgeAlert(id);
      toast.success(`Alert #${id} acknowledged.`);
      await load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to acknowledge alert.");
    } finally {
      setBusy(null);
    }
  };

  const handleSnooze = async (id: number) => {
    setBusy(id);
    try {
      await snoozeAlert(id, 60);
      toast.success(`Alert #${id} snoozed for 60 minutes.`);
      await load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to snooze alert.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
      <div className="border-b border-border/60 bg-muted/30 px-6 py-4">
        <div className="flex items-center gap-2">
          <BellRing className="h-4 w-4 text-primary" />
          <h2 className="text-base font-semibold text-foreground">Deadline Alerts</h2>
        </div>
        <p className="text-sm text-muted-foreground">Due and upcoming actions requiring attention.</p>
      </div>
      <div className="p-6">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading alerts...
          </div>
        ) : alerts.notifications.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/60 p-4 text-sm text-muted-foreground">
            <Bell className="mb-2 h-4 w-4" />
            No active alerts.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.notifications.map((notification) => (
              <div key={notification.id} className="rounded-lg border border-border/60 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">Action #{notification.action_id}</p>
                    <p className="text-xs text-muted-foreground">
                      Due {new Date(notification.due_at).toLocaleString()} · {notification.channel} · {notification.status}
                    </p>
                    <p className="mt-2 text-sm text-foreground">{String((notification.payload as any)?.task ?? "")}</p>
                    <p className="mt-1 text-xs text-muted-foreground">Urgency: {String((notification.payload as any)?.urgency ?? "low")}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleSnooze(notification.id)} disabled={busy !== null}>
                      <Clock3 className="mr-1 h-3.5 w-3.5" /> Snooze
                    </Button>
                    <Button size="sm" onClick={() => handleAck(notification.id)} disabled={busy !== null}>
                      {busy === notification.id ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
                      <PauseCircle className="mr-1 h-3.5 w-3.5" /> Acknowledge
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};