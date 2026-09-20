import { createFileRoute } from "@tanstack/react-router";
import AuthPage from "../auth/AuthPage";
import { loginWithUsername, tokenStorage } from "../services/api";

export const Route = createFileRoute("/admin2/signin")({
  head: () => ({
    meta: [
      { title: "Admin 2 Sign In — Jaago Teaching Portal" },
      { name: "description", content: "Admin 2 sign in for school management at Jaago." },
      { property: "og:title", content: "Admin 2 Sign In — Jaago Teaching Portal" },
      { property: "og:description", content: "Admin 2 sign in for school management." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <AuthPage
      title="Admin 2 Sign In"
      subtitle="Sign in to manage students, volunteers, assignments and school day status."
      submitLabel="SIGN IN"
      successMessage="Signed in successfully."
      redirectTo="/admin2/dashboard"
      onSubmit={async (values) => {
        const data = await loginWithUsername(values.username, values.password);
        if (data.profile?.role !== "ADMIN2") {
          tokenStorage.clear();
          throw new Error("This account is not registered as Admin 2. Please use the correct sign in page.");
        }
        return data;
      }}
      fields={[
        { name: "username", label: "Admin 2 Username", placeholder: "admin2", autoComplete: "username" },
        { name: "password", label: "Password", type: "password", autoComplete: "current-password" },
      ]}
      links={[{ to: "/admin2/forgot-password", label: "Forgot password?" }]}
    />
  ),
});
