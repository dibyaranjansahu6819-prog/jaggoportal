import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import API from "../services/api";
import "../signup/signup.css";
import "./auth.css";

/**
 * Shared sign-in / forgot-password / reset-password screen.
 * Styled to match the Jaago signup pages (cream background, spinning motifs, watermark).
 *
 * `onSubmit(values)` performs the real API call for this specific screen — kept
 * generic here because the backend does not use one shared login/reset contract
 * per role (see the exported helpers in this file for the real ones):
 *
 *   - Volunteers sign in via POST /teachers/login/  { user_id, password }
 *   - Admin 1 / Admin 2 both sign in via the ONE common POST /auth/login/
 *     { username, password } and are told apart by response.profile.role —
 *     there is no separate "admin1 login" / "admin2 login" backend route.
 *   - Every "forgot password" screen uses POST /auth/forgot-password/ { email }
 *   - Every "reset password" screen uses
 *     POST /auth/reset-password/<uid>/<token>/ { new_password, confirm_password }
 *
 * - `disabled`: renders the form read-only (e.g. reset link missing its token).
 * - If the fields include `confirm_password`, password match + min length are checked client-side.
 */
export default function AuthPage({
  title,
  subtitle,
  fields,
  submitLabel,
  onSubmit,
  successMessage,
  links = [],
  redirectTo,
  disabled = false,
}) {
  const navigate = useNavigate();
  const [values, setValues] = useState(() =>
    Object.fromEntries(fields.map((field) => [field.name, ""])),
  );
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [showRequestAccess, setShowRequestAccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setStatus(null);
    if ("confirm_password" in values) {
      if ((values.new_password || "").length < 8) {
        setError("New password must be at least 8 characters.");
        return;
      }
      if (values.new_password !== values.confirm_password) {
        setError("Passwords do not match.");
        return;
      }
    }
    setSubmitting(true);
    setShowRequestAccess(false);
    try {
      await onSubmit(values);
      if (redirectTo) {
        navigate({ to: redirectTo });
        return;
      }
      setStatus(successMessage);
    } catch (err) {
      const serverDetail =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message;
      if (serverDetail) {
        setError(serverDetail);
      } else {
        setError(
          "Unable to reach the server. Please check your connection and try again.",
        );
      }
      if (err?.response?.data?.access_request_allowed) {
        setShowRequestAccess(true);
      }
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
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>

        <form className="signup-form" onSubmit={handleSubmit}>
          {fields.map((field) => (
            <div className="auth-field" key={field.name}>
              <label htmlFor={`auth-${field.name}`}>{field.label}</label>
              <input
                id={`auth-${field.name}`}
                name={field.name}
                type={field.type || "text"}
                value={values[field.name]}
                onChange={handleChange}
                placeholder={field.placeholder || ""}
                autoComplete={field.autoComplete || "off"}
                required
                disabled={disabled}
              />
            </div>
          ))}

          {error ? <p className="auth-message auth-error">{error}</p> : null}
          {showRequestAccess ? (
            <p className="auth-message">
              <Link to="/volunteer/request-access">Request access from Admin 2 →</Link>
            </p>
          ) : null}
          {status ? <p className="auth-message auth-success">{status}</p> : null}

          <button className="signup-button" type="submit" disabled={submitting || disabled}>
            {submitting ? "Please wait…" : submitLabel}
          </button>
        </form>

        <div className="auth-links">
          {links.map((link) => (
            <Link key={link.to} to={link.to}>
              {link.label}
            </Link>
          ))}
          <Link to="/">Back to home</Link>
        </div>
      </div>
    </div>
  );
}
