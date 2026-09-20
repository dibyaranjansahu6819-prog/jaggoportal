import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import API from "../services/api";
import "./Admin1Attendance.css";
import JaagoBg from "../admin2/JaagoBg";

/**
 * Admin 1's own attendance record: today's summary
 * (GET /attendance/summary/) and every past session
 * (GET /attendance/history/) this Admin 1 account has run.
 */
export default function Admin1History() {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [summaryRes, historyRes] = await Promise.all([
          API.get("/attendance/summary/"),
          API.get("/attendance/history/"),
        ]);
        if (!cancelled) {
          setSummary(summaryRes.data);
          setHistory(historyRes.data.sessions || []);
        }
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.error || "Unable to load attendance history.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const presentStudents = summary?.students?.filter((s) => s.status === "PRESENT").length ?? 0;
  const presentVolunteers = summary?.volunteers?.filter((v) => v.status === "PRESENT").length ?? 0;

  return (
    <div className="admin-attendance-page">
      <JaagoBg />

      <div className="toolkit-header">
        <img className="toolkit-logo" src="/jaago-attendance-logo.jpeg" alt="Jaago" />
        <div className="toolkit-brand">
          <p className="toolkit-eyebrow">Admin 1</p>
          <h1 className="toolkit-title">Attendance History</h1>
        </div>
        <div className="toolkit-session">
          <Link to="/admin1/attendance-dashboard" className="end-session-btn">Back to today</Link>
        </div>
      </div>

      {loading ? <p className="toolkit-loading">Loading…</p> : null}
      {error ? <p className="toolkit-message">{error}</p> : null}

      {!loading && summary?.holiday ? (
        <div className="toolkit-panel">
          <p>Today is a holiday — {summary.holiday.name} ({String(summary.holiday.date)}).</p>
        </div>
      ) : null}

      {!loading && !summary?.holiday ? (
        <section className="toolkit-panel">
          <div className="panel-header">
            <span className="panel-kicker">Today</span>
          </div>
          {summary?.session ? (
            <p style={{ padding: "0 4px" }}>
              Session {summary.session.session_date} — {summary.session.is_active ? "active" : "closed"} ·{" "}
              {presentStudents} student(s) present · {presentVolunteers} volunteer(s) present
            </p>
          ) : (
            <p style={{ padding: "0 4px" }}>No attendance session has been started today yet.</p>
          )}
        </section>
      ) : null}

      <section className="toolkit-panel" style={{ marginTop: 16 }}>
        <div className="panel-header">
          <span className="panel-kicker">Past Sessions</span>
          <span className="panel-count">{history.length}</span>
        </div>
        <div className="attendance-list">
          {history.length === 0 && !loading ? (
            <div className="list-empty">No past sessions yet.</div>
          ) : (
            history.map((session) => (
              <div className="attendance-row" key={session.id}>
                <div className="person-info">
                  <strong>{String(session.session_date)}</strong>
                  <span>
                    {session.started_at ? new Date(session.started_at).toLocaleTimeString() : "—"}
                    {session.ended_at ? ` – ${new Date(session.ended_at).toLocaleTimeString()}` : ""}
                  </span>
                </div>
                <span className={`source-pill ${session.is_active ? "source-assigned" : "source-special"}`}>
                  {session.is_active ? "Active" : session.has_expired ? "Expired" : "Closed"}
                </span>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
