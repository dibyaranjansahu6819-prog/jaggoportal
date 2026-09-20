import { createFileRoute } from "@tanstack/react-router";
import Admin2Roster from "@/admin2/Admin2Roster";

export const Route = createFileRoute("/admin2/roster")({
  head: () => ({
    meta: [
      { title: "Registered Volunteers — Jaago Admin 2" },
      { name: "description", content: "Full volunteer roster, today's assigned volunteers and module assignment." },
      { property: "og:title", content: "Registered Volunteers — Jaago Admin 2" },
      { property: "og:description", content: "Full volunteer roster, today's assigned volunteers and module assignment." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Roster,
});
