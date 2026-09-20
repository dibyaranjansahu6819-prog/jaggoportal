import { createFileRoute } from "@tanstack/react-router";
import VolunteerRequestAccess from "../auth/VolunteerRequestAccess";

export const Route = createFileRoute("/volunteer/request-access")({
  head: () => ({
    meta: [
      { title: "Request Access — Jaago Teaching Portal" },
      { name: "description", content: "Ask Admin 2 to restore a removed volunteer account." },
    ],
  }),
  component: VolunteerRequestAccess,
});
