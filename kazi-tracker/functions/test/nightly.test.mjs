import assert from "node:assert/strict";
import { describe, test } from "node:test";
import {
  deadlineForDate,
  resetStepCompletion,
  wasLate,
} from "../lib/nightly.js";

describe("recurring nightly behavior", () => {
  test("moves a deadline to the next Nairobi day without changing its time", () => {
    assert.equal(
      deadlineForDate("2026-07-04T18:30:00+03:00", "2026-07-05"),
      "2026-07-05T18:30:00+03:00",
    );
    assert.equal(deadlineForDate(null, "2026-07-05"), null);
  });

  test("reports incomplete and late-completed tasks as late", () => {
    const dayEnd = new Date("2026-07-05T00:00:00+03:00");
    const deadline = "2026-07-04T18:30:00+03:00";
    assert.equal(wasLate(deadline, false, null, dayEnd), true);
    assert.equal(
      wasLate(deadline, true, new Date("2026-07-04T18:31:00+03:00"), dayEnd),
      true,
    );
    assert.equal(
      wasLate(deadline, true, new Date("2026-07-04T18:29:00+03:00"), dayEnd),
      false,
    );
  });

  test("clears recurring task step completion without changing step data", () => {
    assert.deepEqual(
      resetStepCompletion([
        { id: "first", title: "First", completed: true },
        { id: "second", title: "Second", completed: false },
      ]),
      [
        { id: "first", title: "First", completed: false },
        { id: "second", title: "Second", completed: false },
      ],
    );
  });
});
