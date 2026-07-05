import { useEffect, useState } from "react";
import { collection, limit, onSnapshot, orderBy, query } from "firebase/firestore";
import { motion } from "framer-motion";
import { CalendarDays, Check, ClipboardList } from "lucide-react";
import { db } from "../lib/firebase";
import type { DailySummary, Priority } from "../types/task";
import { PriorityBadge } from "../components/PriorityBadge";

function ProgressRing({ value }: { value: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  return (
    <div className="progress-ring">
      <svg viewBox="0 0 100 100" aria-label={`${value}% complete`}>
        <circle className="ring-track" cx="50" cy="50" r={radius} />
        <motion.circle
          className="ring-value"
          cx="50"
          cy="50"
          r={radius}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - value / 100) }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </svg>
      <strong>{Math.round(value)}%</strong>
    </div>
  );
}

function friendlyDate(date: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}

export function SummaryPage({ uid }: { uid: string }) {
  const [summaries, setSummaries] = useState<DailySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const summariesQuery = query(
      collection(db, "users", uid, "summaries"),
      orderBy("date", "desc"),
      limit(180),
    );
    return onSnapshot(
      summariesQuery,
      (snapshot) => {
        setSummaries(snapshot.docs.map((item) => item.data() as DailySummary));
        setLoading(false);
      },
      (caught) => {
        setError(caught.message);
        setLoading(false);
      },
    );
  }, [uid]);

  return (
    <main>
      <div className="summary-hero">
        <div>
          <span className="eyebrow">Daily telemetry</span>
          <h1>Your progress, in focus.</h1>
          <p>Each midnight snapshot turns effort into a pattern you can use.</p>
        </div>
        <div className="summary-orb"><ClipboardList size={36} /></div>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="summary-skeleton" />}
      {!loading && summaries.length === 0 && (
        <div className="summary-empty">
          <CalendarDays size={36} />
          <h2>No summaries yet</h2>
          <p>Your first daily report will appear after the nightly function runs.</p>
        </div>
      )}
      <div className="summary-list">
        {summaries.map((summary, index) => (
          <motion.article
            key={summary.date}
            className="summary-card"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06 }}
          >
            <div className="summary-top">
              <div>
                <span>{summary.date}</span>
                <h2>{friendlyDate(summary.date)}</h2>
                <p>{summary.completedTasks} of {summary.totalTasks} tasks completed</p>
              </div>
              <ProgressRing value={summary.completionRate} />
            </div>
            <div className="priority-stats">
              {(["high", "medium", "low"] as Priority[]).map((priority) => (
                <div key={priority}>
                  <PriorityBadge priority={priority} />
                  <strong>
                    {summary.byPriority[priority]?.completed ?? 0}
                    <span> / {summary.byPriority[priority]?.total ?? 0}</span>
                  </strong>
                </div>
              ))}
            </div>
            {summary.completedList.length > 0 && (
              <div className="completed-list">
                <h3>Completed</h3>
                {summary.completedList.map((task, taskIndex) => (
                  <div key={`${task.title}-${taskIndex}`}>
                    <Check size={14} />
                    <span>{task.title}</span>
                    <PriorityBadge priority={task.priority} />
                  </div>
                ))}
              </div>
            )}
          </motion.article>
        ))}
      </div>
    </main>
  );
}
