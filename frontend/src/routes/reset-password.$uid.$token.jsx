import { createFileRoute, useParams } from "@tanstack/react-router";
import ResetPasswordPage from "../auth/ResetPasswordPage";

export const Route = createFileRoute("/reset-password/$uid/$token")({
  head: () => ({
    meta: [
      { title: "Reset Password — Jaago Portal" },
      { name: "description", content: "Choose a new password for your Jaago Portal account." },
      { property: "og:title", content: "Reset Password — Jaago Portal" },
      { property: "og:description", content: "Choose a new password for your Jaago Portal account." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: EmailResetPassword,
});

function EmailResetPassword() {
  const { uid, token } = useParams({ strict: false });
  return (
    <ResetPasswordPage
      title="Reset Password"
      uid={uid}
      token={token}
    />
  );
}
