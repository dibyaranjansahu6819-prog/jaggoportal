import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import "../signup/signup.css";
import "../auth/auth.css";
import API from "../services/api";

export default function VolunteerChecking() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);
  const [drafts, setDrafts] = useState({});

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/teachers/checking/");
      setData(response.data);
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to load today's checking list.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const draftFor = (studentId, existing) =>
    drafts[studentId] || {
      homework_status: existing?.homework_status || "DONE",
      feedback: existing?.feedback || "",
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
      const response = await API.post(`/teachers/checking/students/${studentId}/save/`, {
        homework_status: draft.homework_status,
        feedback: draft.feedback,
      });
      setData((prev) => ({
        ...prev,
        students: prev.students.map((row) =>
          row.student === studentId ? { ...row, checked: true, checking: response.data.checking } : row,
        ),
        students_checked: prev.students.some((row) => row.student === studentId && row.checked)
          ? prev.students_checked
          : prev.students_checked + 1,
        students_pending: prev.students.some((row) => row.student === studentId && row.checked)
          ? prev.students_pending
          : prev.students_pending - 1,
      }));
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to save this student's checking.");
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
          <h1>Homework Checking</h1>
          <p>Mark today's homework as done or not done for each present student.</p>
        </div>

        {loading ? <p>Loading…</p> : null}
        {error ? <p className="auth-message auth-error">{error}</p> : null}

        {!loading && data ? (
          <p style={{ width: "100%" }}>
            <strong>{data.students_checked}</strong> checked · <strong>{data.students_pending}</strong> pending of {data.students_present} present
          </p>
        ) : null}

        {!loading && data?.students?.length ? (
          <div style={{ width: "100%", textAlign: "left" }}>
            {data.students.map((row) => {
              const draft = draftFor(row.student, row.checking);
              return (
                <div
                  key={row.student}
                  style={{
                    border: "1px solid var(--a2-border, #e3d8c5)",
                    borderRadius: 12,
                    padding: 14,
                    marginBottom: 14,
                  }}
                >
                  <p style={{ margin: "0 0 8px" }}>
                    <strong>{row.name}</strong> — {row.roll_no} ({row.student_class})
                    {row.checked ? <span className="auth-message auth-success" style={{ marginLeft: 8 }}>Checked</span> : null}
                  </p>

                  <div className="auth-field">
                    <label>Homework status</label>
                    <select
                      value={draft.homework_status}
                      onChange={(e) => updateDraft(row.student, { homework_status: e.target.value }, row.checking)}
                    >
                      <option value="DONE">Done</option>
                      <option value="NOT_DONE">Not done</option>
                    </select>
                  </div>

                  <div className="auth-field">
                    <label>Feedback</label>
                    <input
                      type="text"
                      value={draft.feedback}
                      placeholder="Short note (optional)"
                      onChange={(e) => updateDraft(row.student, { feedback: e.target.value }, row.checking)}
                    />
                  </div>

                  <button
                    className="signup-button"
                    type="button"
                    disabled={savingId === row.student}
                    onClick={() => save(row.student)}
                  >
                    {savingId === row.student ? "Saving…" : row.checked ? "Update" : "Save"}
                  </button>
                </div>
              );
            })}
          </div>
        ) : null}

        {!loading && data && data.students?.length === 0 ? (
          <p className="auth-message">No present students in your assigned class right now.</p>
        ) : null}

        <div className="auth-links">
          <Link to="/volunteer/dashboard">Back to dashboard</Link>
        </div>
      </div>
    </div>
  );
}
