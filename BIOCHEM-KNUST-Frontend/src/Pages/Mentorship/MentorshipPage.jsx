import  { useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  GraduationCap,
  Award,
  Clock,
  ChevronRight,
  BookOpen,
  UserCheck,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";


export function MentorshipPage() {

  const {
    areas,
    eligibility,
    fetchAreas,
    checkEligibility,
    loading,
    myMentorApplications,
    myMenteeApplications,
    fetchMyMentorApplications,
    fetchMyMenteeApplications,
  } = useMentorship();


  // Ensure arrays are always arrays for safe filtering
  const mentorApps = Array.isArray(myMentorApplications)
    ? myMentorApplications
    : [];
  const menteeApps = Array.isArray(myMenteeApplications)
    ? myMenteeApplications
    : [];
  const safeAreas = Array.isArray(areas) ? areas : [];

  useEffect(() => {
    fetchAreas();
    checkEligibility();
    fetchMyMentorApplications();
    fetchMyMenteeApplications();
  }, []);

  const getStatusColor = (status) => {
    const colors = {
      draft: "bg-gray-100 text-gray-700",
      submitted: "bg-blue-100 text-blue-700",
      interview_scheduled: "bg-orange-100 text-orange-700",
      interview_completed: "bg-purple-100 text-purple-700",
      approved: "bg-green-100 text-green-700",
      rejected: "bg-red-100 text-red-700",
      pending: "bg-yellow-100 text-yellow-700",
      accepted: "bg-green-100 text-green-700",
      withdrawn: "bg-gray-100 text-gray-700",
    };
    return colors[status] || "bg-gray-100 text-gray-700";
  };

 
  const approvedMentorApp = mentorApps.find((app) => app.status === "approved");

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      {/* Header */}
      <div className="mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 mb-2"
        >
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
            <Users className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            Mentorship
          </h1>
        </motion.div>
        <p className="text-gray-600 ml-12">
          Connect with mentors, grow your skills, and give back to the community
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div
            className="flex items-center gap-3"
            title="Total number of mentorship areas available in the program"
          >
            <div className="p-2 bg-blue-100 rounded-lg">
              <BookOpen className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {safeAreas.length}
              </p>
              <p className="text-sm text-gray-500">Areas</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div
            className="flex items-center gap-3"
            title={
              approvedMentorApp
                ? "You are an approved mentor and can accept mentees"
                : "You are not yet an approved mentor"
            }
          >
            <div className="p-2 bg-green-100 rounded-lg">
              <UserCheck className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {approvedMentorApp ? "Active" : "—"}
              </p>
              <p className="text-sm text-gray-500">Mentor Status</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div
            className="flex items-center gap-3"
            title="Number of mentors who have accepted your mentee applications"
          >
            <div className="p-2 bg-purple-100 rounded-lg">
              <GraduationCap className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {menteeApps.filter((a) => a.status === "accepted")?.length || 0}
              </p>
              <p className="text-sm text-gray-500">My Mentors</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div
            className="flex items-center gap-3"
            title="Number of mentee applications awaiting mentor response"
          >
            <div className="p-2 bg-orange-100 rounded-lg">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {menteeApps.filter((a) => a.status === "pending")?.length || 0}
              </p>
              <p className="text-sm text-gray-500">Pending</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Action Cards */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Become a Mentor Card */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-white/20 rounded-xl">
              <Award className="w-8 h-8" />
            </div>
            {eligibility?.is_approved_mentor && (
              <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-medium">
                ✓ Approved Mentor
              </span>
            )}
          </div>
          <h2 className="text-xl font-bold mb-2">Become a Mentor</h2>
          <p className="text-blue-100 mb-4 text-sm">
            Share your knowledge and experience with fellow students. Guide them
            through their academic journey and beyond.
          </p>

          {/* Eligibility Check */}
          {loading ? (
            <div className="flex items-center gap-2 text-blue-100">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Checking eligibility...</span>
            </div>
          ) : eligibility?.is_approved_mentor ? (
            <Link
              to="/dashboard/mentorship/mentor-dashboard"
              className="inline-flex items-center gap-2 bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              Go to Mentor Dashboard
              <ChevronRight className="w-4 h-4" />
            </Link>
          ) : eligibility?.has_pending_application ? (
            <Link
              to="/dashboard/mentorship/my-applications"
              className="inline-flex items-center gap-2 bg-white/20 text-white px-4 py-2 rounded-lg font-medium hover:bg-white/30 transition-colors"
            >
              <Clock className="w-4 h-4" />
              View Application Status
            </Link>
          ) : eligibility?.is_eligible ? (
            <Link
              to="/dashboard/mentorship/apply-mentor"
              className="inline-flex items-center gap-2 bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              Apply Now
              <ChevronRight className="w-4 h-4" />
            </Link>
          ) : (
            <div className="space-y-3">
              <div className="flex items-start gap-2 bg-white/10 rounded-lg p-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-sm">Not Eligible</p>
                  <p className="text-xs text-blue-100">
                    {eligibility?.message ||
                      "First-year students cannot apply as mentors."}
                  </p>
                </div>
              </div>
              <Link
                to="/dashboard/mentorship/mentee-dashboard"
                className="inline-flex items-center gap-2 bg-white/20 text-white px-4 py-2 rounded-lg font-medium hover:bg-white/30 transition-colors"
              >
                <GraduationCap className="w-4 h-4" />
                Go to Mentee Dashboard
              </Link>
            </div>
          )}
        </motion.div>

        {/* Find a Mentor Card */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-white/20 rounded-xl">
              <GraduationCap className="w-8 h-8" />
            </div>
          </div>
          <h2 className="text-xl font-bold mb-2">Find a Mentor</h2>
          <p className="text-purple-100 mb-4 text-sm">
            Browse approved mentors across various areas. Apply to learn from
            experienced students who can help you grow.
          </p>

          <Link
            to="/dashboard/mentorship/browse-mentors"
            className="inline-flex items-center gap-2 bg-white text-purple-600 px-4 py-2 rounded-lg font-medium hover:bg-purple-50 transition-colors"
          >
            Browse Mentors
            <ChevronRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </div>

      {/* Mentorship Areas */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Mentorship Areas
          </h2>
          <span className="text-sm text-gray-500">
            {safeAreas.length} areas available
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {safeAreas.slice(0, 10).map((area, index) => (
              <motion.div
                key={area.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * index }}
                className="flex items-center gap-2 p-3 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 transition-all cursor-pointer"
                style={{ borderLeftColor: area.color, borderLeftWidth: 3 }}
                title={`${area.name}: ${
                  area.mentor_count || 0
                } approved mentor${
                  (area.mentor_count || 0) !== 1 ? "s" : ""
                } available in this area`}
              >
                <span className="text-sm font-medium text-gray-700 truncate">
                  {area.name}
                </span>
                <span
                  className="text-xs text-gray-400 ml-auto"
                  title={`${area.mentor_count || 0} approved mentor${
                    (area.mentor_count || 0) !== 1 ? "s" : ""
                  } in ${area.name}`}
                >
                  {area.mentor_count || 0}
                </span>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* My Applications Summary */}
      {(mentorApps.length > 0 || menteeApps.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            My Applications
          </h2>

          <div className="space-y-3">
            {/* Mentor Applications */}
            {mentorApps.slice(0, 3).map((app) => (
              <div
                key={app.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Award className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 text-sm">
                      Mentor Application
                    </p>
                    <p className="text-xs text-gray-500">
                      {app.areas?.map((a) => a.name || a).join(", ") ||
                        "Multiple areas"}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    app.status
                  )}`}
                >
                  {app.status_display || app.status?.replace("_", " ")}
                </span>
              </div>
            ))}

            {/* Mentee Applications */}
            {menteeApps.slice(0, 3).map((app) => (
              <div
                key={app.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <GraduationCap className="w-4 h-4 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 text-sm">
                      Application to{" "}
                      {app.mentor?.full_name || app.mentor_name || "Mentor"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {app.area?.name || app.area_name || "General"}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    app.status
                  )}`}
                >
                  {app.status_display || app.status}
                </span>
              </div>
            ))}
          </div>

          <Link
            to="/dashboard/mentorship/my-applications"
            className="inline-flex items-center gap-1 text-blue-600 text-sm font-medium mt-4 hover:text-blue-700"
          >
            View all applications
            <ChevronRight className="w-4 h-4" />
          </Link>
        </motion.div>
      )}
    </div>
  );
}

export default MentorshipPage;
