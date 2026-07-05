import { useEffect, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Trash2, X } from "lucide-react";
import { nairobiDeadlineIso, nairobiTimeValue } from "../lib/nairobiDate";
import type { Priority, Task, TaskInput } from "../types/task";

const DEFAULT_DEADLINE_TIME = "23:59";

interface AddTaskModalProps {
  open: boolean;
  task: Task | null;
  tasks: Task[];
  onClose: () => void;
  onSave: (input: TaskInput) => Promise<void>;
  onDelete?: () => Promise<void>;
}

function toTimeValue(deadline: string | null): string {
  if (!deadline) return "";
  return nairobiTimeValue(deadline);
}

export function AddTaskModal({
  open,
  task,
  tasks,
  onClose,
  onSave,
  onDelete,
}: AddTaskModalProps) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [deadlineTime, setDeadlineTime] = useState("");
  const [parentId, setParentId] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setTitle(task?.title ?? "");
    setPriority(task?.priority ?? "medium");
    setDeadlineTime(
      task ? toTimeValue(task.deadline) : DEFAULT_DEADLINE_TIME,
    );
    setParentId(task?.parentId ?? "");
  }, [task, open]);

  async function submit(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    const deadline = deadlineTime
      ? nairobiDeadlineIso(deadlineTime)
      : null;
    await onSave({
      title: title.trim(),
      priority,
      deadline,
      parentId: parentId || null,
    });
    setSaving(false);
    onClose();
  }

  const parentOptions = tasks.filter(
    (candidate) =>
      !candidate.completed &&
      !candidate.parentId &&
      candidate.id !== task?.id,
  );

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => event.target === event.currentTarget && onClose()}
        >
          <motion.div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="task-modal-title"
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
          >
            <div className="modal-heading">
              <div>
                <span className="eyebrow">{task ? "Refine the plan" : "Capture the next move"}</span>
                <h2 id="task-modal-title">{task ? "Edit task" : "New task"}</h2>
              </div>
              <button className="icon-button" onClick={onClose} aria-label="Close">
                <X size={19} />
              </button>
            </div>
            <form onSubmit={(event) => void submit(event)}>
              <label>
                Task name
                <input
                  autoFocus
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="What needs to get done?"
                  maxLength={140}
                  required
                />
              </label>
              <div className="form-grid">
                <label>
                  Priority
                  <select
                    value={priority}
                    onChange={(event) => setPriority(event.target.value as Priority)}
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </label>
                <label>
                  Deadline
                  <input
                    type="time"
                    value={deadlineTime}
                    onChange={(event) => setDeadlineTime(event.target.value)}
                  />
                </label>
              </div>
              <label>
                Parent task <span className="optional">optional</span>
                <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
                  <option value="">No parent</option>
                  {parentOptions.map((candidate) => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.title}
                    </option>
                  ))}
                </select>
              </label>
              <div className="modal-actions">
                {task && onDelete && (
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => void onDelete().then(onClose)}
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                )}
                <span />
                <button type="button" className="ghost-button" onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Saving…" : task ? "Save changes" : "Add task"}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
