import { useState, useEffect, useContext } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import PropTypes from "prop-types";
import { UserContext } from "../../../../Context/UserContext";
import { AlertCircle, LogIn, Users, Award, Clock, CheckCircle } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ConsultantRegistrationForm = ({ eventId }) => {
  const { user } = useContext(UserContext);
  const [formData, setFormData] = useState({
    student_id: "",
    student_name: "",
    email: "",
    phone_number: "",
    year: "Y3",
    expertise_areas: [],
    bio: "",
    profile_picture: null,
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
        
        // Calculate year for consultant (Y3 or Y4)
        const consultantYear = userData.year >= 4 ? "Y4" : "Y3";
        
        // Pre-fill form with user data
        setFormData(prev => ({
          ...prev,
          student_id: userData.student_id || '',
          student_name: userData.full_name || '',
          email: userData.email || '',
          phone_number: userData.phone || '',
          year: consultantYear,
        }));
      } catch (err) {
        console.error("Error fetching user details:", err);
      } finally {
        setFetchingUser(false);
      }
    };

    fetchUserDetails();
  }, [user, eventId]);

  // Available expertise areas
  const expertiseOptions = [
    "Frontend Development",
    "Backend Development",
    "Mobile Development (React Native)",
    "Mobile Development (Flutter)",
    "UI/UX Design",
    "Database Design",
    "API Development",
    "Cloud Services (AWS/Azure)",
    "DevOps & CI/CD",
    "Testing & QA",
    "Project Management",
    "Git & Version Control",
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleExpertiseToggle = (expertise) => {
    setFormData((prev) => ({
      ...prev,
      expertise_areas: prev.expertise_areas.includes(expertise)
        ? prev.expertise_areas.filter((e) => e !== expertise)
        : [...prev.expertise_areas, expertise],
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData((prev) => ({
        ...prev,
        profile_picture: file,
      }));
    }
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
      // Prepare FormData for file upload
      const submitData = new FormData();
      submitData.append("event", eventId);
      submitData.append("student_id", formData.student_id);
      submitData.append("student_name", formData.student_name);
      submitData.append("email", formData.email);
      submitData.append("phone_number", formData.phone_number);
      submitData.append("year", formData.year);
      submitData.append("expertise_areas", JSON.stringify(formData.expertise_areas));
      submitData.append("bio", formData.bio);
      if (formData.profile_picture) {
        submitData.append("profile_image", formData.profile_picture);
      }

      // API call with authentication
      const response = await axios.post(
        `${API_BASE_URL}/codequest/register/consultant/`,
        submitData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${user.access}`,
          },
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
    const isConsultant = registrationData.type === 'consultant';
    const details = isConsultant ? registrationData.consultant : registrationData.participant;
    
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
          {!isConsultant && (
            <p className="text-sm text-gray-500 mt-2">
              You cannot register as a consultant since you&apos;re already a participant.
            </p>
          )}
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
            <div className="flex justify-between">
              <span className="text-gray-600">Registered:</span>
              <span className="font-medium">
                {details?.registration_date ? new Date(details.registration_date).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Consultant Status (only if registered as consultant) */}
        {isConsultant && details && (
          <div className="bg-white border border-gray-200 rounded-lg p-6 max-w-lg mx-auto mb-6">
            <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-green-600" />
              Consultant Status
            </h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Approval Status:</span>
                {details.is_approved ? (
                  <span className="inline-flex items-center gap-1 text-green-600 font-medium">
                    <CheckCircle className="w-4 h-4" />
                    Approved
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-yellow-600 font-medium">
                    <Clock className="w-4 h-4" />
                    Pending Approval
                  </span>
                )}
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Groups Assigned:</span>
                <span className="font-medium">{details.assigned_groups_count || 0}</span>
              </div>
              {details.expertise_areas && (
                <div className="pt-2 border-t">
                  <span className="text-gray-600">Expertise Areas:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {(typeof details.expertise_areas === 'string' 
                      ? JSON.parse(details.expertise_areas) 
                      : details.expertise_areas
                    ).map((area, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {!details.is_approved && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
                <p className="text-sm text-yellow-800">
                  ⏳ Your application is being reviewed by the admin team. You&apos;ll receive an email notification once approved.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Participant Group Status (if registered as participant) */}
        {!isConsultant && details && (
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
              </div>
            ) : (
              <div className="flex items-center gap-3 text-gray-600">
                <Clock className="w-5 h-5" />
                <span>Not yet assigned to a group.</span>
              </div>
            )}
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
          You need to be logged in with your CSS account to apply as a Code Quest consultant. 
          Your account details will be automatically filled in the application form.
        </p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-left">
              <p className="text-sm text-blue-800 font-medium">Why login?</p>
              <p className="text-sm text-blue-700 mt-1">
                Logging in links your consultant application to your CSS account, 
                making it easier to manage your groups and receive notifications.
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
        <div className="text-6xl mb-6">🎓</div>
        <h3 className="text-3xl font-bold text-green-600 mb-4">
          Consultant Application Submitted!
        </h3>
        <p className="text-gray-600 mb-6">
          Thank you for offering to mentor! Here&apos;s your access key:
        </p>
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 max-w-md mx-auto mb-6">
          <p className="text-sm text-gray-600 mb-2">Your Access Key</p>
          <p className="text-3xl font-mono font-bold text-blue-600">
            {accessKey}
          </p>
          <p className="text-sm text-gray-500 mt-3">
            Save this key - you&apos;ll need it after admin approval
          </p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md mx-auto mb-6">
          <p className="text-yellow-800 font-medium">
            ⏳ Pending Admin Approval
          </p>
          <p className="text-sm text-yellow-700 mt-2">
            Your application will be reviewed by the admin team. You&apos;ll
            receive an email notification once approved.
          </p>
        </div>
        <div className="space-y-3 text-left max-w-md mx-auto">
          <p className="text-gray-700">📧 A confirmation email has been sent to you</p>
          <p className="text-gray-700">🔑 Keep your access key safe - you&apos;ll need it later</p>
          <p className="text-gray-700">⏳ Awaiting admin approval</p>
          <p className="text-gray-700">
            📢 You&apos;ll be notified via email when approved
          </p>
          <p className="text-gray-700">
            👥 Groups will be assigned after approval
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
          Consultant Registration
        </h3>
        <p className="text-gray-600">
          Become a mentor and guide Year 2 students in their projects
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
                Applying as: {user.user.first_name} {user.user.last_name}
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

      {/* Student ID & Name */}
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

      {/* Year */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Year *
        </label>
        <select
          name="year"
          value={formData.year}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="Y3">Year 3</option>
          <option value="Y4">Year 4</option>
        </select>
        <p className="text-sm text-gray-500 mt-1">
          Only Year 3 and 4 students can be consultants
        </p>
      </div>

      {/* Expertise Areas */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Expertise Areas *
        </label>
        <p className="text-sm text-gray-600 mb-3">
          Select your areas of expertise (minimum 2)
        </p>
        <div className="flex flex-wrap gap-2">
          {expertiseOptions.map((expertise) => (
            <button
              key={expertise}
              type="button"
              onClick={() => handleExpertiseToggle(expertise)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                formData.expertise_areas.includes(expertise)
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {expertise}
            </button>
          ))}
        </div>
        {formData.expertise_areas.length > 0 && (
          <p className="text-sm text-blue-600 mt-2">
            {formData.expertise_areas.length} selected
          </p>
        )}
      </div>

      {/* Bio */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Why do you want to be a consultant? *
        </label>
        <textarea
          name="bio"
          value={formData.bio}
          onChange={handleChange}
          rows={5}
          placeholder="Share your motivation for mentoring Year 2 students. What experience do you have? What can you offer as a consultant?"
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-sm text-gray-500 mt-1">
          This helps us match you with the right groups
        </p>
      </div>

      {/* Profile Picture */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Profile Picture (Optional)
        </label>
        <div className="flex items-center gap-4">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="profile-picture"
          />
          <label
            htmlFor="profile-picture"
            className="px-6 py-3 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg cursor-pointer transition-colors"
          >
            Choose Photo
          </label>
          {formData.profile_picture && (
            <span className="text-sm text-gray-600">
              {formData.profile_picture.name}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-1">
          A professional photo helps groups connect with you
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || formData.expertise_areas.length < 2}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-4 rounded-lg font-semibold text-lg transition-colors"
      >
        {loading ? "Submitting Application..." : "Submit Application"}
      </button>

      <p className="text-sm text-gray-500 text-center">
        Your application will be reviewed by the admin. You&apos;ll receive an
        email notification once approved.
      </p>
    </form>
  );
};

ConsultantRegistrationForm.propTypes = {
  eventId: PropTypes.number,
};

export default ConsultantRegistrationForm;
