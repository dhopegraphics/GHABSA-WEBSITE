import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  Loader,
  Copy,
  Package,
  ShoppingBag,
  Heart,
  Vote,
  Users,
  Wallet,
  Store,
  RefreshCw,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowRight,
  Ticket,
  Calendar,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { useCart } from "../Context/CartContext";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";

/**
 * Universal Payment Callback - Handles ALL payment types
 * 
 * Payment Types & Prefixes:
 * 
 * Cart Checkout (all use unified_checkout_status endpoint):
 * - ELM-*     → El Mercado only cart purchases
 * - TXN-*     → Merchandise only cart purchases (detected as 'merchandise' type)
 * - UNIFIED-* → Mixed cart (El Mercado + Merchandise)
 * 
 * Other Payments:
 * - TXN-*     → Direct merchandise purchases (non-cart)
 * - DON-*     → Donations
 * - WAL-*     → Wallet Top-ups
 * - VOTE-*    → Voting
 * - MENT-*    → Mentorship sessions
 * - EVTPAY-*  → Event registration payments
 */

// Payment type detection based on reference prefix
const detectPaymentType = (reference) => {
  if (!reference) return "unknown";

  const ref = reference.toUpperCase();

  if (ref.startsWith("UNIFIED-")) return "unified_checkout";
  if (ref.startsWith("ELM-")) return "el_mercado";
  if (ref.startsWith("DON-")) return "donation";
  if (ref.startsWith("WAL-")) return "wallet";
  if (ref.startsWith("VOTE-")) return "voting";
  if (ref.startsWith("MENT-")) return "mentorship";
  if (ref.startsWith("TXN-")) return "merchandise";
  if (ref.startsWith("EVTPAY-")) return "event_registration";

  return "unknown";
};

// Get the appropriate verify endpoint for each payment type
const getVerifyEndpoint = (paymentType) => {
  switch (paymentType) {
    case "unified_checkout":
    case "el_mercado":
      // Both unified and el_mercado go through unified checkout status
      // El Mercado purchases from cart use ELM-* prefix but still need unified checkout processing
      return `${BACKEND_HOST}/payments/api/transactions/unified_checkout_status/`;
    case "donation":
      return `${BACKEND_HOST}/donations/verify/`;
    case "wallet":
      return `${BACKEND_HOST}/payments/wallet/verify/`;
    case "voting":
      return `${BACKEND_HOST}/voting/payments/verify/`;
    case "mentorship":
      return `${BACKEND_HOST}/mentorship/payments/verify/`;
    case "merchandise":
      return `${BACKEND_HOST}/products/payments/verify/`;
    case "event_registration":
      return `${BACKEND_HOST}/events/payments/verify/`;
    default:
      return `${BACKEND_HOST}/payments/transactions/verify_payment/`;
  }
};

// Payment type configurations with colors and icons
const paymentTypeConfig = {
  unified_checkout: {
    icon: Sparkles,
    title: "Mixed Cart Purchase",
    successTitle: "Purchase Complete!",
    successMessage: "Your merchandise and marketplace items have been confirmed.",
    color: "from-violet-500 to-purple-600",
    iconBg: "bg-violet-100",
    iconColor: "text-violet-600",
    redirectPath: "/cart",
    redirectLabel: "Continue Shopping",
    secondaryPath: "/dashboard/purchases",
    secondaryLabel: "View Purchases",
  },
  el_mercado: {
    icon: Store,
    title: "Marketplace Purchase",
    successTitle: "Order Confirmed!",
    successMessage: "Your El Mercado order has been placed successfully.",
    color: "from-orange-500 to-amber-600",
    iconBg: "bg-orange-100",
    iconColor: "text-orange-600",
    redirectPath: "/el-mercado",
    redirectLabel: "Continue Shopping",
    secondaryPath: "/dashboard/orders",
    secondaryLabel: "View Orders",
  },
  merchandise: {
    icon: ShoppingBag,
    title: "Merchandise Purchase",
    successTitle: "Payment Successful!",
    successMessage: "Your merchandise purchase has been confirmed.",
    color: "from-green-500 to-emerald-600",
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    redirectPath: "/purchase-merchandise",
    redirectLabel: "Continue Shopping",
    secondaryPath: "/dashboard/purchases",
    secondaryLabel: "View Purchases",
  },
  donation: {
    icon: Heart,
    title: "Donation",
    successTitle: "Thank You for Your Donation!",
    successMessage: "Your generous contribution has been received.",
    color: "from-pink-500 to-rose-600",
    iconBg: "bg-pink-100",
    iconColor: "text-pink-600",
    redirectPath: "/donations",
    redirectLabel: "Make Another Donation",
    secondaryPath: "/dashboard",
    secondaryLabel: "Go to Dashboard",
  },
  wallet: {
    icon: Wallet,
    title: "Wallet Top-up",
    successTitle: "Wallet Topped Up!",
    successMessage: "Your wallet has been credited successfully.",
    color: "from-purple-500 to-indigo-600",
    iconBg: "bg-purple-100",
    iconColor: "text-purple-600",
    redirectPath: "/dashboard/wallet",
    redirectLabel: "View Wallet",
    secondaryPath: "/dashboard",
    secondaryLabel: "Go to Dashboard",
  },
  voting: {
    icon: Vote,
    title: "Voting Payment",
    successTitle: "Vote Payment Successful!",
    successMessage: "Your voting credits have been added.",
    color: "from-blue-500 to-cyan-600",
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    redirectPath: "/voting",
    redirectLabel: "Continue Voting",
    secondaryPath: "/dashboard",
    secondaryLabel: "Go to Dashboard",
  },
  mentorship: {
    icon: Users,
    title: "Mentorship Payment",
    successTitle: "Mentorship Session Booked!",
    successMessage: "Your mentorship session has been confirmed.",
    color: "from-teal-500 to-emerald-600",
    iconBg: "bg-teal-100",
    iconColor: "text-teal-600",
    redirectPath: "/mentorship",
    redirectLabel: "View Sessions",
    secondaryPath: "/dashboard",
    secondaryLabel: "Go to Dashboard",
  },
  event_registration: {
    icon: Ticket,
    title: "Event Registration",
    successTitle: "Registration Confirmed!",
    successMessage: "Your event registration has been confirmed. See you there!",
    color: "from-indigo-500 to-blue-600",
    iconBg: "bg-indigo-100",
    iconColor: "text-indigo-600",
    redirectPath: "/events",
    redirectLabel: "Browse Events",
    secondaryPath: "/dashboard/event-registrations",
    secondaryLabel: "My Registrations",
  },
  unknown: {
    icon: Package,
    title: "Payment",
    successTitle: "Payment Successful!",
    successMessage: "Your payment has been confirmed.",
    color: "from-gray-500 to-slate-600",
    iconBg: "bg-gray-100",
    iconColor: "text-gray-600",
    redirectPath: "/",
    redirectLabel: "Go Home",
    secondaryPath: "/dashboard",
    secondaryLabel: "Go to Dashboard",
  },
};

export function UniversalPaymentCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const axiosInstance = useAxiosWithRefresh();
  const { clearCart } = useCart();

  const [loading, setLoading] = useState(true);
  const [paymentData, setPaymentData] = useState(null);
  const [error, setError] = useState(null);
  const [copiedCode, setCopiedCode] = useState(null);
  const [paymentType, setPaymentType] = useState("unknown");
  const [retryCount, setRetryCount] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [expandedOrders, setExpandedOrders] = useState({}); // Track which orders are expanded
  const maxRetries = 5;
  const retryTimeoutRef = useRef(null);

  // Paystack returns reference as 'trxref' or 'reference'
  const reference = searchParams.get("reference") || searchParams.get("trxref");
  // Optional: payment type can be passed as query param for explicit handling
  const explicitType = searchParams.get("type");

  const verifyPayment = useCallback(async (isRetry = false, forceRecheck = false) => {
    if (!reference) {
      setError("No payment reference found. Payment may not have completed.");
      setLoading(false);
      return;
    }

    // Detect payment type
    const detectedType = explicitType || detectPaymentType(reference);
    setPaymentType(detectedType);

    try {
      if (isRetry) {
        setRetrying(true);
        setStatusMessage(`Checking payment status (attempt ${retryCount + 1}/${maxRetries})...`);
      } else {
        setLoading(true);
        setStatusMessage("Verifying payment with server...");
      }

      const verifyUrl = getVerifyEndpoint(detectedType);

      // Different endpoints expect different request formats
      let response;
      if (detectedType === "donation") {
        // Donation verify is a GET request with reference in URL
        response = await axiosInstance.get(`${verifyUrl}${reference}/`);
      } else {
        // Others are POST with reference in body
        response = await axiosInstance.post(verifyUrl, {
          reference: reference,
          force_recheck: forceRecheck,
        }, {
          timeout: 30000,
        });
      }

      if (response.data.success) {
        const data = response.data;

        // Check for pending completion (validation codes not yet created)
        const hasValidationCodes = data.validation_code ||
          (data.validation_codes && data.validation_codes.length > 0) ||
          (data.merchandise_results && data.merchandise_results.length > 0) ||
          (data.el_mercado_results && data.el_mercado_results.length > 0);

        const isPendingCompletion = data.pending_completion ||
          (data.transaction?.status === "success" && !hasValidationCodes);

        if (isPendingCompletion && retryCount < maxRetries) {
          const delay = Math.min(3000 * Math.pow(1.3, retryCount), 10000);
          console.log(`Payment pending completion, retrying in ${delay}ms (attempt ${retryCount + 1}/${maxRetries})`);
          setStatusMessage(`Payment received! Creating your order (attempt ${retryCount + 1}/${maxRetries})...`);

          retryTimeoutRef.current = setTimeout(() => {
            setRetryCount((prev) => prev + 1);
            verifyPayment(true, true);
          }, delay);
          return;
        }

        setPaymentData(data);
        setError(null);
        setStatusMessage("");

        // Clear cart after successful payment
        const status = data.transaction?.status || data.status;
        if (status === "success" || status === "completed" || status === "verified") {
          if (["merchandise", "unified_checkout", "el_mercado"].includes(detectedType)) {
            clearCart();
            localStorage.removeItem("pending_cart_checkout");
          }
        }
      } else {
        // Retry if non-success response
        if (retryCount < maxRetries) {
          const delay = Math.min(3000 * Math.pow(1.3, retryCount), 10000);
          console.log(`Verification returned non-success, retrying in ${delay}ms`);
          setStatusMessage(`Verifying payment with Paystack (attempt ${retryCount + 1}/${maxRetries})...`);

          retryTimeoutRef.current = setTimeout(() => {
            setRetryCount((prev) => prev + 1);
            verifyPayment(true, true);
          }, delay);
          return;
        }
        setError(response.data.error || "Payment verification failed");
        setStatusMessage("");
      }
    } catch (err) {
      console.error("Verification error:", err);

      // Auto-retry on network errors or 5xx errors
      const isRetryableError = !err.response ||
        (err.response.status >= 500 && err.response.status < 600) ||
        err.code === "ECONNABORTED" ||
        err.code === "ERR_NETWORK";

      if (isRetryableError && retryCount < maxRetries) {
        const delay = Math.min(3000 * Math.pow(1.3, retryCount), 10000);
        console.log(`Network/server error, retrying in ${delay}ms`);
        setStatusMessage(`Connection issue, retrying (attempt ${retryCount + 1}/${maxRetries})...`);

        retryTimeoutRef.current = setTimeout(() => {
          setRetryCount((prev) => prev + 1);
          verifyPayment(true, true);
        }, delay);
        return;
      }

      setError(
        err.response?.data?.error ||
          err.response?.data?.details ||
          err.message ||
          "Failed to verify payment"
      );
      setStatusMessage("");
    } finally {
      setLoading(false);
      setRetrying(false);
    }
  }, [reference, explicitType, axiosInstance, clearCart, retryCount]);

  // Manual retry handler
  const handleManualRetry = () => {
    setError(null);
    setRetryCount(0);
    setStatusMessage("Re-verifying payment...");
    verifyPayment(false, true);
  };

  useEffect(() => {
    // Small initial delay to allow webhook to potentially complete first
    const initialDelay = setTimeout(() => {
      verifyPayment(false, false);
    }, 1000);

    return () => {
      clearTimeout(initialDelay);
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reference]);

  const copyValidationCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  // Get config for current payment type (dynamic for cart checkouts)
  const getEffectiveConfig = () => {
    const baseConfig = paymentTypeConfig[paymentType] || paymentTypeConfig.unknown;
    
    // For cart checkout purchases, dynamically determine display based on what was actually purchased
    // This handles ELM-* (el_mercado_only), TXN-* (merchandise_only via cart), and UNIFIED-* (mixed)
    if ((paymentType === "unified_checkout" || paymentType === "el_mercado" || paymentType === "merchandise") && paymentData) {
      const merchandiseResults = paymentData.merchandise_results || [];
      const elMercadoResults = paymentData.el_mercado_results || [];
      
      const hasMerchandise = merchandiseResults.length > 0;
      const hasElMercado = elMercadoResults.length > 0;
      
      // Only El Mercado items - show El Mercado-style config
      if (hasElMercado && !hasMerchandise) {
        return {
          ...paymentTypeConfig.el_mercado,
          title: "Marketplace Purchase",
          successTitle: "Order Confirmed!",
          successMessage: "Your El Mercado marketplace order has been placed successfully.",
        };
      }
      
      // Only Merchandise items - show Merchandise-style config
      if (hasMerchandise && !hasElMercado) {
        return {
          ...paymentTypeConfig.merchandise,
          title: "Merchandise Purchase",
          successTitle: "Payment Successful!",
          successMessage: "Your merchandise purchase has been confirmed.",
        };
      }
      
      // Mixed - use unified config
      if (hasMerchandise && hasElMercado) {
        return paymentTypeConfig.unified_checkout;
      }
    }
    
    return baseConfig;
  };

  const config = getEffectiveConfig();

  // Extract status and details based on payment type
  const getPaymentStatus = () => {
    if (!paymentData) return null;

    // Base status extraction
    const baseStatus = {
      isSuccess:
        paymentData.transaction?.status === "success" ||
        paymentData.status === "success" ||
        paymentData.status === "completed" ||
        paymentData.status === "verified",
      reference: paymentData.transaction?.reference || paymentData.reference || reference,
      amount: paymentData.transaction?.amount || paymentData.amount,
      status: paymentData.transaction?.status || paymentData.status,
      completedAt: paymentData.transaction?.completed_at || paymentData.completed_at,
    };

    // Donation-specific
    if (paymentType === "donation") {
      return {
        ...baseStatus,
        isSuccess: paymentData.donation?.status === "completed" || paymentData.status === "completed",
        reference: paymentData.donation?.reference || paymentData.reference,
        amount: paymentData.donation?.amount || paymentData.amount,
        status: paymentData.donation?.status || paymentData.status,
        completedAt: paymentData.donation?.completed_at || paymentData.completed_at,
        donorName: paymentData.donation?.donor_name || paymentData.donor_name,
        message: paymentData.donation?.message || paymentData.message,
      };
    }

    // Unified checkout (mixed Merchandise + El Mercado)
    if (paymentType === "unified_checkout") {
      const unifiedStatus = {
        ...baseStatus,
        merchandiseResults: paymentData.merchandise_results || [],
        elMercadoResults: paymentData.el_mercado_results || [],
        validationCodes: paymentData.validation_codes || [],
        totalItems: paymentData.total_items || 0,
      };
      
      // Debug logging
      console.log('Unified Checkout Status:', {
        validationCodes: unifiedStatus.validationCodes,
        merchandiseResults: unifiedStatus.merchandiseResults,
        elMercadoResults: unifiedStatus.elMercadoResults,
        rawPaymentData: paymentData
      });
      
      return unifiedStatus;
    }

    // El Mercado specific (ELM-* prefix goes through unified checkout endpoint)
    if (paymentType === "el_mercado") {
      // Data comes from unified_checkout_status endpoint as el_mercado_results array
      const elMercadoResults = paymentData.el_mercado_results || [];
      const firstOrder = elMercadoResults[0] || {};
      
      // Debug logging
      console.log('El Mercado Payment Status:', {
        elMercadoResultsCount: elMercadoResults.length,
        elMercadoResults: elMercadoResults,
        firstOrder: firstOrder,
        rawPaymentData: paymentData
      });
      
      return {
        ...baseStatus,
        // For backward compatibility with single order display
        orderNumber: firstOrder.order_number,
        sellerName: firstOrder.seller_name,
        items: firstOrder.items || [],
        orderStatus: firstOrder.order_status,
        // Also include full results for multi-order display
        elMercadoResults: elMercadoResults,
        // Note: delivery_code is NOT available at purchase time
        // It's generated when the seller ships the order
      };
    }

    // Merchandise (products) specific
    if (paymentType === "merchandise") {
      const merchandiseStatus = {
        ...baseStatus,
        validationCodes: paymentData.validation_codes || [],
        validationCode: paymentData.validation_code,
        isCartCheckout: paymentData.is_cart_checkout,
        merchandiseCollected: paymentData.merchandise_collected,
        productDetails: paymentData.transaction?.product_details,
      };
      
      // Debug logging
      console.log('Merchandise Payment Status:', {
        validationCode: merchandiseStatus.validationCode,
        isCartCheckout: merchandiseStatus.isCartCheckout,
        validationCodesLength: merchandiseStatus.validationCodes?.length,
        merchandiseCollected: merchandiseStatus.merchandiseCollected,
        rawPaymentData: paymentData
      });
      
      return merchandiseStatus;
    }

    // Voting specific
    if (paymentType === "voting") {
      return {
        ...baseStatus,
        votes: paymentData.votes,
        eventName: paymentData.event_name,
      };
    }

    // Mentorship specific
    if (paymentType === "mentorship") {
      return {
        ...baseStatus,
        sessionDetails: paymentData.session_details,
      };
    }

    // Event registration specific
    if (paymentType === "event_registration") {
      return {
        ...baseStatus,
        isSuccess: paymentData.success || paymentData.status === "success",
        registrationNumber: paymentData.registration?.registration_number || paymentData.registration_number,
        eventName: paymentData.registration?.event_name || paymentData.event_name,
        eventId: paymentData.registration?.event || paymentData.event_id,
        packageName: paymentData.registration?.payment_info?.package_name || paymentData.package_name,
        amountPaid: paymentData.amount || paymentData.registration?.payment_info?.amount_paid,
        paymentStatus: paymentData.registration?.payment_info?.status || paymentData.payment_status,
        isFullyPaid: paymentData.registration?.payment_info?.is_fully_paid,
        balanceDue: paymentData.registration?.payment_info?.balance_due,
        registration: paymentData.registration,
      };
    }

    return baseStatus;
  };

  const paymentStatus = getPaymentStatus();

  // Render validation codes section for merchandise
  const renderMerchandiseValidationCodes = (codes, isCartCheckout = false) => {
    if (!codes || codes.length === 0) return null;

    return (
      <div className="mb-8">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <ShoppingBag className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">
                Merchandise Collection {isCartCheckout ? "Codes" : "Code"}
              </h3>
              <p className="text-sm text-gray-600">
                Present {isCartCheckout ? "these codes" : "this code"} to collect your items
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {codes.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white border border-blue-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Product name and validation code header */}
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{item.product_name}</p>
                    {/* Show recipient info for gift or on-behalf purchases */}
                    {(item.is_gift || item.is_on_behalf) && (item.recipient_name || item.recipient_phone) && (
                      <p className={`text-xs mt-0.5 flex items-center gap-1 ${item.is_gift ? 'text-purple-600' : 'text-blue-600'}`}>
                        {item.is_gift ? <Heart className="w-3 h-3" /> : <Users className="w-3 h-3" />}
                        {item.is_gift ? 'Gift for ' : 'Purchased for '}
                        {item.recipient_name || item.recipient_phone}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div className="text-xl font-mono font-bold text-blue-600 tracking-wider bg-blue-50 px-4 py-2 rounded-lg border-2 border-dashed border-blue-300">
                      {item.code}
                    </div>
                    <button
                      onClick={() => copyValidationCode(item.code)}
                      className="p-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm"
                      title="Copy code"
                    >
                      {copiedCode === item.code ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Variant details section */}
                {item.variant_selections && item.variant_selections.length > 0 && (
                  <div className="border-t border-blue-100 pt-3">
                    <p className="text-xs text-gray-500 mb-2 font-medium">Items to collect with this code:</p>
                    <div className="space-y-2">
                      {item.variant_selections.map((variant, vIndex) => (
                        <div 
                          key={vIndex} 
                          className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2"
                        >
                          <div className="flex items-center gap-2">
                            {variant.color && (
                              <span className="inline-flex items-center gap-1.5 text-sm">
                                <span 
                                  className="w-4 h-4 rounded-full border border-gray-300 shadow-sm"
                                  style={{ 
                                    backgroundColor: variant.color.toLowerCase() === 'white' ? '#ffffff' : 
                                                     variant.color.toLowerCase() === 'black' ? '#1f2937' :
                                                     variant.color.toLowerCase() === 'red' ? '#ef4444' :
                                                     variant.color.toLowerCase() === 'blue' ? '#3b82f6' :
                                                     variant.color.toLowerCase() === 'green' ? '#22c55e' :
                                                     variant.color.toLowerCase() === 'yellow' ? '#eab308' :
                                                     variant.color.toLowerCase() === 'purple' ? '#a855f7' :
                                                     variant.color.toLowerCase() === 'pink' ? '#ec4899' :
                                                     variant.color.toLowerCase() === 'orange' ? '#f97316' :
                                                     variant.color.toLowerCase() === 'gray' || variant.color.toLowerCase() === 'grey' ? '#6b7280' :
                                                     variant.color.toLowerCase() === 'royal blue' ? '#4169e1' :
                                                     variant.color.toLowerCase() === 'navy' ? '#1e3a5f' :
                                                     variant.color.toLowerCase()
                                  }}
                                />
                                <span className="capitalize font-medium text-gray-700">{variant.color}</span>
                              </span>
                            )}
                            {variant.size && (
                              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase">
                                {variant.size}
                              </span>
                            )}
                          </div>
                          <span className="text-sm text-gray-600">
                            Qty: <span className="font-semibold text-gray-900">{variant.quantity}</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Legacy quantity display if no variant_selections */}
                {(!item.variant_selections || item.variant_selections.length === 0) && item.quantity && (
                  <p className="text-sm text-gray-500 border-t border-blue-100 pt-2 mt-2">
                    Quantity: {item.quantity}
                  </p>
                )}

                <AnimatePresence>
                  {copiedCode === item.code && (
                    <motion.p
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="text-sm text-green-600 mt-2 text-right font-medium"
                    >
                      ✓ Copied to clipboard!
                    </motion.p>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800">
            <strong>Important:</strong> Save {isCartCheckout ? "these codes" : "this code"}! 
            You&apos;ll need {isCartCheckout ? "them" : "it"} to collect your merchandise. 
            You can always view {isCartCheckout ? "them" : "it"} in your{" "}
            <a href="/dashboard/purchases" className="text-amber-700 underline font-medium hover:text-amber-900">Purchases</a>.
          </p>
        </div>
      </div>
    );
  };

  // Toggle order expansion
  const toggleOrderExpanded = (orderKey) => {
    setExpandedOrders(prev => ({
      ...prev,
      [orderKey]: !prev[orderKey]
    }));
  };

  // Render El Mercado order section
  const renderElMercadoOrders = (orders) => {
    if (!orders || orders.length === 0) return null;

    return (
      <div className="mb-8">
        <div className="bg-gradient-to-br from-orange-50 to-amber-50 border-2 border-orange-200 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-orange-600 rounded-xl flex items-center justify-center">
              <Store className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">El Mercado Orders</h3>
              <p className="text-sm text-gray-600">
                Your marketplace orders have been placed
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {orders.map((order, index) => {
              const orderKey = order.order_number || `order-${index}`;
              const items = order.items || [];
              const itemCount = items.length || order.items_count || 0;
              const isSingleItem = itemCount === 1;
              const isExpanded = expandedOrders[orderKey] || isSingleItem;
              const firstItem = items[0];

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white border border-orange-200 rounded-xl p-4 shadow-sm"
                >
                  {/* Order Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900">
                        Order #{order.order_number}
                      </p>
                      <p className="text-sm text-gray-500">
                        Seller: {order.seller_name}
                      </p>
                    </div>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                      {order.order_status === 'PAID' ? 'Awaiting Shipment' : order.order_status || 'Confirmed'}
                    </span>
                  </div>

                  {/* Single Item - Show directly with full details */}
                  {isSingleItem && firstItem && (
                    <div className="p-4 bg-orange-50 rounded-lg mb-3">
                      <div className="flex items-start gap-4">
                        {firstItem.image ? (
                          <img 
                            src={firstItem.image} 
                            alt={firstItem.name}
                            className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                          />
                        ) : (
                          <div className="w-20 h-20 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Package className="w-10 h-10 text-orange-400" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-gray-900 text-lg">{firstItem.name}</p>
                          {firstItem.description && (
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{firstItem.description}</p>
                          )}
                          {firstItem.variant_name && (
                            <p className="text-sm text-orange-600 mt-1">Variant: {firstItem.variant_name}</p>
                          )}
                          <div className="flex items-center justify-between mt-3">
                            <p className="text-sm text-gray-600">
                              Qty: {firstItem.quantity} × GH₵{firstItem.unit_price}
                            </p>
                            <p className="font-bold text-orange-600 text-lg">
                              GH₵{firstItem.total_price}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Multiple Items - Show summary with expand button */}
                  {!isSingleItem && itemCount > 0 && (
                    <>
                      {/* Summary line with item names */}
                      <div className="mb-3">
                        <div 
                          className="flex items-center justify-between p-3 bg-orange-50 rounded-lg cursor-pointer hover:bg-orange-100 transition-colors"
                          onClick={() => toggleOrderExpanded(orderKey)}
                        >
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">
                              {itemCount} items purchased
                            </p>
                            <p className="text-sm text-gray-600 truncate">
                              {items.slice(0, 2).map(i => i.name).join(', ')}
                              {items.length > 2 && ` +${items.length - 2} more`}
                            </p>
                          </div>
                          <button className="p-2 text-orange-600 hover:bg-orange-200 rounded-lg transition-colors">
                            {isExpanded ? (
                              <ChevronUp className="w-5 h-5" />
                            ) : (
                              <ChevronDown className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Expandable items list */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="space-y-3 mb-3">
                              {items.map((item, itemIndex) => (
                                <div key={itemIndex} className="p-3 bg-gray-50 rounded-lg">
                                  <div className="flex items-start gap-3">
                                    {item.image ? (
                                      <img 
                                        src={item.image} 
                                        alt={item.name}
                                        className="w-14 h-14 object-cover rounded-lg flex-shrink-0"
                                      />
                                    ) : (
                                      <div className="w-14 h-14 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <Package className="w-7 h-7 text-orange-400" />
                                      </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                      <p className="font-semibold text-gray-900">{item.name}</p>
                                      {item.description && (
                                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{item.description}</p>
                                      )}
                                      {item.variant_name && (
                                        <p className="text-xs text-orange-600 mt-1">Variant: {item.variant_name}</p>
                                      )}
                                      <div className="flex items-center justify-between mt-2">
                                        <p className="text-sm text-gray-600">
                                          Qty: {item.quantity} × GH₵{item.unit_price}
                                        </p>
                                        <p className="font-semibold text-orange-600">
                                          GH₵{item.total_price}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </>
                  )}

                  {/* No items data - show count only */}
                  {itemCount === 0 && order.items_count > 0 && (
                    <div className="p-3 bg-orange-50 rounded-lg mb-3">
                      <p className="text-gray-700">
                        {order.items_count} item(s) in this order
                      </p>
                    </div>
                  )}

                  {/* Order Total */}
                  <div className="flex items-center justify-between pt-3 border-t border-orange-100">
                    <p className="text-sm text-gray-600">
                      {itemCount || order.items_count || 0} item(s)
                    </p>
                    <p className="font-bold text-gray-900">
                      Total: GH₵{order.total_amount || order.total}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <p className="mb-2">
              <strong>What happens next:</strong>
            </p>
            <ol className="list-decimal list-inside space-y-1">
              <li>The seller will review and prepare your order</li>
              <li>When shipped, you&apos;ll receive a <strong>delivery code</strong> via notification</li>
              <li>Use this code when you receive your order to confirm delivery</li>
            </ol>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-16 mt-[70px]">
        {/* Loading State */}
        {(loading || retrying) && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl shadow-xl p-12 text-center"
          >
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-25" />
              <div className="relative w-full h-full bg-blue-50 rounded-full flex items-center justify-center">
                <Loader className="w-10 h-10 text-blue-600 animate-spin" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {retrying ? "Confirming Payment..." : `Verifying ${config.title}`}
            </h2>
            <p className="text-gray-600 mb-4">
              {statusMessage || "Please wait while we confirm your payment..."}
            </p>
            {(retrying || retryCount > 0) && (
              <div className="mt-6">
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3 overflow-hidden">
                  <motion.div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min((retryCount + 1) / maxRetries * 100, 100)}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p className="text-sm text-gray-500 flex items-center justify-center gap-2">
                  <Clock className="w-4 h-4" />
                  This may take a few moments. Please don&apos;t close this page.
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* Error State */}
        {!loading && !retrying && error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl shadow-xl p-12 text-center"
          >
            <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-14 h-14 text-red-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Verification Issue
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <p className="text-sm text-gray-500 mb-8 max-w-md mx-auto">
              If you believe your payment was successful, try clicking &quot;Retry Verification&quot; below 
              or check your{" "}
              <a href="/dashboard/purchases" className="text-blue-600 underline hover:text-blue-800">Purchases</a>{" "}
              page.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleManualRetry}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25"
              >
                <RefreshCw className="w-5 h-5" />
                Retry Verification
              </button>
              <button
                onClick={() => navigate(config.redirectPath)}
                className="px-6 py-3 bg-gray-100 text-gray-900 rounded-xl hover:bg-gray-200 transition"
              >
                {config.redirectLabel}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-8">
              Reference: <span className="font-mono">{reference}</span>
            </p>
          </motion.div>
        )}

        {/* Success State */}
        {!loading && !retrying && !error && paymentStatus?.isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl shadow-xl overflow-hidden"
          >
            {/* Success Header */}
            <div className={`bg-gradient-to-r ${config.color} p-8 text-white text-center relative overflow-hidden`}>
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full -translate-x-1/2 -translate-y-1/2" />
                <div className="absolute bottom-0 right-0 w-60 h-60 bg-white rounded-full translate-x-1/3 translate-y-1/3" />
              </div>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
                className="relative w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg"
              >
                <CheckCircle className={`w-14 h-14 ${config.iconColor}`} />
              </motion.div>
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-3xl font-bold mb-2 relative"
              >
                {config.successTitle}
              </motion.h2>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-white/90 relative"
              >
                {config.successMessage}
              </motion.p>
            </div>

            {/* Payment Details */}
            <div className="p-8">
              {/* === UNIFIED CHECKOUT (Mixed Cart) === */}
              {paymentType === "unified_checkout" && (
                <>
                  {/* Merchandise validation codes from unified checkout */}
                  {(() => {
                    // Try validation_codes first (already includes variant_selections from backend)
                    let merchCodes = paymentStatus.validationCodes
                      ?.filter(vc => vc.source === 'merchandise')
                      .map(r => ({
                        product_name: r.product_name,
                        quantity: r.quantity,
                        code: r.code,
                        variant_selections: r.variant_selections || [],
                        recipient_phone: r.recipient_phone,
                        is_gift: r.is_gift,
                        is_on_behalf: r.is_on_behalf,
                        recipient_name: r.recipient_name,
                      })) || [];
                    
                    // Fallback to merchandiseResults if no validation_codes
                    if (merchCodes.length === 0) {
                      merchCodes = paymentStatus.merchandiseResults
                        ?.filter(r => r.validation_code && r.status === 'success')
                        .map(r => ({
                          product_name: r.product_name,
                          quantity: r.quantity,
                          code: r.validation_code,
                          variant_selections: r.variant_selections || [],
                          recipient_phone: r.recipient_phone,
                          is_gift: r.is_gift,
                          is_on_behalf: r.is_on_behalf,
                          recipient_name: r.recipient_name
                        })) || [];
                    }
                    
                    if (merchCodes.length > 0) {
                      return renderMerchandiseValidationCodes(merchCodes, true);
                    }
                    return null;
                  })()}
                  
                  {paymentStatus.elMercadoResults?.length > 0 && 
                    renderElMercadoOrders(paymentStatus.elMercadoResults)
                  }

                  {/* Quick Navigation Cards */}
                  <div className="mt-8">
                    <p className="text-sm text-gray-500 text-center mb-4">Track your purchases</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Merchandise Purchases */}
                      {paymentStatus.merchandiseResults?.length > 0 && (
                        <motion.button
                          whileHover={{ scale: 1.02, y: -2 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigate('/dashboard/purchases')}
                          className="group relative overflow-hidden bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-5 text-left shadow-lg hover:shadow-xl transition-all duration-300"
                        >
                          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/10 rounded-full blur-2xl" />
                          <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-2">
                              <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                                <ShoppingBag className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="font-bold text-white">My Purchases</p>
                                <p className="text-xs text-green-100">
                                  {paymentStatus.merchandiseResults.length} item(s) added
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-white/80 text-sm mt-3">
                              <span>View collection codes</span>
                              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </div>
                          </div>
                        </motion.button>
                      )}

                      {/* El Mercado Orders */}
                      {paymentStatus.elMercadoResults?.length > 0 && (
                        <motion.button
                          whileHover={{ scale: 1.02, y: -2 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigate('/dashboard/orders')}
                          className="group relative overflow-hidden bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl p-5 text-left shadow-lg hover:shadow-xl transition-all duration-300"
                        >
                          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/10 rounded-full blur-2xl" />
                          <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-2">
                              <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                                <Store className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="font-bold text-white">My Orders</p>
                                <p className="text-xs text-orange-100">
                                  {paymentStatus.elMercadoResults.length} order(s) placed
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-white/80 text-sm mt-3">
                              <span>Track delivery status</span>
                              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </div>
                          </div>
                        </motion.button>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* === MERCHANDISE (Products) === */}
              {paymentType === "merchandise" && (
                <>
                  {/* Cart Checkout - Multiple items */}
                  {paymentStatus.isCartCheckout && paymentStatus.validationCodes?.length > 0 &&
                    renderMerchandiseValidationCodes(paymentStatus.validationCodes, true)
                  }

                  {/* Single Item Checkout */}
                  {!paymentStatus.isCartCheckout && (
                    <>
                      {paymentStatus.productDetails && (
                        <div className="mb-8 p-5 bg-gray-50 rounded-xl">
                          <div className="flex items-start gap-4">
                            {paymentStatus.productDetails.product_image && (
                              <img
                                src={paymentStatus.productDetails.product_image}
                                alt={paymentStatus.productDetails.product_name}
                                className="w-24 h-24 object-cover rounded-xl shadow-sm"
                              />
                            )}
                            <div className="flex-1">
                              <h3 className="font-bold text-lg text-gray-900">
                                {paymentStatus.productDetails.product_name}
                              </h3>
                              <p className="text-sm text-gray-600 capitalize">
                                {paymentStatus.productDetails.product_type}
                              </p>
                              <p className="text-xl font-bold text-blue-600 mt-2">
                                GH₵{paymentStatus.amount}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Show validation code if exists and not collected */}
                      {paymentStatus.validationCode && (
                        paymentStatus.merchandiseCollected ? (
                          <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-xl">
                            <p className="text-green-800 flex items-center gap-2">
                              <CheckCircle className="w-5 h-5" />
                              Merchandise has been collected
                            </p>
                          </div>
                        ) : (
                          // Use validationCodes array if available (has variant_selections), otherwise build manually
                          renderMerchandiseValidationCodes(
                            paymentStatus.validationCodes?.length > 0 
                              ? paymentStatus.validationCodes 
                              : [{
                                  product_name: paymentStatus.productDetails?.product_name || "Your Item",
                                  quantity: 1,
                                  code: paymentStatus.validationCode,
                                  variant_selections: [],
                                }],
                            false
                          )
                        )
                      )}
                    </>
                  )}
                </>
              )}

              {/* === EL MERCADO === */}
              {paymentType === "el_mercado" && (
                <>
                  {/* Use shared renderer for all El Mercado orders */}
                  {paymentStatus.elMercadoResults?.length > 0 && 
                    renderElMercadoOrders(paymentStatus.elMercadoResults)
                  }

                  {/* Fallback: Show basic info if elMercadoResults is empty but we have order data */}
                  {(!paymentStatus.elMercadoResults || paymentStatus.elMercadoResults.length === 0) && 
                   paymentStatus.orderNumber && (
                    <div className="mb-8">
                      <div className="bg-gradient-to-br from-orange-50 to-amber-50 border-2 border-orange-200 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 bg-orange-600 rounded-xl flex items-center justify-center">
                            <Store className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <h3 className="font-bold text-gray-900">Order Placed</h3>
                            <p className="text-sm text-gray-600">
                              Order #{paymentStatus.orderNumber}
                            </p>
                          </div>
                        </div>

                        <div className="bg-white rounded-xl p-4 mb-4">
                          <p className="text-sm text-gray-600 mb-1">Seller</p>
                          <p className="font-semibold text-gray-900">{paymentStatus.sellerName}</p>
                        </div>
                        
                        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
                          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                          <div className="text-sm text-amber-800">
                            <p className="mb-2">
                              <strong>What happens next:</strong>
                            </p>
                            <ol className="list-decimal list-inside space-y-1">
                              <li>The seller will review and prepare your order</li>
                              <li>When shipped, you&apos;ll receive a <strong>delivery code</strong></li>
                              <li>Use this code when you receive your order</li>
                            </ol>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Track Order Button */}
                  <motion.button
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/dashboard/orders')}
                    className="group w-full mt-6 relative overflow-hidden bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl p-5 text-left shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-white/10 rounded-full blur-2xl" />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                        <ArrowRight className="w-6 h-6 text-white group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                    <div className="relative z-10 pr-16">
                      <div className="flex items-center gap-3 mb-1">
                        <Store className="w-5 h-5 text-white" />
                        <p className="font-bold text-white text-lg">Track My Orders</p>
                      </div>
                      <p className="text-orange-100 text-sm">
                        View order status, get delivery codes & confirm deliveries
                      </p>
                    </div>
                  </motion.button>
                </>
              )}

              {/* === DONATION === */}
              {paymentType === "donation" && (
                <div className="mb-8 p-6 bg-gradient-to-br from-pink-50 to-rose-50 border border-pink-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-pink-600 rounded-xl flex items-center justify-center">
                      <Heart className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-bold text-gray-900">Donation Received</h3>
                  </div>
                  {paymentStatus.donorName && (
                    <p className="text-gray-700 text-lg">
                      Thank you, <strong>{paymentStatus.donorName}</strong>!
                    </p>
                  )}
                  {paymentStatus.message && (
                    <p className="text-gray-600 mt-3 italic bg-white p-3 rounded-lg">
                      &ldquo;{paymentStatus.message}&rdquo;
                    </p>
                  )}
                </div>
              )}

              {/* === VOTING === */}
              {paymentType === "voting" && paymentStatus.votes && (
                <div className="mb-8 p-6 bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                      <Vote className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-bold text-gray-900">Voting Credits Added</h3>
                  </div>
                  <p className="text-gray-700 text-lg">
                    You have received <strong className="text-blue-600">{paymentStatus.votes} votes</strong>
                    {paymentStatus.eventName && (
                      <> for <strong>{paymentStatus.eventName}</strong></>
                    )}.
                  </p>
                </div>
              )}

              {/* === MENTORSHIP === */}
              {paymentType === "mentorship" && paymentStatus.sessionDetails && (
                <div className="mb-8 p-6 bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-teal-600 rounded-xl flex items-center justify-center">
                      <Users className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-bold text-gray-900">Session Confirmed</h3>
                  </div>
                  <div className="space-y-2 text-gray-700">
                    {paymentStatus.sessionDetails.mentor_name && (
                      <p>Mentor: <strong>{paymentStatus.sessionDetails.mentor_name}</strong></p>
                    )}
                    {paymentStatus.sessionDetails.date && (
                      <p>Date: <strong>{paymentStatus.sessionDetails.date}</strong></p>
                    )}
                    {paymentStatus.sessionDetails.time && (
                      <p>Time: <strong>{paymentStatus.sessionDetails.time}</strong></p>
                    )}
                  </div>
                </div>
              )}

              {/* === WALLET === */}
              {paymentType === "wallet" && (
                <div className="mb-8 p-6 bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
                      <Wallet className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-bold text-gray-900">Wallet Credited</h3>
                  </div>
                  <p className="text-gray-700 text-lg">
                    <strong className="text-purple-600">GH₵{paymentStatus.amount}</strong> has been added to your wallet.
                  </p>
                </div>
              )}

              {/* === EVENT REGISTRATION === */}
              {paymentType === "event_registration" && (
                <div className="mb-8">
                  <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border-2 border-indigo-200 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                        <Ticket className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900">Registration Confirmed</h3>
                        <p className="text-sm text-gray-600">
                          {paymentStatus.eventName || "Event Registration"}
                        </p>
                      </div>
                    </div>

                    {/* Registration Number */}
                    {paymentStatus.registrationNumber && (
                      <div className="bg-white rounded-xl p-4 mb-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600 mb-1">Registration Number</p>
                            <p className="text-2xl font-mono font-bold text-indigo-600 tracking-wider">
                              {paymentStatus.registrationNumber}
                            </p>
                          </div>
                          <button
                            onClick={() => copyValidationCode(paymentStatus.registrationNumber)}
                            className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
                            title="Copy registration number"
                          >
                            {copiedCode === paymentStatus.registrationNumber ? (
                              <CheckCircle className="w-5 h-5" />
                            ) : (
                              <Copy className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Package Info */}
                    {paymentStatus.packageName && (
                      <div className="bg-white rounded-xl p-4 mb-4">
                        <p className="text-sm text-gray-600 mb-1">Package</p>
                        <p className="font-semibold text-gray-900">{paymentStatus.packageName}</p>
                      </div>
                    )}

                    {/* Payment Status */}
                    <div className="bg-white rounded-xl p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600 mb-1">Payment Status</p>
                          <p className={`font-semibold ${paymentStatus.isFullyPaid ? 'text-green-600' : 'text-amber-600'}`}>
                            {paymentStatus.isFullyPaid ? 'Fully Paid' : 'Partial Payment'}
                          </p>
                        </div>
                        {!paymentStatus.isFullyPaid && paymentStatus.balanceDue && (
                          <div className="text-right">
                            <p className="text-sm text-gray-600 mb-1">Balance Due</p>
                            <p className="font-bold text-amber-600">GH₵{paymentStatus.balanceDue}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Event info note */}
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800">
                      <p className="font-semibold mb-1">What&apos;s next?</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Keep your registration number safe</li>
                        <li>Check your email for event details</li>
                        <li>Present your registration number at check-in</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Transaction Details */}
              <div className="bg-gray-50 rounded-2xl p-6 mb-8">
                <h3 className="font-bold text-gray-900 mb-4">Transaction Details</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Reference</span>
                    <span className="font-mono text-gray-900 bg-gray-100 px-2 py-0.5 rounded">
                      {paymentStatus.reference}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Amount</span>
                    <span className="font-bold text-gray-900">GH₵{paymentStatus.amount}</span>
                  </div>
                  {paymentStatus.completedAt && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Date</span>
                      <span className="text-gray-900">
                        {new Date(paymentStatus.completedAt).toLocaleString()}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Status</span>
                    <span className="text-green-600 font-semibold capitalize flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      {paymentStatus.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-4">
                {/* For unified checkout with both types, show both shopping options */}
                {paymentType === "unified_checkout" && paymentStatus.merchandiseResults?.length > 0 && paymentStatus.elMercadoResults?.length > 0 ? (
                  <>
                    <button
                      onClick={() => navigate("/purchase-merchandise")}
                      className="flex-1 px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:opacity-90 transition font-medium shadow-lg flex items-center justify-center gap-2"
                    >
                      <ShoppingBag className="w-5 h-5" />
                      Merchandise Store
                    </button>
                    <button
                      onClick={() => navigate("/el-mercado")}
                      className="flex-1 px-6 py-4 bg-gradient-to-r from-orange-500 to-amber-600 text-white rounded-xl hover:opacity-90 transition font-medium shadow-lg flex items-center justify-center gap-2"
                    >
                      <Store className="w-5 h-5" />
                      El Mercado
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => navigate(config.redirectPath)}
                      className="flex-1 px-6 py-4 bg-gray-100 text-gray-900 rounded-xl hover:bg-gray-200 transition font-medium flex items-center justify-center gap-2"
                    >
                      {config.redirectLabel}
                    </button>
                    <button
                      onClick={() => navigate(config.secondaryPath)}
                      className={`flex-1 px-6 py-4 bg-gradient-to-r ${config.color} text-white rounded-xl hover:opacity-90 transition font-medium shadow-lg flex items-center justify-center gap-2`}
                    >
                      {config.secondaryLabel}
                      <ArrowRight className="w-5 h-5" />
                    </button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Pending State */}
        {!loading && !retrying && !error && paymentStatus && !paymentStatus.isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl shadow-xl p-12 text-center"
          >
            <div className="w-24 h-24 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Clock className="w-14 h-14 text-amber-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {config.title} Pending
            </h2>
            <p className="text-gray-600 mb-8">
              Your payment is being processed. Status:{" "}
              <span className="font-semibold capitalize">{paymentStatus?.status}</span>
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleManualRetry}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-5 h-5" />
                Check Again
              </button>
              <button
                onClick={() => navigate(config.redirectPath)}
                className="px-6 py-3 bg-gray-100 text-gray-900 rounded-xl hover:bg-gray-200 transition"
              >
                {config.redirectLabel}
              </button>
            </div>
          </motion.div>
        )}
      </div>
      <Footer />
    </div>
  );
}

export default UniversalPaymentCallback;
