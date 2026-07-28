const STORAGE_KEY = "kazi-tracker:error-log:v1";
const MAX_ENTRIES = 200;
const MAX_FIELD_LENGTH = 20_000;
const REDACTED = "[redacted]";

export interface AppErrorEntry {
  id: string;
  timestamp: string;
  source: string;
  name: string;
  message: string;
  route: string;
  stack: string | null;
  details: string | null;
}

type ErrorLogListener = () => void;

let entries: AppErrorEntry[] = loadEntries();
const listeners = new Set<ErrorLogListener>();
let captureInstalled = false;

function scrub(text: string): string {
  return text
    .replace(
      /(["']?(?:password|token|accessToken|refreshToken|apiKey|authorization)["']?\s*[:=]\s*["']?)[^"',}\s&]+/gi,
      `$1${REDACTED}`,
    )
    .replace(
      /([?&](?:token|key|api_key|access_token|refresh_token|auth)=)[^&\s]+/gi,
      `$1${REDACTED}`,
    )
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, `Bearer ${REDACTED}`)
    .slice(0, MAX_FIELD_LENGTH);
}

function isSensitiveKey(key: string): boolean {
  return /password|token|secret|api.?key|authorization|credential/i.test(key);
}

function objectProperties(value: object): Record<string, unknown> {
  const properties: Record<string, unknown> = {};
  let ownKeys: string[] = [];
  try {
    ownKeys = Object.getOwnPropertyNames(value);
  } catch {
    return { value: "[Unable to inspect object properties]" };
  }
  const keys = new Set([
    ...ownKeys,
    "name",
    "message",
    "stack",
    "code",
  ]);
  for (const key of keys) {
    try {
      if (key in value) {
        properties[key] = (value as Record<string, unknown>)[key];
      }
    } catch {
      properties[key] = "[Unable to read property]";
    }
  }
  return properties;
}

function serialize(value: unknown): string {
  if (typeof value === "string") return scrub(value);
  if (value instanceof Error) {
    return scrub(value.stack || `${value.name}: ${value.message}`);
  }

  const seen = new WeakSet<object>();
  try {
    const serializable = value && typeof value === "object" && !Array.isArray(value)
      ? objectProperties(value)
      : value;
    const serialized = JSON.stringify(
      serializable,
      (key, item: unknown) => {
        if (isSensitiveKey(key)) return REDACTED;
        if (typeof item === "bigint") return item.toString();
        if (typeof item === "object" && item !== null) {
          if (seen.has(item)) return "[circular]";
          seen.add(item);
        }
        if (item instanceof Error) {
          return {
            name: item.name,
            message: item.message,
            stack: item.stack,
          };
        }
        return item;
      },
      2,
    );
    return scrub(serialized ?? String(value));
  } catch {
    return scrub(String(value));
  }
}

function isErrorEntry(value: unknown): value is AppErrorEntry {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AppErrorEntry>;
  return (
    typeof candidate.id === "string"
    && typeof candidate.timestamp === "string"
    && typeof candidate.source === "string"
    && typeof candidate.name === "string"
    && typeof candidate.message === "string"
    && typeof candidate.route === "string"
    && (candidate.stack === null || typeof candidate.stack === "string")
    && (candidate.details === null || typeof candidate.details === "string")
  );
}

function loadEntries(): AppErrorEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const stored: unknown = JSON.parse(
      window.localStorage.getItem(STORAGE_KEY) ?? "[]",
    );
    return Array.isArray(stored)
      ? stored.filter(isErrorEntry).slice(0, MAX_ENTRIES)
      : [];
  } catch {
    return [];
  }
}

function saveEntries(): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // Runtime capture remains available when browser storage is blocked or full.
  }
}

function notify(): void {
  listeners.forEach((listener) => listener());
}

function currentRoute(): string {
  return typeof window === "undefined" ? "unknown" : window.location.pathname;
}

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function normalizedError(caught: unknown): {
  name: string;
  message: string;
  stack: string | null;
} {
  if (caught instanceof Error) {
    return {
      name: caught.name || "Error",
      message: scrub(caught.message || "No error message was provided."),
      stack: caught.stack ? scrub(caught.stack) : null,
    };
  }
  if (caught && typeof caught === "object") {
    const properties = objectProperties(caught);
    return {
      name: typeof properties.name === "string" && properties.name
        ? scrub(properties.name)
        : "NonErrorException",
      message: typeof properties.message === "string" && properties.message
        ? scrub(properties.message)
        : "A non-Error object was thrown.",
      stack: typeof properties.stack === "string" && properties.stack
        ? scrub(properties.stack)
        : null,
    };
  }
  return {
    name: typeof caught,
    message: serialize(caught),
    stack: null,
  };
}

function implicitDetails(caught: unknown): Record<string, unknown> | null {
  if (!caught || typeof caught !== "object") return null;
  const properties = objectProperties(caught);
  delete properties.name;
  delete properties.message;
  delete properties.stack;
  return Object.keys(properties).length > 0 ? properties : null;
}

function isRecentDuplicate(candidate: AppErrorEntry): boolean {
  const latest = entries[0];
  if (!latest) return false;
  return (
    latest.name === candidate.name
    && latest.message === candidate.message
    && latest.stack === candidate.stack
    && Date.parse(candidate.timestamp) - Date.parse(latest.timestamp) < 1_500
  );
}

export function reportAppError(
  caught: unknown,
  source: string,
  details?: unknown,
): AppErrorEntry {
  const normalized = normalizedError(caught);
  const diagnosticDetails = details === undefined
    ? implicitDetails(caught)
    : details;
  const entry: AppErrorEntry = {
    id: createId(),
    timestamp: new Date().toISOString(),
    source: scrub(source),
    name: normalized.name,
    message: normalized.message,
    route: scrub(currentRoute()),
    stack: normalized.stack,
    details: diagnosticDetails === null || diagnosticDetails === undefined
      ? null
      : serialize(diagnosticDetails),
  };
  if (isRecentDuplicate(entry)) return entries[0];
  entries = [entry, ...entries].slice(0, MAX_ENTRIES);
  saveEntries();
  notify();
  return entry;
}

export function getErrorLogSnapshot(): AppErrorEntry[] {
  return entries;
}

export function subscribeToErrorLog(listener: ErrorLogListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function clearErrorLog(): void {
  entries = [];
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // The in-memory log is still cleared when browser storage is unavailable.
  }
  notify();
}

function resourceDetails(target: EventTarget | null): Record<string, string> | null {
  if (target instanceof HTMLScriptElement) {
    return { element: "script", url: target.src };
  }
  if (target instanceof HTMLLinkElement) {
    return { element: "link", url: target.href };
  }
  if (target instanceof HTMLImageElement) {
    return { element: "image", url: target.src };
  }
  return null;
}

export function installGlobalErrorCapture(): void {
  if (captureInstalled || typeof window === "undefined") return;
  captureInstalled = true;

  window.addEventListener(
    "error",
    (event: Event) => {
      if (event instanceof ErrorEvent) {
        reportAppError(event.error ?? event.message, "Window error", {
          filename: event.filename,
          line: event.lineno,
          column: event.colno,
        });
        return;
      }
      const resource = resourceDetails(event.target);
      if (resource) {
        reportAppError(
          new Error(`Failed to load ${resource.element} resource.`),
          "Resource load",
          resource,
        );
      }
    },
    true,
  );

  window.addEventListener("unhandledrejection", (event) => {
    reportAppError(event.reason, "Unhandled promise rejection");
  });

  const originalConsoleError = console.error.bind(console);
  console.error = (...values: unknown[]): void => {
    originalConsoleError(...values);
    const primary = values.find((value) => value instanceof Error) ?? values[0];
    reportAppError(primary ?? "console.error called without arguments", "Console", values);
  };

  window.addEventListener("storage", (event) => {
    if (event.key !== STORAGE_KEY) return;
    entries = loadEntries();
    notify();
  });
}
