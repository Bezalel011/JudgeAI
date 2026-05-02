import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Check, X, Search, AlertTriangle, Loader2, Eye } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { Action } from "@/lib/api";
import { reviewAction } from "@/services/services";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface Props {
  actions: Action[];
  loading: boolean;
  onChanged: () => void;
}

const PAGE_SIZE = 8;

const isUrgent = (deadline?: string) => {
  if (!deadline) return false;
  const d = new Date(deadline);
  if (isNaN(d.getTime())) return false;
  const diff = (d.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return diff <= 7 && diff >= -1;
};

const truncate = (text: string, n = 80) =>
  text.length > n ? text.slice(0, n).trimEnd() + "…" : text;

export const ActionsTable = ({ actions, loading, onChanged }: Props) => {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState<string | null>(null);
  const [openTask, setOpenTask] = useState<Action | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return actions.filter((a) => {
      const status = (a.status ?? "PENDING").toUpperCase();
      if (statusFilter !== "ALL" && status !== statusFilter) return false;
      if (!q) return true;
      const haystack = [a.task, a.type, a.deadline, String(a.id)]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [actions, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const handleReview = async (id: Action["id"], status: "APPROVED" | "REJECTED") => {
    const key = `${id}-${status}`;
    setBusy(key);
    try {
      await reviewAction(id, status);
      toast.success(`Action #${id} ${status.toLowerCase()}.`);
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update action.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
      <div className="flex flex-col gap-3 border-b border-border/60 bg-muted/30 px-6 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">Extracted Actions</h2>
          <p className="text-sm text-muted-foreground">
            Review and verify actions extracted from judgments.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search actions…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-8 sm:w-64"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => { setStatusFilter(v); setPage(1); }}
          >
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="APPROVED">Approved</SelectItem>
              <SelectItem value="REJECTED">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/20 hover:bg-muted/20">
              <TableHead className="w-16">ID</TableHead>
              <TableHead className="w-36">Type</TableHead>
              <TableHead>Task</TableHead>
              <TableHead className="w-40">Deadline</TableHead>
              <TableHead className="w-32">Status</TableHead>
              <TableHead className="w-44 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="py-12 text-center text-muted-foreground">
                  <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />
                  Loading actions…
                </TableCell>
              </TableRow>
            ) : pageItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-12 text-center text-muted-foreground">
                  No actions found. Upload a judgment to get started.
                </TableCell>
              </TableRow>
            ) : (
              pageItems.map((a) => {
                const task = a.task ?? "";
                const urgent = isUrgent(a.deadline);
                const status = (a.status ?? "PENDING").toUpperCase();
                return (
                  <TableRow key={String(a.id)} className="align-top">
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      #{a.id}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex rounded-md bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                        {a.type ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-md">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            onClick={() => setOpenTask(a)}
                            className="flex items-start gap-1.5 text-left text-sm text-foreground hover:text-primary"
                          >
                            <span>{truncate(task) || "—"}</span>
                            {task.length > 80 && <Eye className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-60" />}
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">
                          <p className="text-xs">{task || "No task description"}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <div className={cn("flex items-center gap-1.5 text-sm", urgent && "font-semibold text-destructive")}>
                        {urgent && <AlertTriangle className="h-3.5 w-3.5" />}
                        {a.deadline ?? "—"}
                      </div>
                    </TableCell>
                    <TableCell><StatusBadge status={status} /></TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy !== null || status === "APPROVED"}
                          onClick={() => handleReview(a.id, "APPROVED")}
                          className="border-success/30 bg-success-soft text-success hover:bg-success hover:text-success-foreground"
                        >
                          {busy === `${a.id}-APPROVED` ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Check className="h-3.5 w-3.5" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy !== null || status === "REJECTED"}
                          onClick={() => handleReview(a.id, "REJECTED")}
                          className="border-destructive/30 bg-danger-soft text-destructive hover:bg-destructive hover:text-destructive-foreground"
                        >
                          {busy === `${a.id}-REJECTED` ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <X className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-between border-t border-border/60 bg-muted/20 px-6 py-3">
          <p className="text-xs text-muted-foreground">
            Showing {(currentPage - 1) * PAGE_SIZE + 1}–
            {Math.min(currentPage * PAGE_SIZE, filtered.length)} of {filtered.length}
          </p>
          <Pagination className="mx-0 w-auto justify-end">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(e) => { e.preventDefault(); setPage(Math.max(1, currentPage - 1)); }}
                  className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
              {Array.from({ length: totalPages }, (_, i) => i + 1).slice(0, 5).map((p) => (
                <PaginationItem key={p}>
                  <PaginationLink
                    href="#"
                    isActive={p === currentPage}
                    onClick={(e) => { e.preventDefault(); setPage(p); }}
                  >
                    {p}
                  </PaginationLink>
                </PaginationItem>
              ))}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => { e.preventDefault(); setPage(Math.min(totalPages, currentPage + 1)); }}
                  className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}

      <Dialog open={!!openTask} onOpenChange={(o) => !o && setOpenTask(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Action #{openTask?.id} — {openTask?.type ?? "—"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Task</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">{openTask?.task ?? "—"}</p>
            </div>
            <div className="flex items-center gap-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Deadline</p>
                <p className="mt-1 text-sm">{openTask?.deadline ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</p>
                <div className="mt-1"><StatusBadge status={openTask?.status} /></div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
