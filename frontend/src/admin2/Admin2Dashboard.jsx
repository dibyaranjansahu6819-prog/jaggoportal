import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2Dashboard() {
  const [data, setData] = useState(null);
  const [dayStatus, setDayStatus] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [dashboardRes, statusRes] = await Promise.all([
          API.get("/admin2/dashboard/"),
          API.get("/admin2/daily-status/"),
        ]);
        if (!cancelled) {
          setData(dashboardRes.data);
          setDayStatus(statusRes.data);
        }
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load the dashboard.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const stats = data ? [
    { label: "Students", value: data.students.total_registered, tone: "green" },
    { label: "Present Today", value: data.students.present_today, tone: "gold" },
    { label: "Volunteers", value: data.volunteers.registered, tone: "violet" },
    { label: "Assignments Today", value: data.assignments_today, tone: "green" },
    { label: "Active Cautions", value: data.active_cautions, tone: "red" },
    { label: "Pending Requests", value: data.pending_access_requests, tone: "gold" },
  ] : [];

  return <>
    {dayStatus && dayStatus.status && dayStatus.status !== "REGULAR_CLASS" && (
      <section className="a2-holiday" aria-label="School day status">
        <h2>{dayStatus.status === "HOLIDAY" ? "🏖 SCHOOL HOLIDAY" : "🏏 PLAYING DAY"}</h2>
        <p><strong>{String(dayStatus.date)}</strong></p>
        <p>Attendance, assignments, volunteer sessions, volunteer work, and homework are paused today. Management remains available.</p>
      </section>
    )}
    <PageHead title="Dashboard" subtitle={data ? `Today's school overview — ${String(data.date)}` : "Today's school overview"}><Link className="a2-button" to="/admin2/school-day-status">Update day status</Link></PageHead>
    {loading && <p>Loading…</p>}
    {error && <p className="a2-note">{error}</p>}
    {!loading && !error && (
      <section className="a2-grid a2-stats" aria-label="Dashboard totals">{stats.map(item => <article className={`a2-card a2-stat ${item.tone}`} key={item.label}><span>{item.label}</span><strong>{item.value}</strong></article>)}</section>
    )}
    <section className="a2-panel" style={{marginTop:18}}><h3>Management remains open</h3><p style={{margin:0,color:"var(--a2-muted)",lineHeight:1.65}}>Admin2 can continue managing students, volunteers, cautions, access requests, assignment history, and daily records throughout the holiday.</p></section>
  </>;
}
