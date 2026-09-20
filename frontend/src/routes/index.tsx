import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, ClipboardList, GraduationCap, ShieldCheck, Users } from "lucide-react";

type PortalLink = { label: string; to: string };

const portalChoices: {
  title: string;
  description: string;
  action: string;
  to: string;
  icon: typeof GraduationCap;
  tone: string;
  links: PortalLink[];
}[] = [
  {
    title: "Student Registration",
    description: "New here? Register as a student to get your roll number and join classes at Jaago.",
    action: "Register as Student",
    to: "/student/signup",
    icon: GraduationCap,
    tone: "green",
    links: [],
  },
  {
    title: "Volunteer Sign Up / Sign In",
    description: "Join as a teaching volunteer or continue your journey — sign up or sign in to manage your classes.",
    action: "Sign Up / Sign In",
    to: "/teacher/signup",
    icon: Users,
    tone: "violet",
    links: [
      { label: "Sign In", to: "/teacher/signin" },
      { label: "Forgot password?", to: "/teacher/forgot-password" },
    ],
  },
  {
    title: "Admin 1 Sign In",
    description: "Attendance admins sign in to run the daily student and volunteer attendance session.",
    action: "Sign In as Admin 1",
    to: "/admin1/signin",
    icon: ClipboardList,
    tone: "gold",
    links: [{ label: "Forgot password?", to: "/admin1/forgot-password" }],
  },
  {
    title: "Admin 2 Sign In",
    description: "Management admins sign in for students, volunteers, assignments, cautions and requests.",
    action: "Sign In as Admin 2",
    to: "/admin2/signin",
    icon: ShieldCheck,
    tone: "violet",
    links: [{ label: "Forgot password?", to: "/admin2/forgot-password" }],
  },
];

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Jaago Teaching Portal" },
      {
        name: "description",
        content: "Jaago Teaching Portal for students, volunteers, attendance, and school management.",
      },
      { property: "og:title", content: "Jaago Teaching Portal" },
      {
        property: "og:description",
        content: "Learning, attendance, and volunteer management for the Jaago community.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HomePage,
});

function HomePage() {
  return (
    <main className="portal-home jaago-page">
      <img className="jaago-ornament jaago-ornament-gold" src="/jaago-bg-gold-motif.png" alt="" />
      <img className="jaago-ornament jaago-ornament-violet" src="/jaago-bg-violet-motif.png" alt="" />
      <img className="jaago-watermark" src="/jaago-bg-watermark.png" alt="" />

      <header className="portal-header">
        <a className="portal-brand" href="#top" aria-label="Jaago Teaching Portal home">
          <img src="/jaago-attendance-logo.jpeg" alt="Jaago" />
          <strong>Jaago Teaching Portal</strong>
        </a>
        <nav aria-label="Homepage navigation">
          <a href="#top">Home</a>
          <a href="#about">About Us</a>
        </nav>
      </header>

      <div id="top" className="portal-content">
        <section id="about" className="portal-about" aria-labelledby="about-heading">
          <div className="portal-logo-card">
            <img src="/jaago-attendance-logo.jpeg" alt="Jaago — Uddhare Daatmanatmanam" />
          </div>
          <div className="portal-about-copy">
            <h2 id="about-heading">About Us</h2>
            <p>
              Jaago is a community-driven initiative bringing volunteer teachers and students together to make
              quality education accessible for every child. From classroom lessons to attendance tracking, the
              Jaago Teaching Portal is built to support students, volunteers and administrators every step of the way.
            </p>
          </div>
        </section>

        <section className="portal-intro" aria-labelledby="portal-heading">
          <h1 id="portal-heading">
            <span>Jaago</span> <span>Teaching</span> <span>Portal</span>
          </h1>
          <p>Uddhare Daatmanatmanam — Empowering learners, one classroom at a time</p>
        </section>

        <section className="portal-choice-grid" aria-label="Portal access choices">
          {portalChoices.map(({ title, description, action, to, icon: Icon, tone, links }) => (
            <article className={`portal-choice portal-choice-${tone}`} key={title}>
              <div className="portal-choice-icon" aria-hidden="true"><Icon size={24} strokeWidth={2.2} /></div>
              <h2>{title}</h2>
              <p>{description}</p>
              <Link to={to}>
                {action} <ArrowRight size={15} aria-hidden="true" />
              </Link>
              {links.length > 0 && (
                <div className="portal-choice-links">
                  {links.map((link) => (
                    <Link key={link.to} to={link.to}>
                      {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
