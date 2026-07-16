import { useContext } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowDown,
  ArrowUpRight,
  BookOpen,
  BriefcaseBusiness,
  CalendarDays,
  ChevronRight,
  FlaskConical,
  HeartHandshake,
  Microscope,
  Sparkles,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";

import Navbar from "../Components/Navbar";
import { EventsTimeline } from "../Components/Events/EventsTimeline";
import { ResourcesSection } from "../Components/Resources/ResourcesSection";
import { InternshipsSection } from "../Components/Internships/InternshipsSection";
import { BlogSection } from "../Components/Blog/BlogSection";
import { TeamSection } from "../Components/Team/TeamSection";
import { Footer } from "../Components/Footer/Footer";
import { UserContext } from "../Context/UserContext";
import { useAuthModals } from "../Context/AuthModalsContext";
import heroImage from "../assets/hero.png";
import communityImage from "../assets/cs3.jpg";

const pathways = [
  {
    icon: BookOpen,
    label: "Study smarter",
    title: "Academic resources",
    description: "Course materials, guides and resources organised for every year.",
    href: "/#resources",
    color: "bg-blue-600",
  },
  {
    icon: CalendarDays,
    label: "Stay involved",
    title: "Events & workshops",
    description: "Find the next seminar, social, workshop or society experience.",
    to: "/events",
    color: "bg-violet-600",
  },
  {
    icon: BriefcaseBusiness,
    label: "Build your future",
    title: "Career opportunities",
    description: "Explore internships and practical opportunities beyond the lecture hall.",
    to: "/internships",
    color: "bg-emerald-600",
  },
  {
    icon: HeartHandshake,
    label: "Find your people",
    title: "Community & support",
    description: "Meet, learn and grow with a community built around student success.",
    to: "/contact-us",
    color: "bg-orange-500",
  },
];

const reveal = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

function HomePage() {
  const { user } = useContext(UserContext);
  const { openLoginModal } = useAuthModals();
  const navigate = useNavigate();

  const handlePrimaryAction = () => {
    if (user) navigate("/dashboard/home");
    else openLoginModal();
  };

  return (
    <>
      <Helmet>
        <title>Home | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="The home of Biochemistry students at KNUST—academic resources, events, opportunities and community."
        />
        <meta name="keywords" content="Biochemistry Society KNUST, biochem KNUST, student resources, KNUST events" />
        <meta name="robots" content="index, follow" />
        <meta property="og:title" content="BIO-CHEM KNUST — Discover more together" />
        <meta property="og:description" content="Learn, connect and grow with the Biochemistry Society, KNUST." />
        <meta property="og:image" content="https://biochemknust.com/images/logo.png" />
        <meta property="og:url" content="https://biochemknust.com/" />
      </Helmet>

      <main className="overflow-hidden bg-[#f7f8fa] text-slate-950">
        <Navbar />

        <section className="relative min-h-[760px] bg-[#07162f] pt-[60px] text-white sm:pt-[65px] md:pt-[70px] lg:min-h-screen lg:pt-[75px]">
          <img
            src={heroImage}
            alt="Biochemistry Society students at KNUST"
            className="absolute inset-0 h-full w-full object-cover object-center opacity-55"
          />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(4,15,35,0.98)_0%,rgba(4,15,35,0.82)_47%,rgba(4,15,35,0.3)_100%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_76%_35%,rgba(55,138,255,0.28),transparent_31%)]" />

          <div className="relative mx-auto flex min-h-[700px] max-w-7xl items-center px-5 py-16 sm:px-8 lg:min-h-[calc(100vh-75px)] lg:px-10">
            <motion.div
              initial="hidden"
              animate="visible"
              transition={{ staggerChildren: 0.12 }}
              className="max-w-3xl"
            >
              <motion.h1 variants={reveal} transition={{ duration: 0.7 }} className="max-w-3xl text-5xl font-semibold leading-[0.98] tracking-[-0.055em] sm:text-6xl lg:text-[88px]">
                Curious minds.
                <span className="block text-blue-400">Real discovery.</span>
              </motion.h1>

              <motion.p variants={reveal} transition={{ duration: 0.7 }} className="mt-7 max-w-xl text-base leading-7 text-slate-200 sm:text-lg sm:leading-8">
                Your student society for academic support, practical opportunities and the people who make the Biochemistry journey worth sharing.
              </motion.p>

              <motion.div variants={reveal} transition={{ duration: 0.7 }} className="mt-9 flex flex-col gap-3 sm:flex-row">
                <button onClick={handlePrimaryAction} className="group inline-flex items-center justify-center gap-3 rounded-full bg-blue-500 px-7 py-4 font-semibold text-white shadow-[0_14px_40px_rgba(37,99,235,0.35)] hover:bg-blue-400">
                  {user ? "Open your dashboard" : "Join the community"}
                  <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </button>
                <a href="#explore" className="inline-flex items-center justify-center gap-3 rounded-full border border-white/25 bg-white/10 px-7 py-4 font-semibold backdrop-blur-md hover:bg-white/15">
                  Explore the society
                  <ArrowDown className="h-5 w-5" />
                </a>
              </motion.div>

              <motion.div variants={reveal} transition={{ duration: 0.7 }} className="mt-12 flex flex-wrap gap-x-8 gap-y-4 border-t border-white/15 pt-6 text-sm text-slate-300">
                <span className="flex items-center gap-2"><Users className="h-4 w-4 text-lime-300" /> Student-led</span>
                <span className="flex items-center gap-2"><Microscope className="h-4 w-4 text-lime-300" /> Science-driven</span>
                <span className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-lime-300" /> Future-focused</span>
              </motion.div>
            </motion.div>
          </div>

          <div className="absolute bottom-0 right-0 hidden rounded-tl-[36px] border-l border-t border-white/15 bg-white/10 px-8 py-6 backdrop-blur-xl lg:block">
            <p className="mt-1 text-lg font-semibold">Learn · Connect · Become</p>
          </div>
        </section>

        <section id="explore" className="relative py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="grid gap-8 lg:grid-cols-[0.75fr_1.25fr] lg:items-end">
              <div>
                <h2 className="text-4xl font-semibold leading-tight tracking-[-0.04em] sm:text-5xl">Everything you need to move forward.</h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600 lg:justify-self-end">
                No hunting through different platforms. The essentials of student life are organised into four clear paths.
              </p>
            </div>

            <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {pathways.map(({ icon: Icon, label, title, description, to, href, color }, index) => {
                const cardClass = "group flex min-h-[330px] flex-col rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_12px_45px_rgba(15,23,42,0.05)] hover:-translate-y-1 hover:border-blue-200 hover:shadow-[0_20px_55px_rgba(15,23,42,0.1)]";
                const content = (
                  <>
                    <div className={`flex h-12 w-12 items-center justify-center rounded-2xl text-white ${color}`}><Icon className="h-6 w-6" /></div>
                    <p className="mt-8 text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">0{index + 1} · {label}</p>
                    <h3 className="mt-3 text-xl font-semibold tracking-tight">{title}</h3>
                    <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
                    <span className="mt-auto flex items-center justify-between pt-7 text-sm font-semibold text-blue-700">Explore <ChevronRight className="h-5 w-5 transition-transform group-hover:translate-x-1" /></span>
                  </>
                );
                return to ? <Link key={title} to={to} className={cardClass}>{content}</Link> : <a key={title} href={href} className={cardClass}>{content}</a>;
              })}
            </div>
          </div>
        </section>

        <section className="px-5 pb-20 sm:px-8 sm:pb-28 lg:px-10">
          <div className="mx-auto grid max-w-7xl overflow-hidden rounded-[36px] bg-[#0b2347] text-white lg:grid-cols-2">
            <div className="relative min-h-[380px] lg:min-h-[570px]">
              <img src={communityImage} alt="Students building community at KNUST" className="absolute inset-0 h-full w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#07162f]/80 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-white/20 bg-white/10 p-5 backdrop-blur-md sm:bottom-8 sm:left-8 sm:right-auto sm:max-w-xs">
                <p className="text-sm leading-6 text-slate-100">“The society should feel like the place where your academic life and your people meet.”</p>
              </div>
            </div>
            <div className="flex flex-col justify-center p-7 sm:p-12 lg:p-16">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-lime-300 text-[#07162f]"><FlaskConical className="h-6 w-6" /></div>
              <h2 className="mt-8 text-4xl font-semibold leading-tight tracking-[-0.04em] sm:text-5xl">Science grows through community.</h2>
              <p className="mt-6 text-base leading-8 text-slate-300">We connect Biochemistry students with the knowledge, experiences and relationships that turn a demanding degree into a meaningful journey—from first year to final year and beyond.</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/history" className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 font-semibold text-[#07162f] hover:bg-blue-50">Our story <ArrowUpRight className="h-4 w-4" /></Link>
                <Link to="/projects" className="inline-flex items-center gap-2 rounded-full border border-white/25 px-6 py-3 font-semibold hover:bg-white/10">See our impact</Link>
              </div>
            </div>
          </div>
        </section>

        <div className="home-live-content bg-white">
          <EventsTimeline />
          <ResourcesSection />
          <InternshipsSection />
          <BlogSection />
          <TeamSection />
        </div>

        <section className="bg-white px-5 pb-20 sm:px-8 sm:pb-28 lg:px-10">
          <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[36px] bg-blue-600 px-7 py-14 text-white sm:px-12 lg:flex lg:items-center lg:justify-between lg:px-16 lg:py-16">
            <div className="absolute -right-20 -top-32 h-80 w-80 rounded-full border-[48px] border-white/10" />
            <div className="relative max-w-2xl">
              <h2 className="text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">Make your society experience count.</h2>
            </div>
            <button onClick={handlePrimaryAction} className="relative mt-8 inline-flex items-center gap-3 rounded-full bg-lime-300 px-7 py-4 font-semibold text-[#07162f] hover:bg-lime-200 lg:mt-0">
              {user ? "Go to dashboard" : "Become a member"}<ArrowUpRight className="h-5 w-5" />
            </button>
          </div>
        </section>

        <Footer />
      </main>
    </>
  );
}

export default HomePage;
