import { useEffect, useState, useCallback, useMemo, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useParams, useSearchParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Search,
  Grid,
  List,
  Star,
  Heart,
  ShoppingCart,
  Package,
  Store,
  ArrowUpDown,
  X,
  ShoppingBag,
  Calendar,
  MessageCircle,
  Share2,
  BadgeCheck,
  Clock,
  Users,
  Check,
  Loader2,
  ArrowLeft,
  Instagram,
  Twitter,
  Facebook,
  Globe,
  UserPlus,
  UserMinus,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { useCart } from "../../Context/CartContext";
import { UserContext } from "../../Context/UserContext";
import { ProductGridSkeleton } from "../../Components/ElMercado/ProductCardSkeleton";
import { ContactSellerModal } from "../../Components/ElMercado/ContactSellerModal";
import { ShareModal } from "../../Components/ElMercado/ShareModal";

// Animation variants
const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const cardVariants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: { duration: 0.3 }
  },
  hover: {
    y: -8,
    transition: { duration: 0.2 }
  },
};

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

// Listing types for filters
const LISTING_TYPES = [
  { value: "", label: "All Types" },
  { value: "PRODUCT", label: "Physical Products" },
  { value: "DIGITAL", label: "Digital Products" },
  { value: "SERVICE", label: "Services" },
];

const SORT_OPTIONS = [
  { value: "-created_at", label: "Newest First" },
  { value: "created_at", label: "Oldest First" },
  { value: "price", label: "Price: Low to High" },
  { value: "-price", label: "Price: High to Low" },
  { value: "-average_rating", label: "Highest Rated" },
  { value: "-order_count", label: "Best Selling" },
];

// Format price with currency
const formatPrice = (price, currency = "GHS") => {
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: currency,
  }).format(price);
};

// Format date
const formatDate = (date) => {
  return new Date(date).toLocaleDateString("en-GB", {
    month: "short",
    year: "numeric",
  });
};

// Product Card Component
function ProductCard({ product, viewMode }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isFavorited, setIsFavorited] = useState(product.is_favorited || false);
  const [addingToCart, setAddingToCart] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [togglingFavorite, setTogglingFavorite] = useState(false);
  const { addToFavorites, removeFromFavorites } = useElMercado();
  const { addToCart } = useCart();
  const navigate = useNavigate();
  
  const imageUrl = product.main_image_url || product.main_image || "/images/placeholder-product.jpg";
  const discountPercentage = product.discount_percentage || 0;
  const hasDiscount = discountPercentage > 0;

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!product.is_in_stock || addingToCart) return;
    
    setAddingToCart(true);
    
    const cartItem = {
      id: product.id,
      slug: product.slug,
      title: product.title,
      price: product.price,
      currency: product.currency,
      main_image: product.main_image_url || product.main_image,
      stock_quantity: product.stock_quantity,
      seller: product.seller,
    };
    
    addToCart(cartItem, 1);
    
    setTimeout(() => setAddingToCart(false), 500);
  };

  const handleFavoriteToggle = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (togglingFavorite) return;
    setTogglingFavorite(true);
    
    try {
      if (isFavorited) {
        const result = await removeFromFavorites(product.slug);
        if (result.success) setIsFavorited(false);
      } else {
        const result = await addToFavorites(product.slug);
        if (result.success) setIsFavorited(true);
      }
    } finally {
      setTogglingFavorite(false);
    }
  };

  if (viewMode === "list") {
    return (
      <motion.div
        variants={cardVariants}
        initial="initial"
        animate="animate"
        whileHover="hover"
        className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow"
      >
        <Link to={`/el-mercado/products/${product.slug}`} className="flex">
          {/* Image */}
          <div className="relative w-48 h-48 flex-shrink-0 bg-gray-100">
            {/* Loading skeleton */}
            {!imageLoaded && !imageError && (
              <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
                <Package className="w-12 h-12 text-gray-400" />
              </div>
            )}
            
            {/* Error state */}
            {imageError && (
              <div className="absolute inset-0 bg-gray-100 flex flex-col items-center justify-center p-4 text-center">
                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mb-2">
                  <Package className="w-6 h-6 text-gray-400" />
                </div>
                <p className="text-xs text-gray-500 font-medium line-clamp-2">{product.title}</p>
                <span className="text-[10px] text-gray-400 mt-1">Image unavailable</span>
              </div>
            )}
            
            <img
              src={imageUrl}
              alt={product.title}
              className={`w-full h-full object-cover transition-opacity duration-300 ${
                imageLoaded && !imageError ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={() => {
                setImageError(true);
                setImageLoaded(false);
              }}
            />
            {hasDiscount && (
              <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
                -{discountPercentage}%
              </span>
            )}
            <button
              onClick={handleFavoriteToggle}
              disabled={togglingFavorite}
              className={`absolute top-2 right-2 p-2 rounded-full transition-all ${
                isFavorited
                  ? "bg-red-500 text-white"
                  : "bg-white/80 text-gray-600 hover:bg-white hover:text-red-500"
              } ${togglingFavorite ? "opacity-50 cursor-wait" : ""}`}
            >
              <Heart className={`w-4 h-4 ${isFavorited ? "fill-current" : ""}`} />
            </button>
          </div>
          
          {/* Content */}
          <div className="flex-1 p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  product.listing_type === "PRODUCT" 
                    ? "bg-blue-100 text-blue-700"
                    : product.listing_type === "DIGITAL"
                    ? "bg-purple-100 text-purple-700"
                    : "bg-green-100 text-green-700"
                }`}>
                  {product.listing_type_display || product.listing_type}
                </span>
                {product.condition_display && (
                  <span className="text-xs text-gray-500">
                    {product.condition_display}
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-gray-900 line-clamp-2 mb-1">
                {product.title}
              </h3>
              <p className="text-sm text-gray-500 mb-2">
                {product.category_name}
              </p>
              
              {/* Rating */}
              {product.average_rating > 0 && (
                <div className="flex items-center gap-1 mb-2">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="text-sm font-medium">{parseFloat(product.average_rating).toFixed(1)}</span>
                  <span className="text-sm text-gray-400">({product.review_count} reviews)</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-between mt-4">
              <div>
                <span className="text-xl font-bold text-gray-900">
                  {formatPrice(product.price, product.currency)}
                </span>
                {hasDiscount && (
                  <span className="ml-2 text-sm text-gray-400 line-through">
                    {formatPrice(product.compare_at_price, product.currency)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-medium ${
                  product.is_in_stock ? "text-green-600" : "text-red-500"
                }`}>
                  {product.is_in_stock ? "In Stock" : "Out of Stock"}
                </span>
                {product.is_in_stock && (
                  <button
                    onClick={handleAddToCart}
                    disabled={addingToCart}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:bg-blue-400"
                  >
                    <ShoppingCart className={`w-4 h-4 ${addingToCart ? 'animate-bounce' : ''}`} />
                    {addingToCart ? 'Added!' : 'Add'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </Link>
      </motion.div>
    );
  }

  // Grid view (default)
  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl transition-all group"
    >
      <Link to={`/el-mercado/products/${product.slug}`}>
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden bg-gray-100">
          {/* Loading skeleton */}
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
              <Package className="w-12 h-12 text-gray-400" />
            </div>
          )}
          
          {/* Error state */}
          {imageError && (
            <div className="absolute inset-0 bg-gray-100 flex flex-col items-center justify-center p-4 text-center">
              <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-2">
                <Package className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-xs text-gray-500 font-medium line-clamp-2">{product.title}</p>
              <span className="text-[10px] text-gray-400 mt-1">Image unavailable</span>
            </div>
          )}
          
          <img
            src={imageUrl}
            alt={product.title}
            className={`w-full h-full object-cover group-hover:scale-110 transition-all duration-500 ${
              imageLoaded && !imageError ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={() => setImageLoaded(true)}
            onError={() => {
              setImageError(true);
              setImageLoaded(false);
            }}
          />
          
          {/* Overlay badges */}
          <div className="absolute top-3 left-3 flex flex-col gap-2">
            {hasDiscount && (
              <span className="bg-red-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-lg">
                -{discountPercentage}% OFF
              </span>
            )}
            {!product.is_in_stock && (
              <span className="bg-gray-800/90 text-white text-xs font-medium px-2.5 py-1 rounded-full">
                Out of Stock
              </span>
            )}
          </div>
          
          {/* Favorite button */}
          <button
            onClick={handleFavoriteToggle}
            disabled={togglingFavorite}
            className={`absolute top-3 right-3 p-2.5 rounded-full shadow-lg transition-all ${
              isFavorited
                ? "bg-red-500 text-white scale-110"
                : "bg-white/90 text-gray-600 hover:bg-white hover:text-red-500"
            } ${togglingFavorite ? "opacity-50 cursor-wait" : ""}`}
          >
            <Heart className={`w-5 h-5 ${isFavorited ? "fill-current" : ""}`} />
          </button>
          
          {/* Quick actions - shows on hover */}
          <AnimatePresence>
            {isHovered && product.is_in_stock && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-3 left-3 right-3 flex gap-2"
              >
                <button 
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    navigate(`/el-mercado/products/${product.slug}`);
                  }}
                  className="flex-1 bg-white/95 hover:bg-white text-gray-800 font-semibold py-2.5 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg text-sm"
                >
                  Quick View
                </button>
                <button 
                  onClick={handleAddToCart}
                  disabled={addingToCart}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg text-sm disabled:bg-blue-400"
                >
                  <ShoppingCart className={`w-4 h-4 ${addingToCart ? 'animate-bounce' : ''}`} />
                  {addingToCart ? 'Added!' : 'Add to Cart'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Content */}
        <div className="p-4">
          {/* Category & Type */}
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              product.listing_type === "PRODUCT" 
                ? "bg-blue-50 text-blue-700"
                : product.listing_type === "DIGITAL"
                ? "bg-purple-50 text-purple-700"
                : "bg-green-50 text-green-700"
            }`}>
              {product.listing_type_display || product.listing_type}
            </span>
            <span className="text-xs text-gray-400 truncate">
              {product.category_name}
            </span>
          </div>
          
          {/* Title */}
          <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
            {product.title}
          </h3>
          
          {/* Rating */}
          <div className="flex items-center gap-2 mb-3">
            {product.average_rating > 0 ? (
              <>
                <div className="flex items-center gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-3.5 h-3.5 ${
                        i < Math.floor(product.average_rating)
                          ? "text-yellow-400 fill-yellow-400"
                          : "text-gray-300"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-500">
                  ({product.review_count})
                </span>
              </>
            ) : (
              <span className="text-xs text-gray-400">No reviews yet</span>
            )}
          </div>
          
          {/* Price */}
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold text-gray-900">
              {formatPrice(product.price, product.currency)}
            </span>
            {hasDiscount && (
              <span className="text-sm text-gray-400 line-through">
                {formatPrice(product.compare_at_price, product.currency)}
              </span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// Seller Stats Card
function StatCard({ icon: Icon, label, value, color = "blue" }) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    orange: "bg-orange-50 text-orange-600",
    yellow: "bg-yellow-50 text-yellow-600",
  };

  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

// Category Filter Chip
function CategoryChip({ category, isSelected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
        isSelected
          ? "bg-blue-600 text-white shadow-md"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {category.name}
      {category.listing_count > 0 && (
        <span className={`ml-1.5 ${isSelected ? "text-blue-200" : "text-gray-400"}`}>
          ({category.listing_count})
        </span>
      )}
    </button>
  );
}

// Loading Skeleton
function SellerStoreSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Banner Skeleton */}
      <div className="h-64 bg-gray-200 animate-pulse" />
      
      {/* Profile Section Skeleton */}
      <div className="max-w-7xl mx-auto px-4 -mt-16 relative z-10">
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="w-32 h-32 bg-gray-200 rounded-2xl animate-pulse" />
            <div className="flex-1 space-y-3">
              <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse" />
              <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
              <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
            </div>
          </div>
        </div>
        
        {/* Stats Skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl p-4 border border-gray-100">
              <div className="h-12 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
        
        {/* Products Skeleton */}
        <ProductGridSkeleton viewMode="grid" count={8} />
      </div>
    </div>
  );
}

// Empty Products State
function EmptyProductsState({ sellerName }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center"
    >
      <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Package className="w-10 h-10 text-gray-400" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        No Products Yet
      </h3>
      <p className="text-gray-500 mb-6 max-w-md mx-auto">
        {sellerName} hasn&apos;t listed any products yet. Check back later for new items!
      </p>
      <Link
        to="/el-mercado/browse"
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Browse All Products
      </Link>
    </motion.div>
  );
}

// Not Found State
function SellerNotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-lg p-8 text-center max-w-md"
      >
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Store className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Store Not Found</h1>
        <p className="text-gray-500 mb-6">
          The store you&apos;re looking for doesn&apos;t exist or may have been removed.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/el-mercado/browse"
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Browse Products
          </Link>
          <Link
            to="/el-mercado"
            className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
          >
            Go to Marketplace
          </Link>
        </div>
      </motion.div>
    </div>
  );
}

// Main Seller Store Page
export function SellerStorePage() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const { fetchSellerBySlug, fetchListings, followSeller, unfollowSeller, checkIsFollowing } = useElMercado();
  const { user } = useContext(UserContext);
  const isAuthenticated = !!user;

  // State
  const [seller, setSeller] = useState(null);
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listingsLoading, setListingsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("grid");
  const [copied, setCopied] = useState(false);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  const [showContactModal, setShowContactModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [contentReady, setContentReady] = useState(false);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  // Get filters from URL params
  const filters = useMemo(() => ({
    search: searchParams.get("search") || "",
    category: searchParams.get("category") || "",
    listing_type: searchParams.get("type") || "",
    condition: searchParams.get("condition") || "",
    min_price: searchParams.get("min_price") || "",
    max_price: searchParams.get("max_price") || "",
    ordering: searchParams.get("sort") || "-created_at",
  }), [searchParams]);

  // Update URL params when filters change
  const updateFilters = useCallback((key, value) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key === "listing_type" ? "type" : key === "ordering" ? "sort" : key, value);
    } else {
      newParams.delete(key === "listing_type" ? "type" : key === "ordering" ? "sort" : key);
    }
    setSearchParams(newParams, { replace: true });
  }, [searchParams, setSearchParams]);

  // Reset all filters
  const resetFilters = useCallback(() => {
    setSearchParams(new URLSearchParams(), { replace: true });
  }, [setSearchParams]);

  // Fetch seller data
  useEffect(() => {
    let isCancelled = false;
    
    const loadSeller = async () => {
      if (!slug) return;
      
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSellerBySlug(slug);
        if (isCancelled) return;
        
        if (data) {
          setSeller(data);
        } else {
          setError("Seller not found");
        }
      } catch (err) {
        if (!isCancelled) {
          console.error("Error fetching seller:", err);
          setError("Failed to load seller");
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    loadSeller();
    
    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  // Fetch listings when seller or filters change
  useEffect(() => {
    let isCancelled = false;
    
    const loadListings = async () => {
      if (!seller?.slug) return;
      
      setListingsLoading(true);
      setContentReady(false);
      try {
        const result = await fetchListings({
          seller: seller.slug,
          ...filters,
        });
        
        if (isCancelled) return;
        
        const data = result?.results || result || [];
        setListings(Array.isArray(data) ? data : []);
        setPagination({
          count: result?.count || data.length,
          next: result?.next,
          previous: result?.previous,
        });
        
        // Small delay for smooth transition
        setTimeout(() => {
          if (!isCancelled) {
            setContentReady(true);
          }
        }, 150);
      } catch (err) {
        if (!isCancelled) {
          console.error("Error fetching listings:", err);
          setContentReady(true);
        }
      } finally {
        if (!isCancelled) {
          setListingsLoading(false);
        }
      }
    };

    loadListings();
    
    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seller?.slug, filters.search, filters.category, filters.listing_type, filters.condition, filters.min_price, filters.max_price, filters.ordering]);

  useEffect(() => {
    scrollToTop();
  }, [slug]);

  // Check follow status when seller loads
  useEffect(() => {
    const checkFollowStatus = async () => {
      if (!seller?.slug || !isAuthenticated) {
        setIsFollowing(false);
        return;
      }
      
      // Check from seller data first (if is_following is available)
      if (seller.is_following !== undefined) {
        setIsFollowing(seller.is_following);
        return;
      }
      
      // Otherwise check via API
      const following = await checkIsFollowing(seller.slug);
      setIsFollowing(following);
    };

    checkFollowStatus();
  }, [seller?.slug, isAuthenticated, seller?.is_following, checkIsFollowing]);

  // Handle follow/unfollow toggle
  const handleFollowToggle = async () => {
    if (!isAuthenticated) {
      // Redirect to login or show toast
      return;
    }

    setFollowLoading(true);
    try {
      if (isFollowing) {
        const result = await unfollowSeller(seller.slug);
        if (result.success) {
          setIsFollowing(false);
        }
      } else {
        const result = await followSeller(seller.slug);
        if (result.success) {
          setIsFollowing(true);
        }
      }
    } catch (err) {
      console.error("Error toggling follow:", err);
    } finally {
      setFollowLoading(false);
    }
  };

  // Copy store URL (used by ShareModal for copy link button)
  // eslint-disable-next-line no-unused-vars
  const copyStoreUrl = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Share store
  const shareStore = () => {
    setShowShareModal(true);
  };

  // Derive seller categories from listings
  const sellerCategories = useMemo(() => {
    if (!listings.length) return [];
    
    const categoryMap = new Map();
    listings.forEach(listing => {
      if (listing.category_name && listing.category) {
        const existing = categoryMap.get(listing.category);
        if (existing) {
          existing.listing_count += 1;
        } else {
          categoryMap.set(listing.category, {
            id: listing.category,
            name: listing.category_name,
            listing_count: 1,
          });
        }
      }
    });
    
    return Array.from(categoryMap.values()).sort((a, b) => b.listing_count - a.listing_count);
  }, [listings]);

  // Loading state
  if (loading) {
    return (
      <>
        <Navbar />
        <SellerStoreSkeleton />
        <Footer />
      </>
    );
  }

  // Error state
  if (error || !seller) {
    return (
      <>
        <Navbar />
        <SellerNotFound />
        <Footer />
      </>
    );
  }

  const bannerUrl = seller.banner_url || seller.banner || null;
  const logoUrl = seller.logo_url || seller.logo || null;
  const memberSince = seller.created_at ? formatDate(seller.created_at) : "Member";
  const isVerified = seller.is_verified;
  const isVacationMode = seller.vacation_mode;

  return (
    <>
      <Helmet>
        <title>{seller.display_name} | El Mercado - BIO-CHEM KNUST</title>
        <meta
          name="description"
          content={seller.description || `Shop products from ${seller.display_name} on El Mercado, the official KNUST marketplace.`}
        />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="profile" />
        <meta property="og:url" content={`${window.location.origin}/el-mercado/store/${seller.slug}`} />
        <meta property="og:title" content={`${seller.display_name} | El Mercado`} />
        <meta property="og:description" content={seller.description || `Shop products from ${seller.display_name} on El Mercado, KNUST's official marketplace.`} />
        <meta property="og:image" content={bannerUrl || logoUrl || `${window.location.origin}/images/el-mercado-og.jpg`} />
        <meta property="og:site_name" content="El Mercado - BIO-CHEM KNUST" />
        
        {/* Profile-specific Open Graph */}
        <meta property="profile:username" content={seller.display_name} />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content={`${window.location.origin}/el-mercado/store/${seller.slug}`} />
        <meta name="twitter:title" content={`${seller.display_name} | El Mercado`} />
        <meta name="twitter:description" content={seller.description || `Shop products from ${seller.display_name} on El Mercado.`} />
        <meta name="twitter:image" content={bannerUrl || logoUrl || `${window.location.origin}/images/el-mercado-og.jpg`} />
        <meta name="twitter:label1" content="Products" />
        <meta name="twitter:data1" content={`${seller.total_listings || 0} items`} />
        <meta name="twitter:label2" content="Rating" />
        <meta name="twitter:data2" content={seller.average_rating ? `${parseFloat(seller.average_rating).toFixed(1)} ⭐` : "New Store"} />
        
        {/* Additional SEO */}
        <link rel="canonical" href={`${window.location.origin}/el-mercado/store/${seller.slug}`} />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-16">
          {/* Store Banner */}
          <section className="relative h-48 md:h-64 lg:h-72 overflow-hidden">
            {bannerUrl ? (
              <img
                src={bannerUrl}
                alt={`${seller.display_name} banner`}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700">
                {/* Default pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div
                    className="absolute inset-0"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                    }}
                  />
                </div>
              </div>
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
            
            {/* Back button */}
            <Link
              to="/el-mercado/browse"
              className="absolute top-4 left-4 flex items-center gap-2 px-4 py-2 bg-white/90 backdrop-blur-sm rounded-lg text-gray-700 hover:bg-white transition-colors shadow-md"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="font-medium">Back</span>
            </Link>
            
            {/* Share button */}
            <button
              onClick={shareStore}
              className="absolute top-4 right-4 flex items-center gap-2 px-4 py-2 bg-white/90 backdrop-blur-sm rounded-lg text-gray-700 hover:bg-white transition-colors shadow-md"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-green-600" />
                  <span className="font-medium text-green-600">Copied!</span>
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4" />
                  <span className="font-medium">Share</span>
                </>
              )}
            </button>
          </section>

          {/* Store Profile Card */}
          <div className="max-w-7xl mx-auto px-4 -mt-16 relative z-10">
            <motion.div
              variants={fadeInUp}
              initial="initial"
              animate="animate"
              className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 mb-8"
            >
              <div className="flex flex-col md:flex-row gap-6">
                {/* Logo */}
                <div className="flex-shrink-0">
                  <div className="w-28 h-28 md:w-32 md:h-32 rounded-2xl bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center overflow-hidden border-4 border-white shadow-lg">
                    {logoUrl ? (
                      <img
                        src={logoUrl}
                        alt={seller.display_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-4xl md:text-5xl font-bold text-blue-600">
                        {seller.display_name?.charAt(0)?.toUpperCase() || "S"}
                      </span>
                    )}
                  </div>
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                          {seller.display_name}
                        </h1>
                        {isVerified && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                            <BadgeCheck className="w-4 h-4" />
                            Verified
                          </span>
                        )}
                        {isVacationMode && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                            <Clock className="w-4 h-4" />
                            On Vacation
                          </span>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-3">
                        <span className="inline-flex items-center gap-1.5">
                          <Store className="w-4 h-4" />
                          {seller.seller_type_display || seller.seller_type}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <Calendar className="w-4 h-4" />
                          Since {memberSince}
                        </span>
                        {seller.average_rating > 0 && (
                          <span className="inline-flex items-center gap-1.5">
                            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                            {parseFloat(seller.average_rating).toFixed(1)} ({seller.total_reviews} reviews)
                          </span>
                        )}
                      </div>

                      {seller.description && (
                        <p className="text-gray-600 max-w-2xl line-clamp-2">
                          {seller.description}
                        </p>
                      )}

                      {/* Social Links */}
                      {(seller.instagram || seller.twitter || seller.facebook || seller.website) && (
                        <div className="flex flex-wrap items-center gap-2 mt-3">
                          {seller.instagram && (
                            <a
                              href={`https://instagram.com/${seller.instagram}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium rounded-full hover:opacity-90 transition-opacity"
                            >
                              <Instagram className="w-4 h-4" />
                              @{seller.instagram}
                            </a>
                          )}
                          {seller.twitter && (
                            <a
                              href={`https://x.com/${seller.twitter}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-black text-white text-sm font-medium rounded-full hover:bg-gray-800 transition-colors"
                            >
                              <Twitter className="w-4 h-4" />
                              @{seller.twitter}
                            </a>
                          )}
                          {seller.facebook && (
                            <a
                              href={`https://facebook.com/${seller.facebook}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-full hover:bg-blue-700 transition-colors"
                            >
                              <Facebook className="w-4 h-4" />
                              {seller.facebook}
                            </a>
                          )}
                          {seller.website && (
                            <a
                              href={seller.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-full hover:bg-gray-200 transition-colors"
                            >
                              <Globe className="w-4 h-4" />
                              Website
                            </a>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap items-center gap-3">
                      {/* Follow/Unfollow Button */}
                      {isAuthenticated && (
                        <button
                          onClick={handleFollowToggle}
                          disabled={followLoading}
                          className={`px-5 py-2.5 font-semibold rounded-xl transition-all flex items-center gap-2 shadow-md ${
                            isFollowing
                              ? "bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200"
                              : "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
                          }`}
                        >
                          {followLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                          ) : isFollowing ? (
                            <>
                              <UserMinus className="w-5 h-5" />
                              Following
                            </>
                          ) : (
                            <>
                              <UserPlus className="w-5 h-5" />
                              Follow
                            </>
                          )}
                        </button>
                      )}

                      {/* Contact Button */}
                      <button
                        onClick={() => setShowContactModal(true)}
                        className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-md"
                      >
                        <MessageCircle className="w-5 h-5" />
                        Contact Seller
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Vacation Mode Notice */}
              {isVacationMode && seller.vacation_message && (
                <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Clock className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-orange-800">Store on Vacation</p>
                      <p className="text-sm text-orange-700">{seller.vacation_message}</p>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Stats Grid */}
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
              className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
            >
              <motion.div variants={cardVariants}>
                <StatCard
                  icon={Package}
                  label="Products"
                  value={pagination.count || listings.length}
                  color="blue"
                />
              </motion.div>
              <motion.div variants={cardVariants}>
                <StatCard
                  icon={Star}
                  label="Rating"
                  value={seller.average_rating ? parseFloat(seller.average_rating).toFixed(1) : "New"}
                  color="yellow"
                />
              </motion.div>
              <motion.div variants={cardVariants}>
                <StatCard
                  icon={ShoppingBag}
                  label="Total Sales"
                  value={seller.total_sales || 0}
                  color="green"
                />
              </motion.div>
              <motion.div variants={cardVariants}>
                <StatCard
                  icon={Users}
                  label="Reviews"
                  value={seller.total_reviews || 0}
                  color="purple"
                />
              </motion.div>
            </motion.div>

            {/* Category Chips */}
            {sellerCategories.length > 0 && (
              <motion.div
                variants={fadeInUp}
                initial="initial"
                animate="animate"
                className="mb-6"
              >
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Shop by Category
                </h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => updateFilters("category", "")}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      !filters.category
                        ? "bg-blue-600 text-white shadow-md"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    All Products
                  </button>
                  {sellerCategories.map((category) => (
                    <CategoryChip
                      key={category.id}
                      category={category}
                      isSelected={filters.category === category.id.toString()}
                      onClick={() => updateFilters("category", category.id.toString())}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Toolbar */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Search within store */}
                <div className="flex-1 max-w-md">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const formData = new FormData(e.target);
                      updateFilters("search", formData.get("search"));
                    }}
                    className="relative"
                  >
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      name="search"
                      defaultValue={filters.search}
                      placeholder={`Search in ${seller.display_name}'s store...`}
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </form>
                </div>

                {/* Right side controls */}
                <div className="flex items-center gap-3">
                  {/* Messages link */}
                  <Link
                    to="/el-mercado/messages"
                    className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span className="hidden sm:inline">Messages</span>
                  </Link>
                  
                  {/* Favorites link */}
                  <Link
                    to="/el-mercado/favorites"
                    className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-colors"
                  >
                    <Heart className="w-4 h-4" />
                    <span className="hidden sm:inline">Favorites</span>
                  </Link>
                  
                  {/* Results count */}
                  <span className="text-sm text-gray-500">
                    <span className="font-semibold text-gray-900">{pagination.count}</span> products
                  </span>

                  {/* Sort */}
                  <div className="relative">
                    <select
                      value={filters.ordering}
                      onChange={(e) => updateFilters("ordering", e.target.value)}
                      className="appearance-none pl-3 pr-10 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white cursor-pointer"
                    >
                      {SORT_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <ArrowUpDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                  </div>

                  {/* View mode toggle */}
                  <div className="hidden sm:flex items-center border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`p-2 ${
                        viewMode === "grid"
                          ? "bg-blue-600 text-white"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      <Grid className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode("list")}
                      className={`p-2 ${
                        viewMode === "list"
                          ? "bg-blue-600 text-white"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Active Filters */}
              {(filters.search || filters.category || filters.listing_type) && (
                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100 flex-wrap">
                  <span className="text-sm text-gray-500">Active filters:</span>
                  {filters.search && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                      Search: {filters.search}
                      <button onClick={() => updateFilters("search", "")}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}
                  {filters.category && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      Category
                      <button onClick={() => updateFilters("category", "")}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}
                  {filters.listing_type && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                      {LISTING_TYPES.find((t) => t.value === filters.listing_type)?.label}
                      <button onClick={() => updateFilters("listing_type", "")}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}
                  <button
                    onClick={resetFilters}
                    className="text-xs text-red-600 hover:text-red-700 font-medium ml-2"
                  >
                    Clear all
                  </button>
                </div>
              )}
            </div>

            {/* Products Grid */}
            <section className="pb-16">
              <AnimatePresence mode="wait">
                {listingsLoading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-center justify-center py-12"
                  >
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </motion.div>
                ) : listings.length === 0 ? (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <EmptyProductsState sellerName={seller.display_name} />
                  </motion.div>
                ) : (
                  <motion.div
                    key="content"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: contentReady ? 1 : 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <motion.div
                      variants={staggerContainer}
                      initial="initial"
                      animate="animate"
                      className={
                        viewMode === "list"
                          ? "space-y-4"
                          : "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                      }
                    >
                      {listings.map((product, index) => (
                        <motion.div
                          key={product.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05, duration: 0.3 }}
                        >
                          <ProductCard
                            product={product}
                            viewMode={viewMode}
                          />
                        </motion.div>
                      ))}
                    </motion.div>

                    {/* Load More */}
                    {pagination.next && (
                      <div className="text-center mt-8">
                        <button
                          className="px-6 py-3 bg-white border border-gray-200 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                        >
                          Load More Products
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </section>
          </div>
        </main>

        <Footer />

        {/* Contact Seller Modal */}
        <ContactSellerModal
          isOpen={showContactModal}
          onClose={() => setShowContactModal(false)}
          seller={seller}
        />
        
        {/* Share Modal */}
        <ShareModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          type="store"
          data={seller}
        />
      </div>
    </>
  );
}

export default SellerStorePage;
