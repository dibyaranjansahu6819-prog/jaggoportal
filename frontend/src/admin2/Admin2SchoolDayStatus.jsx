import { useEffect, useState } from "react";
import { PageHead } from "./Admin2Layout";
import API from "../services/api";

// Backend (admin2.DailySchoolStatusView) only tracks ONE status per
// date — there is no date-range / holiday-calendar model. This page
// is scoped to TOMORROW's status (?scope=tomorrow) so Admin 2 can
// plan the next school day a day ahead, matching what GET/POST
// /admin2/daily-status/ supports.
export default function Admin2SchoolDayStatus() {
  const [mode, setMode] = useState("REGULAR_CLASS");
  const [current, setCurrent] = useState(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [emailResult, setEmailResult] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/admin2/daily-status/?scope=tomorrow");
      setCurrent(response.data);
      if (response.data.status) setMode(response.data.status);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load tomorrow's status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    setSaved(false);
    setError("");
    setEmailResult(null);
    setSaving(true);
    try {
      const response = await API.post("/admin2/daily-status/", { status: mode, scope: "tomorrow" });
      setCurrent(response.data);
      setSaved(true);
      if (response.data.playing_day_email_result) {
        setEmailResult(response.data.playing_day_email_result);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to save tomorrow's status.");
    } finally {
      setSaving(false);
    }
  };

  return <><PageHead title="School Day Status" subtitle={current ? `Operating mode for ${String(current.date)} (tomorrow)` : "Operating mode for tomorrow"} />
    <form className="a2-panel" onSubmit={save}>
      {loading && <p>Loading…</p>}
      <div className="a2-field full"><span className="a2-label">Tomorrow's school day status</span><div className="a2-radio-row">{[["REGULAR_CLASS","Regular Class"],["PLAYING_DAY","Playing Day"],["HOLIDAY","Holiday"]].map(([value,label])=><label className="a2-radio" key={value}><input type="radio" name="mode" value={value} checked={mode===value} onChange={()=>{setMode(value);setSaved(false)}} /> {label}</label>)}</div></div>

      {mode==="HOLIDAY" && <div className="a2-note"><strong>Holiday restrictions:</strong> On a holiday there is no student attendance, volunteer assignment, volunteer work, volunteer session, or homework. Admin2 management access stays available.</div>}
      {mode==="PLAYING_DAY" && <div className="a2-note">Setting Playing Day emails every registered volunteer automatically (backend sends this on save).</div>}

      {error && <p className="a2-note">{error}</p>}

      <button className="a2-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save Status"}</button>
      {saved && <span className="a2-success" role="status">Status saved.</span>}
      {emailResult && (
        <p className="a2-note">
          Playing Day emails: {emailResult.sent ?? emailResult.sent_count ?? "?"} sent
          {emailResult.failed ? `, ${emailResult.failed} failed` : ""}.
        </p>
      )}
    </form>
  </>;
}
