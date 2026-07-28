import type { Timestamp } from "firebase/firestore";

export type Priority = "high" | "medium" | "low";

export interface StepTask {
  id: string;
  title: string;
  order: number;
  completed: boolean;
}

export interface Task {
  id: string;
  title: string;
  priority: Priority;
  deadline: string | null;
  order: number;
  completed: boolean;
  completedAt: Timestamp | null;
  createdAt: Timestamp;
  date: string;
  parentId: string | null;
  recurring: boolean;
  steps?: StepTask[];
}

export interface TaskInput {
  title: string;
  priority: Priority;
  deadline: string | null;
  parentId: string | null;
  recurring: boolean;
}

export interface PrioritySummary {
  total: number;
  completed: number;
}

export interface CompletedTaskSummary {
  title: string;
  priority: Priority;
  completedAt: Timestamp | null;
}

export interface LateTaskSummary {
  title: string;
  priority: Priority;
  deadline: string;
  recurring: boolean;
}

export interface DailySummary {
  date: string;
  totalTasks: number;
  completedTasks: number;
  completionRate: number;
  byPriority: Record<Priority, PrioritySummary>;
  completedList: CompletedTaskSummary[];
  lateTasks?: number;
  lateList?: LateTaskSummary[];
  generatedAt: Timestamp;
}
