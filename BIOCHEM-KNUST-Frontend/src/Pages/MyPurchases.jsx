import { useState, useContext, useEffect } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { useNavigate } from "react-router-dom";
import {
  Package,
  CheckCircle,
  Clock,
  Copy,
  Check,
  RefreshCw,
  AlertCircle,
  ShoppingBag,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Oval } from "react-loader-spinner";
import { VariantModal } from "../Components/Merchandise/VariantModal";

export function MyPurchases() {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState("info");
  const [purchases, setPurchases] = useState([]);
  const [pendingTransactions, setPendingTransactions] = useState([]);
  const [loadingPurchases, setLoadingPurchases] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);

  // Retroactive variant modal state
  const [showRetroactiveModal, setShowRetroactiveModal] = useState(false);
  const [selectedPurchase, setSelectedPurchase] = useState(null);
  const [isUpdatingPreferences, setIsUpdatingPreferences] = useState(false);

  const handleClose = () => {
    setOpen(false);
  };

  // Fetch purchases and pending transactions
  useEffect(() => {
    const fetchPurchases = async () => {
      if (!user) {
        setPurchases([]);
        setPendingTransactions([]);
        return;
      }

      try {
        setLoadingPurchases(true);
        
        // Fetch successful purchases
        const successUrl = `${BACKEND_HOST}/products/payments/my_purchases/?status=success`;
        const successResponse = await axiosInstance.get(successUrl);
        if (successResponse.data.success) {
          setPurchases(successResponse.data.purchases || []);
        }
        
        // Fetch pending transactions
        const pendingUrl = `${BACKEND_HOST}/payments/api/transactions/?status=pending&transaction_type=payment`;
        const pendingResponse = await axiosInstance.get(pendingUrl);
        if (pendingResponse.data) {
          setPendingTransactions(pendingResponse.data.results || pendingResponse.data || []);
        }
      } catch (error) {
        console.error("Error fetching purchases:", error);
        console.error("Error response:", error.response?.data);
      } finally {
        setLoadingPurchases(false);
      }
    };

    fetchPurchases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const copyValidationCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setMessage("Validation code copied!");
    setSeverity("success");
    setOpen(true);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleSetRetroactivePreferences = (purchase) => {
    // Check if product has variants enabled
    const hasColors = purchase.product_details?.has_colors;
    const hasSizes = purchase.product_details?.has_sizes;

    if (!hasColors && !hasSizes) {
      setMessage("This product doesn't have color/size options available");
      setSeverity("info");
      setOpen(true);
      return;
    }

    setSelectedPurchase(purchase);
    setShowRetroactiveModal(true);
  };

  const handleUpdatePreferences = async (variantSelections) => {
    if (!selectedPurchase) return;

    try {
      setIsUpdatingPreferences(true);
      const url = `${BACKEND_HOST}/products/payments/update_variant_preferences/`;
      const payload = {
        reference: selectedPurchase.reference,
        variant_selections: variantSelections,
      };

      const response = await axiosInstance.post(url, payload);

      if (response.data.success) {
        const changesRemaining = response.data.changes_remaining || 0;
        let successMessage = "Preferences updated successfully!";
        
        if (response.data.preferences_locked) {
          successMessage += " Your preferences are now locked and cannot be changed again.";
        } else if (changesRemaining === 0) {
          successMessage += " You have used your one-time preference change. Further changes are not allowed.";
        }
        
        setMessage(successMessage);
        setSeverity("success");
        setOpen(true);
        setShowRetroactiveModal(false);
        setSelectedPurchase(null);

        // Refresh purchases to show updated preferences
        const fetchUrl = `${BACKEND_HOST}/products/payments/my_purchases/?status=success`;
        const fetchResponse = await axiosInstance.get(fetchUrl);
        if (fetchResponse.data.success) {
          setPurchases(fetchResponse.data.purchases || []);
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || "Failed to update preferences";
      setMessage(errorMsg);
      setSeverity("error");
      setOpen(true);
    } finally {
      setIsUpdatingPreferences(false);
    }
  };

  const refreshPurchases = async () => {
    setLoadingPurchases(true);
    try {
      // Fetch successful purchases
      const successUrl = `${BACKEND_HOST}/products/payments/my_purchases/?status=success`;
      const successResponse = await axiosInstance.get(successUrl);
      if (successResponse.data.success) {
        setPurchases(successResponse.data.purchases || []);
      }
      
      // Fetch pending transactions
      const pendingUrl = `${BACKEND_HOST}/payments/api/transactions/?status=pending&transaction_type=payment`;
      const pendingResponse = await axiosInstance.get(pendingUrl);
      if (pendingResponse.data) {
        setPendingTransactions(pendingResponse.data.results || pendingResponse.data || []);
      }
      
      setMessage("Purchases refreshed!");
      setSeverity("success");
      setOpen(true);
    } catch {
      setMessage("Failed to refresh purchases");
      setSeverity("error");
      setOpen(true);
    } finally {
      setLoadingPurchases(false);
    }
  };

  // If user is not logged in
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 sm:py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg p-12 text-center"
          >
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Package className="w-10 h-10 text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Please Login
            </h2>
            <p className="text-gray-600 mb-6">
              Login to view your purchase history
            </p>
            <button
              onClick={() => navigate("/login")}
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Login
            </button>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Snackbar
        open={open}
        autoHideDuration={5000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={handleClose}
      >
        <Alert onClose={handleClose} severity={severity} sx={{ width: "100%" }}>
          <AlertTitle>
            {severity.charAt(0).toUpperCase() + severity.slice(1)}
          </AlertTitle>
          {message}
        </Alert>
      </Snackbar>

      <div className="min-h-screen bg-gray-50 py-8 sm:py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8 sm:mb-12">
            <div>
              <motion.h1
                variants={fadeIn("up", 0.5, 0)}
                initial="offscreen"
                whileInView="onscreen"
                viewport={{ once: true, amount: 0 }}
                className="text-3xl sm:text-4xl md:text-5xl mb-2 font-bold text-gray-900"
              >
                My{" "}
                <span className="relative text-blue-600">
                  Purchases
                  <motion.div
                    variants={underlineAnimation(0.7)}
                    initial="offscreen"
                    whileInView="onscreen"
                    exit="reverse"
                    className="absolute left-0 bottom-0 h-1 bg-blue-600"
                    style={{ width: "0%", height: "3px" }}
                  />
                </span>
              </motion.h1>
              <p className="text-gray-600 text-sm sm:text-base">
                View your purchase history and validation codes
              </p>
            </div>
            <button
              onClick={refreshPurchases}
              disabled={loadingPurchases}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium text-gray-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loadingPurchases ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Pending Transactions Alert Section */}
          {pendingTransactions.length > 0 && (
            <motion.div
              variants={fadeIn("up", 0.4, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="mb-8"
            >
              <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                      <Clock className="w-6 h-6 text-yellow-600" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      Pending Transactions ({pendingTransactions.length})
                    </h3>
                    <p className="text-gray-700 mb-4">
                      You have {pendingTransactions.length} payment{pendingTransactions.length > 1 ? 's' : ''} that {pendingTransactions.length > 1 ? 'are' : 'is'} pending verification. 
                      If you&apos;ve already paid but didn&apos;t receive confirmation, you can retry verification.
                    </p>
                    
                    {/* Pending transactions list */}
                    <div className="space-y-3 mb-4">
                      {pendingTransactions.slice(0, 3).map((transaction) => (
                        <div 
                          key={transaction.id || transaction.reference}
                          className="bg-white rounded-lg p-4 border border-yellow-200"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <p className="font-semibold text-gray-900">
                                GH₵ {parseFloat(transaction.amount).toFixed(2)}
                              </p>
                              <p className="text-sm text-gray-600">
                                {transaction.description || 'Product Purchase'}
                              </p>
                            </div>
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                              Pending
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mb-1">
                            Reference: {transaction.reference}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(transaction.initiated_at).toLocaleString()}
                          </p>
                        </div>
                      ))}
                      
                      {pendingTransactions.length > 3 && (
                        <p className="text-sm text-gray-600 text-center">
                          + {pendingTransactions.length - 3} more pending transaction{pendingTransactions.length - 3 > 1 ? 's' : ''}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => navigate('/dashboard/retry-payment')}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                      >
                        <RefreshCw className="w-4 h-4" />
                        Retry Verification
                      </button>
                      <button
                        onClick={() => {
                          setMessage("Our system automatically checks pending transactions every 5 minutes. If you were charged, your purchase will be processed automatically.");
                          setSeverity("info");
                          setOpen(true);
                        }}
                        className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
                      >
                        More Info
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Purchase History */}
          {loadingPurchases ? (
            <div className="flex justify-center py-12">
              <Oval
                height={60}
                width={60}
                color="#2563eb"
                visible={true}
                ariaLabel="oval-loading"
                secondaryColor="#2563eb"
                strokeWidth={2}
                strokeWidthSecondary={2}
              />
            </div>
          ) : purchases.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-lg p-12 text-center"
            >
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Package className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                No Purchases Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Your purchase history will appear here after you make your first purchase
              </p>
              <a
                href="/purchase-merchandise"
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <ShoppingBag className="w-5 h-5" />
                Browse Merchandise
              </a>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {purchases.map((purchase, index) => (
                <motion.div
                  key={purchase.payment_id || purchase.reference}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden"
                >
                  {/* Product Image */}
                  {purchase.product_details?.product_image && (
                    <div className="h-48 overflow-hidden bg-gray-100">
                      <img
                        src={purchase.product_details.product_image}
                        alt={purchase.product_details.product_name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}

                  <div className="p-6">
                    {/* Product Name */}
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      {purchase.product_details?.product_name || "Product"}
                    </h3>

                    {/* Purchase Type Indicator */}
                    {(purchase.is_gift_purchase || purchase.is_purchase_on_behalf) && (
                      <div className="mb-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl">
                            {purchase.is_gift_purchase ? "🎁" : "🤝"}
                          </span>
                          {purchase.recipient_info?.linked ? (
                            <span className={`text-sm font-medium ${
                              purchase.is_gift_purchase ? "text-pink-600" : "text-purple-600"
                            }`}>
                              {String(purchase.buyer_info?.id) === String(user?.user?.id)
                                ? `${purchase.is_gift_purchase ? "Gift to" : "Bought on behalf of"} ${purchase.recipient_info.name}`
                                : `${purchase.is_gift_purchase ? "Gift" : "Purchased on your behalf"} from ${purchase.buyer_info?.name}`}
                            </span>
                          ) : (
                            <span className="text-sm font-medium text-orange-600">
                              {String(purchase.buyer_info?.id) === String(user?.user?.id)
                                ? `${purchase.is_gift_purchase ? "Gift to" : "On behalf of"} ${purchase.recipient_info?.phone} (Pending)`
                                : `${purchase.is_gift_purchase ? "Gift" : "Purchase"} (Pending)`}
                            </span>
                          )}
                        </div>
                        
                        {/* Show gift message if user is the recipient and it's a gift */}
                        {purchase.is_gift_purchase && 
                         purchase.gift_message && 
                         String(purchase.recipient_info?.id) === String(user?.user?.id) && (
                          <div className="bg-pink-50 border-l-4 border-pink-500 p-3 rounded">
                            <p className="text-sm text-gray-700 italic">&quot;{purchase.gift_message}&quot;</p>
                            <p className="text-xs text-gray-500 mt-1">
                              From {purchase.buyer_info?.name}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Status Badge */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      {purchase.merchandise_taken ? (
                        <span className="flex items-center gap-1 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                          <CheckCircle className="w-4 h-4" />
                          Fully Collected
                        </span>
                      ) : purchase.status === 'partial' || purchase.collection_summary?.overall_status === 'partial' ? (
                        <span className="flex items-center gap-1 text-sm text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
                          <Clock className="w-4 h-4" />
                          Partially Collected
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-sm text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                          <Clock className="w-4 h-4" />
                          Pending Collection
                        </span>
                      )}
                      {/* Show collection progress if partial */}
                      {purchase.collection_summary && purchase.collection_summary.total_collected > 0 && !purchase.merchandise_taken && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          {purchase.collection_summary.total_collected}/{purchase.collection_summary.total_ordered} items
                        </span>
                      )}
                    </div>

                    {/* Purchase Details */}
                    <div className="space-y-2 mb-4 text-sm">
                      <div className="flex justify-between text-gray-600">
                        <span>Quantity:</span>
                        <span className="font-semibold text-gray-900">
                          {purchase.quantity || 1}
                        </span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>Amount:</span>
                        <span className="font-semibold text-gray-900">
                          GH₵{parseFloat(purchase.amount).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>Date:</span>
                        <span className="font-semibold text-gray-900">
                          {new Date(
                            purchase.payed_at ||
                              purchase.initiated_at ||
                              purchase.created_at
                          ).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {/* Variant Selections Display/Update */}
                    {purchase.formatted_variant_selections &&
                    purchase.formatted_variant_selections.length > 0 ? (
                      <div className="mb-4 bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div className="flex justify-between items-start mb-2">
                          <p className="text-xs font-semibold text-gray-700">
                            Your Preferences:
                          </p>
                          {/* Show change status - only if no collection has started */}
                          {purchase.can_change_preferences?.allowed && !purchase.merchandise_taken && (
                            <button
                              onClick={() => handleSetRetroactivePreferences(purchase)}
                              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                            >
                              Change ({purchase.can_change_preferences.changes_remaining} left)
                            </button>
                          )}
                          {(purchase.preferences_locked || purchase.collection_summary?.total_collected > 0) && (
                            <span className="text-xs text-gray-500 italic">
                              {purchase.collection_summary?.total_collected > 0 ? 'Collection started' : 'Locked'}
                            </span>
                          )}
                        </div>
                        {/* Use formatted_collection_details if available for per-item status */}
                        {purchase.formatted_collection_details && purchase.formatted_collection_details.length > 0 ? (
                          purchase.formatted_collection_details.map((detail, idx) => (
                            <div
                              key={idx}
                              className={`text-xs flex flex-wrap gap-2 mb-1.5 p-1.5 rounded ${
                                detail.status === 'collected' ? 'bg-green-50' :
                                detail.status === 'partial' ? 'bg-amber-50' :
                                detail.status === 'unavailable' ? 'bg-red-50' :
                                'bg-white'
                              }`}
                            >
                              <span className="font-medium text-gray-700">
                                Item {idx + 1}:
                              </span>
                              {detail.color_name && (
                                <span className="px-2 py-0.5 rounded flex items-center gap-1 bg-white/50">
                                  <span
                                    className="w-3 h-3 rounded-full border border-gray-300"
                                    style={{ backgroundColor: detail.color_hex || '#888' }}
                                  />
                                  {detail.color_name}
                                </span>
                              )}
                              {detail.size_name && (
                                <span className="bg-white/50 px-2 py-0.5 rounded">
                                  {detail.size_code || detail.size_name}
                                </span>
                              )}
                              {/* Collection status indicator */}
                              <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                detail.status === 'collected' ? 'bg-green-100 text-green-700' :
                                detail.status === 'partial' ? 'bg-amber-100 text-amber-700' :
                                detail.status === 'unavailable' ? 'bg-red-100 text-red-700' :
                                'bg-gray-100 text-gray-600'
                              }`}>
                                {detail.status === 'collected' ? `✓ ${detail.collected_quantity}/${detail.ordered_quantity}` :
                                 detail.status === 'partial' ? `${detail.collected_quantity}/${detail.ordered_quantity}` :
                                 detail.status === 'unavailable' ? 'N/A' :
                                 'Pending'}
                              </span>
                            </div>
                          ))
                        ) : (
                          // Fallback to formatted_variant_selections if no collection_details
                          purchase.formatted_variant_selections.map((sel, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-gray-600 flex gap-2 mb-1"
                            >
                              <span className="font-medium">
                                Item {idx + 1}:
                              </span>
                              {sel.color && (
                                <span className="bg-white px-2 py-0.5 rounded flex items-center gap-1">
                                  <span
                                    className="w-3 h-3 rounded-full border border-gray-300"
                                    style={{ backgroundColor: sel.color.hex_code }}
                                  />
                                  {sel.color.name}
                                </span>
                              )}
                              {sel.size && (
                                <span className="bg-white px-2 py-0.5 rounded">
                                  {sel.size.code || sel.size.name}
                                </span>
                              )}
                            </div>
                          ))
                        )}
                        {/* Show last updated time if changed */}
                        {purchase.preferences_last_updated_at && purchase.preference_change_count > 0 && (
                          <p className="text-xs text-gray-500 italic mt-2">
                            Updated {new Date(purchase.preferences_last_updated_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    ) : (
                      // Only show "Set Preferences" if product has variants enabled
                      (purchase.product_details?.has_colors ||
                        purchase.product_details?.has_sizes) && (
                        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex items-start gap-2 mb-2">
                            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm font-semibold text-red-800 mb-1">
                                ⚠️ Preferences Required!
                              </p>
                              <p className="text-xs text-red-700 mb-2">
                                You need to set your {purchase.needs_preferences?.missing?.join(' and ')} preferences for collection.
                                {purchase.can_change_preferences?.allowed && ` You have ${purchase.can_change_preferences.changes_remaining} chance to set/change.`}
                              </p>
                              {purchase.can_change_preferences?.allowed && !purchase.merchandise_taken && purchase.collection_summary?.total_collected === 0 ? (
                                <button
                                  onClick={() => handleSetRetroactivePreferences(purchase)}
                                  className="text-xs bg-red-600 text-white px-3 py-1.5 rounded hover:bg-red-700 font-medium"
                                >
                                  Set Preferences Now
                                </button>
                              ) : (
                                <p className="text-xs text-red-600 italic">
                                  {purchase.collection_summary?.total_collected > 0 
                                    ? "Cannot change preferences after collection has started"
                                    : purchase.can_change_preferences?.reason || "Cannot set preferences"}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    )}

                    {/* Validation Code */}
                    {!purchase.merchandise_taken &&
                      purchase.transaction_validation_code && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1 font-medium">
                            Validation Code:
                          </p>
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-2xl font-bold text-blue-600 tracking-wider">
                              {purchase.transaction_validation_code}
                            </span>
                            <button
                              onClick={() =>
                                copyValidationCode(
                                  purchase.transaction_validation_code
                                )
                              }
                              className="p-2 hover:bg-blue-100 rounded-lg transition"
                              title="Copy code"
                            >
                              {copiedCode ===
                              purchase.transaction_validation_code ? (
                                <Check className="w-5 h-5 text-green-600" />
                              ) : (
                                <Copy className="w-5 h-5 text-blue-600" />
                              )}
                            </button>
                          </div>
                          <p className="text-xs text-gray-500 mt-2">
                            Show this code to collect your merchandise
                          </p>
                        </div>
                      )}

                    {/* Collection Date */}
                    {purchase.merchandise_taken &&
                      purchase.merchandise_taken_at && (
                        <p className="text-xs text-gray-500 mt-3">
                          Collected on{" "}
                          {new Date(
                            purchase.merchandise_taken_at
                          ).toLocaleDateString()}
                        </p>
                      )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Loading Overlay for Updating Preferences */}
      {isUpdatingPreferences && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="flex flex-col items-center">
            <Oval
              height={80}
              width={80}
              color="#2563eb"
              visible={true}
              ariaLabel="oval-loading"
              secondaryColor="#2563eb"
              strokeWidth={2}
              strokeWidthSecondary={2}
            />
            <p className="mt-4 text-lg font-semibold text-white">
              Updating your preferences...
            </p>
          </div>
        </div>
      )}

      {/* Retroactive Variant Modal */}
      <VariantModal
        isOpen={showRetroactiveModal && selectedPurchase !== null}
        onClose={() => {
          setShowRetroactiveModal(false);
          setSelectedPurchase(null);
        }}
        product={{
          product_name:
            selectedPurchase?.product_details?.product_name ||
            selectedPurchase?.product_name ||
            "",
          has_colors: selectedPurchase?.product_details?.has_colors || false,
          has_sizes: selectedPurchase?.product_details?.has_sizes || false,
          available_colors:
            selectedPurchase?.product_details?.available_colors || [],
          available_sizes:
            selectedPurchase?.product_details?.available_sizes || [],
        }}
        quantity={selectedPurchase?.quantity || 1}
        onConfirm={handleUpdatePreferences}
        isLoading={isUpdatingPreferences}
        mode="update"
        initialSelections={
          selectedPurchase?.formatted_variant_selections ||
          selectedPurchase?.variant_selections ||
          []
        }
      />
    </>
  );
}
