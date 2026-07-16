import { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Receipt,
  Info,
  Copy,
  Check,
  ArrowLeft,
  Search,
  Sparkles,
  ShieldCheck,
  Clock,
  HelpCircle,
  Mail,
  MessageSquare,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { Oval } from "react-loader-spinner";
import { Alert, AlertTitle, Snackbar } from "@mui/material";

export function RetryPaymentPage() {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const navigate = useNavigate();

  const [reference, setReference] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [result, setResult] = useState(null);
  const [copiedCode, setCopiedCode] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarSeverity, setSnackbarSeverity] = useState("info");

  const handleRetry = async (e) => {
    e.preventDefault();

    if (!reference.trim()) {
      setError("Please enter a transaction reference");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setResult(null);

    try {
      const response = await axiosInstance.post(
        "/payments/api/transactions/retry_verification/",
        {
          reference: reference.trim(),
        }
      );

      if (response.data.success) {
        setSuccess(response.data.message);
        setResult(response.data);

        // Show success notification
        setSnackbarMessage("Payment verified successfully!");
        setSnackbarSeverity("success");
        setSnackbarOpen(true);

        // Redirect after 3 seconds
        setTimeout(() => {
          navigate("/dashboard/purchases");
        }, 3000);
      } else {
        setError(response.data.error || "Failed to verify transaction");
      }
    } catch (err) {
      console.error("Retry verification error:", err);

      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.message ||
        "An error occurred while verifying your transaction. Please try again.";

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setReference("");
    setError(null);
    setSuccess(null);
    setResult(null);
  };

  const copyValidationCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setSnackbarMessage("Validation code copied!");
    setSnackbarSeverity("success");
    setSnackbarOpen(true);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const tips = [
    {
      icon: Clock,
      text: "Wait 5-10 minutes after payment before retrying verification",
    },
    {
      icon: RefreshCw,
      text: "Our system automatically checks pending transactions every 5 minutes",
    },
    {
      icon: Mail,
      text: "Keep your payment receipt/email from Paystack as proof",
    },
    {
      icon: MessageSquare,
      text: "Contact support if verification fails after multiple attempts",
    },
  ];

  const steps = [
    { step: 1, text: "Check your email for the Paystack payment receipt" },
    { step: 2, text: 'Find the "Reference" or "Transaction ID" field' },
    { step: 3, text: 'It usually starts with "TXN-" or is a long code' },
    { step: 4, text: "Copy and paste it in the field below" },
  ];

  return (
    <>
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={5000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ width: "100%" }}
        >
          <AlertTitle>
            {snackbarSeverity.charAt(0).toUpperCase() + snackbarSeverity.slice(1)}
          </AlertTitle>
          {snackbarMessage}
        </Alert>
      </Snackbar>

      <div className="min-h-screen bg-gray-50 py-8 sm:py-12 lg:py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8 sm:mb-12">
            <button
              onClick={() => navigate("/dashboard/purchases")}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition mb-6 group"
            >
              <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
              <span>Back to Purchases</span>
            </button>

            <motion.div
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
            >
              <h1 className="text-3xl sm:text-4xl md:text-5xl mb-2 font-bold text-gray-900">
                Retry{" "}
                <span className="relative text-blue-600">
                  Verification
                  <motion.div
                    variants={underlineAnimation(0.7)}
                    initial="offscreen"
                    whileInView="onscreen"
                    exit="reverse"
                    className="absolute left-0 bottom-0 h-1 bg-blue-600"
                    style={{ width: "0%", height: "3px" }}
                  />
                </span>
              </h1>
              <p className="text-gray-600 text-sm sm:text-base max-w-2xl">
                If your payment was successful but didn&apos;t reflect in your account,
                enter your transaction reference below to retry verification.
              </p>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Verification Form Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-white rounded-2xl shadow-lg overflow-hidden"
              >
                {/* Card Header */}
                <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                      <Search className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">
                        Payment Verification
                      </h2>
                      <p className="text-blue-100 text-sm">
                        Enter your transaction reference to verify
                      </p>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-6">
                  {!result ? (
                    <form onSubmit={handleRetry}>
                      {/* Input Field */}
                      <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Transaction Reference
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Receipt className="w-5 h-5 text-gray-400" />
                          </div>
                          <input
                            type="text"
                            value={reference}
                            onChange={(e) => setReference(e.target.value)}
                            placeholder="e.g., TXN-123456789ABC"
                            disabled={loading}
                            className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all text-lg font-mono disabled:bg-gray-50 disabled:cursor-not-allowed"
                          />
                        </div>
                        <p className="mt-2 text-sm text-gray-500">
                          Find this in your Paystack email receipt or SMS
                        </p>
                      </div>

                      {/* Error Alert */}
                      {error && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4"
                        >
                          <div className="flex items-start gap-3">
                            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="font-semibold text-red-800">
                                Verification Failed
                              </p>
                              <p className="text-sm text-red-700 mt-1">{error}</p>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        <button
                          type="submit"
                          disabled={loading || !reference.trim()}
                          className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all font-semibold disabled:bg-gray-300 disabled:cursor-not-allowed shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40"
                        >
                          {loading ? (
                            <>
                              <Oval
                                height={20}
                                width={20}
                                color="#ffffff"
                                secondaryColor="#ffffff"
                                strokeWidth={4}
                                strokeWidthSecondary={4}
                              />
                              <span>Verifying...</span>
                            </>
                          ) : (
                            <>
                              <RefreshCw className="w-5 h-5" />
                              <span>Verify Payment</span>
                            </>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => navigate("/dashboard/cart")}
                          disabled={loading}
                          className="px-6 py-4 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition font-medium disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    /* Success Result */
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                    >
                      {/* Success Banner */}
                      <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 mb-6">
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-green-800">
                              {result.message || "Payment Verified Successfully!"}
                            </h3>
                            {result.already_completed && (
                              <p className="text-sm text-green-700 mt-1">
                                This transaction was already processed.
                              </p>
                            )}
                            <p className="text-sm text-green-600 mt-2">
                              Redirecting to your purchases in 3 seconds...
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Validation Codes */}
                      {result.validation_codes && result.validation_codes.length > 0 && (
                        <div className="space-y-3 mb-6">
                          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-yellow-500" />
                            Your Validation Codes
                          </h4>
                          {result.validation_codes.map((item, index) => (
                            <div
                              key={index}
                              className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4"
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="font-medium text-gray-900">
                                    {item.product_name}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    Quantity: {item.quantity}
                                  </p>
                                  {item.variants_summary && (
                                    <p className="text-xs text-gray-500 mt-1">
                                      {item.variants_summary}
                                    </p>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-2xl font-bold font-mono text-blue-600 bg-white px-4 py-2 rounded-lg border border-blue-200">
                                    {item.validation_code}
                                  </span>
                                  <button
                                    onClick={() => copyValidationCode(item.validation_code)}
                                    className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                    title="Copy code"
                                  >
                                    {copiedCode === item.validation_code ? (
                                      <Check className="w-5 h-5" />
                                    ) : (
                                      <Copy className="w-5 h-5" />
                                    )}
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        <button
                          onClick={() => navigate("/dashboard/purchases")}
                          className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-semibold"
                        >
                          View My Purchases
                        </button>
                        <button
                          onClick={handleReset}
                          className="px-6 py-4 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition font-medium"
                        >
                          Verify Another
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>

              {/* How to Find Reference */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-2xl shadow-lg p-6"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                    <HelpCircle className="w-5 h-5 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">
                    How to Find Your Reference
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {steps.map((item) => (
                    <div
                      key={item.step}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl"
                    >
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        {item.step}
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{item.text}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Security Badge */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold">Secure Verification</h3>
                </div>
                <p className="text-green-100 text-sm">
                  Your payment information is verified directly with Paystack&apos;s
                  secure servers. We never store your card details.
                </p>
              </motion.div>

              {/* Tips Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-2xl shadow-lg p-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Info className="w-5 h-5 text-blue-600" />
                  <h3 className="font-bold text-gray-900">Helpful Tips</h3>
                </div>

                <div className="space-y-4">
                  {tips.map((tip, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                        <tip.icon className="w-4 h-4 text-blue-600" />
                      </div>
                      <p className="text-sm text-gray-600">{tip.text}</p>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Need Help */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-gray-100 rounded-2xl p-6"
              >
                <h3 className="font-bold text-gray-900 mb-2">Need Help?</h3>
                <p className="text-sm text-gray-600 mb-4">
                  If you&apos;re still having issues, our support team is ready to help.
                </p>
                <button
                  onClick={() => navigate("/dashboard/helpdesk")}
                  className="w-full px-4 py-3 bg-white text-gray-700 rounded-xl hover:bg-gray-50 transition font-medium border border-gray-200 flex items-center justify-center gap-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  Contact Support
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
