import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { Badge, PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2VolunteerDetail() {
  const { id } = useParams({ strict: false });
  const [tab, setTab] = useState("Profile");

  const [volunteer, setVolunteer] = useState(null);
  const [accountStatus, setAccountStatus] = useState(null);
  const [caution, setCaution] = useState(null);
  const [xpData, setXpData] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [direction, setDirection] = useState("add");
  const [points, setPoints] = useState("");
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState("");
  const [removeReason, setRemoveReason] = useState("");
  const [removeNotice, setRemoveNotice] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [listRes, statusRes, xpRes, historyRes, cautionRes] = await Promise.all([
        API.get("/admin2/volunteers/"),
        API.get(`/admin2/volunteers/${id}/status/`),
        API.get(`/admin2/xp/${id}/`),
        API.get("/admin2/assignments/history/"),
        API.get("/admin2/cautions/"),
      ]);
      const found = (listRes.data.volunteers || []).find((v) => String(v.id) === String(id));
      setVolunteer(found || null);
      setAccountStatus(statusRes.data);
      setXpData(xpRes.data);
      setAssignments((historyRes.data.assignments || []).filter((a) => String(a.volunteer) === String(id)));
      setCaution((cautionRes.data.cautions || []).find((c) => String(c.volunteer) === String(id)) || null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load this volunteer.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const saveXp = async (e) => {
    e.preventDefault();
    setNotice("");
    const amount = Number(points);
    if (!amount || amount < 1 || !reason.trim()) {
      setNotice("Enter points and a reason before saving.");
      return;
    }
    const delta = direction === "add" ? amount : -amount;
    try {
      const response = await API.post("/admin2/xp/adjust/", {
        volunteer: id,
        points: delta,
        reason: reason.trim(),
      });
      setNotice(`${delta > 0 ? "+" : "−"}${Math.abs(delta)} XP saved.`);
      setPoints("");
      setReason("");
      setXpData((prev) => ({
        ...prev,
        xp: response.data.current_xp,
        transactions: [response.data.transaction, ...(prev?.transactions || [])],
      }));
    } catch (err) {
      setNotice(err?.response?.data?.detail || "Unable to save XP adjustment.");
    }
  };

  const removeVolunteer = async (e) => {
    e.preventDefault();
    setRemoveNotice("");
    try {
      await API.post(`/admin2/volunteers/${id}/remove/`, {
        reason: removeReason.trim() || "Removed by Admin 2.",
      });
      setRemoveNotice("Volunteer removed.");
      load();
    } catch (err) {
      setRemoveNotice(err?.response?.data?.detail || "Unable to remove volunteer.");
    }
  };

  if (loading) return <p>Loading…</p>;
  if (error || !volunteer) return <p className="a2-note">{error || "Volunteer not found."}</p>;

  const tabs = ["Profile", "XP History", "Assignments", "Removal"];

  return (
    <>
      <PageHead title={volunteer.name} subtitle={`Volunteer ID ${volunteer.user_id}`}>
        <Link className="a2-button secondary" to="/admin2/volunteers">Back to Volunteers</Link>
      </PageHead>

      <section className="a2-panel a2-profile">
        <div>
          <h2>{volunteer.name}</h2>
          <div className="a2-meta">
            <span><strong>Subject:</strong> {volunteer.subject_name}</span>
            <span><strong>Free Days:</strong> {(volunteer.free_days || []).join(", ")}</span>
            <span><strong>Status:</strong> {accountStatus?.status ?? volunteer.status}</span>
          </div>
        </div>
        <article className="a2-card violet a2-stat"><span>Current XP</span><strong>{xpData?.xp ?? volunteer.xp}</strong></article>
      </section>

      <section className="a2-panel">
        <div className="a2-tabs" role="tablist">
          {tabs.map((t) => (
            <button type="button" className={`a2-tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)} key={t}>{t}</button>
          ))}
        </div>

        {tab === "Profile" && (
          <>
            <div className="a2-grid a2-two-col">
              <div><span className="a2-label">Email</span><p>{volunteer.email}</p></div>
              <div><span className="a2-label">WhatsApp</span><p>{volunteer.whatsapp_number}</p></div>
              <div><span className="a2-label">Joining Year</span><p>{volunteer.joining_year}</p></div>
              <div>
                <span className="a2-label">Status</span>
                <p><Badge tone={accountStatus?.status === "REMOVED" ? "red" : accountStatus?.status === "CAUTION" ? "gold" : ""}>{accountStatus?.status ?? volunteer.status}</Badge></p>
              </div>
            </div>

            {accountStatus?.status === "REMOVED" && (
              <div className="a2-note" style={{ marginTop: 12 }}>
                <strong>Removed:</strong> {accountStatus.removed_at ? String(accountStatus.removed_at).slice(0, 10) : "—"}
                {accountStatus.removal_reason ? ` — ${accountStatus.removal_reason}` : ""}
              </div>
            )}

            {caution && (
              <div className="a2-note" style={{ marginTop: 12 }}>
                <strong>Caution:</strong> {caution.absence_streak} consecutive assigned absence(s), as of {caution.caution_date}
                {caution.note ? ` — ${caution.note}` : ""}
              </div>
            )}
          </>
        )}

        {tab === "XP History" && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Date</th><th>Source</th><th>Reason</th><th>Points</th></tr></thead>
              <tbody>
                {(xpData?.transactions || []).map((t) => (
                  <tr key={t.id}>
                    <td>{t.created_at ? String(t.created_at).slice(0, 10) : "—"}</td>
                    <td>{t.source}</td>
                    <td>{t.reason}</td>
                    <td><strong>{t.points > 0 ? "+" : ""}{t.points}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "Assignments" && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Date</th><th>Class</th><th>Task</th><th>Email Status</th></tr></thead>
              <tbody>
                {assignments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.assignment_date}</td>
                    <td>{a.assigned_class_display}</td>
                    <td>{a.task_display}</td>
                    <td><Badge tone={a.email_status === "SENT" ? "green" : a.email_status === "FAILED" ? "red" : ""}>{a.email_status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {assignments.length === 0 && <p className="a2-empty">No assignment history for this volunteer.</p>}
          </div>
        )}

        {tab === "Removal" && (
          <form className="a2-form-grid" onSubmit={removeVolunteer}>
            <div className="a2-field full">
              <label htmlFor="remove-reason">Removal reason</label>
              <input id="remove-reason" value={removeReason} onChange={(e) => setRemoveReason(e.target.value)} placeholder="Reason for removing this volunteer" />
            </div>
            <div>
              <button className="a2-button danger" type="submit" disabled={accountStatus?.status === "REMOVED"}>
                {accountStatus?.status === "REMOVED" ? "Already removed" : "Remove volunteer"}
              </button>
              {removeNotice && <span className="a2-success" role="status">{removeNotice}</span>}
            </div>
          </form>
        )}
      </section>

      <section className="a2-panel">
        <h3>Manual XP Adjustment</h3>
        <form className="a2-form-grid" onSubmit={saveXp}>
          <div className="a2-field">
            <label>Manual adjustment by Admin 2</label>
            <div className="a2-xp-buttons">
              <button type="button" className={`a2-button ${direction === "add" ? "" : "secondary"}`} aria-pressed={direction === "add"} onClick={() => setDirection("add")}>+ XP</button>
              <button type="button" className={`a2-button ${direction === "subtract" ? "danger" : "secondary"}`} aria-pressed={direction === "subtract"} onClick={() => setDirection("subtract")}>− XP</button>
            </div>
          </div>
          <div className="a2-field">
            <label htmlFor="xp-points">Points</label>
            <input id="xp-points" type="number" min="1" value={points} onChange={(e) => setPoints(e.target.value)} />
          </div>
          <div className="a2-field full">
            <label htmlFor="xp-reason">Reason</label>
            <input id="xp-reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for manual adjustment" />
          </div>
          <div>
            <button className="a2-button" type="submit">Save</button>
            {notice && <span className="a2-success" role="status">{notice}</span>}
          </div>
        </form>
      </section>
    </>
  );
}
