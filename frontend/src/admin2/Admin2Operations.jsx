import { useEffect, useState } from "react";
import { Badge, PageHead } from "./Admin2Layout";
import API, { getMediaUrl } from "../services/api";

export function Admin2Caution() {
  const [cautions, setCautions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await API.get("/admin2/cautions/");
        if (!cancelled) setCautions(response.data.cautions || []);
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load cautions.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <>
      <PageHead title="Caution" subtitle="Consecutive assigned absences only" />
      <div className="a2-note"><strong>Caution rule:</strong> Only assigned volunteer absences contribute to the 3-consecutive-absence caution. Special Added and Playing Day absences are excluded.</div>
      <section className="a2-panel">
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && !error && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Volunteer</th><th>Consecutive Assigned Absences</th><th>Status</th><th>Caution Date</th><th>Note</th></tr></thead>
              <tbody>
                {cautions.map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.volunteer_name}</strong><br /><small>{c.volunteer_user_id}</small></td>
                    <td>{c.absence_streak}</td>
                    <td><Badge tone={c.absence_streak >= 3 ? "red" : "gold"}>{c.status}</Badge></td>
                    <td>{c.caution_date}</td>
                    <td>{c.note || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {cautions.length === 0 && <p className="a2-empty">No active cautions.</p>}
          </div>
        )}
      </section>
    </>
  );
}

export function Admin2AccessRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/admin2/access-requests/");
      setRequests(response.data.requests || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load access requests.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const decide = async (id, decision) => {
    setBusyId(id);
    try {
      await API.post(`/admin2/access-requests/${id}/decide/`, { decision });
      setRequests((items) => items.filter((item) => item.id !== id));
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to record this decision.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <PageHead title="Access Requests" subtitle="Review pending volunteer access" />
      <section className="a2-panel">
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && !error && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Volunteer</th><th>Requested</th><th>Message</th><th>Action</th></tr></thead>
              <tbody>
                {requests.map((r) => (
                  <tr key={r.id}>
                    <td>{r.volunteer_name} ({r.volunteer_user_id})</td>
                    <td>{r.requested_at ? String(r.requested_at).slice(0, 10) : "—"}</td>
                    <td>{r.message || "—"}</td>
                    <td>
                      <div className="a2-actions">
                        <button className="a2-button small" disabled={busyId === r.id} onClick={() => decide(r.id, "APPROVED")}>Approve</button>
                        <button className="a2-button small danger" disabled={busyId === r.id} onClick={() => decide(r.id, "DENIED")}>Deny</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {requests.length === 0 && <p className="a2-empty">No pending access requests.</p>}
          </div>
        )}
      </section>
    </>
  );
}

export function Admin2Assignments() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryingId, setRetryingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/admin2/assignments/history/");
      setRows(response.data.assignments || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load assignment history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const retry = async (id) => {
    setRetryingId(id);
    try {
      const response = await API.post(`/admin2/assignments/${id}/retry-email/`);
      setRows((items) => items.map((item) => (item.id === id ? response.data.assignment : item)));
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to retry this email.");
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <>
      <PageHead title="Assignment History" subtitle="Everything Admin 2 has assigned — volunteer instructions, email delivery and work sessions" />
      <section className="a2-panel">
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Date</th><th>Volunteer</th><th>Class</th><th>Subject</th><th>Task</th><th>Instruction</th><th>Email Status</th></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.assignment_date}</td>
                    <td>{r.volunteer_name}</td>
                    <td>{r.assigned_class_display}</td>
                    <td>{r.volunteer_subject}</td>
                    <td>{r.task_display}</td>
                    <td>
                      {r.instruction}
                      {r.attachment && (
                        <>
                          {" "}
                          <a href={getMediaUrl(r.attachment)} target="_blank" rel="noreferrer">📎 module</a>
                        </>
                      )}
                      {r.homework_attachment && (
                        <>
                          {" "}
                          <a href={getMediaUrl(r.homework_attachment)} target="_blank" rel="noreferrer">📎 homework</a>
                        </>
                      )}
                    </td>
                    <td>
                      <Badge tone={r.email_status === "SENT" ? "green" : r.email_status === "FAILED" ? "red" : ""}>{r.email_status}</Badge>
                      {r.email_status === "FAILED" && (
                        <button className="a2-button small danger" style={{ marginTop: 7 }} disabled={retryingId === r.id} onClick={() => retry(r.id)}>
                          {retryingId === r.id ? "Retrying…" : "Retry Email"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && rows.length === 0 && <p className="a2-empty">No assignments yet.</p>}
      </section>
    </>
  );
}

export function Admin2DailyPNG() {
  const [todayRows, setTodayRows] = useState([]);
  const [todayInfo, setTodayInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await API.get("/admin2/assignments/today/");
        if (!cancelled) {
          setTodayRows(response.data.assignments || []);
          setTodayInfo(response.data);
        }
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load today's assignments.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const downloadBlob = async (path, filename) => {
    setDownloading(true);
    try {
      const response = await API.get(path, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Unable to generate the download.");
    } finally {
      setDownloading(false);
    }
  };

  const dateLabel = todayInfo ? String(todayInfo.date) : "";

  return (
    <>
      <PageHead title="Daily PNG" subtitle="All volunteers assigned for today — class, name, subject, role" />
      <div className="a2-png-controls">
        <button className="a2-button secondary" disabled={downloading} onClick={() => downloadBlob("/admin2/assignments/export-excel/?all=true", "jaago-assignments-all.xlsx")}>
          Export to Excel
        </button>
        <button className="a2-button" disabled={downloading} onClick={() => downloadBlob("/admin2/assignments/export-png/", `jaago-daily-${dateLabel}.png`)}>
          Download PNG
        </button>
      </div>
      {error && <p className="a2-note">{error}</p>}
      {loading && <p>Loading…</p>}
      {!loading && (
        <section className="a2-png-card">
          <h2>JAAGO — DAILY SCHOOL RECORD</h2>
          <p style={{ marginTop: 0, color: "var(--a2-muted)" }}>{dateLabel} · {todayRows.length} volunteer(s) assigned</p>
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Class</th><th>Volunteer</th><th>Subject</th><th>Task</th></tr></thead>
              <tbody>
                {todayRows.map((r) => (
                  <tr key={r.id}><td>{r.assigned_class_display}</td><td>{r.volunteer_name}</td><td>{r.volunteer_subject}</td><td>{r.task_display}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          {todayRows.length === 0 && <p className="a2-empty">No volunteers assigned for today.</p>}
        </section>
      )}
    </>
  );
}
