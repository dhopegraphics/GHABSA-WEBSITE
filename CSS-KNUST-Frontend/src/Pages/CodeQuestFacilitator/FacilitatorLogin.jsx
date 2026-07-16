import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import axios from "axios";

const FacilitatorLogin = () => {
  const navigate = useNavigate();
  const [accessCode, setAccessCode] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAccessCodeChange = (e) => {
    const value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (value.length <= 12) {
      setAccessCode(value);
      setError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (accessCode.length !== 12) {
      setError("Access code must be 12 characters");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await axios.post("/codequest/facilitator/login/", {
        access_code: accessCode,
      });

      // Store access code
      if (rememberMe) {
        localStorage.setItem("facilitator_access_code", accessCode);
      } else {
        sessionStorage.setItem("facilitator_access_code", accessCode);
      }

      // Store facilitator data
      localStorage.setItem(
        "facilitator_data",
        JSON.stringify(response.data.facilitator)
      );

      // Navigate to dashboard
      navigate("/code-quest-facilitators/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.error || "Invalid access code. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 flex items-center justify-center p-4">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      </div>

      {/* Login Card */}
      <motion.div
        className="relative z-10 bg-white rounded-2xl shadow-2xl max-w-md w-full p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            className="inline-block text-6xl mb-4"
            animate={{
              rotate: [0, 10, -10, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            🎯
          </motion.div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Facilitator Portal
          </h1>
          <p className="text-gray-600">
            Enter your access code to view and score projects
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-2">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          </motion.div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Access Code Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Access Code
            </label>
            <input
              type="text"
              value={accessCode}
              onChange={handleAccessCodeChange}
              placeholder="ABCD12345678"
              maxLength={12}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-center text-2xl font-mono tracking-wider uppercase"
              required
            />
            <p className="text-sm text-gray-500 mt-2 text-center">
              {accessCode.length}/12 characters
            </p>
          </div>

          {/* Remember Me */}
          <div className="flex items-center">
            <input
              id="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <label
              htmlFor="remember-me"
              className="ml-2 block text-sm text-gray-700"
            >
              Remember me on this device
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || accessCode.length !== 12}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Logging in...</span>
              </div>
            ) : (
              "Login to Dashboard"
            )}
          </button>
        </form>

        {/* Help Section */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 text-center">
            Don&apos;t have an access code?
          </p>
          <p className="text-sm text-purple-600 font-medium text-center mt-1">
            Contact the admin for your access code
          </p>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">Code Quest Facilitator Portal</p>
          <p className="text-xs text-gray-400 mt-1">
            Presentation Day Scoring System
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default FacilitatorLogin;
