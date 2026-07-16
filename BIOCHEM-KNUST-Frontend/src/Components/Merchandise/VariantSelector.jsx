import { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Check, Gift } from "lucide-react";

export function VariantSelector({
  product,
  quantity,
  initialSelections = [],
  onSelectionsChange,
  onSetVariantRecipient, // NEW: Callback to set recipient for specific variant
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selections, setSelections] = useState([]);
  const prevInitialSelectionsRef = useRef(null);

  // Initialize selections based on quantity and initialSelections
  useEffect(() => {
    // Check if initialSelections actually changed (deep comparison of relevant fields INCLUDING recipient)
    const initialSelectionsKey = JSON.stringify(
      initialSelections.map((s) => ({
        color_id: s.color_id,
        size_id: s.size_id,
        quantity: s.quantity,
        recipient: s.recipient, // Include recipient in change detection
      }))
    );


    if (
      prevInitialSelectionsRef.current === initialSelectionsKey &&
      selections.length === quantity
    ) {
      return; // No changes, skip update
    }

    prevInitialSelectionsRef.current = initialSelectionsKey;

    // Build selections array to match quantity
    let newSelections = [];

    if (
      initialSelections.length > 0 &&
      initialSelections.some((s) => s.color_id || s.size_id)
    ) {
      // Start with normalized initial selections (PRESERVE recipient field)
      const normalizedInitial = initialSelections.map((sel, index) => ({
        id: sel.id ?? index,
        color_id: sel.color_id || null,
        size_id: sel.size_id || null,
        quantity: sel.quantity || 1,
        recipient: sel.recipient || null, // Preserve recipient data
      }));

      if (normalizedInitial.length >= quantity) {
        // More selections than needed, truncate
        newSelections = normalizedInitial.slice(0, quantity);
      } else {
        // Fewer selections than needed, add empty ones for remaining
        newSelections = [...normalizedInitial];
        for (let i = normalizedInitial.length; i < quantity; i++) {
          newSelections.push({
            id: i,
            color_id: null,
            size_id: null,
            quantity: 1,
            recipient: null, // New selections have no recipient
          });
        }
      }
  
    } else {
      // Create empty selections for each item
      newSelections = Array.from({ length: quantity }, (_, index) => ({
        id: index,
        color_id: null,
        size_id: null,
        quantity: 1,
        recipient: null, // Initialize with no recipient
      }));
     
    }

    setSelections(newSelections);

    // Notify parent of the updated selections (important when quantity changes)
    if (onSelectionsChange && newSelections.length > 0) {
      onSelectionsChange(newSelections);
    }
  }, [quantity, initialSelections]);

  // Get available sizes for a specific color (from variant_stock_map)
  const getAvailableSizesForColor = (colorId) => {
    if (!product.variant_stock_map?.sizes_by_color || !colorId) {
      return product.available_sizes || [];
    }
    return product.variant_stock_map.sizes_by_color[colorId] || [];
  };

  // Get available colors for a specific size (from variant_stock_map)
  const getAvailableColorsForSize = (sizeId) => {
    if (!product.variant_stock_map?.colors_by_size || !sizeId) {
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
    const newSelections = selections.map((sel, i) => {
      if (i !== index) return sel;
      
      // When color changes, check if current size is still available
      let newSizeId = sel.size_id;
      if (newSizeId && product.variant_stock_map?.sizes_by_color) {
        const availableSizes = getAvailableSizesForColor(colorId);
        const sizeStillAvailable = availableSizes.some(s => s.id === newSizeId);
        if (!sizeStillAvailable) {
          newSizeId = null;
        }
      }
      
      return { ...sel, color_id: colorId, size_id: newSizeId };
    });
    setSelections(newSelections);
    if (onSelectionsChange) {
      onSelectionsChange(newSelections);
    }
  };

  const handleSizeSelect = (index, sizeId) => {
    const newSelections = selections.map((sel, i) => {
      if (i !== index) return sel;
      
      // When size changes, check if current color is still available
      let newColorId = sel.color_id;
      if (newColorId && product.variant_stock_map?.colors_by_size) {
        const availableColors = getAvailableColorsForSize(sizeId);
        const colorStillAvailable = availableColors.some(c => c.id === newColorId);
        if (!colorStillAvailable) {
          newColorId = null;
        }
      }
      
      return { ...sel, size_id: sizeId, color_id: newColorId };
    });
    setSelections(newSelections);
    if (onSelectionsChange) {
      onSelectionsChange(newSelections);
    }
  };

  const hasVariants = product.has_colors || product.has_sizes;
  const allSelected = selections.every((sel) => {
    const colorSelected = !product.has_colors || sel.color_id;
    const sizeSelected = !product.has_sizes || sel.size_id;
    return colorSelected && sizeSelected;
  });

  if (!hasVariants) {
    return null;
  }

  return (
    <div className="mt-3 border-t pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between text-sm font-medium transition ${
          allSelected ? "text-green-600" : "text-orange-600"
        }`}
      >
        <span className="flex items-center gap-2">
          {allSelected ? (
            <>
              <Check className="w-4 h-4" />
              Variants Selected
            </>
          ) : (
            <>
              ⚠️ Select {product.has_colors ? "Color" : ""}
              {product.has_colors && product.has_sizes ? " & " : ""}
              {product.has_sizes ? "Size" : ""}
            </>
          )}
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-4 max-h-[400px] overflow-y-auto">
              {selections.map((selection, index) => {
                // Get filtered sizes/colors based on current selection
                const displaySizes = selection.color_id
                  ? getAvailableSizesForColor(selection.color_id)
                  : product.available_sizes || [];
                const displayColors = selection.size_id
                  ? getAvailableColorsForSize(selection.size_id)
                  : product.available_colors || [];

                return (
                <div
                  key={selection.id}
                  className="bg-gray-50 rounded-lg p-3 border border-gray-200"
                >
                  <p className="text-xs font-semibold text-gray-700 mb-2">
                    Item #{index + 1}
                  </p>

                  {/* Color Selection */}
                  {product.has_colors &&
                    displayColors?.length > 0 && (
                      <div className="mb-3">
                        <label className="text-xs text-gray-600 mb-1 block">
                          Color:
                          {selection.size_id && displayColors.length < (product.available_colors?.length || 0) && (
                            <span className="ml-1 text-gray-400">
                              (filtered by size)
                            </span>
                          )}
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {displayColors.map((color) => {
                            const hasStock = selection.size_id
                              ? isVariantInStock(color.id, selection.size_id)
                              : true;
                            
                            return (
                            <button
                              key={color.id}
                              onClick={() => handleColorSelect(index, color.id)}
                              disabled={!hasStock}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border-2 ${
                                selection.color_id === color.id
                                  ? "bg-blue-600 text-white border-blue-600"
                                  : !hasStock
                                  ? "bg-gray-100 text-gray-400 border-gray-200 opacity-50 cursor-not-allowed"
                                  : "bg-white text-gray-700 border-gray-300 hover:border-blue-600"
                              }`}
                              style={
                                color.hex_code &&
                                selection.color_id !== color.id &&
                                hasStock
                                  ? { borderColor: color.hex_code }
                                  : {}
                              }
                            >
                              {color.hex_code && (
                                <span
                                  className="inline-block w-3 h-3 rounded-full mr-1"
                                  style={{ backgroundColor: color.hex_code }}
                                />
                              )}
                              {color.name}
                            </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                  {/* Size Selection */}
                  {product.has_sizes && displaySizes?.length > 0 && (
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">
                        Size:
                        {selection.color_id && displaySizes.length < (product.available_sizes?.length || 0) && (
                          <span className="ml-1 text-gray-400">
                            (filtered by color)
                          </span>
                        )}
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {displaySizes.map((size) => {
                          const hasStock = selection.color_id
                            ? isVariantInStock(selection.color_id, size.id)
                            : true;
                          
                          return (
                          <button
                            key={size.id}
                            onClick={() => handleSizeSelect(index, size.id)}
                            disabled={!hasStock}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border-2 ${
                              selection.size_id === size.id
                                ? "bg-blue-600 text-white border-blue-600"
                                : !hasStock
                                ? "bg-gray-100 text-gray-400 border-gray-200 opacity-50 cursor-not-allowed line-through"
                                : "bg-white text-gray-700 border-gray-300 hover:border-blue-600"
                            }`}
                          >
                            {size.code}
                          </button>
                          );
                        })}
                      </div>
                      {selection.color_id && displaySizes.length === 0 && (
                        <p className="mt-1 text-xs text-red-500">
                          No sizes available for selected color
                        </p>
                      )}
                    </div>
                  )}
                  {/* Set Recipient Button for This Variant */}
                  {onSetVariantRecipient && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <button
                        onClick={() => onSetVariantRecipient(index)}
                        className="flex items-center gap-1.5 text-xs text-purple-600 hover:text-purple-700 font-medium"
                      >
                        <Gift className="w-3 h-3" />
                        Set recipient for this variant
                      </button>
                      {selection.recipient && (
                        <span className="text-xs text-green-600 ml-5">
                          ✓ {selection.recipient.purchaseType === "gift" ? "Gift" : "On-behalf"}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

VariantSelector.propTypes = {
  product: PropTypes.shape({
    has_colors: PropTypes.bool,
    has_sizes: PropTypes.bool,
    available_colors: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        hex_code: PropTypes.string,
      })
    ),
    available_sizes: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        code: PropTypes.string.isRequired,
      })
    ),
    // Dynamic variant stock mapping for filtering options
    variant_stock_map: PropTypes.shape({
      sizes_by_color: PropTypes.object,
      colors_by_size: PropTypes.object,
      stock_by_variant: PropTypes.object,
    }),
  }).isRequired,
  quantity: PropTypes.number.isRequired,
  initialSelections: PropTypes.array,
  onSelectionsChange: PropTypes.func,
  onSetVariantRecipient: PropTypes.func, // Optional callback for setting variant-specific recipient
};
