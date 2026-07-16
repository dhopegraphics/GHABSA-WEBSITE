import { useState, useEffect, useContext } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import PropTypes from "prop-types";
import { UserContext } from "../../../../Context/UserContext";
import { AlertCircle, LogIn, Users, Award, Clock } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ParticipantRegistrationForm = ({ eventId }) => {
  const { user } = useContext(UserContext);
  const [formData, setFormData] = useState({
    student_id: "",
    student_name: "",
    email: "",
    phone_number: "",
    year: 2,
    is_deferred: false,
    preferred_role: "",
    skills: [],
  });

  const [loading, setLoading] = useState(false);
  const [fetchingUser, setFetchingUser] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [accessKey, setAccessKey] = useState("");
  const [registrationData, setRegistrationData] = useState(null);

  // Fetch user details and pre-fill form when logged in
  useEffect(() => {
    const fetchUserDetails = async () => {
      if (!user?.access || !eventId) return;
      
      setFetchingUser(true);
      try {
        const response = await axios.get(
          `${API_BASE_URL}/codequest/user/details/?event_id=${eventId}`,
          {
            headers: { Authorization: `Bearer ${user.access}` }
          }
        );
        
        const userData = response.data.user;
        const registrationStatus = response.data.registration_status;
        const participantDetails = response.data.participant;
        const consultantDetails = response.data.consultant;
        
        // Check if already registered
        if (registrationStatus.is_registered) {
          setRegistrationData({
            type: registrationStatus.registered_as,
            participant: participantDetails,
            consultant: consultantDetails,
          });
          return;
        }
        
        // Pre-fill form with user data
        setFormData(prev => ({
          ...prev,
          student_id: userData.student_id || '',
          student_name: userData.full_name || '',
          email: userData.email || '',
          phone_number: userData.phone || '',
          year: userData.year || 2,
          is_deferred: userData.year > 2,
        }));
      } catch (err) {
        console.error("Error fetching user details:", err);
      } finally {
        setFetchingUser(false);
      }
    };

    fetchUserDetails();
  }, [user, eventId]);

  // Available options - match backend ROLE_CHOICES
  const roles = [
    { value: "Frontend", label: "Frontend Developer" },
    { value: "Backend", label: "Backend Developer" },
    { value: "UI/UX", label: "UI/UX Designer" },
    { value: "Mobile", label: "Mobile Developer" },
    { value: "Data Science", label: "Data Scientist" },
    { value: "DevOps", label: "DevOps Engineer" },
    { value: "QA", label: "Quality Assurance" },
    { value: "Other", label: "Other" },
  ];

  const technologies = [
    "React",
    "React Native",
    "Flutter",
    "Node.js",
    "Python",
    "Django",
    "MongoDB",
    "PostgreSQL",
    "Firebase",
    "Git",
    "Docker",
    "TypeScript",
    "JavaScript",
    "Java",
    "Kotlin",
    "Swift",
  ];

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    // Auto-check deferred if Year 3 or 4 is selected
    if (name === "year") {
      const yearValue = parseInt(value);
      setFormData((prev) => ({
        ...prev,
        year: yearValue,
        is_deferred: yearValue === 3 || yearValue === 4,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: type === "checkbox" ? checked : value,
      }));
    }
  };

  const handleSkillToggle = (skill) => {
    setFormData((prev) => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter((s) => s !== skill)
        : [...prev.skills, skill],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!user?.access) {
      setError("You must be logged in to register. Please login first.");
      setLoading(false);
      return;
    }

    if (!eventId) {
      setError("No active event found. Please try again later.");
      setLoading(false);
      return;
    }

    try {
      // Prepare data for API - match backend field names
      const submitData = {
        event: eventId,
        student_id: formData.student_id,
        student_name: formData.student_name,
        email: formData.email,
        phone_number: formData.phone_number,
        year: formData.year,
        is_deferred: formData.is_deferred,
        preferred_role: formData.preferred_role,
        skills: formData.skills.join(", "),
      };

      // API call with authentication
      const response = await axios.post(
        `${API_BASE_URL}/codequest/register/student/`,
        submitData,
        {
          headers: { Authorization: `Bearer ${user.access}` }
        }
      );

      // Success - show access key
      setAccessKey(response.data.access_key);
      setSuccess(true);
    } catch (err) {
      // Handle 401 Unauthorized
      if (err.response?.status === 401) {
        setError("Your session has expired. Please login again.");
        return;
      }
      
      // Handle validation errors from backend
      const errorData = err.response?.data;
      if (errorData && typeof errorData === 'object') {
        // Format field-specific errors
        const errorMessages = Object.entries(errorData)
          .map(([field, messages]) => {
            const fieldLabel = field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            return `${fieldLabel}: ${Array.isArray(messages) ? messages.join(', ') : messages}`;
          })
          .join('\n');
        setError(errorMessages || "Registration failed. Please try again.");
      } else {
        setError(err.response?.data?.message || "Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  // Already registered state - detailed view
  if (registrationData) {
    const isParticipant = registrationData.type === 'participant';
    const details = isParticipant ? registrationData.participant : registrationData.consultant;
    
    return (
      <motion.div
        className="py-8"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
      >
        <div className="text-center mb-8">
          <div className="text-6xl mb-6">✅</div>
          <h3 className="text-2xl font-bold text-blue-600 mb-2">
            Already Registered!
          </h3>
          <p className="text-gray-600">
            You are registered as a <span className="font-semibold capitalize">{registrationData.type}</span> for this Code Quest event.
          </p>
        </div>

        {/* Access Key Card */}
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 max-w-md mx-auto mb-6">
          <p className="text-sm text-gray-600 mb-2">Your Access Key</p>
          <p className="text-3xl font-mono font-bold text-blue-600">
            {details?.access_key}
          </p>
        </div>

        {/* Registration Details */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 max-w-lg mx-auto mb-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            Registration Details
          </h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Name:</span>
              <span className="font-medium">{details?.student_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Student ID:</span>
              <span className="font-medium">{details?.student_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Year:</span>
              <span className="font-medium">Year {details?.year}</span>
            </div>
            {isParticipant && (
              <div className="flex justify-between">
                <span className="text-gray-600">Preferred Role:</span>
                <span className="font-medium">{details?.preferred_role}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600">Registered:</span>
              <span className="font-medium">
                {details?.registration_date ? new Date(details.registration_date).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Group Assignment Status (Participant only) */}
        {isParticipant && (
          <div className="bg-white border border-gray-200 rounded-lg p-6 max-w-lg mx-auto mb-6">
            <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-green-600" />
              Group Status
            </h4>
            {details?.group ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Group:</span>
                  <span className="font-medium">
                    {details.group.group_name || `Group ${details.group.group_number}`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Members:</span>
                  <span className="font-medium">{details.group.member_count}</span>
                </div>
                {details.is_project_manager && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-3">
                    <p className="text-sm text-yellow-800 font-medium flex items-center gap-2">
                      <Award className="w-4 h-4" />
                      You are the Project Manager of this group!
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-3 text-gray-600">
                <Clock className="w-5 h-5" />
                <span>Not yet assigned to a group. You&apos;ll be notified when groups are formed.</span>
              </div>
            )}
          </div>
        )}

        {/* Consultant Approval Status */}
        {!isParticipant && details && (
          <div className="bg-white border border-gray-200 rounded-lg p-6 max-w-lg mx-auto mb-6">
            <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-green-600" />
              Consultant Status
            </h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Approval Status:</span>
                <span className={`font-medium ${details.is_approved ? 'text-green-600' : 'text-yellow-600'}`}>
                  {details.is_approved ? '✓ Approved' : '⏳ Pending Approval'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Groups Assigned:</span>
                <span className="font-medium">{details.assigned_groups_count || 0}</span>
              </div>
              {details.expertise_areas && (
                <div className="pt-2">
                  <span className="text-gray-600">Expertise:</span>
                  <p className="font-medium mt-1">{details.expertise_areas}</p>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="text-center">
          <button
            onClick={() => (window.location.href = "/code-quest-portal")}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
          >
            Go to Portal →
          </button>
        </div>
      </motion.div>
    );
  }

  // Not logged in state
  if (!user?.access) {
    return (
      <motion.div
        className="text-center py-12"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
      >
        <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <LogIn className="w-10 h-10 text-blue-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-4">
          Login Required
        </h3>
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          You need to be logged in with your CSS account to register for Code Quest. 
          Your account details will be automatically filled in the registration form.
        </p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-left">
              <p className="text-sm text-blue-800 font-medium">Why login?</p>
              <p className="text-sm text-blue-700 mt-1">
                Logging in links your Code Quest registration to your CSS account, 
                making it easier to track your progress and receive notifications.
              </p>
            </div>
          </div>
        </div>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
        >
          <LogIn className="w-5 h-5" />
          Login to Continue
        </Link>
        <p className="text-sm text-gray-500 mt-4">
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="text-blue-600 hover:underline">
            Sign up here
          </Link>
        </p>
      </motion.div>
    );
  }

  // Loading user details state
  if (fetchingUser) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading your details...</p>
      </div>
    );
  }

  // Success Modal
  if (success) {
    return (
      <motion.div
        className="text-center py-12"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
      >
        <div className="text-6xl mb-6">🎉</div>
        <h3 className="text-3xl font-bold text-green-600 mb-4">
          Registration Successful!
        </h3>
        <p className="text-gray-600 mb-6">
          Welcome to Code Quest! Here&apos;s your access key:
        </p>
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 max-w-md mx-auto mb-6">
          <p className="text-sm text-gray-600 mb-2">Your Access Key</p>
          <p className="text-3xl font-mono font-bold text-blue-600">
            {accessKey}
          </p>
          <p className="text-sm text-gray-500 mt-3">
            Save this key - you&apos;ll need it to access your portal
          </p>
        </div>
        <div className="space-y-3 text-left max-w-md mx-auto">
          <p className="text-gray-700">📧 A confirmation email has been sent to you</p>
          <p className="text-gray-700">
            🔑 Use this key to login to the participant portal
          </p>
          <p className="text-gray-700">
            📢 You&apos;ll be notified via email when groups are formed
          </p>
        </div>
        <button
          onClick={() => (window.location.href = "/code-quest-portal")}
          className="mt-8 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
        >
          Go to Portal →
        </button>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Participant Registration
        </h3>
        <p className="text-gray-600">
          Join Code Quest as a participant and build amazing apps!
        </p>
      </div>

      {/* Logged in user info banner */}
      {user?.user && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
              {user.user.first_name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="font-medium text-green-800">
                Registering as: {user.user.first_name} {user.user.last_name}
              </p>
              <p className="text-sm text-green-600">
                Your details have been pre-filled from your account
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg whitespace-pre-line">
          {error}
        </div>
      )}

      {/* Student ID & Full Name */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Student ID *
          </label>
          <input
            type="text"
            name="student_id"
            value={formData.student_id}
            onChange={handleChange}
            placeholder="e.g., 10945678"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Full Name *
          </label>
          <input
            type="text"
            name="student_name"
            value={formData.student_name}
            onChange={handleChange}
            placeholder="Your full name"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Email & Phone */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Personal Email Address *
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="yourname@gmail.com"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">Use your personal email for reliable communication</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number *
          </label>
          <input
            type="tel"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleChange}
            placeholder="0XX XXX XXXX"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Current Year */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Current Year *
        </label>
        <select
          name="year"
          value={formData.year}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value={2}>Year 2</option>
          <option value={3}>Year 3</option>
          <option value={4}>Year 4</option>
        </select>
      </div>

      {/* Deferred Student Status */}
      {formData.is_deferred && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-2xl">ℹ️</div>
            <div>
              <span className="font-medium text-gray-900">
                Deferred Student Status
              </span>
              <p className="text-sm text-gray-600 mt-1">
                You are registered as a deferred student (Year 3/4 completing
                this course)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preferred Role */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Preferred Role *
        </label>
        <select
          name="preferred_role"
          value={formData.preferred_role}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select a role</option>
          {roles.map((role) => (
            <option key={role.value} value={role.value}>
              {role.label}
            </option>
          ))}
        </select>
      </div>

      {/* Skills & Technologies */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Skills & Technologies
        </label>
        <p className="text-sm text-gray-600 mb-3">
          Select all that apply (you can select multiple)
        </p>
        <div className="flex flex-wrap gap-2">
          {technologies.map((tech) => (
            <button
              key={tech}
              type="button"
              onClick={() => handleSkillToggle(tech)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                formData.skills.includes(tech)
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {tech}
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-4 rounded-lg font-semibold text-lg transition-colors"
      >
        {loading ? "Registering..." : "Complete Registration"}
      </button>

      <p className="text-sm text-gray-500 text-center">
        By registering, you agree to participate actively in Code Quest and
        follow the event guidelines
      </p>
    </form>
  );
};

ParticipantRegistrationForm.propTypes = {
  eventId: PropTypes.number,
};

export default ParticipantRegistrationForm;
