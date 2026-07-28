import type { CSSProperties } from "react";
import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { activeChildren, activeParents } from "../lib/taskOrdering";
import type { Priority, Task } from "../types/task";
import { TaskItem } from "./TaskItem";

interface TaskListProps {
  priority: Priority;
  tasks: Task[];
  positionLabels: Map<string, string>;
  lockedParentIds: Set<string>;
  celebratingTaskIds: Set<string>;
  onEdit: (task: Task) => void;
  onComplete: (taskId: string, completed: boolean) => Promise<void>;
  onOpenSteps: (task: Task) => void;
}

interface SortableTaskProps {
  task: Task;
  label: string;
  familyStyle: CSSProperties;
  familyDragging: boolean;
  celebrating: boolean;
  onEdit: (task: Task) => void;
  onComplete: (taskId: string, completed: boolean) => Promise<void>;
  onOpenSteps: (task: Task) => void;
}

const headings: Record<Priority, { title: string; eyebrow: string }> = {
  high: { title: "High priority", eyebrow: "Do first" },
  medium: { title: "Medium priority", eyebrow: "Keep moving" },
  low: { title: "Low priority", eyebrow: "When time allows" },
};

function SortableChild({
  task,
  label,
  familyStyle,
  familyDragging,
  celebrating,
  onEdit,
  onComplete,
  onOpenSteps,
}: SortableTaskProps) {
  const {
    attributes,
    listeners,
    setActivatorNodeRef,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.id,
    data: { type: "child", parentId: task.parentId },
  });
  return (
    <div className="numbered-task-row child-task-row">
      <span className="task-position-label" aria-hidden="true">{label}</span>
      <div
        className={familyDragging ? "family-dragging" : undefined}
        style={familyStyle}
      >
        <div
          ref={setNodeRef}
          className={`task-sortable-content ${isDragging ? "sortable-source-dragging" : ""}`}
          style={{
            transform: CSS.Transform.toString(transform),
            transition,
          }}
        >
          <TaskItem
            task={task}
            depth={1}
            dragHandle={{ attributes, listeners, setActivatorNodeRef }}
            celebrating={celebrating}
            onEdit={onEdit}
            onComplete={onComplete}
            onOpenSteps={onOpenSteps}
          />
        </div>
      </div>
    </div>
  );
}

function SortableFamily({
  parent,
  children,
  positionLabels,
  lockedParentIds,
  celebratingTaskIds,
  onEdit,
  onComplete,
  onOpenSteps,
}: {
  parent: Task;
  children: Task[];
  positionLabels: Map<string, string>;
  lockedParentIds: Set<string>;
  celebratingTaskIds: Set<string>;
  onEdit: (task: Task) => void;
  onComplete: (taskId: string, completed: boolean) => Promise<void>;
  onOpenSteps: (task: Task) => void;
}) {
  const {
    attributes,
    listeners,
    setActivatorNodeRef,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: parent.id,
    data: { type: "parent", priority: parent.priority },
  });
  const familyStyle: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} className="task-family">
      <div className="numbered-task-row">
        <span className="task-position-label" aria-hidden="true">
          {positionLabels.get(parent.id)}
        </span>
        <div
          className={`task-sortable-content ${isDragging ? "sortable-source-dragging" : ""}`}
          style={familyStyle}
        >
          <TaskItem
            task={parent}
            dragHandle={{ attributes, listeners, setActivatorNodeRef }}
            completionLocked={lockedParentIds.has(parent.id)}
            celebrating={celebratingTaskIds.has(parent.id)}
            onEdit={onEdit}
            onComplete={onComplete}
            onOpenSteps={onOpenSteps}
          />
        </div>
      </div>
      <SortableContext
        items={children.map((child) => child.id)}
        strategy={verticalListSortingStrategy}
      >
        {children.map((child) => (
          <SortableChild
            key={child.id}
            task={child}
            label={positionLabels.get(child.id) ?? ""}
            familyStyle={familyStyle}
            familyDragging={isDragging}
            celebrating={celebratingTaskIds.has(child.id)}
            onEdit={onEdit}
            onComplete={onComplete}
            onOpenSteps={onOpenSteps}
          />
        ))}
      </SortableContext>
    </div>
  );
}

export function TaskList({
  priority,
  tasks,
  positionLabels,
  lockedParentIds,
  celebratingTaskIds,
  onEdit,
  onComplete,
  onOpenSteps,
}: TaskListProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `group-${priority}`,
    data: { type: "group", priority },
  });
  const parents = activeParents(tasks, priority);
  const visibleTaskCount = parents.reduce(
    (count, parent) => count + 1 + activeChildren(tasks, parent.id).length,
    0,
  );

  return (
    <section
      ref={setNodeRef}
      className={`priority-section section-${priority} ${isOver ? "drop-active" : ""}`}
    >
      <header className="priority-header">
        <div>
          <span>{headings[priority].eyebrow}</span>
          <h2>{headings[priority].title}</h2>
        </div>
        <strong>{visibleTaskCount.toString().padStart(2, "0")}</strong>
      </header>
      <SortableContext
        items={parents.map((task) => task.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="task-stack">
          {parents.map((parent) => (
            <SortableFamily
              key={parent.id}
              parent={parent}
              children={activeChildren(tasks, parent.id)}
              positionLabels={positionLabels}
              lockedParentIds={lockedParentIds}
              celebratingTaskIds={celebratingTaskIds}
              onEdit={onEdit}
              onComplete={onComplete}
              onOpenSteps={onOpenSteps}
            />
          ))}
          {parents.length === 0 && (
            <div className="empty-drop">Drop a task here or add something new.</div>
          )}
        </div>
      </SortableContext>
    </section>
  );
}
