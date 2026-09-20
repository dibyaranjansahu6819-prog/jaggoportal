import { useState } from "react";
import { Link } from "@tanstack/react-router";
import "../signup/signup.css";
import "./auth.css";
import API from "../services/api";

/**
 * Public page for a REMOVED volunteer to ask Admin 2 for their
 * account to be reinstated.
 *
 * Backend: POST /api/admin2/volunteer/request-access/ (AllowAny)
 *   body: { user_id, message }
 */
export default function VolunteerRequestAccess() {
  const [userId, setUserId] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setStatus(null);
    if (!userId.trim()) {
      setError("Your Teacher User ID is required.");
      return;
    }
    setSubmitting(true);
    try {
      const response = await API.post("/admin2/volunteer/request-access/", {
        user_id: userId.trim(),
        message: message.trim(),
      });
      setStatus(response.data.message || "Access request submitted.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to submit your request right now.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="signup-page jaago-page auth-page">
      <img className="jaago-ornament jaago-ornament-gold" src="/jaago-bg-gold-motif.png" alt="" />
      <img className="jaago-ornament jaago-ornament-violet" src="/jaago-bg-violet-motif.png" alt="" />
      <img className="jaago-watermark" src="/jaago-bg-watermark.png" alt="" />

      <div className="signup-card auth-card">
        <div className="signup-header">
          <h1>Request Access</h1>
          <p>If your volunteer account was removed by Admin 2, request access again here.</p>
        </div>

        <form className="signup-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="access-user-id">Teacher User ID</label>
            <input
              id="access-user-id"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="e.g. SAHM001"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="access-message">Message (optional)</label>
            <input
              id="access-message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Briefly explain why you'd like access restored"
            />
          </div>

          {error ? <p className="auth-message auth-error">{error}</p> : null}
          {status ? <p className="auth-message auth-success">{status}</p> : null}

          <button className="signup-button" type="submit" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit Request"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/teacher/signin">Back to volunteer sign in</Link>
          <Link to="/">Back to home</Link>
        </div>
      </div>
    </div>
  );
}
