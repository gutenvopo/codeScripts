import { useEffect, useState } from "react";
import {
  DndContext,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Check, GripVertical, Plus, Trash2 } from "lucide-react";
import { moveStepTask } from "../lib/stepTasks";
import type { StepTask } from "../types/task";

interface StepTaskBoardProps {
  steps: StepTask[];
  editable?: boolean;
  onChange: (steps: StepTask[]) => Promise<void>;
}

function StepTitleEditor({
  step,
  onSave,
}: {
  step: StepTask;
  onSave: (title: string) => void;
}) {
  const [title, setTitle] = useState(step.title);

  useEffect(() => setTitle(step.title), [step.title]);

  function save(): void {
    const trimmed = title.trim();
    if (trimmed && trimmed !== step.title) onSave(trimmed);
    else setTitle(step.title);
  }

  return (
    <input
      className="step-title-input"
      value={title}
      maxLength={140}
      aria-label={`Edit ${step.title}`}
      onChange={(event) => setTitle(event.target.value)}
      onBlur={save}
      onKeyDown={(event) => {
        if (event.key === "Enter") event.currentTarget.blur();
        if (event.key === "Escape") {
          setTitle(step.title);
          event.currentTarget.blur();
        }
      }}
    />
  );
}

function SortableStep({
  step,
  number,
  editable,
  onToggle,
  onRename,
  onRemove,
}: {
  step: StepTask;
  number: number;
  editable: boolean;
  onToggle: () => void;
  onRename: (title: string) => void;
  onRemove: () => void;
}) {
  const {
    attributes,
    listeners,
    setActivatorNodeRef,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: step.id });

  return (
    <div
      ref={setNodeRef}
      className={`step-task-row ${step.completed ? "step-completed" : ""} ${
        isDragging ? "step-dragging" : ""
      }`}
      style={{ transform: CSS.Transform.toString(transform), transition }}
    >
      <button
        ref={setActivatorNodeRef}
        className="step-drag-handle"
        {...attributes}
        {...listeners}
        aria-label={`Reorder ${step.title}`}
      >
        <GripVertical size={15} />
      </button>
      <span className="step-number">{number}</span>
      {editable ? (
        <StepTitleEditor step={step} onSave={onRename} />
      ) : (
        <button
          type="button"
          className={`step-checkbox ${step.completed ? "checked" : ""}`}
          onClick={onToggle}
          aria-label={
            step.completed ? `Mark ${step.title} incomplete` : `Complete ${step.title}`
          }
        >
          <Check size={12} />
        </button>
      )}
      {!editable && <span className="step-title">{step.title}</span>}
      {editable && (
        <button
          type="button"
          className="step-delete"
          onClick={onRemove}
          aria-label={`Remove ${step.title}`}
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
}

export function StepTaskBoard({
  steps,
  editable = false,
  onChange,
}: StepTaskBoardProps) {
  const [title, setTitle] = useState("");
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 160, tolerance: 5 } }),
  );

  function addStep(): void {
    const trimmed = title.trim();
    if (!trimmed || steps.length >= 100) return;
    setTitle("");
    void onChange([
      ...steps,
      {
        id: crypto.randomUUID(),
        title: trimmed,
        order: steps.length,
        completed: false,
      },
    ]);
  }

  function handleDragEnd({ active, over }: DragEndEvent): void {
    if (!over || active.id === over.id) return;
    void onChange(moveStepTask(steps, String(active.id), String(over.id)));
  }

  return (
    <div className="step-board">
      {editable && (
        <div className="step-add-form">
          <input
            value={title}
            maxLength={140}
            placeholder="Add a step needed to finish this task"
            onChange={(event) => setTitle(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addStep();
              }
            }}
          />
          <button
            type="button"
            className="step-add-button"
            disabled={!title.trim()}
            onClick={addStep}
          >
            <Plus size={15} />
            Add step
          </button>
        </div>
      )}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={steps.map((step) => step.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="step-group-list">
            {steps.map((step, index) => (
              <SortableStep
                key={step.id}
                step={step}
                number={index + 1}
                editable={editable}
                onToggle={() =>
                  void onChange(
                    steps.map((candidate) =>
                      candidate.id === step.id
                        ? { ...candidate, completed: !candidate.completed }
                        : candidate,
                    ),
                  )
                }
                onRename={(nextTitle) =>
                  void onChange(
                    steps.map((candidate) =>
                      candidate.id === step.id
                        ? { ...candidate, title: nextTitle }
                        : candidate,
                    ),
                  )
                }
                onRemove={() =>
                  void onChange(
                    steps.filter((candidate) => candidate.id !== step.id),
                  )
                }
              />
            ))}
            {steps.length === 0 && (
              <span className="step-empty">No step tasks yet.</span>
            )}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}
