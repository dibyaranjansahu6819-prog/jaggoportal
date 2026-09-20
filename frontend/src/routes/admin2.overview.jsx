import { createFileRoute } from "@tanstack/react-router";
import Admin2Overview from "@/admin2/Admin2Overview";

export const Route = createFileRoute("/admin2/overview")({
  head: () => ({
    meta: [
      { title: "Admin 2 Overview — Jaago" },
      { name: "description", content: "Jaago Admin 2 overview of registered students and volunteers." },
      { property: "og:title", content: "Admin 2 Overview — Jaago" },
      { property: "og:description", content: "Jaago Admin 2 overview of registered students and volunteers." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Overview,
});
