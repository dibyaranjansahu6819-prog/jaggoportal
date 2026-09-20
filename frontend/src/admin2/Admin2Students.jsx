import { useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2Students() {
  const [search, setSearch] = useState("");
  const [className, setClassName] = useState("All");
  const [presentOnly, setPresentOnly] = useState(false);
  const [students, setStudents] = useState([]);
  const [presentIds, setPresentIds] = useState(null);
  const [presentDate, setPresentDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [presentLoading, setPresentLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await API.get("/admin2/students/total/");
        if (!cancelled) setStudents(response.data.students || []);
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load students.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const togglePresentOnly = async () => {
    const next = !presentOnly;
    setPresentOnly(next);
    if (next && presentIds === null) {
      setPresentLoading(true);
      try {
        const response = await API.get("/admin2/students/present-today/");
        setPresentIds(new Set((response.data.students || []).map((s) => s.id)));
        setPresentDate(response.data.date);
      } catch (err) {
        setError(err?.response?.data?.detail || "Unable to load today's present students.");
        setPresentOnly(false);
      } finally {
        setPresentLoading(false);
      }
    }
  };

  const classOptions = useMemo(
    () => Array.from(new Set(students.map((s) => s.student_class))).sort(),
    [students],
  );

  const shown = students.filter((s) =>
    `${s.roll_no} ${s.name}`.toLowerCase().includes(search.toLowerCase())
    && (className === "All" || s.student_class === className)
    && (!presentOnly || (presentIds && presentIds.has(s.id))));

  return (
    <>
      <PageHead title="Students" subtitle="Search and review student records" />
      <section className="a2-panel">
        <div className="a2-filters">
          <input
            aria-label="Search students"
            placeholder="Search name or roll number"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            aria-label="Filter by class"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
          >
            <option value="All">All Classes</option>
            {classOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <button
            type="button"
            className={`a2-button small ${presentOnly ? "" : "secondary"}`}
            onClick={togglePresentOnly}
            disabled={presentLoading}
          >
            {presentLoading ? "Loading…" : presentOnly ? "Present Today ✓" : "Present Today"}
          </button>
        </div>
        {presentOnly && presentDate ? (
          <p className="a2-note" style={{ marginTop: 0 }}>Showing students marked present on {String(presentDate)}.</p>
        ) : null}
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && !error && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead>
                <tr>
                  <th>Roll No</th><th>Name</th><th>Class</th><th>School</th><th>Registered</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((s) => (
                  <tr className="clickable" key={s.id}>
                    <td><Link className="a2-link" to={`/admin2/students/${s.id}`}>{s.roll_no}</Link></td>
                    <td><Link className="a2-link" to={`/admin2/students/${s.id}`}>{s.name}</Link></td>
                    <td>{s.student_class}</td>
                    <td>{s.school_name}</td>
                    <td>{s.created_at ? String(s.created_at).slice(0, 10) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !error && !shown.length && <div className="a2-empty">No students match these filters.</div>}
      </section>
    </>
  );
}
