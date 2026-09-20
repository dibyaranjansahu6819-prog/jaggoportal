import { createFileRoute } from "@tanstack/react-router";
import Admin2Holidays from "@/admin2/Admin2Holidays";

export const Route = createFileRoute("/admin2/holidays")({
  head: () => ({
    meta: [
      { title: "Holidays — Jaago Admin 2" },
      { name: "description", content: "Manage the school holiday calendar." },
    ],
  }),
  component: Admin2Holidays,
});
