import { createFileRoute } from "@tanstack/react-router";
import AuthPage from "../auth/AuthPage";
import API from "../services/api";

export const Route = createFileRoute("/admin1/forgot-password")({
  head: () => ({
    meta: [
      { title: "Admin 1 Forgot Password — Jaago Teaching Portal" },
      { name: "description", content: "Reset the Admin 1 attendance account password." },
      { property: "og:title", content: "Admin 1 Forgot Password — Jaago Teaching Portal" },
      { property: "og:description", content: "Reset the Admin 1 attendance account password." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <AuthPage
      title="Forgot Password"
      subtitle="Enter the Admin 1 email to receive a password reset link."
      submitLabel="SEND RESET LINK"
      onSubmit={(values) => API.post("/auth/forgot-password/", { email: values.email })}
      successMessage="If that email is registered, a reset link is on its way."
      fields={[
        { name: "email", label: "Admin 1 Email", type: "email", placeholder: "admin1@jaago.org", autoComplete: "email" },
      ]}
      links={[{ to: "/admin1/signin", label: "Back to Admin 1 sign in" }]}
    />
  ),
});
