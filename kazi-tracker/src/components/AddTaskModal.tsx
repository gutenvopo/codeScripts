import { useEffect, useRef, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus, Trash2, X } from "lucide-react";
import { nairobiDeadlineIso, nairobiTimeValue } from "../lib/nairobiDate";
import type { Priority, StepTask, Task, TaskInput } from "../types/task";
import { StepTaskBoard } from "./StepTaskBoard";

const DEFAULT_DEADLINE_TIME = "23:59";
const parentTitleCollator = new Intl.Collator(undefined, {
  sensitivity: "base",
});

interface AddTaskModalProps {
  open: boolean;
  task: Task | null;
  tasks: Task[];
  focusSubtask?: boolean;
  onClose: () => void;
  onSave: (input: TaskInput) => Promise<void>;
  onAddSubtask?: (input: TaskInput) => Promise<void>;
  onDelete?: () => Promise<void>;
  onUpdateSteps?: (taskId: string, steps: StepTask[]) => Promise<void>;
}

function toTimeValue(deadline: string | null): string {
  if (!deadline) return "";
  return nairobiTimeValue(deadline);
}

export function AddTaskModal({
  open,
  task,
  tasks,
  focusSubtask = false,
  onClose,
  onSave,
  onAddSubtask,
  onDelete,
  onUpdateSteps,
}: AddTaskModalProps) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [deadlineTime, setDeadlineTime] = useState("");
  const [parentId, setParentId] = useState("");
  const [recurring, setRecurring] = useState(false);
  const [saving, setSaving] = useState(false);
  const [subtaskTitle, setSubtaskTitle] = useState("");
  const [subtaskPriority, setSubtaskPriority] = useState<Priority>("medium");
  const [subtaskDeadlineTime, setSubtaskDeadlineTime] = useState(
    DEFAULT_DEADLINE_TIME,
  );
  const [savingSubtask, setSavingSubtask] = useState(false);
  const initializedFor = useRef<string | null>(null);
  const subtaskInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) {
      initializedFor.current = null;
      return;
    }
    const taskKey = task?.id ?? "new-task";
    if (initializedFor.current === taskKey) return;
    initializedFor.current = taskKey;
    setTitle(task?.title ?? "");
    setPriority(task?.priority ?? "medium");
    setDeadlineTime(
      task ? toTimeValue(task.deadline) : DEFAULT_DEADLINE_TIME,
    );
    setParentId(task?.parentId ?? "");
    setRecurring(task?.recurring ?? false);
    setSubtaskTitle("");
    setSubtaskPriority(task?.priority ?? "medium");
    setSubtaskDeadlineTime(DEFAULT_DEADLINE_TIME);
  }, [task, open]);

  useEffect(() => {
    if (!open || !focusSubtask || !task) return;
    const frame = window.requestAnimationFrame(() => {
      subtaskInput.current?.focus();
      subtaskInput.current?.scrollIntoView({ block: "center" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [focusSubtask, open, task]);

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
      recurring,
    });
    setSaving(false);
    onClose();
  }

  async function addSubtask(): Promise<void> {
    if (!task || !onAddSubtask || !subtaskTitle.trim()) return;
    setSavingSubtask(true);
    const deadline = subtaskDeadlineTime
      ? nairobiDeadlineIso(subtaskDeadlineTime)
      : null;
    try {
      await onAddSubtask({
        title: subtaskTitle.trim(),
        priority: subtaskPriority,
        deadline,
        parentId: task.id,
        recurring: false,
      });
      setSubtaskTitle("");
      setSubtaskPriority(task.priority);
      setSubtaskDeadlineTime(DEFAULT_DEADLINE_TIME);
    } finally {
      setSavingSubtask(false);
    }
  }

  const parentOptions = tasks.filter(
    (candidate) =>
      !candidate.completed &&
      !candidate.parentId &&
      candidate.id !== task?.id,
  ).sort((left, right) => parentTitleCollator.compare(left.title, right.title));
  const canAddSubtask = Boolean(
    task && !task.parentId && !parentId && onAddSubtask,
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
            className={`modal-card ${task ? "task-editor-modal" : ""}`}
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
                  autoFocus={!focusSubtask}
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
              <label className="recurring-toggle">
                <input
                  type="checkbox"
                  checked={recurring}
                  onChange={(event) => setRecurring(event.target.checked)}
                />
                <span>
                  <strong>Recurring daily</strong>
                  Resets after the nightly report and starts fresh tomorrow.
                </span>
              </label>
              <label>
                Parent task <span className="optional">optional</span>
                <select
                  value={parentId}
                  disabled={(task?.steps?.length ?? 0) > 0}
                  onChange={(event) => setParentId(event.target.value)}
                >
                  <option value="">No parent</option>
                  {parentOptions.map((candidate) => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.title}
                    </option>
                  ))}
                </select>
              </label>
              {(task?.steps?.length ?? 0) > 0 && (
                <p className="step-parent-note">
                  Remove all step tasks before converting this main task into a subtask.
                </p>
              )}
              {canAddSubtask && (
                <section className="subtask-editor-section">
                  <div>
                    <span className="eyebrow">Subtask</span>
                    <h3>Add a subtask</h3>
                    <p>
                      Create a child task under this regular task.
                    </p>
                  </div>
                  <div className="subtask-add-form">
                    <input
                      ref={subtaskInput}
                      value={subtaskTitle}
                      onChange={(event) => setSubtaskTitle(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          void addSubtask();
                        }
                      }}
                      placeholder="What smaller step belongs here?"
                      maxLength={140}
                      aria-label="Subtask name"
                    />
                    <select
                      value={subtaskPriority}
                      onChange={(event) =>
                        setSubtaskPriority(event.target.value as Priority)
                      }
                      aria-label="Subtask priority"
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                    <input
                      type="time"
                      value={subtaskDeadlineTime}
                      onChange={(event) =>
                        setSubtaskDeadlineTime(event.target.value)
                      }
                      aria-label="Subtask deadline"
                    />
                    <button
                      type="button"
                      className="subtask-add-button"
                      disabled={savingSubtask || !subtaskTitle.trim()}
                      onClick={() => void addSubtask()}
                    >
                      <Plus size={15} />
                      {savingSubtask ? "Adding…" : "Add subtask"}
                    </button>
                  </div>
                </section>
              )}
              {task && !task.parentId && !parentId && onUpdateSteps && (
                <section className="step-editor-section">
                  <div>
                    <span className="eyebrow">Step tasks</span>
                    <h3>Build the completion path</h3>
                    <p>
                      Drag steps into the order they should be completed.
                    </p>
                  </div>
                  <StepTaskBoard
                    editable
                    steps={task.steps ?? []}
                    onChange={(steps) => onUpdateSteps(task.id, steps)}
                  />
                </section>
              )}
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
