import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Users,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  MessageSquare,
  Star,
  BookOpen,
  Video,
  MapPin,
  Loader2,
  Send,
  Award,
  Target,
  TrendingUp,
  Mail,
  ExternalLink,
  X,
  DollarSign,
  Eye,
  Briefcase,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

const STATUS_COLORS = {
  pending: { bg: "bg-yellow-100", text: "text-yellow-700", icon: Clock },
  accepted: { bg: "bg-green-100", text: "text-green-700", icon: CheckCircle },
  rejected: { bg: "bg-red-100", text: "text-red-700", icon: XCircle },
  active: { bg: "bg-blue-100", text: "text-blue-700", icon: Users },
  completed: { bg: "bg-gray-100", text: "text-gray-700", icon: CheckCircle },
};

export function MenteeDashboardPage() {
  const { menteeDashboard, fetchMenteeDashboard, reviewSession, loading } =
    useMentorship();

  const [activeTab, setActiveTab] = useState("overview");
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchMenteeDashboard();
  }, []);

  const handleViewSession = (session) => {
    setSelectedSession(session);
  };

  const handleStartReview = (session) => {
    setSelectedSession(session);
    setShowReviewModal(true);
  };

  const handleReviewSession = async (sessionId, reviewData) => {
    setProcessingId(sessionId);
    const result = await reviewSession(sessionId, reviewData);
    if (result.success) {
      await fetchMenteeDashboard();
      setShowReviewModal(false);
      setSelectedSession(null);
    }
    setProcessingId(null);
    return result;
  };

  if (loading && !menteeDashboard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const stats = [
    {
      label: "Active Mentors",
      value: menteeDashboard?.active_mentors_count || 0,
      icon: Users,
      color: "blue",
      tooltip: "Number of mentors who have accepted you as their mentee",
    },
    {
      label: "Pending Applications",
      value: menteeDashboard?.pending_applications?.length || 0,
      icon: Clock,
      color: "yellow",
      tooltip: "Applications waiting for mentor approval",
    },
    {
      label: "Total Sessions",
      value: menteeDashboard?.total_sessions || 0,
      icon: Calendar,
      color: "green",
      tooltip: "Total mentoring sessions you've attended",
    },
    {
      label: "Goals Achieved",
      value: menteeDashboard?.goals_achieved || 0,
      icon: Target,
      color: "purple",
      tooltip: "Learning goals you've completed with your mentors",
    },
  ];

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "mentors", label: "My Mentors" },
    { id: "applications", label: "Applications" },
    { id: "sessions", label: "Sessions" },
    { id: "progress", label: "Progress" },
  ];

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
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              Mentee Dashboard
            </h1>
            <p className="text-gray-600">Track your mentorship journey</p>
          </div>
          <Link
            to="/dashboard/mentorship/find-mentor"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <Users className="w-4 h-4" />
            Find Mentor
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-xl p-4 shadow-sm cursor-help"
            title={stat.tooltip}
          >
            <div
              className={`w-10 h-10 rounded-lg bg-${stat.color}-100 flex items-center justify-center mb-3`}
            >
              <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm mb-6 overflow-hidden">
        <div className="flex border-b overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-all relative ${
                activeTab === tab.id
                  ? "text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <motion.div
                  layoutId="activeTabMentee"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                />
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-4 md:p-6">
          <AnimatePresence mode="wait">
            {activeTab === "overview" && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                {/* Quick Actions */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Quick Actions
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Link
                      to="/dashboard/mentorship/find-mentor"
                      className="p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors text-center"
                    >
                      <Users className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Find Mentor
                      </span>
                    </Link>
                    <button
                      onClick={() => setActiveTab("sessions")}
                      className="p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors text-center"
                    >
                      <Calendar className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        View Sessions
                      </span>
                    </button>
                    <button
                      onClick={() => setActiveTab("progress")}
                      className="p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-colors text-center"
                    >
                      <TrendingUp className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Track Progress
                      </span>
                    </button>
                    <Link
                      to="/dashboard/mentorship/resources"
                      className="p-4 bg-orange-50 rounded-xl hover:bg-orange-100 transition-colors text-center"
                    >
                      <BookOpen className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Resources
                      </span>
                    </Link>
                  </div>
                </div>

                {/* Current Mentors */}
                {menteeDashboard?.active_mentors?.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900">
                        Your Mentors
                      </h3>
                      <button
                        onClick={() => setActiveTab("mentors")}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        View All
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {menteeDashboard.active_mentors
                        .slice(0, 2)
                        .map((mentor) => (
                          <ActiveMentorCard key={mentor.id} mentor={mentor} />
                        ))}
                    </div>
                  </div>
                )}

                {/* Pending Applications */}
                {menteeDashboard?.pending_applications?.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900">
                        Pending Applications
                      </h3>
                      <button
                        onClick={() => setActiveTab("applications")}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        View All
                      </button>
                    </div>
                    <div className="space-y-3">
                      {menteeDashboard.pending_applications
                        .slice(0, 2)
                        .map((app) => (
                          <ApplicationCard key={app.id} application={app} />
                        ))}
                    </div>
                  </div>
                )}

                {/* Upcoming Sessions */}
                {menteeDashboard?.upcoming_sessions?.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900">
                        Upcoming Sessions
                      </h3>
                      <button
                        onClick={() => setActiveTab("sessions")}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        View All
                      </button>
                    </div>
                    <div className="space-y-3">
                      {menteeDashboard.upcoming_sessions
                        .slice(0, 3)
                        .map((session) => (
                          <SessionCard
                            key={session.id}
                            session={session}
                            onClick={() => handleViewSession(session)}
                            onReview={() => handleStartReview(session)}
                            isMentor={false}
                          />
                        ))}
                    </div>
                  </div>
                )}

                {/* Empty State */}
                {!menteeDashboard?.active_mentors?.length &&
                  !menteeDashboard?.pending_applications?.length && (
                    <EmptyState
                      icon={Users}
                      title="Start Your Mentorship Journey"
                      description="Find experienced mentors to guide you through your academic and career goals."
                      action={{
                        label: "Find a Mentor",
                        to: "/dashboard/mentorship/find-mentor",
                      }}
                    />
                  )}
              </motion.div>
            )}

            {activeTab === "mentors" && (
              <motion.div
                key="mentors"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {menteeDashboard?.active_mentors?.length === 0 ? (
                  <EmptyState
                    icon={Users}
                    title="No Active Mentors"
                    description="You don't have any active mentors yet. Browse available mentors and send applications."
                    action={{
                      label: "Find a Mentor",
                      to: "/dashboard/mentorship/find-mentor",
                    }}
                  />
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {menteeDashboard?.active_mentors?.map((mentor) => (
                      <ActiveMentorCard
                        key={mentor.id}
                        mentor={mentor}
                        detailed
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "applications" && (
              <motion.div
                key="applications"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {menteeDashboard?.all_applications?.length === 0 ? (
                  <EmptyState
                    icon={Send}
                    title="No Applications"
                    description="You haven't applied to any mentors yet."
                    action={{
                      label: "Find a Mentor",
                      to: "/dashboard/mentorship/find-mentor",
                    }}
                  />
                ) : (
                  <div className="space-y-4">
                    {menteeDashboard?.all_applications?.map((app) => (
                      <ApplicationCard
                        key={app.id}
                        application={app}
                        detailed
                        onViewDetails={setSelectedApplication}
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "sessions" && (
              <motion.div
                key="sessions"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {menteeDashboard?.all_sessions?.length === 0 ? (
                  <EmptyState
                    icon={Calendar}
                    title="No Sessions Yet"
                    description="Your mentorship sessions will appear here once scheduled."
                  />
                ) : (
                  <div className="space-y-4">
                    {menteeDashboard?.all_sessions?.map((session) => (
                      <SessionCard
                        key={session.id}
                        session={session}
                        detailed
                        onClick={() => handleViewSession(session)}
                        onReview={() => handleStartReview(session)}
                        isMentor={false}
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "progress" && (
              <motion.div
                key="progress"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                {/* Progress Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-5 h-5 text-blue-600" />
                      <span className="text-sm text-blue-600">
                        Sessions Attended
                      </span>
                    </div>
                    <p className="text-2xl font-bold text-blue-700">
                      {menteeDashboard?.sessions_attended || 0}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-5 h-5 text-green-600" />
                      <span className="text-sm text-green-600">
                        Goals Achieved
                      </span>
                    </div>
                    <p className="text-2xl font-bold text-green-700">
                      {menteeDashboard?.goals_achieved || 0}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Award className="w-5 h-5 text-purple-600" />
                      <span className="text-sm text-purple-600">
                        Skills Learned
                      </span>
                    </div>
                    <p className="text-2xl font-bold text-purple-700">
                      {menteeDashboard?.skills_learned || 0}
                    </p>
                  </div>
                </div>

                {/* Learning Goals */}
                {menteeDashboard?.learning_goals?.length > 0 ? (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">
                      Learning Goals
                    </h3>
                    <div className="space-y-3">
                      {menteeDashboard.learning_goals.map((goal) => (
                        <div
                          key={goal.id}
                          className={`p-4 rounded-xl border ${
                            goal.completed
                              ? "bg-green-50 border-green-200"
                              : "bg-gray-50 border-gray-100"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div
                              className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                goal.completed ? "bg-green-500" : "bg-gray-300"
                              }`}
                            >
                              {goal.completed && (
                                <CheckCircle className="w-4 h-4 text-white" />
                              )}
                            </div>
                            <div className="flex-1">
                              <h4 className="font-medium text-gray-900">
                                {goal.title}
                              </h4>
                              <p className="text-sm text-gray-500">
                                {goal.description}
                              </p>
                              {goal.progress !== undefined && (
                                <div className="mt-2">
                                  <div className="flex items-center justify-between text-xs mb-1">
                                    <span className="text-gray-500">
                                      Progress
                                    </span>
                                    <span className="font-medium">
                                      {goal.progress}%
                                    </span>
                                  </div>
                                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-blue-500 rounded-full"
                                      style={{ width: `${goal.progress}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <EmptyState
                    icon={Target}
                    title="No Goals Set"
                    description="Work with your mentor to set learning goals and track your progress."
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Application Details Modal */}
      <ApplicationDetailsModal
        application={selectedApplication}
        isOpen={!!selectedApplication}
        onClose={() => setSelectedApplication(null)}
      />

      {/* Session Details Modal */}
      <AnimatePresence>
        {selectedSession && !showReviewModal && (
          <SessionDetailsModal
            session={selectedSession}
            onClose={() => setSelectedSession(null)}
            onReview={() => handleStartReview(selectedSession)}
            isMentor={false}
          />
        )}
      </AnimatePresence>

      {/* Review Session Modal */}
      <AnimatePresence>
        {showReviewModal && selectedSession && (
          <ReviewSessionModal
            session={selectedSession}
            onClose={() => {
              setShowReviewModal(false);
              setSelectedSession(null);
            }}
            onSubmit={(data) => handleReviewSession(selectedSession.id, data)}
            processing={processingId === selectedSession.id}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function ActiveMentorCard({ mentor, detailed }) {
  // Handle both data formats: mentor.user.first_name OR mentor.first_name
  const firstName = mentor.user?.first_name || mentor.first_name;
  const lastName = mentor.user?.last_name || mentor.last_name;
  const fullName = mentor.full_name || `${firstName} ${lastName}`;
  const profilePicture = mentor.user?.profile_picture || mentor.profile_picture;
  const email = mentor.user?.email || mentor.email;

  // Format start date
  const startDate = mentor.started_at
    ? new Date(mentor.started_at).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      })
    : mentor.start_date;

  return (
    <div className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
          {profilePicture ? (
            <img
              src={profilePicture}
              alt={firstName}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-white font-bold text-lg">
              {firstName?.[0]}
              {lastName?.[0]}
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900">{fullName}</h4>
          <p className="text-sm text-gray-500">
            {mentor.area?.name || mentor.areas?.map((a) => a.name).join(", ")}
          </p>
          {mentor.rating && (
            <div className="flex items-center gap-1 mt-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium text-gray-700">
                {mentor.rating.toFixed(1)}
              </span>
            </div>
          )}
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
            <span>
              {mentor.sessions_completed || mentor.sessions_count || 0} sessions
            </span>
            {startDate && (
              <>
                <span>•</span>
                <span>Since {startDate}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {detailed && (
        <div className="mt-4 pt-4 border-t border-gray-200 flex items-center gap-2">
          {email && (
            <a
              href={`mailto:${email}`}
              className="flex items-center gap-1 px-3 py-1.5 bg-white rounded-lg text-sm text-gray-600 hover:bg-gray-200 transition-colors"
            >
              <Mail className="w-4 h-4" />
              Email
            </a>
          )}
          <Link
            to={`/dashboard/mentorship/mentor/${mentor.id}`}
            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View Profile
          </Link>
        </div>
      )}
    </div>
  );
}

function ApplicationCard({ application, detailed, onViewDetails }) {
  const status = STATUS_COLORS[application.status] || STATUS_COLORS.pending;
  const StatusIcon = status.icon;

  // Format date nicely
  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div
      className={`bg-gray-50 rounded-xl p-4 ${
        detailed ? "border border-gray-100" : ""
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold">
              {application.mentor?.first_name?.[0]}
              {application.mentor?.last_name?.[0]}
            </span>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">
              {application.mentor?.full_name ||
                `${application.mentor?.first_name} ${application.mentor?.last_name}`}
            </h4>
            <p className="text-sm text-gray-500">
              {application.area?.name && (
                <span className="text-blue-600 font-medium">
                  {application.area.name} •{" "}
                </span>
              )}
              Applied {formatDate(application.created_at)}
            </p>
          </div>
        </div>
        <span
          className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full ${status.bg} ${status.text}`}
        >
          <StatusIcon className="w-3 h-3" />
          {application.status_display || application.status}
        </span>
      </div>

      {/* Brief preview of message */}
      {application.message && (
        <div className="mt-3 p-3 bg-white rounded-lg">
          <p className="text-sm text-gray-600 line-clamp-2">
            {application.message}
          </p>
        </div>
      )}

      {application.status === "rejected" && application.rejection_reason && (
        <div className="mt-3 p-3 bg-red-50 rounded-lg">
          <p className="text-sm font-medium text-red-700 mb-1">Reason:</p>
          <p className="text-sm text-red-600">{application.rejection_reason}</p>
        </div>
      )}

      {/* Action buttons */}
      {detailed && (
        <div className="mt-4 pt-3 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={() => onViewDetails?.(application)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Eye className="w-4 h-4" />
            View Full Details
          </button>
          {application.mentor?.id && (
            <Link
              to={`/dashboard/mentorship/mentor/${application.mentor.id}`}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
            >
              View Mentor
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

// Application Details Modal
function ApplicationDetailsModal({ application, isOpen, onClose }) {
  if (!isOpen || !application) return null;

  const status = STATUS_COLORS[application.status] || STATUS_COLORS.pending;
  const StatusIcon = status.icon;

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  const getOfferingTypeLabel = (type) => {
    const labels = {
      free: "Free Mentorship",
      paid: "Paid Mentorship",
      exchange: "Skill Exchange",
    };
    return labels[type] || type;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-bold text-xl">
                      {application.mentor?.first_name?.[0]}
                      {application.mentor?.last_name?.[0]}
                    </span>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      Application to{" "}
                      {application.mentor?.full_name ||
                        `${application.mentor?.first_name} ${application.mentor?.last_name}`}
                    </h2>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full ${status.bg} ${status.text}`}
                      >
                        <StatusIcon className="w-3 h-3" />
                        {application.status_display || application.status}
                      </span>
                      {application.area?.name && (
                        <span
                          className="px-2.5 py-1 text-xs font-medium rounded-full"
                          style={{
                            backgroundColor: `${application.area.color}20`,
                            color: application.area.color,
                          }}
                        >
                          {application.area.name}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] space-y-6">
              {/* Mentor Info */}
              <div className="bg-blue-50 rounded-xl p-4">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  Mentor Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Name</p>
                    <p className="font-medium text-gray-900">
                      {application.mentor?.full_name ||
                        `${application.mentor?.first_name} ${application.mentor?.last_name}`}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Areas</p>
                    <p className="font-medium text-gray-900">
                      {application.mentor?.areas
                        ?.map((a) => a.name)
                        .join(", ") || "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Session Type</p>
                    <p className="font-medium text-gray-900 capitalize">
                      {application.mentor?.session_type || "Hybrid"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Your Message */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-purple-600" />
                  Your Message
                </h3>
                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {application.message || "No message provided"}
                  </p>
                </div>
              </div>

              {/* Learning Goals */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-green-600" />
                  Learning Goals
                </h3>
                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {application.learning_goals ||
                      "No learning goals specified"}
                  </p>
                </div>
              </div>

              {/* Skills Description */}
              {application.skills_description && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Briefcase className="w-5 h-5 text-orange-600" />
                    Your Skills & Background
                  </h3>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {application.skills_description}
                    </p>
                  </div>
                </div>
              )}

              {/* Offering Details */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-emerald-600" />
                  Mentorship Offering
                </h3>
                <div className="bg-gray-50 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Type</span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        application.offering_type === "free"
                          ? "bg-green-100 text-green-700"
                          : application.offering_type === "paid"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-purple-100 text-purple-700"
                      }`}
                    >
                      {getOfferingTypeLabel(application.offering_type)}
                    </span>
                  </div>
                  {application.offering_type === "paid" &&
                    application.offering_amount && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Amount</span>
                        <span className="font-semibold text-gray-900">
                          GHS {application.offering_amount}
                        </span>
                      </div>
                    )}
                  {application.offering_description && (
                    <div className="pt-2 border-t border-gray-200">
                      <p className="text-sm text-gray-500 mb-1">Description</p>
                      <p className="text-gray-700">
                        {application.offering_description}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Timeline */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-gray-600" />
                  Application Timeline
                </h3>
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Submitted</span>
                      <span className="text-gray-900 font-medium">
                        {formatDate(application.created_at)}
                      </span>
                    </div>
                    {application.status === "accepted" && (
                      <div className="flex items-center justify-between text-green-700">
                        <span>Accepted</span>
                        <span className="font-medium">
                          {formatDate(application.updated_at)}
                        </span>
                      </div>
                    )}
                    {application.status === "rejected" && (
                      <div className="flex items-center justify-between text-red-700">
                        <span>Rejected</span>
                        <span className="font-medium">
                          {formatDate(application.updated_at)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Rejection Reason */}
              {application.status === "rejected" &&
                application.rejection_reason && (
                  <div className="bg-red-50 rounded-xl p-4">
                    <h3 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                      <XCircle className="w-5 h-5" />
                      Rejection Reason
                    </h3>
                    <p className="text-red-600">
                      {application.rejection_reason}
                    </p>
                  </div>
                )}

              {/* Response Message from Mentor */}
              {application.response_message && (
                <div className="bg-blue-50 rounded-xl p-4">
                  <h3 className="font-semibold text-blue-700 mb-2 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Response from Mentor
                  </h3>
                  <p className="text-blue-800">
                    {application.response_message}
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                Close
              </button>
              {application.mentor?.id && (
                <Link
                  to={`/dashboard/mentorship/mentor/${application.mentor.id}`}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                  onClick={onClose}
                >
                  <ExternalLink className="w-4 h-4" />
                  View Mentor Profile
                </Link>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function SessionCard({ session, detailed, onClick, onReview, isMentor }) {
  const isUpcoming =
    new Date(session.date || session.scheduled_date) > new Date();
  const isScheduled = session.status === "scheduled";
  const isCompleted = session.status === "completed";
  const needsReview = isCompleted && !session.rating && !isMentor;

  const getStatusBadge = () => {
    if (isCompleted) {
      return { bg: "bg-green-100", text: "text-green-700", label: "Completed" };
    }
    if (isUpcoming) {
      return { bg: "bg-blue-100", text: "text-blue-700", label: "Upcoming" };
    }
    if (isScheduled) {
      return {
        bg: "bg-yellow-100",
        text: "text-yellow-700",
        label: "Scheduled",
      };
    }
    return {
      bg: "bg-gray-100",
      text: "text-gray-600",
      label: session.status_display || session.status,
    };
  };

  const status = getStatusBadge();

  return (
    <div
      className={`bg-gray-50 rounded-xl p-4 ${
        detailed ? "border border-gray-100" : ""
      } ${onClick ? "cursor-pointer hover:bg-gray-100 transition-colors" : ""}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {session.session_type === "virtual" ? (
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Video className="w-5 h-5 text-blue-600" />
            </div>
          ) : (
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <MapPin className="w-5 h-5 text-green-600" />
            </div>
          )}
          <div>
            <h4 className="font-medium text-gray-900">
              {session.title || "Mentoring Session"}
            </h4>
            <p className="text-sm text-gray-500">
              With {session.mentor?.first_name} {session.mentor?.last_name}
            </p>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              <Calendar className="w-3 h-3" />
              <span>{session.scheduled_date || session.date}</span>
              <Clock className="w-3 h-3 ml-2" />
              <span>{session.scheduled_time || session.start_time}</span>
            </div>
          </div>
        </div>
        <span
          className={`px-2 py-1 text-xs rounded-full ${status.bg} ${status.text}`}
        >
          {status.label}
        </span>
      </div>

      {/* Agenda Preview */}
      {detailed && session.agenda && (
        <div className="mt-3 p-3 bg-white rounded-lg">
          <p className="text-xs text-gray-500 mb-1">Agenda</p>
          <p className="text-sm text-gray-700 line-clamp-2">{session.agenda}</p>
        </div>
      )}

      {/* Completed Session Info */}
      {detailed && isCompleted && (
        <div className="mt-3 space-y-2">
          {session.mentor_notes && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600 font-medium mb-1">
                Mentor Notes
              </p>
              <p className="text-sm text-gray-700 line-clamp-2">
                {session.mentor_notes}
              </p>
            </div>
          )}
          {session.rating && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Rating:</span>
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-4 h-4 ${
                      star <= session.rating
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-300"
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {detailed && (
        <div className="mt-4 pt-3 border-t border-gray-200 flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClick?.();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <Eye className="w-4 h-4" />
            View Details
          </button>

          {session.meeting_link && isUpcoming && !isCompleted && (
            <a
              href={session.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors ml-auto"
            >
              <Video className="w-4 h-4" />
              Join Session
            </a>
          )}

          {needsReview && onReview && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onReview();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-500 text-white rounded-lg text-sm hover:bg-yellow-600 transition-colors ml-auto"
            >
              <Star className="w-4 h-4" />
              Rate & Review
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Session Details Modal for Mentees
function SessionDetailsModal({ session, onClose, onReview, isMentor }) {
  const isUpcoming =
    new Date(session.date || session.scheduled_date) > new Date();
  const isCompleted = session.status === "completed";
  const needsReview = isCompleted && !session.rating && !isMentor;

  const getStatusInfo = () => {
    if (isCompleted)
      return { bg: "bg-green-100", text: "text-green-700", label: "Completed" };
    if (isUpcoming)
      return { bg: "bg-blue-100", text: "text-blue-700", label: "Upcoming" };
    return {
      bg: "bg-yellow-100",
      text: "text-yellow-700",
      label: session.status_display || session.status,
    };
  };

  const status = getStatusInfo();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {session.session_type === "virtual" ? (
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Video className="w-7 h-7 text-blue-600" />
                </div>
              ) : (
                <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center">
                  <MapPin className="w-7 h-7 text-green-600" />
                </div>
              )}
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {session.title || "Mentoring Session"}
                </h2>
                <p className="text-gray-600">
                  {session.session_type_display || session.session_type} Session
                </p>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full mt-1 ${status.bg} ${status.text}`}
                >
                  {isCompleted && <CheckCircle className="w-3 h-3" />}
                  {status.label}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/50 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] space-y-6">
          {/* Date & Time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                <Calendar className="w-4 h-4" />
                Date
              </div>
              <p className="font-semibold text-gray-900">
                {session.scheduled_date || session.date}
              </p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                <Clock className="w-4 h-4" />
                Time
              </div>
              <p className="font-semibold text-gray-900">
                {session.scheduled_time ||
                  `${session.start_time} - ${session.end_time}`}
              </p>
            </div>
          </div>

          {/* Mentor Info */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              Your Mentor
            </h3>
            <div className="bg-blue-50 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">
                    {session.mentor?.first_name?.[0]}
                    {session.mentor?.last_name?.[0]}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {session.mentor?.full_name ||
                      `${session.mentor?.first_name} ${session.mentor?.last_name}`}
                  </p>
                  <Link
                    to={`/dashboard/mentorship/mentor/${session.mentor?.id}`}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    View Profile <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Meeting Link */}
          {session.meeting_link && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Meeting Link
              </h3>
              <a
                href={session.meeting_link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg text-blue-600 hover:bg-blue-100 transition-colors"
              >
                <Video className="w-5 h-5" />
                <span className="truncate">{session.meeting_link}</span>
                <ExternalLink className="w-4 h-4 ml-auto flex-shrink-0" />
              </a>
            </div>
          )}

          {/* Location */}
          {session.location && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Location
              </h3>
              <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg text-green-700">
                <MapPin className="w-5 h-5" />
                <span>{session.location}</span>
              </div>
            </div>
          )}

          {/* Agenda */}
          {session.agenda && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Agenda</h3>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {session.agenda}
                </p>
              </div>
            </div>
          )}

          {/* Completed Session Details */}
          {isCompleted && (
            <>
              {session.mentor_notes && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">
                    Mentor Notes
                  </h3>
                  <div className="p-4 bg-blue-50 rounded-xl">
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {session.mentor_notes}
                    </p>
                  </div>
                </div>
              )}

              {session.mentee_feedback && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">
                    Feedback from Mentor
                  </h3>
                  <div className="p-4 bg-purple-50 rounded-xl">
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {session.mentee_feedback}
                    </p>
                  </div>
                </div>
              )}

              {session.rating && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">
                    Session Rating
                  </h3>
                  <div className="flex items-center gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-6 h-6 ${
                          star <= session.rating
                            ? "fill-yellow-400 text-yellow-400"
                            : "text-gray-300"
                        }`}
                      />
                    ))}
                    <span className="ml-2 text-lg font-semibold text-gray-900">
                      {session.rating}/5
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t bg-gray-50 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
          >
            Close
          </button>

          {session.meeting_link && isUpcoming && !isCompleted && (
            <a
              href={session.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              <Video className="w-5 h-5" />
              Join Session
            </a>
          )}

          {needsReview && onReview && (
            <button
              onClick={onReview}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-yellow-500 text-white rounded-xl font-medium hover:bg-yellow-600 transition-colors"
            >
              <Star className="w-5 h-5" />
              Rate & Review
            </button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// Review Session Modal - For mentees to rate and provide feedback
function ReviewSessionModal({ session, onClose, onSubmit, processing }) {
  const [formData, setFormData] = useState({
    feedback: "",
    rating: 0,
  });
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (formData.rating === 0) {
      setError("Please select a rating");
      return;
    }

    const result = await onSubmit(formData);
    if (!result.success) {
      setError(result.error || "Failed to submit review");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-yellow-50 to-orange-50">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Rate Your Session
              </h2>
              <p className="text-gray-600">
                Share your feedback to help improve future sessions
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/50 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Session Info */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h4 className="font-medium text-gray-900 mb-1">
              {session.title || "Mentoring Session"}
            </h4>
            <p className="text-sm text-gray-500">
              With {session.mentor?.first_name} {session.mentor?.last_name} •{" "}
              {session.scheduled_date || session.date}
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How would you rate this session? *
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      rating: star,
                    }))
                  }
                  className="p-1 hover:scale-110 transition-transform"
                >
                  <Star
                    className={`w-10 h-10 ${
                      star <= formData.rating
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-300 hover:text-yellow-300"
                    }`}
                  />
                </button>
              ))}
            </div>
            {formData.rating > 0 && (
              <p className="mt-2 text-sm text-gray-600">
                {formData.rating === 1 &&
                  "Poor - Needs significant improvement"}
                {formData.rating === 2 && "Fair - Below expectations"}
                {formData.rating === 3 && "Good - Met expectations"}
                {formData.rating === 4 && "Very Good - Exceeded expectations"}
                {formData.rating === 5 && "Excellent - Outstanding session!"}
              </p>
            )}
          </div>

          {/* Feedback */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Feedback (Optional)
            </label>
            <textarea
              value={formData.feedback}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  feedback: e.target.value,
                }))
              }
              placeholder="Share your thoughts about the session... What went well? What could be improved?"
              rows={4}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="bg-blue-50 rounded-xl p-4">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> Your feedback helps mentors improve and
              guides other mentees in their mentor selection.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex gap-3">
          <button
            onClick={onClose}
            disabled={processing}
            className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={processing || formData.rating === 0}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-yellow-500 text-white rounded-xl font-medium hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Star className="w-5 h-5" />
                Submit Review
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-4 max-w-sm mx-auto">{description}</p>
      {action && (
        <Link
          to={action.to}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}

export default MenteeDashboardPage;
