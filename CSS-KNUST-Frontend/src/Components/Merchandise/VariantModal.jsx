import { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  ShoppingCart,
  Check,
  AlertCircle,
  Plus,
  Minus,
  Trash2,
} from "lucide-react";

export function VariantModal({
  isOpen,
  onClose,
  product,
  quantity = 1,
  onConfirm,
  isLoading = false,
  mode = "cart", // "cart", "buy", or "update"
  maxQuantity = 10, // Maximum items that can be added at once
  initialSelections = [], // Pre-populate with existing selections (for update mode)
}) {
  const [selections, setSelections] = useState([]);
  const [error, setError] = useState("");
  const [previewImage, setPreviewImage] = useState(null);
  const [currentQuantity, setCurrentQuantity] = useState(quantity);

  // Purchase type state (only for "buy" mode)
  const [purchaseType, setPurchaseType] = useState("self"); // "self", "gift", or "on_behalf"
  const [recipientPhone, setRecipientPhone] = useState("");
  const [giftMessage, setGiftMessage] = useState("");

  // Initialize selections when modal opens
  // Use stable values in dependencies to avoid infinite re-renders
  const productName = product?.product_name;
  const productImage = product?.product_image;
  const availableColors = product?.available_colors;
  const stockQuantity = product?.stock_quantity;
  const initialSelectionsLength = initialSelections?.length || 0;

  useEffect(() => {
    if (isOpen) {
     
      
      // Check if we have initial selections to pre-populate (for update mode)
      if (initialSelections && initialSelections.length > 0) {
        // Normalize and use existing selections
        const normalizedSelections = initialSelections.map((sel, index) => ({
          id: index,
          color_id: sel.color_id || sel.color?.id || null,
          size_id: sel.size_id || sel.size?.id || null,
          quantity: sel.quantity || 1,
        }));
        

        setSelections(normalizedSelections);
        setCurrentQuantity(normalizedSelections.length);
        
        // Set preview image based on first selection's color
        const firstColorId = normalizedSelections[0]?.color_id;
        if (firstColorId && availableColors) {
          const selectedColor = availableColors.find(c => c.id === firstColorId);
          if (selectedColor?.image_url) {
            setPreviewImage(selectedColor.image_url);
          } else {
            setPreviewImage(productImage);
          }
        } else {
          setPreviewImage(productImage);
        }
      } else {
        // Create empty selections for new items
        const initialQuantity = quantity || 1;
        setCurrentQuantity(initialQuantity);
        const emptySelections = Array.from(
          { length: initialQuantity },
          (_, index) => ({
            id: index,
            color_id: null,
            size_id: null,
            quantity: 1,
          })
        );
        setSelections(emptySelections);
        
        // Set initial preview image
        if (productImage) {
          setPreviewImage(productImage);
        } else if (availableColors?.[0]?.image_url) {
          setPreviewImage(availableColors[0].image_url);
        }
      }
      
      setError("");
    }
  }, [isOpen, quantity, productName, productImage, availableColors, initialSelectionsLength, mode]);

  // Add a new item selection
  const handleAddItem = () => {
    if (currentQuantity >= maxQuantity) {
      setError(`Maximum ${maxQuantity} items can be added at once`);
      return;
    }
    if (product.stock_quantity && currentQuantity >= product.stock_quantity) {
      setError(`Only ${product.stock_quantity} items available in stock`);
      return;
    }

    const newId =
      selections.length > 0 ? Math.max(...selections.map((s) => s.id)) + 1 : 0;
    setSelections((prev) => [
      ...prev,
      {
        id: newId,
        color_id: null,
        size_id: null,
        quantity: 1,
      },
    ]);
    setCurrentQuantity((prev) => prev + 1);
    setError("");
  };

  // Remove an item selection
  const handleRemoveItem = (index) => {
    if (selections.length <= 1) {
      setError("At least one item is required");
      return;
    }
    setSelections((prev) => prev.filter((_, i) => i !== index));
    setCurrentQuantity((prev) => prev - 1);
    setError("");
  };

  // Get available sizes for a specific color (from variant_stock_map)
  const getAvailableSizesForColor = (colorId) => {
    if (!product.variant_stock_map?.sizes_by_color || !colorId) {
      // Fall back to all available sizes if no stock map
      return product.available_sizes || [];
    }
    return product.variant_stock_map.sizes_by_color[colorId] || [];
  };

  // Get available colors for a specific size (from variant_stock_map)
  const getAvailableColorsForSize = (sizeId) => {
    if (!product.variant_stock_map?.colors_by_size || !sizeId) {
      // Fall back to all available colors if no stock map
      return product.available_colors || [];
    }
    return product.variant_stock_map.colors_by_size[sizeId] || [];
  };

  // Check if a specific color+size combination is in stock
  const isVariantInStock = (colorId, sizeId) => {
    if (!product.variant_stock_map?.stock_by_variant) return true;
    const key = `${colorId || 'no_color'}:${sizeId || 'no_size'}`;
    const variant = product.variant_stock_map.stock_by_variant[key];
    return variant ? variant.available > 0 : false;
  };

  const handleColorSelect = (index, colorId) => {
    setSelections((prev) =>
      prev.map((sel, i) => {
        if (i !== index) return sel;
        
        // When color changes, check if current size is still available for this color
        let newSizeId = sel.size_id;
        if (newSizeId && product.variant_stock_map?.sizes_by_color) {
          const availableSizes = getAvailableSizesForColor(colorId);
          const sizeStillAvailable = availableSizes.some(s => s.id === newSizeId);
          if (!sizeStillAvailable) {
            newSizeId = null; // Reset size if not available for new color
          }
        }
        
        return { ...sel, color_id: colorId, size_id: newSizeId };
      })
    );
    setError("");

    // Update preview image when color is selected
    const selectedColor = product.available_colors?.find(
      (c) => c.id === colorId
    );
    if (selectedColor?.image_url) {
      setPreviewImage(selectedColor.image_url);
    }
  };

  const handleSizeSelect = (index, sizeId) => {
    setSelections((prev) =>
      prev.map((sel, i) => {
        if (i !== index) return sel;
        
        // When size changes, check if current color is still available for this size
        let newColorId = sel.color_id;
        if (newColorId && product.variant_stock_map?.colors_by_size) {
          const availableColors = getAvailableColorsForSize(sizeId);
          const colorStillAvailable = availableColors.some(c => c.id === newColorId);
          if (!colorStillAvailable) {
            newColorId = null; // Reset color if not available for new size
          }
        }
        
        return { ...sel, size_id: sizeId, color_id: newColorId };
      })
    );
    setError("");
  };

  const validateSelections = () => {
    for (let i = 0; i < selections.length; i++) {
      const sel = selections[i];
      if (product.has_colors && !sel.color_id) {
        setError(`Please select a color for Item #${i + 1}`);
        return false;
      }
      if (product.has_sizes && !sel.size_id) {
        setError(`Please select a size for Item #${i + 1}`);
        return false;
      }
    }

    // Validate purchase type phone number
    if (mode === "buy" && purchaseType !== "self" && !recipientPhone.trim()) {
      setError(`Please enter recipient's phone number for ${purchaseType === "gift" ? "gift" : "on-behalf"} purchase`);
      return false;
    }

    return true;
  };

  const handleConfirm = () => {
    if (validateSelections()) {
     
      // Pass purchase type data along with selections (only in buy mode)
      onConfirm(selections, mode === "buy" && purchaseType !== "self" ? {
        isGiftPurchase: purchaseType === "gift",
        isPurchaseOnBehalf: purchaseType === "on_behalf",
        recipientPhone,
        giftMessage: purchaseType === "gift" ? giftMessage : null,
      } : null);
      onClose();
    }
  };

  // Calculate total price (price is already discounted from backend)
  const totalPrice = product.price
    ? (parseFloat(product.price) * currentQuantity).toFixed(2)
    : null;
  
  // Calculate original total if discount applies
  const originalTotalPrice = product.original_price
    ? (parseFloat(product.original_price) * currentQuantity).toFixed(2)
    : null;

  // Check if all items have complete selections
  const allComplete = selections.every((sel) => {
    const colorOk = !product.has_colors || sel.color_id;
    const sizeOk = !product.has_sizes || sel.size_id;
    return colorOk && sizeOk;
  });

  const hasVariants = product.has_colors || product.has_sizes;

  // Always show modal in "buy" mode (for purchase type selection), even without variants
  // Only show if product has variants in other modes
  if (!isOpen || (!hasVariants && mode !== "buy")) {
    return null;
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[95vh] sm:max-h-[90vh] flex flex-col"
        >
          {/* Header - flex-shrink-0 to prevent shrinking */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 sm:p-6 flex-shrink-0">
            <div className="flex justify-between items-start">
              <div className="flex-1 min-w-0 pr-2">
                <h2 className="text-lg sm:text-2xl font-bold mb-1">
                  {hasVariants ? "Select Your Preferences" : "Purchase Options"}
                </h2>
                <p className="text-blue-100 text-xs sm:text-sm truncate">{product.product_name}</p>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:bg-white/20 rounded-lg p-1.5 sm:p-2 transition flex-shrink-0"
              >
                <X className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>

            {/* Quantity Controls in Header */}
            <div className="mt-3 sm:mt-4 flex flex-wrap items-center justify-between gap-2 bg-white/10 rounded-xl p-2 sm:p-3">
              <span className="text-xs sm:text-sm font-medium">
                Items: {currentQuantity}
              </span>
              <div className="flex items-center gap-2 sm:gap-3">
                <button
                  onClick={() => handleRemoveItem(selections.length - 1)}
                  disabled={currentQuantity <= 1}
                  className="p-1.5 sm:p-2 rounded-lg bg-white/20 hover:bg-white/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Minus className="w-3 h-3 sm:w-4 sm:h-4" />
                </button>
                <span className="text-lg sm:text-xl font-bold min-w-[1.5rem] sm:min-w-[2rem] text-center">
                  {currentQuantity}
                </span>
                <button
                  onClick={handleAddItem}
                  disabled={
                    currentQuantity >= maxQuantity ||
                    (product.stock_quantity &&
                      currentQuantity >= product.stock_quantity)
                  }
                  className="p-1.5 sm:p-2 rounded-lg bg-white/20 hover:bg-white/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
                </button>
              </div>
              {totalPrice && (
                <div className="flex flex-col items-end">
                  <span className="text-xs sm:text-sm font-semibold">
                    GHS {totalPrice}
                  </span>
                  {product.has_discount && originalTotalPrice && (
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-white/60 line-through">
                        GHS {originalTotalPrice}
                      </span>
                      <span className="text-xs bg-green-400/20 text-green-200 px-1 py-0.5 rounded text-[10px]">
                        {product.discount_info?.savings_display}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Content - flex-1 to take remaining space, overflow-y-auto for scrolling */}
          <div className="p-3 sm:p-6 overflow-y-auto flex-1 min-h-0">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Image Preview */}
            {previewImage && (
              <div className="mb-6 bg-gray-100 rounded-2xl overflow-hidden border-2 border-gray-200">
                <div className="relative aspect-[4/3] w-full">
                  <img
                    src={previewImage}
                    alt={product.product_name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                </div>
              </div>
            )}

            {/* Selections */}
            <div className="space-y-4">
              {selections.map((selection, index) => {
                const isComplete =
                  (!product.has_colors || selection.color_id) &&
                  (!product.has_sizes || selection.size_id);
                
                // Get filtered sizes based on selected color
                const filteredSizes = selection.color_id && product.variant_stock_map?.sizes_by_color
                  ? getAvailableSizesForColor(selection.color_id)
                  : product.available_sizes || [];
                
                // Get filtered colors based on selected size
                const filteredColors = selection.size_id && product.variant_stock_map?.colors_by_size
                  ? getAvailableColorsForSize(selection.size_id)
                  : product.available_colors || [];
                
                // For display, use filtered list if we have a selection, otherwise show all
                const displayColors = selection.size_id ? filteredColors : (product.available_colors || []);
                const displaySizes = selection.color_id ? filteredSizes : (product.available_sizes || []);

                return (
                  <motion.div
                    key={selection.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`bg-gray-50 rounded-xl p-5 border-2 transition-colors ${
                      isComplete ? "border-green-300" : "border-gray-200"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold text-gray-900">
                          Item #{index + 1}
                        </h3>
                        {isComplete && (
                          <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full flex items-center gap-1">
                            <Check className="w-3 h-3" /> Complete
                          </span>
                        )}
                      </div>
                      {selections.length > 1 && (
                        <button
                          onClick={() => handleRemoveItem(index)}
                          className="text-red-500 hover:bg-red-50 rounded-lg p-2 transition"
                          title="Remove this item"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>

                    {/* Color Selection */}
                    {product.has_colors &&
                      displayColors?.length > 0 && (
                        <div className="mb-5">
                          <label className="block text-sm font-semibold text-gray-700 mb-3">
                            Choose Color:{" "}
                            <span className="text-red-500">*</span>
                            {selection.size_id && displayColors.length < (product.available_colors?.length || 0) && (
                              <span className="ml-2 text-xs text-gray-500 font-normal">
                                (showing colors available in selected size)
                              </span>
                            )}
                          </label>
                          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            {displayColors.map((color) => {
                              // Check stock for this color + current size combination
                              const hasStockForSelection = selection.size_id
                                ? isVariantInStock(color.id, selection.size_id)
                                : true;
                              
                              return (
                                <button
                                  key={color.id}
                                  onClick={() =>
                                    handleColorSelect(index, color.id)
                                  }
                                  disabled={!hasStockForSelection}
                                  className={`group relative px-3 py-2 rounded-lg text-sm font-medium transition-all border-2 ${
                                    selection.color_id === color.id
                                      ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                                      : !hasStockForSelection
                                      ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed opacity-50"
                                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:shadow-md"
                                  }`}
                                >
                                <div className="flex items-center justify-center gap-2">
                                  {color.hex_code && (
                                    <span
                                      className="w-4 h-4 rounded-full border-2 border-white shadow-sm flex-shrink-0"
                                      style={{
                                        backgroundColor: color.hex_code,
                                      }}
                                    />
                                  )}
                                  <span className="truncate text-xs">
                                    {color.name}
                                  </span>
                                </div>
                                {selection.color_id === color.id && (
                                  <Check className="absolute top-0.5 right-0.5 w-3 h-3" />
                                )}
                              </button>
                              );
                            })}
                          </div>
                        </div>
                      )}

                    {/* Size Selection */}
                    {product.has_sizes &&
                      displaySizes?.length > 0 && (
                        <div>
                          <label className="block text-sm font-semibold text-gray-700 mb-3">
                            Choose Size: <span className="text-red-500">*</span>
                            {selection.color_id && displaySizes.length < (product.available_sizes?.length || 0) && (
                              <span className="ml-2 text-xs text-gray-500 font-normal">
                                (showing sizes available in selected color)
                              </span>
                            )}
                          </label>
                          <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
                            {displaySizes.map((size) => {
                              // Check stock for this size + current color combination
                              const hasStockForSelection = selection.color_id
                                ? isVariantInStock(selection.color_id, size.id)
                                : true;
                              
                              return (
                                <button
                                  key={size.id}
                                  onClick={() => handleSizeSelect(index, size.id)}
                                  disabled={!hasStockForSelection}
                                  className={`relative px-3 py-2 rounded-lg text-sm font-bold transition-all border-2 ${
                                    selection.size_id === size.id
                                      ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                                      : !hasStockForSelection
                                      ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed opacity-50 line-through"
                                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:shadow-md"
                                  }`}
                                >
                                  {size.code}
                                  {selection.size_id === size.id && (
                                    <Check className="absolute top-0.5 right-0.5 w-3 h-3" />
                                  )}
                                </button>
                              );
                            })}
                          </div>
                          {/* Show "no sizes available" message if color selected but no sizes in stock */}
                          {selection.color_id && displaySizes.length === 0 && (
                            <p className="mt-2 text-sm text-red-500">
                              No sizes available for the selected color
                            </p>
                          )}
                        </div>
                      )}
                  </motion.div>
                );
              })}

              {/* Add Another Item Button */}
              {mode === "cart" && (
                <button
                  onClick={handleAddItem}
                  disabled={
                    currentQuantity >= maxQuantity ||
                    (product.stock_quantity &&
                      currentQuantity >= product.stock_quantity)
                  }
                  className="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 font-medium hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-gray-300 disabled:hover:text-gray-600 disabled:hover:bg-transparent"
                >
                  <Plus className="w-5 h-5" />
                  Add Another Item with Different Variant
                </button>
              )}

              {/* Purchase Type Section (only for "buy" mode) */}
              {mode === "buy" && (
                <div className="mt-6 p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border-2 border-purple-200">
                  <h3 className="text-sm font-semibold text-gray-800 mb-3">
                    Who is this purchase for?
                  </h3>
                  
                  <div className="space-y-2">
                    {/* For Myself */}
                    <label className="flex items-start space-x-3 cursor-pointer group p-2.5 rounded-lg hover:bg-white/50 transition">
                      <input
                        type="radio"
                        name="purchaseType"
                        value="self"
                        checked={purchaseType === "self"}
                        onChange={() => {
                          setPurchaseType("self");
                          setRecipientPhone("");
                          setGiftMessage("");
                          setError("");
                        }}
                        className="w-4 h-4 text-blue-600 mt-0.5"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-800 block">
                          👤 For Myself
                        </span>
                        <span className="text-xs text-gray-500">
                          Standard purchase
                        </span>
                      </div>
                    </label>

                    {/* As Gift */}
                    <label className="flex items-start space-x-3 cursor-pointer group p-2.5 rounded-lg hover:bg-white/50 transition">
                      <input
                        type="radio"
                        name="purchaseType"
                        value="gift"
                        checked={purchaseType === "gift"}
                        onChange={() => setPurchaseType("gift")}
                        className="w-4 h-4 text-pink-600 mt-0.5"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-800 block">
                          🎁 As a Gift
                        </span>
                        <span className="text-xs text-gray-500">
                          Send as a present with optional message
                        </span>
                      </div>
                    </label>

                    {/* On Behalf Of */}
                    <label className="flex items-start space-x-3 cursor-pointer group p-2.5 rounded-lg hover:bg-white/50 transition">
                      <input
                        type="radio"
                        name="purchaseType"
                        value="on_behalf"
                        checked={purchaseType === "on_behalf"}
                        onChange={() => {
                          setPurchaseType("on_behalf");
                          setGiftMessage(""); // Clear gift message
                          setError("");
                        }}
                        className="w-4 h-4 text-purple-600 mt-0.5"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-800 block">
                          🤝 Buying on Behalf
                        </span>
                        <span className="text-xs text-gray-500">
                          Purchasing for someone (they requested it)
                        </span>
                      </div>
                    </label>
                  </div>

                  {/* Recipient Details */}
                  {purchaseType !== "self" && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4 space-y-3 border-t border-purple-200 pt-4"
                    >
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                          Recipient's Phone Number *
                        </label>
                        <input
                          type="tel"
                          value={recipientPhone}
                          onChange={(e) => {
                            setRecipientPhone(e.target.value);
                            setError("");
                          }}
                          placeholder="+233 24 123 4567"
                          required={purchaseType !== "self"}
                          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                        />
                        <p className="text-xs text-gray-500 mt-1.5 flex items-start gap-1">
                          <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          {purchaseType === "gift"
                            ? "The recipient will see this purchase in their dashboard when they register"
                            : "They will be able to collect this purchase using their phone number"}
                        </p>
                      </div>

                      {/* Gift Message - Only for gifts */}
                      {purchaseType === "gift" && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Gift Message (Optional)
                          </label>
                          <textarea
                            value={giftMessage}
                            onChange={(e) => setGiftMessage(e.target.value)}
                            placeholder="Add a personal message for the recipient..."
                            rows={3}
                            maxLength={500}
                            className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent text-sm resize-none"
                          />
                          <p className="text-xs text-gray-400 mt-1 text-right">
                            {giftMessage.length}/500
                          </p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Footer - flex-shrink-0 to prevent shrinking, sticky at bottom */}
          <div className="border-t bg-gray-50 p-3 sm:p-4 flex-shrink-0">
            {/* Summary */}
            <div className="flex items-center justify-between mb-3 text-xs sm:text-sm">
              <span className="text-gray-600">
                {currentQuantity} item{currentQuantity > 1 ? "s" : ""}
              </span>
              <span
                className={`font-medium ${
                  allComplete ? "text-green-600" : "text-orange-500"
                }`}
              >
                {allComplete
                  ? "✓ Ready"
                  : `${
                      selections.filter(
                        (s) =>
                          (!product.has_colors || s.color_id) &&
                          (!product.has_sizes || s.size_id)
                      ).length
                    }/${currentQuantity} done`}
              </span>
            </div>

            <div className="flex gap-2 sm:gap-3">
              <button
                onClick={onClose}
                disabled={isLoading}
                className="flex-1 px-3 sm:px-6 py-2.5 sm:py-3 bg-gray-200 text-gray-700 rounded-xl text-sm sm:text-base font-semibold hover:bg-gray-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={isLoading || !allComplete}
                className="flex-1 px-3 sm:px-6 py-2.5 sm:py-3 bg-blue-600 text-white rounded-xl text-sm sm:text-base font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-1 sm:gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShoppingCart className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="truncate">
                  {isLoading
                    ? mode === "update"
                      ? "Updating..."
                      : mode === "buy"
                      ? "Processing..."
                      : "Adding..."
                    : mode === "update"
                    ? "Update"
                    : mode === "buy"
                    ? `Buy (${currentQuantity})`
                    : `Add (${currentQuantity})`}
                </span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

VariantModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  product: PropTypes.shape({
    product_name: PropTypes.string.isRequired,
    product_image: PropTypes.string,
    price: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    stock_quantity: PropTypes.number,
    has_colors: PropTypes.bool,
    has_sizes: PropTypes.bool,
    available_colors: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        hex_code: PropTypes.string,
        image_url: PropTypes.string,
      })
    ),
    available_sizes: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        code: PropTypes.string.isRequired,
      })
    ),
    // Dynamic variant stock mapping for filtering
    variant_stock_map: PropTypes.shape({
      sizes_by_color: PropTypes.objectOf(
        PropTypes.arrayOf(
          PropTypes.shape({
            id: PropTypes.string.isRequired,
            name: PropTypes.string,
            code: PropTypes.string,
            stock: PropTypes.number,
          })
        )
      ),
      colors_by_size: PropTypes.objectOf(
        PropTypes.arrayOf(
          PropTypes.shape({
            id: PropTypes.string.isRequired,
            name: PropTypes.string,
            hex_code: PropTypes.string,
            stock: PropTypes.number,
          })
        )
      ),
      stock_by_variant: PropTypes.objectOf(
        PropTypes.shape({
          stock: PropTypes.number,
          available: PropTypes.number,
          is_low: PropTypes.bool,
        })
      ),
    }),
  }).isRequired,
  quantity: PropTypes.number,
  onConfirm: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
  mode: PropTypes.oneOf(["cart", "buy", "update"]),
  maxQuantity: PropTypes.number,
  initialSelections: PropTypes.arrayOf(
    PropTypes.shape({
      color_id: PropTypes.string,
      size_id: PropTypes.string,
      color: PropTypes.shape({
        id: PropTypes.string,
        name: PropTypes.string,
        hex_code: PropTypes.string,
      }),
      size: PropTypes.shape({
        id: PropTypes.string,
        name: PropTypes.string,
        code: PropTypes.string,
      }),
      quantity: PropTypes.number,
    })
  ),
};
