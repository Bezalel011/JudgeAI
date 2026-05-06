import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import type { Action } from "@/lib/api";
import { updateAction } from "@/services/services";

interface Props {
  action: Action | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
}

export const ActionEditDialog = ({ action, open, onOpenChange, onSaved }: Props) => {
  const [saving, setSaving] = useState(false);
  const [task, setTask] = useState("");
  const [department, setDepartment] = useState("");
  const [deadline, setDeadline] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [reviewerName, setReviewerName] = useState("human_reviewer");
  const [comments, setComments] = useState("");

  useEffect(() => {
    if (!action) return;
    setTask(String(action.task ?? ""));
    setDepartment(String(action.department ?? ""));
    setDeadline(String(action.deadline ?? ""));
    setPriority(String(action.priority ?? "Medium"));
    setComments("");
  }, [action]);

  const handleSave = async () => {
    if (!action) return;

    setSaving(true);
    try {
      await updateAction(action.id, {
        task,
        department,
        deadline: deadline || null,
        priority,
        reviewer_name: reviewerName,
        comments: comments || null,
      });
      toast.success(`Action #${action.id} updated.`);
      onSaved();
      onOpenChange(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update action.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Action #{action?.id ?? ""}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="task">Task</Label>
            <Textarea id="task" value={task} onChange={(e) => setTask(e.target.value)} rows={4} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Input id="department" value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="deadline">Deadline</Label>
            <Input id="deadline" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Priority</Label>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="High">High</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="Low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="reviewer_name">Reviewer</Label>
            <Input id="reviewer_name" value={reviewerName} onChange={(e) => setReviewerName(e.target.value)} />
          </div>
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="comments">Comments</Label>
            <Textarea id="comments" value={comments} onChange={(e) => setComments(e.target.value)} rows={3} placeholder="Optional edit note" />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving || !action}>
            {saving ? "Saving..." : "Save Edit"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};