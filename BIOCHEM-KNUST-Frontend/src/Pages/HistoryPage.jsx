import { useState, useEffect } from "react";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";
import {
  getSocietyHistory,
  getAvailableYears,
  getExecutivesByYear,
  getAppointeesByParams,
} from "../utils/executivesApi";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { getOptimizedImageUrl, IMAGE_PRESETS } from "../utils/imageUtils";
import { Helmet } from "react-helmet-async";
import {
  Calendar,
  Users,
  Award,
  GraduationCap,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import Login from "./Login";
import SignUp from "./SignUp";
import { useNavigate } from "react-router-dom";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";

const categoryIcons = {
  founding: Sparkles,
  administration: Users,
  milestone: Award,
  achievement: Award,
  event: Calendar,
  lecture: GraduationCap,
};

const categoryColors = {
  founding: "from-amber-500 to-orange-600",
  administration: "from-blue-500 to-indigo-600",
  milestone: "from-purple-500 to-pink-600",
  achievement: "from-green-500 to-emerald-600",
  event: "from-red-500 to-rose-600",
  lecture: "from-cyan-500 to-teal-600",
};

const categories = [
  { value: "all", label: "All History" },
  { value: "founding", label: "Founding & Early Years" },
  { value: "administration", label: "Past Administrations" },
  { value: "milestone", label: "Major Milestones" },
  { value: "achievement", label: "Notable Achievements" },
  { value: "event", label: "Historic Events" },
  { value: "lecture", label: "Past Lecturers" },
];

export default function HistoryPage() {
  const [histories, setHistories] = useState([]);
  const [filteredHistories, setFilteredHistories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [expandedHistory, setExpandedHistory] = useState(null);
  // Past administrations state
  const [adminYears, setAdminYears] = useState([]);
  const [selectedAdminYear, setSelectedAdminYear] = useState(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminExecutives, setAdminExecutives] = useState([]);
  const [adminAppointees, setAdminAppointees] = useState([]);

  useEffect(() => {
    // load history and admin years once on mount
    (async () => {
      setLoading(true);
      const { data } = await getSocietyHistory();
      if (data) {
        setHistories(data);
        setFilteredHistories(data);
      }
      setLoading(false);

      const { data: yearsData } = await getAvailableYears();
      if (yearsData && yearsData.years) {
        const years = yearsData.years;
        // Exclude the current academic year entirely from past-administrations dropdown
        const now = new Date();
        const currentAcademicYear = `${now.getFullYear()}/${
          now.getFullYear() + 1
        }`;
        const pastYears = years.filter((y) => y !== currentAcademicYear);
        setAdminYears(pastYears);

        if (!selectedAdminYear && pastYears.length > 0) {
          // default to the most recent available past year
          setSelectedAdminYear(pastYears[0]);
        } else if (!selectedAdminYear) {
          // no past years available
          setSelectedAdminYear(null);
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedAdminYear) {
      fetchAdministrationByYear(selectedAdminYear);
    }
  }, [selectedAdminYear]);

  useEffect(() => {
    if (selectedCategory === "all") {
      setFilteredHistories(histories);
    } else {
      const filtered = histories.filter((h) => h.category === selectedCategory);
      setFilteredHistories(filtered);
    }
  }, [selectedCategory, histories]);

  const fetchAdministrationByYear = async (year) => {
    setAdminLoading(true);
    const { data: execData } = await getExecutivesByYear(year);
    const { data: appData } = await getAppointeesByParams(year, true);

    // Only include past (inactive) executives/appointees for the selected year
    const pastExecs = (execData || []).filter((e) => e.is_active === false);
    const pastApps = (appData || []).filter((a) => a.is_active === false);

    setAdminExecutives(pastExecs);
    setAdminAppointees(pastApps);
    setAdminLoading(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const toggleExpanded = (historyId) => {
    setExpandedHistory(expandedHistory === historyId ? null : historyId);
  };

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
        <title>History | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Explore the rich history of the Biochemistry Society, KNUST. Journey through decades of excellence, innovation, and community. Learn about our founding, past administrations, milestones, and achievements."
        />
        <meta
          name="keywords"
          content="BIO-CHEM KNUST history, past administrations, founding members, milestones, achievements, historic events, past lecturers, KNUST CS legacy"
        />
        <meta name="author" content="BIO-CHEM KNUST" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://biochemknust.com/history" />
        <meta property="og:title" content="History | BIO-CHEM KNUST" />
        <meta
          property="og:description"
          content="Journey through the decades of excellence, innovation, and community that define the Biochemistry Society, KNUST."
        />
        <meta
          property="og:image"
          content="https://biochemknust.com/og-history.jpg"
        />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content="https://biochemknust.com/history" />
        <meta name="twitter:title" content="History | BIO-CHEM KNUST" />
        <meta
          name="twitter:description"
          content="Journey through the decades of excellence, innovation, and community that define BIO-CHEM KNUST."
        />
        <meta
          name="twitter:image"
          content="https://biochemknust.com/og-history.jpg"
        />

        {/* Additional Meta */}
        <link rel="canonical" href="https://biochemknust.com/history" />
        <meta name="robots" content="index, follow" />
        <meta name="language" content="English" />
        <meta name="revisit-after" content="14 days" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
        <Navbar onSignInClick={handleOpenLoginModal} />

        {/* Hero Section */}
        <section className="relative pt-32 pb-20 px-4 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 opacity-10"></div>
          <div className="max-w-7xl mx-auto text-center relative z-10">
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-5xl md:text-7xl mb-6 font-bold text-gray-900"
            >
              Our Rich{" "}
              <span className="relative text-blue-600">
                History
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
            <p className="text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto">
              Journey through the decades of excellence, innovation, and
              community that define the Biochemistry Society, KNUST
            </p>
          </div>
        </section>

        {/* Category Filter */}
        <section className="py-8 px-4 sticky top-20 z-40 bg-white/80 backdrop-blur-lg shadow-md">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-wrap gap-3 justify-center">
              {categories.map((category) => (
                <button
                  key={category.value}
                  onClick={() => setSelectedCategory(category.value)}
                  className={`px-6 py-3 rounded-full font-semibold transition-all duration-300 transform hover:scale-105 ${
                    selectedCategory === category.value
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg"
                      : "bg-white text-gray-700 hover:bg-gray-100 shadow-md"
                  }`}
                >
                  {category.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* History Timeline or Past Administrations */}
        <section className="py-16 px-4">
          <div className="max-w-6xl mx-auto">
            {selectedCategory === "administration" ? (
              // Past Administrations view
              adminLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600"></div>
                </div>
              ) : adminExecutives.length === 0 &&
                adminAppointees.length === 0 ? (
                <div className="text-center py-20">
                  <p className="text-2xl text-gray-600">
                    No past administration data found for {selectedAdminYear}.
                  </p>
                </div>
              ) : (
                <div>
                  <div className="flex justify-center mb-8">
                    <div className="relative inline-block">
                      <select
                        value={selectedAdminYear || ""}
                        onChange={(e) => setSelectedAdminYear(e.target.value)}
                        className="appearance-none bg-white border-2 border-blue-600 text-gray-900 py-3 px-6 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer hover:bg-blue-50 transition-all duration-200 font-medium"
                      >
                        {adminYears.map((year) => (
                          <option key={year} value={year}>
                            {year}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Past Executives */}
                  {adminExecutives && adminExecutives.length > 0 && (
                    <div className="mb-12">
                      <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
                        Past Executives — {selectedAdminYear}
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {adminExecutives.map((member) => (
                          <div
                            key={member.executive_id}
                            className="bg-white rounded-2xl shadow p-4"
                          >
                            <div className="relative h-56 rounded overflow-hidden">
                              <img
                                src={getOptimizedImageUrl(
                                  member.image || "/images/default-profile.png",
                                  IMAGE_PRESETS.card
                                )}
                                alt={member.executive_name}
                                className="w-full h-full object-cover object-top"
                                loading="lazy"
                              />
                              <div className="absolute bottom-4 left-4 text-white">
                                <h3 className="text-lg font-bold">
                                  {member.executive_name}
                                </h3>
                                <p className="text-sm">
                                  {member.position?.name}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Past Appointees */}
                  {adminAppointees && adminAppointees.length > 0 && (
                    <div>
                      <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
                        Past Appointees — {selectedAdminYear}
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {adminAppointees.map((app) => (
                          <div
                            key={app.appointee_id}
                            className="bg-white rounded-2xl shadow p-4"
                          >
                            <div className="relative h-56 rounded overflow-hidden">
                              <img
                                src={getOptimizedImageUrl(
                                  app.image || "/images/default-profile.png",
                                  IMAGE_PRESETS.card
                                )}
                                alt={app.appointee_name}
                                className="w-full h-full object-cover object-top"
                                loading="lazy"
                              />
                              <div className="absolute bottom-4 left-4 text-white">
                                <h3 className="text-lg font-bold">
                                  {app.appointee_name}
                                </h3>
                                <p className="text-sm">
                                  {app.committee_name} — {app.role}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            ) : loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600"></div>
              </div>
            ) : filteredHistories.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-2xl text-gray-600">
                  No history records found for this category.
                </p>
              </div>
            ) : (
              <div className="relative">
                {/* Timeline Line */}
                <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-400 via-indigo-500 to-purple-600 transform md:-translate-x-1/2"></div>

                {filteredHistories.map((history, index) => {
                  const Icon = categoryIcons[history.category] || Calendar;
                  const isExpanded = expandedHistory === history.history_id;
                  const isEven = index % 2 === 0;

                  return (
                    <div
                      key={history.history_id}
                      className={`relative mb-12 ${
                        isEven ? "md:pr-1/2" : "md:pl-1/2 md:text-right"
                      }`}
                    >
                      {/* Timeline Dot */}
                      <div
                        className={`absolute left-8 md:left-1/2 transform ${
                          isEven ? "md:-translate-x-1/2" : "md:-translate-x-1/2"
                        } -translate-y-1/2 top-8`}
                      >
                        <div
                          className={`w-16 h-16 rounded-full bg-gradient-to-br ${
                            categoryColors[history.category]
                          } flex items-center justify-center shadow-lg`}
                        >
                          <Icon className="w-8 h-8 text-white" />
                        </div>
                      </div>

                      {/* Content Card */}
                      <div
                        className={`ml-24 md:ml-0 ${
                          isEven ? "md:mr-16" : "md:ml-16"
                        }`}
                      >
                        <div className="bg-white rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2">
                          {history.image && (
                            <div className="h-64 overflow-hidden">
                              <img
                                src={history.image}
                                alt={history.title}
                                className="w-full h-full object-cover"
                              />
                            </div>
                          )}
                          <div className="p-6">
                            <div className="flex items-center gap-3 mb-3">
                              {history.session_year && (
                                <span className="px-4 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                                  {history.session_year}
                                </span>
                              )}
                              <span
                                className={`px-4 py-1 bg-gradient-to-r ${
                                  categoryColors[history.category]
                                } text-white rounded-full text-sm font-semibold`}
                              >
                                {
                                  categories.find(
                                    (c) => c.value === history.category
                                  )?.label
                                }
                              </span>
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900 mb-3">
                              {history.title}
                            </h3>
                            {history.start_date && (
                              <p className="text-gray-600 mb-4 flex items-center gap-2">
                                <Calendar className="w-5 h-5" />
                                {formatDate(history.start_date)}
                                {history.end_date &&
                                  ` - ${formatDate(history.end_date)}`}
                              </p>
                            )}
                            <p
                              className={`text-gray-700 leading-relaxed ${
                                !isExpanded && "line-clamp-3"
                              }`}
                            >
                              {history.description}
                            </p>
                            {history.description.length > 200 && (
                              <button
                                onClick={() =>
                                  toggleExpanded(history.history_id)
                                }
                                className="mt-3 text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-2"
                              >
                                {isExpanded ? "Read Less" : "Read More"}
                                <ChevronDown
                                  className={`w-5 h-5 transition-transform ${
                                    isExpanded ? "rotate-180" : ""
                                  }`}
                                />
                              </button>
                            )}

                            {/* Leaders */}
                            {history.leaders && history.leaders.length > 0 && (
                              <div className="mt-6 pt-6 border-t border-gray-200">
                                <h4 className="text-lg font-bold text-gray-900 mb-4">
                                  Key Figures
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  {history.leaders.map((leader) => (
                                    <div
                                      key={leader.leader_id}
                                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                                    >
                                      {leader.image && (
                                        <img
                                          src={leader.image}
                                          alt={leader.name}
                                          className="w-12 h-12 rounded-full object-cover"
                                        />
                                      )}
                                      <div>
                                        <p className="font-semibold text-gray-900">
                                          {leader.name}
                                        </p>
                                        <p className="text-sm text-gray-600">
                                          {leader.position}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
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
