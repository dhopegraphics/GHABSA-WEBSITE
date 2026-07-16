import { useState, useContext } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import {
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  ShoppingBag,
  AlertCircle,
  Gift,
  Users,
  Store,
  Package,
  MapPin,
} from "lucide-react";
import { useCart } from "../Context/CartContext";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Oval } from "react-loader-spinner";
import { VariantSelector } from "../Components/Merchandise/VariantSelector";
import { RecipientModal } from "../Components/Cart/RecipientModal";
import { ShippingAddressSelector } from "../Components/ShippingAddresses";

export function CartPage() {
  const {
    cartItems,
    removeFromCart,
    updateQuantity,
    updateVariantSelections,
    getCartTotal,
    clearCart,
    // Recipient management
    globalRecipient,
    setGlobalRecipientInfo,
    setItemRecipient,
    setVariantRecipient,
    getEffectiveRecipient,
    // Unified cart methods
    getCartItemsBySource,
    getCartTotalsBySource,
  } = useCart();
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [isProcessing, setIsProcessing] = useState(false);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState("info");

  // Shipping address state
  const [selectedShippingAddress, setSelectedShippingAddress] = useState(null);

  // Recipient modal state
  const [recipientModalOpen, setRecipientModalOpen] = useState(false);
  const [recipientModalConfig, setRecipientModalConfig] = useState({
    level: null, // 'global', 'item', or 'variant'
    productId: null,
    variantIndex: null,
    initialData: null,
    title: "",
    description: "",
  });

  // Get cart items by source for display
  const cartBySource = getCartItemsBySource ? getCartItemsBySource() : { merchandise: cartItems, el_mercado: [] };
  const cartTotals = getCartTotalsBySource ? getCartTotalsBySource() : { merchandise: getCartTotal(), el_mercado: 0, total: getCartTotal() };
  const hasMixedCart = cartBySource.merchandise.length > 0 && cartBySource.el_mercado.length > 0;

  // Group El Mercado items by seller for better UX
  const elMercadoItemsBySeller = cartBySource.el_mercado.reduce((groups, item) => {
    const sellerId = item.seller_id || item.seller?.id || 'unknown';
    // Backend returns display_name (primary), business_name is alias in some serializers
    const sellerName = item.seller?.display_name || item.seller?.business_name || item.seller_name || 'Unknown Seller';
    
    if (!groups[sellerId]) {
      groups[sellerId] = {
        sellerId,
        sellerName,
        sellerVerified: item.seller?.is_verified || false,
        items: [],
        subtotal: 0,
      };
    }
    
    groups[sellerId].items.push(item);
    groups[sellerId].subtotal += parseFloat(item.price) * item.quantity;
    
    return groups;
  }, {});
  
  const sellerGroups = Object.values(elMercadoItemsBySeller);
  const hasMultipleSellers = sellerGroups.length > 1;

  const handleQuantityChange = (itemId, newQuantity, maxStock, source = null) => {
    if (newQuantity > maxStock) {
      setMessage(`Only ${maxStock} items available in stock`);
      setSeverity("warning");
      setOpen(true);
      return;
    }
    updateQuantity(itemId, newQuantity, source);
  };

  const handleRemove = (itemId, source = null) => {
    removeFromCart(itemId, source);
    setMessage("Item removed from cart");
    setSeverity("success");
    setOpen(true);
  };

  // ========== Recipient Modal Handlers ==========
  
  const openGlobalRecipientModal = () => {
    setRecipientModalConfig({
      level: 'global',
      productId: null,
      variantIndex: null,
      initialData: globalRecipient,
      title: "Set Recipients for All Items",
      description: "This will apply to all items in your cart",
    });
    setRecipientModalOpen(true);
  };

  const openItemRecipientModal = (item) => {
    const itemId = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
    setRecipientModalConfig({
      level: 'item',
      productId: itemId,
      variantIndex: null,
      initialData: item.recipient || null,
      title: `Set Recipient for ${item.product_name || item.title}`,
      description: "This will apply to this specific item",
      source: item.source,
    });
    setRecipientModalOpen(true);
  };

  const openVariantRecipientModal = (item, variantIndex) => {
    const itemId = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
    const variantRecipient = item.variantSelections?.[variantIndex]?.recipient;
    setRecipientModalConfig({
      level: 'variant',
      productId: itemId,
      variantIndex,
      initialData: variantRecipient || null,
      title: `Set Recipient for Variant #${variantIndex + 1}`,
      description: `${item.product_name || item.title} - Variant ${variantIndex + 1}`,
      source: item.source,
    });
    setRecipientModalOpen(true);
  };

  const handleRecipientConfirm = (recipientData) => {
    const { level, productId, variantIndex, source } = recipientModalConfig;

    if (level === 'global') {
      setGlobalRecipientInfo(recipientData);
      setMessage(recipientData ? "Applied to all items in cart" : "Cleared global recipient");
    } else if (level === 'item') {
      setItemRecipient(productId, recipientData, source);
      setMessage(recipientData ? "Recipient set for this item" : "Cleared item recipient");
    } else if (level === 'variant') {
      setVariantRecipient(productId, variantIndex, recipientData, source);
      setMessage(recipientData ? "Recipient set for this variant" : "Cleared variant recipient");
    }

    setSeverity("success");
    setOpen(true);
  };

  const handleCheckout = async () => {
    if (!user) {
      setMessage("Please login to proceed with checkout");
      setSeverity("error");
      setOpen(true);
      return;
    }

    if (cartItems.length === 0) {
      setMessage("Your cart is empty");
      setSeverity("warning");
      setOpen(true);
      return;
    }

    // Validate variant selections for merchandise products that require them
    for (const item of cartBySource.merchandise) {
      if (item.has_colors || item.has_sizes) {
        const selections = item.variantSelections || [];

        // Check if all items have variant selections
        if (selections.length !== item.quantity) {
          setMessage(
            `Please select color/size preferences for ${item.product_name}`
          );
          setSeverity("warning");
          setOpen(true);
          return;
        }

        // Validate each selection is complete
        for (let i = 0; i < selections.length; i++) {
          const sel = selections[i];
          if (item.has_colors && !sel.color_id) {
            setMessage(
              `Please select color for all ${item.product_name} items`
            );
            setSeverity("warning");
            setOpen(true);
            return;
          }
          if (item.has_sizes && !sel.size_id) {
            setMessage(`Please select size for all ${item.product_name} items`);
            setSeverity("warning");
            setOpen(true);
            return;
          }
        }
      }
      
      // Validate recipient phone numbers (variant-level > item-level > global)
      const itemRecipient = getEffectiveRecipient(item);
      if (itemRecipient && itemRecipient.purchaseType !== "self") {
        if (!itemRecipient.recipientPhone || !itemRecipient.recipientPhone.trim()) {
          setMessage(`Please enter recipient phone number for ${item.product_name}`);
          setSeverity("error");
          setOpen(true);
          return;
        }
      }
    }

    // Validate shipping address for El Mercado items
    const hasElMercadoItems = cartBySource.el_mercado.length > 0;
    if (hasElMercadoItems && !selectedShippingAddress) {
      setMessage("Please select a shipping address for El Mercado items before checkout");
      setSeverity("warning");
      setOpen(true);
      return;
    }

    try {
      setIsProcessing(true);
      setMessage("Initializing payment...");
      setSeverity("info");
      setOpen(true);

      // Determine if we need unified checkout (has El Mercado items)
      const hasMerchandiseItems = cartBySource.merchandise.length > 0;

      if (hasElMercadoItems) {
        // Use unified checkout for mixed carts or El Mercado only carts
        await handleUnifiedCheckout();
      } else if (hasMerchandiseItems) {
        // Use original merchandise-only checkout
        await handleMerchandiseCheckout();
      }
    } catch (error) {
      setMessage(
        error.response?.data?.error ||
          error.message ||
          "Checkout failed. Please try again."
      );
      setSeverity("error");
      setOpen(true);
      setIsProcessing(false);
    }
  };

  // Unified checkout for mixed carts (Merchandise + El Mercado)
  const handleUnifiedCheckout = async () => {
    // Prepare cart items for unified checkout
    const unifiedCartItems = [];

    // Add merchandise items
    for (const item of cartBySource.merchandise) {
      const itemRecipient = item.recipient || globalRecipient;
      
      unifiedCartItems.push({
        source: 'merchandise',
        product_id: item.product_id,
        quantity: item.quantity,
        variant_selections: (item.variantSelections || []).map((sel) => {
          const effectiveRecipient = sel.recipient || itemRecipient;
          return {
            color_id: sel.color_id || null,
            size_id: sel.size_id || null,
            quantity: sel.quantity || 1,
            ...(effectiveRecipient && effectiveRecipient.purchaseType !== "self" && {
              is_gift_purchase: effectiveRecipient.purchaseType === "gift",
              is_purchase_on_behalf: effectiveRecipient.purchaseType === "on_behalf",
              purchased_for_phone: effectiveRecipient.recipientPhone,
              gift_message: effectiveRecipient.purchaseType === "gift" ? effectiveRecipient.giftMessage : null,
            }),
          };
        }),
        ...(itemRecipient && itemRecipient.purchaseType !== "self" && {
          is_gift_purchase: itemRecipient.purchaseType === "gift",
          is_purchase_on_behalf: itemRecipient.purchaseType === "on_behalf",
          purchased_for_phone: itemRecipient.recipientPhone,
          gift_message: itemRecipient.purchaseType === "gift" ? itemRecipient.giftMessage : null,
        }),
      });
    }

    // Add El Mercado items
    for (const item of cartBySource.el_mercado) {
      unifiedCartItems.push({
        source: 'el_mercado',
        listing_id: item.listing_id || item.id,
        seller_id: item.seller_id || item.seller?.id,
        quantity: item.quantity,
        variant_id: item.variant_id || null,
      });
    }

    // Build shipping info from selected address or fallback to user data
    const shippingInfo = selectedShippingAddress
      ? {
          shipping_address_id: selectedShippingAddress.id,
          name: selectedShippingAddress.full_name,
          phone: selectedShippingAddress.phone,
          email: selectedShippingAddress.email || user?.personal_email || user?.email || '',
          address: selectedShippingAddress.address_line_1,
          address_line_2: selectedShippingAddress.address_line_2 || '',
          city: selectedShippingAddress.city,
          region: selectedShippingAddress.region || '',
          digital_address: selectedShippingAddress.digital_address || '',
          landmark: selectedShippingAddress.landmark || '',
          delivery_instructions: selectedShippingAddress.delivery_instructions || '',
        }
      : {
          name: user?.first_name ? `${user.first_name} ${user.last_name}` : '',
          phone: user?.phone || '',
          email: user?.personal_email || user?.email || '',
        };

    const url = `${BACKEND_HOST}/payments/api/transactions/unified_checkout/`;
    const payload = {
      cart_items: unifiedCartItems,
      callback_url: `${window.location.origin}/product/payment/callback`,
      shipping_info: shippingInfo,
    };

    const response = await axiosInstance.post(url, payload);

    if (response.data.success) {
      // Store cart state before redirect
      localStorage.setItem(
        "pending_cart_checkout",
        JSON.stringify({
          items: cartItems,
          isUnifiedCheckout: true,
          summary: response.data.summary,
        })
      );
      window.location.href = response.data.payment_url;
    } else {
      throw new Error(response.data.error || "Payment initialization failed");
    }
  };

  // Original merchandise-only checkout
  const handleMerchandiseCheckout = async () => {
    // Prepare cart items for checkout with per-item/per-variant recipient data
    const checkoutItems = cartBySource.merchandise.map((item) => {
      const itemRecipient = item.recipient || globalRecipient;
      
      return {
        product_id: item.product_id,
        quantity: item.quantity,
        variant_selections: (item.variantSelections || []).map((sel) => {
          const effectiveRecipient = sel.recipient || itemRecipient;
          
          return {
            color_id: sel.color_id || null,
            size_id: sel.size_id || null,
            quantity: sel.quantity || 1,
            ...(effectiveRecipient && effectiveRecipient.purchaseType !== "self" && {
              is_gift_purchase: effectiveRecipient.purchaseType === "gift",
              is_purchase_on_behalf: effectiveRecipient.purchaseType === "on_behalf",
              purchased_for_phone: effectiveRecipient.recipientPhone,
              gift_message: effectiveRecipient.purchaseType === "gift" ? effectiveRecipient.giftMessage : null,
            }),
          };
        }),
        ...(itemRecipient && itemRecipient.purchaseType !== "self" && {
          is_gift_purchase: itemRecipient.purchaseType === "gift",
          is_purchase_on_behalf: itemRecipient.purchaseType === "on_behalf",
          purchased_for_phone: itemRecipient.recipientPhone,
          gift_message: itemRecipient.purchaseType === "gift" ? itemRecipient.giftMessage : null,
        }),
      };
    });

    const url = `${BACKEND_HOST}/products/payments/cart_checkout/`;
    const payload = {
      cart_items: checkoutItems,
      gateway: "paystack",
      callback_url: `${window.location.origin}/product/payment/callback`,
    };

    const response = await axiosInstance.post(url, payload);

    if (response.data.success) {
      localStorage.setItem(
        "pending_cart_checkout",
        JSON.stringify(cartItems)
      );
      window.location.href = response.data.payment_url;
    } else {
      throw new Error(response.data.error || "Payment initialization failed");
    }
  };

  const handleClose = () => {
    setOpen(false);
  };

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

      {isProcessing && (
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
              Processing your order...
            </p>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-gray-50 py-8 sm:py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-8 sm:mb-12">
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-3xl sm:text-4xl md:text-5xl mb-3 sm:mb-4 font-bold text-gray-900"
            >
              Shopping{" "}
              <span className="relative text-blue-600">
                Cart
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
              Review your items and proceed to checkout
            </p>
          </div>

          {cartItems.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-lg p-12 text-center"
            >
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <ShoppingCart className="w-10 h-10 text-gray-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Your Cart is Empty
              </h2>
              <p className="text-gray-600 mb-6">
                Add some items to your cart to get started
              </p>
              <a
                href="/purchase-merchandise"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Browse Merchandise
              </a>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8">
              {/* Cart Items */}
              <div className="xl:col-span-2 space-y-4">
                {/* Mixed Cart Banner */}
                {hasMixedCart && (
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white rounded-lg">
                        <ShoppingBag className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800">
                          Mixed Cart Checkout
                        </h3>
                        <p className="text-sm text-gray-600">
                          You have items from both Merchandise and El Mercado. All items will be purchased together in a single checkout.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Merchandise Items */}
                {cartBySource.merchandise.length > 0 && (
                  <>
                    {hasMixedCart && (
                      <div className="flex items-center gap-2 mt-6 mb-3">
                        <Package className="w-5 h-5 text-blue-600" />
                        <h3 className="font-semibold text-gray-800">Merchandise ({cartBySource.merchandise.length})</h3>
                        <span className="text-sm text-gray-500">GH₵{cartTotals.merchandise.toFixed(2)}</span>
                      </div>
                    )}
                    {cartBySource.merchandise.map((item, index) => (
                      <CartItemCard
                        key={item.product_id}
                        item={item}
                        index={index}
                        handleQuantityChange={handleQuantityChange}
                        handleRemove={handleRemove}
                        updateVariantSelections={updateVariantSelections}
                        openItemRecipientModal={openItemRecipientModal}
                        openVariantRecipientModal={openVariantRecipientModal}
                        globalRecipient={globalRecipient}
                        showSourceBadge={hasMixedCart}
                      />
                    ))}
                  </>
                )}

                {/* El Mercado Items - Grouped by Seller */}
                {cartBySource.el_mercado.length > 0 && (
                  <>
                    {hasMixedCart && (
                      <div className="flex items-center gap-2 mt-6 mb-3">
                        <Store className="w-5 h-5 text-purple-600" />
                        <h3 className="font-semibold text-gray-800">El Mercado ({cartBySource.el_mercado.length})</h3>
                        <span className="text-sm text-gray-500">GH₵{cartTotals.el_mercado.toFixed(2)}</span>
                      </div>
                    )}
                    
                    {/* Show multiple sellers notice */}
                    {hasMultipleSellers && (
                      <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-amber-800">
                            Items from {sellerGroups.length} different sellers
                          </p>
                          <p className="text-xs text-amber-700 mt-0.5">
                            You'll receive separate orders from each seller after checkout.
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Render items grouped by seller */}
                    {sellerGroups.map((sellerGroup, groupIndex) => (
                      <div key={sellerGroup.sellerId} className={groupIndex > 0 ? "mt-6" : ""}>
                        {/* Seller Header */}
                        <div className="flex items-center justify-between mb-3 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-100">
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-white rounded-lg shadow-sm">
                              <Store className="w-4 h-4 text-purple-600" />
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="font-semibold text-gray-800 text-sm">
                                  {sellerGroup.sellerName}
                                </span>
                                {sellerGroup.sellerVerified && (
                                  <span className="text-blue-500 text-xs" title="Verified Seller">✓</span>
                                )}
                              </div>
                              <span className="text-xs text-gray-500">
                                {sellerGroup.items.length} item{sellerGroup.items.length > 1 ? 's' : ''}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-semibold text-purple-700">
                              GH₵{sellerGroup.subtotal.toFixed(2)}
                            </span>
                            {hasMultipleSellers && (
                              <p className="text-xs text-gray-500">Separate order</p>
                            )}
                          </div>
                        </div>
                        
                        {/* Seller's Items */}
                        {sellerGroup.items.map((item, index) => (
                          <ElMercadoCartItemCard
                            key={item.listing_id || item.slug || item.id}
                            item={item}
                            index={index}
                            handleQuantityChange={handleQuantityChange}
                            handleRemove={handleRemove}
                            showSourceBadge={hasMixedCart}
                            showSellerName={false}
                          />
                        ))}
                      </div>
                    ))}
                  </>
                )}
              </div>

              {/* Order Summary */}
              <div className="xl:col-span-1">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-xl shadow-lg p-4 sm:p-6 sticky top-20"
                >
                  <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4">
                    Order Summary
                  </h2>

                  <div className="space-y-3 mb-6">
                    {hasMixedCart ? (
                      <>
                        <div className="flex justify-between text-sm sm:text-base text-gray-600">
                          <span className="flex items-center gap-2">
                            <Package className="w-4 h-4 text-blue-500" />
                            Merchandise
                          </span>
                          <span>GH₵{cartTotals.merchandise.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-sm sm:text-base text-gray-600">
                          <span className="flex items-center gap-2">
                            <Store className="w-4 h-4 text-purple-500" />
                            El Mercado
                          </span>
                          <span>GH₵{cartTotals.el_mercado.toFixed(2)}</span>
                        </div>
                      </>
                    ) : (
                      <div className="flex justify-between text-sm sm:text-base text-gray-600">
                        <span>Subtotal</span>
                        <span>GH₵{cartTotals.total.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-sm sm:text-base text-gray-600">
                      <span>Items</span>
                      <span>{cartItems.length}</span>
                    </div>
                    <div className="border-t pt-3">
                      <div className="flex justify-between text-base sm:text-lg font-bold text-gray-900">
                        <span>Total</span>
                        <span className="text-blue-600">
                          GH₵{cartTotals.total.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Shipping Address Selector - Required for El Mercado items */}
                  {user && (cartBySource.el_mercado.length > 0 || hasMixedCart) && (
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-orange-600" />
                        Shipping Address
                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
                          Required
                        </span>
                      </h3>
                      <ShippingAddressSelector
                        selectedAddress={selectedShippingAddress}
                        onAddressSelect={setSelectedShippingAddress}
                        user={user}
                      />
                      {!selectedShippingAddress && (
                        <div className="mt-2 p-3 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
                          <p className="text-xs text-orange-700">
                            A shipping address is required for El Mercado items. Please select or add an address to continue.
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Set Global Recipients Button - Only show for merchandise items */}
                  {cartBySource.merchandise.length > 0 && (
                    <div className="mb-6">
                      <button
                        onClick={openGlobalRecipientModal}
                        className="w-full p-4 bg-gradient-to-br from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border-2 border-purple-200 hover:border-purple-300 rounded-xl text-left transition-all group"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-white rounded-lg group-hover:bg-purple-100 transition">
                              <Gift className="w-5 h-5 text-purple-600" />
                            </div>
                            <div>
                              <h3 className="text-sm font-semibold text-gray-800">
                                Set Recipients for All Items
                              </h3>
                              <p className="text-xs text-gray-600 mt-0.5">
                                {globalRecipient 
                                  ? `${globalRecipient.purchaseType === "gift" ? "Gift" : "On-behalf"} for ${globalRecipient.recipientPhone}`
                                  : "Buy for yourself, as gifts, or on-behalf"}
                              </p>
                            </div>
                          </div>
                          <div className="text-purple-600 group-hover:translate-x-1 transition-transform">
                            →
                          </div>
                        </div>
                      </button>
                      {globalRecipient && (
                        <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Applied to all items without specific recipients
                        </p>
                      )}
                    </div>
                  )}

                  <button
                    onClick={handleCheckout}
                    disabled={isProcessing || !user || (cartBySource.el_mercado.length > 0 && !selectedShippingAddress)}
                    className={`w-full py-3 ${cartBySource.el_mercado.length > 0 && !selectedShippingAddress ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} text-white rounded-lg transition font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base`}
                  >
                    <ShoppingBag className="w-5 h-5" />
                    {cartBySource.el_mercado.length > 0 && !selectedShippingAddress 
                      ? 'Select Shipping Address First'
                      : 'Proceed to Checkout'}
                  </button>

                  {!user && (
                    <p className="text-xs text-center text-red-500 mt-2">
                      Please login to proceed with checkout
                    </p>
                  )}

                  {user && cartBySource.el_mercado.length > 0 && !selectedShippingAddress && (
                    <p className="text-xs text-center text-orange-600 mt-2 flex items-center justify-center gap-1">
                      <MapPin className="w-3 h-3" />
                      Shipping address required for marketplace items
                    </p>
                  )}

                  <button
                    onClick={clearCart}
                    className="w-full mt-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm"
                  >
                    Clear Cart
                  </button>
                </motion.div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recipient Modal */}
      <RecipientModal
        isOpen={recipientModalOpen}
        onClose={() => setRecipientModalOpen(false)}
        onConfirm={handleRecipientConfirm}
        title={recipientModalConfig.title}
        description={recipientModalConfig.description}
        initialData={recipientModalConfig.initialData}
      />
    </>
  );
}

// Sub-component for Merchandise Cart Items
function CartItemCard({
  item,
  index,
  handleQuantityChange,
  handleRemove,
  updateVariantSelections,
  openItemRecipientModal,
  openVariantRecipientModal,
  globalRecipient,
  showSourceBadge,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-md p-4 sm:p-6 hover:shadow-lg transition"
    >
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Product Image */}
        <div className="w-full sm:w-24 h-48 sm:h-24 flex-shrink-0 relative">
          <img
            src={item.product_image}
            alt={item.product_name}
            className="w-full h-full object-cover rounded-lg"
          />
          {showSourceBadge && (
            <div className="absolute top-2 left-2 px-2 py-1 bg-blue-500 text-white text-xs font-semibold rounded-full flex items-center gap-1">
              <Package className="w-3 h-3" />
              Merchandise
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start mb-2 gap-2">
            <div className="min-w-0 flex-1">
              <h3 className="text-base sm:text-lg font-bold text-gray-900 truncate">
                {item.product_name}
              </h3>
              <p className="text-xs sm:text-sm text-gray-600 capitalize">
                {item.type_of_product}
              </p>
            </div>
            <button
              onClick={() => handleRemove(item.product_id, 'merchandise')}
              className="text-red-500 hover:text-red-700 transition flex-shrink-0"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            {/* Quantity Controls */}
            <div className="flex items-center gap-3">
              <button
                onClick={() =>
                  handleQuantityChange(
                    item.product_id,
                    item.quantity - 1,
                    item.stock_quantity,
                    'merchandise'
                  )
                }
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition"
                disabled={item.quantity <= 1}
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-lg font-semibold w-8 text-center">
                {item.quantity}
              </span>
              <button
                onClick={() =>
                  handleQuantityChange(
                    item.product_id,
                    item.quantity + 1,
                    item.stock_quantity,
                    'merchandise'
                  )
                }
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition"
                disabled={item.quantity >= item.stock_quantity}
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Price */}
            <div className="text-left sm:text-right">
              <p className="text-lg font-bold text-blue-600">
                GH₵{(parseFloat(item.price) * item.quantity).toFixed(2)}
              </p>
              <div className="flex flex-col items-start sm:items-end gap-0.5">
                <p className="text-xs text-gray-500">GH₵{item.price} each</p>
                {item.has_discount && item.original_price && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-gray-400 line-through">
                      GH₵{item.original_price}
                    </span>
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                      {item.discount_info?.savings_display}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stock Warning */}
          {item.quantity >= item.stock_quantity && (
            <p className="text-xs text-orange-500 mt-2 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Maximum stock reached
            </p>
          )}

          {/* Variant Selector */}
          {(item.has_colors || item.has_sizes) && (
            <>
              {/* Check if variant data is available */}
              {(item.available_colors?.length > 0 || item.available_sizes?.length > 0) ? (
                <VariantSelector
                  product={item}
                  quantity={item.quantity}
                  initialSelections={item.variantSelections || []}
                  onSelectionsChange={(selections) =>
                    updateVariantSelections(item.product_id, selections, 'merchandise')
                  }
                  onSetVariantRecipient={(variantIndex) =>
                    openVariantRecipientModal(item, variantIndex)
                  }
                />
              ) : (
                <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-xs text-orange-700 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    <span>
                      Variant selection unavailable. Please remove this item and add it again from the product page to select colors/sizes.
                    </span>
                  </p>
                </div>
              )}
            </>
          )}

          {/* Set Recipient for This Item Button */}
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => openItemRecipientModal(item)}
              className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border border-purple-200 rounded-lg text-sm font-medium text-purple-700 transition-all"
            >
              <Gift className="w-4 h-4" />
              Set Recipient
            </button>
            {(item.recipient || globalRecipient) && (
              <div className="flex items-center gap-1 px-2 py-1 bg-green-50 border border-green-200 rounded text-xs font-medium text-green-700">
                {item.recipient ? (
                  <>
                    <Users className="w-3 h-3" />
                    {item.recipient.purchaseType === "gift" ? "Gift" : "On-behalf"}
                  </>
                ) : (
                  <>
                    <Users className="w-3 h-3" />
                    Using global
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Sub-component for El Mercado Cart Items
function ElMercadoCartItemCard({
  item,
  index,
  handleQuantityChange,
  handleRemove,
  showSourceBadge,
  showSellerName = true,
}) {
  // Use the same key logic as CartContext: slug || id (not listing_id first)
  const itemId = item.slug || item.id || item.listing_id;
  const itemName = item.title || item.product_name;
  const itemImage = item.image || item.images?.[0]?.image || item.product_image || item.main_image;
  const itemPrice = parseFloat(item.price);
  const stockQuantity = item.stock_quantity || 999;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-md p-4 sm:p-6 hover:shadow-lg transition border-l-4 border-purple-400"
    >
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Product Image */}
        <div className="w-full sm:w-24 h-48 sm:h-24 flex-shrink-0 relative">
          <img
            src={itemImage}
            alt={itemName}
            className="w-full h-full object-cover rounded-lg"
          />
          {showSourceBadge && (
            <div className="absolute top-2 left-2 px-2 py-1 bg-purple-500 text-white text-xs font-semibold rounded-full flex items-center gap-1">
              <Store className="w-3 h-3" />
              El Mercado
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start mb-2 gap-2">
            <div className="min-w-0 flex-1">
              <h3 className="text-base sm:text-lg font-bold text-gray-900 truncate">
                {itemName}
              </h3>
              {showSellerName && (
                <p className="text-xs sm:text-sm text-gray-600">
                  by {item.seller?.display_name || item.seller?.business_name || item.seller_name || 'Seller'}
                </p>
              )}
              {item.listing_type && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full capitalize">
                  {item.listing_type}
                </span>
              )}
            </div>
            <button
              onClick={() => handleRemove(itemId, 'el_mercado')}
              className="text-red-500 hover:text-red-700 transition flex-shrink-0"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            {/* Quantity Controls */}
            <div className="flex items-center gap-3">
              <button
                onClick={() =>
                  handleQuantityChange(itemId, item.quantity - 1, stockQuantity, 'el_mercado')
                }
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition"
                disabled={item.quantity <= 1}
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-lg font-semibold w-8 text-center">
                {item.quantity}
              </span>
              <button
                onClick={() =>
                  handleQuantityChange(itemId, item.quantity + 1, stockQuantity, 'el_mercado')
                }
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition"
                disabled={item.quantity >= stockQuantity}
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Price */}
            <div className="text-left sm:text-right">
              <p className="text-lg font-bold text-purple-600">
                GH₵{(itemPrice * item.quantity).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">GH₵{itemPrice.toFixed(2)} each</p>
            </div>
          </div>

          {/* Variant info if present */}
          {item.variant_name && (
            <p className="text-xs text-gray-600 mt-2">
              Variant: {item.variant_name}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
