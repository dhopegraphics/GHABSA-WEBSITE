import { useState, useContext, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { useNavigate, Link } from "react-router-dom";
import {
  Package,
  Clock,
  Copy,
  Check,
  RefreshCw,
  ShoppingBag,
  Truck,
  CheckCircle,
  XCircle,
  MapPin,
  Phone,
  Mail,
  Key,
  ChevronRight,
  AlertTriangle,
  Eye,
  Store,
  Edit2,
  X,
  Loader2,
  Star,
  PenSquare,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Oval } from "react-loader-spinner";
import ShippingAddressService from "../Components/ShippingAddresses/ShippingAddressService";

// Order status configurations
const ORDER_STATUS = {
  PENDING: { label: "Pending", color: "yellow", icon: Clock, description: "Awaiting seller confirmation" },
  AWAITING_PAYMENT: { label: "Awaiting Payment", color: "orange", icon: Clock, description: "Payment required" },
  PAID: { label: "Paid", color: "blue", icon: CheckCircle, description: "Payment confirmed" },
  PROCESSING: { label: "Processing", color: "purple", icon: Package, description: "Seller is preparing your order" },
  SHIPPED: { label: "Shipped", color: "indigo", icon: Truck, description: "On its way to you" },
  DELIVERED: { label: "Delivered", color: "green", icon: CheckCircle, description: "Order delivered" },
  COMPLETED: { label: "Completed", color: "green", icon: CheckCircle, description: "Order completed" },
  CANCELLED: { label: "Cancelled", color: "red", icon: XCircle, description: "Order was cancelled" },
  REFUNDED: { label: "Refunded", color: "gray", icon: XCircle, description: "Payment refunded" },
};

const getStatusConfig = (status) => ORDER_STATUS[status] || ORDER_STATUS.PENDING;

export function MyOrders() {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState("info");
  const [orders, setOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Shipping address update state
  const [showShippingModal, setShowShippingModal] = useState(false);
  const [shippingOrderId, setShippingOrderId] = useState(null);
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [loadingAddresses, setLoadingAddresses] = useState(false);
  const [updatingShipping, setUpdatingShipping] = useState(false);

  const handleClose = () => {
    setOpen(false);
  };

  // Fetch orders
  useEffect(() => {
    const fetchOrders = async () => {
      if (!user) {
        setOrders([]);
        return;
      }

      try {
        setLoadingOrders(true);
        const response = await axiosInstance.get(`${BACKEND_HOST}/marketplace/orders/`);
        setOrders(response.data.results || response.data || []);
      } catch (error) {
        console.error("Error fetching orders:", error);
        setMessage("Failed to load orders");
        setSeverity("error");
        setOpen(true);
      } finally {
        setLoadingOrders(false);
      }
    };

    fetchOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const refreshOrders = async () => {
    if (!user) return;
    
    try {
      setLoadingOrders(true);
      const response = await axiosInstance.get(`${BACKEND_HOST}/marketplace/orders/`);
      setOrders(response.data.results || response.data || []);
      setMessage("Orders refreshed");
      setSeverity("success");
      setOpen(true);
    } catch (error) {
      console.error("Error refreshing orders:", error);
      setMessage("Failed to refresh orders");
      setSeverity("error");
      setOpen(true);
    } finally {
      setLoadingOrders(false);
    }
  };

  const copyDeliveryCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setMessage("Delivery code copied! Give this to the seller upon delivery.");
    setSeverity("success");
    setOpen(true);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const confirmDelivery = async (orderId) => {
    try {
      const response = await axiosInstance.post(`${BACKEND_HOST}/marketplace/orders/${orderId}/confirm_delivery/`);
      setMessage("Delivery confirmed! Order completed successfully.");
      setSeverity("success");
      setOpen(true);
      refreshOrders();
    } catch (error) {
      console.error("Error confirming delivery:", error);
      setMessage(error.response?.data?.error || "Failed to confirm delivery");
      setSeverity("error");
      setOpen(true);
    }
  };

  // Open shipping address selection modal
  const openShippingModal = async (orderId) => {
    setShippingOrderId(orderId);
    setShowShippingModal(true);
    setLoadingAddresses(true);
    
    try {
      const response = await ShippingAddressService.getShippingAddresses(axiosInstance);
      setSavedAddresses(response.data || []);
    } catch (error) {
      console.error("Error fetching addresses:", error);
      setMessage("Failed to load addresses. Please add one in settings.");
      setSeverity("error");
      setOpen(true);
    } finally {
      setLoadingAddresses(false);
    }
  };

  // Update shipping address on order
  const updateOrderShipping = async (addressId) => {
    if (!shippingOrderId) return;
    
    setUpdatingShipping(true);
    try {
      await axiosInstance.post(
        `${BACKEND_HOST}/marketplace/orders/${shippingOrderId}/update_shipping/`,
        { shipping_address_id: addressId }
      );
      setMessage("Shipping address updated successfully!");
      setSeverity("success");
      setOpen(true);
      setShowShippingModal(false);
      setShippingOrderId(null);
      refreshOrders();
    } catch (error) {
      console.error("Error updating shipping:", error);
      setMessage(error.response?.data?.error || "Failed to update shipping address");
      setSeverity("error");
      setOpen(true);
    } finally {
      setUpdatingShipping(false);
    }
  };

  // Filter orders
  const filteredOrders = orders.filter(order => {
    if (statusFilter === "all") return true;
    if (statusFilter === "active") return !["COMPLETED", "CANCELLED", "REFUNDED"].includes(order.status);
    return order.status === statusFilter;
  });

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
              <ShoppingBag className="w-10 h-10 text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Please Login
            </h2>
            <p className="text-gray-600 mb-6">
              Login to view your marketplace orders
            </p>
            <button
              onClick={() => navigate("/login")}
              className="inline-block px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
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
                <span className="relative text-purple-600">
                  Orders
                  <motion.div
                    variants={underlineAnimation(0.7)}
                    initial="offscreen"
                    whileInView="onscreen"
                    exit="reverse"
                    className="absolute left-0 bottom-0 h-1 bg-purple-600"
                    style={{ width: "0%", height: "3px" }}
                  />
                </span>
              </motion.h1>
              <p className="text-gray-600 text-sm sm:text-base">
                Track your El Mercado marketplace orders
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/dashboard/settings/shipping-addresses"
                className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg hover:bg-purple-100 transition font-medium text-sm"
              >
                <MapPin className="w-4 h-4" />
                Manage Addresses
              </Link>
              <button
                onClick={refreshOrders}
                disabled={loadingOrders}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium text-gray-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loadingOrders ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Status Filter Tabs */}
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              { key: "all", label: "All Orders" },
              { key: "active", label: "Active" },
              { key: "SHIPPED", label: "Shipped" },
              { key: "DELIVERED", label: "Delivered" },
              { key: "COMPLETED", label: "Completed" },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setStatusFilter(tab.key)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  statusFilter === tab.key
                    ? "bg-purple-600 text-white"
                    : "bg-white text-gray-600 border border-gray-200 hover:border-purple-300"
                }`}
              >
                {tab.label}
                {tab.key === "all" && orders.length > 0 && (
                  <span className="ml-2 bg-white/20 px-2 py-0.5 rounded-full text-xs">
                    {orders.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Orders List */}
          {loadingOrders ? (
            <div className="flex justify-center py-12">
              <Oval
                height={60}
                width={60}
                color="#9333ea"
                visible={true}
                ariaLabel="oval-loading"
                secondaryColor="#9333ea"
                strokeWidth={2}
                strokeWidthSecondary={2}
              />
            </div>
          ) : filteredOrders.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-lg p-12 text-center"
            >
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <ShoppingBag className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {statusFilter === "all" ? "No Orders Yet" : `No ${statusFilter.toLowerCase()} orders`}
              </h3>
              <p className="text-gray-600 mb-6">
                {statusFilter === "all" 
                  ? "Your marketplace orders will appear here after you make a purchase"
                  : "No orders match this filter"}
              </p>
              <Link
                to="/el-mercado"
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                <Store className="w-5 h-5" />
                Browse El Mercado
              </Link>
            </motion.div>
          ) : (
            <div className="space-y-4">
              {filteredOrders.map((order, index) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  index={index}
                  copiedCode={copiedCode}
                  onCopyCode={copyDeliveryCode}
                  onConfirmDelivery={confirmDelivery}
                  onViewDetails={() => setSelectedOrder(order)}
                  onUpdateShipping={() => openShippingModal(order.id)}
                  isExpanded={selectedOrder?.id === order.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <OrderDetailsModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          copiedCode={copiedCode}
          onCopyCode={copyDeliveryCode}
          onConfirmDelivery={confirmDelivery}
        />
      )}

      {/* Shipping Address Selection Modal */}
      <AnimatePresence>
        {showShippingModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
            onClick={() => !updatingShipping && setShowShippingModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl max-w-md w-full max-h-[80vh] overflow-hidden"
            >
              {/* Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-900">Select Shipping Address</h2>
                  <button
                    onClick={() => !updatingShipping && setShowShippingModal(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition"
                    disabled={updatingShipping}
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Choose a saved address for your order delivery
                </p>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[50vh]">
                {loadingAddresses ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
                  </div>
                ) : savedAddresses.length === 0 ? (
                  <div className="text-center py-8">
                    <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="font-semibold text-gray-900 mb-2">No Saved Addresses</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      You haven't added any shipping addresses yet.
                    </p>
                    <Link
                      to="/dashboard/settings/shipping-addresses"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm font-medium"
                    >
                      Add Address
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {savedAddresses.map((address) => (
                      <button
                        key={address.id}
                        onClick={() => updateOrderShipping(address.id)}
                        disabled={updatingShipping}
                        className="w-full p-4 border-2 border-gray-200 rounded-xl hover:border-purple-400 hover:bg-purple-50 transition text-left disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex items-start gap-3">
                          <MapPin className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold text-gray-900">{address.label}</span>
                              {address.is_default && (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                                  Default
                                </span>
                              )}
                            </div>
                            <p className="text-sm font-medium text-gray-800">{address.full_name}</p>
                            <p className="text-sm text-gray-600">{address.address_line_1}</p>
                            <p className="text-sm text-gray-600">{address.city}</p>
                            <p className="text-sm text-gray-500 mt-1">{address.phone}</p>
                          </div>
                          {updatingShipping && (
                            <Loader2 className="w-5 h-5 text-purple-600 animate-spin" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <Link
                  to="/dashboard/settings/shipping-addresses"
                  className="flex items-center justify-center gap-2 w-full py-2 text-purple-600 hover:text-purple-700 font-medium text-sm"
                >
                  <Edit2 className="w-4 h-4" />
                  Manage Addresses
                </Link>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Order Card Component
function OrderCard({ order, index, copiedCode, onCopyCode, onConfirmDelivery, onViewDetails, onUpdateShipping }) {
  const statusConfig = getStatusConfig(order.status);
  const StatusIcon = statusConfig.icon;
  
  const statusColors = {
    yellow: "bg-yellow-100 text-yellow-700 border-yellow-200",
    orange: "bg-orange-100 text-orange-700 border-orange-200",
    blue: "bg-blue-100 text-blue-700 border-blue-200",
    purple: "bg-purple-100 text-purple-700 border-purple-200",
    indigo: "bg-indigo-100 text-indigo-700 border-indigo-200",
    green: "bg-green-100 text-green-700 border-green-200",
    red: "bg-red-100 text-red-700 border-red-200",
    gray: "bg-gray-100 text-gray-700 border-gray-200",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition overflow-hidden"
    >
      {/* Order Header */}
      <div className="p-4 sm:p-6 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${statusColors[statusConfig.color]}`}>
              <StatusIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">Order #{order.order_number}</h3>
              <p className="text-sm text-gray-500">
                {new Date(order.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${statusColors[statusConfig.color]}`}>
              {statusConfig.label}
            </span>
            <span className="text-lg font-bold text-gray-900">
              GH₵{parseFloat(order.total_amount).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Order Items Preview */}
      <div className="p-4 sm:p-6">
        <div className="flex items-center gap-4 mb-4">
          {order.seller?.logo_url ? (
            <img src={order.seller.logo_url} alt="" className="w-8 h-8 rounded-full object-cover" />
          ) : (
            <Store className="w-4 h-4 text-gray-400" />
          )}
          <div>
            <span className="text-sm font-medium text-gray-700 block">
              {order.seller?.display_name || order.seller_name || "Seller"}
            </span>
            {order.seller?.phone && (
              <span className="text-xs text-gray-500">{order.seller.phone}</span>
            )}
          </div>
        </div>

        {/* Items */}
        <div className="flex flex-wrap gap-3 mb-4">
          {order.items?.slice(0, 3).map((item, idx) => (
            <div key={idx} className="flex items-center gap-3 bg-gray-50 rounded-lg p-2 pr-4">
              {item.listing_image_url ? (
                <img
                  src={item.listing_image_url}
                  alt={item.listing_title}
                  className="w-12 h-12 rounded-lg object-cover"
                />
              ) : (
                <div className="w-12 h-12 rounded-lg bg-gray-200 flex items-center justify-center">
                  <Package className="w-6 h-6 text-gray-400" />
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-gray-900 line-clamp-1">
                  {item.listing_title}
                </p>
                <p className="text-xs text-gray-500">
                  Qty: {item.quantity} × GH₵{parseFloat(item.unit_price).toFixed(2)}
                </p>
              </div>
            </div>
          ))}
          {order.items?.length > 3 && (
            <div className="flex items-center px-3 text-sm text-gray-500">
              +{order.items.length - 3} more
            </div>
          )}
        </div>

        {/* Delivery Code Section - Only for shipped orders */}
        {order.status === "SHIPPED" && order.delivery_code && (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Key className="w-5 h-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-purple-900 mb-1">Delivery Verification Code</h4>
                <p className="text-sm text-purple-700 mb-3">
                  Give this code to the seller when you receive your order
                </p>
                <div className="flex items-center gap-3">
                  <code className="px-4 py-2 bg-white rounded-lg text-xl font-mono font-bold text-purple-900 tracking-widest border border-purple-200">
                    {order.delivery_code}
                  </code>
                  <button
                    onClick={() => onCopyCode(order.delivery_code)}
                    className="p-2 bg-purple-100 hover:bg-purple-200 rounded-lg transition"
                  >
                    {copiedCode === order.delivery_code ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <Copy className="w-5 h-5 text-purple-600" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Shipping Address Warning */}
        {!order.shipping_address_line_1 && !["CANCELLED", "REFUNDED", "COMPLETED", "SHIPPED", "DELIVERED"].includes(order.status) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-yellow-800 mb-1">Shipping Address Not Set</h4>
                <p className="text-sm text-yellow-700 mb-3">
                  Please add a shipping address so the seller knows where to deliver your order.
                </p>
                <button
                  onClick={onUpdateShipping}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition text-sm font-medium"
                >
                  <MapPin className="w-4 h-4" />
                  Set Shipping Address
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Shipping Info */}
        {order.shipping_address_line_1 && (
          <div className="flex items-start gap-3 text-sm text-gray-600 mb-4">
            <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-medium text-gray-700">Shipping to: </span>
              {order.shipping_name}, {order.shipping_address_line_1}
              {order.shipping_city && `, ${order.shipping_city}`}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-100">
          <button
            onClick={onViewDetails}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          >
            <Eye className="w-4 h-4" />
            View Details
          </button>
          
          {order.status === "SHIPPED" && (
            <button
              onClick={() => onConfirmDelivery(order.id)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition"
            >
              <CheckCircle className="w-4 h-4" />
              Confirm Delivery
            </button>
          )}
          
          {/* Write Review button for completed orders */}
          {["DELIVERED", "COMPLETED"].includes(order.status) && order.items?.length > 0 && (
            <Link
              to={`/el-mercado/products/${order.items[0]?.listing_slug || order.items[0]?.listing}/review`}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition"
            >
              <Star className="w-4 h-4" />
              Write Review
            </Link>
          )}
          
          {order.tracking_number && (
            <a
              href={order.tracking_url || `https://www.google.com/search?q=${order.tracking_number}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-lg transition"
            >
              <Truck className="w-4 h-4" />
              Track Order
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Order Details Modal
function OrderDetailsModal({ order, onClose, copiedCode, onCopyCode, onConfirmDelivery }) {
  const statusConfig = getStatusConfig(order.status);
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Order #{order.order_number}</h2>
            <p className="text-sm text-gray-500">{statusConfig.description}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <XCircle className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status Timeline */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Order Status</h3>
            {/* Check if order was cancelled or refunded */}
            {["CANCELLED", "REFUNDED"].includes(order.status) ? (
              <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                <XCircle className="w-6 h-6 text-red-500" />
                <div>
                  <p className="font-medium text-red-800">{order.status === "CANCELLED" ? "Order Cancelled" : "Order Refunded"}</p>
                  <p className="text-sm text-red-600">This order has been {order.status.toLowerCase()}</p>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  {["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "COMPLETED"].map((status, idx) => {
                    // Map order status to timeline position
                    // PAID status should be treated same as PENDING (early stage)
                    // AWAITING_PAYMENT should be treated same as PENDING
                    const statusOrder = {
                      "PENDING": 0,
                      "AWAITING_PAYMENT": 0,
                      "PAID": 0,
                      "PROCESSING": 1,
                      "SHIPPED": 2,
                      "DELIVERED": 3,
                      "COMPLETED": 4
                    };
                    const currentStatusIdx = statusOrder[order.status] ?? -1;
                    const isActive = currentStatusIdx >= idx;
                    const isCurrent = (order.status === status) || 
                      (status === "PENDING" && ["AWAITING_PAYMENT", "PAID"].includes(order.status));
                    
                    return (
                      <div key={status} className="flex items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                          isActive ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-500"
                        } ${isCurrent ? "ring-2 ring-purple-300 ring-offset-2" : ""}`}>
                          {isActive ? <Check className="w-4 h-4" /> : idx + 1}
                        </div>
                        {idx < 4 && (
                          <div className={`w-8 h-1 ${isActive && currentStatusIdx > idx ? "bg-purple-600" : "bg-gray-200"}`} />
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-500">
                  <span>Pending</span>
                  <span>Processing</span>
                  <span>Shipped</span>
                  <span>Delivered</span>
                  <span>Complete</span>
                </div>
              </>
            )}
          </div>

          {/* Completed Order - Success Message */}
          {order.status === "COMPLETED" && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-green-900">Order Completed!</h4>
                  <p className="text-sm text-green-700">
                    Thank you for your purchase. Your order has been successfully delivered.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Delivery Code */}
          {order.status === "SHIPPED" && order.delivery_code && (
            <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <Key className="w-6 h-6 text-purple-600" />
                <h3 className="font-semibold text-purple-900">Your Delivery Code</h3>
              </div>
              <p className="text-sm text-purple-700 mb-4">
                When you receive your order, give this code to the seller to confirm delivery.
              </p>
              <div className="flex items-center gap-3">
                <code className="flex-1 px-6 py-3 bg-white rounded-lg text-2xl font-mono font-bold text-purple-900 tracking-[0.3em] text-center border border-purple-200">
                  {order.delivery_code}
                </code>
                <button
                  onClick={() => onCopyCode(order.delivery_code)}
                  className="p-3 bg-purple-100 hover:bg-purple-200 rounded-lg transition"
                >
                  {copiedCode === order.delivery_code ? (
                    <Check className="w-6 h-6 text-green-600" />
                  ) : (
                    <Copy className="w-6 h-6 text-purple-600" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Order Items */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Items ({order.items?.length || 0})</h3>
            <div className="space-y-3">
              {order.items?.map((item, idx) => (
                <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                  {item.listing_image_url ? (
                    <img
                      src={item.listing_image_url}
                      alt={item.listing_title}
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-gray-200 flex items-center justify-center">
                      <Package className="w-8 h-8 text-gray-400" />
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.listing_title}</p>
                    {item.variant_name && (
                      <p className="text-sm text-gray-500">{item.variant_name}</p>
                    )}
                    <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                    {/* Review link for completed orders */}
                    {["DELIVERED", "COMPLETED"].includes(order.status) && item.listing && (
                      <Link
                        to={`/el-mercado/products/${item.listing_slug || item.listing}/review`}
                        className="inline-flex items-center gap-1 mt-1 text-xs text-purple-600 hover:text-purple-700 font-medium"
                      >
                        <Star className="w-3 h-3" />
                        Write Review
                      </Link>
                    )}
                  </div>
                  <p className="font-bold text-gray-900">
                    GH₵{parseFloat(item.total_price).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Order Summary */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Order Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="text-gray-900">GH₵{parseFloat(order.subtotal).toFixed(2)}</span>
              </div>
              {parseFloat(order.shipping_cost) > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Shipping</span>
                  <span className="text-gray-900">GH₵{parseFloat(order.shipping_cost).toFixed(2)}</span>
                </div>
              )}
              {parseFloat(order.discount_amount) > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-GH₵{parseFloat(order.discount_amount).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between pt-2 border-t border-gray-200 font-bold text-lg">
                <span>Total</span>
                <span>GH₵{parseFloat(order.total_amount).toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Shipping Address */}
          {order.shipping_address_line_1 ? (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Shipping Address</h3>
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">{order.shipping_name}</p>
                    <p className="text-sm text-gray-600">{order.shipping_address_line_1}</p>
                    {order.shipping_address_line_2 && (
                      <p className="text-sm text-gray-600">{order.shipping_address_line_2}</p>
                    )}
                    <p className="text-sm text-gray-600">
                      {order.shipping_city}{order.shipping_region && `, ${order.shipping_region}`}
                    </p>
                    {order.shipping_digital_address && (
                      <p className="text-sm text-purple-600 font-medium mt-1">
                        📍 {order.shipping_digital_address}
                      </p>
                    )}
                  </div>
                </div>
                {order.shipping_phone && (
                  <div className="flex items-center gap-3 mt-3 pt-3 border-t border-gray-200">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-600">{order.shipping_phone}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold text-yellow-800">No Shipping Address</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Please add a shipping address for this order.
                  </p>
                  <Link
                    to="/dashboard/settings/shipping-addresses"
                    className="inline-flex items-center gap-1 mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900"
                  >
                    Add Address <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Seller Info */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Seller</h3>
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
              {order.seller?.logo_url ? (
                <img src={order.seller.logo_url} alt="" className="w-12 h-12 rounded-full object-cover" />
              ) : (
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <Store className="w-6 h-6 text-purple-600" />
                </div>
              )}
              <div className="flex-1">
                <p className="font-medium text-gray-900">{order.seller?.display_name || order.seller_name || "Seller"}</p>
                {order.seller?.phone && (
                  <a href={`tel:${order.seller.phone}`} className="flex items-center gap-1 text-sm text-gray-600 hover:text-purple-600">
                    <Phone className="w-3 h-3" />
                    {order.seller.phone}
                  </a>
                )}
                {order.seller?.email && (
                  <a href={`mailto:${order.seller.email}`} className="flex items-center gap-1 text-sm text-gray-500 hover:text-purple-600">
                    <Mail className="w-3 h-3" />
                    {order.seller.email}
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-white border-t border-gray-100 p-6 flex flex-wrap gap-3">
          <button
            onClick={onClose}
            className="flex-1 min-w-[120px] px-4 py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition"
          >
            Close
          </button>
          {order.status === "SHIPPED" && (
            <button
              onClick={() => {
                onConfirmDelivery(order.id);
                onClose();
              }}
              className="flex-1 min-w-[150px] px-4 py-3 text-white bg-green-600 hover:bg-green-700 rounded-lg font-medium transition flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-5 h-5" />
              Confirm Delivery
            </button>
          )}
          {["DELIVERED", "COMPLETED"].includes(order.status) && order.items?.length > 0 && (
            <Link
              to={`/el-mercado/products/${order.items[0]?.listing_slug || order.items[0]?.listing}/review`}
              onClick={onClose}
              className="flex-1 min-w-[150px] px-4 py-3 text-white bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition flex items-center justify-center gap-2"
            >
              <PenSquare className="w-5 h-5" />
              Write a Review
            </Link>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default MyOrders;
