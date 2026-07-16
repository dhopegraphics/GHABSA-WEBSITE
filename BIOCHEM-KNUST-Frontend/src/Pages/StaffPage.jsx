import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { Mail, MapPin, Award, BookOpen } from "lucide-react";
import { BACKEND_HOST } from "../utils/config";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";
import { Helmet } from "react-helmet-async";
import Login from "./Login";
import SignUp from "./SignUp";
import { useNavigate } from "react-router-dom";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";

export function StaffPage() {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState("PROFESSOR");

  const filters = [
    { label: "Professors", value: "PROFESSOR" },
    { label: "Associate Professors", value: "ASSOCIATE_PROFESSOR" },
    { label: "Senior Lecturers", value: "SENIOR_LECTURER" },
    { label: "Lecturers", value: "LECTURER" },
    { label: "Part-Time Lecturers", value: "PART_TIME_LECTURER" },
  ];

  useEffect(() => {
    fetchStaff();
  }, [selectedFilter]);

  const fetchStaff = async () => {
    try {
      setLoading(true);
      const url = `${BACKEND_HOST}/faculty/staff/?position=${selectedFilter}`;

      const response = await fetch(url);
      const data = await response.json();
      setStaff(data);
    } catch (error) {
      console.error("Error fetching staff:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStaffCount = () => {
    return staff.length;
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
        <title>Department & Staff | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Meet our world-class educators and researchers driving innovation in computer science at KNUST. Browse our faculty of professors, lecturers, and research experts."
        />
        <meta
          name="keywords"
          content="KNUST staff, computer science professors, KNUST lecturers, CS faculty, research staff, associate professors, senior lecturers, KNUST educators"
        />
        <meta name="author" content="BIO-CHEM KNUST" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://biochemknust.com/staff" />
        <meta property="og:title" content="Department & Staff | BIO-CHEM KNUST" />
        <meta
          property="og:description"
          content="Meet our world-class educators and researchers driving innovation in computer science at KNUST."
        />
        <meta property="og:image" content="https://biochemknust.com/og-staff.jpg" />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content="https://biochemknust.com/staff" />
        <meta name="twitter:title" content="Department & Staff | BIO-CHEM KNUST" />
        <meta
          name="twitter:description"
          content="Meet our world-class educators and researchers driving innovation in computer science at KNUST."
        />
        <meta
          name="twitter:image"
          content="https://biochemknust.com/og-staff.jpg"
        />

        {/* Additional Meta */}
        <link rel="canonical" href="https://biochemknust.com/staff" />
        <meta name="robots" content="index, follow" />
        <meta name="language" content="English" />
        <meta name="revisit-after" content="7 days" />
      </Helmet>

      <Navbar onSignInClick={handleOpenLoginModal} />

      <div className="min-h-screen bg-gray-50 pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-12">
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-4xl md:text-5xl mb-4 font-bold text-gray-900"
            >
              Department &{" "}
              <span className="relative text-blue-600">
                Staff
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
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Meet our world-class educators and researchers driving innovation
              in computer science
            </p>
          </div>

          {/* Filters */}
          <div className="mb-8 flex flex-wrap justify-center gap-3">
            {filters.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setSelectedFilter(filter.value)}
                className={`px-4 py-2 rounded-full font-medium transition-all ${
                  selectedFilter === filter.value
                    ? "bg-blue-600 text-white shadow-lg"
                    : "bg-white text-gray-700 hover:bg-gray-100"
                }`}
              >
                {filter.label}
                {selectedFilter === filter.value && (
                  <span className="ml-2 text-sm">({getStaffCount()})</span>
                )}
              </button>
            ))}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading staff members...</p>
            </div>
          )}

          {/* Staff Grid */}
          {!loading && staff.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {staff.map((member) => (
                <StaffCard key={member.id} member={member} />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && staff.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">
                No staff members found in this category.
              </p>
            </div>
          )}
        </div>
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
    </>
  );
}

function StaffCard({ member }) {
  // Helper function to get status badge styling
  const getStatusBadge = (status, statusDisplay) => {
    const styles = {
      ACTIVE: "bg-green-100 text-green-800",
      ON_LEAVE: "bg-yellow-100 text-yellow-800",
      RETIRED: "bg-gray-100 text-gray-800",
      FORMER: "bg-gray-100 text-gray-800",
    };

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          styles[status] || "bg-gray-100 text-gray-800"
        }`}
      >
        {statusDisplay}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* Image */}
      <div className="aspect-w-16 aspect-h-12 bg-gradient-to-br from-blue-400 to-blue-600">
        {member.image ? (
          <img
            src={member.image}
            alt={member.name}
            className="w-full h-64 object-cover"
          />
        ) : (
          <div className="w-full h-64 flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-white/20 flex items-center justify-center">
              <span className="text-4xl font-bold text-white">
                {member.name.charAt(0)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Name & Position */}
        <div className="flex items-start justify-between mb-1">
          <h3 className="text-xl font-bold text-gray-900 flex-1">
            {member.name}
          </h3>
          {member.status && member.status_display && (
            <div className="ml-2">
              {getStatusBadge(member.status, member.status_display)}
            </div>
          )}
        </div>
        <p className="text-blue-600 font-medium mb-2">
          {member.position_display}
        </p>

        {/* Specialization */}
        <div className="mb-3">
          <p className="text-sm font-semibold text-gray-700">
            {member.specialization}
          </p>
        </div>

        {/* Bio */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-3">{member.bio}</p>

        {/* Stats */}
        <div className="flex items-center gap-4 mb-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <BookOpen className="w-4 h-4" />
            <span>{member.publications_count} Publications</span>
          </div>
          <div className="flex items-center gap-1">
            <Award className="w-4 h-4" />
            <span>{member.awards_count} Awards</span>
          </div>
        </div>

        {/* Research Areas */}
        {member.research_areas && member.research_areas.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {member.research_areas.slice(0, 3).map((area) => (
              <span
                key={area.id}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
              >
                {area.name}
              </span>
            ))}
            {member.research_areas.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                +{member.research_areas.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Contact Info */}
        <div className="space-y-2 border-t pt-4">
          <a
            href={`mailto:${member.email}`}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600 transition-colors"
          >
            <Mail className="w-4 h-4" />
            <span className="truncate">{member.email}</span>
          </a>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <MapPin className="w-4 h-4" />
            <span>{member.office_location}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StaffPage;
