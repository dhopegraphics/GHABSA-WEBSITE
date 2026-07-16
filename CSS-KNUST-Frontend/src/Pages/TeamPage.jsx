import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import Login from "./Login";
import { getData } from "../utils/apiHandler";
import { TeamCard } from "../Components/Team/TeamCard";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { useNavigate } from "react-router-dom";
import ExecutiveLogin from "./ExecutiveLogin";
import { useTeam } from "../Context/TeamContext";
import { TeamCardSkeleton } from "../Components/Team/TeamCardSkeleton";

export function TeamPage() {
  const { team, setTeam } = useTeam();
  const [pastExecutives, setPastExecutives] = useState([]);
  const [availableYears, setAvailableYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState("");
  const [loading, setLoading] = useState(false);
  const [pastLoading, setPastLoading] = useState(false);

  const fetchTeam = async () => {
    setLoading(true);
    const { response, error } = await getData("/executives/");
    if (error) {
      console.error("Error fetching Team:", error);
    }
    if (response) {
      setTeam(response?.filter((i) => i?.is_active == true));
    }
    setLoading(false);
  };

  const fetchAvailableYears = async () => {
    const { response, error } = await getData("/executives/years/");
    if (error) {
      console.error("Error fetching years:", error);
    }
    if (response && response.years) {
      setAvailableYears(response.years);
      if (response.years.length > 0) {
        setSelectedYear(response.years[0]); // Set first year as default
      }
    }
  };

  const fetchPastExecutivesByYear = async (year) => {
    if (!year) return;
    setPastLoading(true);
    const { response, error } = await getData(`/executives/year/${year}/`);
    if (error) {
      console.error("Error fetching past executives:", error);
    }
    if (response) {
      // Filter out active executives from past section
      setPastExecutives(response.filter((i) => i?.is_active === false));
    }
    setPastLoading(false);
  };

  useEffect(() => {
    fetchTeam();
    fetchAvailableYears();
    scrollToTop();
  }, []);

  useEffect(() => {
    if (selectedYear) {
      fetchPastExecutivesByYear(selectedYear);
    }
  }, [selectedYear]);

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
    <div className="relative mt-[70px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <div className="max-w-7xl mx-auto px-4 py-16">
        {/* Current Executives Section */}
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
        >
          Current{" "}
          <span className="relative text-blue-600">
            {" "}
            Executives
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
          Guided by innovation, expertise, and a shared commitment to
          excellence, our executive team leads the way in shaping our future.
          Each member brings a wealth of experience and a passion for driving
          progress, ensuring we stay true to our mission while embracing
          opportunities to grow and evolve.
        </p>

        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
          {loading ? (
            Array.from({ length: 4 }).map((_, index) => (
              <TeamCardSkeleton key={index} />
            ))
          ) : team?.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-500 text-lg">
                No current executives at the moment
              </p>
            </div>
          ) : (
            team?.map((member) => (
              <TeamCard
                key={member?.executive_id}
                imageUrl={member?.image}
                name={member?.executive_name}
                role={member?.position?.name}
                socialLinks={member?.social_media_links}
              />
            ))
          )}
        </ul>

        {/* Past Executives Section */}
        {availableYears.length > 0 && (
          <>
            <motion.h2
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-3xl md:text-4xl mb-8 font-bold text-gray-900 text-center mt-16"
            >
              Past{" "}
              <span className="relative text-blue-600">
                {" "}
                Executives
                <motion.div
                  variants={underlineAnimation(0.7)}
                  initial="offscreen"
                  whileInView="onscreen"
                  exit="reverse"
                  className="absolute left-0 bottom-0 h-1 bg-blue-600"
                  style={{ width: "0%", height: "3px" }}
                />
              </span>
            </motion.h2>

            <div className="flex justify-center mb-8">
              <div className="relative inline-block">
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  className="appearance-none bg-white border-2 border-blue-600 text-gray-900 py-3 px-6 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer hover:bg-blue-50 transition-all duration-200 font-medium"
                >
                  {availableYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-blue-600">
                  <svg
                    className="fill-current h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                  >
                    <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                  </svg>
                </div>
              </div>
            </div>

            <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {pastLoading ? (
                Array.from({ length: 4 }).map((_, index) => (
                  <TeamCardSkeleton key={index} />
                ))
              ) : pastExecutives?.length === 0 ? (
                <div className="col-span-full text-center py-12">
                  <p className="text-gray-500 text-lg">
                    No past executives found for {selectedYear}
                  </p>
                </div>
              ) : (
                pastExecutives?.map((member) => (
                  <TeamCard
                    key={member?.executive_id}
                    imageUrl={member?.image}
                    name={member?.executive_name}
                    role={member?.position?.name}
                    socialLinks={member?.social_media_links}
                  />
                ))
              )}
            </ul>
          </>
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
  );
}
