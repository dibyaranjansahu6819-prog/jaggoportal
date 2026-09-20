import { useEffect, useState } from "react";
import { Badge, PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2Holidays() {
  const [holidays, setHolidays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [date, setDate] = useState("");
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState("");

  const [savingId, setSavingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/admin2/holidays/");
      setHolidays(response.data.holidays || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load holidays.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createHoliday = async (e) => {
    e.preventDefault();
    setFormError("");
    if (!date || !name.trim()) {
      setFormError("Date and name are both required.");
      return;
    }
    setCreating(true);
    try {
      const response = await API.post("/admin2/holidays/", { date, name: name.trim() });
      setHolidays((prev) => [response.data.holiday, ...prev]);
      setDate("");
      setName("");
    } catch (err) {
      const data = err?.response?.data;
      setFormError(data?.date?.[0] || data?.name?.[0] || data?.detail || "Unable to create this holiday.");
    } finally {
      setCreating(false);
    }
  };

  const toggleActive = async (holiday) => {
    setSavingId(holiday.id);
    try {
      const response = await API.patch(`/admin2/holidays/${holiday.id}/`, { is_active: !holiday.is_active });
      setHolidays((prev) => prev.map((h) => (h.id === holiday.id ? response.data.holiday : h)));
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to update this holiday.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <>
      <PageHead title="Holidays" subtitle="Manage the school holiday calendar" />

      <section className="a2-panel">
        <h3 style={{ marginTop: 0 }}>Add a holiday</h3>
        <form className="a2-form-grid" onSubmit={createHoliday}>
          <div className="a2-field">
            <label htmlFor="holiday-date">Date</label>
            <input id="holiday-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="a2-field full">
            <label htmlFor="holiday-name">Name</label>
            <input id="holiday-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Durga Puja" />
          </div>
          {formError && <p className="a2-note">{formError}</p>}
          <div>
            <button className="a2-button" type="submit" disabled={creating}>
              {creating ? "Adding…" : "Add Holiday"}
            </button>
          </div>
        </form>
      </section>

      <section className="a2-panel" style={{ marginTop: 16 }}>
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && !error && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Date</th><th>Name</th><th>Status</th><th>Added by</th><th></th></tr></thead>
              <tbody>
                {holidays.map((h) => (
                  <tr key={h.id}>
                    <td>{h.date}</td>
                    <td>{h.name}</td>
                    <td><Badge tone={h.is_active ? "green" : "red"}>{h.is_active ? "Active" : "Inactive"}</Badge></td>
                    <td>{h.created_by_username || "—"}</td>
                    <td>
                      <button
                        className="a2-button small secondary"
                        type="button"
                        disabled={savingId === h.id}
                        onClick={() => toggleActive(h)}
                      >
                        {h.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {holidays.length === 0 && <p className="a2-empty">No holidays added yet.</p>}
          </div>
        )}
      </section>
    </>
  );
}
