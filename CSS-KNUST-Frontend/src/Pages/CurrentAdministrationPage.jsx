import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";
import ProfileModal from "../Components/ProfileModal";
import { getCurrentAdministration } from "../utils/executivesApi";
import { getOptimizedImageUrl, IMAGE_PRESETS } from "../utils/imageUtils";
import { Helmet } from "react-helmet-async";
import {
  Mail,
  Phone,
  MapPin,
  Clock,
  Linkedin,
  Twitter,
  Facebook,
  Instagram,
  Github,
  Users,
  Crown,
  Shield,
  ChevronRight,
  Search,
  Menu,
  X,
} from "lucide-react";
import Login from "./Login";
import SignUp from "./SignUp";
import { useNavigate } from "react-router-dom";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";

/* eslint-disable react/prop-types */

const socialIcons = {
  linkedin: Linkedin,
  twitter: Twitter,
  facebook: Facebook,
  instagram: Instagram,
  github: Github,
};

const getRoleColor = (role) => {
  switch (role) {
    case "head":
      return "from-amber-500 to-orange-600";
    case "deputy_head":
      return "from-blue-500 to-indigo-600";
    default:
      return "from-gray-500 to-gray-700";
  }
};

const getRoleIcon = (role) => {
  switch (role) {
    case "head":
      return Crown;
    case "deputy_head":
      return Shield;
    default:
      return Users;
  }
};

export default function CurrentAdministrationPage() {
  const [executives, setExecutives] = useState([]);
  const [committees, setCommittees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [modalType, setModalType] = useState(null);
  const [selectedCommittee, setSelectedCommittee] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    fetchAdministration();
  }, []);

  // Lock body scroll when mobile sidebar is open
  useEffect(() => {
    if (isSidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isSidebarOpen]);

  const fetchAdministration = async () => {
    setLoading(true);
    const { data } = await getCurrentAdministration();
    if (data) {
      setExecutives(data.executives || []);
      setCommittees(data.committees || []);
      // Auto-select first committee if available
      if (data.committees && data.committees.length > 0) {
        setSelectedCommittee(data.committees[0].committee_id);
      }
    }
    setLoading(false);
  };

  const openModal = (person, type) => {
    setSelectedPerson(person);
    setModalType(type);
    document.body.style.overflow = "hidden"; // Prevent background scrolling
  };

  const closeModal = () => {
    setSelectedPerson(null);
    setModalType(null);
    document.body.style.overflow = "unset";
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

  // Filter committees based on search term
  const filteredCommittees = committees.filter((committee) =>
    committee.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get currently selected committee data
  const currentCommittee = committees.find(
    (c) => c.committee_id === selectedCommittee
  );

  const ExecutiveCard = ({ executive }) => (
    <div
      className="bg-white rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 cursor-pointer"
      onClick={() => openModal(executive, "executive")}
    >
      <div className="relative h-64 sm:h-72">
        <img
          src={getOptimizedImageUrl(
            executive.image || "/images/default-profile.png",
            IMAGE_PRESETS.card
          )}
          alt={executive.executive_name}
          className="w-full h-full object-cover object-top"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent"></div>
        <div className="absolute bottom-4 left-4 right-4 text-white">
          <h3 className="text-xl sm:text-2xl font-bold mb-1">
            {executive.executive_name}
          </h3>
          <p className="text-base sm:text-lg font-semibold text-yellow-300">
            {executive.position?.name}
          </p>
        </div>
      </div>
      <div className="p-4 sm:p-6">
        {executive.phone && (
          <a
            href={`tel:${executive.phone}`}
            className="flex items-center gap-2 text-gray-700 hover:text-blue-600 mb-2 text-sm sm:text-base"
          >
            <Phone className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
            <span className="truncate">{executive.phone}</span>
          </a>
        )}
        {executive.social_media_links &&
          executive.social_media_links.length > 0 && (
            <div className="flex gap-2 sm:gap-3 mt-4">
              {executive.social_media_links.map((link) => {
                const Icon = socialIcons[link.platform.toLowerCase()] || null;
                return Icon ? (
                  <a
                    key={link.id}
                    href={link.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-100 hover:bg-blue-600 hover:text-white flex items-center justify-center transition-all duration-300"
                  >
                    <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
                  </a>
                ) : null;
              })}
            </div>
          )}
      </div>
    </div>
  );

  const AppointeeCard = ({ appointee, role }) => {
    const RoleIcon = getRoleIcon(role);
    const roleColor = getRoleColor(role);

    return (
      <div
        className={`bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer ${
          role === "member" ? "" : "transform hover:-translate-y-1"
        }`}
        onClick={() => openModal(appointee, "appointee")}
      >
        <div className="relative h-48">
          <img
            src={getOptimizedImageUrl(
              appointee.image || "/images/default-profile.png",
              IMAGE_PRESETS.card
            )}
            alt={appointee.appointee_name}
            className="w-full h-full object-cover object-top"
            loading="lazy"
          />
          <div
            className={`absolute top-2 right-2 px-3 py-1 rounded-full bg-gradient-to-r ${roleColor} text-white text-xs font-bold flex items-center gap-1`}
          >
            <RoleIcon className="w-4 h-4" />
            {role === "head"
              ? "Head"
              : role === "deputy_head"
              ? "Deputy"
              : "Member"}
          </div>
        </div>
        <div className="p-4">
          <h4 className="text-lg font-bold text-gray-900 mb-1">
            {appointee.appointee_name}
          </h4>
          {appointee.portfolio && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {appointee.portfolio}
            </p>
          )}

          {/* Contact Details */}
          {appointee.contact_details && (
            <div className="space-y-2 text-sm">
              {appointee.contact_details.email && (
                <a
                  href={`mailto:${appointee.contact_details.email}`}
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
                >
                  <Mail className="w-4 h-4" />
                  <span className="truncate">
                    {appointee.contact_details.email}
                  </span>
                </a>
              )}
              {appointee.contact_details.phone && (
                <a
                  href={`tel:${appointee.contact_details.phone}`}
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
                >
                  <Phone className="w-4 h-4" />
                  {appointee.contact_details.phone}
                </a>
              )}
              {appointee.contact_details.office_location && (
                <div className="flex items-center gap-2 text-gray-700">
                  <MapPin className="w-4 h-4" />
                  <span className="truncate">
                    {appointee.contact_details.office_location}
                  </span>
                </div>
              )}
              {appointee.contact_details.office_hours && (
                <div className="flex items-center gap-2 text-gray-700">
                  <Clock className="w-4 h-4" />
                  <span className="truncate">
                    {appointee.contact_details.office_hours}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Social Links */}
          {appointee.social_media_links &&
            appointee.social_media_links.length > 0 && (
              <div className="flex gap-2 mt-4">
                {appointee.social_media_links.map((link) => {
                  const Icon = socialIcons[link.platform.toLowerCase()] || null;
                  return Icon ? (
                    <a
                      key={link.id}
                      href={link.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-8 h-8 rounded-full bg-gray-100 hover:bg-blue-600 hover:text-white flex items-center justify-center transition-all duration-300"
                    >
                      <Icon className="w-4 h-4" />
                    </a>
                  ) : null;
                })}
              </div>
            )}
        </div>
      </div>
    );
  };

  return (
    <>
      <Helmet>
        <title>Current Administration | CSS KNUST</title>
        <meta
          name="description"
          content="Meet the current executives and committee members of the Computer Science Society of KNUST. Discover the leadership steering our society towards excellence."
        />
        <meta
          name="keywords"
          content="CSS KNUST executives, current administration, committee members, student leadership, KNUST CS society, executive board, committee heads"
        />
        <meta name="author" content="CSS KNUST" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cssknust.com/administration" />
        <meta
          property="og:title"
          content="Current Administration | CSS KNUST"
        />
        <meta
          property="og:description"
          content="Meet the dedicated team leading CSS KNUST into the future. Executive board and committee members."
        />
        <meta
          property="og:image"
          content="https://cssknust.com/og-administration.jpg"
        />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta
          name="twitter:url"
          content="https://cssknust.com/administration"
        />
        <meta
          name="twitter:title"
          content="Current Administration | CSS KNUST"
        />
        <meta
          name="twitter:description"
          content="Meet the dedicated team leading CSS KNUST into the future."
        />
        <meta
          name="twitter:image"
          content="https://cssknust.com/og-administration.jpg"
        />

        {/* Additional Meta */}
        <link rel="canonical" href="https://cssknust.com/administration" />
        <meta name="robots" content="index, follow" />
        <meta name="language" content="English" />
        <meta name="revisit-after" content="3 days" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
        <Navbar onSignInClick={handleOpenLoginModal} />

        {/* Hero Section */}
        <section className="relative pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 px-4 overflow-hidden">

          <div className="max-w-7xl mx-auto text-center relative z-10">
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl mb-4 sm:mb-6 font-bold text-gray-900 px-4"
            >
              Current{" "}
              <span className="relative text-blue-600">
                Administration
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
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-700 max-w-3xl mx-auto px-4">
              Meet the dedicated team leading CSS KNUST into the future
            </p>
          </div>
        </section>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Executives Section */}
            {executives.length > 0 && (
              <section className="py-12 md:py-16 px-4">
                <div className="max-w-7xl mx-auto">
                  <div className="text-center mb-8 md:mb-12">
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent mb-3 md:mb-4">
                      Executive Board
                    </h2>
                    <p className="text-lg md:text-xl text-gray-600 px-4">
                      The leadership steering our society towards excellence
                    </p>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
                    {executives.map((executive) => (
                      <ExecutiveCard
                        key={executive.executive_id}
                        executive={executive}
                      />
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* Committees Section */}
            {committees.length > 0 && (
              <section className="py-8 md:py-16 px-4 bg-white/50">
                <div className="max-w-7xl mx-auto">
                  <div className="text-center mb-8 md:mb-12">
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent mb-3 md:mb-4">
                      Committees
                    </h2>
                    <p className="text-lg md:text-xl text-gray-600 px-4">
                      Specialized teams driving our initiatives forward
                    </p>
                  </div>

                  {/* Search Bar & Mobile Toggle */}
                  <div className="mb-6 md:mb-8 space-y-4">
                    <div className="max-w-md mx-auto relative">
                      <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        type="text"
                        placeholder="Search committees..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-600 focus:outline-none transition-colors duration-300 text-sm md:text-base"
                      />
                    </div>
                    
                    {/* Mobile Committee Toggle Button */}
                    <div className="lg:hidden flex justify-center">
                      <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
                      >
                        {isSidebarOpen ? (
                          <>
                            <X className="w-5 h-5" />
                            Close Menu
                          </>
                        ) : (
                          <>
                            <Menu className="w-5 h-5" />
                            Select Committee
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 lg:gap-8">
                    {/* Committee List Sidebar */}
                    <div className="lg:col-span-1">
                      {/* Mobile Overlay */}
                      {isSidebarOpen && (
                        <div
                          className="lg:hidden fixed inset-0 bg-black/50 z-40"
                          onClick={() => setIsSidebarOpen(false)}
                        />
                      )}
                      
                      {/* Sidebar */}
                      <div
                        className={`
                          fixed lg:sticky top-0 lg:top-24 left-0 h-full lg:h-auto w-80 lg:w-auto
                          bg-white rounded-none lg:rounded-2xl shadow-2xl lg:shadow-xl
                          p-6 lg:p-4 z-50 lg:z-auto
                          transition-transform duration-300 ease-in-out
                          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                        `}
                      >
                        {/* Mobile Header */}
                        <div className="lg:hidden flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                          <h3 className="text-xl font-bold text-gray-900">
                            Select Committee
                          </h3>
                          <button
                            onClick={() => setIsSidebarOpen(false)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          >
                            <X className="w-6 h-6 text-gray-600" />
                          </button>
                        </div>
                        
                        <h3 className="hidden lg:block text-lg font-bold text-gray-900 mb-4 px-2">
                          All Committees
                        </h3>
                        <div className="space-y-2 max-h-[calc(100vh-200px)] lg:max-h-[600px] overflow-y-auto custom-scrollbar">
                          {filteredCommittees.map((committee) => (
                            <button
                              key={committee.committee_id}
                              onClick={() => {
                                setSelectedCommittee(committee.committee_id);
                                setIsSidebarOpen(false);
                              }}
                              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 flex items-center justify-between group ${
                                selectedCommittee === committee.committee_id
                                  ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg"
                                  : "hover:bg-gray-100 text-gray-700"
                              }`}
                            >
                              <span className="font-medium text-sm">
                                {committee.name}
                              </span>
                              <ChevronRight
                                className={`w-5 h-5 transition-transform duration-300 flex-shrink-0 ${
                                  selectedCommittee === committee.committee_id
                                    ? "transform translate-x-1"
                                    : ""
                                }`}
                              />
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Committee Details */}
                    <div className="lg:col-span-3">
                      <AnimatePresence mode="wait">
                        {currentCommittee && (
                          <motion.div
                            key={currentCommittee.committee_id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                            className="bg-white rounded-2xl lg:rounded-3xl shadow-2xl p-4 sm:p-6 md:p-8"
                          >
                            <div className="mb-6 md:mb-8">
                              <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 md:mb-3">
                                {currentCommittee.name}
                              </h3>
                              <p className="text-base md:text-lg text-gray-600">
                                {currentCommittee.description}
                              </p>
                            </div>

                            {/* Leadership - Head & Deputy Head */}
                            {(currentCommittee.head || currentCommittee.deputy_head) && (
                              <div className="mb-6 md:mb-8">
                                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                  <Crown className="w-5 h-5 md:w-6 md:h-6 text-amber-500" />
                                  Leadership
                                </h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6">
                                  {currentCommittee.head && (
                                    <div>
                                      <div className="text-sm font-semibold text-gray-600 mb-2 flex items-center gap-1">
                                        <Crown className="w-4 h-4 text-amber-500" />
                                        Committee Head
                                      </div>
                                      <AppointeeCard
                                        appointee={currentCommittee.head}
                                        role="head"
                                      />
                                    </div>
                                  )}
                                  {currentCommittee.deputy_head && (
                                    <div>
                                      <div className="text-sm font-semibold text-gray-600 mb-2 flex items-center gap-1">
                                        <Shield className="w-4 h-4 text-blue-500" />
                                        Deputy Head
                                      </div>
                                      <AppointeeCard
                                        appointee={currentCommittee.deputy_head}
                                        role="deputy_head"
                                      />
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Members */}
                            {currentCommittee.members &&
                              currentCommittee.members.length > 0 && (
                                <div>
                                  <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Users className="w-5 h-5 md:w-6 md:h-6 text-gray-500" />
                                    <span className="text-base md:text-xl">
                                      Committee Members (
                                      {currentCommittee.members.length})
                                    </span>
                                  </h4>
                                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                                    {currentCommittee.members.map((member) => (
                                      <AppointeeCard
                                        key={member.appointee_id}
                                        appointee={member}
                                        role="member"
                                      />
                                    ))}
                                  </div>
                                </div>
                              )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </>
        )}

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

      {/* Profile Modal */}
      {selectedPerson && (
        <ProfileModal
          person={selectedPerson}
          type={modalType}
          onClose={closeModal}
        />
      )}
    </>
  );
}
