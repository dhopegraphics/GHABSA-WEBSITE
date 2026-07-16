import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Search,
  Filter,
  User,
  Star,
  Clock,
  Users,
  MapPin,
  Wifi,
  ChevronDown,
  X,
  BookOpen,
  Send,
  Loader2,
  CheckCircle,
  AlertCircle,
  Target,
  Gift,
  DollarSign,
  ChevronRight,
  Eye,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

const OFFERING_TYPES = [
  { value: "none", label: "No Offering", description: "Volunteer mentorship" },
  {
    value: "gratitude",
    label: "Gratitude",
    description: "Thank you note or small gesture",
  },
  {
    value: "skill_exchange",
    label: "Skill Exchange",
    description: "Offer your skills in return",
  },
  {
    value: "monetary",
    label: "Monetary",
    description: "Financial compensation",
  },
];

const SESSION_TYPE_LABELS = {
  physical: "In-Person",
  virtual: "Virtual",
  hybrid: "Hybrid",
};

export function BrowseMentorsPage() {
  const navigate = useNavigate();
  const {
    areas,
    mentors,
    fetchAreas,
    fetchMentors,
    checkMenteeEligibility,
    submitMenteeApplication,
    loading,
  } = useMentorship();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedArea, setSelectedArea] = useState(null);
  const [sessionTypeFilter, setSessionTypeFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Eligibility state - maps mentor ID to eligibility data
  const [mentorEligibility, setMentorEligibility] = useState({});
  const [loadingEligibility, setLoadingEligibility] = useState({});

  // Active mentorship state (blocks all new applications)
  const [hasActiveMentorship, setHasActiveMentorship] = useState(false);
  const [activeMentorInfo, setActiveMentorInfo] = useState(null);

  // Apply modal state
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState(null);
  const [applicationStep, setApplicationStep] = useState(1);
  const [applicationData, setApplicationData] = useState({
    area: null,
    message: "",
    learning_goals: "",
    skills_description: "",
    offering_type: "none",
    offering_description: "",
    offering_amount: "",
  });
  const [applying, setApplying] = useState(false);
  const [applicationResult, setApplicationResult] = useState(null);
  const [eligibleAreas, setEligibleAreas] = useState([]);

  useEffect(() => {
    fetchAreas();
    fetchMentors();
  }, []);

  const filteredMentors = mentors?.filter((mentor) => {
    // Search filter
    const searchMatch =
      !searchQuery ||
      mentor.user?.first_name
        ?.toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      mentor.user?.last_name
        ?.toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      mentor.areas?.some((a) =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase())
      ) ||
      mentor.skills?.some((s) =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase())
      );

    // Area filter
    const areaMatch =
      !selectedArea || mentor.areas?.some((a) => a.id === selectedArea);

    // Session type filter
    const sessionMatch =
      !sessionTypeFilter || mentor.session_type === sessionTypeFilter;

    return searchMatch && areaMatch && sessionMatch;
  });

  // Check eligibility for a specific mentor
  const fetchMentorEligibility = async (mentorId) => {
    if (mentorEligibility[mentorId] || loadingEligibility[mentorId]) return;

    setLoadingEligibility((prev) => ({ ...prev, [mentorId]: true }));
    const result = await checkMenteeEligibility(mentorId);

    // Check if user has an active mentorship (blocks all applications)
    if (result.reason === "active_mentorship") {
      setHasActiveMentorship(true);
      setActiveMentorInfo(result.active_mentor);
    }

    setMentorEligibility((prev) => ({ ...prev, [mentorId]: result }));
    setLoadingEligibility((prev) => ({ ...prev, [mentorId]: false }));
    return result;
  };

  const handleApplyClick = async (mentor) => {
    // First check eligibility
    let eligibility = mentorEligibility[mentor.id];
    if (!eligibility) {
      setLoadingEligibility((prev) => ({ ...prev, [mentor.id]: true }));
      eligibility = await checkMenteeEligibility(mentor.id);
      setMentorEligibility((prev) => ({ ...prev, [mentor.id]: eligibility }));
      setLoadingEligibility((prev) => ({ ...prev, [mentor.id]: false }));
    }

    // If user has an active mentorship, show message
    if (eligibility.reason === "active_mentorship") {
      setHasActiveMentorship(true);
      setActiveMentorInfo(eligibility.active_mentor);
      setSelectedMentor(mentor);
      setShowApplyModal(true);
      return;
    }

    // Filter to only eligible areas
    const areasUserCanApplyTo =
      eligibility.areas?.filter((a) => a.can_apply) || [];
    setEligibleAreas(areasUserCanApplyTo);

    if (areasUserCanApplyTo.length === 0) {
      // No areas available - show modal with message
      setSelectedMentor(mentor);
      setShowApplyModal(true);
      return;
    }

    setSelectedMentor(mentor);
    setApplicationStep(1);
    setApplicationData({
      area: areasUserCanApplyTo.length === 1 ? areasUserCanApplyTo[0].id : null,
      message: "",
      learning_goals: "",
      skills_description: "",
      offering_type: "none",
      offering_description: "",
      offering_amount: "",
    });
    setApplicationResult(null);
    setShowApplyModal(true);
  };

  const handleSubmitApplication = async () => {
    if (
      !selectedMentor ||
      !applicationData.area ||
      !applicationData.message.trim()
    )
      return;

    setApplying(true);
    const result = await submitMenteeApplication({
      mentor: selectedMentor.id,
      area: applicationData.area,
      message: applicationData.message,
      learning_goals: applicationData.learning_goals,
      skills_description: applicationData.skills_description,
      offering_type: applicationData.offering_type,
      offering_description: applicationData.offering_description,
      offering_amount:
        applicationData.offering_type === "monetary"
          ? parseFloat(applicationData.offering_amount) || 0
          : null,
    });

    setApplicationResult(result);
    setApplying(false);

    if (result.success) {
      // Refresh eligibility for this mentor since they now have a pending application
      setMentorEligibility((prev) => ({ ...prev, [selectedMentor.id]: null }));

      setTimeout(() => {
        closeApplyModal();
      }, 2000);
    }
  };

  const closeApplyModal = () => {
    setShowApplyModal(false);
    setSelectedMentor(null);
    setApplicationResult(null);
    setEligibleAreas([]);
    setApplicationStep(1);
    // Don't reset hasActiveMentorship - it's a global state
  };

  const canProceedStep1 = applicationData.area !== null;
  const canProceedStep2 =
    applicationData.message.length >= 20 &&
    applicationData.learning_goals.length >= 10;
  const canSubmit = canProceedStep1 && canProceedStep2;

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedArea(null);
    setSessionTypeFilter("");
  };

  const hasActiveFilters = searchQuery || selectedArea || sessionTypeFilter;

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/dashboard/mentorship"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Mentorship
        </Link>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Find a Mentor
        </h1>
        <p className="text-gray-600">
          Browse and connect with experienced mentors
        </p>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl p-4 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search mentors, skills, areas..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              showFilters || hasActiveFilters
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                !
              </span>
            )}
          </button>
        </div>

        {/* Expanded Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-4 border-t mt-4 space-y-4">
                {/* Area Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mentorship Area
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {areas?.map((area) => (
                      <button
                        key={area.id}
                        onClick={() =>
                          setSelectedArea(
                            selectedArea === area.id ? null : area.id
                          )
                        }
                        className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                          selectedArea === area.id
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                      >
                        {area.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Session Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Session Type
                  </label>
                  <div className="flex gap-2">
                    {Object.entries(SESSION_TYPE_LABELS).map(
                      ([value, label]) => (
                        <button
                          key={value}
                          onClick={() =>
                            setSessionTypeFilter(
                              sessionTypeFilter === value ? "" : value
                            )
                          }
                          className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                            sessionTypeFilter === value
                              ? "bg-blue-600 text-white"
                              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                          }`}
                        >
                          {label}
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* Clear Filters */}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-2 text-sm text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                    Clear all filters
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Results Count */}
      <div className="mb-4 flex items-center justify-between">
        <p
          className="text-sm text-gray-600"
          title={`${filteredMentors?.length || 0} approved mentor${
            filteredMentors?.length !== 1 ? "s" : ""
          } matching your search criteria`}
        >
          {filteredMentors?.length || 0} mentor
          {filteredMentors?.length !== 1 ? "s" : ""} found
        </p>
      </div>

      {/* Mentors Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : filteredMentors?.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Mentors Found
          </h3>
          <p className="text-gray-600 mb-4">
            {hasActiveFilters
              ? "Try adjusting your filters to find more mentors"
              : "No mentors are available at the moment"}
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear all filters
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMentors?.map((mentor) => (
            <MentorCard
              key={mentor.id}
              mentor={mentor}
              onApply={() => handleApplyClick(mentor)}
            />
          ))}
        </div>
      )}

      {/* Apply Modal */}
      <AnimatePresence>
        {showApplyModal && selectedMentor && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => !applying && closeApplyModal()}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Show Active Mentorship Block */}
              {hasActiveMentorship && activeMentorInfo ? (
                <div className="text-center py-6">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-yellow-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Active Mentorship Exists
                  </h3>
                  <p className="text-gray-600 mb-4">
                    You already have an active mentorship with{" "}
                    <span className="font-semibold">
                      {activeMentorInfo.name}
                    </span>{" "}
                    in{" "}
                    <span className="font-semibold">
                      {activeMentorInfo.area}
                    </span>
                    .
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    You can only have one active mentorship at a time. Complete
                    or end your current mentorship before applying to another
                    mentor.
                  </p>
                  <div className="flex gap-3 justify-center">
                    <button
                      onClick={closeApplyModal}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                    >
                      Close
                    </button>
                    <Link
                      to="/dashboard/mentorship/mentee-dashboard"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                    >
                      Go to Dashboard
                    </Link>
                  </div>
                </div>
              ) : eligibleAreas.length === 0 && !applicationResult?.success ? (
                // No eligible areas
                <div className="text-center py-6">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Cannot Apply to This Mentor
                  </h3>
                  <p className="text-gray-600 mb-4">
                    You cannot apply to {selectedMentor?.user?.first_name} for
                    any area because:
                  </p>
                  <div className="text-left bg-gray-50 rounded-lg p-4 mb-4">
                    {mentorEligibility[selectedMentor?.id]?.areas?.map(
                      (area) => (
                        <div
                          key={area.id}
                          className="flex items-start gap-2 mb-2 last:mb-0"
                        >
                          <X className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-medium text-gray-900">
                              {area.name}:
                            </span>{" "}
                            <span className="text-gray-600">
                              {area.message}
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                  <button
                    onClick={closeApplyModal}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                  >
                    Close
                  </button>
                </div>
              ) : applicationResult?.success ? (
                <div className="text-center py-6">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Application Sent!
                  </h3>
                  <p className="text-gray-600">
                    Your application has been sent to{" "}
                    {selectedMentor.user?.first_name}. They will review and
                    respond to your request.
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">
                        Apply to Mentor
                      </h3>
                      <p className="text-sm text-gray-500">
                        Step {applicationStep} of 3
                      </p>
                    </div>
                    <button
                      onClick={closeApplyModal}
                      className="p-2 hover:bg-gray-100 rounded-full"
                    >
                      <X className="w-5 h-5 text-gray-500" />
                    </button>
                  </div>

                  {/* Progress Bar */}
                  <div className="flex gap-1 mb-4">
                    {[1, 2, 3].map((step) => (
                      <div
                        key={step}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                          step <= applicationStep
                            ? "bg-blue-600"
                            : "bg-gray-200"
                        }`}
                      />
                    ))}
                  </div>

                  {/* Mentor Info */}
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold">
                        {selectedMentor.user?.first_name?.[0]}
                        {selectedMentor.user?.last_name?.[0]}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {selectedMentor.user?.first_name}{" "}
                        {selectedMentor.user?.last_name}
                      </h4>
                      <p className="text-sm text-gray-500">
                        {eligibleAreas.map((a) => a.name).join(", ")}
                      </p>
                    </div>
                  </div>

                  {applicationResult?.error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4 flex items-start gap-2">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <p className="text-sm text-red-600">
                        {typeof applicationResult.error === "object"
                          ? Object.entries(applicationResult.error).map(
                              ([key, val]) => (
                                <span key={key} className="block">
                                  {key}:{" "}
                                  {Array.isArray(val) ? val.join(", ") : val}
                                </span>
                              )
                            )
                          : applicationResult.error}
                      </p>
                    </div>
                  )}

                  {/* Step 1: Select Area */}
                  {applicationStep === 1 && (
                    <div className="space-y-4">
                      <div>
                        <label className="block font-medium text-gray-900 mb-2">
                          <Target className="w-4 h-4 inline mr-2" />
                          Select Mentorship Area *
                        </label>
                        <p className="text-sm text-gray-500 mb-3">
                          Choose the area you want to be mentored in
                          {eligibleAreas.length <
                            (selectedMentor?.areas?.length || 0) && (
                            <span className="block text-yellow-600 mt-1">
                              Some areas are unavailable because you&apos;ve
                              already been mentored in them.
                            </span>
                          )}
                        </p>
                        <div className="grid gap-2">
                          {eligibleAreas.map((area) => (
                            <button
                              key={area.id}
                              onClick={() =>
                                setApplicationData((prev) => ({
                                  ...prev,
                                  area: area.id,
                                }))
                              }
                              className={`p-3 rounded-xl border-2 text-left transition-all ${
                                applicationData.area === area.id
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{
                                    backgroundColor: area.color || "#3B82F6",
                                  }}
                                />
                                <span className="font-medium text-gray-900">
                                  {area.name}
                                </span>
                                {applicationData.area === area.id && (
                                  <CheckCircle className="w-5 h-5 text-blue-600 ml-auto" />
                                )}
                              </div>
                              {area.description && (
                                <p className="text-sm text-gray-500 mt-1 ml-6">
                                  {area.description}
                                </p>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step 2: Goals & Message */}
                  {applicationStep === 2 && (
                    <div className="space-y-4">
                      <div>
                        <label className="block font-medium text-gray-900 mb-2">
                          Introduction & Why This Mentor? *
                        </label>
                        <textarea
                          value={applicationData.message}
                          onChange={(e) =>
                            setApplicationData((prev) => ({
                              ...prev,
                              message: e.target.value,
                            }))
                          }
                          placeholder="Introduce yourself and explain why you'd like to be mentored by this person..."
                          rows={3}
                          className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {applicationData.message.length}/20 minimum characters
                        </p>
                      </div>

                      <div>
                        <label className="block font-medium text-gray-900 mb-2">
                          Learning Goals *
                        </label>
                        <textarea
                          value={applicationData.learning_goals}
                          onChange={(e) =>
                            setApplicationData((prev) => ({
                              ...prev,
                              learning_goals: e.target.value,
                            }))
                          }
                          placeholder="What do you hope to achieve from this mentorship?"
                          rows={3}
                          className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {applicationData.learning_goals.length}/10 minimum
                          characters
                        </p>
                      </div>

                      <div>
                        <label className="block font-medium text-gray-900 mb-2">
                          Current Skills (Optional)
                        </label>
                        <textarea
                          value={applicationData.skills_description}
                          onChange={(e) =>
                            setApplicationData((prev) => ({
                              ...prev,
                              skills_description: e.target.value,
                            }))
                          }
                          placeholder="Describe your current skills and experience level..."
                          rows={2}
                          className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        />
                      </div>
                    </div>
                  )}

                  {/* Step 3: Offering */}
                  {applicationStep === 3 && (
                    <div className="space-y-4">
                      <div>
                        <label className="block font-medium text-gray-900 mb-2">
                          <Gift className="w-4 h-4 inline mr-2" />
                          What Can You Offer? (Optional)
                        </label>
                        <p className="text-sm text-gray-500 mb-3">
                          Mentorship can be a two-way exchange
                        </p>
                        <div className="grid gap-2">
                          {OFFERING_TYPES.map((type) => (
                            <button
                              key={type.value}
                              onClick={() =>
                                setApplicationData((prev) => ({
                                  ...prev,
                                  offering_type: type.value,
                                  offering_amount:
                                    type.value !== "monetary"
                                      ? ""
                                      : prev.offering_amount,
                                }))
                              }
                              className={`p-3 rounded-xl border-2 text-left transition-all ${
                                applicationData.offering_type === type.value
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <span className="font-medium text-gray-900">
                                    {type.label}
                                  </span>
                                  <p className="text-sm text-gray-500">
                                    {type.description}
                                  </p>
                                </div>
                                {applicationData.offering_type ===
                                  type.value && (
                                  <CheckCircle className="w-5 h-5 text-blue-600" />
                                )}
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>

                      {applicationData.offering_type === "monetary" && (
                        <div>
                          <label className="block font-medium text-gray-900 mb-2">
                            <DollarSign className="w-4 h-4 inline mr-2" />
                            Amount (GHS)
                          </label>
                          <input
                            type="number"
                            value={applicationData.offering_amount}
                            onChange={(e) =>
                              setApplicationData((prev) => ({
                                ...prev,
                                offering_amount: e.target.value,
                              }))
                            }
                            placeholder="Enter amount"
                            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                      )}

                      {(applicationData.offering_type === "skill_exchange" ||
                        applicationData.offering_type === "gratitude") && (
                        <div>
                          <label className="block font-medium text-gray-900 mb-2">
                            Description
                          </label>
                          <textarea
                            value={applicationData.offering_description}
                            onChange={(e) =>
                              setApplicationData((prev) => ({
                                ...prev,
                                offering_description: e.target.value,
                              }))
                            }
                            placeholder={
                              applicationData.offering_type === "skill_exchange"
                                ? "Describe the skills you can offer in exchange..."
                                : "Describe your gesture of gratitude..."
                            }
                            rows={2}
                            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Navigation Buttons */}
                  <div className="flex gap-3 mt-6">
                    {applicationStep > 1 && (
                      <button
                        onClick={() => setApplicationStep((prev) => prev - 1)}
                        disabled={applying}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all disabled:opacity-50"
                      >
                        Back
                      </button>
                    )}
                    {applicationStep === 1 && (
                      <button
                        onClick={closeApplyModal}
                        disabled={applying}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    )}
                    {applicationStep < 3 ? (
                      <button
                        onClick={() => setApplicationStep((prev) => prev + 1)}
                        disabled={
                          (applicationStep === 1 && !canProceedStep1) ||
                          (applicationStep === 2 && !canProceedStep2)
                        }
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Continue
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={handleSubmitApplication}
                        disabled={applying || !canSubmit}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {applying ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Sending...
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4" />
                            Submit Application
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function MentorCard({ mentor, onApply }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);

  const handleViewProfile = () => {
    navigate(`/dashboard/mentorship/mentor/${mentor.id}`);
  };

  return (
    <motion.div
      layout
      className="bg-white rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow"
    >
      {/* Header - Clickable to view profile */}
      <div
        className="flex items-start gap-3 mb-4 cursor-pointer group"
        onClick={handleViewProfile}
      >
        <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 group-hover:ring-2 group-hover:ring-blue-300 transition-all">
          {mentor.user?.profile_picture || mentor.profile_image ? (
            <img
              src={mentor.user?.profile_picture || mentor.profile_image}
              alt={mentor.full_name || mentor.user?.first_name}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-white font-bold text-lg">
              {mentor.full_name
                ? mentor.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                : `${mentor.user?.first_name?.[0] || ""}${
                    mentor.user?.last_name?.[0] || ""
                  }`}
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
            {mentor.full_name ||
              `${mentor.user?.first_name} ${mentor.user?.last_name}`}
          </h3>
          <p className="text-sm text-gray-500">
            Year {mentor.year || mentor.user?.year || "N/A"} •{" "}
            {mentor.programme || mentor.user?.programme || "Computer Science"}
          </p>
          {mentor.rating && (
            <div className="flex items-center gap-1 mt-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium text-gray-700">
                {mentor.rating.toFixed(1)}
              </span>
              <span className="text-xs text-gray-400">
                ({mentor.total_mentees || 0} mentees)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Areas */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {mentor.areas?.slice(0, 3).map((area) => (
          <span
            key={area.id}
            className="px-2 py-0.5 text-xs rounded-full"
            style={{
              backgroundColor: `${area.color}20`,
              color: area.color,
            }}
          >
            {area.name}
          </span>
        ))}
        {mentor.areas?.length > 3 && (
          <span
            className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full cursor-help"
            title={`${mentor.areas.length - 3} more area${
              mentor.areas.length - 3 !== 1 ? "s" : ""
            }: ${mentor.areas
              .slice(3)
              .map((a) => a.name)
              .join(", ")}`}
          >
            +{mentor.areas.length - 3}
          </span>
        )}
      </div>

      {/* Quick Info */}
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <div
          className="flex items-center gap-1"
          title={`This mentor offers ${
            mentor.session_type || "hybrid"
          } mentoring sessions`}
        >
          {mentor.session_type === "virtual" ? (
            <Wifi className="w-4 h-4" />
          ) : mentor.session_type === "physical" ? (
            <MapPin className="w-4 h-4" />
          ) : (
            <Users className="w-4 h-4" />
          )}
          <span className="capitalize">{mentor.session_type || "Hybrid"}</span>
        </div>
        <div
          className="flex items-center gap-1"
          title={`${mentor.available_slots || 0} mentee slot${
            (mentor.available_slots || 0) !== 1 ? "s" : ""
          } available - how many more mentees this mentor can accept`}
        >
          <Users className="w-4 h-4" />
          <span>{mentor.available_slots || 0} slots</span>
        </div>
      </div>

      {/* Expandable Skills */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="pt-3 border-t mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Skills</h4>
              <div className="flex flex-wrap gap-1.5">
                {mentor.skills?.map((skill) => (
                  <span
                    key={skill.id}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded-full"
                  >
                    {skill.name}
                  </span>
                ))}
              </div>
              {mentor.bio && (
                <div className="mt-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    About
                  </h4>
                  <p className="text-sm text-gray-600">{mentor.bio}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
        >
          {expanded ? "Show Less" : "View More"}
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              expanded ? "rotate-180" : ""
            }`}
          />
        </button>
        <div className="flex-1" />
        <button
          onClick={handleViewProfile}
          className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-all"
          title="View full profile"
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          onClick={onApply}
          disabled={mentor.available_slots === 0}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            mentor.available_slots === 0
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          <Send className="w-4 h-4" />
          {mentor.available_slots === 0 ? "Full" : "Apply"}
        </button>
      </div>
    </motion.div>
  );
}

export default BrowseMentorsPage;
