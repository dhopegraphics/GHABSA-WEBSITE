import { useEffect, useState } from "react";
import signupImage from "../assets/3d1.png";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { validatePassword } from "../utils/vallidatePassword";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Hourglass } from "react-loader-spinner";
import VerificationModal from "../Components/VerificationModal";

const SignUp = ({ onClose, switchToLogin }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [graduationYearLocked, setGraduationYearLocked] = useState(true);
  
  // Calculate effective academic year (after Nov 30, next year becomes effective)
  const getEffectiveAcademicYear = () => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const month = now.getMonth(); // 0-indexed (11 = December)
    const day = now.getDate();
    
    // After Nov 30th, use next year as effective year
    return (month === 11 || (month === 10 && day > 30)) ? currentYear + 1 : currentYear;
  };
  
  // Calculate graduation year based on year level
  const calculateGraduationYear = (yearLevel) => {
    if (!yearLevel) return getEffectiveAcademicYear();
    
    const effectiveYear = getEffectiveAcademicYear();
    const yearNumber = parseInt(yearLevel);
    
    // Graduation year = effective year + (4 - year level)
    // 1st year: effective + 4, 2nd year: effective + 3, etc.
    return effectiveYear + (4 - yearNumber);
  };
  
  const [formData, setFormData] = useState({
    first_name: "",
    middle_name: "",
    last_name: "",
    phone: "+233",
    year_level: "", // New field for selecting 1st, 2nd, 3rd, 4th year
    graduation_year: getEffectiveAcademicYear(),
    password: "",
    program: "",
    student_id: "",
    gender: "", // New field
    personal_email: "", // New field
  });

  const [errors, setErrors] = useState({});
  const [res, setRes] = useState();

  // Verification modal state
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [verificationPhone, setVerificationPhone] = useState("");

  const togglePassword = () => {
    setShowPassword(!showPassword);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Auto-calculate graduation year when year level changes (if locked)
    if (name === "year_level" && graduationYearLocked) {
      const calculatedYear = calculateGraduationYear(value);
      setFormData({ 
        ...formData, 
        [name]: value,
        graduation_year: calculatedYear
      });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  // Clean phone number to +233XXXXXXXXX format
  const cleanPhoneNumber = (phone) => {
    // Remove all non-digit characters except +
    let cleaned = phone.replace(/[^0-9+]/g, "");

    // Handle various formats
    if (cleaned.startsWith("0")) {
      // Convert 0XXXXXXXXX to +233XXXXXXXXX
      cleaned = "+233" + cleaned.substring(1);
    } else if (cleaned.startsWith("233")) {
      // Convert 233XXXXXXXXX to +233XXXXXXXXX
      cleaned = "+" + cleaned;
    } else if (!cleaned.startsWith("+233")) {
      // If doesn't start with +233, add it
      cleaned = "+233" + cleaned.replace(/^\+/, "");
    }

    return cleaned;
  };

  const validateForm = () => {
    let formErrors = {};

    // Name validation
    if (!formData.first_name || formData.first_name.trim().length < 2) {
      formErrors.first_name = "First name must be at least 2 characters";
    }
    if (!formData.last_name || formData.last_name.trim().length < 2) {
      formErrors.last_name = "Last name must be at least 2 characters";
    }

    // Phone validation with cleaning
    const cleanedPhone = cleanPhoneNumber(formData.phone);
    if (!/^\+233[0-9]{9}$/.test(cleanedPhone)) {
      formErrors.phone = "Please enter a valid Ghanaian phone number";
    }

    // Year validation
    const currentYear = new Date().getFullYear();
    const year = parseInt(formData.graduation_year);
    if (!year || year < currentYear || year > currentYear + 6) {
      formErrors.graduation_year = `Year must be between ${currentYear} and ${
        currentYear + 6
      }`;
    }

    // Program validation
    if (!formData.program) {
      formErrors.program = "Please select your program";
    }    
    // Year level validation
    if (!formData.year_level) {
      formErrors.year_level = "Please select your current year";
    }
    
    // Gender validation
    if (!formData.gender) {
      formErrors.gender = "Gender is required";
    }
    
    // Personal email validation (optional, but validate format if provided)
    if (formData.personal_email && formData.personal_email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.personal_email)) {
        formErrors.personal_email = "Please enter a valid email address";
      }
    }
    // Student ID validation
    if (!formData.student_id || formData.student_id.trim().length < 3) {
      formErrors.student_id = "Student ID is required (minimum 3 characters)";
    }

    // Password validation
    if (!formData.password || formData.password.length < 6) {
      formErrors.password = "Password must be at least 6 characters";
    }

    return formErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent multiple submissions
    if (isLoading) return;

    const formErrors = validateForm();

    // Clear previous errors
    setErrors({});

    // Check for validation errors
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setError(Object.values(formErrors)[0]); // Show first error
      setSeverity("error");
      ShowNoti();
      return;
    }

    // Check password strength
    const passwordValidation = validatePassword(formData.password);
    if (passwordValidation !== "Password is valid") {
      setError(passwordValidation);
      setSeverity("error");
      ShowNoti();
      return;
    }

    try {
      setIsLoading(true); // Disable button and show loading

      // Clean phone number before sending
      const cleanedPhone = cleanPhoneNumber(formData.phone);

      // Prepare data for backend (exclude year_level as it's frontend-only)
      const { year_level, ...backendData } = formData;

      const url = `${BACKEND_HOST}/accounts/register/`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...backendData,
          phone: cleanedPhone,
        }),
      });

      const resp = await response.json();

      if (response.ok) {
        setRes(resp);
        
        // Clear form fields after successful signup
        setFormData({
          first_name: "",
          middle_name: "",
          last_name: "",
          phone: "+233",
          year_level: "",
          graduation_year: getEffectiveAcademicYear(),
          password: "",
          program: "",
          student_id: "",
          gender: "",
          personal_email: "",
        });

        // Check if verification is required
        if (resp.data?.verification_required) {
          // Show verification modal instead of switching to login
          setVerificationPhone(resp.data.phone);
          setShowVerificationModal(true);
          setIsLoading(false); // Re-enable if needed

          const message =
            resp.detail ||
            "Account created! Please enter the verification code sent to your phone.";
          setError(message);
          setSeverity("success");
          ShowNoti();
        } else {
          // Old flow (if verification not required for some reason)
          const successMessage =
            resp.detail ||
            "Account created successfully! Logging you in...";
          setError(successMessage);
          setSeverity("success");
          ShowNoti();
          
          // Keep loading state active to show we're transitioning
          setTimeout(() => {
            switchToLogin();
          }, 2500);
        }
      } else {
        // Re-enable button on error
        setIsLoading(false);

        // Handle different error scenarios with user-friendly messages
        let errorMessage = "We couldn't create your account. Please try again.";

        if (resp.detail) {
          errorMessage = resp.detail;
        } else if (resp.student_id && Array.isArray(resp.student_id)) {
          const studentIdError = resp.student_id[0].toLowerCase();
          if (
            studentIdError.includes("already") ||
            studentIdError.includes("exists")
          ) {
            errorMessage =
              "This Student ID is already registered. Please use a different ID or contact support.";
          } else {
            errorMessage = "Invalid Student ID. " + resp.student_id[0];
          }
        } else if (resp.phone && Array.isArray(resp.phone)) {
          const phoneError = resp.phone[0].toLowerCase();
          if (phoneError.includes("already") || phoneError.includes("exists")) {
            errorMessage =
              "This phone number is already registered. Please log in or use a different number.";
          } else {
            errorMessage = "Please enter a valid phone number.";
          }
        } else if (resp.password && Array.isArray(resp.password)) {
          errorMessage = "Password is too weak. " + resp.password[0];
        } else if (resp.error) {
          errorMessage = resp.error;
        } else if (resp.non_field_errors) {
          errorMessage = resp.non_field_errors[0];
        }

        // Handle rate limiting
        if (
          errorMessage.toLowerCase().includes("throttled") ||
          errorMessage.toLowerCase().includes("too many")
        ) {
          errorMessage =
            "Too many signup attempts. Please wait a while before trying again.";
        }

        setError(errorMessage);
        setSeverity("error");
        ShowNoti();
        setErrors(resp);
      }
    } catch (error) {
      console.error("Registration error:", error);
      setIsLoading(false); // Re-enable button on error

      let errorMessage =
        "Network error. Please check your connection and try again.";

      if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);
      setSeverity("error");
      ShowNoti();
      setErrors({ general: errorMessage });
    }
    // Note: Don't set loading to false on success - keep button disabled
  };

  const [open, setOpen] = useState(false);
  const [error, setError] = useState();
  const [severity, setSeverity] = useState();

  const ShowNoti = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  function capitalizeFirstLetter(word) {
    if (!word) return "";
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60 z-50 flex justify-center items-center"
      >
        <Snackbar
          open={open}
          autoHideDuration={3000}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          onClose={handleClose}
        >
          <Alert
            onClose={handleClose}
            severity={severity}
            // variant="filled"
            sx={{ width: "100%" }}
          >
            <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
            {error}
          </Alert>
        </Snackbar>
        {showContent && (
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[95%] sm:w-[90%] max-w-2xl p-4 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl shadow-2xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto"
          >
            <button 
              className="absolute top-3 right-3 sm:top-4 sm:right-4 z-10 p-2 hover:bg-gray-100 rounded-full transition-colors" 
              onClick={onClose}
              aria-label="Close"
            >
              <FaXmark className="w-5 h-5 sm:w-6 sm:h-6 text-gray-600 hover:text-gray-900" />
            </button>

            <div className="flex flex-col items-center">
              <img
                src={signupImage}
                alt="Sign Up Illustration"
                className="w-20 sm:w-28 md:w-32 mb-3 sm:mb-4"
              />

              <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-800 mb-2 sm:mb-3 text-center">
                Create an Account
              </h2>
              
              <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 text-center px-2">
                Join BIO-CHEM KNUST community today
              </p>

              {errors?.general && (
                <div className="w-full mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-center text-red-600 text-sm">
                    {errors.general}
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="w-full space-y-4 sm:space-y-5 relative">
                {/* Overlay when loading/transitioning */}
                {isLoading && (
                  <div className="absolute inset-0 bg-white/70 backdrop-blur-sm rounded-xl z-10 flex items-center justify-center">
                    <div className="text-center">
                      <Hourglass
                        colors={["#2563eb", "#1d4ed8"]}
                        width="40"
                        height={40}
                      />
                      <p className="mt-3 text-sm font-medium text-gray-700">Processing...</p>
                    </div>
                  </div>
                )}
                
                {/* Names Section - Responsive Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                  <div className="w-full">
                    <label
                      htmlFor="firstName"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      autoFocus
                      id="firstName"
                      placeholder="First Name"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        errors.first_name ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.first_name}
                      onChange={handleInputChange}
                    />
                    {errors.first_name && (
                      <p className="text-xs text-red-500 mt-1">{errors.first_name}</p>
                    )}
                  </div>
                  <div className="w-full">
                    <label
                      htmlFor="middleName"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Middle Name{" "}
                      <span className="text-gray-400 text-xs sm:text-sm">(Optional)</span>
                    </label>
                    <input
                      type="text"
                      name="middle_name"
                      id="middleName"
                      placeholder="Middle Name"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        errors.middle_name
                          ? "border-red-500 bg-red-50"
                          : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.middle_name}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="w-full sm:col-span-2 lg:col-span-1">
                    <label
                      htmlFor="lastName"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="lastName"
                      placeholder="Last Name"
                      name="last_name"
                      disabled={isLoading}
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        errors.last_name ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    />
                    {errors.last_name && (
                      <p className="text-xs text-red-500 mt-1">{errors.last_name}</p>
                    )}
                  </div>
                </div>

                {/* Program, Year Level & Gender - Responsive Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                  <div className="w-full">
                    <label
                      htmlFor="program"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Program <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="program"
                      name="program"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base bg-white ${
                        errors.program ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.program}
                      onChange={handleInputChange}
                    >
                      <option value="">Select your program</option>
                      <option value="CS">BSc Computer Science</option>
                      <option value="IT">BSc Information Technology</option>
                    </select>
                    {errors.program && (
                      <p className="text-xs text-red-500 mt-1">
                        {errors.program}
                      </p>
                    )}
                  </div>

                  <div className="w-full">
                    <label
                      htmlFor="year_level"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Current Year <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="year_level"
                      name="year_level"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base bg-white ${
                        errors.year_level ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.year_level}
                      onChange={handleInputChange}
                    >
                      <option value="">Select your year</option>
                      <option value="1">1st Year / Fresher</option>
                      <option value="2">2nd Year</option>
                      <option value="3">3rd Year</option>
                      <option value="4">4th Year</option>
                    </select>
                    {errors.year_level && (
                      <p className="text-xs text-red-500 mt-1">
                        {errors.year_level}
                      </p>
                    )}
                  </div>

                  <div className="w-full sm:col-span-2 lg:col-span-1">
                    <label
                      htmlFor="gender"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Gender <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="gender"
                      name="gender"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base bg-white ${
                        errors.gender ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.gender}
                      onChange={handleInputChange}
                    >
                      <option value="">Select gender</option>
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                    {errors.gender && (
                      <p className="text-xs text-red-500 mt-1">
                        {errors.gender}
                      </p>
                    )}
                  </div>
                </div>

                {/* Graduation Year (Auto-calculated, lockable) */}
                <div className="w-full">
                  <label
                    htmlFor="graduation"
                    className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                  >
                    Graduation Year <span className="text-red-500">*</span>
                    <span className="text-xs text-gray-500 ml-2">
                      (Auto-calculated based on year level)
                    </span>
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      id="graduation"
                      name="graduation_year"
                      placeholder="e.g., 2029"
                      disabled={isLoading}
                      readOnly={graduationYearLocked}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 pr-12 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        graduationYearLocked ? 'bg-gray-100 cursor-not-allowed' : ''
                      } ${
                        errors.graduation_year
                          ? "border-red-500 bg-red-50"
                          : "border-gray-300"
                      } ${isLoading ? 'opacity-50' : ''}`}
                      value={formData.graduation_year}
                      onChange={handleInputChange}
                    />
                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() => setGraduationYearLocked(!graduationYearLocked)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-200 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title={graduationYearLocked ? "Unlock to edit manually" : "Lock to auto-calculate"}
                    >
                      {graduationYearLocked ? (
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                        </svg>
                      )}
                    </button>
                  </div>
                  {errors.graduation_year && (
                    <p className="text-xs text-red-500 mt-1">
                      {errors.graduation_year}
                    </p>
                  )}
                </div>

                {/* Student ID & Phone - Responsive Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div className="w-full">
                    <label
                      htmlFor="student_id"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Student ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="student_id"
                      name="student_id"
                      placeholder="Your student ID"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        errors.student_id ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.student_id}
                      onChange={handleInputChange}
                    />
                    {errors.student_id && (
                      <p className="text-xs text-red-500 mt-1">
                        {errors.student_id}
                      </p>
                    )}
                  </div>

                  <div className="w-full">
                    <label
                      htmlFor="phone"
                      className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                    >
                      Phone Number <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      placeholder="+233XXXXXXXXX"
                      disabled={isLoading}
                      className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                        errors.phone ? "border-red-500 bg-red-50" : "border-gray-300"
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      value={formData.phone}
                      onChange={handleInputChange}
                    />
                    {errors.phone && (
                      <p className="text-xs text-red-500 mt-1">{errors.phone}</p>
                    )}
                  </div>
                </div>

                {/* Personal Email */}
                <div className="w-full">
                  <label
                    htmlFor="personal_email"
                    className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                  >
                    Personal Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    id="personal_email"
                    name="personal_email"
                    placeholder="your.email@example.com"
                    disabled={isLoading}
                    className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                      errors.personal_email ? "border-red-500 bg-red-50" : "border-gray-300"
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    value={formData.personal_email}
                    onChange={handleInputChange}
                  />
                  {errors.personal_email && (
                    <p className="text-xs text-red-500 mt-1">{errors.personal_email}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    We'll use this for important account notifications
                  </p>
                </div>

                {/* Password Field */}
                <div className="w-full relative">
                  <label
                    htmlFor="password"
                    className="block text-gray-700 font-medium mb-1.5 sm:mb-2 text-sm sm:text-base"
                  >
                    Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    name="password"
                    placeholder="Min. 6 characters"
                    disabled={isLoading}
                    className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 pr-16 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm sm:text-base ${
                      errors.password ? "border-red-500 bg-red-50" : "border-gray-300"
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    value={formData.password}
                    onChange={handleInputChange}
                  />
                  <button
                    type="button"
                    onClick={togglePassword}
                    className="absolute right-3 top-[38px] sm:top-[42px] text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                  {errors.password && (
                    <p className="text-xs text-red-500 mt-1">{errors.password}</p>
                  )}
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 sm:py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition-all duration-200 flex flex-row items-center justify-center gap-2 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base mt-6"
                >
                  <span>Sign Up</span>
                  {isLoading && (
                    <Hourglass
                      colors={["#ffffff", "#ffffff"]}
                      width="20"
                      height={20}
                    />
                  )}
                </button>
              </form>
              
              {/* Login Link */}
              <div className="mt-4 sm:mt-6 text-center">
                <p className="text-gray-600 text-xs sm:text-sm">
                  Already have an account?{" "}
                  <span
                    onClick={switchToLogin}
                    className="text-blue-600 hover:text-blue-800 font-semibold hover:underline cursor-pointer transition-colors"
                  >
                    Log in
                  </span>
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Verification Modal */}
      {showVerificationModal && (
        <VerificationModal
          phone={verificationPhone}
          onClose={() => setShowVerificationModal(false)}
          onVerified={() => {
            setShowVerificationModal(false);
            setIsLoading(true); // Show loading state
            setError("Phone verified successfully! Logging you in...");
            setSeverity("success");
            ShowNoti();
            setTimeout(() => {
              switchToLogin();
            }, 2000);
          }}
          showResend={true}
          requireAuth={false}
        />
      )}
    </AnimatePresence>
  );
};

export default SignUp;
