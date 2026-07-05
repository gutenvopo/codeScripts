import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import {
  FieldValue,
  Timestamp,
  getFirestore,
  type DocumentData,
} from "firebase-admin/firestore";
import { defineBoolean } from "firebase-functions/params";
import { onSchedule } from "firebase-functions/v2/scheduler";

initializeApp();

const db = getFirestore();
const archiveCompletedTasks = defineBoolean("ARCHIVE_COMPLETED_TASKS", {
  default: true,
  description:
    "Archive completed task documents after generating the nightly summary.",
});
const TIME_ZONE = "Africa/Nairobi";
const priorities = ["high", "medium", "low"] as const;
type Priority = (typeof priorities)[number];

interface TaskData {
  id: string;
  title: string;
  priority: Priority;
  completed: boolean;
  completedAt: Timestamp | null;
}

function zonedDateKey(value: Date): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value);
  const valueOf = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((part) => part.type === type)?.value ?? "";
  return `${valueOf("year")}-${valueOf("month")}-${valueOf("day")}`;
}

function previousDateKey(currentKey: string): string {
  const [year, month, day] = currentKey.split("-").map(Number);
  const previous = new Date(Date.UTC(year, month - 1, day - 1));
  return previous.toISOString().slice(0, 10);
}

function isPriority(value: unknown): value is Priority {
  return priorities.includes(value as Priority);
}

function toTask(data: DocumentData, id: string): TaskData {
  return {
    id,
    title: typeof data.title === "string" ? data.title : "Untitled task",
    priority: isPriority(data.priority) ? data.priority : "low",
    completed: data.completed === true,
    completedAt: data.completedAt instanceof Timestamp ? data.completedAt : null,
  };
}

function buildSummary(tasks: TaskData[], date: string): DocumentData {
  const completed = tasks.filter((task) => task.completed);
  const byPriority = Object.fromEntries(
    priorities.map((priority) => {
      const matching = tasks.filter((task) => task.priority === priority);
      return [
        priority,
        {
          total: matching.length,
          completed: matching.filter((task) => task.completed).length,
        },
      ];
    }),
  );
  return {
    date,
    totalTasks: tasks.length,
    completedTasks: completed.length,
    completionRate: tasks.length
      ? Math.round((completed.length / tasks.length) * 10000) / 100
      : 0,
    byPriority,
    completedList: completed.map(({ title, priority, completedAt }) => ({
      title,
      priority,
      completedAt,
    })),
    generatedAt: FieldValue.serverTimestamp(),
  };
}

async function processUser(
  uid: string,
  summaryDate: string,
  nextDate: string,
): Promise<void> {
  if (!uid || uid.length > 128 || uid.includes("/")) {
    throw new Error("Refusing to process an invalid Firebase Authentication UID.");
  }
  const tasksReference = db.collection("users").doc(uid).collection("tasks");
  const snapshot = await tasksReference.where("date", "==", summaryDate).get();
  const tasks = snapshot.docs.map((item) => toTask(item.data(), item.id));
  await db
    .collection("users")
    .doc(uid)
    .collection("summaries")
    .doc(summaryDate)
    .set(buildSummary(tasks, summaryDate));

  const writer = db.bulkWriter();
  for (const item of snapshot.docs) {
    const task = toTask(item.data(), item.id);
    if (!task.completed) {
      writer.update(item.ref, { date: nextDate });
      continue;
    }
    if (!archiveCompletedTasks.value()) continue;
    const archiveReference = db
      .collection("users")
      .doc(uid)
      .collection("taskArchive")
      .doc(item.id);
    writer.set(archiveReference, {
      ...item.data(),
      archivedAt: FieldValue.serverTimestamp(),
      sourceDate: summaryDate,
    });
    writer.delete(item.ref);
  }
  await writer.close();
}

export const generateNightlySummaries = onSchedule(
  {
    schedule: "5 0 * * *",
    timeZone: TIME_ZONE,
    region: "europe-west1",
    retryCount: 3,
    concurrency: 1,
    maxInstances: 1,
    timeoutSeconds: 540,
  },
  async () => {
    const nextDate = zonedDateKey(new Date());
    const summaryDate = previousDateKey(nextDate);
    let pageToken: string | undefined;
    do {
      const page = await getAuth().listUsers(500, pageToken);
      await Promise.all(
        page.users.map((user) => processUser(user.uid, summaryDate, nextDate)),
      );
      pageToken = page.pageToken;
    } while (pageToken);
  },
);
