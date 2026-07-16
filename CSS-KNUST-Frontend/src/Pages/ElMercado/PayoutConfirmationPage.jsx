import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  ArrowLeft,
  Wallet,
  User,
  Building2,
  Hash,
  BadgeCheck,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { API_BASE_URL } from "../../utils/config";

export function PayoutConfirmationPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [payoutData, setPayoutData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState(null);
  const [confirmed, setConfirmed] = useState(false);

  // Fetch payout details on mount
  useEffect(() => {
    const fetchPayoutDetails = async () => {
      if (!token) {
        setError("No confirmation token provided.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE_URL}/marketplace/payout/confirm/?token=${encodeURIComponent(token)}`
        );
        const data = await response.json();

        if (response.ok) {
          setPayoutData(data);
        } else {
          setError(data.error || "Failed to fetch payout details.");
        }
      } catch {
        setError("Network error. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchPayoutDetails();
  }, [token]);

  // Handle confirmation
  const handleConfirm = async () => {
    if (!token || confirming) return;

    setConfirming(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/marketplace/payout/confirm/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      });
      const data = await response.json();

      if (response.ok) {
        setConfirmed(true);
        setPayoutData((prev) => ({
          ...prev,
          status: "COMPLETED",
          can_confirm: false,
        }));
      } else {
        setError(data.error || "Failed to confirm payout.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setConfirming(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <Loader2 className="w-12 h-12 animate-spin text-emerald-600" />
          <p className="mt-4 text-gray-600">Loading payout details...</p>
        </div>
        <Footer />
      </div>
    );
  }

  // Error state (no token or fetch failed)
  if (error && !payoutData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center"
          >
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Error</h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Return to Home
            </Link>
          </motion.div>
        </div>
        <Footer />
      </div>
    );
  }

  // Success confirmation state
  if (confirmed) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.5, delay: 0.2 }}
              className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6"
            >
              <CheckCircle className="w-12 h-12 text-emerald-500" />
            </motion.div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Payout Confirmed!
            </h1>
            <p className="text-gray-600 mb-4">
              The payout has been marked as completed. The seller will be notified.
            </p>
            <div className="bg-emerald-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-emerald-700">
                <span className="font-semibold">Reference:</span>{" "}
                {payoutData?.reference}
              </p>
              <p className="text-sm text-emerald-700 mt-1">
                <span className="font-semibold">Amount:</span> GHS{" "}
                {payoutData?.net_amount}
              </p>
            </div>
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Return to Home
            </Link>
          </motion.div>
        </div>
        <Footer />
      </div>
    );
  }

  // Main payout details view
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Wallet className="w-8 h-8 text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Payout Confirmation
          </h1>
          <p className="text-gray-600 mt-2">
            Review and confirm the payout details below
          </p>
        </motion.div>

        {/* Payout Details Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-lg overflow-hidden"
        >
          {/* Status Badge */}
          <div
            className={`px-6 py-3 ${
              payoutData?.status === "COMPLETED"
                ? "bg-emerald-500"
                : payoutData?.status === "PENDING"
                ? "bg-yellow-500"
                : "bg-gray-500"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-white font-medium flex items-center gap-2">
                <BadgeCheck className="w-5 h-5" />
                Status: {payoutData?.status}
              </span>
              {payoutData?.can_confirm && (
                <span className="text-white/80 text-sm">Awaiting Confirmation</span>
              )}
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Amount Section */}
            <div className="bg-gray-50 rounded-xl p-5">
              <p className="text-sm text-gray-500 mb-1">Amount to Transfer</p>
              <p className="text-3xl font-bold text-gray-900">
                GHS {payoutData?.net_amount}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Original: GHS {payoutData?.amount} | Fee: GHS {payoutData?.platform_fee}
              </p>
            </div>

            {/* Seller Info */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <User className="w-5 h-5 text-gray-400" />
                Seller Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Seller Name</p>
                  <p className="font-medium text-gray-900">{payoutData?.seller_name}</p>
                </div>
              </div>
            </div>

            {/* Account Info */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-gray-400" />
                Payment Account
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Account Name</p>
                  <p className="font-medium text-gray-900">
                    {payoutData?.account_name || "N/A"}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Account Number</p>
                  <p className="font-medium text-gray-900">
                    {payoutData?.account_number || "N/A"}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Payment Method</p>
                  <p className="font-medium text-gray-900">
                    {payoutData?.payout_method || "N/A"}
                  </p>
                </div>
                {payoutData?.provider && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Provider</p>
                    <p className="font-medium text-gray-900">
                      {payoutData?.provider}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Reference & Date */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <Hash className="w-5 h-5 text-gray-400" />
                Request Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Reference</p>
                  <p className="font-medium text-gray-900 font-mono text-sm">
                    {payoutData?.reference}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Requested On</p>
                  <p className="font-medium text-gray-900">
                    {payoutData?.created_at
                      ? new Date(payoutData.created_at).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "N/A"}
                  </p>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3"
              >
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 text-sm">{error}</p>
              </motion.div>
            )}

            {/* Action Buttons */}
            {payoutData?.can_confirm ? (
              <div className="pt-4 border-t border-gray-100">
                <p className="text-sm text-gray-600 mb-4 text-center">
                  Please confirm that you have completed the mobile money transfer
                  to the account details shown above.
                </p>
                <button
                  onClick={handleConfirm}
                  disabled={confirming}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  {confirming ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Confirming...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Yes, I&apos;ve Sent the Money
                    </>
                  )}
                </button>
                <p className="text-xs text-gray-500 text-center mt-3">
                  This will mark the payout as completed and notify the seller.
                </p>
              </div>
            ) : (
              <div className="pt-4 border-t border-gray-100">
                <div className="bg-gray-100 rounded-lg p-4 text-center">
                  <p className="text-gray-600">
                    {payoutData?.status === "COMPLETED"
                      ? "This payout has already been completed."
                      : "This payout cannot be confirmed at this time."}
                  </p>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Back Link */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center mt-6"
        >
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Home
          </Link>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

export default PayoutConfirmationPage;
