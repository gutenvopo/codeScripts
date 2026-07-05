import { arrayMove } from "@dnd-kit/sortable";
import type { Priority, Task } from "../types/task";

export interface TaskOrderUpdate {
  id: string;
  order: number;
  priority?: Priority;
}

const priorities: Priority[] = ["high", "medium", "low"];

function byOrder(left: Task, right: Task): number {
  return left.order - right.order || left.id.localeCompare(right.id);
}

function childSuffix(index: number): string {
  let value = index + 1;
  let suffix = "";
  while (value > 0) {
    value -= 1;
    suffix = String.fromCharCode(97 + (value % 26)) + suffix;
    value = Math.floor(value / 26);
  }
  return suffix;
}

export function activeParents(tasks: Task[], priority?: Priority): Task[] {
  return tasks
    .filter(
      (task) =>
        !task.completed &&
        !task.parentId &&
        (priority === undefined || task.priority === priority),
    )
    .sort(byOrder);
}

export function activeChildren(tasks: Task[], parentId: string): Task[] {
  return tasks
    .filter((task) => !task.completed && task.parentId === parentId)
    .sort(byOrder);
}

export function createPositionLabels(tasks: Task[]): Map<string, string> {
  const labels = new Map<string, string>();
  let parentPosition = 1;
  priorities.forEach((priority) => {
    activeParents(tasks, priority).forEach((parent) => {
      const parentLabel = String(parentPosition++);
      labels.set(parent.id, parentLabel);
      activeChildren(tasks, parent.id).forEach((child, index) => {
        labels.set(child.id, `${parentLabel}${childSuffix(index)}`);
      });
    });
  });
  return labels;
}

function mergeUpdate(
  updates: Map<string, TaskOrderUpdate>,
  update: TaskOrderUpdate,
): void {
  updates.set(update.id, { ...updates.get(update.id), ...update });
}

function addRankUpdates(
  updates: Map<string, TaskOrderUpdate>,
  originalTasks: Task[],
  orderedParents: Task[],
  priority: Priority,
): void {
  orderedParents.forEach((parent, order) => {
    const original = originalTasks.find((task) => task.id === parent.id);
    if (!original || (original.order === order && original.priority === priority)) return;
    mergeUpdate(updates, {
      id: parent.id,
      order,
      ...(original.priority !== priority ? { priority } : {}),
    });
  });
}

export function parentReorderUpdates(
  tasks: Task[],
  parentId: string,
  targetPriority: Priority,
  overParentId: string | null,
): TaskOrderUpdate[] {
  const parent = tasks.find((task) => task.id === parentId && !task.parentId);
  if (!parent) return [];
  const sourceParents = activeParents(tasks, parent.priority);
  const updates = new Map<string, TaskOrderUpdate>();

  if (parent.priority === targetPriority) {
    const oldIndex = sourceParents.findIndex((task) => task.id === parentId);
    const newIndex = overParentId
      ? sourceParents.findIndex((task) => task.id === overParentId)
      : sourceParents.length - 1;
    if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return [];
    addRankUpdates(
      updates,
      tasks,
      arrayMove(sourceParents, oldIndex, newIndex),
      targetPriority,
    );
    return [...updates.values()];
  }

  const remainingSource = sourceParents.filter((task) => task.id !== parentId);
  const destination = activeParents(tasks, targetPriority);
  const targetIndex = overParentId
    ? destination.findIndex((task) => task.id === overParentId)
    : destination.length;
  destination.splice(targetIndex < 0 ? destination.length : targetIndex, 0, parent);
  addRankUpdates(updates, tasks, remainingSource, parent.priority);
  addRankUpdates(updates, tasks, destination, targetPriority);
  tasks
    .filter((task) => task.parentId === parentId && task.priority !== targetPriority)
    .forEach((child) => {
      mergeUpdate(updates, {
        id: child.id,
        order: child.order,
        priority: targetPriority,
      });
    });
  return [...updates.values()];
}

export function childReorderUpdates(
  tasks: Task[],
  childId: string,
  overChildId: string,
): TaskOrderUpdate[] {
  const child = tasks.find((task) => task.id === childId);
  const overChild = tasks.find((task) => task.id === overChildId);
  if (!child?.parentId || child.parentId !== overChild?.parentId) return [];
  const siblings = activeChildren(tasks, child.parentId);
  const oldIndex = siblings.findIndex((task) => task.id === childId);
  const newIndex = siblings.findIndex((task) => task.id === overChildId);
  if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return [];
  return arrayMove(siblings, oldIndex, newIndex)
    .map((task, order) => ({ id: task.id, order }))
    .filter((update) => tasks.find((task) => task.id === update.id)?.order !== update.order);
}
