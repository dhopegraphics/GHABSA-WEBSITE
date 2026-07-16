import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Edit3,
  Copy,
  ExternalLink,
  Store,
  PartyPopper,
} from "lucide-react";
import Navbar from "../../../../Components/Navbar";
import { Footer } from "../../../../Components/Footer/Footer";
import { API_BASE_URL } from "../../../../utils/config";

// APPROVED STATUS VIEW
export function ApprovedStatusView({ application, onCopyTrackingCode }) {
  const getSellerDashboardUrl = () => {
    return `${API_BASE_URL}/seller-dashboard/login/?next=/seller-dashboard/`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          <div className="text-center mb-8">
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <PartyPopper className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">🎉 Congratulations!</h2>
            <p className="text-xl text-green-600 font-semibold mb-2">
              Your Seller Application Has Been Approved!
            </p>
            <p className="text-gray-600">
              Welcome to El Mercado! You can now access your seller dashboard and start listing
              your products.
            </p>
          </div>

          {/* Seller Details */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Store className="w-5 h-5 text-green-600" />
              Your Seller Profile
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Seller Name:</span>
                <span className="text-gray-900 font-medium">
                  {application.business_name || application.applicant_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Seller Type:</span>
                <span className="text-gray-900">
                  {application.seller_type_display || application.seller_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Email:</span>
                <span className="text-gray-900">{application.applicant_email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Approved On:</span>
                <span className="text-gray-900">
                  {application.updated_at
                    ? new Date(application.updated_at).toLocaleDateString()
                    : "Recently"}
                </span>
              </div>
            </div>
          </div>

          {/* Tracking Code */}
          {application.tracking_code && (
            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-gray-500 mb-2">Your Application Tracking Code:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white px-4 py-2 rounded-lg border font-mono text-lg">
                  {application.tracking_code}
                </code>
                <button
                  onClick={() => onCopyTrackingCode(application.tracking_code)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
                  title="Copy tracking code"
                >
                  <Copy className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {/* Action Buttons */}
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
            <Link
              to="/el-mercado"
              className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
            >
              Browse El Mercado
            </Link>
          </div>

          {/* Policy Links */}
          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <a
              href="/el_mercado/seller-terms"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border-2 border-purple-200 text-purple-600 rounded-lg font-medium hover:bg-purple-50 hover:border-purple-300 transition-all text-sm"
            >
              Terms &amp; Conditions
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              href="/el_mercado/commission-policy"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border-2 border-green-200 text-green-600 rounded-lg font-medium hover:bg-green-50 hover:border-green-300 transition-all text-sm"
            >
              Commission Policy
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <p className="text-center text-gray-500 text-sm mt-6">
            Need help getting started? Check out our{" "}
            <a href="/el-mercado/seller-guide" className="text-purple-600 hover:underline">
              Seller Guide
            </a>
          </p>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

// REJECTED STATUS VIEW
export function RejectedStatusView({ application, onCopyTrackingCode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          <div className="text-center mb-6">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Application Not Approved</h2>
            <p className="text-gray-600">
              Unfortunately, your seller application was not approved at this time.
            </p>
          </div>

          {application.status_reason && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
              <p className="text-red-800 font-medium text-sm mb-1">Reason:</p>
              <p className="text-red-700 text-sm">{application.status_reason}</p>
            </div>
          )}

          {/* Tracking Code */}
          {application.tracking_code && (
            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-gray-500 mb-2">Application Tracking Code:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white px-4 py-2 rounded-lg border font-mono">
                  {application.tracking_code}
                </code>
                <button
                  onClick={() => onCopyTrackingCode(application.tracking_code)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
                  title="Copy tracking code"
                >
                  <Copy className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/"
              className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Home
            </Link>
            <Link
              to="/contact"
              className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition-colors"
            >
              Contact Support
            </Link>
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

// PENDING / REVISION_REQUESTED / UNDER_REVIEW STATUS VIEW
export function PendingStatusView({
  application,
  updateSuccess,
  onDismissUpdateSuccess,
  onEnterEditMode,
  onCopyTrackingCode,
}) {
  const canEdit = ["PENDING", "REVISION_REQUESTED"].includes(application.status);
  const isRevisionRequested = application.status === "REVISION_REQUESTED";

  // Helper to find missing fields
  const getMissingFields = () => {
    const missing = [];
    if (!application.address_line_1) missing.push("Address");
    if (!application.city) missing.push("City");
    if (!application.region) missing.push("Region");
    if (!application.description) missing.push("Description");
    if (!application.categories_of_interest?.length) missing.push("Categories");
    if (application.seller_type === "BUSINESS" && !application.business_name) {
      missing.push("Business Name");
    }
    return missing;
  };

  const missingFields = getMissingFields();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-20">
        {/* Update Success Message */}
        {updateSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6 flex items-start gap-3"
          >
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-green-800 font-medium">Application Updated Successfully!</p>
              <p className="text-green-700 text-sm">Your changes have been saved.</p>
            </div>
            <button
              onClick={onDismissUpdateSuccess}
              className="ml-auto text-green-600 hover:text-green-800"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          <div className="text-center mb-6">
            <div
              className={`w-20 h-20 ${
                isRevisionRequested ? "bg-orange-100" : "bg-yellow-100"
              } rounded-full flex items-center justify-center mx-auto mb-6`}
            >
              <AlertCircle
                className={`w-10 h-10 ${
                  isRevisionRequested ? "text-orange-600" : "text-yellow-600"
                }`}
              />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {isRevisionRequested ? "Revision Requested" : "Application In Progress"}
            </h2>
            <p className="text-gray-600 mb-2">
              Your seller application is{" "}
              <span
                className={`font-semibold ${
                  isRevisionRequested ? "text-orange-600" : "text-yellow-600"
                }`}
              >
                {application.status_display || application.status}
              </span>
            </p>
            {isRevisionRequested && application.status_reason && (
              <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mt-4 text-left">
                <p className="text-orange-800 font-medium text-sm mb-1">Revision Reason:</p>
                <p className="text-orange-700 text-sm">{application.status_reason}</p>
              </div>
            )}
          </div>

          {/* Application Details */}
          <div className="bg-gray-50 rounded-xl p-6 mb-6 text-left">
            <h3 className="font-semibold text-gray-900 mb-4">Application Details:</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Type:</span>
                <span className="text-gray-900 font-medium">
                  {application.seller_type_display || application.seller_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Name:</span>
                <span className="text-gray-900">{application.applicant_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Email:</span>
                <span className="text-gray-900">{application.applicant_email}</span>
              </div>
              {application.business_name && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Business:</span>
                  <span className="text-gray-900">{application.business_name}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">City:</span>
                <span className="text-gray-900">{application.city || "Not provided"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Description:</span>
                <span className="text-gray-900 text-right max-w-[200px] truncate">
                  {application.description || "Not provided"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Submitted:</span>
                <span className="text-gray-900">
                  {application.created_at
                    ? new Date(application.created_at).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>
              {application.updated_at &&
                application.created_at &&
                new Date(application.updated_at).getTime() >
                  new Date(application.created_at).getTime() + 60000 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Updated:</span>
                    <span className="text-gray-900">
                      {new Date(application.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
            </div>

            {/* Missing fields warning */}
            {missingFields.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-orange-600 text-sm font-medium mb-2">
                  ⚠️ Incomplete Information:
                </p>
                <p className="text-gray-600 text-sm">{missingFields.join(", ")}</p>
              </div>
            )}
          </div>

          {/* Tracking Code */}
          {application.tracking_code && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
              <p className="text-sm text-blue-700 mb-2 font-medium">
                📋 Your Application Tracking Code:
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white px-4 py-2 rounded-lg border border-blue-200 font-mono text-lg text-center">
                  {application.tracking_code}
                </code>
                <button
                  onClick={() => onCopyTrackingCode(application.tracking_code)}
                  className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                  title="Copy tracking code"
                >
                  <Copy className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-blue-600 mt-2">
                Save this code to check your application status anytime.
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/"
              className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Home
            </Link>
            {canEdit && (
              <button
                onClick={onEnterEditMode}
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
              >
                <Edit3 className="w-5 h-5" />
                {isRevisionRequested ? "Make Revisions" : "Edit Application"}
              </button>
            )}
          </div>

          {!canEdit && application.status === "UNDER_REVIEW" && (
            <p className="text-center text-gray-500 text-sm mt-4">
              Your application is currently under review and cannot be edited.
            </p>
          )}
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}

export default PendingStatusView;
