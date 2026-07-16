import { useState, useEffect, useRef, forwardRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import {
  ShoppingCart,
  X,
  Trash2,
  Plus,
  Minus,
  ShoppingBag,
  ChevronRight,
  Package,
  Store,
} from "lucide-react";
import { useCart } from "../../Context/CartContext";

// Format price with currency
const formatPrice = (price, currency = "GHS") => {
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: currency,
  }).format(price);
};

// Mini Cart Item Component - wrapped with forwardRef for AnimatePresence
const MiniCartItem = forwardRef(function MiniCartItem({ item, onRemove, onUpdateQuantity }, ref) {
  const [imageError, setImageError] = useState(false);
  
  const imageUrl = item.main_image || item.image || "/images/placeholder-product.jpg";
  const isElMercado = item.source === "el_mercado";

  return (
    <motion.div
      ref={ref}
      layout
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
    >
      {/* Product Image */}
      <div className="relative w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-gray-200">
        {imageError ? (
          <div className="w-full h-full flex items-center justify-center">
            <Package className="w-6 h-6 text-gray-400" />
          </div>
        ) : (
          <img
            src={imageUrl}
            alt={item.title || item.name}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        )}
        {/* Source badge */}
        <div className={`absolute top-1 left-1 p-1 rounded-full ${
          isElMercado ? "bg-purple-500" : "bg-blue-500"
        }`}>
          {isElMercado ? (
            <Store className="w-2.5 h-2.5 text-white" />
          ) : (
            <Package className="w-2.5 h-2.5 text-white" />
          )}
        </div>
      </div>

      {/* Product Info */}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-gray-900 truncate">
          {item.title || item.name}
        </h4>
        {item.selectedVariant && (
          <p className="text-xs text-gray-500 truncate">
            {item.selectedVariant.name}
          </p>
        )}
        <div className="mt-1 flex items-center justify-between">
          <span className="text-sm font-semibold text-blue-600">
            {formatPrice(item.price, item.currency)}
          </span>
          
          {/* Quantity Controls */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onUpdateQuantity(item.quantity - 1)}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
              disabled={item.quantity <= 1}
            >
              <Minus className="w-3 h-3 text-gray-500" />
            </button>
            <span className="text-xs font-medium w-5 text-center">{item.quantity}</span>
            <button
              onClick={() => onUpdateQuantity(item.quantity + 1)}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
            >
              <Plus className="w-3 h-3 text-gray-500" />
            </button>
          </div>
        </div>
      </div>

      {/* Remove Button */}
      <button
        onClick={onRemove}
        className="p-1.5 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </motion.div>
  );
});

// Main Floating Cart Preview Component
export function FloatingCartPreview({ position = "bottom-right" }) {
  const {
    cartItems,
    getCartCount,
    getCartTotal,
    removeFromCart,
    updateQuantity,
  } = useCart();
  
  const [isOpen, setIsOpen] = useState(false);
  const [showAddedAnimation, setShowAddedAnimation] = useState(false);
  const [prevCount, setPrevCount] = useState(0);
  const panelRef = useRef(null);
  const location = useLocation();
  
  const cartCount = getCartCount();
  const cartTotal = getCartTotal();

  // Hide on cart page
  const isCartPage = location.pathname === "/dashboard/cart";

  // Animate when item is added
  useEffect(() => {
    if (cartCount > prevCount && prevCount > 0) {
      setShowAddedAnimation(true);
      // Auto-open briefly when item added
      setIsOpen(true);
      const timer = setTimeout(() => {
        setShowAddedAnimation(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
    setPrevCount(cartCount);
  }, [cartCount, prevCount]);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  const handleRemoveItem = (item) => {
    const itemId = item.source === "merchandise" ? item.product_id : (item.slug || item.id);
    removeFromCart(itemId, item.source);
  };

  const handleUpdateQuantity = (item, newQuantity) => {
    if (newQuantity <= 0) {
      handleRemoveItem(item);
      return;
    }
    const itemId = item.source === "merchandise" ? item.product_id : (item.slug || item.id);
    updateQuantity(itemId, newQuantity, item.source);
  };

  // Position classes
  const positionClasses = {
    "bottom-right": "bottom-6 right-6",
    "bottom-left": "bottom-6 left-6",
    "top-right": "top-24 right-6",
    "top-left": "top-24 left-6",
  };

  // Don't render on cart page or if no items
  if (isCartPage) return null;

  return (
    <div 
      ref={panelRef}
      className={`fixed ${positionClasses[position]} z-50`}
    >
      <AnimatePresence>
        {/* Expanded Cart Panel */}
        {isOpen && cartCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="absolute bottom-20 right-0 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <ShoppingBag className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Your Cart</h3>
                  <p className="text-xs text-gray-500">{cartCount} item{cartCount !== 1 ? "s" : ""}</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Cart Items */}
            <div className="max-h-80 overflow-y-auto p-3 space-y-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
              <AnimatePresence mode="popLayout">
                {cartItems.slice(0, 5).map((item) => {
                  const itemKey = item.source === "merchandise" 
                    ? item.product_id 
                    : (item.slug || item.id);
                  return (
                    <MiniCartItem
                      key={`${item.source}-${itemKey}`}
                      item={item}
                      onRemove={() => handleRemoveItem(item)}
                      onUpdateQuantity={(qty) => handleUpdateQuantity(item, qty)}
                    />
                  );
                })}
              </AnimatePresence>
              
              {/* Show more indicator */}
              {cartItems.length > 5 && (
                <div className="text-center py-2 text-sm text-gray-500">
                  +{cartItems.length - 5} more item{cartItems.length - 5 !== 1 ? "s" : ""}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-100 bg-gray-50">
              {/* Total */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-600">Subtotal</span>
                <span className="text-lg font-bold text-gray-900">
                  {formatPrice(cartTotal)}
                </span>
              </div>

              {/* View Cart Button */}
              <Link
                to="/dashboard/cart"
                onClick={() => setIsOpen(false)}
                className="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-xl transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
              >
                <ShoppingCart className="w-5 h-5" />
                View Cart & Checkout
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Cart Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`relative p-4 rounded-full shadow-xl transition-all ${
          cartCount > 0
            ? "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            : "bg-gray-200 hover:bg-gray-300"
        }`}
      >
        {/* Added animation */}
        <AnimatePresence>
          {showAddedAnimation && (
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1.5, opacity: 1 }}
              exit={{ scale: 2, opacity: 0 }}
              className="absolute inset-0 rounded-full bg-green-400"
            />
          )}
        </AnimatePresence>

        <ShoppingCart className={`w-6 h-6 relative z-10 ${
          cartCount > 0 ? "text-white" : "text-gray-500"
        }`} />

        {/* Cart Count Badge */}
        <AnimatePresence>
          {cartCount > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="absolute -top-1 -right-1 min-w-[22px] h-[22px] flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full px-1 shadow-lg"
            >
              {cartCount > 99 ? "99+" : cartCount}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Pulse animation when items in cart */}
        {cartCount > 0 && !isOpen && (
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="absolute inset-0 rounded-full bg-blue-400 opacity-30"
          />
        )}
      </motion.button>

      {/* Quick total display */}
      <AnimatePresence>
        {cartCount > 0 && !isOpen && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-white px-3 py-1.5 rounded-lg shadow-lg whitespace-nowrap"
          >
            <span className="text-sm font-semibold text-gray-900">
              {formatPrice(cartTotal)}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default FloatingCartPreview;
