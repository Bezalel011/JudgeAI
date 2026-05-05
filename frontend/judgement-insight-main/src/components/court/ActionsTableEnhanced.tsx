import { useEffect, useMemo, useState } from "react";
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
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Check, X, Search, AlertTriangle, Loader2, Eye, Edit2 } from "lucide-react";
import { StatusBadge, PriorityBadge, ConfidenceBadge } from "./StatusBadge";
import type { Action, ActionHistory } from "@/lib/api";
import { getActionHistory, reviewAction, updateAction } from "@/services/services";
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

export const ActionsTableEnhanced = ({ actions, loading, onChanged }: Props) => {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState<string | null>(null);
  const [openTask, setOpenTask] = useState<Action | null>(null);
  const [editingTask, setEditingTask] = useState<Action | null>(null);
  const [history, setHistory] = useState<ActionHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [editForm, setEditForm] = useState({ task: "", deadline: "", department: "", priority: "" });

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return actions.filter((a) => {
      const status = (a.status ?? "PENDING").toUpperCase();
      const priority = (a.priority ?? "Medium").toLowerCase();
      
      if (statusFilter !== "ALL" && status !== statusFilter) return false;
      if (priorityFilter !== "ALL" && priority !== priorityFilter) return false;
      
      if (!q) return true;
      const haystack = [a.task, a.type, a.deadline, String(a.id), a.department]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [actions, search, statusFilter, priorityFilter]);

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

  const handleEditOpen = (action: Action) => {
    setEditingTask(action);
    setEditForm({
      task: action.task ?? "",
      deadline: action.deadline ?? "",
      department: action.department ?? "",
      priority: action.priority ?? "Medium",
    });
  };

  const handleEditSave = async () => {
    if (!editingTask) return;
    setBusy("edit");
    try {
      await updateAction(editingTask.id, {
        task: editForm.task || undefined,
        deadline: editForm.deadline || undefined,
        department: editForm.department || undefined,
        priority: editForm.priority || undefined,
      });
      toast.success("Action updated successfully.");
      setEditingTask(null);
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update action.");
    } finally {
      setBusy(null);
    }
  };

  useEffect(() => {
    let alive = true;
    const loadHistory = async () => {
      if (!openTask?.id) {
        setHistory(null);
        return;
      }
      setHistoryLoading(true);
      try {
        const data = await getActionHistory(openTask.id);
        if (alive) setHistory(data);
      } catch {
        if (alive) setHistory(null);
      } finally {
        if (alive) setHistoryLoading(false);
      }
    };

    loadHistory();
    return () => {
      alive = false;
    };
  }, [openTask?.id]);

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
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-8 sm:w-64"
            />
          </div>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Statuses</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="APPROVED">Approved</SelectItem>
              <SelectItem value="REJECTED">Rejected</SelectItem>
              <SelectItem value="OVERDUE">Overdue</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={(v) => { setPriorityFilter(v); setPage(1); }}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Priorities</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/20 hover:bg-muted/20">
              <TableHead className="w-12">ID</TableHead>
              <TableHead className="w-24">Type</TableHead>
              <TableHead className="min-w-48">Task</TableHead>
              <TableHead className="w-16">Priority</TableHead>
              <TableHead className="w-20">Confidence</TableHead>
              <TableHead className="w-28">Deadline</TableHead>
              <TableHead className="w-24">Status</TableHead>
              <TableHead className="w-48 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="py-12 text-center text-muted-foreground">
                  <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />
                  Loading actions…
                </TableCell>
              </TableRow>
            ) : pageItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="py-12 text-center text-muted-foreground">
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
                    <TableCell className="font-mono text-xs font-semibold text-muted-foreground">
                      #{a.id}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex rounded-md bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                        {a.type ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            onClick={() => setOpenTask(a)}
                            className="flex items-start gap-1.5 text-left text-sm text-foreground hover:text-primary transition-colors"
                          >
                            <span className="truncate">{truncate(task) || "—"}</span>
                            {task.length > 80 && <Eye className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-60" />}
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">
                          <p className="text-xs">{task || "No task description"}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <PriorityBadge priority={a.priority} />
                    </TableCell>
                    <TableCell>
                      <ConfidenceBadge confidence={a.confidence} />
                    </TableCell>
                    <TableCell>
                      <div className={cn("flex items-center gap-1.5 text-xs whitespace-nowrap", urgent && "font-semibold text-destructive")}>
                        {urgent && <AlertTriangle className="h-3 w-3 shrink-0" />}
                        {a.deadline ?? "—"}
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button size="sm" variant="ghost" onClick={() => setOpenTask(a)}>
                              <Eye className="h-3.5 w-3.5" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>View Details</TooltipContent>
                        </Tooltip>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button size="sm" variant="ghost" onClick={() => handleEditOpen(a)}>
                              <Edit2 className="h-3.5 w-3.5" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Edit Action</TooltipContent>
                        </Tooltip>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy !== null || status === "APPROVED"}
                          onClick={() => handleReview(a.id, "APPROVED")}
                          className="border-success/30 bg-success-soft text-success hover:bg-success hover:text-success-foreground"
                          title="Approve"
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
                          title="Reject"
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
                  onClick={(e) => {
                    e.preventDefault();
                    setPage(Math.max(1, currentPage - 1));
                  }}
                  className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .slice(0, 5)
                .map((p) => (
                  <PaginationItem key={p}>
                    <PaginationLink
                      href="#"
                      isActive={p === currentPage}
                      onClick={(e) => {
                        e.preventDefault();
                        setPage(p);
                      }}
                    >
                      {p}
                    </PaginationLink>
                  </PaginationItem>
                ))}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setPage(Math.min(totalPages, currentPage + 1));
                  }}
                  className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}

      {/* Details Modal */}
      <Dialog open={!!openTask} onOpenChange={(o) => !o && setOpenTask(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Action #{openTask?.id} <span className="text-sm font-normal text-muted-foreground">— {openTask?.type ?? "—"}</span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</p>
                <div className="mt-1">
                  <StatusBadge status={openTask?.status} />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Priority</p>
                <div className="mt-1">
                  <PriorityBadge priority={openTask?.priority} />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Confidence</p>
                <div className="mt-1">
                  <ConfidenceBadge confidence={openTask?.confidence} />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Department</p>
                <p className="mt-1 text-sm">{openTask?.department ?? "—"}</p>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Task</p>
              <p className="mt-2 rounded-lg bg-muted/30 p-3 text-sm leading-relaxed whitespace-pre-wrap">{openTask?.task ?? "—"}</p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Evidence & Source</p>
              {openTask?.evidence ? (
                <div className="rounded-lg bg-muted/30 p-3 text-sm space-y-2">
                  {(() => {
                    const ev = openTask.evidence as any;
                    const text = (ev?.text ?? "") as string;
                    const start = Number(ev?.char_start ?? -1);
                    const end = Number(ev?.char_end ?? -1);
                    
                    if (start >= 0 && end > start) {
                      const before = text.slice(0, start);
                      const middle = text.slice(start, end);
                      const after = text.slice(end);
                      return (
                        <p className="whitespace-pre-wrap leading-relaxed">
                          {before}
                          <mark className="bg-yellow-200 text-yellow-900 px-0.5 rounded font-semibold">{middle}</mark>
                          {after}
                        </p>
                      );
                    }
                    return <p className="whitespace-pre-wrap leading-relaxed text-muted-foreground">{text || "No text available"}</p>;
                  })()}
                  <p className="text-xs text-muted-foreground border-t border-border/60 pt-2">
                    <span className="font-medium">Page:</span> {String(ev?.page ?? "—")} · <span className="font-medium">Sentence:</span> {String(ev?.sentence_index ?? "—")}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No evidence available</p>
              )}
            </div>

            <div className="grid grid-cols-1 gap-2 pt-2 border-t border-border/60">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Deadline</p>
                <p className="mt-1 text-sm">{openTask?.deadline ?? "—"}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Created</p>
                  <p className="mt-1 text-xs text-muted-foreground">{String((openTask as any)?.created_at ?? "—")}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Updated</p>
                  <p className="mt-1 text-xs text-muted-foreground">{String((openTask as any)?.updated_at ?? "—")}</p>
                </div>
              </div>
            </div>

            <div className="border-t border-border/60 pt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Review History</p>
              {historyLoading ? (
                <p className="mt-2 text-sm text-muted-foreground">Loading review history...</p>
              ) : history?.reviews?.length ? (
                <div className="mt-2 space-y-2">
                  {history.reviews.map((r) => (
                    <div key={r.id} className="rounded-md border border-border/60 bg-muted/20 p-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">{r.reviewer_name}</span>
                        <span className="text-xs text-muted-foreground">{r.timestamp}</span>
                      </div>
                      <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground font-medium">{r.decision}</p>
                      {r.comments ? <p className="mt-1 text-xs leading-relaxed">{r.comments}</p> : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">No review records yet.</p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={!!editingTask} onOpenChange={(o) => !o && setEditingTask(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Action #{editingTask?.id}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Task</label>
              <Input
                className="mt-1"
                placeholder="Task description"
                value={editForm.task}
                onChange={(e) => setEditForm({ ...editForm, task: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Deadline</label>
              <Input
                className="mt-1"
                type="date"
                value={editForm.deadline?.split("T")[0] ?? ""}
                onChange={(e) => setEditForm({ ...editForm, deadline: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Department</label>
              <Input
                className="mt-1"
                placeholder="Department"
                value={editForm.department}
                onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Priority</label>
              <Select value={editForm.priority} onValueChange={(v) => setEditForm({ ...editForm, priority: v })}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Low">Low</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingTask(null)}>
              Cancel
            </Button>
            <Button disabled={busy === "edit"} onClick={handleEditSave}>
              {busy === "edit" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
