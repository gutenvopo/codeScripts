/* global AbortSignal, console, fetch, process */

import admin from "firebase-admin";
import { load } from "cheerio";

const SOURCE_URL =
  "https://docs.google.com/document/d/e/2PACX-1vRDIPVHVZTjCvN-LTEN7AE5-zBmrGMOrJLi1l_czN3cJ67o_hK6sfE-XzLarF_0EIY0PP5kN4YXkNFr/pub";
const TARGET_EMAIL = "kirwaboit@gmail.com";
const TIME_ZONE = "Africa/Nairobi";
const MAX_BATCH_SIZE = 500;
const PRIORITIES = ["high", "medium", "low"] as const;

type Priority = (typeof PRIORITIES)[number];

interface ParsedTask {
  title: string;
  priority: Priority;
  deadline: string;
  order: number;
  parentIndex: number | null;
}

interface DeadlineResult {
  deadline: string;
  ambiguous: boolean;
}

const ignoredText = new Set([
  "published using google docs",
  "report abuse",
  "updated automatically every 5 minutes",
  "task app updater",
]);

function parseArguments(): { force: boolean } {
  const argumentsList = process.argv.slice(2);
  const unknown = argumentsList.filter((argument) => argument !== "--force");
  if (unknown.length > 0) {
    throw new Error(`Unknown argument(s): ${unknown.join(", ")}. Only --force is supported.`);
  }
  return { force: argumentsList.includes("--force") };
}

function nairobiDateKey(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const value = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((part) => part.type === type)?.value ?? "";
  return `${value("year")}-${value("month")}-${value("day")}`;
}

function parseDeadline(title: string, date: string): DeadlineResult {
  const clockPattern = /(\d{1,2})(?::([0-5]\d))?\s*([ap])\.?m\.?/gi;
  const matches = [...title.matchAll(clockPattern)];
  const valid = matches.filter((match) => {
    const hour = Number(match[1]);
    return hour >= 1 && hour <= 12;
  });

  if (valid.length === 0) {
    return {
      deadline: `${date}T23:59:00+03:00`,
      ambiguous: matches.length > 0,
    };
  }

  const first = valid[0];
  const twelveHour = Number(first[1]);
  const minutes = Number(first[2] ?? "0");
  const isPm = first[3].toLowerCase() === "p";
  const hour = (twelveHour % 12) + (isPm ? 12 : 0);
  return {
    deadline: `${date}T${String(hour).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:00+03:00`,
    ambiguous: matches.length > 1,
  };
}

function priorityFrom(text: string): Priority | null {
  const candidate = text.toLowerCase();
  return PRIORITIES.find((priority) => priority === candidate) ?? null;
}

function parseTasks(html: string, date: string): ParsedTask[] {
  const $ = load(html);
  const tasks: ParsedTask[] = [];
  const orders: Record<Priority, number> = { high: 0, medium: 0, low: 0 };
  const foundPriorities = new Set<Priority>();
  let currentPriority: Priority | null = null;
  let currentParentIndex: number | null = null;

  $(".doc-content li, #contents li").each((_index, element) => {
    const item = $(element);
    const ownItem = item.clone();
    ownItem.children("ul, ol").remove();
    const text = ownItem.text().replaceAll("\u00a0", " ").trim();
    if (!text || ignoredText.has(text.toLowerCase())) return;

    const nestedDepth = item.parents("ul, ol").length;
    const listClass = item.parent("ul, ol").attr("class") ?? "";
    const googleLevel = Number(listClass.match(/\blst-kix_\S+-(\d+)\b/)?.[1] ?? -1) + 1;
    const depth = Math.max(nestedDepth, googleLevel);
    const heading = depth === 1 ? priorityFrom(text) : null;
    if (heading) {
      currentPriority = heading;
      currentParentIndex = null;
      foundPriorities.add(heading);
      return;
    }
    if (depth === 1) return;
    if (!currentPriority) {
      throw new Error(`Task appeared before a priority heading: "${text}"`);
    }

    if (depth === 2) {
      currentParentIndex = tasks.length;
    } else if (currentParentIndex === null) {
      throw new Error(`Child task has no parent: "${text}"`);
    }

    tasks.push({
      title: text,
      priority: currentPriority,
      deadline: parseDeadline(text, date).deadline,
      order: orders[currentPriority]++,
      parentIndex: depth === 2 ? null : currentParentIndex,
    });
  });

  if (foundPriorities.size !== PRIORITIES.length || tasks.length === 0) {
    throw new Error("The Google Doc did not contain the expected High, Medium, and Low task lists.");
  }
  return tasks;
}

async function fetchSource(): Promise<string> {
  const response = await fetch(SOURCE_URL, {
    signal: AbortSignal.timeout(30_000),
    headers: { "user-agent": "KaziTrackerOneTimeImporter/1.0" },
  });
  if (!response.ok) {
    throw new Error(`Google Doc request failed with HTTP ${response.status}.`);
  }
  return response.text();
}

function initializeAdmin(): void {
  if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    throw new Error("GOOGLE_APPLICATION_CREDENTIALS must point to a service account JSON key.");
  }
  if (admin.apps.length === 0) {
    admin.initializeApp({ credential: admin.credential.applicationDefault() });
  }
}

async function resolveTargetUser(): Promise<admin.auth.UserRecord> {
  let user: admin.auth.UserRecord;
  try {
    user = await admin.auth().getUserByEmail(TARGET_EMAIL);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Could not resolve the required account ${TARGET_EMAIL}: ${detail}`);
  }
  if (user.email?.toLowerCase() !== TARGET_EMAIL.toLowerCase()) {
    throw new Error(`Resolved account email did not match ${TARGET_EMAIL}; aborting.`);
  }
  return user;
}

async function guardAgainstDuplicate(
  tasksReference: admin.firestore.CollectionReference,
  date: string,
  force: boolean,
): Promise<void> {
  const existing = await tasksReference.where("date", "==", date).limit(1).get();
  if (existing.empty) return;

  const warning = `WARNING: ${TARGET_EMAIL} already has tasks dated ${date}.`;
  if (!force) {
    throw new Error(`${warning} Re-run with --force only if duplicate import is intentional.`);
  }
  console.warn(`${warning} --force was supplied; importing additional tasks.`);
}

async function writeTasks(
  tasksReference: admin.firestore.CollectionReference,
  tasks: ParsedTask[],
  date: string,
): Promise<void> {
  const references = tasks.map(() => tasksReference.doc());
  for (let start = 0; start < tasks.length; start += MAX_BATCH_SIZE) {
    const batch = admin.firestore().batch();
    tasks.slice(start, start + MAX_BATCH_SIZE).forEach((task, offset) => {
      const index = start + offset;
      const reference = references[index];
      batch.set(reference, {
        id: reference.id,
        title: task.title,
        priority: task.priority,
        deadline: task.deadline,
        order: task.order,
        completed: false,
        completedAt: null,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        date,
        parentId: task.parentIndex === null ? null : references[task.parentIndex].id,
      });
    });
    await batch.commit();
  }
}

function printSummary(tasks: ParsedTask[], date: string): void {
  const counts = Object.fromEntries(
    PRIORITIES.map((priority) => [
      priority,
      tasks.filter((task) => task.priority === priority).length,
    ]),
  );
  const parentCount = tasks.filter((task) => task.parentIndex === null).length;
  const ambiguous = tasks
    .filter((task) => parseDeadline(task.title, date).ambiguous)
    .map((task) => task.title);

  console.log(`Imported ${tasks.length} tasks for ${date}.`);
  console.log(`Priority counts: high=${counts.high}, medium=${counts.medium}, low=${counts.low}`);
  console.log(`Task levels: parents=${parentCount}, children=${tasks.length - parentCount}`);
  console.log(
    ambiguous.length > 0
      ? `Ambiguous time parsing (${ambiguous.length}):\n- ${ambiguous.join("\n- ")}`
      : "Ambiguous time parsing: none",
  );
}

async function main(): Promise<void> {
  const { force } = parseArguments();
  initializeAdmin();
  const user = await resolveTargetUser();
  console.log(`Importing to ${TARGET_EMAIL} (uid: ${user.uid})`);

  const date = nairobiDateKey();
  const tasksReference = admin.firestore().collection("users").doc(user.uid).collection("tasks");
  if (tasksReference.path !== `users/${user.uid}/tasks`) {
    throw new Error("Refusing to write outside the resolved target user's task collection.");
  }

  const html = await fetchSource();
  const tasks = parseTasks(html, date);
  await guardAgainstDuplicate(tasksReference, date, force);
  await writeTasks(tasksReference, tasks, date);
  printSummary(tasks, date);
}

main().catch((error: unknown) => {
  const detail = error instanceof Error ? error.message : String(error);
  console.error(`Import aborted: ${detail}`);
  process.exitCode = 1;
});
