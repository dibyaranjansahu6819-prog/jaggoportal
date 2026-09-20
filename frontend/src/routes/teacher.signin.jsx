import { createFileRoute } from "@tanstack/react-router";
import AuthPage from "../auth/AuthPage";
import { loginVolunteer } from "../services/api";

export const Route = createFileRoute("/teacher/signin")({
  head: () => ({
    meta: [
      { title: "Volunteer Sign In — Jaago Teaching Portal" },
      { name: "description", content: "Volunteers sign in to view assignments and attendance." },
      { property: "og:title", content: "Volunteer Sign In — Jaago Teaching Portal" },
      { property: "og:description", content: "Volunteers sign in to view assignments and attendance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <AuthPage
      title="Volunteer Sign In"
      subtitle="Sign in with your Teacher User ID to see your assigned classes, work sessions and XP."
      redirectTo="/volunteer/dashboard"
      submitLabel="SIGN IN"
      successMessage="Signed in successfully."
      onSubmit={(values) => loginVolunteer(values.user_id, values.password)}
      fields={[
        { name: "user_id", label: "Teacher User ID", type: "text", placeholder: "e.g. SAHM001", autoComplete: "username" },
        { name: "password", label: "Password", type: "password", autoComplete: "current-password" },
      ]}
      links={[
        { to: "/teacher/forgot-password", label: "Forgot password?" },
        { to: "/teacher/signup", label: "Create an account" },
      ]}
    />
  ),
});

