import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2Overview() {
  const [open, setOpen] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await API.get("/admin2/dashboard/");
        if (!cancelled) setData(response.data);
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load the overview.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const toggle = (card) => setOpen((current) => (current === card ? null : card));

  if (loading) return <p>Loading…</p>;
  if (error || !data) return <p className="a2-note">{error || "Overview unavailable."}</p>;

  const studentsRegistered = data.students.total_registered;
  const presentToday = data.students.present_today;
  const absentToday = Math.max(studentsRegistered - presentToday, 0);
  const volunteersRegistered = data.volunteers.registered;
  const assignedToday = data.assignments_today;

  return (
    <>
      <PageHead title="Admin 2 Overview" subtitle="Registered students and volunteers at a glance" />

      <div className="a2-flashcards">
        <button type="button" className={`a2-flashcard green ${open === "students" ? "active" : ""}`} onClick={() => toggle("students")}>
          <span className="a2-flash-icon">🎓</span>
          <div className="a2-flash-text"><h3>Students</h3><p><strong>{studentsRegistered}</strong> registered</p></div>
        </button>

        <button type="button" className={`a2-flashcard gold ${open === "volunteers" ? "active" : ""}`} onClick={() => toggle("volunteers")}>
          <span className="a2-flash-icon">🧑‍🏫</span>
          <div className="a2-flash-text"><h3>Volunteers</h3><p><strong>{volunteersRegistered}</strong> registered</p></div>
        </button>
      </div>

      {open === "students" && (
        <section className="a2-panel a2-overview-panel">
          <div className="a2-overview-head"><h3>Students Overview</h3><button type="button" className="a2-overview-close" onClick={() => setOpen(null)}>×</button></div>
          <div className="a2-overview-stats">
            <div className="a2-stat"><strong>{studentsRegistered}</strong><span>Registered</span></div>
            <div className="a2-stat"><strong className="a2-green-num">{presentToday}</strong><span>Present Today</span></div>
            <div className="a2-stat"><strong className="a2-red-num">{absentToday}</strong><span>Absent Today</span></div>
          </div>
          <Link to="/admin2/students" className="a2-button small">View Full →</Link>
        </section>
      )}

      {open === "volunteers" && (
        <section className="a2-panel a2-overview-panel">
          <div className="a2-overview-head"><h3>Volunteers Overview</h3><button type="button" className="a2-overview-close" onClick={() => setOpen(null)}>×</button></div>
          <div className="a2-overview-stats">
            <div className="a2-stat"><strong>{volunteersRegistered}</strong><span>Registered</span></div>
            <div className="a2-stat"><strong className="a2-green-num">{assignedToday}</strong><span>Assigned Today</span></div>
          </div>
          <Link to="/admin2/volunteers" className="a2-button small">View Full →</Link>
        </section>
      )}
    </>
  );
}
