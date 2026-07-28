import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Plus } from "lucide-react";
import { AddTaskModal } from "../components/AddTaskModal";
import { TaskItem } from "../components/TaskItem";
import { TaskList } from "../components/TaskList";
import { StepTasksDialog } from "../components/StepTasksDialog";
import { WeatherWidget } from "../components/WeatherWidget";
import { useTasks } from "../hooks/useTasks";
import { reportAppError } from "../lib/errorLog";
import { nairobiDeadlineIso } from "../lib/nairobiDate";
import {
  allStepsComplete,
  computeParentState,
  isTaskCompletionLocked,
} from "../lib/taskHierarchy";
import {
  activeChildren,
  childReorderUpdates,
  createPositionLabels,
  parentReorderUpdates,
  type TaskOrderUpdate,
} from "../lib/taskOrdering";
import type { Priority, StepTask, Task, TaskInput } from "../types/task";
import type { UserProfile } from "../types/profile";

const priorities: Priority[] = ["high", "medium", "low"];
const completionAnimationMs = 520;
const shoppingTitle = "Shopping";

function waitForCompletionAnimation(): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, completionAnimationMs));
}

export function TasksPage({
  uid,
  profile,
}: {
  uid: string;
  profile: UserProfile | null;
}) {
  const {
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
  } = useTasks(uid);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [focusSubtask, setFocusSubtask] = useState(false);
  const [shoppingOpening, setShoppingOpening] = useState(false);
  const [shoppingError, setShoppingError] = useState<string | null>(null);
  const [celebratingTaskIds, setCelebratingTaskIds] = useState<Set<string>>(new Set());
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [stepDialogTaskId, setStepDialogTaskId] = useState<string | null>(null);
  const pendingCompletionIds = useRef<Set<string>>(new Set());
  const previousTasks = useRef<Task[] | null>(null);
  const frozenDragTasks = useRef<Task[] | null>(null);
  const shoppingActionPending = useRef(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 180, tolerance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const openTasks = useMemo(() => tasks.filter((task) => !task.completed), [tasks]);
  const renderedTasks = activeDragId && frozenDragTasks.current
    ? frozenDragTasks.current
    : tasks;
  const activeTasks = useMemo(
    () => renderedTasks.filter((task) => !task.completed),
    [renderedTasks],
  );
  const positionLabels = useMemo(
    () => createPositionLabels(renderedTasks),
    [renderedTasks],
  );
  const completedTasks = useMemo(
    () =>
      tasks
        .filter((task) => task.completed)
        .sort(
          (a, b) =>
            (b.completedAt?.toMillis() ?? 0) - (a.completedAt?.toMillis() ?? 0),
        ),
    [tasks],
  );
  const completedFamilies = useMemo(() => {
    const completedIds = new Set(completedTasks.map((task) => task.id));
    return completedTasks
      .filter((task) => !task.parentId || !completedIds.has(task.parentId))
      .map((parent) => ({
        parent,
        children: completedTasks
          .filter((task) => task.parentId === parent.id)
          .sort((a, b) => a.order - b.order),
      }));
  }, [completedTasks]);
  const lockedParentIds = useMemo(
    () =>
      new Set(
        tasks
          .filter((task) => isTaskCompletionLocked(task, tasks))
          .map((task) => task.id),
      ),
    [tasks],
  );

  const setCelebrating = useCallback((taskIds: string[], active: boolean): void => {
    setCelebratingTaskIds((current) => {
      const next = new Set(current);
      taskIds.forEach((taskId) => (active ? next.add(taskId) : next.delete(taskId)));
      return next;
    });
  }, []);

  const autoCompleteParent = useCallback(
    async (parentId: string): Promise<void> => {
      if (pendingCompletionIds.current.has(parentId)) return;
      pendingCompletionIds.current.add(parentId);
      setCelebrating([parentId], true);
      await waitForCompletionAnimation();
      setCelebrating([parentId], false);
      try {
        await setCompleted(parentId, true);
      } finally {
        pendingCompletionIds.current.delete(parentId);
      }
    },
    [setCelebrating, setCompleted],
  );

  useEffect(() => {
    if (loading) {
      previousTasks.current = null;
      return;
    }
    const priorTasks = previousTasks.current;
    previousTasks.current = tasks;
    if (!priorTasks) return;

    tasks.forEach((parent) => {
      const priorState = computeParentState(parent.id, priorTasks);
      const currentState = computeParentState(parent.id, tasks);
      if (!priorState.allChildrenComplete && currentState.allChildrenComplete) {
        if (!parent.completed && allStepsComplete(parent)) {
          void autoCompleteParent(parent.id);
        }
      } else if (
        priorState.allChildrenComplete &&
        !currentState.allChildrenComplete &&
        parent.completed &&
        !pendingCompletionIds.current.has(parent.id)
      ) {
        void setCompleted(parent.id, false);
      }
    });
  }, [autoCompleteParent, loading, setCompleted, tasks]);

  const handleCompletion = useCallback(
    async (taskId: string, completed: boolean): Promise<void> => {
      const task = tasks.find((candidate) => candidate.id === taskId);
      if (!task || pendingCompletionIds.current.has(taskId)) return;
      if (completed && lockedParentIds.has(taskId)) return;
      if (!completed) {
        await setCompleted(taskId, false);
        return;
      }

      const celebrationIds = [taskId];
      if (task.parentId) {
        const projected = tasks.map((candidate) =>
          candidate.id === taskId ? { ...candidate, completed: true } : candidate,
        );
        const parent = tasks.find((candidate) => candidate.id === task.parentId);
        if (
          parent &&
          !parent.completed &&
          computeParentState(parent.id, projected).allChildrenComplete &&
          allStepsComplete(parent)
        ) {
          celebrationIds.push(parent.id);
        }
      }
      if (celebrationIds.some((id) => pendingCompletionIds.current.has(id))) return;

      celebrationIds.forEach((id) => pendingCompletionIds.current.add(id));
      setCelebrating(celebrationIds, true);
      await waitForCompletionAnimation();
      setCelebrating(celebrationIds, false);
      try {
        await setCompleted(taskId, true);
      } finally {
        celebrationIds.forEach((id) => pendingCompletionIds.current.delete(id));
      }
    },
    [lockedParentIds, setCelebrating, setCompleted, tasks],
  );

  function openNewTask(): void {
    setEditingTask(null);
    setFocusSubtask(false);
    setModalOpen(true);
  }

  function openEditTask(task: Task): void {
    setEditingTask(task);
    setFocusSubtask(false);
    setModalOpen(true);
  }

  async function openShoppingSubtask(): Promise<void> {
    if (shoppingActionPending.current || loading) return;
    shoppingActionPending.current = true;
    setShoppingOpening(true);
    setShoppingError(null);
    try {
      const existingShopping = tasks.find(
        (task) =>
          !task.completed
          && !task.parentId
          && task.priority === "medium"
          && task.title.trim().toLocaleLowerCase() === shoppingTitle.toLowerCase(),
      );
      const shoppingTask = existingShopping ?? await addTask({
        title: shoppingTitle,
        priority: "medium",
        deadline: nairobiDeadlineIso("23:59"),
        parentId: null,
        recurring: false,
      });
      setEditingTask(shoppingTask);
      setFocusSubtask(true);
      setModalOpen(true);
    } catch (caught) {
      reportAppError(caught, "Shopping quick action");
      setShoppingError(
        caught instanceof Error
          ? caught.message
          : "Could not open the Shopping task.",
      );
    } finally {
      shoppingActionPending.current = false;
      setShoppingOpening(false);
    }
  }

  function closeTaskModal(): void {
    setModalOpen(false);
    setFocusSubtask(false);
  }

  async function saveStepTasks(
    taskId: string,
    steps: StepTask[],
  ): Promise<void> {
    setEditingTask((current) =>
      current?.id === taskId ? { ...current, steps } : current,
    );
    await updateStepTasks(taskId, steps);
  }

  async function saveTask(input: TaskInput): Promise<void> {
    if (editingTask) await updateTask(editingTask.id, input);
    else await addTask(input);
  }

  function handleDragEnd({ active, over }: DragEndEvent): void {
    const dragTasks = frozenDragTasks.current ?? tasks;
    const activeTask = dragTasks.find((task) => task.id === active.id);
    let updates: TaskOrderUpdate[] = [];
    if (over && activeTask && active.id !== over.id) {
      const overId = String(over.id);
      const overTask = dragTasks.find((task) => task.id === overId);
      if (activeTask.parentId) {
        if (overTask?.parentId === activeTask.parentId) {
          updates = childReorderUpdates(dragTasks, activeTask.id, overTask.id);
        }
      } else {
        const overParent = overTask?.parentId
          ? dragTasks.find((task) => task.id === overTask.parentId)
          : overTask;
        const targetPriority = overId.startsWith("group-")
          ? (overId.replace("group-", "") as Priority)
          : overParent?.priority;
        if (targetPriority) {
          updates = parentReorderUpdates(
            dragTasks,
            activeTask.id,
            targetPriority,
            overParent?.id ?? null,
          );
        }
      }
    }
    const persistence = reorderTasks(updates);
    frozenDragTasks.current = null;
    setActiveDragId(null);
    void persistence;
  }

  function handleDragStart({ active }: DragStartEvent): void {
    frozenDragTasks.current = tasks;
    setActiveDragId(String(active.id));
  }

  function handleDragCancel(): void {
    frozenDragTasks.current = null;
    setActiveDragId(null);
  }

  const draggedTask = activeDragId
    ? (frozenDragTasks.current ?? tasks).find((task) => task.id === activeDragId)
    : undefined;
  const draggedChildren = draggedTask && !draggedTask.parentId
    ? activeChildren(frozenDragTasks.current ?? tasks, draggedTask.id)
    : [];
  const greetingName = profile
    ? `${profile.firstName} ${profile.lastName.charAt(0).toUpperCase()}.`
    : null;

  return (
    <main>
      <div className="task-page-context">
        <p className="task-greeting">
          {greetingName ? `Welcome back, ${greetingName}` : "Hello"}
        </p>
      </div>
      <WeatherWidget uid={uid} />
      <div className="page-heading">
        <div>
          <span className="eyebrow">Today’s command centre</span>
          <h1>Make progress visible.</h1>
          <p>
            {openTasks.length} open {openTasks.length === 1 ? "task" : "tasks"} ·{" "}
            {completedTasks.length} completed
          </p>
        </div>
        <button className="primary-button add-task-button" onClick={openNewTask}>
          <Plus size={18} />
          Add task
        </button>
      </div>

      {(shoppingError ?? error) && (
        <div className="error-banner">{shoppingError ?? error}</div>
      )}
      {loading ? (
        <div className="loading-grid">
          <div /><div /><div />
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          modifiers={[restrictToVerticalAxis]}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <div className="priority-grid">
            {priorities.map((priority) => (
              <TaskList
                key={priority}
                priority={priority}
                tasks={activeTasks}
                positionLabels={positionLabels}
                lockedParentIds={lockedParentIds}
                celebratingTaskIds={celebratingTaskIds}
                onEdit={openEditTask}
                onComplete={handleCompletion}
                onOpenSteps={(task) => setStepDialogTaskId(task.id)}
              />
            ))}
          </div>
          <DragOverlay>
            {draggedTask && (
              <div className="task-drag-overlay">
                <TaskItem
                  task={draggedTask}
                  completionLocked={lockedParentIds.has(draggedTask.id)}
                  onEdit={openEditTask}
                  onComplete={handleCompletion}
                />
                {draggedChildren.map((child) => (
                  <div key={child.id} className="overlay-child-task">
                    <TaskItem
                      task={child}
                      depth={1}
                      onEdit={openEditTask}
                      onComplete={handleCompletion}
                    />
                  </div>
                ))}
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}

      <section className="completed-section">
        <header>
          <div>
            <span className="eyebrow">Done and dusted</span>
            <h2><CheckCircle2 size={19} /> Completed</h2>
          </div>
          <strong>{completedTasks.length.toString().padStart(2, "0")}</strong>
        </header>
        <AnimatePresence initial={false}>
          {completedFamilies.map(({ parent, children }) => (
            <motion.div
              key={parent.id}
              className="task-family completed-task-family"
              layout
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
            >
              <TaskItem
                task={parent}
                completionLocked={lockedParentIds.has(parent.id)}
                celebrating={celebratingTaskIds.has(parent.id)}
                onEdit={openEditTask}
                onComplete={handleCompletion}
                onOpenSteps={(task) => setStepDialogTaskId(task.id)}
              />
              {children.map((child) => (
                <div key={child.id} className="completed-child-task">
                  <TaskItem
                    task={child}
                    depth={1}
                    celebrating={celebratingTaskIds.has(child.id)}
                    onEdit={openEditTask}
                    onComplete={handleCompletion}
                    onOpenSteps={(task) => setStepDialogTaskId(task.id)}
                  />
                </div>
              ))}
            </motion.div>
          ))}
        </AnimatePresence>
        {!completedTasks.length && (
          <p className="completed-empty">Completed tasks land here. Go make a dent.</p>
        )}
      </section>

      <div className="floating-task-actions" aria-label="Quick task actions">
        <button
          className="floating-task-action floating-shopping-action"
          type="button"
          disabled={shoppingOpening || loading}
          onClick={() => void openShoppingSubtask()}
          aria-label="Add a Shopping subtask"
        >
          <span className="floating-action-icon"><Plus size={25} /></span>
          <span className="floating-action-label">
            {shoppingOpening ? "Opening…" : "Shopping"}
          </span>
        </button>
        <button
          className="floating-task-action floating-add-action"
          type="button"
          onClick={openNewTask}
          aria-label="Add task"
        >
          <span className="floating-action-icon"><Plus size={25} /></span>
          <span className="floating-action-label">Task</span>
        </button>
      </div>
      <AddTaskModal
        open={modalOpen}
        task={
          editingTask
            ? tasks.find((task) => task.id === editingTask.id) ?? editingTask
            : null
        }
        tasks={openTasks}
        focusSubtask={focusSubtask}
        onClose={closeTaskModal}
        onSave={saveTask}
        onAddSubtask={addSubtask}
        onUpdateSteps={saveStepTasks}
        onDelete={
          editingTask
            ? async () => {
                if (window.confirm(`Delete “${editingTask.title}”?`)) {
                  await removeTask(editingTask.id);
                }
              }
            : undefined
        }
      />
      <StepTasksDialog
        task={
          stepDialogTaskId
            ? tasks.find((task) => task.id === stepDialogTaskId) ?? null
            : null
        }
        onClose={() => setStepDialogTaskId(null)}
        onChange={saveStepTasks}
      />
    </main>
  );
}
