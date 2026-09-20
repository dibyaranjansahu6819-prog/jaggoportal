import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import JaagoBg from "../admin2/JaagoBg";
import "../signup/signup.css";
import "../auth/auth.css";
import API from "../services/api";

const PERFORMANCE_OPTIONS = [
  { value: "GOOD", label: "Good" },
  { value: "AVERAGE", label: "Average" },
  { value: "POOR", label: "Poor" },
];

export default function VolunteerTeaching() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);
  const [drafts, setDrafts] = useState({});

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/teachers/students/");
      setData(response.data);
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to load today's students.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const draftFor = (studentId, existing) =>
    drafts[studentId] || {
      performance: existing?.performance || "GOOD",
      feedback: existing?.feedback || "",
      homework_given: existing?.homework_given ?? true,
    };

  const updateDraft = (studentId, patch, existing) => {
    setDrafts((prev) => ({
      ...prev,
      [studentId]: { ...draftFor(studentId, existing), ...patch },
    }));
  };

  const save = async (studentId) => {
    const draft = draftFor(studentId, null);
    setSavingId(studentId);
    setError("");
    try {
      const response = await API.post("/teachers/progress/", {
        student: studentId,
        performance: draft.performance,
        feedback: draft.feedback,
        homework_given: draft.homework_given,
      });
      setData((prev) => ({
        ...prev,
        students: prev.students.map((row) =>
          row.student_id === studentId ? { ...row, progress: response.data.progress } : row,
        ),
      }));
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to save this student's progress.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="signup-page jaago-page auth-page">
      <img className="jaago-ornament jaago-ornament-gold" src="/jaago-bg-gold-motif.png" alt="" />
      <img className="jaago-ornament jaago-ornament-violet" src="/jaago-bg-violet-motif.png" alt="" />
      <img className="jaago-watermark" src="/jaago-bg-watermark.png" alt="" />

      <div className="signup-card auth-card" style={{ maxWidth: 720 }}>
        <div className="signup-header">
          <h1>Track Progress</h1>
          <p>Record each present student's performance for today's Teaching session.</p>
        </div>

        {loading ? <p>Loading…</p> : null}
        {error ? <p className="auth-message auth-error">{error}</p> : null}
        {!loading && data?.message ? <p className="auth-message">{data.message}</p> : null}

        {!loading && data?.students?.length ? (
          <div style={{ width: "100%", textAlign: "left" }}>
            {data.students.map((row) => {
              const draft = draftFor(row.student_id, row.progress);
              const saved = Boolean(row.progress);
              return (
                <div
                  key={row.student_id}
                  style={{
                    border: "1px solid var(--a2-border, #e3d8c5)",
                    borderRadius: 12,
                    padding: 14,
                    marginBottom: 14,
                  }}
                >
                  <p style={{ margin: "0 0 8px" }}>
                    <strong>{row.name}</strong> — {row.roll_no} ({row.class})
                    {saved ? <span className="auth-message auth-success" style={{ marginLeft: 8 }}>Saved</span> : null}
                  </p>

                  <div className="auth-field">
                    <label>Performance</label>
                    <select
                      value={draft.performance}
                      onChange={(e) => updateDraft(row.student_id, { performance: e.target.value }, row.progress)}
                    >
                      {PERFORMANCE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="auth-field">
                    <label>Feedback</label>
                    <input
                      type="text"
                      value={draft.feedback}
                      placeholder="Short note about today"
                      onChange={(e) => updateDraft(row.student_id, { feedback: e.target.value }, row.progress)}
                    />
                  </div>

                  <label style={{ display: "flex", alignItems: "center", gap: 8, margin: "8px 0" }}>
                    <input
                      type="checkbox"
                      checked={draft.homework_given}
                      onChange={(e) => updateDraft(row.student_id, { homework_given: e.target.checked }, row.progress)}
                    />
                    Homework given
                  </label>

                  <button
                    className="signup-button"
                    type="button"
                    disabled={savingId === row.student_id}
                    onClick={() => save(row.student_id)}
                  >
                    {savingId === row.student_id ? "Saving…" : saved ? "Update" : "Save"}
                  </button>
                </div>
              );
            })}
          </div>
        ) : null}

        <div className="auth-links">
          <Link to="/volunteer/dashboard">Back to dashboard</Link>
        </div>
      </div>
    </div>
  );
}
