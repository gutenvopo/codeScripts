import { readFile } from "node:fs/promises";
import { after, before, beforeEach, describe, test } from "node:test";
import assert from "node:assert/strict";
import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
} from "@firebase/rules-unit-testing";
import {
  Timestamp,
  collection,
  doc,
  getDoc,
  getDocs,
  limit,
  query,
  setDoc,
} from "firebase/firestore";

const projectId = "kazi-tracker-data";
const aliceUid = "alice";
const bobUid = "bob";
let testEnvironment;

function taskData(id, overrides = {}) {
  return {
    id,
    title: "A valid task",
    priority: "high",
    deadline: "2026-07-04T23:59:00+03:00",
    order: 0,
    completed: false,
    completedAt: null,
    createdAt: Timestamp.now(),
    date: "2026-07-04",
    parentId: null,
    recurring: false,
    steps: [],
    ...overrides,
  };
}

before(async () => {
  testEnvironment = await initializeTestEnvironment({
    projectId,
    firestore: {
      rules: await readFile(new URL("../firestore.rules", import.meta.url), "utf8"),
    },
  });
});

beforeEach(async () => {
  await testEnvironment.clearFirestore();
  await testEnvironment.withSecurityRulesDisabled(async (context) => {
    await setDoc(
      doc(context.firestore(), "users", bobUid, "tasks", "bob-task"),
      taskData("bob-task"),
    );
    await setDoc(
      doc(context.firestore(), "users", aliceUid, "summaries", "2026-07-03"),
      { date: "2026-07-03" },
    );
  });
});

after(async () => {
  await testEnvironment.cleanup();
});

describe("owner isolation", () => {
  test("an authenticated user can create, query, and read valid own tasks", async () => {
    const db = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertSucceeds(
      setDoc(doc(db, "users", aliceUid, "tasks", "alice-task"), taskData("alice-task")),
    );
    await assertSucceeds(
      getDocs(query(collection(db, "users", aliceUid, "tasks"), limit(100))),
    );
    const snapshot = await assertSucceeds(
      getDoc(doc(db, "users", aliceUid, "tasks", "alice-task")),
    );
    assert.equal(snapshot.data()?.title, "A valid task");
  });

  test("user A cannot read or write user B documents", async () => {
    const aliceDb = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertFails(
      getDoc(doc(aliceDb, "users", bobUid, "tasks", "bob-task")),
    );
    await assertFails(
      setDoc(
        doc(aliceDb, "users", bobUid, "tasks", "injected"),
        taskData("injected"),
      ),
    );
  });

  test("unauthenticated clients cannot read or write user documents", async () => {
    const db = testEnvironment.unauthenticatedContext().firestore();
    await assertFails(getDoc(doc(db, "users", bobUid, "tasks", "bob-task")));
    await assertFails(
      setDoc(doc(db, "users", aliceUid, "tasks", "anonymous"), taskData("anonymous")),
    );
  });
});

describe("schema validation and server-owned data", () => {
  test("invalid priorities, oversized titles, and unexpected fields are rejected", async () => {
    const db = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "oversized"),
        taskData("oversized", { title: "x".repeat(501) }),
      ),
    );
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "bad-priority"),
        taskData("bad-priority", { priority: "urgent" }),
      ),
    );
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "extra-field"),
        taskData("extra-field", { secret: "not allowed" }),
      ),
    );
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "bad-recurring"),
        taskData("bad-recurring", { recurring: "daily" }),
      ),
    );
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "bad-steps"),
        taskData("bad-steps", { steps: "not-a-list" }),
      ),
    );
  });

  test("recurring is persisted as a boolean while legacy tasks remain valid", async () => {
    const db = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertSucceeds(
      setDoc(
        doc(db, "users", aliceUid, "tasks", "recurring"),
        taskData("recurring", { recurring: true }),
      ),
    );
    const legacy = taskData("legacy");
    delete legacy.recurring;
    delete legacy.steps;
    await assertSucceeds(
      setDoc(doc(db, "users", aliceUid, "tasks", "legacy"), legacy),
    );
  });

  test("task collection queries must have a bounded limit", async () => {
    const db = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertFails(getDocs(collection(db, "users", aliceUid, "tasks")));
    await assertFails(
      getDocs(query(collection(db, "users", aliceUid, "tasks"), limit(501))),
    );
  });

  test("owners can read but cannot forge generated summaries", async () => {
    const db = testEnvironment.authenticatedContext(aliceUid).firestore();
    await assertSucceeds(
      getDoc(doc(db, "users", aliceUid, "summaries", "2026-07-03")),
    );
    await assertFails(
      setDoc(
        doc(db, "users", aliceUid, "summaries", "2026-07-04"),
        { date: "2026-07-04" },
      ),
    );
  });
});
