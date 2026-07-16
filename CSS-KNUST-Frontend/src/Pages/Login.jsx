import React, { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import loginImage from "../assets/3d1.png";
import { FaXmark, FaCheck } from "react-icons/fa6";
import { AnimatePresence, motion } from "framer-motion";
import { UserContext } from "../Context/UserContext";
import { Hourglass } from "react-loader-spinner";
import { BACKEND_HOST } from "../utils/config";

const Login = ({
  onClose,
  switchToSignup,
  switchToForgot,
  switchToExecutive,
}) => {
  const navigate = useNavigate();
  const [showContent, setShowContent] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timeout = setTimeout(() => setShowContent(true), 200);
    return () => clearTimeout(timeout);
  }, []);

  // Countdown timer for auto-close after login success
  useEffect(() => {
    if (loginSuccess && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (loginSuccess && countdown === 0) {
      // Auto close and stay on current page
      onClose();
    }
  }, [loginSuccess, countdown, onClose]);

  const [formData, setFormData] = useState({
    phone: "+233",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useContext(UserContext);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
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
    const newErrors = {};

    // Clean and validate phone
    const cleanedPhone = cleanPhoneNumber(formData.phone);
    if (!/^\+233[0-9]{9}$/.test(cleanedPhone)) {
      newErrors.phone = "Please enter a valid phone number";
    }

    if (!formData.password.trim() || formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent multiple submissions
    if (isLoading) return;

    if (validateForm()) {
      setErrors({});
      try {
        setIsLoading(true); // Disable button and show loading

        // Clean phone number before sending
        const cleanedPhone = cleanPhoneNumber(formData.phone);

        const url = `${BACKEND_HOST}/accounts/obtain-token/`;
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...formData,
            phone: cleanedPhone,
          }),
        });

        const resp = await response.json();

        if (response.ok) {
          login(resp?.access, resp?.refresh, resp?.user);
          setLoginSuccess(true);
          // Keep button disabled on success
        } else {
          // Re-enable button on error
          setIsLoading(false);

          // User-friendly error messages
          let errorMessage = "Login failed. Please check your credentials.";

          if (resp.detail) {
            const detailLower = resp.detail.toLowerCase();
            if (
              detailLower.includes("credential") ||
              detailLower.includes("authentication")
            ) {
              errorMessage =
                "Incorrect phone number or password. Please try again.";
            } else if (detailLower.includes("inactive")) {
              errorMessage =
                "Your account is inactive. Please contact support.";
            } else if (
              detailLower.includes("throttled") ||
              detailLower.includes("too many")
            ) {
              errorMessage =
                "Too many login attempts. Please wait a while before trying again.";
            } else {
              errorMessage = resp.detail;
            }
          } else if (resp.non_field_errors) {
            errorMessage = resp.non_field_errors[0];
          }

          setErrors({ general: errorMessage });
        }
      } catch (error) {
        console.error("Login error:", error);
        setIsLoading(false); // Re-enable button on error

        let errorMessage =
          "Network error. Please check your connection and try again.";

        if (error.message) {
          errorMessage = error.message;
        }

        setErrors({ general: errorMessage });
      }
      // Note: Don't set loading to false on success - keep button disabled
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleGoToDashboard = () => {
    onClose();
    navigate('/dashboard/home');
  };

  const handleStay = () => {
    onClose();
  };

  // Success view after login
  if (loginSuccess) {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-slate-900/60 z-50 flex justify-center items-center"
        >
          <motion.div
            initial={{ scale: 0, rotate: "12.5deg" }}
            animate={{ scale: 1, rotate: "0deg" }}
            exit={{ scale: 0, rotate: "0deg" }}
            onClick={(e) => e.stopPropagation()}
            className="relative bg-white w-[90%] max-w-md p-8 rounded-xl shadow-lg"
          >
            <div className="flex flex-col items-center text-center">
              {/* Success Icon */}
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <FaCheck className="w-10 h-10 text-green-600" />
              </div>

              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Login Successful!
              </h2>
              <p className="text-gray-600 mb-6">
                Welcome back! What would you like to do?
              </p>

              <div className="w-full space-y-3">
                <button
                  onClick={handleGoToDashboard}
                  className="w-full py-3 bg-blue-700 text-white font-bold rounded-lg hover:bg-blue-800 transition"
                >
                  Go to Dashboard
                </button>
                <button
                  onClick={handleStay}
                  className="w-full py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition"
                >
                  Stay on this page
                </button>
              </div>

              <p className="text-sm text-gray-500 mt-4">
                Auto-closing in <span className="font-semibold text-blue-600">{countdown}</span> seconds...
              </p>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    );
  }

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
                <p className="text-center text-red-500 text-sm">
                  {errors.general}
                </p>
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
                    placeholder="Enter your index number"
                    className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                  />
                  {errors.phone && (
                    <p className="text-red-500 text-sm">{errors.phone}</p>
                  )}
                </div>

                <div className="mb-4">
                  <label
                    htmlFor="password"
                    className="block text-gray-700 font-medium mb-2"
                  >
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      id="password"
                      placeholder="Enter your password"
                      className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={togglePasswordVisibility}
                      className="absolute inset-y-0 right-3 flex items-center text-gray-500 dark:text-gray-400"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                  {errors?.password && (
                    <p className="text-red-500 text-sm">{errors?.password}</p>
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
                  Login
                  {isLoading && (
                    <Hourglass
                      colors={["#ffffff", "#000000"]}
                      width="20"
                      height={16}
                    />
                  )}
                </button>

                <div className="text-center mt-4">
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                    Are you an executive member?{" "}
                    <span
                      onClick={switchToExecutive}
                      className="text-blue-600 hover:underline cursor-pointer"
                    >
                      Log in
                    </span>
                  </p>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Don't have an account?{" "}
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

export default Login;
