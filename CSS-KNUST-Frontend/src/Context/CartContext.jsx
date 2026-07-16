import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import PropTypes from "prop-types";

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState(() => {
    // Load cart from localStorage on initialization
    const savedCart = localStorage.getItem("cart");
    return savedCart ? JSON.parse(savedCart) : [];
  });

  // Global recipient info (applies to all items by default)
  const [globalRecipient, setGlobalRecipient] = useState(null);

  // Floating cart preview visibility state
  const [showFloatingCart, setShowFloatingCart] = useState(true);

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("cart", JSON.stringify(cartItems));
  }, [cartItems]);

  /**
   * Determine the source of a product
   * @param {Object} product - Product data
   * @returns {'merchandise' | 'el_mercado'} Source identifier
   */
  const getProductSource = useCallback((product) => {
    // Merchandise products have product_id as UUID and type_of_product field
    if (product.product_id && product.type_of_product) {
      return 'merchandise';
    }
    // El Mercado listings have listing_type (PRODUCT, SERVICE, DIGITAL)
    if (product.listing_type || product.seller) {
      return 'el_mercado';
    }
    // Fallback: check if product_id looks like a merchandise UUID
    if (product.product_id && typeof product.product_id === 'string' && product.product_id.includes('-')) {
      return 'merchandise';
    }
    // Default to el_mercado for new listings
    return 'el_mercado';
  }, []);

  const addToCart = useCallback((product, quantity = 1) => {
    setCartItems((prevItems) => {
      // Determine source first
      const source = getProductSource(product);
      
      // Determine unique identifier based on source
      const productKey = source === 'merchandise' 
        ? product.product_id 
        : (product.slug || product.id);
      
      const existingItem = prevItems.find((item) => {
        const itemKey = item.source === 'merchandise' 
          ? item.product_id 
          : (item.slug || item.id);
        return itemKey === productKey && item.source === source;
      });

      // Normalize product data for cart storage
      const normalizedProduct = {
        // Core identification
        product_id: source === 'merchandise' ? product.product_id : null,
        listing_id: source === 'el_mercado' ? (product.id || product.listing_id) : null,
        id: product.id || product.product_id,
        slug: product.slug,
        
        // Product details
        product_name: product.product_name || product.title,
        title: product.title || product.product_name,
        price: product.price,
        currency: product.currency || 'GHS',
        
        // Images
        product_image: product.product_image || product.main_image_url || product.main_image,
        main_image: product.main_image || product.main_image_url || product.product_image,
        
        // Stock & availability
        stock_quantity: product.stock_quantity,
        is_available_for_purchase: product.is_available_for_purchase !== undefined 
          ? product.is_available_for_purchase 
          : (product.is_in_stock !== undefined ? product.is_in_stock : true),
        
        // Variants (for both systems)
        variantSelections: product.variantSelections || [],
        selectedVariant: product.selectedVariant || null,
        variants: product.variants || [],
        
        // Merchandise-specific variant data (CRITICAL for VariantSelector)
        has_colors: product.has_colors || false,
        has_sizes: product.has_sizes || false,
        available_colors: product.available_colors || [],
        available_sizes: product.available_sizes || [],
        variant_stock_map: product.variant_stock_map || null,
        type_of_product: product.type_of_product || null,
        
        // Discount info (for display)
        has_discount: product.has_discount || false,
        original_price: product.original_price || null,
        discount_info: product.discount_info || null,
        
        // El Mercado-specific
        listing_type: product.listing_type || null,
        seller: product.seller || null,
        seller_id: product.seller?.id || product.seller_id || null,
        // Store seller name explicitly for easier access (display_name is primary from backend)
        seller_name: product.seller?.display_name || product.seller?.business_name || product.seller_name || null,
        
        // Source identifier (CRITICAL for routing)
        source: source,
      };

      if (existingItem) {
        // Update quantity and merge variant selections if item already exists
        const newVariantSelections = normalizedProduct.variantSelections || [];
        const existingVariantSelections = existingItem.variantSelections || [];

        // Merge variant selections: keep existing ones and add new ones
        const mergedSelections = [
          ...existingVariantSelections,
          ...newVariantSelections.map((sel, idx) => ({
            ...sel,
            id: existingVariantSelections.length + idx, // Ensure unique IDs
          })),
        ];


        return prevItems.map((item) => {
          const itemKey = item.source === 'merchandise' 
            ? item.product_id 
            : (item.slug || item.id);
          return itemKey === productKey && item.source === source
            ? {
                ...item,
                quantity: item.quantity + quantity,
                variantSelections: mergedSelections,
              }
            : item;
        });
      } else {
        // Add new item with variant selections from product or empty array
        console.log("🛒 Adding new cart item:", {
          productName: normalizedProduct.product_name,
          source: normalizedProduct.source,
          quantity,
          variantSelections: normalizedProduct.variantSelections,
        });
        return [
          ...prevItems,
          {
            ...normalizedProduct,
            quantity,
          },
        ];
      }
    });
  }, [getProductSource]);

  const updateVariantSelections = useCallback(
    (itemId, variantSelections, source = 'merchandise') => {
      console.log("🛒 Updating variant selections in cart:", {
        itemId,
        source,
        variantSelections,
      });
      setCartItems((prevItems) =>
        prevItems.map((item) => {
          const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
          return itemKey === itemId && item.source === source
            ? { ...item, variantSelections } 
            : item;
        })
      );
    },
    []
  );

  const removeFromCart = useCallback((itemId, source = null) => {
    console.log("🗑️ Removing from cart:", { itemId, source });
    setCartItems((prevItems) => {
      console.log("🗑️ Current items before removal:", prevItems.map(item => ({
        key: item.source === 'merchandise' ? item.product_id : (item.slug || item.id),
        source: item.source,
        name: item.product_name || item.title
      })));
      
      return prevItems.filter((item) => {
        const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
        // If source is provided, match both; otherwise just match the key
        if (source) {
          return !(itemKey === itemId && item.source === source);
        }
        return itemKey !== itemId;
      });
    });
  }, []);

  const updateQuantity = useCallback(
    (itemId, quantity, source = null) => {
      if (quantity <= 0) {
        removeFromCart(itemId, source);
        return;
      }

      setCartItems((prevItems) =>
        prevItems.map((item) => {
          const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
          const matchesItem = source 
            ? (itemKey === itemId && item.source === source)
            : (itemKey === itemId);
          
          return matchesItem
            ? { ...item, quantity: Math.min(quantity, item.stock_quantity || 999) }
            : item;
        })
      );
    },
    [removeFromCart]
  );

  const clearCart = useCallback(() => {
    setCartItems([]);
  }, []);

  const getCartTotal = useCallback(() => {
    return cartItems.reduce(
      (total, item) => total + parseFloat(item.price) * item.quantity,
      0
    );
  }, [cartItems]);

  const getCartCount = useCallback(() => {
    return cartItems.reduce((count, item) => count + item.quantity, 0);
  }, [cartItems]);

  /**
   * Get cart items grouped by source
   * @returns {{ merchandise: Array, el_mercado: Array }}
   */
  const getCartItemsBySource = useCallback(() => {
    return {
      merchandise: cartItems.filter(item => item.source === 'merchandise'),
      el_mercado: cartItems.filter(item => item.source === 'el_mercado'),
    };
  }, [cartItems]);

  /**
   * Get totals by source
   * @returns {{ merchandise: number, el_mercado: number, total: number }}
   */
  const getCartTotalsBySource = useCallback(() => {
    const groups = getCartItemsBySource();
    const merchandiseTotal = groups.merchandise.reduce(
      (total, item) => total + parseFloat(item.price) * item.quantity, 0
    );
    const elMercadoTotal = groups.el_mercado.reduce(
      (total, item) => total + parseFloat(item.price) * item.quantity, 0
    );
    return {
      merchandise: merchandiseTotal,
      el_mercado: elMercadoTotal,
      total: merchandiseTotal + elMercadoTotal,
    };
  }, [getCartItemsBySource]);

  const isInCart = useCallback(
    (itemId, source = null) => {
      return cartItems.some((item) => {
        const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
        if (source) {
          return itemKey === itemId && item.source === source;
        }
        return itemKey === itemId;
      });
    },
    [cartItems]
  );

  const getCartItemQuantity = useCallback(
    (itemId, source = null) => {
      const item = cartItems.find((item) => {
        const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
        if (source) {
          return itemKey === itemId && item.source === source;
        }
        return itemKey === itemId;
      });
      return item ? item.quantity : 0;
    },
    [cartItems]
  );

  // ========== Recipient Management Methods ==========
  
  /**
   * Set global recipient for ALL items in cart
   * @param {Object|null} recipientData - { purchaseType, recipientPhone, giftMessage } or null to clear
   */
  const setGlobalRecipientInfo = useCallback((recipientData) => {
    setGlobalRecipient(recipientData);
  }, []);

  /**
   * Set recipient for a specific cart item
   * @param {string} itemId - Product ID or listing slug
   * @param {Object|null} recipientData - { purchaseType, recipientPhone, giftMessage } or null to clear
   * @param {string} source - 'merchandise' or 'el_mercado'
   */
  const setItemRecipient = useCallback((itemId, recipientData, source = null) => {
    setCartItems((prevItems) =>
      prevItems.map((item) => {
        const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
        const matches = source 
          ? (itemKey === itemId && item.source === source)
          : (itemKey === itemId);
        return matches
          ? { ...item, recipient: recipientData }
          : item;
      })
    );
  }, []);

  /**
   * Set recipient for a specific variant within an item
   * @param {string} itemId - Product ID or listing slug
   * @param {number} variantIndex - Index of variant in variantSelections array
   * @param {Object|null} recipientData - { purchaseType, recipientPhone, giftMessage } or null to clear
   * @param {string} source - 'merchandise' or 'el_mercado'
   */
  const setVariantRecipient = useCallback((itemId, variantIndex, recipientData, source = null) => {
    setCartItems((prevItems) =>
      prevItems.map((item) => {
        const itemKey = item.source === 'merchandise' ? item.product_id : (item.slug || item.id);
        const matches = source 
          ? (itemKey === itemId && item.source === source)
          : (itemKey === itemId);
        
        if (matches && item.variantSelections) {
          const updatedSelections = item.variantSelections.map((sel, idx) =>
            idx === variantIndex
              ? { ...sel, recipient: recipientData }
              : sel
          );
          return { ...item, variantSelections: updatedSelections };
        }
        return item;
      })
    );
  }, []);

  /**
   * Get effective recipient for an item (considering hierarchy: variant > item > global)
   * @param {Object} item - Cart item
   * @param {number} variantIndex - Optional variant index
   * @returns {Object|null} Recipient data or null
   */
  const getEffectiveRecipient = useCallback((item, variantIndex = null) => {
    // Priority: variant-level > item-level > global
    if (variantIndex !== null && item.variantSelections?.[variantIndex]?.recipient) {
      return item.variantSelections[variantIndex].recipient;
    }
    if (item.recipient) {
      return item.recipient;
    }
    return globalRecipient;
  }, [globalRecipient]);

  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        removeFromCart,
        updateQuantity,
        updateVariantSelections,
        clearCart,
        getCartTotal,
        getCartCount,
        isInCart,
        getCartItemQuantity,
        // Recipient management
        globalRecipient,
        setGlobalRecipientInfo,
        setItemRecipient,
        setVariantRecipient,
        getEffectiveRecipient,
        // Unified cart methods for dual-source support
        getCartItemsBySource,
        getCartTotalsBySource,
        getProductSource,
        // Floating cart visibility control
        showFloatingCart,
        setShowFloatingCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

CartProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
