import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { Badge, PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2StudentDetail() {
  const { rollNo: id } = useParams({ strict: false });
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const response = await API.get(`/students/${id}/14-day-history/`);
        if (!cancelled) setData(response.data);
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.error || "Unable to load this student's record.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  if (loading) return <p>Loading…</p>;
  if (error || !data) return <p className="a2-note">{error || "Student not found."}</p>;

  const { student, period, records } = data;

  const presentDays = records.filter((r) => r.attendance_status === "PRESENT").length;
  const absentDays = records.filter((r) => r.attendance_status === "ABSENT").length;
  const totalXp = records.reduce((sum, r) => sum + (r.total_xp_earned || 0), 0);
  const homeworkCompleted = records.reduce((sum, r) => sum + (r.homework_completed || 0), 0);
  const homeworkPending = records.reduce((sum, r) => sum + (r.homework_pending || 0), 0);
  const attendancePct = presentDays + absentDays > 0
    ? Math.round((presentDays / (presentDays + absentDays)) * 100)
    : 0;

  const attendanceTone = (status) => {
    if (status === "PRESENT") return "green";
    if (status === "ABSENT") return "red";
    if (status === "HOLIDAY") return "gold";
    return "";
  };

  return (
    <>
      <PageHead title={student.name} subtitle={`Roll No ${student.roll_no}`}>
        <Link className="a2-button secondary" to="/admin2/students">Back to Students</Link>
      </PageHead>

      <section className="a2-panel a2-profile">
        <div>
          <h2>Student Profile</h2>
          <div className="a2-meta">
            <span><strong>Name:</strong> {student.name}</span>
            <span><strong>Roll No:</strong> {student.roll_no}</span>
            <span><strong>Class:</strong> {student.student_class}</span>
            <span><strong>Group:</strong> {student.group}</span>
            <span><strong>School:</strong> {student.school_name}</span>
          </div>
        </div>
      </section>

      <section className="a2-grid a2-detail-grid">
        <article className="a2-card"><span className="a2-label">Attendance</span><strong className="a2-stat">{attendancePct}%</strong><small>{presentDays} present · {absentDays} absent ({period.days} days)</small></article>
        <article className="a2-card violet"><span className="a2-label">XP earned (14 days)</span><strong className="a2-stat">{totalXp} XP</strong></article>
        <article className="a2-card gold"><span className="a2-label">Homework</span><strong className="a2-stat">{homeworkCompleted + homeworkPending}</strong><small>{homeworkCompleted} completed · {homeworkPending} pending</small></article>
      </section>

      <section className="a2-panel">
        <h3>Daily Record — {period.start_date} to {period.end_date}</h3>
        <div className="a2-table-wrap">
          <table className="a2-table">
            <thead>
              <tr><th>Date</th><th>Day</th><th>Attendance</th><th>Homework</th><th>XP</th></tr>
            </thead>
            <tbody>
              {records.map((row) => (
                <tr key={row.date}>
                  <td>{row.date}{row.is_today ? " (today)" : ""}</td>
                  <td>{row.day}</td>
                  <td><Badge tone={attendanceTone(row.attendance_status)}>{row.attendance_status}</Badge></td>
                  <td>{row.homework_total ? `${row.homework_completed}/${row.homework_total} done` : "—"}</td>
                  <td>{row.total_xp_earned}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
