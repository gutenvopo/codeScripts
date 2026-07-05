import { useCallback, useEffect, useMemo, useState } from "react";
import {
  collection,
  doc,
  limit,
  onSnapshot,
  query,
  serverTimestamp,
  setDoc,
  updateDoc,
  where,
  writeBatch,
} from "firebase/firestore";
import { db } from "../lib/firebase";
import { computeParentState } from "../lib/taskHierarchy";
import type { TaskOrderUpdate } from "../lib/taskOrdering";
import type { Task, TaskInput } from "../types/task";
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
        setError(caught.message);
        setLoading(false);
      },
    );
  }, [dateKey, taskCollection]);

  const addTask = useCallback(
    async (input: TaskInput): Promise<void> => {
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
      });
    },
    [dateKey, taskCollection, tasks],
  );

  const updateTask = useCallback(
    async (taskId: string, input: TaskInput): Promise<void> => {
      await updateDoc(doc(taskCollection, taskId), {
        title: input.title,
        priority: input.priority,
        deadline: input.deadline,
        parentId: input.parentId,
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
      const ownParentState = computeParentState(task.id, tasks);
      if (completed && ownParentState.hasChildren && !ownParentState.allChildrenComplete) {
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
        if (parent && completed && parentState.allChildrenComplete && !parent.completed) {
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
    updateTask,
    removeTask,
    setCompleted,
    reorderTasks,
  };
}
