import { createFileRoute } from "@tanstack/react-router";
import AuthPage from "../auth/AuthPage";
import { loginWithUsername, tokenStorage } from "../services/api";

export const Route = createFileRoute("/admin1/signin")({
  head: () => ({
    meta: [
      { title: "Admin 1 Sign In — Jaago Teaching Portal" },
      { name: "description", content: "Admin 1 sign in for daily attendance sessions at Jaago." },
      { property: "og:title", content: "Admin 1 Sign In — Jaago Teaching Portal" },
      { property: "og:description", content: "Admin 1 sign in for daily attendance sessions." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <AuthPage
      title="Admin 1 Sign In"
      subtitle="Sign in to run today's student and volunteer attendance session."
      submitLabel="SIGN IN"
      successMessage="Signed in successfully."
      redirectTo="/admin1/attendance-dashboard"
      onSubmit={async (values) => {
        const data = await loginWithUsername(values.username, values.password);
        if (data.profile?.role !== "ADMIN1") {
          tokenStorage.clear();
          throw new Error("This account is not registered as Admin 1. Please use the correct sign in page.");
        }
        return data;
      }}
      fields={[
        { name: "username", label: "Admin 1 Username", placeholder: "admin1", autoComplete: "username" },
        { name: "password", label: "Password", type: "password", autoComplete: "current-password" },
      ]}
      links={[{ to: "/admin1/forgot-password", label: "Forgot password?" }]}
    />
  ),
});
