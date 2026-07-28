import { AnimatePresence, motion } from "framer-motion";
import { ListChecks, X } from "lucide-react";
import type { StepTask, Task } from "../types/task";
import { StepTaskBoard } from "./StepTaskBoard";

export function StepTasksDialog({
  task,
  onClose,
  onChange,
}: {
  task: Task | null;
  onClose: () => void;
  onChange: (taskId: string, steps: StepTask[]) => Promise<void>;
}) {
  return (
    <AnimatePresence>
      {task && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => event.target === event.currentTarget && onClose()}
        >
          <motion.div
            className="modal-card step-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="step-dialog-title"
            initial={{ opacity: 0, y: 22, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 14, scale: 0.98 }}
          >
            <div className="modal-heading">
              <div>
                <span className="eyebrow">Completion path</span>
                <h2 id="step-dialog-title">
                  <ListChecks size={20} />
                  {task.title}
                </h2>
              </div>
              <button className="icon-button" onClick={onClose} aria-label="Close">
                <X size={19} />
              </button>
            </div>
            <p className="step-dialog-copy">
              Complete every step before finishing the main task. Drag steps to
              arrange the order in which they should be done.
            </p>
            <StepTaskBoard
              steps={task.steps ?? []}
              onChange={(steps) => onChange(task.id, steps)}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
