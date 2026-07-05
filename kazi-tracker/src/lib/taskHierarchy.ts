import type { Task } from "../types/task";

export interface ParentState {
  hasChildren: boolean;
  allChildrenComplete: boolean;
}

export function computeParentState(parentId: string, tasks: Task[]): ParentState {
  const children = tasks.filter((task) => task.parentId === parentId);
  return {
    hasChildren: children.length > 0,
    allChildrenComplete:
      children.length > 0 && children.every((child) => child.completed),
  };
}
