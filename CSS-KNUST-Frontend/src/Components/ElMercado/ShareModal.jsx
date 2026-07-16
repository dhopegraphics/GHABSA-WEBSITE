import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Copy,
  Check,
  Share2,
  MessageCircle,
  Mail,
  Link2,
  Twitter,
  Facebook,
  Send,
  ExternalLink,
  Store,
  Package,
  Star,
} from "lucide-react";

// Format price with currency
const formatPrice = (price, currency = "GHS") => {
  if (!price) return "";
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: currency,
  }).format(price);
};

/**
 * ShareModal - A comprehensive sharing modal with rich metadata
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is open
 * @param {function} props.onClose - Close handler
 * @param {string} props.type - Type of content: 'product', 'seller', 'store'
 * @param {Object} props.data - The data to share (product or seller object)
 */
export function ShareModal({ isOpen, onClose, type = "product", data }) {
  const [copied, setCopied] = useState(false);
  const [activeShare, setActiveShare] = useState(null);

  // Reset copied state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setCopied(false);
      setActiveShare(null);
    }
  }, [isOpen]);

  // Generate share data based on type
  const getShareData = useCallback(() => {
    const baseUrl = window.location.origin;
    
    if (type === "product" && data) {
      const productUrl = `${baseUrl}/el-mercado/products/${data.slug}`;
      const price = formatPrice(data.price, data.currency);
      const hasDiscount = data.discount_percentage > 0;
      const discountText = hasDiscount ? ` (${data.discount_percentage}% OFF!)` : "";
      
      return {
        url: productUrl,
        title: data.title,
        text: `Check out "${data.title}" on El Mercado - KNUST's marketplace!`,
        fullText: `🛍️ ${data.title}\n\n💰 ${price}${discountText}\n\n${data.description?.substring(0, 150) || ""}...\n\n🏪 Sold by: ${data.seller?.business_name || data.seller?.display_name || "El Mercado Seller"}\n\n👉 Shop now: ${productUrl}`,
        hashtags: ["ElMercado", "KNUST", "CSS", "Shopping"],
        image: data.main_image_url || data.main_image,
        previewData: {
          type: "product",
          name: data.title,
          price: price,
          discount: hasDiscount ? `${data.discount_percentage}% OFF` : null,
          image: data.main_image_url || data.main_image,
          seller: data.seller?.business_name || data.seller?.display_name,
          rating: data.average_rating,
          reviewCount: data.review_count,
          category: data.category_name,
        },
      };
    }
    
    if ((type === "seller" || type === "store") && data) {
      const storeUrl = `${baseUrl}/el-mercado/store/${data.slug}`;
      const description = data.description || `Check out ${data.display_name}'s store on El Mercado!`;
      
      return {
        url: storeUrl,
        title: `${data.display_name} on El Mercado`,
        text: `Shop at ${data.display_name}'s store on El Mercado - KNUST's marketplace!`,
        fullText: `🏪 ${data.display_name}\n\n${description.substring(0, 150)}${description.length > 150 ? "..." : ""}\n\n⭐ ${data.average_rating ? parseFloat(data.average_rating).toFixed(1) : "New"} rating • ${data.total_sales || 0} sales\n\n👉 Visit store: ${storeUrl}`,
        hashtags: ["ElMercado", "KNUST", "CSS", "ShopLocal"],
        image: data.banner_url || data.banner || data.logo_url || data.logo,
        previewData: {
          type: "store",
          name: data.display_name,
          description: description,
          image: data.banner_url || data.banner,
          logo: data.logo_url || data.logo,
          rating: data.average_rating,
          totalSales: data.total_sales,
          productCount: data.total_listings,
          isVerified: data.is_verified,
          memberSince: data.created_at,
        },
      };
    }
    
    // Fallback
    return {
      url: window.location.href,
      title: "El Mercado - KNUST Marketplace",
      text: "Check out El Mercado - KNUST's official marketplace!",
      fullText: "🛍️ El Mercado - KNUST's Official Marketplace\n\nDiscover amazing products from fellow students and verified sellers!\n\n👉 Shop now: " + window.location.href,
      hashtags: ["ElMercado", "KNUST", "CSS"],
      image: null,
      previewData: null,
    };
  }, [type, data]);

  const shareData = getShareData();

  // Copy link to clipboard
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareData.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Copy with rich text
  const copyRichText = async () => {
    try {
      await navigator.clipboard.writeText(shareData.fullText);
      setCopied(true);
      setActiveShare("text");
      setTimeout(() => {
        setCopied(false);
        setActiveShare(null);
      }, 2500);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Share handlers
  const shareToWhatsApp = () => {
    setActiveShare("whatsapp");
    const text = encodeURIComponent(shareData.fullText);
    window.open(`https://wa.me/?text=${text}`, "_blank", "noopener,noreferrer");
  };

  const shareToTwitter = () => {
    setActiveShare("twitter");
    const text = encodeURIComponent(shareData.text);
    const url = encodeURIComponent(shareData.url);
    const hashtags = shareData.hashtags.join(",");
    window.open(
      `https://twitter.com/intent/tweet?text=${text}&url=${url}&hashtags=${hashtags}`,
      "_blank",
      "noopener,noreferrer"
    );
  };

  const shareToFacebook = () => {
    setActiveShare("facebook");
    const url = encodeURIComponent(shareData.url);
    window.open(
      `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      "_blank",
      "noopener,noreferrer"
    );
  };

  const shareToTelegram = () => {
    setActiveShare("telegram");
    const text = encodeURIComponent(shareData.fullText);
    window.open(
      `https://t.me/share/url?url=${encodeURIComponent(shareData.url)}&text=${text}`,
      "_blank",
      "noopener,noreferrer"
    );
  };

  const shareViaEmail = () => {
    setActiveShare("email");
    const subject = encodeURIComponent(shareData.title);
    const body = encodeURIComponent(shareData.fullText);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  // Native share (mobile)
  const nativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareData.title,
          text: shareData.text,
          url: shareData.url,
        });
      } catch (err) {
        if (err.name !== "AbortError") {
          console.log("Share cancelled or failed:", err);
        }
      }
    }
  };

  // Share options
  const shareOptions = [
    {
      id: "whatsapp",
      name: "WhatsApp",
      icon: MessageCircle,
      color: "bg-green-500 hover:bg-green-600",
      textColor: "text-green-600",
      onClick: shareToWhatsApp,
    },
    {
      id: "twitter",
      name: "X (Twitter)",
      icon: Twitter,
      color: "bg-black hover:bg-gray-800",
      textColor: "text-gray-900",
      onClick: shareToTwitter,
    },
    {
      id: "facebook",
      name: "Facebook",
      icon: Facebook,
      color: "bg-blue-600 hover:bg-blue-700",
      textColor: "text-blue-600",
      onClick: shareToFacebook,
    },
    {
      id: "telegram",
      name: "Telegram",
      icon: Send,
      color: "bg-sky-500 hover:bg-sky-600",
      textColor: "text-sky-500",
      onClick: shareToTelegram,
    },
    {
      id: "email",
      name: "Email",
      icon: Mail,
      color: "bg-gray-600 hover:bg-gray-700",
      textColor: "text-gray-600",
      onClick: shareViaEmail,
    },
  ];

  // Render preview card based on type
  const renderPreview = () => {
    const preview = shareData.previewData;
    if (!preview) return null;

    if (preview.type === "product") {
      return (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="flex">
            {/* Product Image */}
            <div className="w-24 h-24 sm:w-32 sm:h-32 flex-shrink-0 bg-gray-100">
              {preview.image ? (
                <img
                  src={preview.image}
                  alt={preview.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Package className="w-8 h-8 text-gray-400" />
                </div>
              )}
            </div>
            
            {/* Product Info */}
            <div className="flex-1 p-3 sm:p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500 mb-0.5">
                    {preview.category || "El Mercado"}
                  </p>
                  <h4 className="font-semibold text-gray-900 text-sm sm:text-base line-clamp-2">
                    {preview.name}
                  </h4>
                </div>
                {preview.discount && (
                  <span className="flex-shrink-0 bg-red-100 text-red-600 text-xs font-bold px-2 py-1 rounded-full">
                    {preview.discount}
                  </span>
                )}
              </div>
              
              <div className="mt-2 flex items-center gap-3">
                <span className="font-bold text-blue-600">{preview.price}</span>
                {preview.rating > 0 && (
                  <div className="flex items-center gap-1 text-sm">
                    <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
                    <span className="text-gray-600">{parseFloat(preview.rating).toFixed(1)}</span>
                    {preview.reviewCount > 0 && (
                      <span className="text-gray-400">({preview.reviewCount})</span>
                    )}
                  </div>
                )}
              </div>
              
              {preview.seller && (
                <p className="mt-1 text-xs text-gray-500 flex items-center gap-1">
                  <Store className="w-3 h-3" />
                  {preview.seller}
                </p>
              )}
            </div>
          </div>
          
          {/* URL Preview */}
          <div className="px-3 sm:px-4 py-2 bg-gray-50 border-t border-gray-100">
            <p className="text-xs text-gray-500 truncate flex items-center gap-1">
              <Link2 className="w-3 h-3 flex-shrink-0" />
              {shareData.url}
            </p>
          </div>
        </div>
      );
    }

    if (preview.type === "store") {
      return (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          {/* Store Banner */}
          <div className="h-20 sm:h-24 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 relative">
            {preview.image && (
              <img
                src={preview.image}
                alt={preview.name}
                className="w-full h-full object-cover"
              />
            )}
            
            {/* Store Logo */}
            <div className="absolute -bottom-6 left-4">
              <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-white shadow-lg border-2 border-white overflow-hidden">
                {preview.logo ? (
                  <img
                    src={preview.logo}
                    alt={preview.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold text-lg">
                    {preview.name?.charAt(0)}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Store Info */}
          <div className="pt-8 pb-3 px-4">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-gray-900">{preview.name}</h4>
              {preview.isVerified && (
                <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                  Verified
                </span>
              )}
            </div>
            
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">
              {preview.description}
            </p>
            
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
              {preview.rating > 0 && (
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
                  <span className="font-medium text-gray-700">{parseFloat(preview.rating).toFixed(1)}</span>
                </div>
              )}
              {preview.productCount > 0 && (
                <div className="flex items-center gap-1">
                  <Package className="w-3.5 h-3.5" />
                  <span>{preview.productCount} products</span>
                </div>
              )}
              {preview.totalSales > 0 && (
                <span>{preview.totalSales} sales</span>
              )}
            </div>
          </div>
          
          {/* URL Preview */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
            <p className="text-xs text-gray-500 truncate flex items-center gap-1">
              <Link2 className="w-3 h-3 flex-shrink-0" />
              {shareData.url}
            </p>
          </div>
        </div>
      );
    }

    return null;
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Share2 className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Share</h2>
                  <p className="text-xs text-gray-500">
                    {type === "product" ? "Share this product" : "Share this store"}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-y-auto flex-1">
              {/* Preview Card */}
              <div className="mb-5">
                <p className="text-xs text-gray-500 mb-2 font-medium">PREVIEW</p>
                {renderPreview()}
              </div>

              {/* Share Options */}
              <div className="mb-5">
                <p className="text-xs text-gray-500 mb-3 font-medium">SHARE VIA</p>
                <div className="grid grid-cols-5 gap-3">
                  {shareOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={option.onClick}
                      className="flex flex-col items-center gap-1.5 group"
                    >
                      <div
                        className={`w-12 h-12 rounded-full ${option.color} text-white flex items-center justify-center transition-all group-hover:scale-110 shadow-md ${
                          activeShare === option.id ? "ring-2 ring-offset-2 ring-blue-500" : ""
                        }`}
                      >
                        <option.icon className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600 font-medium">
                        {option.name}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Copy Link Section */}
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium">OR COPY LINK</p>
                <div className="flex items-stretch gap-2">
                  <div className="flex-1 bg-gray-100 rounded-lg px-3 py-2.5 text-sm text-gray-600 truncate flex items-center">
                    <Link2 className="w-4 h-4 mr-2 flex-shrink-0 text-gray-400" />
                    <span className="truncate">{shareData.url}</span>
                  </div>
                  <button
                    onClick={copyLink}
                    className={`px-4 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${
                      copied && activeShare !== "text"
                        ? "bg-green-500 text-white"
                        : "bg-blue-600 hover:bg-blue-700 text-white"
                    }`}
                  >
                    {copied && activeShare !== "text" ? (
                      <>
                        <Check className="w-4 h-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Copy Rich Text */}
              <button
                onClick={copyRichText}
                className={`w-full mt-3 py-2.5 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2 ${
                  copied && activeShare === "text"
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                }`}
              >
                {copied && activeShare === "text" ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied with details!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy with full details
                  </>
                )}
              </button>

              {/* Native Share Button (Mobile) */}
              {typeof navigator !== "undefined" && navigator.share && (
                <button
                  onClick={nativeShare}
                  className="w-full mt-3 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium text-sm transition-all hover:from-blue-700 hover:to-indigo-700 flex items-center justify-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  More sharing options
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default ShareModal;
