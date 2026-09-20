import { createFileRoute } from "@tanstack/react-router";
import Admin2Volunteers from "@/admin2/Admin2Volunteers";

export const Route = createFileRoute("/admin2/volunteers/")({
  head: () => ({
    meta: [
      { title: "Volunteers — Jaago Admin 2" },
      { name: "description", content: "Volunteer management: profiles, availability, XP and status." },
      { property: "og:title", content: "Volunteers — Jaago Admin 2" },
      { property: "og:description", content: "Volunteer management: profiles, availability, XP and status." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Volunteers,
});
