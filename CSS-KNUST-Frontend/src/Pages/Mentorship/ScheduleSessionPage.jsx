import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Calendar,
  Clock,
  Video,
  MapPin,
  Users,
  Loader2,
  Check,
  AlertCircle,
} from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

export function ScheduleSessionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const menteeId = searchParams.get("mentee");

  const { mentorDashboard, fetchMentorDashboard, scheduleSession, loading } =
    useMentorship();

  const [formData, setFormData] = useState({
    relationship: menteeId || "", // This is actually the relationship ID
    date: "",
    start_time: "09:00",
    end_time: "10:00",
    session_type: "virtual",
    agenda: "",
    meeting_link: "",
    location: "",
  });

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMentorDashboard();
  }, []);

  // Get active mentees for selection
  const activeMentees = mentorDashboard?.active_mentees || [];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Validate times
    if (formData.start_time >= formData.end_time) {
      setError("End time must be after start time");
      setSubmitting(false);
      return;
    }

    // Prepare session data for the API
    const sessionData = {
      relationship: formData.relationship,
      date: formData.date,
      start_time: formData.start_time,
      end_time: formData.end_time,
      session_type: formData.session_type,
      agenda: formData.agenda || "",
      meeting_link: formData.meeting_link || "",
      location: formData.location || "",
    };

    const result = await scheduleSession(sessionData);

    if (result.success) {
      setSuccess(true);
      setSubmitting(false);
      setTimeout(() => {
        navigate("/dashboard/mentorship/mentor-dashboard");
      }, 2000);
    } else {
      setError(
        typeof result.error === "object"
          ? Object.values(result.error).flat().join(", ")
          : result.error
      );
      setSubmitting(false);
    }
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
            Access Denied
          </h2>
          <p className="text-gray-600 mb-6">
            You need to be an approved mentor to schedule sessions.
          </p>
          <Link
            to="/dashboard/mentorship"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Mentorship
          </Link>
        </motion.div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl p-8 shadow-lg max-w-md text-center"
        >
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Session Scheduled!
          </h2>
          <p className="text-gray-600 mb-4">
            Your mentoring session has been scheduled successfully. Your mentee
            will be notified.
          </p>
          <p className="text-sm text-gray-500">Redirecting...</p>
        </motion.div>
      </div>
    );
  }

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
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Schedule a Session
        </h1>
        <p className="text-gray-600">
          Set up a mentoring session with your mentee
        </p>
      </div>

      {/* Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm max-w-2xl"
      >
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Error</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Mentee Selection (via Relationship) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Mentee *
            </label>
            {activeMentees.length === 0 ? (
              <div className="p-4 bg-gray-50 rounded-lg text-center">
                <Users className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500 text-sm">No active mentees yet</p>
                <p className="text-xs text-gray-400 mt-1">
                  Accept mentee applications to schedule sessions
                </p>
              </div>
            ) : (
              <select
                value={formData.relationship}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    relationship: e.target.value,
                  }))
                }
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select a mentee</option>
                {activeMentees.map((mentee) => (
                  <option key={mentee.id} value={mentee.id}>
                    {mentee.mentee_name} ({mentee.area_name})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date *
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, date: e.target.value }))
                  }
                  min={new Date().toISOString().split("T")[0]}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Time *
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      start_time: e.target.value,
                    }))
                  }
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Time *
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      end_time: e.target.value,
                    }))
                  }
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
          </div>

          {/* Session Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Session Type *
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: "virtual", label: "Virtual", icon: Video },
                { value: "physical", label: "In-Person", icon: MapPin },
                { value: "hybrid", label: "Hybrid", icon: Users },
              ].map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      session_type: type.value,
                    }))
                  }
                  className={`p-3 rounded-xl border-2 flex flex-col items-center gap-2 transition-all ${
                    formData.session_type === type.value
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-gray-100 hover:border-gray-200 text-gray-600"
                  }`}
                >
                  <type.icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Meeting Link (for virtual/hybrid) */}
          {(formData.session_type === "virtual" ||
            formData.session_type === "hybrid") && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meeting Link
              </label>
              <div className="relative">
                <Video className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="url"
                  value={formData.meeting_link}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      meeting_link: e.target.value,
                    }))
                  }
                  placeholder="https://meet.google.com/..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Google Meet, Zoom, or Teams link
              </p>
            </div>
          )}

          {/* Location (for physical/hybrid) */}
          {(formData.session_type === "physical" ||
            formData.session_type === "hybrid") && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      location: e.target.value,
                    }))
                  }
                  placeholder="e.g., Library Room 203"
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Agenda / Topic */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Session Agenda *
            </label>
            <textarea
              value={formData.agenda}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, agenda: e.target.value }))
              }
              placeholder="e.g., Introduction to Python Data Structures, career guidance discussion, portfolio review..."
              rows={3}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Describe what you plan to cover in this session
            </p>
          </div>

          {/* Submit */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <Link
              to="/dashboard/mentorship/mentor-dashboard"
              className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting || activeMentees.length === 0}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Scheduling...
                </>
              ) : (
                <>
                  <Calendar className="w-4 h-4" />
                  Schedule Session
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default ScheduleSessionPage;
