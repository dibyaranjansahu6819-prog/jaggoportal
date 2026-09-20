import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import "../signup/signup.css";
import "../auth/auth.css";
import API, { getCurrentUser, logout } from "../services/api";

export const Route = createFileRoute("/volunteer/dashboard")({
  head: () => ({
    meta: [
      { title: "Volunteer Dashboard — Jaago Teaching Portal" },
      { name: "description", content: "Volunteer dashboard: assignments, work sessions and XP." },
      { property: "og:title", content: "Volunteer Dashboard — Jaago Teaching Portal" },
      { property: "og:description", content: "Volunteer dashboard: assignments, work sessions and XP." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: VolunteerDashboard,
});

function VolunteerDashboard() {
  const navigate = useNavigate();
  const cachedUser = getCurrentUser();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removed, setRemoved] = useState(false);
  const [actionError, setActionError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/teachers/dashboard/");
      setDashboard(response.data);
    } catch (err) {
      if (err?.response?.status === 403 && err.response.data?.code === "VOLUNTEER_REMOVED") {
        setError(err.response.data.message || err.response.data.error);
        setRemoved(true);
      } else {
        setError(err?.response?.data?.error || "Unable to load your dashboard. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSignOut = () => {
    logout();
    navigate({ to: "/teacher/signin" });
  };

  const startSession = async () => {
    setActionLoading(true);
    setActionError("");
    try {
      await API.post("/teachers/session/start/");
      await loadDashboard();
    } catch (err) {
      setActionError(err?.response?.data?.error || "Unable to start work session.");
    } finally {
      setActionLoading(false);
    }
  };

  const endSession = async () => {
    setActionLoading(true);
    setActionError("");
    try {
      await API.post("/teachers/session/end/");
      await loadDashboard();
    } catch (err) {
      setActionError(err?.response?.data?.error || "Unable to end work session.");
    } finally {
      setActionLoading(false);
    }
  };

  const volunteer = dashboard?.volunteer || cachedUser || {};
  const assignment = dashboard?.assignment;
  const workSession = assignment?.work_session;

  return (
    <div className="signup-page jaago-page auth-page">
      <img className="jaago-ornament jaago-ornament-gold" src="/jaago-bg-gold-motif.png" alt="" />
      <img className="jaago-ornament jaago-ornament-violet" src="/jaago-bg-violet-motif.png" alt="" />
      <img className="jaago-watermark" src="/jaago-bg-watermark.png" alt="" />

      <div className="signup-card auth-card">
        <div className="signup-header">
          <h1>Volunteer Dashboard</h1>
          <p>{volunteer.name ? `Welcome, ${volunteer.name}` : "Your assigned classes, work sessions and XP."}</p>
        </div>

        {loading ? <p>Loading your dashboard…</p> : null}
        {error ? <p className="auth-message auth-error">{error}</p> : null}
        {removed ? (
          <p className="auth-message">
            <Link to="/volunteer/request-access">Request access from Admin 2 →</Link>
          </p>
        ) : null}

        {!loading && !error && dashboard ? (
          <div style={{ textAlign: "left", width: "100%" }}>
            <p><strong>Date:</strong> {String(dashboard.date)}</p>
            <p><strong>School status:</strong> {dashboard.school_status}</p>
            <p><strong>Work source:</strong> {dashboard.work_source}</p>

            {!assignment ? (
              <>
                <p className="auth-message">{dashboard.message || "No work assigned for today."}</p>
                <Link to="/volunteer/special-added" className="signup-button" style={{ display: "inline-block", textAlign: "center", textDecoration: "none" }}>
                  Check for Special Added work
                </Link>
              </>
            ) : (
              <>
                <p><strong>Class:</strong> {assignment.assigned_class_display || assignment.assigned_class}</p>
                <p><strong>Task:</strong> {assignment.task_display || assignment.task}</p>
                {assignment.instruction ? <p><strong>Instruction:</strong> {assignment.instruction}</p> : null}

                <p><strong>Work session status:</strong> {workSession ? workSession.status : "NOT_STARTED"}</p>

                {actionError ? <p className="auth-message auth-error">{actionError}</p> : null}

                {(!workSession || workSession.status === "NOT_STARTED") && (
                  <button className="signup-button" type="button" disabled={actionLoading} onClick={startSession}>
                    {actionLoading ? "Please wait…" : "Start work session"}
                  </button>
                )}

                {workSession && workSession.status === "IN_PROGRESS" && (
                  <>
                    {assignment.task === "TEACHING" && (
                      <Link to="/volunteer/teaching" className="signup-button" style={{ display: "inline-block", textAlign: "center", textDecoration: "none", marginBottom: 10 }}>
                        Open Track Progress
                      </Link>
                    )}
                    {assignment.task === "CHECKING" && (
                      <Link to="/volunteer/checking" className="signup-button" style={{ display: "inline-block", textAlign: "center", textDecoration: "none", marginBottom: 10 }}>
                        Open Homework Checking
                      </Link>
                    )}
                    <button className="signup-button" type="button" disabled={actionLoading} onClick={endSession}>
                      {actionLoading ? "Please wait…" : "End work session"}
                    </button>
                  </>
                )}

                {workSession && workSession.status === "COMPLETED" && (
                  <p className="auth-message auth-success">Today's work is complete.</p>
                )}
              </>
            )}

            {dashboard.special_added_access ? (
              <p>
                <strong>Special Added:</strong> covering for {dashboard.special_added_access.original_volunteer} (
                {dashboard.special_added_access.original_volunteer_id})
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="auth-links">
          <button type="button" className="signup-button auth-test-button" onClick={handleSignOut}>
            Sign out
          </button>
          <Link to="/">Back to home</Link>
        </div>
      </div>
    </div>
  );
}
