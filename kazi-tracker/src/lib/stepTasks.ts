import { arrayMove } from "@dnd-kit/sortable";
import type { StepTask } from "../types/task";

export function normalizeStepOrders(steps: StepTask[]): StepTask[] {
  return steps.map((step, order) => {
    const normalized = { ...step } as StepTask & { priority?: unknown };
    delete normalized.priority;
    return { ...normalized, order };
  });
}

export function moveStepTask(
  steps: StepTask[],
  stepId: string,
  overStepId: string,
): StepTask[] {
  const oldIndex = steps.findIndex((step) => step.id === stepId);
  const newIndex = steps.findIndex((step) => step.id === overStepId);
  if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return steps;
  return normalizeStepOrders(arrayMove(steps, oldIndex, newIndex));
}
