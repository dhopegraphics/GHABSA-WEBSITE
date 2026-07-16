/**
 * Public Donations Page
 * Display donation statistics, recent donations, withdrawals, and donation form
 */
import React, { useState, useEffect, useContext } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Heart,
  Users,
  TrendingUp,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Gift,
  Eye,
  EyeOff,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Receipt,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import {
  getPublicDonationData,
  initializeDonation,
  verifyDonation,
} from "../services/donationService";

// Format currency
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return "Hidden";
  return `GH₵${parseFloat(amount).toLocaleString("en-GH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

// Format date
const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString("en-GH", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

// Format time ago
const timeAgo = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(dateString);
};

// Stat Card Component
const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
  </div>
);

// Recent Donation Item
const DonationItem = ({ donation }) => (
  <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-red-500 flex items-center justify-center">
        <Heart className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="font-medium text-gray-900">{donation.display_name}</p>
        {donation.message && (
          <p className="text-sm text-gray-500 truncate max-w-[200px]">
            "{donation.message}"
          </p>
        )}
      </div>
    </div>
    <div className="text-right">
      <p
        className={`font-semibold ${
          donation.display_amount ? "text-green-600" : "text-gray-400"
        }`}
      >
        {formatCurrency(donation.display_amount)}
      </p>
      <p className="text-xs text-gray-400">{timeAgo(donation.completed_at)}</p>
    </div>
  </div>
);

// Withdrawal Item
const WithdrawalItem = ({ withdrawal }) => (
  <div className="flex items-start justify-between py-3 border-b border-gray-100 last:border-0">
    <div className="flex items-start gap-3">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center flex-shrink-0">
        <ArrowUpRight className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="font-medium text-gray-900">{withdrawal.purpose}</p>
        <p className="text-sm text-gray-500">To: {withdrawal.recipient_name}</p>
        <span className="inline-block mt-1 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
          {withdrawal.category_display}
        </span>
      </div>
    </div>
    <div className="text-right">
      <p className="font-semibold text-red-600">
        -{formatCurrency(withdrawal.amount)}
      </p>
      <p className="text-xs text-gray-400">
        {timeAgo(withdrawal.completed_at)}
      </p>
    </div>
  </div>
);

// Donation Form Component
const DonationForm = ({ user, onSuccess }) => {
  // Extract actual user data (user context stores { access, refresh, user })
  const userData = user?.user || user;

  const [formData, setFormData] = useState({
    amount: "",
    email:
      userData?.personal_email ||
      userData?.student_email ||
      userData?.email ||
      "",
    donor_name: userData
      ? `${userData.first_name || ""} ${userData.last_name || ""}`.trim()
      : "",
    phone: userData?.phone || "",
    message: "",
    is_anonymous: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const predefinedAmounts = [10, 20, 50, 100, 200, 500];

  const handleAmountClick = (amount) => {
    setFormData((prev) => ({ ...prev, amount: amount.toString() }));
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!formData.amount || parseFloat(formData.amount) < 1) {
      setError("Please enter a valid amount (minimum GH₵1.00)");
      return;
    }

    if (!formData.email) {
      setError("Please enter your email address");
      return;
    }

    setLoading(true);

    try {
      const callbackUrl = `${window.location.origin}/donate?verify=true`;

      const result = await initializeDonation({
        ...formData,
        amount: parseFloat(formData.amount),
        callback_url: callbackUrl,
      });

      if (result.success && result.data.authorization_url) {
        // Store reference for verification
        localStorage.setItem("pendingDonationRef", result.data.reference);
        // Redirect to payment page
        window.location.href = result.data.authorization_url;
      } else {
        setError(
          typeof result.error === "object"
            ? Object.values(result.error).flat().join(", ")
            : result.error || "Failed to initialize donation"
        );
      }
    } catch (err) {
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Predefined Amounts */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Amount
        </label>
        <div className="grid grid-cols-3 gap-2">
          {predefinedAmounts.map((amount) => (
            <button
              key={amount}
              type="button"
              onClick={() => handleAmountClick(amount)}
              className={`py-3 px-4 rounded-lg border-2 font-semibold transition-all ${
                formData.amount === amount.toString()
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-blue-300 text-gray-700"
              }`}
            >
              GH₵{amount}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Amount */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Or Enter Custom Amount
        </label>
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 font-medium">
            GH₵
          </span>
          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            min="1"
            step="0.01"
            placeholder="0.00"
            className="w-full pl-14 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Donor Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Name
          </label>
          <input
            type="text"
            name="donor_name"
            value={formData.donor_name}
            onChange={handleChange}
            placeholder="John Doe"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            placeholder="john@example.com"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Phone */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Phone Number (Optional)
        </label>
        <input
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+233XXXXXXXXX"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Message */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Message (Optional)
        </label>
        <textarea
          name="message"
          value={formData.message}
          onChange={handleChange}
          rows={3}
          placeholder="Leave a message of support..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
        />
      </div>

      {/* Privacy Option */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            name="is_anonymous"
            checked={formData.is_anonymous}
            onChange={handleChange}
            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <div className="flex items-center gap-2">
            <EyeOff className="w-4 h-4 text-gray-500" />
            <span className="text-gray-700">
              Hide my name (donate anonymously)
            </span>
          </div>
        </label>
        <p className="text-xs text-gray-500 mt-2 ml-8">
          Note: Donation amounts are always public for full transparency.
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2 disabled:opacity-70"
      >
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Heart className="w-5 h-5" />
        )}
        {loading ? "Processing..." : "Donate Now"}
      </button>
    </form>
  );
};

// Verification Result Modal
const VerificationModal = ({ result, onClose }) => (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-2xl max-w-md w-full p-8 text-center">
      {result.success ? (
        <>
          <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Thank You! 🎉
          </h3>
          <p className="text-gray-600 mb-4">
            Your donation of {formatCurrency(result.donation?.amount)} has been
            received successfully.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Reference: {result.donation?.reference}
          </p>
        </>
      ) : (
        <>
          <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-600" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Payment Issue
          </h3>
          <p className="text-gray-600 mb-6">
            {result.error ||
              "We couldn't verify your payment. Please try again."}
          </p>
        </>
      )}
      <button
        onClick={onClose}
        className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
      >
        Continue
      </button>
    </div>
  </div>
);

// Main Page Component
export default function DonationsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useContext(UserContext);

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [showAllDonations, setShowAllDonations] = useState(false);
  const [showAllWithdrawals, setShowAllWithdrawals] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  // Fetch public data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const result = await getPublicDonationData();
      if (result.success) {
        setData(result.data);
      } else {
        setError(result.error);
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  // Handle payment verification
  useEffect(() => {
    const verifyPayment = async () => {
      const isVerify = searchParams.get("verify");
      const reference =
        searchParams.get("reference") ||
        localStorage.getItem("pendingDonationRef");

      if (isVerify && reference) {
        const result = await verifyDonation(reference);
        setVerificationResult(result.data || result);
        localStorage.removeItem("pendingDonationRef");

        // Clear URL params
        setSearchParams({});

        // Refresh data
        const refreshResult = await getPublicDonationData();
        if (refreshResult.success) {
          setData(refreshResult.data);
        }
      }
    };

    verifyPayment();
  }, [searchParams]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading donation data...</p>
        </div>
      </div>
    );
  }

  const wallet = data?.wallet || {};
  const recentDonations = data?.recent_donations || [];
  const recentWithdrawals = data?.recent_withdrawals || [];
  const topDonors = data?.top_donors || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Verification Modal */}
      {verificationResult && (
        <VerificationModal
          result={verificationResult}
          onClose={() => setVerificationResult(null)}
        />
      )}

      {/* Back to Homepage Button */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <button
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium shadow-sm mb-4"
        >
          <ArrowDownRight className="w-5 h-5" />
          Back to Homepage
        </button>
      </div>

      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="flex items-center justify-center mb-6">
              <div className="p-4 bg-white/20 rounded-full backdrop-blur-sm">
                <Heart className="w-10 h-10" />
              </div>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Support Student Welfare 💙
            </h1>
            <p className="text-xl text-white/90 mb-8">
              Your donations go directly to supporting students in need —
              helping with medical emergencies, financial hardships, and
              critical welfare support. Every contribution touches a life!
            </p>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={Wallet}
            title="Current Balance"
            value={formatCurrency(wallet.balance)}
            color="bg-green-500"
          />
          <StatCard
            icon={TrendingUp}
            title="Total Received"
            value={formatCurrency(wallet.total_received)}
            color="bg-blue-500"
          />
          <StatCard
            icon={ArrowDownRight}
            title="Total Withdrawn"
            value={formatCurrency(wallet.total_withdrawn)}
            color="bg-orange-500"
          />
          <StatCard
            icon={Users}
            title="Total Donors"
            value={wallet.total_donors_count || 0}
            subtitle={`${wallet.total_donations_count || 0} donations`}
            color="bg-purple-500"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Donation Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sticky top-8">
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <Gift className="w-5 h-5 text-pink-500" />
                Make a Donation
              </h2>
              <DonationForm user={user} />
            </div>
          </div>

          {/* Activity Feed */}
          <div className="lg:col-span-2 space-y-6">
            {/* Recent Donations */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <Heart className="w-5 h-5 text-pink-500" />
                  Recent Donations
                </h2>
                {recentDonations.length > 5 && (
                  <button
                    onClick={() => setShowAllDonations(!showAllDonations)}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    {showAllDonations ? "Show Less" : "View All"}
                    {showAllDonations ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
              {recentDonations.length === 0 ? (
                <div className="text-center py-8">
                  <Heart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">
                    No donations yet. Be the first!
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {(showAllDonations
                    ? recentDonations
                    : recentDonations.slice(0, 5)
                  ).map((donation) => (
                    <DonationItem key={donation.id} donation={donation} />
                  ))}
                </div>
              )}
            </div>

            {/* Withdrawals/Expenses */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-orange-500" />
                  Fund Utilization
                </h2>
                {recentWithdrawals.length > 5 && (
                  <button
                    onClick={() => setShowAllWithdrawals(!showAllWithdrawals)}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    {showAllWithdrawals ? "Show Less" : "View All"}
                    {showAllWithdrawals ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
              {recentWithdrawals.length === 0 ? (
                <div className="text-center py-8">
                  <Receipt className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">
                    No expenses recorded yet. Funds are being saved!
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {(showAllWithdrawals
                    ? recentWithdrawals
                    : recentWithdrawals.slice(0, 5)
                  ).map((withdrawal) => (
                    <WithdrawalItem
                      key={withdrawal.id}
                      withdrawal={withdrawal}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Top Donors */}
            {topDonors.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-500" />
                  Top Supporters
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {topDonors.slice(0, 6).map((donor, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                          index === 0
                            ? "bg-yellow-500"
                            : index === 1
                            ? "bg-gray-400"
                            : index === 2
                            ? "bg-amber-600"
                            : "bg-blue-500"
                        }`}
                      >
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {donor.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {donor.donation_count} donation
                          {donor.donation_count !== 1 ? "s" : ""}
                        </p>
                      </div>
                      <p className="font-semibold text-green-600">
                        {formatCurrency(donor.total_donated)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="bg-white border-t border-gray-100 py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <details className="group bg-gray-50 rounded-lg">
              <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-gray-900">
                How is my donation used?
                <ChevronDown className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" />
              </summary>
              <p className="px-4 pb-4 text-gray-600">
                100% of your donations go directly to{" "}
                <strong>student welfare</strong> — supporting students facing
                medical emergencies, unexpected financial hardships, bereavement
                support, and other critical needs. We believe in taking care of
                our own. All expenses are transparently recorded and visible in
                the "Fund Utilization" section.
              </p>
            </details>
            <details className="group bg-gray-50 rounded-lg">
              <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-gray-900">
                Can I donate anonymously?
                <ChevronDown className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" />
              </summary>
              <p className="px-4 pb-4 text-gray-600">
                Yes! You can choose to make your donation anonymous by checking
                the "Make my donation anonymous" option. Your name will be
                hidden publicly, but we'll still have your email for the
                receipt.
              </p>
            </details>
            <details className="group bg-gray-50 rounded-lg">
              <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-gray-900">
                What payment methods are accepted?
                <ChevronDown className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" />
              </summary>
              <p className="px-4 pb-4 text-gray-600">
                We accept mobile money (MTN, Vodafone, AirtelTigo) and card
                payments (Visa, Mastercard) through our secure Paystack payment
                gateway.
              </p>
            </details>
            <details className="group bg-gray-50 rounded-lg">
              <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-gray-900">
                Is my payment secure?
                <ChevronDown className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" />
              </summary>
              <p className="px-4 pb-4 text-gray-600">
                Absolutely! All payments are processed through Paystack, a
                PCI-DSS compliant payment provider. We never store your card
                details on our servers.
              </p>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}
