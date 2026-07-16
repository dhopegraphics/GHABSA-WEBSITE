import { useContext, useState, useEffect } from "react";
import {
  ShoppingBag,
  Tag,
  Clock,
  AlertCircle,
  ShoppingCart,
  ChevronLeft,
  ChevronRight,
  X,
  Lock,
  Users,
 
} from "lucide-react";
import { Oval } from "react-loader-spinner";
import { UserContext } from "../../Context/UserContext";
import { useCart } from "../../Context/CartContext";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../../utils/config";
import PropTypes from "prop-types";
import { VariantModal } from "./VariantModal";
import { normalizePhoneNumber } from "../../utils/phoneUtils";

export function MerchandiseCard({
  product_image,
  product_name,
  type_of_product,
  price,
  product_id,
  stock_quantity,
  status,
  availability_message,
  is_available_for_purchase,
  is_low_stock,
  has_colors,
  has_sizes,
  available_colors,
  available_sizes,
  // Dynamic variant stock mapping for filtering options
  variant_stock_map,
  // Eligibility fields
  eligibility_info,
  // Discount fields (price is already the final discounted price)
  original_price,
  has_discount,
  discount_info,
  onLoginRequired,
}) {
  const { user } = useContext(UserContext);
  const { addToCart, isInCart, getCartItemQuantity } = useCart();
  const axiosInstance = useAxiosWithRefresh();

  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [errors, setErrors] = useState();
  const [severity, setSeverity] = useState();
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [variantAction, setVariantAction] = useState(null); // 'cart' or 'buy'
  const [selectedVariants, setSelectedVariants] = useState([]);
  const [selectedColorId, setSelectedColorId] = useState(null);
  const [displayImage, setDisplayImage] = useState(product_image);
  const [showImageGallery, setShowImageGallery] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Update display image when color selection changes
  useEffect(() => {
    if (selectedColorId && available_colors) {
      const selectedColor = available_colors.find(
        (c) => c.id === selectedColorId
      );
      if (selectedColor?.image_url) {
        setDisplayImage(selectedColor.image_url);
      } else {
        setDisplayImage(product_image);
      }
    } else {
      setDisplayImage(product_image);
    }
  }, [selectedColorId, available_colors, product_image]);

  // Get all available images for gallery
  const getAllImages = () => {
    const images = [{ url: product_image, label: "Main Image" }];
    if (available_colors && available_colors.length > 0) {
      available_colors.forEach((color) => {
        if (color.image_url && color.image_url !== product_image) {
          images.push({ url: color.image_url, label: color.name });
        }
      });
    }
    return images;
  };

  const handleOpenGallery = () => {
    setShowImageGallery(true);
    setCurrentImageIndex(0);
  };

  const handleCloseGallery = () => {
    setShowImageGallery(false);
  };

  const handleNextImage = () => {
    const images = getAllImages();
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const handlePrevImage = () => {
    const images = getAllImages();
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const handleAddToCart = () => {
    if (!user) {
      // Trigger login modal from parent component
      if (onLoginRequired) {
        onLoginRequired();
      }
      setErrors("Please login to add items to cart");
      setSeverity("error");
      ShowNoti();
      return;
    }

 
    // Check if product has variants
    if (has_colors || has_sizes) {
      setVariantAction("cart");
      setShowVariantModal(true);
      return;
    }

    // No variants, add directly
    addProductToCart([]);
  };

  const addProductToCart = (variantSelections) => {
    // CRITICAL: Validate variant selections if product requires them
    if (has_colors || has_sizes) {
      if (!variantSelections || variantSelections.length === 0) {
        setErrors("Please select color/size preferences before adding to cart");
        setSeverity("error");
        ShowNoti();
        return;
      }

      // Validate each selection has required fields
      for (const selection of variantSelections) {
        if (has_colors && !selection.color_id) {
          setErrors("Please select a color for all items");
          setSeverity("error");
          ShowNoti();
          return;
        }
        if (has_sizes && !selection.size_id) {
          setErrors("Please select a size for all items");
          setSeverity("error");
          ShowNoti();
          return;
        }
      }
    }

    const productData = {
      product_id,
      product_name,
      product_image,
      type_of_product,
      price,
      stock_quantity,
      status,
      availability_message,
      is_available_for_purchase,
      is_low_stock,
      has_colors,
      has_sizes,
      available_colors,
      available_sizes,
      // Include variant stock map for dynamic filtering in cart
      variant_stock_map,
      variantSelections,
      // Include discount info for cart display
      original_price,
      has_discount,
      discount_info,
    };

    // Quantity is determined by the number of variant selections
    const quantity = variantSelections.length || 1;
    addToCart(productData, quantity);
    setErrors(
      `${quantity} ${product_name}${quantity > 1 ? "s" : ""} added to cart!`
    );
    setSeverity("success");
    ShowNoti();
  };

  const handlePurchase = async (variantSelections = [], giftData = null) => {
   
    if (!user) {
      if (onLoginRequired) {
        onLoginRequired();
      }
      setErrors("Please login to purchase products");
      setSeverity("error");
      ShowNoti();
      return;
    }


    // CRITICAL: Check if product has variants and none selected
    if ((has_colors || has_sizes) && variantSelections.length === 0) {
      setVariantAction("buy");
      setShowVariantModal(true);
      return;
    }

    // CRITICAL: Validate that variant selections have required fields
    if (has_colors || has_sizes) {
      for (const selection of variantSelections) {
        if (has_colors && !selection.color_id) {
          setErrors("Please select a color for all items before purchasing");
          setSeverity("error");
          ShowNoti();
          setVariantAction("buy");
          setShowVariantModal(true);
          return;
        }
        if (has_sizes && !selection.size_id) {
          setErrors("Please select a size for all items before purchasing");
          setSeverity("error");
          ShowNoti();
          setVariantAction("buy");
          setShowVariantModal(true);
          return;
        }
      }
    }

    try {
      setIsLoading(true);
      setErrors("Initializing payment...");
      setSeverity("info");
      ShowNoti();

      // Initialize payment using new integrated endpoint
      const url = `${BACKEND_HOST}/products/payments/initialize/`;
      
      // Calculate total quantity from variant selections
      const totalQuantity = variantSelections && variantSelections.length > 0
        ? variantSelections.reduce((sum, sel) => sum + (sel.quantity || 1), 0)
        : 1;
      
      const payload = {
        product_id: product_id,
        quantity: totalQuantity,
        gateway: "paystack",
        callback_url: `${window.location.origin}/product/payment/callback`,
      };

     
      if (giftData) {
        if (giftData.isGiftPurchase) {
          payload.is_gift_purchase = true;
          payload.purchased_for_phone = normalizePhoneNumber(giftData.recipientPhone);
          payload.gift_message = giftData.giftMessage || null;
         
        } else if (giftData.isPurchaseOnBehalf) {
          payload.is_purchase_on_behalf = true;
          payload.purchased_for_phone = normalizePhoneNumber(giftData.recipientPhone);
         
        }
      }

      // Add variant selections if present - clean them to only include backend-expected fields
      if (variantSelections && variantSelections.length > 0) {
        // Clean selections: only send color_id, size_id, quantity (remove frontend-only 'id' field)
        payload.variant_selections = variantSelections.map(sel => ({
          color_id: sel.color_id || null,
          size_id: sel.size_id || null,
          quantity: sel.quantity || 1,
        }));
        
       
      } else if (has_colors || has_sizes) {
        // CRITICAL: This should never happen due to validation above
        console.error("❌ CRITICAL: No variant selections but product requires them!");
        setErrors("Please select color/size preferences before purchasing");
        setSeverity("error");
        ShowNoti();
        setIsLoading(false);
        return;
      }

      const response = await axiosInstance.post(url, payload);

      if (response.data.success) {
        // Redirect to Paystack payment page
        window.location.href = response.data.payment_url;
      } else {
        throw new Error(response.data.error || "Payment initialization failed");
      }
    } catch (error) {
      console.error("Error initializing payment:", error);
      setErrors(
        error.response?.data?.error ||
          error.message ||
          "Payment initialization failed"
      );
      setSeverity("error");
      ShowNoti();
      setIsLoading(false);
    }
  };

  const handleVariantConfirm = (selections, giftData = null) => {

    setSelectedVariants(selections);

    if (variantAction === "cart") {
      addProductToCart(selections);
      setShowVariantModal(false);
    } else if (variantAction === "buy") {
      setShowVariantModal(false);

      handlePurchase(selections, giftData);
    }
  };

  const ShowNoti = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  function capitalizeFirstLetter(word) {
    if (!word) return "";
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }

  const getStatusBadgeColor = () => {
    // Check eligibility first (if user is logged in and not eligible)
    if (eligibility_info && !eligibility_info.is_eligible && user) {
      return "bg-purple-600";
    }
    if (status === "OUT_OF_STOCK" || stock_quantity === 0) return "bg-red-500";
    if (status === "COMING_SOON") return "bg-yellow-500";
    if (is_low_stock) return "bg-orange-500";
    return "bg-green-500";
  };

  const getStatusIcon = () => {
    // Check eligibility first
    if (eligibility_info && !eligibility_info.is_eligible && user) {
      return <Lock className="w-4 h-4" />;
    }
    if (status === "OUT_OF_STOCK" || stock_quantity === 0)
      return <AlertCircle className="w-4 h-4" />;
    if (status === "COMING_SOON") return <Clock className="w-4 h-4" />;
    return null;
  };

  // Determine if product can be purchased (considering both stock and eligibility)
  const canPurchase = () => {
    // Not available due to stock/status
    if (!is_available_for_purchase) return false;
    
    // If user is logged in, check eligibility
    if (user && eligibility_info) {
      return eligibility_info.is_eligible;
    }
    
    // If user is not logged in, we allow them to see the product
    // They'll be prompted to login when trying to purchase
    return true;
  };

  // Get the appropriate unavailability message
  const getUnavailabilityMessage = () => {
    // Check eligibility first (for logged-in users)
    if (user && eligibility_info && !eligibility_info.is_eligible) {
      return eligibility_info.eligibility_message || "You are not eligible to purchase this product";
    }
    // Fall back to availability message
    return availability_message;
  };

  const productForModal = {
    product_name,
    product_image: displayImage,
    price,
    stock_quantity,
    has_colors,
    has_sizes,
    available_colors,
    available_sizes,
    // Dynamic variant stock map for filtering sizes by color (and vice versa)
    variant_stock_map,
    // Discount info for variant modal
    original_price,
    has_discount,
    discount_info,
  };

  return (
    <>
      {/* Image Gallery Modal */}
      {showImageGallery && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={handleCloseGallery}
        >
          <button
            onClick={handleCloseGallery}
            className="absolute top-4 right-4 text-white hover:bg-white/20 rounded-full p-2 transition z-10"
          >
            <X className="w-8 h-8" />
          </button>

          {(() => {
            const images = getAllImages();
            const currentImage = images[currentImageIndex];
            return (
              <div
                className="relative w-full max-w-5xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="relative aspect-[4/3] w-full bg-gray-900 rounded-lg overflow-hidden">
                  <img
                    src={currentImage.url}
                    alt={`${product_name} - ${currentImage.label}`}
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-full text-sm font-medium">
                    {currentImage.label} ({currentImageIndex + 1} /{" "}
                    {images.length})
                  </div>
                </div>

                {images.length > 1 && (
                  <>
                    <button
                      onClick={handlePrevImage}
                      className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white rounded-full p-3 transition backdrop-blur-sm"
                    >
                      <ChevronLeft className="w-8 h-8" />
                    </button>
                    <button
                      onClick={handleNextImage}
                      className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white rounded-full p-3 transition backdrop-blur-sm"
                    >
                      <ChevronRight className="w-8 h-8" />
                    </button>
                  </>
                )}
              </div>
            );
          })()}
        </div>
      )}

      <VariantModal
        isOpen={showVariantModal}
        onClose={() => setShowVariantModal(false)}
        product={productForModal}
        quantity={1}
        onConfirm={handleVariantConfirm}
        mode={variantAction === "buy" ? "buy" : "cart"}
      />
      <Snackbar
        open={open}
        autoHideDuration={5000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={handleClose}
      >
        <Alert onClose={handleClose} severity={severity} sx={{ width: "100%" }}>
          <AlertTitle>{capitalizeFirstLetter(severity)}</AlertTitle>
          {errors}
        </Alert>
      </Snackbar>
      {isLoading && (
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
              Initializing payment...
            </p>
          </div>
        </div>
      )}
      <div className="group bg-white rounded-xl overflow-hidden transition-all duration-300 hover:shadow-xl relative">
        {/* Overlay for unavailable products or ineligible users */}
        {!canPurchase() && (
          <div className="absolute inset-0 bg-gray-900/60 z-10 flex items-center justify-center backdrop-blur-sm">
            <div className="text-center p-4 max-w-[90%]">
              <div
                className={`inline-flex items-center gap-2 ${getStatusBadgeColor()} text-white px-4 py-2 rounded-full text-sm font-bold mb-2`}
              >
                {getStatusIcon()}
                {user && eligibility_info && !eligibility_info.is_eligible 
                  ? "Restricted" 
                  : availability_message}
              </div>
              {/* Show detailed eligibility message for ineligible users */}
              {user && eligibility_info && !eligibility_info.is_eligible && (
                <p className="text-white text-sm mt-2 bg-black/40 px-3 py-2 rounded-lg">
                  {eligibility_info.eligibility_message}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Restriction badge for products with restrictions (visible even if user is eligible) */}
        {eligibility_info?.has_restrictions && canPurchase() && (
          <div className="absolute top-3 left-3 z-10">
            <span className="inline-flex items-center gap-1 bg-purple-600/90 text-white px-2 py-1 rounded-full text-xs font-medium shadow-lg backdrop-blur-sm">
              <Users className="w-3 h-3" />
              {eligibility_info.restriction_summary}
            </span>
          </div>
        )}

        <div
          className="relative h-48 rounded-xl overflow-hidden cursor-pointer"
          onClick={handleOpenGallery}
        >
          <img
            src={displayImage}
            alt={product_name}
            className="w-full h-full object-cover object-top group-hover:scale-110 scale-105 transition-all "
          />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900/60 via-transparent to-transparent"></div>

          {/* Status badges */}
          <div className="absolute top-3 right-3 flex flex-col gap-2">
            {is_low_stock && is_available_for_purchase && (
              <span className="inline-flex items-center gap-1 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                <AlertCircle className="w-3 h-3" />
                Only {stock_quantity} left!
              </span>
            )}
          </div>

          <div className="absolute bottom-3 left-3">
            <span className="inline-flex items-center gap-1 bg-gray-800/70 text-white px-3 py-1 rounded-full text-sm font-medium">
              <Tag className="w-4 h-4" />
              {type_of_product}
            </span>
          </div>
        </div>

        <div className="p-4 flex flex-col gap-3">
          <h3 className="font-semibold text-lg text-gray-900 truncate">
            {product_name}
          </h3>

          {/* Color selector - Quick preview */}
          {has_colors && available_colors && available_colors.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600 font-medium">Colors:</span>
              <div className="flex gap-1.5">
                {available_colors.slice(0, 5).map((color) => (
                  <button
                    key={color.id}
                    onClick={() =>
                      setSelectedColorId(
                        selectedColorId === color.id ? null : color.id
                      )
                    }
                    className={`w-6 h-6 rounded-full border-2 transition-all ${
                      selectedColorId === color.id
                        ? "border-blue-600 scale-110 shadow-md"
                        : "border-gray-300 hover:border-gray-400"
                    }`}
                    style={{ backgroundColor: color.hex_code }}
                    title={color.name}
                  />
                ))}
                {available_colors.length > 5 && (
                  <span className="text-xs text-gray-500 self-center">
                    +{available_colors.length - 5}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-xl md:text-lg font-semibold text-blue-600">
                  GH₵{price}
                </span>
                {has_discount && original_price && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400 line-through">
                      GH₵{original_price}
                    </span>
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                      {discount_info?.savings_display}
                    </span>
                  </div>
                )}
              </div>
              {isInCart(product_id) && (
                <span className="text-xs text-green-600 font-medium">
                  {getCartItemQuantity(product_id)} in cart
                </span>
              )}
            </div>

            {canPurchase() ? (
              <div className="flex flex-col xs:flex-row gap-2">
                <button
                  onClick={handleAddToCart}
                  className="flex-1 min-w-0 px-2 sm:px-3 py-2 bg-white border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 active:bg-blue-100 transition flex items-center justify-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium"
                >
                  <ShoppingCart className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Add to Cart</span>
                </button>
                <button
                  onClick={() => {
                    // Always show variant modal for buy mode to allow purchase type selection
                    setVariantAction("buy");
                    setShowVariantModal(true);
                  }}
                  disabled={isLoading}
                  className="flex-1 min-w-0 px-2 sm:px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium shadow-sm"
                >
                  <ShoppingBag className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                  <span className="truncate">Buy Now</span>
                </button>
              </div>
            ) : (
              <button
                disabled
                className="w-full px-4 py-2 bg-gray-400 text-white rounded-md cursor-not-allowed opacity-60 flex items-center justify-center gap-2"
              >
                {user && eligibility_info && !eligibility_info.is_eligible ? (
                  <>
                    <Lock className="w-4 h-4" />
                    Not Eligible
                  </>
                ) : (
                  "Unavailable"
                )}
              </button>
            )}
          </div>

          {/* Availability message at bottom */}
          {canPurchase() &&
            availability_message !== "Available" && (
              <div className="text-xs text-gray-600 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {availability_message}
              </div>
            )}
        </div>
      </div>
    </>
  );
}

MerchandiseCard.propTypes = {
  product_image: PropTypes.string,
  product_name: PropTypes.string.isRequired,
  type_of_product: PropTypes.string,
  price: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  product_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  stock_quantity: PropTypes.number,
  status: PropTypes.string,
  availability_message: PropTypes.string,
  is_available_for_purchase: PropTypes.bool,
  is_low_stock: PropTypes.bool,
  has_colors: PropTypes.bool,
  has_sizes: PropTypes.bool,
  available_colors: PropTypes.array,
  available_sizes: PropTypes.array,
  // Dynamic variant stock mapping - maps which sizes are available per color
  variant_stock_map: PropTypes.shape({
    sizes_by_color: PropTypes.object,
    colors_by_size: PropTypes.object,
    stock_by_variant: PropTypes.object,
  }),
  // Eligibility props
  eligibility_info: PropTypes.shape({
    is_eligible: PropTypes.bool,
    eligibility_message: PropTypes.string,
    has_restrictions: PropTypes.bool,
    restriction_summary: PropTypes.string,
  }),
  // Discount props (price is already the final discounted price)
  original_price: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  has_discount: PropTypes.bool,
  discount_info: PropTypes.shape({
    discount_name: PropTypes.string,
    discount_type: PropTypes.string,
    discount_percentage: PropTypes.string,
    discount_amount: PropTypes.string,
    savings_display: PropTypes.string,
    reason: PropTypes.string,
  }),
  target_audience: PropTypes.string,
  onLoginRequired: PropTypes.func,
};
