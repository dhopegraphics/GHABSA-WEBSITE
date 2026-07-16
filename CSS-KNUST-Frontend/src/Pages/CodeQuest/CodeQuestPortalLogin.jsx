import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const CodeQuestPortalLogin = () => {
  const [accessKey, setAccessKey] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // API call to verify access key and get user role
      const response = await axios.post(`${API_BASE_URL}/codequest/portal/login/`, {
        access_key: accessKey,
      });

      const { user_type, user_data } = response.data;

      // Store access key and user data
      if (rememberMe) {
        localStorage.setItem("cq_access_key", accessKey);
        localStorage.setItem("cq_user_data", JSON.stringify(user_data));
      } else {
        sessionStorage.setItem("cq_access_key", accessKey);
        sessionStorage.setItem("cq_user_data", JSON.stringify(user_data));
      }

      // Navigate based on user type
      if (user_type === "participant") {
        navigate("/code-quest-portal/participant");
      } else if (user_type === "consultant") {
        navigate("/code-quest-portal/consultant");
      } else {
        setError("Invalid user type");
      }
    } catch (err) {
      setError(
        err.response?.data?.message ||
          "Invalid access key. Please check and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center px-4">
      {/* Background Elements */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-20 w-64 h-64 bg-white rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <motion.div
        className="relative z-10 w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <motion.div
            className="text-6xl mb-4"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
          >
            🚀
          </motion.div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Code Quest Portal
          </h1>
          <p className="text-blue-200">Enter your access key to continue</p>
        </div>

        {/* Login Card */}
        <motion.div
          className="bg-white rounded-2xl shadow-2xl p-8"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <motion.div
                className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                {error}
              </motion.div>
            )}

            {/* Access Key Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Access Key *
              </label>
              <input
                type="text"
                value={accessKey}
                onChange={(e) => setAccessKey(e.target.value.toUpperCase())}
                placeholder="Enter your 12-character access key"
                required
                maxLength={12}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-lg tracking-wider uppercase"
              />
              <p className="text-sm text-gray-500 mt-1">
                Example: ABC123XYZ789
              </p>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="rememberMe"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <label
                htmlFor="rememberMe"
                className="ml-2 text-sm text-gray-700"
              >
                Remember me on this device
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || accessKey.length < 12}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 rounded-lg font-semibold text-lg transition-colors"
            >
              {loading ? "Verifying..." : "Access Portal"}
            </button>
          </form>

          {/* Help Section */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="space-y-2 text-sm text-gray-600">
              <p className="flex items-start gap-2">
                <span>💡</span>
                <span>
                  Your access key was sent to your email after registration
                </span>
              </p>
              <p className="flex items-start gap-2">
                <span>❓</span>
                <span>
                  Lost your access key?{" "}
                  <a
                    href="mailto:admin@biochemknust.com"
                    className="text-blue-600 hover:underline"
                  >
                    Contact support
                  </a>
                </span>
              </p>
              <p className="flex items-start gap-2">
                <span>🔒</span>
                <span>Your data is secure and encrypted</span>
              </p>
            </div>
          </div>
        </motion.div>

        {/* Back to Registration */}
        <div className="text-center mt-6">
          <a
            href="/code-quest"
            className="text-blue-200 hover:text-white transition-colors"
          >
            ← Back to Registration
          </a>
        </div>
      </motion.div>
    </div>
  );
};

export default CodeQuestPortalLogin;
