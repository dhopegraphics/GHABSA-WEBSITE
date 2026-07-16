import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Calendar,
  Users,
  ChevronRight,
  Loader2,
  Eye,
  Edit,
  Trash2,
  RefreshCw,
  MapPin,
  Video,
  ExternalLink,
  User,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

const STATUS_CONFIG = {
  draft: {
    bg: "bg-gray-100",
    text: "text-gray-700",
    border: "border-gray-200",
    icon: FileText,
    label: "Draft",
  },
  submitted: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    border: "border-yellow-200",
    icon: Clock,
    label: "Submitted",
  },
  pending: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    border: "border-yellow-200",
    icon: Clock,
    label: "Pending Review",
  },
  interview_scheduled: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    border: "border-blue-200",
    icon: Calendar,
    label: "Interview Scheduled",
  },
  interview_completed: {
    bg: "bg-indigo-100",
    text: "text-indigo-700",
    border: "border-indigo-200",
    icon: CheckCircle,
    label: "Interview Completed",
  },
  approved: {
    bg: "bg-green-100",
    text: "text-green-700",
    border: "border-green-200",
    icon: CheckCircle,
    label: "Approved",
  },
  rejected: {
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-200",
    icon: XCircle,
    label: "Rejected",
  },
  accepted: {
    bg: "bg-green-100",
    text: "text-green-700",
    border: "border-green-200",
    icon: CheckCircle,
    label: "Accepted",
  },
  withdrawn: {
    bg: "bg-gray-100",
    text: "text-gray-700",
    border: "border-gray-200",
    icon: XCircle,
    label: "Withdrawn",
  },
};

export function MyApplicationsPage() {
  const navigate = useNavigate();
  const { myApplications, fetchMyApplications, loading } = useMentorship();

  const [activeFilter, setActiveFilter] = useState("all");
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    fetchMyApplications();
  }, []);

  // Ensure arrays with safety checks
  const mentorApplications = Array.isArray(myApplications?.mentor_applications)
    ? myApplications.mentor_applications
    : [];
  const menteeApplications = Array.isArray(myApplications?.mentee_applications)
    ? myApplications.mentee_applications
    : [];

  const filteredMentorApps =
    activeFilter === "all"
      ? mentorApplications
      : mentorApplications.filter((app) => app.status === activeFilter);

  const filteredMenteeApps =
    activeFilter === "all"
      ? menteeApplications
      : menteeApplications.filter((app) => app.status === activeFilter);

  const allStatuses = [
    ...new Set([
      ...mentorApplications.map((a) => a.status),
      ...menteeApplications.map((a) => a.status),
    ]),
  ];

  if (loading && !myApplications) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

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
              My Applications
            </h1>
            <p className="text-gray-600">
              Track your mentor and mentee applications
            </p>
          </div>
          <button
            onClick={() => fetchMyApplications()}
            className="p-2 hover:bg-white rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw
              className={`w-5 h-5 text-gray-500 ${
                loading ? "animate-spin" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 mb-6 shadow-sm">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setActiveFilter("all")}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeFilter === "all"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All
          </button>
          {allStatuses.map((status) => {
            const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
            return (
              <button
                key={status}
                onClick={() => setActiveFilter(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  activeFilter === status
                    ? `${config.bg} ${config.text}`
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {config.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Mentor Applications */}
      {filteredMentorApps.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            Mentor Applications
          </h2>
          <div className="space-y-4">
            {filteredMentorApps.map((application) => (
              <MentorApplicationCard
                key={application.id}
                application={application}
                expanded={expandedId === `mentor-${application.id}`}
                onToggle={() =>
                  setExpandedId(
                    expandedId === `mentor-${application.id}`
                      ? null
                      : `mentor-${application.id}`
                  )
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Mentee Applications */}
      {filteredMenteeApps.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-green-600" />
            Mentee Applications
          </h2>
          <div className="space-y-4">
            {filteredMenteeApps.map((application) => (
              <MenteeApplicationCard
                key={application.id}
                application={application}
                expanded={expandedId === `mentee-${application.id}`}
                onToggle={() =>
                  setExpandedId(
                    expandedId === `mentee-${application.id}`
                      ? null
                      : `mentee-${application.id}`
                  )
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredMentorApps.length === 0 && filteredMenteeApps.length === 0 && (
        <div className="bg-white rounded-2xl p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {activeFilter === "all"
              ? "No Applications Yet"
              : "No Matching Applications"}
          </h3>
          <p className="text-gray-600 mb-6 max-w-sm mx-auto">
            {activeFilter === "all"
              ? "You haven't submitted any applications yet. Start your mentorship journey today!"
              : "No applications match the selected filter."}
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              to="/dashboard/mentorship/apply-mentor"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Become a Mentor
            </Link>
            <Link
              to="/dashboard/mentorship/find-mentor"
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
            >
              Find a Mentor
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function MentorApplicationCard({ application, expanded, onToggle }) {
  const config = STATUS_CONFIG[application.status] || STATUS_CONFIG.pending;
  const StatusIcon = config.icon;

  return (
    <motion.div
      layout
      className={`bg-white rounded-xl shadow-sm border ${config.border} overflow-hidden`}
    >
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`flex items-center gap-1.5 px-3 py-1 text-sm font-medium rounded-full ${config.bg} ${config.text}`}
              >
                <StatusIcon className="w-4 h-4" />
                {config.label}
              </span>
              <span className="text-sm text-gray-500">#{application.id}</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">
              Mentor Application
            </h3>
            <p className="text-sm text-gray-500">
              Applied on {application.created_at || "N/A"}
            </p>
            {application.areas && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {application.areas.map((area) => (
                  <span
                    key={area.id}
                    className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-700"
                  >
                    {area.name}
                  </span>
                ))}
              </div>
            )}
          </div>
          <ChevronRight
            className={`w-5 h-5 text-gray-400 transition-transform ${
              expanded ? "rotate-90" : ""
            }`}
          />
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0 border-t border-gray-100">
              {/* Experience */}
              {application.experience_description && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    Experience
                  </h4>
                  <p className="text-sm text-gray-600">
                    {application.experience_description}
                  </p>
                </div>
              )}

              {/* Interview Info */}
              {(application.interview_details ||
                application.interview_date) && (
                <div className="mb-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <h4 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Interview Details
                  </h4>
                  <div className="space-y-2">
                    {/* Interviewer */}
                    {application.assigned_interviewer_name && (
                      <div className="flex items-center gap-2 text-sm">
                        <User className="w-4 h-4 text-blue-600" />
                        <span className="text-gray-600">Interviewer:</span>
                        <span className="font-medium text-gray-900">
                          {application.assigned_interviewer_name}
                        </span>
                      </div>
                    )}

                    {/* Date & Time */}
                    {application.interview_details?.date && (
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="w-4 h-4 text-blue-600" />
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium text-gray-900">
                          {new Date(
                            application.interview_details.date
                          ).toLocaleDateString("en-US", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </span>
                      </div>
                    )}

                    {application.interview_details?.start_time && (
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-blue-600" />
                        <span className="text-gray-600">Time:</span>
                        <span className="font-medium text-gray-900">
                          {application.interview_details.start_time} -{" "}
                          {application.interview_details.end_time}
                        </span>
                      </div>
                    )}

                    {/* Interview Type */}
                    {application.interview_details?.interview_type && (
                      <div className="flex items-center gap-2 text-sm">
                        {application.interview_details.interview_type ===
                        "virtual" ? (
                          <Video className="w-4 h-4 text-blue-600" />
                        ) : (
                          <MapPin className="w-4 h-4 text-blue-600" />
                        )}
                        <span className="text-gray-600">Type:</span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            application.interview_details.interview_type ===
                            "virtual"
                              ? "bg-purple-100 text-purple-700"
                              : application.interview_details.interview_type ===
                                "physical"
                              ? "bg-green-100 text-green-700"
                              : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {application.interview_details
                            .interview_type_display ||
                            application.interview_details.interview_type}
                        </span>
                      </div>
                    )}

                    {/* Location (for physical) */}
                    {application.interview_details?.location && (
                      <div className="flex items-start gap-2 text-sm">
                        <MapPin className="w-4 h-4 text-blue-600 mt-0.5" />
                        <span className="text-gray-600">Location:</span>
                        <span className="font-medium text-gray-900">
                          {application.interview_details.location}
                        </span>
                      </div>
                    )}

                    {/* Meeting Link (for virtual) */}
                    {(application.interview_details?.meeting_link ||
                      application.interview_link) && (
                      <div className="flex items-center gap-2 text-sm mt-3 pt-3 border-t border-blue-200">
                        <Video className="w-4 h-4 text-blue-600" />
                        <span className="text-gray-600">Meeting Link:</span>
                        <a
                          href={
                            application.interview_details?.meeting_link ||
                            application.interview_link
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium hover:underline"
                        >
                          Join Meeting
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    )}

                    {/* Notes */}
                    {application.interview_details?.notes && (
                      <div className="mt-3 pt-3 border-t border-blue-200">
                        <p className="text-xs text-gray-500 mb-1">Notes:</p>
                        <p className="text-sm text-gray-700">
                          {application.interview_details.notes}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Rejection Reason */}
              {application.status === "rejected" &&
                application.rejection_reason && (
                  <div className="mb-4 p-3 bg-red-50 rounded-lg">
                    <h4 className="text-sm font-medium text-red-700 mb-1">
                      Rejection Reason
                    </h4>
                    <p className="text-sm text-red-600">
                      {application.rejection_reason}
                    </p>
                  </div>
                )}

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2">
                {application.status === "approved" && (
                  <Link
                    to="/dashboard/mentorship/mentor-dashboard"
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
                  >
                    Go to Mentor Dashboard
                  </Link>
                )}
                {application.status === "draft" && (
                  <Link
                    to={`/dashboard/mentorship/apply?resume=${application.id}`}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Continue Application
                  </Link>
                )}
                {(application.status === "submitted" ||
                  application.status === "interview_scheduled") &&
                  application.interview_details?.meeting_link && (
                    <a
                      href={application.interview_details.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                      <Video className="w-4 h-4" />
                      Join Meeting
                    </a>
                  )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function MenteeApplicationCard({ application, expanded, onToggle }) {
  const config = STATUS_CONFIG[application.status] || STATUS_CONFIG.pending;
  const StatusIcon = config.icon;

  return (
    <motion.div
      layout
      className={`bg-white rounded-xl shadow-sm border ${config.border} overflow-hidden`}
    >
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">
                {application.mentor?.first_name?.[0]}
                {application.mentor?.last_name?.[0]}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full ${config.bg} ${config.text}`}
                >
                  <StatusIcon className="w-3 h-3" />
                  {config.label}
                </span>
                {application.area && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{
                      backgroundColor: `${
                        application.area.color || "#3B82F6"
                      }20`,
                      color: application.area.color || "#3B82F6",
                    }}
                  >
                    {application.area.name}
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-gray-900">
                Application to{" "}
                {application.mentor?.first_name ||
                  application.mentor?.full_name}{" "}
                {application.mentor?.last_name}
              </h3>
              <p className="text-sm text-gray-500">
                Applied on {application.created_at || "N/A"}
              </p>
            </div>
          </div>
          <ChevronRight
            className={`w-5 h-5 text-gray-400 transition-transform ${
              expanded ? "rotate-90" : ""
            }`}
          />
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0 border-t border-gray-100">
              {/* Area Info */}
              {application.area && (
                <div
                  className="mb-4 p-3 rounded-lg"
                  style={{
                    backgroundColor: `${application.area.color || "#3B82F6"}10`,
                  }}
                >
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    Mentorship Area
                  </h4>
                  <p
                    className="text-sm font-medium"
                    style={{ color: application.area.color || "#3B82F6" }}
                  >
                    {application.area.name}
                  </p>
                </div>
              )}

              {/* Your Message */}
              {application.message && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    Your Message
                  </h4>
                  <p className="text-sm text-gray-600">{application.message}</p>
                </div>
              )}

              {/* Learning Goals */}
              {application.learning_goals && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-700 mb-1">
                    Learning Goals
                  </h4>
                  <p className="text-sm text-gray-600">
                    {application.learning_goals}
                  </p>
                </div>
              )}

              {/* What You Offered */}
              {application.offering_type &&
                application.offering_type !== "none" && (
                  <div className="mb-4 p-3 bg-purple-50 rounded-lg">
                    <h4 className="text-sm font-medium text-purple-700 mb-1">
                      What You Offered
                    </h4>
                    <p className="text-sm text-gray-600 capitalize">
                      {application.offering_type === "monetary"
                        ? `Monetary: GH₵ ${application.offering_amount || 0}`
                        : application.offering_type.replace("_", " ")}
                      {application.offering_description &&
                        ` - ${application.offering_description}`}
                    </p>
                  </div>
                )}

              {/* Mentor Info */}
              {application.mentor && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Mentor Details
                  </h4>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Areas:</span>{" "}
                    {application.mentor.areas?.map((a) => a.name).join(", ") ||
                      "N/A"}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Session Type:</span>{" "}
                    {application.mentor.session_type || "N/A"}
                  </p>
                </div>
              )}

              {/* Rejection Reason */}
              {application.status === "rejected" &&
                application.rejection_reason && (
                  <div className="mb-4 p-3 bg-red-50 rounded-lg">
                    <h4 className="text-sm font-medium text-red-700 mb-1">
                      Rejection Reason
                    </h4>
                    <p className="text-sm text-red-600">
                      {application.rejection_reason}
                    </p>
                  </div>
                )}

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2">
                {application.status === "accepted" && (
                  <Link
                    to="/dashboard/mentorship/mentee-dashboard"
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
                  >
                    Go to Mentee Dashboard
                  </Link>
                )}
                {application.mentor?.id && (
                  <Link
                    to={`/dashboard/mentorship/mentor/${application.mentor.id}`}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    View Mentor
                  </Link>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default MyApplicationsPage;
