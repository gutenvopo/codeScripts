import { useEffect, useRef, useState } from "react";
import type {
  DraggableAttributes,
  DraggableSyntheticListeners,
} from "@dnd-kit/core";
import { motion } from "framer-motion";
import {
  Clock3,
  GripVertical,
  ListChecks,
  Pencil,
  Repeat2,
} from "lucide-react";
import type { Task } from "../types/task";
import { ConfettiBurst } from "./ConfettiBurst";
import { PriorityBadge } from "./PriorityBadge";

interface TaskItemProps {
  task: Task;
  depth?: number;
  dragHandle?: {
    attributes: DraggableAttributes;
    listeners: DraggableSyntheticListeners;
    setActivatorNodeRef: (element: HTMLElement | null) => void;
  };
  completionLocked?: boolean;
  celebrating?: boolean;
  onEdit: (task: Task) => void;
  onComplete: (taskId: string, completed: boolean) => Promise<void>;
  onOpenSteps?: (task: Task) => void;
}

function deadlineLabel(deadline: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(deadline));
}

export function TaskItem({
  task,
  depth = 0,
  dragHandle,
  completionLocked = false,
  celebrating = false,
  onEdit,
  onComplete,
  onOpenSteps,
}: TaskItemProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [burst, setBurst] = useState(0);
  const [origin, setOrigin] = useState({ x: 0.5, y: 0.5 });
  const overdue =
    Boolean(task.deadline) && !task.completed && new Date(task.deadline!).getTime() < Date.now();
  const steps = task.steps ?? [];
  const incompleteSteps = steps.filter((step) => !step.completed).length;
  const opensSteps = steps.length > 0 && onOpenSteps !== undefined;

  useEffect(() => {
    if (!celebrating) return;
    const rectangle = cardRef.current?.getBoundingClientRect();
    if (rectangle) {
      setOrigin({
        x: (rectangle.left + rectangle.width / 2) / window.innerWidth,
        y: (rectangle.top + rectangle.height / 2) / window.innerHeight,
      });
    }
    setBurst((value) => value + 1);
  }, [celebrating]);

  function attachNode(node: HTMLDivElement | null): void {
    cardRef.current = node;
  }

  async function handleToggle(): Promise<void> {
    if (completionLocked) return;
    await onComplete(task.id, !task.completed);
  }

  return (
    <>
      <motion.div
        ref={attachNode}
        layout
        animate={
          celebrating
            ? { x: [0, -7, 7, -5, 5, 0], scale: [1, 1.02, 1] }
            : { x: 0, scale: 1 }
        }
        transition={{ duration: 0.42 }}
        className={`task-card task-${task.priority} ${opensSteps ? "task-has-steps" : ""} ${
          overdue ? "task-overdue" : ""
        } ${
          task.completed ? "task-completed" : ""
        }`}
        role={opensSteps ? "button" : undefined}
        tabIndex={opensSteps ? 0 : undefined}
        onClick={() => opensSteps && onOpenSteps(task)}
        onKeyDown={(event) => {
          if (
            event.target === event.currentTarget &&
            opensSteps &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            onOpenSteps(task);
          }
        }}
      >
        {dragHandle && (
          <button
            ref={dragHandle.setActivatorNodeRef}
            className="drag-handle"
            {...dragHandle.attributes}
            {...dragHandle.listeners}
            aria-label={`Drag ${task.title}`}
            onClick={(event) => event.stopPropagation()}
          >
            <GripVertical size={17} />
          </button>
        )}
        <button
          type="button"
          className={`task-checkbox ${celebrating || task.completed ? "checked" : ""}`}
          aria-label={
            completionLocked
              ? "Complete all sub-tasks and step tasks first"
              : task.completed
                ? "Mark task incomplete"
                : "Mark task complete"
          }
          title={
            completionLocked
              ? "Complete all sub-tasks and step tasks first"
              : undefined
          }
          disabled={completionLocked}
          onClick={(event) => {
            event.stopPropagation();
            void handleToggle();
          }}
        >
          <span />
        </button>
        <div className="task-content">
          <div className="task-title-row">
            <h3>{task.title}</h3>
            <PriorityBadge priority={task.priority} />
          </div>
          <div className="task-meta">
            {task.recurring && (
              <span className="recurring-label">
                <Repeat2 size={13} />
                Recurring
              </span>
            )}
            {steps.length > 0 && (
              <span className="step-count-label">
                <ListChecks size={13} />
                {steps.length} {steps.length === 1 ? "step" : "steps"}
                {incompleteSteps > 0 ? ` · ${incompleteSteps} remaining` : " · complete"}
              </span>
            )}
            {task.deadline && (
              <span className={overdue ? "overdue-label" : ""}>
                <Clock3 size={13} />
                {overdue ? "Overdue · " : ""}
                {deadlineLabel(task.deadline)}
              </span>
            )}
            {depth > 0 && <span>Sub-task</span>}
          </div>
        </div>
        <button
          type="button"
          className="icon-button"
          onClick={(event) => {
            event.stopPropagation();
            onEdit(task);
          }}
          aria-label={`Edit ${task.title}`}
        >
          <Pencil size={16} />
        </button>
      </motion.div>
      <ConfettiBurst burst={burst} origin={origin} />
    </>
  );
}
