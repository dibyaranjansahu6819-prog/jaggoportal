import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Badge, PageHead } from "./Admin2Layout";
import API from "../services/api";

export default function Admin2Volunteers() {
  const [volunteers, setVolunteers] = useState([]);
  const [presentOnly, setPresentOnly] = useState(false);
  const [presentIds, setPresentIds] = useState(null);
  const [presentDate, setPresentDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [presentLoading, setPresentLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await API.get("/admin2/volunteers/");
        if (!cancelled) setVolunteers(response.data.volunteers || []);
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || "Unable to load volunteers.");
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
        const response = await API.get("/admin2/volunteers/present-today/");
        setPresentIds(new Set((response.data.volunteers || []).map((v) => v.id)));
        setPresentDate(response.data.date);
      } catch (err) {
        setError(err?.response?.data?.detail || "Unable to load today's present volunteers.");
        setPresentOnly(false);
      } finally {
        setPresentLoading(false);
      }
    }
  };

  const shown = volunteers.filter((v) => !presentOnly || (presentIds && presentIds.has(v.id)));

  return (
    <>
      <PageHead title="Volunteer Management" subtitle="Profiles, availability, XP and status" />
      <section className="a2-panel">
        <div className="a2-filters">
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
          <p className="a2-note" style={{ marginTop: 0 }}>Showing volunteers marked present on {String(presentDate)}.</p>
        ) : null}
        {loading && <p>Loading…</p>}
        {error && <p className="a2-note">{error}</p>}
        {!loading && !error && (
          <div className="a2-table-wrap">
            <table className="a2-table">
              <thead><tr><th>Volunteer ID</th><th>Name</th><th>Subject</th><th>Free Days</th><th>XP</th><th>Status</th></tr></thead>
              <tbody>
                {shown.map((v) => (
                  <tr className="clickable" key={v.id}>
                    <td><Link className="a2-link" to={`/admin2/volunteers/${v.id}`}>{v.user_id}</Link></td>
                    <td><Link className="a2-link" to={`/admin2/volunteers/${v.id}`}>{v.name}</Link></td>
                    <td>{v.subject_name}</td>
                    <td>{(v.free_days || []).join(", ")}</td>
                    <td>{v.xp}</td>
                    <td><Badge tone={v.status === "CAUTION" ? "gold" : v.status === "REMOVED" ? "red" : ""}>{v.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !error && !shown.length && <div className="a2-empty">No volunteers match these filters.</div>}
      </section>
    </>
  );
}
