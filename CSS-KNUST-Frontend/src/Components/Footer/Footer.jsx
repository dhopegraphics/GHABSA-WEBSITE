import { ArrowRight, FlaskConical, Mail, MapPin } from "lucide-react";
import { Link } from "react-router-dom";

import { SocialLinks } from "./SocialLinks";
import logo from "../../assets/logo.png";
import { BRAND, EMAILS } from "../../config/brand";

const footerGroups = [
  {
    title: "Explore",
    links: [
      { label: "Academic resources", href: "/#resources" },
      { label: "Events", to: "/events" },
      { label: "Internships", to: "/internships" },
      { label: "News & stories", to: "/blogs?page=1" },
      { label: "Merchandise", to: "/purchase-merchandise" },
    ],
  },
  {
    title: "Our society",
    links: [
      { label: "Our history", to: "/history" },
      { label: "Executives", to: "/executives" },
      { label: "Department & staff", to: "/staff" },
      { label: "Projects", to: "/projects" },
      { label: "Current administration", to: "/current-administration" },
    ],
  },
  {
    title: "Support",
    links: [
      { label: "Contact us", to: "/contact-us" },
      { label: "Freshers help desk", to: "/admission?tab=helpdesk" },
      { label: "Frequently asked questions", to: "/faq" },
      { label: "Support the society", to: "/donate" },
    ],
  },
];

const FooterLink = ({ link }) => {
  const className = "group inline-flex items-center gap-2 text-sm text-slate-300 transition-colors hover:text-white";
  const content = (
    <>
      <span>{link.label}</span>
      <ArrowRight className="h-3.5 w-3.5 -translate-x-1 opacity-0 transition-all group-hover:translate-x-0 group-hover:opacity-100" />
    </>
  );

  return link.to ? (
    <Link to={link.to} className={className}>{content}</Link>
  ) : (
    <a href={link.href} className={className}>{content}</a>
  );
};

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative overflow-hidden bg-[#06142b] text-white">
      <div className="pointer-events-none absolute -right-32 top-20 h-[420px] w-[420px] rounded-full border-[70px] border-blue-500/[0.06]" />
      <div className="pointer-events-none absolute bottom-0 left-[12%] h-52 w-52 rounded-full bg-blue-600/10 blur-[100px]" />

      <div className="relative mx-auto max-w-7xl px-5 pb-8 pt-6 sm:px-8 lg:px-10">
        <section className="relative -mt-1 overflow-hidden rounded-[30px] border border-white/10 bg-[#0d2852] px-6 py-9 sm:px-9 lg:grid lg:grid-cols-[1fr_0.85fr] lg:items-center lg:gap-12 lg:px-12 lg:py-11">
          <div className="absolute -right-10 -top-20 h-56 w-56 rounded-full border-[35px] border-white/[0.04]" />
          <div className="relative">
            <h2 className="max-w-xl text-3xl font-semibold leading-tight tracking-[-0.035em] sm:text-4xl">Good opportunities should find you.</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300 sm:text-base">Get important society updates, upcoming events and new academic opportunities in one useful email.</p>
          </div>

          <form className="relative mt-7 flex flex-col gap-3 sm:flex-row lg:mt-0" onSubmit={(event) => event.preventDefault()}>
            <label htmlFor="footer-email" className="sr-only">Email address</label>
            <input
              id="footer-email"
              type="email"
              required
              placeholder="you@example.com"
              className="min-w-0 flex-1 rounded-full border border-white/15 bg-white/10 px-5 py-4 text-sm text-white outline-none placeholder:text-slate-400 focus:border-blue-300 focus:ring-2 focus:ring-blue-300/20"
            />
            <button type="submit" className="inline-flex items-center justify-center gap-2 rounded-full bg-lime-300 px-6 py-4 text-sm font-semibold text-[#06142b] hover:bg-lime-200">
              Subscribe <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </section>

        <div className="grid gap-12 py-16 md:grid-cols-2 lg:grid-cols-[1.35fr_2fr] lg:gap-20 lg:py-20">
          <div>
            <Link to="/" className="inline-flex items-center gap-3">
              <span className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-2xl bg-white p-1 shadow-lg shadow-black/20">
                <img src={logo} className="h-full w-full object-contain" alt={`${BRAND.shortName} logo`} />
              </span>
              <span>
                <span className="block text-xs font-medium uppercase tracking-[0.2em] text-blue-300">KNUST</span>
                <span className="mt-1 block text-xl font-semibold">{BRAND.shortLabel}</span>
              </span>
            </Link>

            <p className="mt-6 max-w-md text-sm leading-7 text-slate-400">{BRAND.tagline}</p>

            <div className="mt-7 space-y-3 border-l border-white/10 pl-4 text-sm">
              <a href={`mailto:${EMAILS.info}`} className="flex items-center gap-3 text-slate-300 hover:text-white">
                <Mail className="h-4 w-4 text-blue-300" /> {EMAILS.info}
              </a>
              <p className="flex items-start gap-3 text-slate-300">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-blue-300" />
                Biochemistry Department, KNUST<br />Kumasi, Ghana
              </p>
            </div>

            <div className="mt-7"><SocialLinks /></div>
          </div>

          <nav aria-label="Footer navigation" className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3">
            {footerGroups.map((group) => (
              <div key={group.title}>
                <h3 className="mb-5 text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">{group.title}</h3>
                <ul className="space-y-3.5">
                  {group.links.map((link) => <li key={link.label}><FooterLink link={link} /></li>)}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        <div className="flex flex-col gap-5 border-t border-white/10 pt-7 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© {currentYear} {BRAND.fullName}. All rights reserved.</p>
          <div className="flex items-center gap-2 text-slate-400">
            <FlaskConical className="h-4 w-4 text-lime-300" />
            <span>Learn · Connect · Become</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
