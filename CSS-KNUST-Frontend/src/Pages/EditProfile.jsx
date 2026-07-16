import React, { useContext, useEffect, useState } from "react";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Hourglass } from "react-loader-spinner";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

const EditProfile = ({ onClose, focus }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  const { user, login } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.user?.first_name || "",
    last_name: user?.user?.last_name || "",
    phone: user?.user?.phone || "",
    graduation_year: user?.user?.graduation_year || "",
    program: user?.user?.program || "",
    student_id: user?.user?.student_id || "",
    index_number: user?.user?.index_number || "",
    personal_email: user?.user?.personal_email || "",
    student_email: user?.user?.student_email || "",
    gender: user?.user?.gender || "",
    group: user?.user?.group || "",
  });

  const [errors, setErrors] = useState({});
  const [open, setOpen] = useState(false);
  const [error, setError] = useState();
  const [severity, setSeverity] = useState();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });

    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    let formErrors = {};

    // First Name validation
    if (!formData.first_name?.trim()) {
      formErrors.first_name = "First name is required";
    }

    // Last Name validation
    if (!formData.last_name?.trim()) {
      formErrors.last_name = "Last name is required";
    }

    // Phone validation
    if (!formData.phone) {
      formErrors.phone = "Phone number is required";
    } else if (!formData.phone.startsWith("+233")) {
      formErrors.phone = "Phone number must start with +233";
    } else if (formData.phone.length !== 13) {
      formErrors.phone =
        "Phone number must be in format +233XXXXXXXXX (13 digits total)";
    }

    // Graduation year validation
    if (!formData.graduation_year) {
      formErrors.graduation_year = "Graduation year is required";
    } else {
      const year = parseInt(formData.graduation_year);
      const currentYear = new Date().getFullYear();
      if (year < 2000 || year > currentYear + 10) {
        formErrors.graduation_year = `Graduation year must be between 2000 and ${
          currentYear + 10
        }`;
      }
    }

    // Student ID validation
    if (!user?.user?.student_id && !formData.student_id?.trim()) {
      formErrors.student_id = "Student ID is required";
    } else if (formData.student_id && formData.student_id.trim().length < 3) {
      formErrors.student_id = "Student ID must be at least 3 characters";
    }

    // Personal Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.personal_email && !emailRegex.test(formData.personal_email)) {
      formErrors.personal_email =
        "Please enter a valid email address (e.g., name@example.com)";
    }

    // Student Email validation
    if (formData.student_email) {
      if (!emailRegex.test(formData.student_email)) {
        formErrors.student_email = "Please enter a valid email address";
      } else if (!formData.student_email.endsWith("@st.knust.edu.gh")) {
        formErrors.student_email =
          "Student email must be a valid KNUST email (@st.knust.edu.gh)";
      }
    }

    return formErrors;
  };

  // Parse backend errors from Django REST Framework
  const parseBackendErrors = (errorResponse) => {
    const parsedErrors = {};

    // Check if errorResponse has data property (Axios error structure)
    const errorData = errorResponse?.data || errorResponse;

    // Handle new error structure with 'errors' field
    if (errorData?.errors && typeof errorData.errors === "object") {
      Object.keys(errorData.errors).forEach((field) => {
        const fieldErrors = errorData.errors[field];

        // Handle array of errors
        if (Array.isArray(fieldErrors)) {
          parsedErrors[field] = fieldErrors[0];
        }
        // Handle string error
        else if (typeof fieldErrors === "string") {
          parsedErrors[field] = fieldErrors;
        }
        // Handle nested error objects
        else if (typeof fieldErrors === "object") {
          parsedErrors[field] = JSON.stringify(fieldErrors);
        }
      });
    }
    // Handle old error structure (backward compatibility)
    else if (typeof errorData === "object" && errorData !== null) {
      // Handle field-specific errors
      Object.keys(errorData).forEach((field) => {
        const fieldErrors = errorData[field];

        // Handle array of errors (standard DRF format)
        if (Array.isArray(fieldErrors)) {
          parsedErrors[field] = fieldErrors[0]; // Take first error message
        }
        // Handle string error
        else if (typeof fieldErrors === "string") {
          parsedErrors[field] = fieldErrors;
        }
        // Handle nested error objects
        else if (typeof fieldErrors === "object") {
          parsedErrors[field] = JSON.stringify(fieldErrors);
        }
      });

      // Handle non_field_errors or general errors
      if (errorData.non_field_errors) {
        const generalError = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors[0]
          : errorData.non_field_errors;
        parsedErrors.general = generalError;
      }

      // Handle detail field (common in DRF)
      if (errorData.detail && !parsedErrors.general) {
        parsedErrors.general =
          typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail);
      }
    } else if (typeof errorData === "string") {
      parsedErrors.general = errorData;
    }

    return Object.keys(parsedErrors).length > 0
      ? parsedErrors
      : { general: "An unexpected error occurred. Please try again." };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});

    // Client-side validation
    const formErrors = validateForm();

    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setError("Please correct the highlighted fields");
      setSeverity("error");
      ShowNoti();
      return;
    }

    try {
      setIsLoading(true);
      const url = `${BACKEND_HOST}/accounts/update-account/`;

      // Filter out empty strings and null values to prevent overwriting with None
      const cleanedData = Object.entries(formData).reduce(
        (acc, [key, value]) => {
          // Only include fields that have actual values (not empty strings or null)
          if (value !== "" && value !== null && value !== undefined) {
            acc[key] = value;
          }
          return acc;
        },
        {}
      );

      await axiosInstance.put(url, cleanedData, {
        headers: { Authorization: `Bearer ${user.access}` },
      });

      // Success - refresh user data
      const url1 = `${BACKEND_HOST}/accounts/profile/`;
      const response = await axiosInstance.get(url1, {
        headers: {
          Authorization: `Bearer ${user.access}`,
        },
      });
      login(user?.access, user?.refresh, response?.data?.user);

      setError("Profile updated successfully!");
      setSeverity("success");
      ShowNoti();

      // Close modal after short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error("Profile update error:", error);

      // Parse backend errors
      const backendErrors = parseBackendErrors(error.response);
      setErrors(backendErrors);

      // Show notification with appropriate message
      if (backendErrors.general) {
        setError(backendErrors.general);
      } else {
        const fieldCount = Object.keys(backendErrors).length;
        setError(
          `Please correct ${fieldCount} error${
            fieldCount > 1 ? "s" : ""
          } in the form`
        );
      }
      setSeverity("error");
      ShowNoti();
    } finally {
      setIsLoading(false);
    }
  };

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

  // Helper to get error message for a field
  const getFieldError = (fieldName) => {
    return errors[fieldName];
  };

  // Helper to check if field has error
  const hasFieldError = (fieldName) => {
    return !!errors[fieldName];
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60 z-[10000] flex justify-center items-center"
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
            className="relative bg-white w-[90%] max-w-md p-8 rounded shadow-lg max-h-[80vh] overflow-y-auto"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-gray-800">Edit Profile</h2>
              <button
                onClick={onClose}
                className="hover:bg-gray-100 p-1 rounded"
              >
                <FaXmark className="w-6 h-6" />
              </button>
            </div>

            <div className="flex flex-col items-center">
              {/* General Error Message */}
              {errors?.general && (
                <div className="w-full mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm font-medium">
                    {errors.general}
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="w-full">
                {/* First and Last Name */}
                <div className="mb-4 flex gap-4">
                  <div className="w-1/2">
                    <label
                      htmlFor="firstName"
                      className="block text-gray-700 font-medium mb-2"
                    >
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      autoFocus={focus === 1}
                      id="firstName"
                      placeholder="First Name"
                      className={`w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 transition-colors ${
                        hasFieldError("first_name")
                          ? "border-red-500 focus:ring-red-200 bg-red-50"
                          : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                      }`}
                      value={formData.first_name}
                      onChange={handleInputChange}
                    />
                    {hasFieldError("first_name") && (
                      <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                        <span>⚠</span>
                        {getFieldError("first_name")}
                      </p>
                    )}
                  </div>

                  <div className="w-1/2">
                    <label
                      htmlFor="lastName"
                      className="block text-gray-700 font-medium mb-2"
                    >
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="lastName"
                      placeholder="Last Name"
                      name="last_name"
                      autoFocus={focus === 2}
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 transition-colors ${
                        hasFieldError("last_name")
                          ? "border-red-500 focus:ring-red-200 bg-red-50"
                          : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                      }`}
                    />
                    {hasFieldError("last_name") && (
                      <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                        <span>⚠</span>
                        {getFieldError("last_name")}
                      </p>
                    )}
                  </div>
                </div>

                {/* Graduation Year */}
                <div className="mb-4">
                  <label
                    htmlFor="graduation"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Graduation Year <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    id="graduation"
                    name="graduation_year"
                    autoFocus={focus === 3}
                    placeholder="e.g., 2025"
                    className={`w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 transition-colors ${
                      hasFieldError("graduation_year")
                        ? "border-red-500 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                    }`}
                    value={formData.graduation_year}
                    onChange={handleInputChange}
                  />
                  {hasFieldError("graduation_year") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("graduation_year")}
                    </p>
                  )}
                </div>

                {/* Program */}
                <div className="mb-4">
                  <label
                    htmlFor="program"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Program
                  </label>
                  <select
                    id="program"
                    name="program"
                    autoFocus={focus === 5}
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.program
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("program")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.program}
                    onChange={handleInputChange}
                    disabled={!!user?.user?.program}
                  >
                    <option value="">Select your program</option>
                    <option value="CS">BSc Computer Science</option>
                    <option value="IT">BSc Information Technology</option>
                  </select>
                  {hasFieldError("program") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("program")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.program
                      ? "Program cannot be changed once set"
                      : "Select your program"}
                  </p>
                </div>

                {/* Student ID */}
                <div className="mb-4">
                  <label
                    htmlFor="student_id"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Student ID{" "}
                    {!user?.user?.student_id && (
                      <span className="text-red-500">*</span>
                    )}
                  </label>
                  <input
                    type="text"
                    id="student_id"
                    name="student_id"
                    placeholder={
                      user?.user?.student_id ? "" : "Enter your student ID"
                    }
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.student_id
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("student_id")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.student_id}
                    onChange={handleInputChange}
                    readOnly={!!user?.user?.student_id}
                    disabled={!!user?.user?.student_id}
                  />
                  {hasFieldError("student_id") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("student_id")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.student_id
                      ? "Student ID cannot be changed once set"
                      : "Required field. Once set, it cannot be changed."}
                  </p>
                </div>

                {/* Index Number */}
                <div className="mb-4">
                  <label
                    htmlFor="index_number"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Index Number{" "}
                    {!user?.user?.index_number && (
                      <span className="text-gray-500 text-sm">
                        (May be unavailable for new students)
                      </span>
                    )}
                  </label>
                  <input
                    type="text"
                    id="index_number"
                    name="index_number"
                    placeholder={
                      user?.user?.index_number
                        ? ""
                        : "Enter your index number (if available)"
                    }
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.index_number
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("index_number")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.index_number}
                    onChange={handleInputChange}
                    readOnly={!!user?.user?.index_number}
                    disabled={!!user?.user?.index_number}
                  />
                  {hasFieldError("index_number") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("index_number")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.index_number
                      ? "Index number cannot be changed once set"
                      : "Leave blank if not yet available. Once set, it cannot be changed."}
                  </p>
                </div>

                {/* Gender */}
                <div className="mb-4">
                  <label
                    htmlFor="gender"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Gender{" "}
                    <span className="text-gray-500 text-sm">(Optional)</span>
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.gender
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("gender")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.gender}
                    onChange={handleInputChange}
                    disabled={!!user?.user?.gender}
                  >
                    <option value="">Prefer not to say</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                  {hasFieldError("gender") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("gender")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.gender
                      ? "Gender cannot be changed once set"
                      : "Optional field"}
                  </p>
                </div>

                {/* Group */}
                <div className="mb-4">
                  <label
                    htmlFor="group"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Class Group{" "}
                    <span className="text-gray-500 text-sm">
                      (Required for timetable)
                    </span>
                  </label>
                  <select
                    id="group"
                    name="group"
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.group
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("group")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.group}
                    onChange={handleInputChange}
                    disabled={!!user?.user?.group}
                  >
                    <option value="">Select your group</option>
                    <option value="G1">Group 1</option>
                    <option value="G2">Group 2</option>
                  </select>
                  {hasFieldError("group") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("group")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.group
                      ? "Class group cannot be changed once set"
                      : "Select your class group to view personalized timetables"}
                  </p>
                </div>

                {/* Personal Email */}
                <div className="mb-4">
                  <label
                    htmlFor="personal_email"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Personal Email{" "}
                    <span className="text-gray-500 text-sm">(Optional)</span>
                  </label>
                  <input
                    type="email"
                    id="personal_email"
                    name="personal_email"
                    placeholder="your.email@example.com"
                    className={`w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 transition-colors ${
                      hasFieldError("personal_email")
                        ? "border-red-500 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
                    }`}
                    value={formData.personal_email}
                    onChange={handleInputChange}
                  />
                  {hasFieldError("personal_email") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("personal_email")}
                    </p>
                  )}
                </div>

                {/* Student Email */}
                <div className="mb-4">
                  <label
                    htmlFor="student_email"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Student Email{" "}
                    <span className="text-gray-500 text-sm">(Optional)</span>
                  </label>
                  <input
                    type="email"
                    id="student_email"
                    name="student_email"
                    placeholder="yourname@st.knust.edu.gh"
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.student_email
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("student_email")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.student_email}
                    onChange={handleInputChange}
                    readOnly={!!user?.user?.student_email}
                    disabled={!!user?.user?.student_email}
                  />
                  {hasFieldError("student_email") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("student_email")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.student_email
                      ? "Student email cannot be changed once set"
                      : "Official KNUST student email address"}
                  </p>
                </div>

                {/* Phone */}
                <div className="mb-4">
                  <label
                    htmlFor="phone"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    autoFocus={focus === 4}
                    placeholder="+233XXXXXXXXX"
                    className={`w-full px-4 py-2 border rounded transition-colors ${
                      user?.user?.phone_confirm
                        ? "border-gray-300 bg-gray-100 cursor-not-allowed"
                        : hasFieldError("phone")
                        ? "border-red-500 focus:ring-2 focus:ring-red-200 bg-red-50"
                        : "border-gray-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    }`}
                    value={formData.phone}
                    onChange={handleInputChange}
                    readOnly={!!user?.user?.phone_confirm}
                    disabled={!!user?.user?.phone_confirm}
                  />
                  {hasFieldError("phone") && (
                    <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                      <span>⚠</span>
                      {getFieldError("phone")}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.user?.phone_confirm
                      ? "Phone number cannot be changed once verified"
                      : "Format: +233XXXXXXXXX (e.g., +233201234567)"}
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2 bg-blue-700 text-white font-bold rounded hover:bg-blue-800 disabled:bg-blue-400 disabled:cursor-not-allowed transition flex flex-row items-center justify-center gap-2"
                >
                  {isLoading ? "Updating..." : "Update Profile"}
                  {isLoading && (
                    <Hourglass
                      colors={["#ffffff", "#ffffff"]}
                      width="20"
                      height={20}
                    />
                  )}
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default EditProfile;
