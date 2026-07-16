import { motion } from "framer-motion";
import PropTypes from "prop-types";

const WaitingForGroup = ({ userData, eventData, selfGroupingEnabled, onStartSelfGrouping }) => {
  const formatDate = (dateString) => {
    if (!dateString) return "TBA";
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="p-6">
      <motion.div
        className="max-w-2xl mx-auto"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Self-Grouping Banner (if enabled) */}
        {selfGroupingEnabled && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-6 mb-6 text-white"
          >
            <div className="flex items-center gap-4">
              <div className="text-4xl">🤝</div>
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-1">Self-Grouping Available!</h3>
                <p className="text-blue-100 text-sm">
                  You can form your own team! Find classmates, send invitations, and create your group.
                </p>
              </div>
              <button
                onClick={onStartSelfGrouping}
                className="px-6 py-3 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-colors"
              >
                Form Team →
              </button>
            </div>
          </motion.div>
        )}

        {/* Main Waiting Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center mb-6">
          <div className="text-6xl mb-6">⏳</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {selfGroupingEnabled ? "Or Wait for Admin Assignment" : "Waiting for Group Formation"}
          </h2>
          <p className="text-gray-600 mb-6">
            {selfGroupingEnabled 
              ? "If you prefer, you can wait for the admin to assign you to a group automatically."
              : "Your group is being formed by the admin. You'll be notified once your group is ready."
            }
          </p>

          {/* Event Timeline */}
          {eventData?.timeline && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-6 text-left">
              <h4 className="font-semibold text-gray-900 mb-4 text-center">📅 Key Dates</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Group Formation:</span>
                  <span className="font-medium text-blue-700">
                    {formatDate(eventData.timeline.grouping_date)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">PM Election:</span>
                  <span className="font-medium text-gray-900">
                    {formatDate(eventData.timeline.voting_start)} - {formatDate(eventData.timeline.voting_end)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Submission Deadline:</span>
                  <span className="font-medium text-orange-600">
                    {formatDate(eventData.timeline.submission_deadline)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Presentation Day:</span>
                  <span className="font-medium text-green-600">
                    {formatDate(eventData.timeline.presentation_date)}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-left p-4 bg-gray-50 rounded-lg">
              <span className="text-2xl">📧</span>
              <span className="text-gray-700">
                You&apos;ll receive an email notification when your group is ready
              </span>
            </div>
            <div className="flex items-center gap-3 text-left p-4 bg-gray-50 rounded-lg">
              <span className="text-2xl">🔔</span>
              <span className="text-gray-700">
                Check back here regularly for updates
              </span>
            </div>
          </div>
        </div>

        {/* Your Registration Details */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Your Registration Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Name</p>
              <p className="font-semibold text-gray-900">
                {userData?.student_name}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Student ID</p>
              <p className="font-semibold text-gray-900">
                {userData?.student_id}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Email</p>
              <p className="font-semibold text-gray-900">{userData?.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Phone</p>
              <p className="font-semibold text-gray-900">{userData?.phone_number || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Year</p>
              <p className="font-semibold text-gray-900">
                Year {userData?.year} {userData?.is_deferred && "(Deferred)"}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Preferred Role</p>
              <p className="font-semibold text-gray-900">
                {userData?.preferred_role || userData?.preferred_role_display || "Not specified"}
              </p>
            </div>
          </div>

          {userData?.skills && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Skills</p>
              <div className="flex flex-wrap gap-2">
                {userData.skills.split(", ").map((skill, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Access Key Display */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg text-center">
            <p className="text-sm text-gray-600 mb-1">Your Access Key</p>
            <p className="text-2xl font-mono font-bold text-blue-600">
              {userData?.access_key}
            </p>
            <p className="text-xs text-gray-500 mt-2">Keep this safe - you&apos;ll need it to login</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

WaitingForGroup.propTypes = {
  userData: PropTypes.object,
  eventData: PropTypes.object,
  selfGroupingEnabled: PropTypes.bool,
  onStartSelfGrouping: PropTypes.func,
};

export default WaitingForGroup;
