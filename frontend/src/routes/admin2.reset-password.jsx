import { createFileRoute } from "@tanstack/react-router";
import ResetPasswordPage from "../auth/ResetPasswordPage";

export const Route = createFileRoute("/admin2/reset-password")({
  validateSearch: (search) => ({
    uid: typeof search.uid === "string" ? search.uid : "",
    token: typeof search.token === "string" ? search.token : "",
  }),
  head: () => ({
    meta: [
      { title: "Admin 2 Reset Password — Jaago Teaching Portal" },
      { name: "description", content: "Choose a new Admin 2 password for the Jaago Teaching Portal." },
      { property: "og:title", content: "Admin 2 Reset Password — Jaago Teaching Portal" },
      { property: "og:description", content: "Choose a new Admin 2 password." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2ResetPassword,
});

function Admin2ResetPassword() {
  const { uid, token } = Route.useSearch();
  return (
    <ResetPasswordPage
      title="Reset Admin 2 Password"
      uid={uid}
      token={token}
      signinTo="/admin2/signin"
      signinLabel="Back to Admin 2 sign in"
      requestTo="/admin2/forgot-password"
    />
  );
}
