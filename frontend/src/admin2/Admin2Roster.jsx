import { useEffect, useState } from "react";
import { PageHead, Badge } from "./Admin2Layout";
import API from "../services/api";

/* "Registered Volunteers" dashboard, now backed by the real Admin 2 API:
     - Registered tab  -> GET /admin2/volunteers/
     - Assigned tab    -> GET /admin2/assignments/today/?scope=tomorrow
     - Assign Module    -> POST /admin2/assignments/send/ (multipart)
   Admin 2 assigns volunteers a day ahead: the "Assigned" tab and the
   assignment itself both target TOMORROW, so today's Assign action is
   for tomorrow's duty. The backend enforces free-day / Sunday /
   duplicate-assignment rules against tomorrow's date itself, so this
   page just surfaces whatever error it returns. */

const CLASS_CHOICES = [
  { value: "ClassA", label: "Class A" },
  { value: "ClassB", label: "Class B" },
  { value: "ClassC", label: "Class C" },
  { value: "ClassD", label: "Class D" },
  { value: "ClassE", label: "Class E" },
];

const TASK_CHOICES = [
  { value: "TEACHING", label: "Teaching" },
  { value: "CHECKING", label: "Checking" },
  { value: "INVIGILATOR", label: "Invigilator" },
];

// Weekday name for a "YYYY-MM-DD" date string, computed without ever
// constructing a real Date in the browser's local timezone — the
// calendar date is what matters, not a moment in time, and a naive
// `new Date(dateStr)` can roll the day backward/forward across a
// timezone boundary and report the wrong weekday.
const weekdayOfIsoDate = (isoDate) => {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", {
    weekday: "long",
    timeZone: "UTC",
  });
};

export default function Admin2Roster() {
  const [tab, setTab] = useState("registered");
  const [volunteers, setVolunteers] = useState([]);
  const [tomorrowAssignments, setTomorrowAssignments] = useState([]);
  const [tomorrowWeekday, setTomorrowWeekday] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [pickerOpen, setPickerOpen] = useState(false);
  const [modalVolunteer, setModalVolunteer] = useState(null);
  const [form, setForm] = useState({ assigned_class: "", task: "TEACHING", instruction: "", attachment: null, homework: "", homeworkFile: null });
  const [msg, setMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [volRes, assignRes] = await Promise.all([
        API.get("/admin2/volunteers/"),
        API.get("/admin2/assignments/today/?scope=tomorrow"),
      ]);
      setVolunteers(volRes.data.volunteers || []);
      setTomorrowAssignments(assignRes.data.assignments || []);
      setTomorrowWeekday(weekdayOfIsoDate(assignRes.data.date));
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load volunteers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const assignedVolunteerIds = new Set(tomorrowAssignments.map((a) => a.volunteer));
  // Only surface volunteers the backend would actually accept for
  // tomorrow: free on tomorrow's weekday (Sunday is never assignable),
  // not already assigned tomorrow, and not removed.
  const free = tomorrowWeekday === "Sunday"
    ? []
    : volunteers.filter((v) =>
        !assignedVolunteerIds.has(v.id) &&
        v.status !== "REMOVED" &&
        (v.free_days || []).includes(tomorrowWeekday)
      );

  const openModal = (volunteer) => {
    setModalVolunteer(volunteer);
    setMsg("");
    setForm({ assigned_class: "", task: "TEACHING", instruction: "", attachment: null, homework: "", homeworkFile: null });
    setPickerOpen(false);
  };

  const submitAssignment = async (e) => {
    e.preventDefault();
    if (!form.assigned_class || !form.instruction.trim()) {
      setMsg("Select a class and describe the task.");
      return;
    }
    setSubmitting(true);
    setMsg("");
    try {
      const body = new FormData();
      body.append("volunteer", modalVolunteer.id);
      body.append("assigned_class", form.assigned_class);
      body.append("task", form.task);
      body.append("instruction", form.instruction.trim());
      if (form.attachment) body.append("attachment", form.attachment);
      if (form.homeworkFile) body.append("homework_attachment", form.homeworkFile);

      await API.post("/admin2/assignments/send/", body, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setModalVolunteer(null);
      await load();
    } catch (err) {
      const data = err?.response?.data;
      const detail = data?.detail || data?.volunteer?.[0] || (Array.isArray(data) ? data[0] : null);
      setMsg(detail || "Unable to send this assignment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHead title="Registered Volunteers" subtitle="Full roster, plus who is assigned to duty tomorrow" />

      <div className="a2-overview-stats a2-panel">
        <div className="a2-stat"><strong>{volunteers.length}</strong><span>Registered</span></div>
        <div className="a2-stat"><strong className="a2-green-num">{tomorrowAssignments.length}</strong><span>Assigned Tomorrow</span></div>
      </div>

      <div className="a2-actions" style={{ margin: "16px 0" }}>
        <button type="button" className={`a2-button small ${tab === "registered" ? "" : "secondary"}`} onClick={() => setTab("registered")}>Registered Volunteers</button>
        <button type="button" className={`a2-button small ${tab === "assigned" ? "" : "secondary"}`} onClick={() => setTab("assigned")}>Assigned Volunteers</button>
      </div>

      {error && <p className="a2-note">{error}</p>}

      {tab === "assigned" && (
        <section className="a2-panel" style={{ marginBottom: 16 }}>
          <button type="button" className="a2-button small" onClick={() => setPickerOpen((v) => !v)}>
            {pickerOpen ? "− Close List" : "+ Assign Volunteer"}
          </button>
          {pickerOpen && (
            <div style={{ marginTop: 12 }}>
              <p style={{ margin: "0 0 8px", color: "var(--a2-muted)" }}>Volunteers free tomorrow, not yet assigned</p>
              {free.length === 0 ? <p className="a2-empty">No unassigned volunteers available.</p> : (
                <div className="a2-actions" style={{ flexWrap: "wrap" }}>
                  {free.map((v) => (
                    <button key={v.id} type="button" className="a2-button small secondary" onClick={() => openModal(v)}>
                      {v.user_id} — {v.name} ({v.subject_name})
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {!loading && (
        <section className="a2-panel">
          <div className="a2-table-wrap">
            {tab === "registered" ? (
              <table className="a2-table">
                <thead><tr><th>Sl</th><th>Jaago User ID</th><th>Name</th><th>Subject</th><th>Free Days</th><th>Status</th></tr></thead>
                <tbody>{volunteers.map((v, i) => (
                  <tr key={v.id}><td>{i + 1}</td><td>{v.user_id}</td><td>{v.name}</td><td>{v.subject_name}</td><td>{(v.free_days || []).join(", ")}</td><td><Badge tone={v.status === "REMOVED" ? "red" : v.status === "CAUTION" ? "gold" : ""}>{v.status}</Badge></td></tr>
                ))}</tbody>
              </table>
            ) : (
              <table className="a2-table">
                <thead><tr><th>Volunteer</th><th>Class</th><th>Task</th><th>Instruction</th><th>Email Status</th></tr></thead>
                <tbody>{tomorrowAssignments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.volunteer_name} ({a.volunteer_user_id})</td>
                    <td>{a.assigned_class_display}</td>
                    <td>{a.task_display}</td>
                    <td>{a.instruction}</td>
                    <td><Badge tone={a.email_status === "SENT" ? "green" : a.email_status === "FAILED" ? "red" : ""}>{a.email_status}</Badge></td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </div>
          {tab === "assigned" && tomorrowAssignments.length === 0 && (
            <p className="a2-empty">No volunteers assigned for tomorrow yet — use “+ Assign Volunteer” above.</p>
          )}
        </section>
      )}

      {modalVolunteer && (
        <div className="a2-modal-overlay" role="dialog" aria-modal="true">
          <div className="a2-modal">
            <div className="a2-modal-head">
              <h3>Assign Work — {modalVolunteer.name}</h3>
              <button type="button" className="a2-overview-close" onClick={() => setModalVolunteer(null)}>×</button>
            </div>
            <form className="a2-modal-body" onSubmit={submitAssignment}>
              <label>Class
                <select value={form.assigned_class} onChange={(e) => setForm({ ...form, assigned_class: e.target.value })}>
                  <option value="">Select Class</option>
                  {CLASS_CHOICES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </label>
              <label>Task
                <select value={form.task} onChange={(e) => setForm({ ...form, task: e.target.value })}>
                  {TASK_CHOICES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </label>
              <label>Instruction
                <textarea rows={4} placeholder="Describe the task for this volunteer…" value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} />
              </label>
              <label>Attach Module (PDF / doc / image)
                <input type="file" onChange={(e) => setForm({ ...form, attachment: e.target.files?.[0] || null })} />
              </label>
              <label>Attach Homework (optional)
                <input type="file" onChange={(e) => setForm({ ...form, homeworkFile: e.target.files?.[0] || null })} />
              </label>
              <label>Send To
                <input type="email" readOnly value={modalVolunteer.email || ""} />
              </label>
              {msg && <p style={{ color: "#b3261e", margin: 0 }}>{msg}</p>}
              <div className="a2-modal-actions">
                <button type="button" className="a2-button small secondary" onClick={() => setModalVolunteer(null)}>Cancel</button>
                <button type="submit" className="a2-button small" disabled={submitting}>{submitting ? "Sending…" : "Send Email"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
