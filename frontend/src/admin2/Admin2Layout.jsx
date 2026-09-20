import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import "./Admin2.css";
import JaagoBg from "./JaagoBg";

const links = [
  ["/admin2/dashboard", "Dashboard"], ["/admin2/overview", "Overview"],
  ["/admin2/school-day-status", "Day Status"],
  ["/admin2/holidays", "Holidays"],
  ["/admin2/students", "Students"], ["/admin2/volunteers", "Volunteers"],
  ["/admin2/roster", "Registered Volunteers"],
  ["/admin2/caution", "Caution"], ["/admin2/access-requests", "Requests"],
  ["/admin2/assignments", "Assignments"], ["/admin2/daily-png", "Daily PNG"],
];

export default function Admin2Layout() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const isAccountPage =
    pathname === "/admin2/signin" ||
    pathname === "/admin2/forgot-password" ||
    pathname === "/admin2/reset-password";

  if (isAccountPage) return <Outlet />;

  return <div className="admin2-page">
    <JaagoBg />
    <div className="admin2-shell">
      <header className="admin2-header">
        <img className="admin2-logo" src="/jaago-attendance-logo.jpeg" alt="Jaago Portal" />
        <div className="admin2-heading"><p className="admin2-kicker">Admin 2</p><h1>Management Dashboard</h1><p>School operations, people and performance</p></div>
        <div className="admin2-date">{new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}</div>
      </header>
      <nav className="admin2-nav" aria-label="Admin 2 navigation">
        {links.map(([to,label]) => <Link key={to} to={to} activeProps={{ className: "active" }}>{label}</Link>)}
      <Link to="/" className="a2-home-link" style={{ marginLeft: "auto" }}>← Back to Home</Link>
      </nav>
      <main className="admin2-content"><Outlet /></main>
    </div>
  </div>;
}

export function PageHead({ title, subtitle, children }) {
  return <div className="a2-page-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{children && <div className="a2-actions">{children}</div>}</div>;
}

export function Badge({ children, tone="" }) { return <span className={`a2-badge ${tone}`}>{children}</span>; }
