import { useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  AlertCircle,
  XCircle,
  Clock,
  Store,
  ExternalLink,
  ArrowLeft,
  Copy,
  Loader2,
  FileEdit,
  PartyPopper,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useElMercado } from "../../Context/ElMercadoContext";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { API_BASE_URL } from "../../utils/config";

const STATUS_CONFIG = {
  PENDING: {
    icon: Clock,
    color: "yellow",
    bgColor: "bg-yellow-100",
    textColor: "text-yellow-600",
    borderColor: "border-yellow-200",
    title: "Pending Review",
    description: "Your application is awaiting review by our team.",
  },
  UNDER_REVIEW: {
    icon: Search,
    color: "blue",
    bgColor: "bg-blue-100",
    textColor: "text-blue-600",
    borderColor: "border-blue-200",
    title: "Under Review",
    description: "Our team is currently reviewing your application.",
  },
  APPROVED: {
    icon: PartyPopper,
    color: "green",
    bgColor: "bg-green-100",
    textColor: "text-green-600",
    borderColor: "border-green-200",
    title: "Approved!",
    description: "Congratulations! Your seller application has been approved.",
  },
  REJECTED: {
    icon: XCircle,
    color: "red",
    bgColor: "bg-red-100",
    textColor: "text-red-600",
    borderColor: "border-red-200",
    title: "Not Approved",
    description: "Unfortunately, your application was not approved.",
  },
  REVISION_REQUESTED: {
    icon: FileEdit,
    color: "orange",
    bgColor: "bg-orange-100",
    textColor: "text-orange-600",
    borderColor: "border-orange-200",
    title: "Revision Requested",
    description: "Please update your application with the requested changes.",
  },
};

export function CheckApplicationStatus() {
  const { checkApplicationByTrackingCode, loading } = useElMercado();
  const [trackingCode, setTrackingCode] = useState("");
  const [applicationData, setApplicationData] = useState(null);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!trackingCode.trim()) {
      setError("Please enter a tracking code");
      return;
    }

    setError(null);
    setSearched(true);
    const result = await checkApplicationByTrackingCode(trackingCode.trim());
    
    if (result.success) {
      setApplicationData(result.data);
    } else {
      setError(result.error);
      setApplicationData(null);
    }
  };

  const copyTrackingCode = (code) => {
    navigator.clipboard.writeText(code);
  };

  const getSellerDashboardUrl = () => {
    return `${API_BASE_URL}/seller-dashboard/login/?next=/seller-dashboard/`;
  };

  const statusConfig = applicationData ? STATUS_CONFIG[applicationData.status] : null;
  const StatusIcon = statusConfig?.icon || AlertCircle;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-xl mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-purple-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Check Application Status
            </h1>
            <p className="text-gray-600">
              Enter your tracking code to check your seller application status
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="mb-8">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={trackingCode}
                  onChange={(e) => setTrackingCode(e.target.value.toUpperCase())}
                  placeholder="e.g., ELM-ABC12345"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all font-mono text-lg tracking-wider"
                  maxLength={12}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Search className="w-5 h-5" />
                )}
                {loading ? "Checking..." : "Check"}
              </button>
            </div>
          </form>

          {/* Error State */}
          {error && searched && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-800 font-medium">Application Not Found</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </motion.div>
          )}

          {/* Application Result */}
          {applicationData && statusConfig && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-6"
            >
              {/* Status Banner */}
              <div className={`${statusConfig.bgColor} ${statusConfig.borderColor} border rounded-xl p-6 text-center`}>
                <StatusIcon className={`w-12 h-12 ${statusConfig.textColor} mx-auto mb-3`} />
                <h2 className={`text-xl font-bold ${statusConfig.textColor} mb-1`}>
                  {statusConfig.title}
                </h2>
                <p className="text-gray-600 text-sm">
                  {statusConfig.description}
                </p>
              </div>

              {/* Application Details */}
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Application Details</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tracking Code:</span>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-900 font-mono">{applicationData.tracking_code}</span>
                      <button
                        onClick={() => copyTrackingCode(applicationData.tracking_code)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Applicant:</span>
                    <span className="text-gray-900">{applicationData.applicant_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Email:</span>
                    <span className="text-gray-900">{applicationData.applicant_email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Seller Type:</span>
                    <span className="text-gray-900">
                      {applicationData.seller_type_display || applicationData.seller_type}
                    </span>
                  </div>
                  {applicationData.business_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Business:</span>
                      <span className="text-gray-900">{applicationData.business_name}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-500">Submitted:</span>
                    <span className="text-gray-900">
                      {new Date(applicationData.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Reason (for rejected/revision) */}
              {applicationData.status_reason && (
                <div className={`${statusConfig.bgColor} ${statusConfig.borderColor} border rounded-xl p-4`}>
                  <p className={`${statusConfig.textColor} font-medium text-sm mb-1`}>
                    {applicationData.status === "REJECTED" ? "Reason:" : "Requested Changes:"}
                  </p>
                  <p className="text-gray-700 text-sm">{applicationData.status_reason}</p>
                </div>
              )}

              {/* Action for Approved */}
              {applicationData.status === "APPROVED" && (
                <div className="space-y-3">
                  <a
                    href={getSellerDashboardUrl()}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full inline-flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl"
                  >
                    <Store className="w-5 h-5" />
                    Go to Seller Dashboard
                    <ExternalLink className="w-4 h-4" />
                  </a>
                  <p className="text-center text-gray-500 text-sm">
                    Use your registered email to log in to the seller dashboard.
                  </p>
                </div>
              )}

              {/* Action for Revision */}
              {applicationData.status === "REVISION_REQUESTED" && (
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 text-center">
                  <p className="text-orange-700 text-sm mb-2">
                    Please log in to your account to make the requested changes.
                  </p>
                  <Link
                    to="/el-mercado/become-a-seller"
                    className="inline-flex items-center gap-2 text-orange-600 hover:text-orange-700 font-medium"
                  >
                    Go to Application Page
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </div>
              )}
            </motion.div>
          )}

          {/* Help Text */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-gray-500 text-sm text-center mb-4">
              Don&apos;t have a tracking code?
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/el-mercado/become-a-seller"
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-purple-50 text-purple-600 rounded-lg font-medium hover:bg-purple-100 transition-colors text-sm"
              >
                <Store className="w-4 h-4" />
                Apply to Become a Seller
              </Link>
              <Link
                to="/"
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium hover:bg-gray-200 transition-colors text-sm"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Home
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

export default CheckApplicationStatus;
