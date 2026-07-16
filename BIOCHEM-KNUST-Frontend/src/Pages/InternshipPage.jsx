import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fadeIn } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import Login from "./Login";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { useNavigate } from "react-router-dom";
import ExecutiveLogin from "./ExecutiveLogin";
import { getData } from "../utils/apiHandler";
import { useInternships } from "../Context/InternshipsContext";
import { InternshipCard } from "../Components/Internships/InternshipCard";
import { InternshipCardSkeleton } from "../Components/Internships/InternshipCardSkeleton";
import { Helmet } from "react-helmet-async";
import { ArrowDown, Briefcase, Calendar, CheckCircle2, Search } from "lucide-react";

export function InternshipPage() {
  const { internships, setInternships } = useInternships();

  useEffect(() => {
    const fetchInternships = async () => {
      const { response, error } = await getData("/academics/internships/");
      if (error) {
        console.error("Error fetching internships:", error);
      }
      if (response) {
        // Backend already filters active internships
        setInternships(response);
      }
    };

    fetchInternships();
    scrollToTop();
  }, [setInternships]);

  const hasInternships = internships && internships.length > 0;
  const navigate = useNavigate();

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
    setIsExecutiveOpen(false);
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };
  return (
    <>
      <Helmet>
        <title>Internships | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Find internship opportunities curated by the Biochemistry Society, KNUST. Build experience and boost your career."
        />
        <meta
          name="keywords"
          content="BIO-CHEM KNUST internships, biochemistry internships Ghana, KNUST industrial training"
        />
        <meta name="robots" content="index, follow" />
        <meta property="og:title" content="BIO-CHEM KNUST - Internships" />
        <meta
          property="og:description"
          content="Explore top internship opportunities for Biochemistry students."
        />
        <meta
          property="og:image"
          content="https://biochemknust.com/images/logo.png"
        />
        <meta property="og:url" content="https://biochemknust.com/internships" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "EducationalOccupationalProgram",
            name: "BIO-CHEM KNUST - Internships",
            provider: {
              "@type": "CollegeOrUniversity",
              name: "Biochemistry Society, KNUST",
              url: "https://biochemknust.com",
            },
            description:
              "Curated internship listings and programs for KNUST Biochemistry students.",
            educationalProgramMode: "online",
            occupationalCategory: "Life, Physical, and Social Science",
          })}
        </script>
      </Helmet>

      <div className="relative bg-[#f5f7fa] pt-[60px] sm:pt-[65px] md:pt-[70px] lg:pt-[75px]">
        <Navbar onSignInClick={handleOpenLoginModal} />
        <header className="relative overflow-hidden bg-[#07162f] px-5 py-20 text-white sm:px-8 sm:py-24 lg:px-10 lg:py-28">
          <div className="absolute -right-24 -top-40 h-[430px] w-[430px] rounded-full border-[70px] border-emerald-400/10" />
          <div className="absolute bottom-0 left-[18%] h-56 w-56 rounded-full bg-emerald-500/15 blur-[100px]" />
          <div className="relative mx-auto max-w-7xl lg:flex lg:items-end lg:justify-between">
          <motion.div
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="max-w-4xl"
          >
            <h1 className="text-5xl font-semibold leading-[1.02] tracking-[-0.05em] sm:text-6xl lg:text-7xl">Experience starts <span className="text-emerald-400">before graduation.</span></h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">Discover research placements, industrial training and practical opportunities selected for Biochemistry students.</p>
            <div className="mt-8 flex flex-wrap gap-6 text-sm text-slate-300"><span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-lime-300" /> Curated opportunities</span><span className="flex items-center gap-2"><Calendar className="h-4 w-4 text-lime-300" /> Active deadlines only</span></div>
          </motion.div>
          <a href="#opportunities" className="mt-9 inline-flex items-center gap-3 rounded-full bg-lime-300 px-6 py-4 font-semibold text-[#07162f] hover:bg-lime-200 lg:mt-0">Browse opportunities <ArrowDown className="h-5 w-5" /></a>
          </div>
        </header>

        <section id="opportunities" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-28 lg:px-10">
          <div className="mb-12 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <div><h2 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">Open opportunities</h2><p className="mt-4 max-w-xl text-base leading-7 text-slate-600">Find the right next step and apply before the listed deadline.</p></div>
            {hasInternships && <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600"><Search className="h-4 w-4 text-emerald-700" />{internships.length} active listing{internships.length === 1 ? "" : "s"}</div>}
          </div>

          {!internships ? (
            // Loading state
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 8 }).map((_, index) => (
                <InternshipCardSkeleton key={index} />
              ))}
            </div>
          ) : hasInternships ? (
            // Has internships - show grid
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {internships.map((internship) => (
                <InternshipCard
                  key={internship.internship_id}
                  internship={internship}
                />
              ))}
            </div>
          ) : (
            // No active internships - show empty state
            <motion.div
              variants={fadeIn("up", 0.3, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="rounded-[32px] border border-slate-200 bg-white px-4 py-20 text-center shadow-[0_18px_55px_rgba(15,23,42,0.06)]"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-50 mb-6">
                <Briefcase className="w-10 h-10 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                No Active Internships Available
              </h2>
              <p className="text-gray-600 mb-2 max-w-md mx-auto">
                There are currently no active internship opportunities. Check
                back soon for new postings!
              </p>
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500 mt-4">
                <Calendar className="w-4 h-4" />
                <span>
                  Internships with past application deadlines are not displayed
                </span>
              </div>
            </motion.div>
          )}
        </section>
        <Footer />
        {isLoginModalOpen && (
          <Login
            onClose={handleCloseModals}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
            action={() => navigate("/dashboard/home")}
            switchToExecutive={handleExecutiveOpen}
          />
        )}

        {isSignupModalOpen && (
          <SignUp
            onClose={handleCloseModals}
            switchToLogin={handleOpenLoginModal}
          />
        )}
        {isOpen && (
          <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
        )}
        {isExecutiveOpen && (
          <ExecutiveLogin
            onClose={handleOpenLoginModal}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
          />
        )}
      </div>
    </>
  );
}
