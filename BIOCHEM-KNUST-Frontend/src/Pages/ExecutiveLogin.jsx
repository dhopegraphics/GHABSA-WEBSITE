import { useState, useEffect } from "react";
import loginImage from "../assets/3d1.png";
import { FaXmark } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { Hourglass } from "react-loader-spinner";
import { BACKEND_HOST } from "../utils/config";

const ExecutiveLogin = ({ onClose, switchToSignup, switchToForgot }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  const [formData, setFormData] = useState({
    phone: "",
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    // Clean phone before validating
    const cleaned = cleanPhoneNumber(formData.phone);
    if (!/^\+233[0-9]{9}$/.test(cleaned)) {
      newErrors.phone =
        "Please enter a valid Ghanaian phone number starting with +233 followed by 9 digits.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Mirror of the signup cleaning logic to normalize different user inputs
  const cleanPhoneNumber = (phone) => {
    if (!phone) return "";
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

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (validateForm()) {
      setErrors({});
      try {
        setIsLoading(true);

        const url = `${BACKEND_HOST}/accounts/executive-door/`;
        const cleanedPhone = cleanPhoneNumber(formData.phone);

        // Detect client-side mobile and notify backend via header so backend
        // can enforce mobile-restriction checks reliably.
        const isClientMobile = () => {
          if (typeof navigator === "undefined") return false;
          return /Mobile|Android|iPhone|iPad|iPod|BlackBerry|Opera Mini|IEMobile/i.test(
            navigator.userAgent
          );
        };

        const headers = {
          "Content-Type": "application/json",
        };
        if (isClientMobile()) {
          headers["X-Client-Platform"] = "mobile";
        }

        const response = await fetch(url, {
          method: "POST",
          headers,
          body: JSON.stringify({ phone: cleanedPhone }),
        });

        const resp = await response.json();

        if (response.ok) {
          // Success - redirect to executive dashboard
          setFormData({
            phone: "",
          });
          setErrors({});
          window.location.href = resp?.executive_login;
        } else {
          // Error handling with detailed messages
          console.log("Login error response:", resp);

          // Extract error message - try multiple possible fields
          let errorMsg = "Login failed. Please try again.";

          if (resp?.message) {
            errorMsg = resp.message;
          } else if (resp?.detail) {
            errorMsg = resp.detail;
          } else if (resp?.error) {
            errorMsg = resp.error;
          }

          // Add error type for better debugging
          const errorType = resp?.error_type || "unknown_error";
          console.log("Error type:", errorType);

          // Provide user-friendly error messages based on error type
          if (errorType === "user_not_found") {
            errorMsg =
              resp?.message ||
              "No account found with this phone number. Please check your number and try again.";
          } else if (errorType === "account_inactive") {
            errorMsg =
              resp?.message ||
              "Your account is inactive. Please contact an administrator.";
          } else if (errorType === "not_executive") {
            errorMsg =
              resp?.message ||
              "Access denied. You do not have executive privileges.";
          } else if (errorType === "mobile_restriction") {
            errorMsg =
              resp?.message ||
              "Mobile access is restricted. Please use a desktop.";
          } else if (errorType === "validation_error") {
            errorMsg =
              resp?.message ||
              "Invalid phone number format. Please check and try again.";
          } else if (errorType === "system_error") {
            errorMsg =
              "System error. Please try again later or contact support.";
          }

          setErrors({
            general: errorMsg,
            errorType: errorType,
            phone: resp?.normalized_phone || formData.phone,
          });
        }
      } catch (error) {
        console.error("Network or unexpected error:", error);
        setErrors({
          general: "Network error. Please check your connection and try again.",
          errorType: "network_error",
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/60  z-50 flex justify-center items-center"
      >
        {showContent && (
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[90%] max-w-md p-8 rounded shadow-lg"
          >
            <button className="absolute top-4 right-4" onClick={onClose}>
              <FaXmark className="w-6 h-6" />
            </button>

            <div className="flex flex-col items-center">
              <img
                src={loginImage}
                alt="Login Illustration"
                className="w-32 mb-4"
              />

              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Welcome Back!
              </h2>

              {errors?.general && (
                <div className="w-full mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-red-500"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3 flex-1">
                      <p className="text-sm font-medium text-red-800">
                        {errors.general}
                      </p>
                      {errors.phone && errors.phone !== formData.phone && (
                        <p className="text-xs text-red-600 mt-1">
                          Phone used: {errors.phone}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="w-full">
                <div className="mb-4">
                  <label
                    htmlFor="index"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    autoFocus
                    id="index"
                    value={formData.phone}
                    onChange={handleInputChange}
                    name="phone"
                    placeholder="Enter your phone number"
                    className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                  />
                  {errors.phone && (
                    <p className="text-red-500 text-sm">{errors.phone}</p>
                  )}
                </div>

                <div
                  onClick={switchToForgot}
                  className="text-end text-blue-600 mb-4 text-sm hover:underline cursor-pointer"
                >
                  Forgotten password?
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2 bg-blue-700 flex flex-row items-center justify-center gap-2 text-white font-bold rounded hover:bg-blue-800 transition"
                >
                  Proceed
                  {isLoading && (
                    <Hourglass
                      colors={["#ffffff", "#000000"]}
                      width="20"
                      height={16}
                    />
                  )}
                </button>

                <div className="text-center mt-4">
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Don&apos;t have an account?{" "}
                    <span
                      onClick={switchToSignup}
                      className="text-blue-600 hover:underline cursor-pointer"
                    >
                      Sign up
                    </span>
                  </p>
                </div>
              </form>
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default ExecutiveLogin;
