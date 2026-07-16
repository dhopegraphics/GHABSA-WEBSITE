import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowLeft,
  Star,
  Heart,
  ShoppingCart,
  Share2,
  Package,
  Shield,
  Truck,
  Check,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Plus,
  Minus,
  MessageCircle,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { ReviewsSection } from "../../Components/ElMercado/ReviewsSection";
import { SellerInfoSection } from "../../Components/ElMercado/SellerInfoSection";
import { ContactSellerModal } from "../../Components/ElMercado/ContactSellerModal";
import { ShareModal } from "../../Components/ElMercado/ShareModal";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { useCart } from "../../Context/CartContext";

// Format price with currency
const formatPrice = (price, currency = "GHS") => {
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: currency,
  }).format(price);
};

// Image Gallery Component
function ImageGallery({ images, mainImage, title }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  // Combine main image with additional images, avoiding duplicates
  const allImages = (() => {
    const result = [];
    
    // Add main image first if it exists
    if (mainImage) {
      result.push({ image: mainImage, image_url: mainImage, is_main: true });
    }
    
    // Add additional images from the images array
    if (images?.length > 0) {
      images.forEach(img => {
        const imgUrl = img.image_url || img.image;
        // Avoid adding duplicate of main image
        if (imgUrl && imgUrl !== mainImage) {
          result.push(img);
        }
      });
    }
    
    return result.length > 0 ? result : [{ image: "/images/placeholder-product.jpg", image_url: "/images/placeholder-product.jpg" }];
  })();

  const currentImage = allImages[selectedIndex]?.image_url || allImages[selectedIndex]?.image || "/images/placeholder-product.jpg";

  const handlePrevious = () => {
    setImageLoaded(false);
    setImageError(false);
    setSelectedIndex((prev) => (prev === 0 ? allImages.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setImageLoaded(false);
    setImageError(false);
    setSelectedIndex((prev) => (prev === allImages.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="space-y-4">
      {/* Main Image */}
      <div className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden group">
        {/* Loading skeleton */}
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <Package className="w-16 h-16 text-gray-300 animate-pulse" />
          </div>
        )}
        
        {/* Error state */}
        {imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100">
            <Package className="w-16 h-16 text-gray-400 mb-2" />
            <span className="text-sm text-gray-500">Image unavailable</span>
          </div>
        )}
        
        <motion.img
          key={selectedIndex}
          initial={{ opacity: 0 }}
          animate={{ opacity: imageLoaded ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          src={currentImage}
          alt={title}
          className="w-full h-full object-cover"
          onLoad={() => {
            setImageLoaded(true);
            setImageError(false);
          }}
          onError={(e) => {
            setImageError(true);
            setImageLoaded(false);
            e.target.src = "/images/placeholder-product.jpg";
          }}
        />
        
        {/* Navigation arrows - always visible on mobile, hover on desktop */}
        {allImages.length > 1 && (
          <>
            <button
              onClick={handlePrevious}
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 bg-white/90 hover:bg-white rounded-full shadow-lg transition-all md:opacity-0 md:group-hover:opacity-100"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-5 h-5 text-gray-700" />
            </button>
            <button
              onClick={handleNext}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-white/90 hover:bg-white rounded-full shadow-lg transition-all md:opacity-0 md:group-hover:opacity-100"
              aria-label="Next image"
            >
              <ChevronRight className="w-5 h-5 text-gray-700" />
            </button>
            
            {/* Image counter indicator */}
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-black/60 text-white text-xs px-3 py-1.5 rounded-full">
              {selectedIndex + 1} / {allImages.length}
            </div>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {allImages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {allImages.map((img, index) => (
            <button
              key={index}
              onClick={() => {
                setSelectedIndex(index);
                setImageLoaded(false);
                setImageError(false);
              }}
              className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-colors ${
                selectedIndex === index
                  ? "border-blue-500 ring-2 ring-blue-200"
                  : "border-gray-200 hover:border-gray-400"
              }`}
            >
              <img
                src={img.image_url || img.image || "/images/placeholder-product.jpg"}
                alt={`${title} ${index + 1}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = "/images/placeholder-product.jpg";
                }}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Seller Info Card
function SellerCard({ seller }) {
  if (!seller) return null;

  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold">
          {seller.business_name?.charAt(0) || "S"}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-gray-900">{seller.business_name}</h4>
            {seller.is_verified && (
              <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                <Check className="w-3 h-3" /> Verified
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">{seller.seller_type_display || "Seller"}</p>
        </div>
      </div>
      
      <div className="mt-4 flex items-center gap-4 text-sm">
        {parseFloat(seller.average_rating) > 0 && (
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
            <span className="font-medium">{parseFloat(seller.average_rating || 0).toFixed(1)}</span>
          </div>
        )}
        {seller.total_products > 0 && (
          <span className="text-gray-500">{seller.total_products} products</span>
        )}
      </div>
      
      <Link
        to={`/el-mercado/store/${seller.slug}`}
        className="mt-4 block w-full text-center py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
      >
        Visit Store
      </Link>
    </div>
  );
}

// Loading Skeleton
function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Image skeleton */}
        <div className="aspect-square bg-gray-200 rounded-2xl animate-pulse" />
        
        {/* Content skeleton */}
        <div className="space-y-4">
          <div className="h-8 bg-gray-200 rounded animate-pulse w-3/4" />
          <div className="h-6 bg-gray-200 rounded animate-pulse w-1/2" />
          <div className="h-10 bg-gray-200 rounded animate-pulse w-1/3" />
          <div className="h-32 bg-gray-200 rounded animate-pulse" />
          <div className="h-12 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
}

// Main Product Detail Page
export function ProductDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { fetchListingBySlug, addToFavorites, removeFromFavorites } = useElMercado();
  const axiosInstance = useAxiosWithRefresh();
  const { addToCart, isInCart } = useCart();
  
  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [isFavorited, setIsFavorited] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [activeTab, setActiveTab] = useState('description'); // Tab state
  const [reviews, setReviews] = useState([]);
  const [loadingReviews, setLoadingReviews] = useState(false);
  const [reviewsError, setReviewsError] = useState(null);
  const hasAttemptedReviewsFetch = useRef(false);
  const [addingToCart, setAddingToCart] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  useEffect(() => {
    scrollToTop();
  }, []);

  useEffect(() => {
    const loadProduct = async () => {
      setIsLoading(true);
      setError(null);
      // Reset reviews state when loading new product
      setReviews([]);
      setReviewsError(null);
      hasAttemptedReviewsFetch.current = false;
      
      const data = await fetchListingBySlug(slug);
      
      if (data) {
        setProduct(data);
        setIsFavorited(data.is_favorited || false);
        // Set default variant if available
        if (data.variants?.length > 0) {
          setSelectedVariant(data.variants[0]);
        }
      } else {
        setError("Product not found");
      }
      
      setIsLoading(false);
    };

    if (slug) {
      loadProduct();
    }
  }, [slug, fetchListingBySlug]);

  // Fetch reviews when reviews tab is opened (only once)
  useEffect(() => {
    const fetchReviews = async () => {
      // Only fetch if we haven't tried yet and we're on reviews tab with a product
      if (activeTab === 'reviews' && product && !hasAttemptedReviewsFetch.current) {
        hasAttemptedReviewsFetch.current = true;
        setLoadingReviews(true);
        setReviewsError(null);
        try {
          const response = await axiosInstance.get(`/marketplace/listings/${slug}/reviews/`);
          setReviews(response.data?.results || response.data || []);
        } catch (err) {
          console.error('Failed to fetch reviews:', err);
          setReviewsError(err.message || 'Failed to load reviews');
          setReviews([]);
        } finally {
          setLoadingReviews(false);
        }
      }
    };

    fetchReviews();
  }, [activeTab, product, slug, axiosInstance]);

  const handleFavoriteToggle = async () => {
    if (isFavorited) {
      await removeFromFavorites(product.slug);
    } else {
      await addToFavorites(product.slug);
    }
    setIsFavorited(!isFavorited);
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  const handleAddToCart = () => {
    setAddingToCart(true);
    
    try {
      // Prepare cart item with El Mercado structure
      const cartItem = {
        id: product.id,
        slug: product.slug,
        title: product.title,
        price: selectedVariant?.price || product.price,
        currency: product.currency,
        main_image: product.main_image_url || product.main_image,
        stock_quantity: selectedVariant?.stock_quantity || product.stock_quantity,
        seller: product.seller,
        // Add variant if selected
        ...(selectedVariant && {
          selectedVariant: {
            id: selectedVariant.id,
            name: selectedVariant.name,
            price: selectedVariant.price,
          }
        }),
      };

      addToCart(cartItem, quantity);
      
      // Show success message
      alert(`${quantity} × ${product.title} added to cart!`);
      
      // Optionally navigate to cart or stay on page
      // navigate('/cart');
      
    } catch (error) {
      console.error('Failed to add to cart:', error);
      alert('Failed to add item to cart. Please try again.');
    } finally {
      setAddingToCart(false);
    }
  };

  const currentPrice = selectedVariant?.price || product?.price;
  const compareAtPrice = selectedVariant?.compare_at_price || product?.compare_at_price;
  const discountPercentage = product?.discount_percentage || 0;
  const hasDiscount = discountPercentage > 0;
  const inStock = selectedVariant ? selectedVariant.stock_quantity > 0 : product?.is_in_stock;
  const stockQuantity = selectedVariant?.stock_quantity || product?.stock_quantity;

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20">
          <LoadingSkeleton />
        </div>
        <Footer />
      </>
    );
  }

  if (error || !product) {
    return (
      <>
        <Helmet>
          <title>Product Not Found | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <div className="pt-20 pb-16 px-4">
            <div className="max-w-lg mx-auto text-center py-20">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-10 h-10 text-red-500" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Product Not Found</h1>
              <p className="text-gray-500 mb-6">
                The product you&apos;re looking for doesn&apos;t exist or has been removed.
              </p>
              <Link
                to="/el-mercado/browse"
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Browse
              </Link>
            </div>
          </div>
          <Footer />
        </div>
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>{product.title} | El Mercado - BIO-CHEM KNUST</title>
        <meta name="description" content={product.description?.substring(0, 160) || `Shop ${product.title} on El Mercado, KNUST's official marketplace.`} />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="product" />
        <meta property="og:url" content={`${window.location.origin}/el-mercado/products/${product.slug}`} />
        <meta property="og:title" content={`${product.title} | El Mercado`} />
        <meta property="og:description" content={product.description?.substring(0, 160) || `Shop ${product.title} on El Mercado.`} />
        <meta property="og:image" content={product.main_image_url || product.main_image} />
        <meta property="og:site_name" content="El Mercado - BIO-CHEM KNUST" />
        
        {/* Product-specific Open Graph */}
        <meta property="product:price:amount" content={product.price} />
        <meta property="product:price:currency" content={product.currency || "GHS"} />
        {product.is_in_stock && <meta property="product:availability" content="in stock" />}
        {!product.is_in_stock && <meta property="product:availability" content="out of stock" />}
        {product.category_name && <meta property="product:category" content={product.category_name} />}
        {product.seller?.business_name && <meta property="product:retailer_item_id" content={product.seller.business_name} />}
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content={`${window.location.origin}/el-mercado/products/${product.slug}`} />
        <meta name="twitter:title" content={`${product.title} | El Mercado`} />
        <meta name="twitter:description" content={product.description?.substring(0, 160) || `Shop ${product.title} on El Mercado.`} />
        <meta name="twitter:image" content={product.main_image_url || product.main_image} />
        <meta name="twitter:label1" content="Price" />
        <meta name="twitter:data1" content={`${product.currency || "GHS"} ${product.price}`} />
        <meta name="twitter:label2" content="Sold by" />
        <meta name="twitter:data2" content={product.seller?.business_name || product.seller?.display_name || "El Mercado Seller"} />
        
        {/* Additional SEO */}
        <link rel="canonical" href={`${window.location.origin}/el-mercado/products/${product.slug}`} />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          <div className="max-w-7xl mx-auto px-4 py-8">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
              <Link to="/el-mercado" className="hover:text-blue-600">El Mercado</Link>
              <span>/</span>
              <Link to="/el-mercado/browse" className="hover:text-blue-600">Products</Link>
              {product.category && (
                <>
                  <span>/</span>
                  <Link 
                    to={`/el-mercado/browse?category=${product.category.id}`}
                    className="hover:text-blue-600"
                  >
                    {product.category.name}
                  </Link>
                </>
              )}
              <span>/</span>
              <span className="text-gray-900 truncate max-w-[200px]">{product.title}</span>
            </nav>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
              {/* Left Column - Images */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <ImageGallery
                  images={product.images}
                  mainImage={product.main_image_url || product.main_image}
                  title={product.title}
                />
              </motion.div>

              {/* Right Column - Product Info */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                {/* Type & Category */}
                <div className="flex items-center gap-3">
                  <span className={`text-sm font-medium px-3 py-1 rounded-full ${
                    product.listing_type === "PRODUCT"
                      ? "bg-blue-100 text-blue-700"
                      : product.listing_type === "DIGITAL"
                      ? "bg-purple-100 text-purple-700"
                      : "bg-green-100 text-green-700"
                  }`}>
                    {product.listing_type_display || product.listing_type}
                  </span>
                  {product.condition_display && (
                    <span className="text-sm text-gray-500">
                      {product.condition_display}
                    </span>
                  )}
                </div>

                {/* Title */}
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                  {product.title}
                </h1>

                {/* Rating & Stats */}
                <div className="flex items-center gap-4 flex-wrap">
                  {parseFloat(product.average_rating) > 0 && (
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`w-5 h-5 ${
                              i < Math.floor(parseFloat(product.average_rating) || 0)
                                ? "text-yellow-400 fill-yellow-400"
                                : "text-gray-300"
                            }`}
                          />
                        ))}
                      </div>
                      <span className="font-medium">{parseFloat(product.average_rating || 0).toFixed(1)}</span>
                      <span className="text-gray-500">({product.review_count || 0} reviews)</span>
                    </div>
                  )}
                  <span className="text-gray-400">|</span>
                  <span className="text-gray-500">{product.order_count || 0} sold</span>
                  {product.view_count > 0 && (
                    <>
                      <span className="text-gray-400">|</span>
                      <span className="text-gray-500">{product.view_count.toLocaleString()} views</span>
                    </>
                  )}
                </div>

                {/* Price */}
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-baseline gap-3">
                    <span className="text-3xl font-bold text-gray-900">
                      {formatPrice(currentPrice, product.currency)}
                    </span>
                    {hasDiscount && compareAtPrice && (
                      <>
                        <span className="text-lg text-gray-400 line-through">
                          {formatPrice(compareAtPrice, product.currency)}
                        </span>
                        <span className="bg-red-100 text-red-600 text-sm font-semibold px-2 py-1 rounded">
                          -{discountPercentage}% OFF
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Variants */}
                {product.variants?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Options</h3>
                    <div className="flex flex-wrap gap-2">
                      {product.variants.map((variant) => (
                        <button
                          key={variant.id}
                          onClick={() => setSelectedVariant(variant)}
                          className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-colors ${
                            selectedVariant?.id === variant.id
                              ? "border-blue-500 bg-blue-50 text-blue-700"
                              : "border-gray-200 hover:border-gray-300"
                          } ${variant.stock_quantity === 0 ? "opacity-50 line-through" : ""}`}
                          disabled={variant.stock_quantity === 0}
                        >
                          {variant.name}
                          {variant.price !== product.price && (
                            <span className="ml-1">({formatPrice(variant.price)})</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stock Status & Quantity */}
                <div className="flex items-center gap-4">
                  <span className={`flex items-center gap-1 text-sm font-medium ${
                    inStock ? "text-green-600" : "text-red-500"
                  }`}>
                    <Package className="w-4 h-4" />
                    {inStock 
                      ? stockQuantity > 10 
                        ? "In Stock" 
                        : `Only ${stockQuantity} left` 
                      : "Out of Stock"}
                  </span>
                </div>

                {/* Quantity Selector */}
                {inStock && (
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-gray-700">Quantity:</span>
                    <div className="flex items-center border border-gray-200 rounded-lg">
                      <button
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="p-2 hover:bg-gray-100 transition-colors"
                        disabled={quantity <= 1}
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                      <span className="w-12 text-center font-medium">{quantity}</span>
                      <button
                        onClick={() => setQuantity(Math.min(stockQuantity || 99, quantity + 1))}
                        className="p-2 hover:bg-gray-100 transition-colors"
                        disabled={quantity >= (stockQuantity || 99)}
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={handleAddToCart}
                    disabled={!inStock || addingToCart}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold transition-all ${
                      inStock && !addingToCart
                        ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl"
                        : "bg-gray-200 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    <ShoppingCart className="w-5 h-5" />
                    {addingToCart ? "Adding..." : inStock ? "Add to Cart" : "Out of Stock"}
                  </button>
                  <button
                    onClick={handleFavoriteToggle}
                    className={`p-3 rounded-xl border-2 transition-all ${
                      isFavorited
                        ? "border-red-500 bg-red-50 text-red-500"
                        : "border-gray-200 hover:border-gray-300 text-gray-600"
                    }`}
                  >
                    <Heart className={`w-5 h-5 ${isFavorited ? "fill-current" : ""}`} />
                  </button>
                  <button
                    onClick={handleShare}
                    className="p-3 rounded-xl border-2 border-gray-200 hover:border-gray-300 text-gray-600 transition-all"
                  >
                    <Share2 className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Contact Seller Button */}
                {product.seller && (
                  <button
                    onClick={() => setShowContactModal(true)}
                    className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg transition-all"
                  >
                    <MessageCircle className="w-5 h-5" />
                    Contact Seller
                  </button>
                )}

                {/* Trust Badges */}
                <div className="flex items-center gap-6 py-4 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Shield className="w-5 h-5 text-green-500" />
                    <span>Secure Payment</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Truck className="w-5 h-5 text-blue-500" />
                    <span>Fast Delivery</span>
                  </div>
                </div>

                {/* Seller Info */}
                <SellerCard seller={product.seller} />
              </motion.div>
            </div>

            {/* Product Details Tabs */}
            <div className="mt-12">
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="border-b border-gray-100">
                  <nav className="flex">
                    <button 
                      onClick={() => setActiveTab('description')}
                      className={`px-6 py-4 text-sm font-semibold transition-colors ${
                        activeTab === 'description'
                          ? 'text-blue-600 border-b-2 border-blue-600'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      Description
                    </button>
                    <button 
                      onClick={() => setActiveTab('reviews')}
                      className={`px-6 py-4 text-sm font-semibold transition-colors ${
                        activeTab === 'reviews'
                          ? 'text-blue-600 border-b-2 border-blue-600'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      Reviews ({product.review_count || 0})
                    </button>
                    {product.seller && (
                      <button 
                        onClick={() => setActiveTab('seller')}
                        className={`px-6 py-4 text-sm font-semibold transition-colors ${
                          activeTab === 'seller'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        Seller Info
                      </button>
                    )}
                  </nav>
                </div>
                
                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'description' && (
                    <div>
                      {product.description ? (
                        <div 
                          className="prose prose-gray max-w-none"
                          dangerouslySetInnerHTML={{ __html: product.description }}
                        />
                      ) : (
                        <p className="text-gray-500">No description provided.</p>
                      )}

                      {/* Tags */}
                      {product.tags && product.tags.length > 0 && (
                        <div className="mt-6 pt-6 border-t border-gray-100">
                          <h4 className="text-sm font-medium text-gray-700 mb-3">Tags</h4>
                          <div className="flex flex-wrap gap-2">
                            {product.tags.map((tag, index) => (
                              <Link
                                key={index}
                                to={`/el-mercado/browse?search=${tag}`}
                                className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm hover:bg-gray-200 transition-colors"
                              >
                                #{tag}
                              </Link>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'reviews' && (
                    <ReviewsSection 
                      product={product} 
                      reviews={reviews}
                      loading={loadingReviews}
                      error={reviewsError}
                      canReview={product.can_review}
                      onWriteReview={() => navigate(`/el-mercado/products/${slug}/review`)}
                      onRetry={() => {
                        hasAttemptedReviewsFetch.current = false;
                        setReviewsError(null);
                        setLoadingReviews(true);
                      }}
                    />
                  )}

                  {activeTab === 'seller' && product.seller && (
                    <SellerInfoSection seller={product.seller} listing={product} />
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>

        <Footer />
        
        {/* Contact Seller Modal */}
        {product.seller && (
          <ContactSellerModal
            isOpen={showContactModal}
            onClose={() => setShowContactModal(false)}
            seller={product.seller}
            listing={product}
          />
        )}
        
        {/* Share Modal */}
        <ShareModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          type="product"
          data={product}
        />
      </div>
    </>
  );
}

export default ProductDetailPage;
