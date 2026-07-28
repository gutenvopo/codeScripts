import { useState, useSyncExternalStore } from "react";
import {
  AlertTriangle,
  Check,
  Clipboard,
  Clock3,
  Eraser,
  FileWarning,
  MapPin,
} from "lucide-react";
import {
  clearErrorLog,
  getErrorLogSnapshot,
  reportAppError,
  subscribeToErrorLog,
  type AppErrorEntry,
} from "../lib/errorLog";

function formatTimestamp(timestamp: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(timestamp));
}

export function ErrorLogPage() {
  const entries = useSyncExternalStore(
    subscribeToErrorLog,
    getErrorLogSnapshot,
    getErrorLogSnapshot,
  );
  const [copied, setCopied] = useState(false);
  const [copiedEntryId, setCopiedEntryId] = useState<string | null>(null);

  async function copyLog(): Promise<void> {
    try {
      await navigator.clipboard.writeText(JSON.stringify(entries, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch (caught) {
      reportAppError(caught, "Error Log copy");
    }
  }

  async function copyEntry(entry: AppErrorEntry): Promise<void> {
    try {
      await navigator.clipboard.writeText(JSON.stringify(entry, null, 2));
      setCopiedEntryId(entry.id);
      window.setTimeout(() => {
        setCopiedEntryId((current) => current === entry.id ? null : current);
      }, 1800);
    } catch (caught) {
      reportAppError(caught, "Error Log entry copy", {
        entryId: entry.id,
      });
    }
  }

  return (
    <main className="error-log-page">
      <div className="error-log-hero">
        <div>
          <span className="eyebrow">Local diagnostics</span>
          <h1>Error Log</h1>
          <p>
            Verbose browser and application failures captured on this device.
            Sensitive credential fields are redacted automatically.
          </p>
        </div>
        <div className="error-log-actions">
          <button
            type="button"
            className="ghost-button"
            onClick={() => void copyLog()}
            disabled={entries.length === 0}
          >
            {copied ? <Check size={16} /> : <Clipboard size={16} />}
            {copied ? "Copied" : "Copy log"}
          </button>
          <button
            type="button"
            className="danger-button"
            onClick={clearErrorLog}
            disabled={entries.length === 0}
          >
            <Eraser size={16} />
            Clear log
          </button>
        </div>
      </div>

      <section className="error-log-summary" aria-label="Error log summary">
        <div className="error-log-summary-icon">
          <FileWarning size={21} />
        </div>
        <div>
          <strong>{entries.length}</strong>
          <span>{entries.length === 1 ? "captured error" : "captured errors"}</span>
        </div>
        <p>
          The newest entries appear first. Up to 200 entries remain in this
          browser until you clear them.
        </p>
      </section>

      {entries.length === 0 ? (
        <section className="error-log-empty">
          <Check size={28} />
          <h2>No errors captured</h2>
          <p>New application failures will appear here automatically.</p>
        </section>
      ) : (
        <div className="error-log-list">
          {entries.map((entry, index) => (
            <article className="error-log-entry" key={entry.id}>
              <header>
                <div className="error-log-entry-index">
                  <AlertTriangle size={17} />
                  <span>#{entries.length - index}</span>
                </div>
                <div className="error-log-entry-heading">
                  <span>{entry.source}</span>
                  <h2>{entry.name}</h2>
                </div>
                <div className="error-log-entry-meta">
                  <time dateTime={entry.timestamp}>
                    <Clock3 size={14} />
                    {formatTimestamp(entry.timestamp)}
                  </time>
                  <button
                    type="button"
                    className="error-log-entry-copy"
                    onClick={() => void copyEntry(entry)}
                    aria-label={`Copy entry ${entries.length - index}`}
                  >
                    {copiedEntryId === entry.id
                      ? <Check size={14} />
                      : <Clipboard size={14} />}
                    {copiedEntryId === entry.id ? "Copied" : "Copy entry"}
                  </button>
                </div>
              </header>
              <p className="error-log-message">{entry.message}</p>
              <div className="error-log-route">
                <MapPin size={14} />
                Route: <code>{entry.route}</code>
              </div>
              {entry.stack && (
                <section className="error-log-detail">
                  <h3>Stack trace</h3>
                  <pre>{entry.stack}</pre>
                </section>
              )}
              {entry.details && (
                <section className="error-log-detail">
                  <h3>Diagnostic details</h3>
                  <pre>{entry.details}</pre>
                </section>
              )}
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
