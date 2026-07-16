import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Star,
  Clock,
  Users,
  Calendar,
  BookOpen,
  Send,
  Loader2,
  CheckCircle,
  AlertCircle,
  Target,
  Mail,
  Award,
  MessageSquare,
  Video,
  MapPin,
  Phone,
  GraduationCap,
  Briefcase,
  ChevronRight,
  CalendarPlus,
  History,
  TrendingUp,
} from "lucide-react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";

const SESSION_TYPE_ICONS = {
  physical: MapPin,
  virtual: Video,
  hybrid: Users,
};

export function MenteeProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { loading, mentorDashboard, fetchMentorDashboard } = useMentorship();
  const axiosInstance = useAxiosWithRefresh();

  const [relationship, setRelationship] = useState(null);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState(null);
  const [sessions, setSessions] = useState([]);

  // Ensure mentor dashboard data is loaded
  useEffect(() => {
    if (!mentorDashboard) {
      fetchMentorDashboard();
    }
  }, [mentorDashboard, fetchMentorDashboard]);

  // Filter sessions when mentorDashboard or relationship changes
  useEffect(() => {
    if (mentorDashboard?.all_sessions && id) {
      const relationshipSessions = mentorDashboard.all_sessions.filter(
        (session) => session.relationship === id
      );
      setSessions(relationshipSessions);
    }
  }, [mentorDashboard, id]);

  useEffect(() => {
    const loadRelationship = async () => {
      if (!id || id === "undefined") {
        setError("Invalid mentee ID");
        setLoadingData(false);
        return;
      }

      setLoadingData(true);
      try {
        // Fetch relationship details
        const response = await axiosInstance.get(
          `/mentorship/relationships/${id}/`
        );

        const data = response.data?.data || response.data;
        setRelationship(data);
      } catch (err) {
        console.error("Error loading mentee profile:", err);
        setError(
          err.response?.data?.message ||
            err.message ||
            "Failed to load mentee profile"
        );
      } finally {
        setLoadingData(false);
      }
    };

    loadRelationship();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loadingData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading mentee profile...</p>
        </div>
      </div>
    );
  }

  if (error || !relationship) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6">
        <div className="mb-6">
          <Link
            to="/dashboard/mentorship/mentor-dashboard"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
        <div className="bg-white rounded-2xl p-12 text-center shadow-sm max-w-md mx-auto">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {error || "Mentee Not Found"}
          </h3>
          <p className="text-gray-600 mb-6">
            The mentee profile you&apos;re looking for could not be loaded.
          </p>
          <Link
            to="/dashboard/mentorship/mentor-dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const mentee = relationship.mentee;
  const area = relationship.area;

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-700";
      case "completed":
        return "bg-blue-100 text-blue-700";
      case "paused":
        return "bg-yellow-100 text-yellow-700";
      case "ended":
        return "bg-gray-100 text-gray-700";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const upcomingSessions = sessions.filter(
    (s) => s.status === "scheduled" && new Date(s.scheduled_date) > new Date()
  );

  const completedSessions = sessions.filter((s) => s.status === "completed");

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/dashboard/mentorship/mentor-dashboard"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm overflow-hidden mb-6"
        >
          <div className="bg-gradient-to-r from-green-600 to-teal-600 h-32" />
          <div className="px-6 pb-6">
            <div className="flex flex-col md:flex-row md:items-end gap-4 -mt-16">
              <div className="w-32 h-32 bg-gradient-to-br from-green-500 to-teal-600 rounded-2xl flex items-center justify-center border-4 border-white shadow-lg">
                {mentee?.profile_picture ? (
                  <img
                    src={mentee.profile_picture}
                    alt={mentee?.first_name}
                    className="w-full h-full rounded-xl object-cover"
                  />
                ) : (
                  <span className="text-white font-bold text-4xl">
                    {mentee?.first_name?.[0]}
                    {mentee?.last_name?.[0]}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3 mb-1">
                  <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                    {mentee?.first_name} {mentee?.last_name}
                  </h1>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      relationship.status
                    )}`}
                  >
                    {relationship.status_display || relationship.status}
                  </span>
                </div>
                <p className="text-gray-600">
                  Year {mentee?.year || "N/A"} •{" "}
                  {mentee?.programme || "Computer Science"}
                </p>
                {(mentee?.personal_email || mentee?.student_email) && (
                  <div className="flex items-center gap-2 mt-2 text-gray-500">
                    <Mail className="w-4 h-4" />
                    <span className="text-sm">
                      {mentee.personal_email || mentee.student_email}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                <Link
                  to={`/dashboard/mentorship/schedule-session?mentee=${id}`}
                  className="px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <CalendarPlus className="w-5 h-5" />
                  Schedule Session
                </Link>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
        >
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
              <Calendar className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {relationship.sessions_completed || 0}
            </p>
            <p className="text-sm text-gray-500">Sessions Completed</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-2">
              <Clock className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {upcomingSessions.length}
            </p>
            <p className="text-sm text-gray-500">Upcoming Sessions</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {relationship.started_at
                ? Math.ceil(
                    (new Date() - new Date(relationship.started_at)) /
                      (1000 * 60 * 60 * 24 * 7)
                  )
                : 0}
            </p>
            <p className="text-sm text-gray-500">Weeks Together</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center mb-2">
              <Target className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-lg font-bold text-gray-900 truncate">
              {area?.name || "General"}
            </p>
            <p className="text-sm text-gray-500">Focus Area</p>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="md:col-span-2 space-y-6"
          >
            {/* Mentorship Details */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-gray-400" />
                Mentorship Details
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">Started</span>
                  <span className="font-medium text-gray-900">
                    {relationship.started_at
                      ? new Date(relationship.started_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          }
                        )
                      : "N/A"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">Last Session</span>
                  <span className="font-medium text-gray-900">
                    {relationship.last_session_date
                      ? new Date(
                          relationship.last_session_date
                        ).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : "No sessions yet"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">Next Session</span>
                  <span className="font-medium text-gray-900">
                    {relationship.next_session_date
                      ? new Date(
                          relationship.next_session_date
                        ).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : "Not scheduled"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-gray-600">Focus Area</span>
                  <div
                    className="flex items-center gap-2 px-3 py-1 rounded-full"
                    style={{
                      backgroundColor: `${area?.color || "#3B82F6"}15`,
                    }}
                  >
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: area?.color || "#3B82F6" }}
                    />
                    <span
                      className="text-sm font-medium"
                      style={{ color: area?.color || "#3B82F6" }}
                    >
                      {area?.name || "General Mentorship"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Sessions */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-gray-400" />
                  Recent Sessions
                </h2>
                {sessions.length > 3 && (
                  <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                    View All
                  </button>
                )}
              </div>
              {sessions.length > 0 ? (
                <div className="space-y-3">
                  {sessions.slice(0, 5).map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                    >
                      <div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          session.status === "completed"
                            ? "bg-green-100"
                            : session.status === "scheduled"
                            ? "bg-blue-100"
                            : "bg-gray-100"
                        }`}
                      >
                        {session.status === "completed" ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <Calendar className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          {session.title ||
                            `Session #${session.session_number || "?"}`}
                        </p>
                        <p className="text-sm text-gray-500">
                          {new Date(
                            session.scheduled_date || session.date
                          ).toLocaleDateString("en-US", {
                            weekday: "short",
                            month: "short",
                            day: "numeric",
                          })}
                          {session.scheduled_time &&
                            ` at ${session.scheduled_time}`}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          session.status === "completed"
                            ? "bg-green-100 text-green-700"
                            : session.status === "scheduled"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {session.status_display || session.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No sessions recorded yet</p>
                  <Link
                    to={`/dashboard/mentorship/schedule-session?mentee=${id}`}
                    className="inline-flex items-center gap-2 mt-4 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    <CalendarPlus className="w-4 h-4" />
                    Schedule First Session
                  </Link>
                </div>
              )}
            </div>
          </motion.div>

          {/* Right Column */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-6"
          >
            {/* Mentee Info */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-gray-400" />
                Mentee Info
              </h2>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <GraduationCap className="w-4 h-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Year</p>
                    <p className="font-medium text-gray-900">
                      Year {mentee?.year || "N/A"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Briefcase className="w-4 h-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Programme</p>
                    <p className="font-medium text-gray-900">
                      {mentee?.programme || "Computer Science"}
                    </p>
                  </div>
                </div>
                {mentee?.phone && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Phone className="w-4 h-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Phone</p>
                      <p className="font-medium text-gray-900">
                        {mentee.phone}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-green-600 to-teal-600 rounded-xl p-6 text-white">
              <h3 className="font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link
                  to={`/dashboard/mentorship/schedule-session?mentee=${id}`}
                  className="flex items-center justify-between w-full px-4 py-3 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <CalendarPlus className="w-4 h-4" />
                    Schedule Session
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
                <a
                  href={`mailto:${
                    mentee?.personal_email || mentee?.student_email || ""
                  }`}
                  className="flex items-center justify-between w-full px-4 py-3 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Send Email
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </a>
                <button className="flex items-center justify-between w-full px-4 py-3 bg-white/10 hover:bg-white/20 rounded-lg transition-colors">
                  <span className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    Send Message
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default MenteeProfilePage;
