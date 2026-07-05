import type { Timestamp } from "firebase/firestore";

export type Priority = "high" | "medium" | "low";

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
}

export interface TaskInput {
  title: string;
  priority: Priority;
  deadline: string | null;
  parentId: string | null;
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

export interface DailySummary {
  date: string;
  totalTasks: number;
  completedTasks: number;
  completionRate: number;
  byPriority: Record<Priority, PrioritySummary>;
  completedList: CompletedTaskSummary[];
  generatedAt: Timestamp;
}
