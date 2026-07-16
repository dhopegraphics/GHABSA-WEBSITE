import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Star,
  Clock,
  Users,
  MapPin,
  Wifi,
  Video,
  Calendar,
  BookOpen,
  Send,
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  Target,
  Gift,
  DollarSign,
  ChevronRight,
  Mail,
  Award,
  Briefcase,
  Heart,
  Wallet,
  ExternalLink,
} from "lucide-react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

const SESSION_TYPE_LABELS = {
  physical: { label: "In-Person", icon: MapPin, color: "green" },
  virtual: { label: "Virtual", icon: Video, color: "purple" },
  hybrid: { label: "Hybrid", icon: Wifi, color: "blue" },
};

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

const DONATION_AMOUNTS = [10, 20, 50, 100];

export function MentorProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    fetchMentorById,
    submitMenteeApplication,
    checkMentorRelationship,
    checkMenteeEligibility,
    donateToMentor,
    loading,
  } = useMentorship();

  const [mentor, setMentor] = useState(null);
  const [loadingMentor, setLoadingMentor] = useState(true);
  const [error, setError] = useState(null);

  // Relationship state
  const [relationshipInfo, setRelationshipInfo] = useState(null);
  const [loadingRelationship, setLoadingRelationship] = useState(false);

  // Donation modal state
  const [showDonateModal, setShowDonateModal] = useState(false);
  const [donationAmount, setDonationAmount] = useState("");
  const [customAmount, setCustomAmount] = useState("");
  const [donationMessage, setDonationMessage] = useState("");
  const [donating, setDonating] = useState(false);
  const [donationResult, setDonationResult] = useState(null);

  // Eligibility state
  const [mentorEligibility, setMentorEligibility] = useState(null);
  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [hasActiveMentorship, setHasActiveMentorship] = useState(false);
  const [activeMentorInfo, setActiveMentorInfo] = useState(null);
  const [eligibleAreas, setEligibleAreas] = useState([]);

  // Apply modal state
  const [showApplyModal, setShowApplyModal] = useState(false);
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

  useEffect(() => {
    const loadMentor = async () => {
      if (!id || id === "undefined") {
        setError("Invalid mentor ID");
        setLoadingMentor(false);
        return;
      }

      setLoadingMentor(true);
      try {
        const result = await fetchMentorById(id);
        if (result) {
          setMentor(result);
        } else {
          setError("Mentor not found");
        }
      } catch (err) {
        setError("Failed to load mentor profile");
      } finally {
        setLoadingMentor(false);
      }
    };

    loadMentor();
  }, [id, fetchMentorById]);

  // Load relationship info when mentor is loaded
  useEffect(() => {
    const loadRelationship = async () => {
      if (!id || !mentor) return;

      setLoadingRelationship(true);
      try {
        const result = await checkMentorRelationship(id);
        setRelationshipInfo(result);
      } catch (err) {
        // Silently fail - user might not be logged in
      } finally {
        setLoadingRelationship(false);
      }
    };

    loadRelationship();
  }, [id, mentor, checkMentorRelationship]);

  const closeApplyModal = () => {
    setShowApplyModal(false);
    setMentorEligibility(null);
    setHasActiveMentorship(false);
    setActiveMentorInfo(null);
    setEligibleAreas([]);
  };

  const handleApplyClick = async () => {
    if (!mentor) return;

    // Check eligibility first
    setLoadingEligibility(true);
    setApplicationResult(null);

    try {
      const eligibility = await checkMenteeEligibility(mentor.id);
      setMentorEligibility(eligibility);

      if (eligibility) {
        // Check if user has an active mentorship with another mentor
        if (
          !eligibility.can_apply &&
          eligibility.reason === "active_mentorship"
        ) {
          setHasActiveMentorship(true);
          setActiveMentorInfo(eligibility.active_mentor_info || null);
          setShowApplyModal(true);
          setLoadingEligibility(false);
          return;
        }

        // Filter to only eligible areas
        const eligible = eligibility.areas?.filter((a) => a.can_apply) || [];
        setEligibleAreas(eligible);

        if (eligible.length === 0) {
          // No eligible areas - show modal with message
          setShowApplyModal(true);
          setLoadingEligibility(false);
          return;
        }

        // Normal flow - has eligible areas
        setApplicationStep(1);
        setApplicationData({
          area: eligible.length === 1 ? eligible[0].id : null,
          message: "",
          learning_goals: "",
          skills_description: "",
          offering_type: "none",
          offering_description: "",
          offering_amount: "",
        });
        setShowApplyModal(true);
      } else {
        // Fallback to old behavior if eligibility check fails
        setApplicationStep(1);
        setApplicationData({
          area: mentor.areas?.length === 1 ? mentor.areas[0].id : null,
          message: "",
          learning_goals: "",
          skills_description: "",
          offering_type: "none",
          offering_description: "",
          offering_amount: "",
        });
        setEligibleAreas(mentor.areas || []);
        setShowApplyModal(true);
      }
    } catch (err) {
      console.error("Failed to check eligibility:", err);
      // Fallback to old behavior
      setApplicationStep(1);
      setApplicationData({
        area: mentor.areas?.length === 1 ? mentor.areas[0].id : null,
        message: "",
        learning_goals: "",
        skills_description: "",
        offering_type: "none",
        offering_description: "",
        offering_amount: "",
      });
      setEligibleAreas(mentor.areas || []);
      setShowApplyModal(true);
    } finally {
      setLoadingEligibility(false);
    }
  };

  const handleDonateClick = () => {
    setDonationAmount("");
    setCustomAmount("");
    setDonationMessage("");
    setDonationResult(null);
    setShowDonateModal(true);
  };

  const handleSubmitDonation = async () => {
    const amount = donationAmount === "custom" ? customAmount : donationAmount;

    if (!amount || parseFloat(amount) <= 0) {
      setDonationResult({ error: "Please select or enter a valid amount" });
      return;
    }

    setDonating(true);
    try {
      const result = await donateToMentor(id, {
        amount: parseFloat(amount),
        message: donationMessage,
        callback_url: `${window.location.origin}/dashboard/mentorship/payment/callback`,
      });

      if (result.success) {
        setDonationResult({ success: true, data: result.data });
        // Redirect to payment page
        if (result.data.authorization_url) {
          window.location.href = result.data.authorization_url;
        }
      } else {
        setDonationResult({ error: result.error });
      }
    } catch (err) {
      setDonationResult({ error: "Failed to initiate donation" });
    } finally {
      setDonating(false);
    }
  };

  const handleSubmitApplication = async () => {
    if (!mentor || !applicationData.area || !applicationData.message.trim())
      return;

    setApplying(true);
    const result = await submitMenteeApplication({
      mentor: mentor.id,
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
      setTimeout(() => {
        setShowApplyModal(false);
        navigate("/dashboard/mentorship/my-applications");
      }, 2000);
    }
  };

  const canProceedStep1 = applicationData.area !== null;
  const canProceedStep2 =
    applicationData.message.length >= 20 &&
    applicationData.learning_goals.length >= 10;
  const canSubmit = canProceedStep1 && canProceedStep2;

  if (loadingMentor) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !mentor) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6">
        <div className="mb-6">
          <Link
            to="/dashboard/mentorship/browse-mentors"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Browse Mentors
          </Link>
        </div>
        <div className="bg-white rounded-2xl p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {error || "Mentor Not Found"}
          </h3>
          <p className="text-gray-600 mb-6">
            The mentor profile you&apos;re looking for could not be loaded.
          </p>
          <Link
            to="/dashboard/mentorship/browse-mentors"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Browse Other Mentors
          </Link>
        </div>
      </div>
    );
  }

  const sessionConfig =
    SESSION_TYPE_LABELS[mentor.session_type] || SESSION_TYPE_LABELS.hybrid;
  const SessionIcon = sessionConfig.icon;

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/dashboard/mentorship/browse-mentors"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Browse Mentors
        </Link>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Profile Header */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 h-32" />
          <div className="px-6 pb-6">
            <div className="flex flex-col md:flex-row md:items-end gap-4 -mt-16">
              <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center border-4 border-white shadow-lg">
                {mentor.user?.profile_picture ? (
                  <img
                    src={mentor.user.profile_picture}
                    alt={mentor.user?.first_name}
                    className="w-full h-full rounded-xl object-cover"
                  />
                ) : (
                  <span className="text-white font-bold text-4xl">
                    {mentor.user?.first_name?.[0]}
                    {mentor.user?.last_name?.[0]}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                  {mentor.user?.first_name} {mentor.user?.last_name}
                </h1>
                <p className="text-gray-600">
                  Year {mentor.year || mentor.user?.year || "N/A"} •{" "}
                  {mentor.programme ||
                    mentor.user?.programme ||
                    "Computer Science"}
                </p>
                <div className="flex items-center gap-4 mt-2">
                  {mentor.rating && (
                    <div className="flex items-center gap-1">
                      <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                      <span className="font-semibold text-gray-900">
                        {mentor.rating.toFixed(1)}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({mentor.total_reviews || 0} reviews)
                      </span>
                    </div>
                  )}
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded-full bg-${sessionConfig.color}-100 text-${sessionConfig.color}-700`}
                  >
                    <SessionIcon className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      {sessionConfig.label}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                {/* Donate Button - Only show if user has relationship with mentor */}
                {relationshipInfo?.can_donate && (
                  <button
                    onClick={handleDonateClick}
                    className="px-4 py-3 bg-pink-600 text-white rounded-xl font-medium hover:bg-pink-700 transition-colors flex items-center gap-2"
                  >
                    <Heart className="w-5 h-5" />
                    Donate
                  </button>
                )}
                <button
                  onClick={handleApplyClick}
                  disabled={
                    !mentor.is_accepting_mentees || !mentor.has_available_slots
                  }
                  className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {!mentor.is_accepting_mentees
                    ? "Not Accepting Mentees"
                    : !mentor.has_available_slots
                    ? "No Available Slots"
                    : "Request Mentorship"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {mentor.total_mentees || 0}
            </p>
            <p className="text-sm text-gray-500">Total Mentees</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-2">
              <Calendar className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {mentor.total_sessions || 0}
            </p>
            <p className="text-sm text-gray-500">Sessions</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-2">
              <Clock className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {mentor.available_slots || 0}
            </p>
            <p className="text-sm text-gray-500">Available Slots</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center mb-2">
              <Award className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {mentor.years_experience || "N/A"}
            </p>
            <p className="text-sm text-gray-500">Years Exp.</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="md:col-span-2 space-y-6">
            {/* Bio */}
            {mentor.bio && (
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="font-semibold text-gray-900 mb-3">About</h2>
                <p className="text-gray-600 whitespace-pre-wrap">
                  {mentor.bio}
                </p>
              </div>
            )}

            {/* Experience */}
            {mentor.experience_description && (
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-gray-400" />
                  Experience
                </h2>
                <p className="text-gray-600 whitespace-pre-wrap">
                  {mentor.experience_description}
                </p>
              </div>
            )}

            {/* Skills */}
            {mentor.skills?.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="font-semibold text-gray-900 mb-3">
                  Skills & Expertise
                </h2>
                <div className="flex flex-wrap gap-2">
                  {mentor.skills.map((skill) => (
                    <span
                      key={skill.id}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {skill.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Mentorship Areas */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Target className="w-5 h-5 text-gray-400" />
                Mentorship Areas
              </h2>
              <div className="space-y-2">
                {mentor.areas?.map((area) => (
                  <div
                    key={area.id}
                    className="flex items-center gap-2 p-2 rounded-lg"
                    style={{ backgroundColor: `${area.color || "#3B82F6"}15` }}
                  >
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: area.color || "#3B82F6" }}
                    />
                    <span className="text-sm font-medium text-gray-700">
                      {area.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Availability */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-3">Availability</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Status</span>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      mentor.is_accepting_mentees
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {mentor.is_accepting_mentees
                      ? "Accepting Mentees"
                      : "Not Accepting"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Available Slots</span>
                  <span className="font-medium text-gray-900">
                    {mentor.available_slots || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Session Type</span>
                  <span className="font-medium text-gray-900">
                    {sessionConfig.label}
                  </span>
                </div>
              </div>
            </div>

            {/* Apply CTA */}
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl p-6 text-white">
              <h3 className="font-semibold mb-2">Ready to Learn?</h3>
              <p className="text-white/80 text-sm mb-4">
                Apply to become {mentor.user?.first_name}&apos;s mentee and
                start your learning journey.
              </p>
              <button
                onClick={handleApplyClick}
                disabled={
                  !mentor.is_accepting_mentees || !mentor.has_available_slots
                }
                className="w-full py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply Now
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Apply Modal - Same as BrowseMentorsPage */}
      <AnimatePresence>
        {showApplyModal && mentor && (
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
              {/* Loading eligibility state */}
              {loadingEligibility ? (
                <div className="text-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-600">Checking eligibility...</p>
                </div>
              ) : hasActiveMentorship ? (
                /* Active mentorship block */
                <div className="text-center py-6">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-orange-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Active Mentorship in Progress
                  </h3>
                  <p className="text-gray-600 mb-4">
                    You currently have an active mentorship
                    {activeMentorInfo && (
                      <span className="font-medium">
                        {" "}
                        with {activeMentorInfo.mentor_name}
                      </span>
                    )}
                    . You can only have one active mentorship at a time.
                  </p>
                  <p className="text-sm text-gray-500 mb-6">
                    Complete or end your current mentorship before applying to a
                    new mentor.
                  </p>
                  <div className="flex gap-3 justify-center">
                    <button
                      onClick={closeApplyModal}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
                    >
                      Close
                    </button>
                    <Link
                      to="/dashboard/mentorship"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                    >
                      View My Mentorship
                    </Link>
                  </div>
                </div>
              ) : eligibleAreas.length === 0 && mentorEligibility ? (
                /* No eligible areas */
                <div className="text-center py-6">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-yellow-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Cannot Apply to This Mentor
                  </h3>
                  <p className="text-gray-600 mb-4">
                    You&apos;ve already had mentorship relationships with{" "}
                    {mentor.user?.first_name} in all their available areas, or
                    have pending applications.
                  </p>
                  {mentorEligibility.areas?.length > 0 && (
                    <div className="text-left bg-gray-50 rounded-lg p-4 mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">
                        Area Status:
                      </p>
                      {mentorEligibility.areas.map((area) => (
                        <div
                          key={area.id}
                          className="flex items-center justify-between text-sm py-1"
                        >
                          <span className="text-gray-600">{area.name}</span>
                          <span className="text-red-600 text-xs">
                            {area.reason === "pending_application"
                              ? "Pending application"
                              : area.reason === "past_relationship"
                              ? "Previous mentorship"
                              : "Not eligible"}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={closeApplyModal}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
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
                    Your application has been sent to {mentor.user?.first_name}.
                    Redirecting to your applications...
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
                        <div className="grid gap-2">
                          {(eligibleAreas.length > 0
                            ? eligibleAreas
                            : mentor.areas
                          )?.map((area) => (
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

      {/* Donation Modal */}
      <AnimatePresence>
        {showDonateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => !donating && setShowDonateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-xl w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-pink-100 rounded-full flex items-center justify-center">
                    <Heart className="w-5 h-5 text-pink-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Support {mentor.user?.first_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Show appreciation for your mentor
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDonateModal(false)}
                  disabled={donating}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {donationResult?.success ? (
                  <div className="text-center py-6">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <CheckCircle className="w-8 h-8 text-green-600" />
                    </div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">
                      Redirecting to Payment
                    </h4>
                    <p className="text-gray-600">
                      You&apos;ll be redirected to complete your donation...
                    </p>
                    <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Please wait...
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Donation Amount Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Select Amount (GHS)
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {DONATION_AMOUNTS.map((amount) => (
                          <button
                            key={amount}
                            onClick={() => {
                              setDonationAmount(amount.toString());
                              setCustomAmount("");
                            }}
                            className={`px-4 py-3 rounded-xl font-medium transition-all ${
                              donationAmount === amount.toString()
                                ? "bg-pink-600 text-white"
                                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                            }`}
                          >
                            ₵{amount}
                          </button>
                        ))}
                      </div>

                      {/* Custom Amount */}
                      <div className="mt-4">
                        <label className="block text-sm text-gray-600 mb-2">
                          Or enter a custom amount
                        </label>
                        <div className="relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            ₵
                          </span>
                          <input
                            type="number"
                            value={customAmount}
                            onChange={(e) => {
                              setCustomAmount(e.target.value);
                              setDonationAmount("custom");
                            }}
                            placeholder="Enter amount"
                            min="1"
                            className="w-full pl-8 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Donation Message */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Add a message (optional)
                      </label>
                      <textarea
                        value={donationMessage}
                        onChange={(e) => setDonationMessage(e.target.value)}
                        placeholder="Thank you for being an amazing mentor!"
                        rows={3}
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-transparent resize-none"
                      />
                    </div>

                    {/* Error Message */}
                    {donationResult?.error && (
                      <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{donationResult.error}</span>
                      </div>
                    )}

                    {/* Info */}
                    <div className="flex items-start gap-2 p-3 bg-blue-50 text-blue-700 rounded-lg">
                      <Wallet className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium">Secure Payment</p>
                        <p className="text-blue-600">
                          Your donation will be processed securely through
                          Paystack and credited to your mentor&apos;s wallet.
                        </p>
                      </div>
                    </div>

                    {/* Submit Button */}
                    <button
                      onClick={handleSubmitDonation}
                      disabled={
                        donating ||
                        (!donationAmount && !customAmount) ||
                        (donationAmount === "custom" && !customAmount)
                      }
                      className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-pink-600 text-white rounded-xl font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {donating ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Heart className="w-5 h-5" />
                          Donate{" "}
                          {donationAmount === "custom"
                            ? customAmount
                              ? `₵${customAmount}`
                              : ""
                            : donationAmount
                            ? `₵${donationAmount}`
                            : ""}
                        </>
                      )}
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default MentorProfilePage;
