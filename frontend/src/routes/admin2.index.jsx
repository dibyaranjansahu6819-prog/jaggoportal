import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/admin2/")({
  beforeLoad: () => {
    throw redirect({ to: "/admin2/dashboard" });
  },
});
