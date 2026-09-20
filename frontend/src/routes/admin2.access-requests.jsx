import { createFileRoute } from "@tanstack/react-router";
import { Admin2AccessRequests } from "@/admin2/Admin2Operations";

export const Route = createFileRoute("/admin2/access-requests")({
  head: () => ({
    meta: [
      { title: "Access Requests — Jaago Admin 2" },
      { name: "description", content: "Approve or deny volunteer access requests." },
      { property: "og:title", content: "Access Requests — Jaago Admin 2" },
      { property: "og:description", content: "Approve or deny volunteer access requests." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2AccessRequests,
});
