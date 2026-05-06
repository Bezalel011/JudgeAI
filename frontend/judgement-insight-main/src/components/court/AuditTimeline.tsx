import type { AuditEntry } from "@/lib/api";

interface Props {
  audits: AuditEntry[];
}

export const AuditTimeline = ({ audits }: Props) => {
  if (!audits.length) {
    return <p className="mt-2 text-sm text-muted-foreground">No audit trail available.</p>;
  }

  return (
    <div className="mt-2 space-y-2">
      {audits.map((entry) => (
        <div key={entry.id} className="rounded-md border border-border/60 p-3 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium">{entry.action}</span>
            <span className="text-xs text-muted-foreground">{entry.timestamp}</span>
          </div>
          <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
            {entry.entity_type} #{entry.entity_id} by {entry.performed_by}
          </p>
          {entry.details ? (
            <pre className="mt-2 overflow-x-auto rounded bg-muted/40 p-2 text-xs text-muted-foreground">
{JSON.stringify(entry.details, null, 2)}
            </pre>
          ) : null}
        </div>
      ))}
    </div>
  );
};