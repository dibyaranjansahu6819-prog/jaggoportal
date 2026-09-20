import { createFileRoute } from "@tanstack/react-router";
import { Admin2Caution } from "@/admin2/Admin2Operations";

export const Route = createFileRoute("/admin2/caution")({
  head: () => ({
    meta: [
      { title: "Caution — Jaago Admin 2" },
      { name: "description", content: "Volunteers with consecutive assigned absences and caution status." },
      { property: "og:title", content: "Caution — Jaago Admin 2" },
      { property: "og:description", content: "Volunteers with consecutive assigned absences and caution status." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Caution,
});
