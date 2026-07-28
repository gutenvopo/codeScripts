const TIME_ZONE = "Africa/Nairobi";

function timePart(
  parts: Intl.DateTimeFormatPart[],
  type: Intl.DateTimeFormatPartTypes,
): string {
  return parts.find((part) => part.type === type)?.value ?? "";
}

export function deadlineForDate(
  deadline: string | null,
  date: string,
): string | null {
  if (!deadline) return null;
  const parsed = new Date(deadline);
  if (Number.isNaN(parsed.getTime())) return deadline;
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(parsed);
  return `${date}T${timePart(parts, "hour")}:${timePart(parts, "minute")}:${timePart(parts, "second")}+03:00`;
}

export function wasLate(
  deadline: string | null,
  completed: boolean,
  completedAt: Date | null,
  dayEnd: Date,
): boolean {
  if (!deadline) return false;
  const dueAt = new Date(deadline);
  if (Number.isNaN(dueAt.getTime()) || dueAt.getTime() >= dayEnd.getTime()) {
    return false;
  }
  return !completed || completedAt === null || completedAt.getTime() > dueAt.getTime();
}

export function resetStepCompletion<T extends { completed?: unknown }>(
  steps: T[],
): Array<T & { completed: false }> {
  return steps.map((step) => ({ ...step, completed: false }));
}
