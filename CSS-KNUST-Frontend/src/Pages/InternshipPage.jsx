import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
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
import { Briefcase, Calendar } from "lucide-react";

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
        <title>Internships | CSS KNUST</title>
        <meta
          name="description"
          content="Find internship opportunities curated by the Computer Science Society of KNUST. Build experience and boost your career."
        />
        <meta
          name="keywords"
          content="CSS KNUST internships, KNUST tech internships, computer science internships Ghana"
        />
        <meta name="robots" content="index, follow" />
        <meta property="og:title" content="CSS KNUST - Internships" />
        <meta
          property="og:description"
          content="Explore top internship opportunities for Computer Science students."
        />
        <meta
          property="og:image"
          content="https://thecssknust.com/images/css.png"
        />
        <meta property="og:url" content="https://thecssknust.com/internships" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "EducationalOccupationalProgram",
            name: "CSS KNUST - Internships",
            provider: {
              "@type": "CollegeOrUniversity",
              name: "Computer Science Society, KNUST",
              url: "https://thecssknust.com",
            },
            description:
              "Curated internship listings and programs for KNUST Computer Science students.",
            educationalProgramMode: "online",
            occupationalCategory: "Information Technology",
          })}
        </script>
      </Helmet>

      <div className="relative mt-[70px]">
        <Navbar onSignInClick={handleOpenLoginModal} />
        <div className="max-w-7xl mx-auto px-4 py-16">
          <motion.h1
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
          >
            Browse{" "}
            <span className="relative text-blue-600">
              {" "}
              Internships
              <motion.div
                variants={underlineAnimation(0.7)}
                initial="offscreen"
                whileInView="onscreen"
                exit="reverse"
                className="absolute left-0 bottom-0 h-1 bg-blue-600"
                style={{ width: "0%", height: "3px" }}
              />
            </span>
          </motion.h1>
          <p className="text-center text-gray-600 mb-12">
            Explore exciting internship opportunities that empower you to learn,
            grow, and make an impact. Gain real-world experience and take the
            first step toward a bright future.
          </p>

          {!internships ? (
            // Loading state
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {Array.from({ length: 8 }).map((_, index) => (
                <InternshipCardSkeleton key={index} />
              ))}
            </div>
          ) : hasInternships ? (
            // Has internships - show grid
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
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
              className="text-center py-16 px-4"
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
        </div>
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
