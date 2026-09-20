import { useEffect, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import "../signup/signup.css";
import "../auth/auth.css";
import API from "../services/api";

export default function VolunteerSpecialAdded() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selecting, setSelecting] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/teachers/special-added/available-work/");
      setData(response.data);
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to load available work.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const select = async (assignmentId) => {
    setSelecting(assignmentId);
    setError("");
    try {
      await API.post("/teachers/special-added/select-work/", { assignment: assignmentId });
      navigate({ to: "/volunteer/dashboard" });
    } catch (err) {
      setError(err?.response?.data?.error || "Unable to select this work.");
    } finally {
      setSelecting(null);
    }
  };

  return (
    <div className="signup-page jaago-page auth-page">
      <img className="jaago-ornament jaago-ornament-gold" src="/jaago-bg-gold-motif.png" alt="" />
      <img className="jaago-ornament jaago-ornament-violet" src="/jaago-bg-violet-motif.png" alt="" />
      <img className="jaago-watermark" src="/jaago-bg-watermark.png" alt="" />

      <div className="signup-card auth-card" style={{ maxWidth: 680 }}>
        <div className="signup-header">
          <h1>Special Added Work</h1>
          <p>Pick an absent volunteer's assignment to cover today.</p>
        </div>

        {loading ? <p>Loading…</p> : null}
        {error ? <p className="auth-message auth-error">{error}</p> : null}

        {!loading && data?.message ? <p className="auth-message">{data.message}</p> : null}

        {!loading && data?.selected ? (
          <div style={{ width: "100%", textAlign: "left" }}>
            <p><strong>Class:</strong> {data.work.class}</p>
            <p><strong>Task:</strong> {data.work.task}</p>
            <p><strong>Covering for:</strong> {data.work.original_volunteer?.name} ({data.work.original_volunteer?.user_id})</p>
            <p><strong>Instruction:</strong> {data.work.instruction || "—"}</p>
          </div>
        ) : null}

        {!loading && data?.eligible && !data?.selected ? (
          <div style={{ width: "100%", textAlign: "left" }}>
            {(data.available_work || []).map((item) => (
              <div
                key={item.id}
                style={{ border: "1px solid var(--a2-border, #e3d8c5)", borderRadius: 12, padding: 14, marginBottom: 14 }}
              >
                <p style={{ margin: "0 0 6px" }}>
                  <strong>{item.class}</strong> — {item.task}
                </p>
                <p style={{ margin: "0 0 6px", color: "#6b6357" }}>
                  Originally assigned to {item.original_volunteer?.name} ({item.original_volunteer?.user_id})
                </p>
                {item.instruction ? <p style={{ margin: "0 0 10px" }}>{item.instruction}</p> : null}
                <button className="signup-button" type="button" disabled={selecting === item.id} onClick={() => select(item.id)}>
                  {selecting === item.id ? "Selecting…" : "Take this work"}
                </button>
              </div>
            ))}
          </div>
        ) : null}

        <div className="auth-links">
          <Link to="/volunteer/dashboard">Back to dashboard</Link>
        </div>
      </div>
    </div>
  );
}
