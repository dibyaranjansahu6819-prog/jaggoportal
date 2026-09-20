import { createFileRoute } from "@tanstack/react-router";
import ResetPasswordPage from "../auth/ResetPasswordPage";

export const Route = createFileRoute("/teacher/reset-password")({
  validateSearch: (search) => ({
    uid: typeof search.uid === "string" ? search.uid : "",
    token: typeof search.token === "string" ? search.token : "",
  }),
  head: () => ({
    meta: [
      { title: "Volunteer Reset Password — Jaago Teaching Portal" },
      { name: "description", content: "Choose a new volunteer account password for the Jaago Teaching Portal." },
      { property: "og:title", content: "Volunteer Reset Password — Jaago Teaching Portal" },
      { property: "og:description", content: "Choose a new volunteer account password." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: TeacherResetPassword,
});

function TeacherResetPassword() {
  const { uid, token } = Route.useSearch();
  return (
    <ResetPasswordPage
      title="Reset Volunteer Password"
      uid={uid}
      token={token}
      signinTo="/teacher/signin"
      signinLabel="Back to volunteer sign in"
      requestTo="/teacher/forgot-password"
    />
  );
}
