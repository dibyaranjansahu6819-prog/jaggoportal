import { createFileRoute } from "@tanstack/react-router";
import AuthPage from "../auth/AuthPage";
import API from "../services/api";

export const Route = createFileRoute("/teacher/forgot-password")({
  head: () => ({
    meta: [
      { title: "Volunteer Forgot Password — Jaago Teaching Portal" },
      { name: "description", content: "Reset your volunteer account password for the Jaago Teaching Portal." },
      { property: "og:title", content: "Volunteer Forgot Password — Jaago Teaching Portal" },
      { property: "og:description", content: "Reset your volunteer account password." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <AuthPage
      title="Forgot Password"
      subtitle="Enter your registered email and we will send you a reset link."
      submitLabel="SEND RESET LINK"
      onSubmit={(values) => API.post("/auth/forgot-password/", { email: values.email })}
      successMessage="If that email is registered, a reset link is on its way."
      fields={[
        { name: "email", label: "Registered Email", type: "email", placeholder: "you@example.com", autoComplete: "email" },
      ]}
      links={[{ to: "/teacher/signin", label: "Back to volunteer sign in" }]}
    />
  ),
});
