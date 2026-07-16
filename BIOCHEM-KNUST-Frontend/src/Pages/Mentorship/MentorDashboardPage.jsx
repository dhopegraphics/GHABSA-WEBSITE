import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Users,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageSquare,
  DollarSign,
  Star,
  Mail,
  Phone,
  Eye,
  BookOpen,
  Video,
  MapPin,
  Loader2,
  ChevronRight,
  Wallet,
  X,
  Target,
  Sparkles,
  Gift,
  GraduationCap,
  Briefcase,
  ExternalLink,
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

const OFFERING_TYPE_LABELS = {
  none: { label: "No Offering", color: "gray" },
  gratitude: { label: "Gratitude", color: "pink" },
  skill_exchange: { label: "Skill Exchange", color: "purple" },
  monetary: { label: "Monetary", color: "green" },
};

export function MentorDashboardPage() {
  const {
    mentorDashboard,
    fetchMentorDashboard,
    acceptMentee,
    rejectMentee,
    completeSession,
    loading,
  } = useMentorship();

  const [activeTab, setActiveTab] = useState("overview");
  const [processingId, setProcessingId] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [showCompleteModal, setShowCompleteModal] = useState(false);

  useEffect(() => {
    fetchMentorDashboard();
  }, []);

  const handleAcceptMentee = async (applicationId) => {
    setProcessingId(applicationId);
    await acceptMentee(applicationId);
    await fetchMentorDashboard();
    setProcessingId(null);
    setSelectedApplication(null);
  };

  const handleRejectMentee = async (applicationId) => {
    setProcessingId(applicationId);
    await rejectMentee(applicationId);
    await fetchMentorDashboard();
    setProcessingId(null);
    setSelectedApplication(null);
  };

  const handleViewApplication = (application) => {
    setSelectedApplication(application);
  };

  const handleViewSession = (session) => {
    setSelectedSession(session);
  };

  const handleCompleteSession = async (sessionId, mentorNotes) => {
    setProcessingId(sessionId);
    const result = await completeSession(sessionId, mentorNotes);
    if (result.success) {
      await fetchMentorDashboard();
      setShowCompleteModal(false);
      setSelectedSession(null);
    }
    setProcessingId(null);
    return result;
  };

  const handleStartComplete = (session) => {
    setSelectedSession(session);
    setShowCompleteModal(true);
  };

  if (loading && !mentorDashboard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!mentorDashboard?.is_approved) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl p-8 shadow-lg max-w-md text-center"
        >
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Not a Mentor Yet
          </h2>
          <p className="text-gray-600 mb-6">
            You haven&apos;t been approved as a mentor yet. Please apply or
            check your application status.
          </p>
          <div className="flex flex-col gap-3">
            <Link
              to="/dashboard/mentorship/apply-mentor"
              className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Apply as Mentor
            </Link>
            <Link
              to="/dashboard/mentorship/my-applications"
              className="inline-flex items-center justify-center gap-2 text-gray-600 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              View My Applications
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  const stats = [
    {
      label: "Active Mentees",
      value: mentorDashboard?.active_mentees_count || 0,
      icon: Users,
      color: "blue",
      tooltip: "Number of mentees you are currently mentoring",
    },
    {
      label: "Pending Requests",
      value: mentorDashboard?.pending_applications?.length || 0,
      icon: Clock,
      color: "yellow",
      tooltip: "Mentee applications waiting for your approval",
    },
    {
      label: "Total Sessions",
      value: mentorDashboard?.total_sessions || 0,
      icon: Calendar,
      color: "green",
      tooltip: "Total mentoring sessions you've conducted",
    },
    {
      label: "Total Earnings",
      value: `GH₵ ${mentorDashboard?.total_earnings?.toFixed(2) || "0.00"}`,
      icon: Wallet,
      color: "purple",
      tooltip: "Total monetary compensation earned from mentoring",
    },
  ];

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "mentees", label: "My Mentees" },
    { id: "requests", label: "Requests" },
    { id: "sessions", label: "Sessions" },
    { id: "earnings", label: "Earnings" },
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
              Mentor Dashboard
            </h1>
            <p className="text-gray-600">Manage your mentees and sessions</p>
          </div>
          {mentorDashboard?.rating && (
            <div className="flex items-center gap-1 bg-yellow-50 px-3 py-1.5 rounded-full">
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
              <span className="font-semibold text-gray-900">
                {mentorDashboard.rating.toFixed(1)}
              </span>
            </div>
          )}
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
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                />
              )}
              {tab.id === "requests" &&
                mentorDashboard?.pending_applications?.length > 0 && (
                  <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                    {mentorDashboard.pending_applications.length}
                  </span>
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
                      to="/dashboard/mentorship/schedule-session"
                      className="p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors text-center"
                    >
                      <Calendar className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Schedule Session
                      </span>
                    </Link>
                    <button
                      onClick={() => setActiveTab("requests")}
                      className="p-4 bg-yellow-50 rounded-xl hover:bg-yellow-100 transition-colors text-center"
                    >
                      <Users className="w-6 h-6 text-yellow-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Review Requests
                      </span>
                    </button>
                    <button
                      onClick={() => setActiveTab("earnings")}
                      className="p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors text-center"
                    >
                      <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        View Earnings
                      </span>
                    </button>
                    <Link
                      to="/dashboard/mentorship/resources"
                      className="p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-colors text-center"
                    >
                      <BookOpen className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <span className="text-sm font-medium text-gray-900">
                        Resources
                      </span>
                    </Link>
                  </div>
                </div>

                {/* Recent Requests */}
                {mentorDashboard?.pending_applications?.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900">
                        Pending Requests
                      </h3>
                      <button
                        onClick={() => setActiveTab("requests")}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        View All
                      </button>
                    </div>
                    <div className="space-y-3">
                      {mentorDashboard.pending_applications
                        .slice(0, 3)
                        .map((app) => (
                          <PendingRequestCard
                            key={app.id}
                            application={app}
                            onAccept={() => handleAcceptMentee(app.id)}
                            onReject={() => handleRejectMentee(app.id)}
                            processing={processingId === app.id}
                          />
                        ))}
                    </div>
                  </div>
                )}

                {/* Upcoming Sessions */}
                {mentorDashboard?.upcoming_sessions?.length > 0 && (
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
                      {mentorDashboard.upcoming_sessions
                        .slice(0, 3)
                        .map((session) => (
                          <SessionCard
                            key={session.id}
                            session={session}
                            onClick={() => handleViewSession(session)}
                            onComplete={() => handleStartComplete(session)}
                            isMentor={true}
                          />
                        ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "mentees" && (
              <motion.div
                key="mentees"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {mentorDashboard?.active_mentees?.length === 0 ? (
                  <EmptyState
                    icon={Users}
                    title="No Active Mentees"
                    description="You don't have any active mentees yet. Accept mentee requests to start mentoring."
                  />
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {mentorDashboard?.active_mentees?.map((mentee) => (
                      <MenteeCard key={mentee.id} mentee={mentee} />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "requests" && (
              <motion.div
                key="requests"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {mentorDashboard?.pending_applications?.length === 0 ? (
                  <EmptyState
                    icon={Clock}
                    title="No Pending Requests"
                    description="You don't have any pending mentee requests at the moment."
                  />
                ) : (
                  <div className="space-y-4">
                    {mentorDashboard?.pending_applications?.map((app) => (
                      <PendingRequestCard
                        key={app.id}
                        application={app}
                        onAccept={() => handleAcceptMentee(app.id)}
                        onReject={() => handleRejectMentee(app.id)}
                        onViewDetails={() => handleViewApplication(app)}
                        processing={processingId === app.id}
                        expanded
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
                {mentorDashboard?.all_sessions?.length === 0 ? (
                  <EmptyState
                    icon={Calendar}
                    title="No Sessions Yet"
                    description="You haven't conducted any sessions yet. Schedule a session with your mentees."
                    action={{
                      label: "Schedule Session",
                      to: "/dashboard/mentorship/schedule-session",
                    }}
                  />
                ) : (
                  <div className="space-y-4">
                    {mentorDashboard?.all_sessions?.map((session) => (
                      <SessionCard
                        key={session.id}
                        session={session}
                        detailed
                        onClick={() => handleViewSession(session)}
                        onComplete={() => handleStartComplete(session)}
                        isMentor={true}
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === "earnings" && (
              <motion.div
                key="earnings"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                {/* Wallet Card */}
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                        <Wallet className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="text-sm text-white/80">Wallet Balance</p>
                        <p className="text-3xl font-bold">
                          GH₵{" "}
                          {mentorDashboard?.wallet_balance?.toFixed(2) ||
                            "0.00"}
                        </p>
                      </div>
                    </div>
                    {mentorDashboard?.has_wallet && (
                      <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
                    <div>
                      <p className="text-white/70 text-sm">Total Donations</p>
                      <p className="text-xl font-semibold">
                        GH₵{" "}
                        {mentorDashboard?.total_donations_received?.toFixed(
                          2
                        ) || "0.00"}
                      </p>
                    </div>
                    <div>
                      <p className="text-white/70 text-sm">Donations Count</p>
                      <p className="text-xl font-semibold">
                        {mentorDashboard?.total_donations_count || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-white/70 text-sm">Total Donors</p>
                      <p className="text-xl font-semibold">
                        {mentorDashboard?.total_donors || 0}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Earnings Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-green-50 rounded-xl p-4">
                    <p className="text-sm text-green-600 mb-1">
                      Total Earnings
                    </p>
                    <p className="text-2xl font-bold text-green-700">
                      GH₵{" "}
                      {mentorDashboard?.total_earnings?.toFixed(2) || "0.00"}
                    </p>
                  </div>
                  <div className="bg-blue-50 rounded-xl p-4">
                    <p className="text-sm text-blue-600 mb-1">Pending Payout</p>
                    <p className="text-2xl font-bold text-blue-700">
                      GH₵{" "}
                      {mentorDashboard?.pending_earnings?.toFixed(2) || "0.00"}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-xl p-4">
                    <p className="text-sm text-purple-600 mb-1">
                      Sessions Paid
                    </p>
                    <p className="text-2xl font-bold text-purple-700">
                      {mentorDashboard?.paid_sessions || 0}
                    </p>
                  </div>
                </div>

                {/* Donation History */}
                {mentorDashboard?.donation_history?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      <Gift className="w-5 h-5 text-pink-500" />
                      Recent Donations Received
                    </h3>
                    <div className="bg-white border rounded-xl divide-y">
                      {mentorDashboard.donation_history.map((donation) => (
                        <div
                          key={donation.id}
                          className="p-4 flex items-center justify-between"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-pink-100 rounded-full flex items-center justify-center">
                              <Gift className="w-5 h-5 text-pink-500" />
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">
                                {donation.donor_name}
                              </p>
                              {donation.message && (
                                <p className="text-sm text-gray-500 italic">
                                  &quot;{donation.message}&quot;
                                </p>
                              )}
                              <p className="text-xs text-gray-400">
                                {donation.date}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-pink-600">
                              +GH₵ {donation.amount.toFixed(2)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Earnings History */}
                {mentorDashboard?.payment_history?.length > 0 ? (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">
                      Payment History
                    </h3>
                    <div className="bg-white border rounded-xl divide-y">
                      {mentorDashboard.payment_history.map((payment) => (
                        <div
                          key={payment.id}
                          className="p-4 flex items-center justify-between"
                        >
                          <div>
                            <p className="font-medium text-gray-900">
                              Session with {payment.mentee_name}
                            </p>
                            <p className="text-sm text-gray-500">
                              {payment.date}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-green-600">
                              +GH₵ {payment.amount.toFixed(2)}
                            </p>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                payment.status === "paid"
                                  ? "bg-green-100 text-green-700"
                                  : "bg-yellow-100 text-yellow-700"
                              }`}
                            >
                              {payment.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : mentorDashboard?.donation_history?.length === 0 ? (
                  <EmptyState
                    icon={DollarSign}
                    title="No Earnings Yet"
                    description="Complete paid sessions or receive donations to start earning."
                  />
                ) : null}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Application Details Modal */}
      <AnimatePresence>
        {selectedApplication && (
          <ApplicationDetailsModal
            application={selectedApplication}
            onClose={() => setSelectedApplication(null)}
            onAccept={() => handleAcceptMentee(selectedApplication.id)}
            onReject={() => handleRejectMentee(selectedApplication.id)}
            processing={processingId === selectedApplication.id}
          />
        )}
      </AnimatePresence>

      {/* Session Details Modal */}
      <AnimatePresence>
        {selectedSession && !showCompleteModal && (
          <SessionDetailsModal
            session={selectedSession}
            onClose={() => setSelectedSession(null)}
            onComplete={() => handleStartComplete(selectedSession)}
            isMentor={true}
          />
        )}
      </AnimatePresence>

      {/* Complete Session Modal */}
      <AnimatePresence>
        {showCompleteModal && selectedSession && (
          <CompleteSessionModal
            session={selectedSession}
            onClose={() => {
              setShowCompleteModal(false);
              setSelectedSession(null);
            }}
            onSubmit={(data) => handleCompleteSession(selectedSession.id, data)}
            processing={processingId === selectedSession.id}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function ApplicationDetailsModal({
  application,
  onClose,
  onAccept,
  onReject,
  processing,
}) {
  const offering =
    OFFERING_TYPE_LABELS[application.offering_type] ||
    OFFERING_TYPE_LABELS.none;

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
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xl">
                  {application.mentee?.first_name?.[0]}
                  {application.mentee?.last_name?.[0]}
                </span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {application.mentee?.first_name}{" "}
                  {application.mentee?.last_name}
                </h2>
                <p className="text-gray-600">
                  Year {application.mentee?.year || "N/A"} •{" "}
                  {application.mentee?.programme || "Computer Science"}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                    Pending Review
                  </span>
                  <span className="text-xs text-gray-500">
                    Applied{" "}
                    {application.created_at
                      ? new Date(application.created_at).toLocaleDateString()
                      : "Recently"}
                  </span>
                </div>
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
          {/* Mentorship Area */}
          {application.area && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                <Target className="w-4 h-4" />
                Mentorship Area
              </div>
              <div
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full"
                style={{
                  backgroundColor: `${application.area.color || "#3B82F6"}20`,
                  color: application.area.color || "#3B82F6",
                }}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: application.area.color || "#3B82F6",
                  }}
                />
                <span className="font-medium">{application.area.name}</span>
              </div>
            </div>
          )}

          {/* Introduction Message */}
          {application.message && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                <MessageSquare className="w-4 h-4" />
                Why They Want You as Their Mentor
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {application.message}
                </p>
              </div>
            </div>
          )}

          {/* Learning Goals */}
          {application.learning_goals && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                <Sparkles className="w-4 h-4" />
                Learning Goals
              </div>
              <div className="bg-blue-50 rounded-xl p-4">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {application.learning_goals}
                </p>
              </div>
            </div>
          )}

          {/* Current Skills */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {application.skills_description && (
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                  <Briefcase className="w-4 h-4" />
                  Current Skills
                </div>
                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-gray-700 text-sm whitespace-pre-wrap">
                    {application.skills_description}
                  </p>
                </div>
              </div>
            )}

            {/* Skills Tags */}
            {application.current_skills?.length > 0 && (
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                  <GraduationCap className="w-4 h-4" />
                  Skill Tags
                </div>
                <div className="flex flex-wrap gap-2">
                  {application.current_skills.map((skill) => (
                    <span
                      key={skill.id}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                    >
                      {skill.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Skills to Learn */}
          {application.skills_to_learn?.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                <BookOpen className="w-4 h-4" />
                Skills They Want to Learn
              </div>
              <div className="flex flex-wrap gap-2">
                {application.skills_to_learn.map((skill) => (
                  <span
                    key={skill.id}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
                  >
                    {skill.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* What They're Offering */}
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
              <Gift className="w-4 h-4" />
              What They&apos;re Offering
            </div>
            <div
              className={`rounded-xl p-4 bg-${offering.color}-50 border border-${offering.color}-100`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`font-medium text-${offering.color}-700`}>
                  {offering.label}
                </span>
                {application.offering_type === "monetary" &&
                  application.offering_amount && (
                    <span className="text-lg font-bold text-green-600">
                      GH₵ {parseFloat(application.offering_amount).toFixed(2)}
                    </span>
                  )}
              </div>
              {application.offering_description && (
                <p className="text-gray-600 text-sm">
                  {application.offering_description}
                </p>
              )}
              {application.offering_type === "none" && (
                <p className="text-gray-500 text-sm">
                  They&apos;re seeking volunteer mentorship
                </p>
              )}
            </div>
          </div>

          {/* Contact Info (if available) */}
          {(application.mentee?.email || application.mentee?.phone) && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-2">
                <Mail className="w-4 h-4" />
                Contact Information
              </div>
              <div className="flex flex-wrap gap-3">
                {application.mentee?.email && (
                  <a
                    href={`mailto:${application.mentee.email}`}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200 transition-colors"
                  >
                    <Mail className="w-4 h-4" />
                    {application.mentee.email}
                  </a>
                )}
                {application.mentee?.phone && (
                  <a
                    href={`tel:${application.mentee.phone}`}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200 transition-colors"
                  >
                    <Phone className="w-4 h-4" />
                    {application.mentee.phone}
                  </a>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t bg-gray-50 flex gap-3">
          <button
            onClick={onReject}
            disabled={processing}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-100 text-red-600 rounded-xl font-medium hover:bg-red-200 transition-all disabled:opacity-50"
          >
            <XCircle className="w-5 h-5" />
            Decline
          </button>
          <button
            onClick={onAccept}
            disabled={processing}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-all disabled:opacity-50"
          >
            {processing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <CheckCircle className="w-5 h-5" />
            )}
            Accept as Mentee
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function PendingRequestCard({
  application,
  onAccept,
  onReject,
  onViewDetails,
  processing,
  expanded,
}) {
  const offering =
    OFFERING_TYPE_LABELS[application.offering_type] ||
    OFFERING_TYPE_LABELS.none;

  return (
    <div
      className={`bg-gray-50 rounded-xl p-4 ${
        expanded ? "border border-gray-100" : ""
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold">
            {application.mentee?.first_name?.[0]}
            {application.mentee?.last_name?.[0]}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-gray-900">
                {application.mentee?.first_name} {application.mentee?.last_name}
              </h4>
              <p className="text-sm text-gray-500">
                Year {application.mentee?.year || "N/A"} •{" "}
                {application.mentee?.programme || "Computer Science"}
              </p>
            </div>
            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="p-2 hover:bg-white rounded-lg transition-colors text-blue-600"
                title="View full application"
              >
                <Eye className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Quick Info Pills */}
          <div className="flex flex-wrap gap-2 mt-2">
            {application.area && (
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full"
                style={{
                  backgroundColor: `${application.area.color || "#3B82F6"}20`,
                  color: application.area.color || "#3B82F6",
                }}
              >
                <Target className="w-3 h-3" />
                {application.area.name}
              </span>
            )}
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-${offering.color}-100 text-${offering.color}-700`}
            >
              <Gift className="w-3 h-3" />
              {offering.label}
              {application.offering_type === "monetary" &&
                application.offering_amount && (
                  <span className="font-medium">
                    {" "}
                    • GH₵{parseFloat(application.offering_amount).toFixed(0)}
                  </span>
                )}
            </span>
          </div>

          {/* Brief Message Preview */}
          {expanded && application.message && (
            <div className="mt-3 p-3 bg-white rounded-lg">
              <p className="text-sm text-gray-700 line-clamp-2">
                {application.message}
              </p>
              {application.message.length > 150 && onViewDetails && (
                <button
                  onClick={onViewDetails}
                  className="text-xs text-blue-600 hover:text-blue-700 mt-1"
                >
                  Read more...
                </button>
              )}
            </div>
          )}

          {/* Learning Goals Preview */}
          {expanded && application.learning_goals && (
            <div className="mt-2 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs font-medium text-blue-700 mb-1">
                Learning Goals:
              </p>
              <p className="text-sm text-gray-700 line-clamp-2">
                {application.learning_goals}
              </p>
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 mt-4">
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all"
          >
            <Eye className="w-4 h-4" />
            Details
          </button>
        )}
        <button
          onClick={onAccept}
          disabled={processing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all disabled:opacity-50"
        >
          {processing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          Accept
        </button>
        <button
          onClick={onReject}
          disabled={processing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-100 text-red-600 rounded-lg font-medium hover:bg-red-200 transition-all disabled:opacity-50"
        >
          <XCircle className="w-4 h-4" />
          Decline
        </button>
      </div>
    </div>
  );
}

function MenteeCard({ mentee }) {
  // mentee here is actually a relationship object from MentorshipRelationshipListSerializer
  const menteeInfo = mentee.mentee || {};
  const menteeName =
    mentee.mentee_name ||
    `${menteeInfo.first_name || ""} ${menteeInfo.last_name || ""}`.trim() ||
    "Unknown";
  const initials =
    menteeName
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "??";

  return (
    <div className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
          {menteeInfo.profile_picture ? (
            <img
              src={menteeInfo.profile_picture}
              alt={menteeName}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-white font-bold">{initials}</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900">{menteeName}</h4>
          <p className="text-sm text-gray-500">
            Year {menteeInfo.year || "N/A"} • Since{" "}
            {mentee.started_at
              ? new Date(mentee.started_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "N/A"}
          </p>
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
            <span>{mentee.sessions_completed || 0} sessions</span>
            <span>•</span>
            <span className="capitalize">
              {mentee.status_display || mentee.status}
            </span>
          </div>
        </div>
        <Link
          to={`/dashboard/mentorship/mentee/${mentee.id}`}
          className="p-2 hover:bg-white rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </Link>
      </div>
    </div>
  );
}

function SessionCard({ session, detailed, onClick, onComplete, isMentor }) {
  const isUpcoming =
    new Date(session.date || session.scheduled_date) > new Date();
  const isScheduled = session.status === "scheduled";
  const isCompleted = session.status === "completed";

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
              With{" "}
              {isMentor
                ? `${session.mentee?.first_name || ""} ${
                    session.mentee?.last_name || ""
                  }`
                : `${session.mentor?.first_name || ""} ${
                    session.mentor?.last_name || ""
                  }`}
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
              <p className="text-sm text-gray-700">{session.mentor_notes}</p>
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

          {isMentor && isScheduled && !isCompleted && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onComplete?.();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Mark Complete
            </button>
          )}

          {session.meeting_link && isUpcoming && !isCompleted && (
            <a
              href={session.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors ml-auto"
            >
              <ExternalLink className="w-4 h-4" />
              Join
            </a>
          )}
        </div>
      )}
    </div>
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

// Session Details Modal - Shows full session information
function SessionDetailsModal({ session, onClose, onComplete, isMentor }) {
  const isUpcoming =
    new Date(session.date || session.scheduled_date) > new Date();
  const isScheduled = session.status === "scheduled";
  const isCompleted = session.status === "completed";

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

          {/* Participants */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              Participants
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-xl p-4">
                <p className="text-xs text-blue-600 mb-1">Mentor</p>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {session.mentor?.first_name?.[0]}
                      {session.mentor?.last_name?.[0]}
                    </span>
                  </div>
                  <span className="font-medium text-gray-900">
                    {session.mentor?.full_name ||
                      `${session.mentor?.first_name} ${session.mentor?.last_name}`}
                  </span>
                </div>
              </div>
              <div className="bg-purple-50 rounded-xl p-4">
                <p className="text-xs text-purple-600 mb-1">Mentee</p>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {session.mentee?.first_name?.[0]}
                      {session.mentee?.last_name?.[0]}
                    </span>
                  </div>
                  <span className="font-medium text-gray-900">
                    {session.mentee?.full_name ||
                      `${session.mentee?.first_name} ${session.mentee?.last_name}`}
                  </span>
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
                    Mentee Feedback
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

          {isMentor && isScheduled && !isCompleted && (
            <button
              onClick={onComplete}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors"
            >
              <CheckCircle className="w-5 h-5" />
              Mark as Complete
            </button>
          )}

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
        </div>
      </motion.div>
    </motion.div>
  );
}

// Complete Session Modal - For mentors to add session notes
function CompleteSessionModal({ session, onClose, onSubmit, processing }) {
  const [mentorNotes, setMentorNotes] = useState("");
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!mentorNotes.trim()) {
      setError("Please add session notes");
      return;
    }

    const result = await onSubmit(mentorNotes);
    if (!result.success) {
      setError(result.error || "Failed to complete session");
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
        <div className="p-6 border-b bg-gradient-to-r from-green-50 to-blue-50">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Complete Session
              </h2>
              <p className="text-gray-600">
                Add notes about what was covered in this session
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
              With {session.mentee?.first_name} {session.mentee?.last_name} •{" "}
              {session.scheduled_date || session.date}
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Mentor Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Session Notes *
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Document what was covered, key takeaways, progress made, and any
              recommendations for your mentee.
            </p>
            <textarea
              value={mentorNotes}
              onChange={(e) => setMentorNotes(e.target.value)}
              placeholder="What was covered in this session? Key takeaways, progress made, advice given..."
              rows={6}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="bg-blue-50 rounded-xl p-4">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> Your mentee will be able to rate and
              provide feedback on this session after you mark it as complete.
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
            disabled={processing}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {processing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Completing...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Complete Session
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default MentorDashboardPage;
