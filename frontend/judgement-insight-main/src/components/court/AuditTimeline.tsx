import type { AuditEntry } from "@/lib/api";

interface Props {
  audits: AuditEntry[];
}

type DetailRow = {
  label: string;
  value: string;
};

const toText = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const items = value.map((item) => toText(item)).filter((item): item is string => Boolean(item));
    return items.length ? items.join(", ") : null;
  }

  return null;
};

const buildDetailRows = (details: Record<string, unknown>): DetailRow[] => {
  const rows: DetailRow[] = [];

  const nextStatus = toText(details.new_status) ?? toText(details.to_status);
  if (nextStatus) {
    rows.push({ label: "Status changed to", value: nextStatus });
  } else {
    const status = toText(details.status);
    if (status) {
      rows.push({ label: "Status", value: status });
    }
  }

  const decision = toText(details.decision);
  if (decision) {
    rows.push({ label: "Decision", value: decision });
  }

  const comments = toText(details.comments);
  if (comments) {
    rows.push({ label: "Comments", value: comments });
  }

  const additionalMappings: Array<[string, string]> = [
    ["from_status", "Previous status"],
    ["type", "Type"],
    ["confidence", "Confidence"],
    ["channel", "Channel"],
    ["due_at", "Due at"],
    ["filename", "Filename"],
    ["notification_id", "Notification ID"],
    ["error_message", "Error"],
  ];

  for (const [key, label] of additionalMappings) {
    const value = toText(details[key]);
    if (value) {
      rows.push({ label, value });
    }
  }

  if (typeof details.has_extracted_text === "boolean") {
    rows.push({
      label: "Extracted text",
      value: details.has_extracted_text ? "Available" : "Not available",
    });
  }

  return rows;
};

export const AuditTimeline = ({ audits }: Props) => {
  if (!audits.length) {
    return <p className="mt-2 text-sm text-muted-foreground">No audit trail available.</p>;
  }

  return (
    <div className="mt-2 space-y-2">
      {audits.map((entry) => {
        const detailRows = entry.details ? buildDetailRows(entry.details) : [];

        return (
          <div key={entry.id} className="rounded-md border border-border/60 p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{entry.action}</span>
              <span className="text-xs text-muted-foreground">{entry.timestamp}</span>
            </div>
            <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
              {entry.entity_type} #{entry.entity_id} by {entry.performed_by}
            </p>
            {detailRows.length ? (
              <div className="mt-2 space-y-1 rounded bg-muted/40 p-2 text-xs text-muted-foreground">
                {detailRows.map((row) => (
                  <p key={`${entry.id}-${row.label}`}>
                    <span className="font-medium text-foreground/80">{row.label}:</span> {row.value}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
};