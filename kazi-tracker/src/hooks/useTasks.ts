import { useCallback, useEffect, useMemo, useState } from "react";
import {
  collection,
  doc,
  limit,
  onSnapshot,
  query,
  serverTimestamp,
  setDoc,
  Timestamp,
  updateDoc,
  where,
  writeBatch,
} from "firebase/firestore";
import { db } from "../lib/firebase";
import {
  allStepsComplete,
  computeParentState,
  isTaskCompletionLocked,
} from "../lib/taskHierarchy";
import { reportAppError } from "../lib/errorLog";
import { normalizeStepOrders } from "../lib/stepTasks";
import type { TaskOrderUpdate } from "../lib/taskOrdering";
import type { StepTask, Task, TaskInput } from "../types/task";
import { useNairobiDate } from "./useNairobiDate";

export function useTasks(uid: string) {
  const { dateKey } = useNairobiDate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const taskCollection = useMemo(
    () => collection(db, "users", uid, "tasks"),
    [uid],
  );

  useEffect(() => {
    const taskQuery = query(
      taskCollection,
      where("date", "==", dateKey),
      limit(500),
    );
    return onSnapshot(
      taskQuery,
      (snapshot) => {
        setTasks(snapshot.docs.map((item) => item.data() as Task));
        setLoading(false);
      },
      (caught) => {
        reportAppError(caught, "Tasks subscription");
        setError(caught.message);
        setLoading(false);
      },
    );
  }, [dateKey, taskCollection]);

  const addTask = useCallback(
    async (input: TaskInput): Promise<Task> => {
      const samePriority = tasks.filter((task) => task.priority === input.priority);
      const reference = doc(taskCollection);
      await setDoc(reference, {
        ...input,
        id: reference.id,
        order: samePriority.length,
        completed: false,
        completedAt: null,
        createdAt: serverTimestamp(),
        date: dateKey,
        steps: [],
      });
      return {
        ...input,
        id: reference.id,
        order: samePriority.length,
        completed: false,
        completedAt: null,
        createdAt: Timestamp.now(),
        date: dateKey,
        steps: [],
      };
    },
    [dateKey, taskCollection, tasks],
  );

  const addSubtask = useCallback(
    async (input: TaskInput): Promise<void> => {
      if (!input.parentId) {
        await addTask(input);
        return;
      }

      const samePriority = tasks.filter((task) => task.priority === input.priority);
      const reference = doc(taskCollection);
      const batch = writeBatch(db);
      batch.set(reference, {
        ...input,
        id: reference.id,
        order: samePriority.length,
        completed: false,
        completedAt: null,
        createdAt: serverTimestamp(),
        date: dateKey,
        steps: [],
      });
      const parent = tasks.find((task) => task.id === input.parentId);
      if (parent?.completed) {
        batch.update(doc(taskCollection, parent.id), {
          completed: false,
          completedAt: null,
        });
      }
      await batch.commit();
    },
    [addTask, dateKey, taskCollection, tasks],
  );

  const updateTask = useCallback(
    async (taskId: string, input: TaskInput): Promise<void> => {
      await updateDoc(doc(taskCollection, taskId), {
        title: input.title,
        priority: input.priority,
        deadline: input.deadline,
        parentId: input.parentId,
        recurring: input.recurring,
      });
    },
    [taskCollection],
  );

  const removeTask = useCallback(
    async (taskId: string): Promise<void> => {
      const batch = writeBatch(db);
      batch.delete(doc(taskCollection, taskId));
      tasks
        .filter((task) => task.parentId === taskId)
        .forEach((child) => batch.update(doc(taskCollection, child.id), { parentId: null }));
      await batch.commit();
    },
    [taskCollection, tasks],
  );

  const setCompleted = useCallback(
    async (taskId: string, completed: boolean): Promise<void> => {
      const task = tasks.find((candidate) => candidate.id === taskId);
      if (!task) return;
      if (completed && isTaskCompletionLocked(task, tasks)) {
        return;
      }

      const batch = writeBatch(db);
      batch.update(doc(taskCollection, taskId), {
        completed,
        completedAt: completed ? serverTimestamp() : null,
      });
      if (task.parentId) {
        const projectedTasks = tasks.map((candidate) =>
          candidate.id === taskId ? { ...candidate, completed } : candidate,
        );
        const parent = tasks.find((candidate) => candidate.id === task.parentId);
        const parentState = computeParentState(task.parentId, projectedTasks);
        if (
          parent &&
          completed &&
          parentState.allChildrenComplete &&
          allStepsComplete(parent) &&
          !parent.completed
        ) {
          batch.update(doc(taskCollection, parent.id), {
            completed: true,
            completedAt: serverTimestamp(),
          });
        } else if (parent?.completed && !completed) {
          batch.update(doc(taskCollection, parent.id), {
            completed: false,
            completedAt: null,
          });
        }
      }
      await batch.commit();
    },
    [taskCollection, tasks],
  );

  const updateStepTasks = useCallback(
    async (taskId: string, steps: StepTask[]): Promise<void> => {
      const task = tasks.find((candidate) => candidate.id === taskId);
      if (!task) return;
      const normalized = normalizeStepOrders(
        steps
          .filter((step) => step.title.trim())
          .slice(0, 100)
          .map((step) => ({
            ...step,
            title: step.title.trim().slice(0, 140),
          })),
      );
      const original = {
        steps: task.steps ?? [],
        completed: task.completed,
        completedAt: task.completedAt,
      };
      const reopen = task.completed && normalized.some((step) => !step.completed);
      setTasks((current) =>
        current.map((candidate) =>
          candidate.id === taskId
            ? {
                ...candidate,
                steps: normalized,
                ...(reopen ? { completed: false, completedAt: null } : {}),
              }
            : candidate,
        ),
      );
      const batch = writeBatch(db);
      batch.update(doc(taskCollection, taskId), { steps: normalized });
      if (reopen) {
        batch.update(doc(taskCollection, taskId), {
          completed: false,
          completedAt: null,
        });
      }
      try {
        await batch.commit();
      } catch (caught) {
        reportAppError(caught, "Step task update");
        setTasks((current) =>
          current.map((candidate) =>
            candidate.id === taskId ? { ...candidate, ...original } : candidate,
          ),
        );
        throw caught;
      }
    },
    [taskCollection, tasks],
  );

  const reorderTasks = useCallback(
    async (updates: TaskOrderUpdate[]): Promise<void> => {
      if (updates.length === 0) return;
      const updatesById = new Map(updates.map((update) => [update.id, update]));
      const originals = new Map(
        tasks
          .filter((task) => updatesById.has(task.id))
          .map((task) => [task.id, { order: task.order, priority: task.priority }]),
      );
      setTasks((current) =>
        current.map((task) => {
          const update = updatesById.get(task.id);
          return update
            ? {
                ...task,
                order: update.order,
                priority: update.priority ?? task.priority,
              }
            : task;
        }),
      );

      const batch = writeBatch(db);
      updates.forEach((update) => {
        batch.update(doc(taskCollection, update.id), {
          order: update.order,
          ...(update.priority ? { priority: update.priority } : {}),
        });
      });
      try {
        await batch.commit();
      } catch (caught) {
        reportAppError(caught, "Task reorder");
        setTasks((current) =>
          current.map((task) => {
            const original = originals.get(task.id);
            return original ? { ...task, ...original } : task;
          }),
        );
        throw caught;
      }
    },
    [taskCollection, tasks],
  );

  return {
    tasks,
    loading,
    error,
    addTask,
    addSubtask,
    updateTask,
    removeTask,
    setCompleted,
    updateStepTasks,
    reorderTasks,
  };
}
