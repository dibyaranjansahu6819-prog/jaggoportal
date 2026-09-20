import { createFileRoute } from "@tanstack/react-router";
import Admin2Layout from "@/admin2/Admin2Layout";

export const Route = createFileRoute("/admin2")({
  component: Admin2Layout,
});
