import { createFileRoute } from "@tanstack/react-router";
import ResetPasswordPage from "../auth/ResetPasswordPage";

export const Route = createFileRoute("/admin1/reset-password")({
  validateSearch: (search) => ({
    uid: typeof search.uid === "string" ? search.uid : "",
    token: typeof search.token === "string" ? search.token : "",
  }),
  head: () => ({
    meta: [
      { title: "Admin 1 Reset Password — Jaago Teaching Portal" },
      { name: "description", content: "Choose a new Admin 1 password for the Jaago Teaching Portal." },
      { property: "og:title", content: "Admin 1 Reset Password — Jaago Teaching Portal" },
      { property: "og:description", content: "Choose a new Admin 1 password." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin1ResetPassword,
});

function Admin1ResetPassword() {
  const { uid, token } = Route.useSearch();
  return (
    <ResetPasswordPage
      title="Reset Admin 1 Password"
      uid={uid}
      token={token}
      signinTo="/admin1/signin"
      signinLabel="Back to Admin 1 sign in"
      requestTo="/admin1/forgot-password"
    />
  );
}
