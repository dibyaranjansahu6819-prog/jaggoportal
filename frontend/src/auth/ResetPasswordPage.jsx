import AuthPage from "./AuthPage";
import API from "../services/api";

/**
 * Password-change page opened from the emailed reset link.
 * The backend emails a link like
 * `<JAAGO_FRONTEND_RESET_URL>/<uidb64>/<token>/` (see accounts.views —
 * JAAGO_FRONTEND_RESET_URL defaults to http://localhost:5173/reset-password)
 * and this page posts the new password to the matching
 * POST /auth/reset-password/<uid>/<token>/ endpoint — the ONE reset-confirm
 * endpoint this backend has; it isn't split per role.
 */
export default function ResetPasswordPage({
  title,
  uid,
  token,
  signinTo,
  signinLabel,
  requestTo,
}) {
  const missingToken = !uid || !token;
  return (
    <AuthPage
      title={title}
      subtitle={
        missingToken
          ? "This reset link is invalid or incomplete. Please request a new one."
          : "Choose a new password for your account."
      }
      submitLabel="CHANGE PASSWORD"
      successMessage="Password changed successfully. You can sign in now."
      disabled={missingToken}
      onSubmit={(values) =>
        API.post(`/auth/reset-password/${uid}/${token}/`, {
          new_password: values.new_password,
          confirm_password: values.confirm_password,
        })
      }
      fields={[
        { name: "new_password", label: "New Password", type: "password", autoComplete: "new-password", placeholder: "At least 8 characters" },
        { name: "confirm_password", label: "Confirm New Password", type: "password", autoComplete: "new-password", placeholder: "Repeat the new password" },
      ]}
      links={[
        ...(missingToken && requestTo ? [{ to: requestTo, label: "Request a new reset link" }] : []),
        ...(signinTo ? [{ to: signinTo, label: signinLabel }] : []),
      ]}
    />
  );
}
