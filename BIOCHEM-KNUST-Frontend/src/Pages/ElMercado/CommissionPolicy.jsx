import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { Helmet } from "react-helmet-async";
import { 
  DollarSign, 
  TrendingUp, 
  Calculator,
  AlertCircle,
  CheckCircle2,
  Info,
  Percent,
  CreditCard,
  Clock,
  Loader2
} from "lucide-react";
import api from "../../services/api";

export function CommissionPolicy() {
  const [loading, setLoading] = useState(true);
  const [commissionData, setCommissionData] = useState(null);
  const [error, setError] = useState(null);
  const [isVerified, setIsVerified] = useState(false);
  const [trackingCode, setTrackingCode] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState('');

  useEffect(() => {
    // Check if tracking code is stored in sessionStorage
    const storedTrackingCode = sessionStorage.getItem('seller_tracking_code');
    if (storedTrackingCode) {
      setTrackingCode(storedTrackingCode);
      setIsVerified(true);
      fetchCommissionRates(storedTrackingCode);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyTrackingCode = async (code) => {
    try {
      setVerifying(true);
      setVerificationError('');
      const response = await api.post('/marketplace/settings/verify_tracking_code/', {
        tracking_code: code
      });
      
      if (response.data.valid) {
        setIsVerified(true);
        sessionStorage.setItem('seller_tracking_code', code);
        fetchCommissionRates(code);
      }
    } catch (err) {
      setVerificationError(err.response?.data?.message || 'Invalid tracking code. Please check and try again.');
    } finally {
      setVerifying(false);
    }
  };

  const handleVerifySubmit = (e) => {
    e.preventDefault();
    if (trackingCode.trim()) {
      verifyTrackingCode(trackingCode.trim());
    }
  };

  const fetchCommissionRates = async (code) => {
    try {
      setLoading(true);
      const response = await api.post('/marketplace/settings/commission_rates/', {
        tracking_code: code
      });
      setCommissionData(response.data);
    } catch (err) {
      console.error('Failed to fetch commission rates:', err);
      setError('Failed to load commission rates');
      // Clear stored tracking code if it's invalid
      if (err.response?.status === 403) {
        sessionStorage.removeItem('seller_tracking_code');
        setIsVerified(false);
        setVerificationError('Your session has expired. Please verify your tracking code again.');
      }
      // Fallback to default values
      setCommissionData({
        commission_rates: [],
        default_rate: 5,
        fees: {
          payment_processing_percentage: 2.5,
          payment_processing_fixed: 1.00,
          payout_transaction_fee: 5.00,
          payout_processing_percentage: 1.5
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Map category types to icons and colors
  const categoryConfig = {
    'STANDARD': {
      icon: <DollarSign className="w-6 h-6" />,
      color: "from-blue-600 to-cyan-600"
    },
    'DIGITAL': {
      icon: <TrendingUp className="w-6 h-6" />,
      color: "from-purple-600 to-pink-600"
    },
    'SERVICES': {
      icon: <CheckCircle2 className="w-6 h-6" />,
      color: "from-green-600 to-emerald-600"
    },
    'HANDMADE': {
      icon: <Percent className="w-6 h-6" />,
      color: "from-orange-600 to-red-600"
    }
  };

  // Build commission tiers from fetched data
  const commissionTiers = commissionData?.commission_rates.map(rate => {
    const config = categoryConfig[rate.category_type] || {
      icon: <DollarSign className="w-6 h-6" />,
      color: "from-gray-600 to-gray-800"
    };

    return {
      type: rate.category_name,
      rate: `${rate.rate}%`,
      description: rate.description,
      icon: config.icon,
      color: config.color,
      examples: rate.examples || []
    };
  }) || [];

  const additionalFees = commissionData ? [
    {
      name: "Payment Processing Fee",
      rate: `${commissionData.fees.payment_processing_percentage}% + GHS ${commissionData.fees.payment_processing_fixed.toFixed(2)}`,
      description: "Covers payment gateway costs (Paystack, MTN Mobile Money, Vodafone Cash)",
      icon: <CreditCard className="w-5 h-5" />
    },
    {
      name: "Payout Transaction Fee",
      rate: `GHS ${commissionData.fees.payout_transaction_fee.toFixed(2)} per payout`,
      description: "One-time fee per withdrawal to your bank or mobile money account",
      icon: <DollarSign className="w-5 h-5" />
    },
    {
      name: "Payout Processing Fee",
      rate: `${commissionData.fees.payout_processing_percentage}%`,
      description: "Processing fee deducted from payout amount",
      icon: <Percent className="w-5 h-5" />
    }
  ] : [];

  // Calculate example with dynamic rates
  const calculateExample = () => {
    if (!commissionData) return { salePrice: 200, commission: 10, paymentFee: 6, payoutFee: 1.84, netEarnings: 182.16 };
    
    const salePrice = 200;
    const commission = salePrice * (commissionData.default_rate / 100);
    const paymentFee = (salePrice * (commissionData.fees.payment_processing_percentage / 100)) + commissionData.fees.payment_processing_fixed;
    const afterCommissionAndPayment = salePrice - commission - paymentFee;
    const payoutFee = afterCommissionAndPayment * (commissionData.fees.payout_processing_percentage / 100);
    const netEarnings = afterCommissionAndPayment - payoutFee;
    
    return {
      salePrice,
      commission: commission.toFixed(2),
      paymentFee: paymentFee.toFixed(2),
      payoutFee: payoutFee.toFixed(2),
      payoutProcessingPercentage: commissionData.fees.payout_processing_percentage,
      netEarnings: netEarnings.toFixed(2)
    };
  };

  const exampleCalculation = calculateExample();

  // Show verification form if not verified
  if (!isVerified) {
    return (
      <>
        <Helmet>
          <title>Commission Policy | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <div className="min-h-screen flex flex-col bg-gradient-to-br from-green-50 via-white to-blue-50">
          <Navbar />
          <main className="flex-grow pt-24 pb-16 px-4 flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-md w-full"
            >
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl mb-4">
                    <Calculator className="w-8 h-8 text-white" />
                  </div>
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">
                    Commission Policy Access
                  </h1>
                  <p className="text-gray-600">
                    Enter your seller application tracking code to view our commission rates and fee structure.
                  </p>
                </div>

                <form onSubmit={handleVerifySubmit} className="space-y-4">
                  <div>
                    <label htmlFor="trackingCode" className="block text-sm font-semibold text-gray-700 mb-2">
                      Tracking Code
                    </label>
                    <input
                      id="trackingCode"
                      type="text"
                      value={trackingCode}
                      onChange={(e) => setTrackingCode(e.target.value.toUpperCase())}
                      placeholder="Enter your tracking code"
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-green-600 focus:ring-2 focus:ring-green-200 outline-none transition-all uppercase font-mono text-center text-lg tracking-wider"
                      maxLength={12}
                      required
                    />
                    {verificationError && (
                      <div className="mt-2 flex items-start gap-2 text-red-600 text-sm">
                        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{verificationError}</span>
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={verifying || !trackingCode.trim()}
                    className="w-full py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white font-bold rounded-xl hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                  >
                    {verifying ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      'View Commission Policy'
                    )}
                  </button>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-start gap-3 text-sm text-gray-600">
                    <Info className="w-5 h-5 flex-shrink-0 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-semibold text-gray-900 mb-1">Don&apos;t have a tracking code?</p>
                      <p className="mb-2">
                        You receive a tracking code when you submit a seller application. 
                      </p>
                      <a
                        href="/el-mercado/become-a-seller"
                        className="text-green-600 hover:text-green-700 font-semibold hover:underline"
                      >
                        Apply to become a seller →
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </main>
          <Footer />
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <Helmet>
          <title>Commission Policy | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <div className="min-h-screen flex flex-col bg-gradient-to-br from-green-50 via-white to-blue-50">
          <Navbar />
          <main className="flex-grow pt-24 pb-16 px-4 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading commission rates...</p>
            </div>
          </main>
          <Footer />
        </div>
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>Commission Policy | El Mercado - BIO-CHEM KNUST</title>
        <meta name="description" content="Understand the commission structure and fees for selling on El Mercado marketplace." />
      </Helmet>

      <div className="min-h-screen flex flex-col bg-gradient-to-br from-green-50 via-white to-blue-50">
        <Navbar />

        <main className="flex-grow pt-24 pb-16 px-4">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl mb-6">
                <Calculator className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Commission Policy
              </h1>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Transparent, fair pricing for sellers on El Mercado
              </p>
              <div className="mt-6 text-sm text-gray-500">
                Last Updated: January 15, 2026
              </div>
            </motion.div>

            {/* Overview */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl shadow-xl p-8 mb-12"
            >
              <h2 className="text-2xl font-bold text-gray-900 mb-4">How El Mercado Pricing Works</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                El Mercado operates on a transparent commission-based model. We only earn when you make a sale, 
                ensuring our success is directly tied to yours. There are no listing fees, monthly subscriptions, 
                or hidden charges.
              </p>
              <p className="text-gray-700 leading-relaxed">
                Our commission rates are competitively set to support the growth of the KNUST community and 
                maintain a high-quality marketplace platform with features like secure payments, dispute resolution, 
                seller analytics, and customer support.
              </p>
            </motion.div>

            {/* Commission Tiers */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-12"
            >
              <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
                Commission Rates by Category
              </h2>
              <div className="grid md:grid-cols-2 gap-6">
                {commissionTiers.map((tier, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all"
                  >
                    <div className={`bg-gradient-to-r ${tier.color} p-6 text-white`}>
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                          {tier.icon}
                        </div>
                        <div className="text-3xl font-bold">{tier.rate}</div>
                      </div>
                      <h3 className="text-2xl font-bold mb-2">{tier.type}</h3>
                      <p className="text-white/90">{tier.description}</p>
                    </div>
                    <div className="p-6">
                      <p className="text-sm font-semibold text-gray-600 mb-3">Examples:</p>
                      <div className="flex flex-wrap gap-2">
                        {tier.examples.map((example, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                          >
                            {example}
                          </span>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Additional Fees */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-2xl shadow-xl p-8 mb-12"
            >
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Additional Fees</h2>
              <div className="space-y-4">
                {additionalFees.map((fee, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-4 p-5 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                      {fee.icon}
                    </div>
                    <div className="flex-grow">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold text-gray-900">{fee.name}</h3>
                        <span className="font-bold text-blue-600">{fee.rate}</span>
                      </div>
                      <p className="text-gray-600 text-sm">{fee.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Example Calculation */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl shadow-xl p-8 mb-12 text-white"
            >
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <Calculator className="w-8 h-8" />
                Example Calculation
              </h2>
              <p className="text-purple-100 mb-8">
                Let&apos;s say you sell a standard product for GHS {exampleCalculation.salePrice}:
              </p>

              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-white/20">
                  <span className="text-lg">Sale Price</span>
                  <span className="text-2xl font-bold">GHS {exampleCalculation.salePrice.toFixed(2)}</span>
                </div>
                
                <div className="flex items-center justify-between text-purple-100">
                  <span>Platform Commission ({commissionData?.default_rate ?? 10}%)</span>
                  <span className="font-semibold">- GHS {exampleCalculation.commission}</span>
                </div>
                
                <div className="flex items-center justify-between text-purple-100">
                  <span>Payment Processing Fee ({commissionData?.fees?.payment_processing_percentage ?? 2.5}% + GHS {commissionData?.fees?.payment_processing_fixed?.toFixed(2) ?? '1.00'})</span>
                  <span className="font-semibold">- GHS {exampleCalculation.paymentFee}</span>
                </div>
                
                <div className="flex items-center justify-between text-purple-100">
                  <span>Payout Processing Fee ({exampleCalculation.payoutProcessingPercentage ?? 1}%)</span>
                  <span className="font-semibold">- GHS {exampleCalculation.payoutFee}</span>
                </div>
                
                <div className="flex items-center justify-between pt-4 border-t border-white/20">
                  <span className="text-xl font-bold">Your Net Earnings</span>
                  <span className="text-3xl font-bold text-green-300">GHS {exampleCalculation.netEarnings}</span>
                </div>
              </div>

              <div className="mt-6 bg-white/10 backdrop-blur-sm rounded-xl p-5 flex items-start gap-3">
                <Info className="w-6 h-6 flex-shrink-0 mt-0.5" />
                <p className="text-purple-100 text-sm leading-relaxed">
                  This means you keep {((exampleCalculation.netEarnings / exampleCalculation.salePrice) * 100).toFixed(1)}% 
                  of your sale price. The fees cover platform maintenance, payment security, customer support, and 
                  continuous feature improvements.
                </p>
              </div>
            </motion.div>

            {/* Payout Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="bg-white rounded-2xl shadow-xl p-8 mb-12"
            >
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <Clock className="w-7 h-7 text-green-600" />
                Payout Schedule &amp; Requirements
              </h2>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-bold text-gray-900 text-lg">Payment Terms</h3>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Funds are held in escrow until order is confirmed delivered</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Released to your wallet 2-3 days after delivery confirmation</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Minimum payout amount: GHS 50.00</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Payouts processed within 24-48 hours of request</span>
                    </li>
                  </ul>
                </div>

                <div className="space-y-4">
                  <h3 className="font-bold text-gray-900 text-lg">Payout Methods</h3>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Bank transfer (All Ghanaian banks supported)</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>MTN Mobile Money</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Vodafone Cash</span>
                    </li>
                    <li className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>AirtelTigo Money</span>
                    </li>
                  </ul>
                </div>
              </div>
            </motion.div>

            {/* Volume Discounts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
              className="bg-gradient-to-r from-orange-50 to-yellow-50 border-2 border-orange-200 rounded-2xl p-8 mb-12"
            >
              <div className="flex items-start gap-4">
                <TrendingUp className="w-8 h-8 text-orange-600 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    High-Volume Seller Benefits
                  </h2>
                  <p className="text-gray-700 mb-4 leading-relaxed">
                    Sellers who consistently achieve high sales volumes may qualify for reduced commission rates 
                    and additional benefits:
                  </p>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-orange-600" />
                      <span><strong>GHS 10,000+/month:</strong> 1% commission reduction</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-orange-600" />
                      <span><strong>GHS 25,000+/month:</strong> 2% commission reduction + priority support</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-orange-600" />
                      <span><strong>GHS 50,000+/month:</strong> 3% commission reduction + featured placement</span>
                    </li>
                  </ul>
                  <p className="text-sm text-gray-600 mt-4">
                    *Volume benefits are reviewed quarterly and applied automatically to qualifying sellers.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Important Notes */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6"
            >
              <div className="flex items-start gap-4">
                <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-blue-900 mb-3">Important Notes</h3>
                  <ul className="space-y-2 text-blue-800 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="font-bold mt-0.5">•</span>
                      <span>All prices and fees are in Ghana Cedis (GHS)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold mt-0.5">•</span>
                      <span>Commission rates are subject to change with 30 days notice</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold mt-0.5">•</span>
                      <span>Sellers are responsible for any applicable taxes on their earnings</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold mt-0.5">•</span>
                      <span>Refunded orders have commission and fees returned to your balance</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold mt-0.5">•</span>
                      <span>Disputed transactions may have funds held until resolution</span>
                    </li>
                  </ul>
                </div>
              </div>
            </motion.div>

            {/* Contact */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
              className="text-center mt-12 p-8 bg-white rounded-2xl shadow-lg"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-3">Questions About Our Commission Policy?</h3>
              <p className="text-gray-600 mb-6">
                Our team is here to help clarify any questions about pricing and payouts.
              </p>
              <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-blue-600" />
                  <span>Email: info@biochemknust.com</span>
                </div>
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-blue-600" />
                  <span>Seller Support: Available 24/7 in your dashboard</span>
                </div>
              </div>
            </motion.div>

            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="flex flex-col sm:flex-row gap-4 justify-center mt-12"
            >
              <a
                href="/el-mercado/become-a-seller"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-xl font-bold hover:from-green-700 hover:to-blue-700 transition-all hover:shadow-xl transform hover:-translate-y-1"
              >
                Apply to Become a Seller
              </a>
              <a
                href="/el_mercado/seller-terms"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white border-2 border-green-600 text-green-600 rounded-xl font-bold hover:bg-green-50 transition-all"
              >
                View Terms &amp; Conditions
              </a>
            </motion.div>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default CommissionPolicy;
