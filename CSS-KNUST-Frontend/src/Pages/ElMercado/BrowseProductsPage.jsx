import { useEffect, useState, useCallback, useMemo, useRef, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Search,
  Filter,
  Grid,
  List,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Star,
  Heart,
  ShoppingCart,
  Package,
  Store,
  Tag,
  ArrowUpDown,
  X,
  AlertCircle,
  ShoppingBag,
  SlidersHorizontal,
  RefreshCw,
  Loader2,
  MessageCircle,
  Users,
  Flame,
  Clock,
  TrendingUp,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { useCart } from "../../Context/CartContext";
import { UserContext } from "../../Context/UserContext";
import { ProductGridSkeleton } from "../../Components/ElMercado/ProductCardSkeleton";

const cardVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: 0.3 }
  },
  hover: {
    y: -8,
    transition: { duration: 0.2 }
  },
};

// Listing types and conditions for filters
const LISTING_TYPES = [
  { value: "", label: "All Types" },
  { value: "PRODUCT", label: "Physical Products" },
  { value: "DIGITAL", label: "Digital Products" },
  { value: "SERVICE", label: "Services" },
];

const CONDITIONS = [
  { value: "", label: "Any Condition" },
  { value: "NEW", label: "Brand New" },
  { value: "LIKE_NEW", label: "Like New" },
  { value: "GOOD", label: "Good" },
  { value: "FAIR", label: "Fair" },
  { value: "USED", label: "Used" },
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

// Product Card Component
function ProductCard({ product, viewMode }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isFavorited, setIsFavorited] = useState(product.is_favorited || false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);
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
        <Link to={`/el-mercado/products/${product.slug}`} className="flex flex-col sm:flex-row">
          {/* Image */}
          <div className="relative w-full sm:w-40 md:w-48 h-48 sm:h-40 md:h-48 flex-shrink-0 bg-gray-100">
            {/* Image loading skeleton */}
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
              onError={(e) => {
                setImageError(true);
                e.target.style.display = 'none';
              }}
            />
            {hasDiscount && (
              <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
                -{discountPercentage}%
              </span>
            )}
            <button
              onClick={handleFavoriteToggle}
              className={`absolute top-2 right-2 p-2 rounded-full transition-all ${
                isFavorited
                  ? "bg-red-500 text-white"
                  : "bg-white/80 text-gray-600 hover:bg-white hover:text-red-500"
              }`}
            >
              <Heart className={`w-4 h-4 ${isFavorited ? "fill-current" : ""}`} />
            </button>
          </div>
          
          {/* Content */}
          <div className="flex-1 p-3 sm:p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2 flex-wrap">
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
                  <span className="text-sm font-medium">{product.average_rating?.toFixed(1)}</span>
                  <span className="text-sm text-gray-400">({product.review_count} reviews)</span>
                </div>
              )}
              
              {/* Seller */}
              {product.seller && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Store className="w-4 h-4" />
                  <span>{product.seller.business_name}</span>
                  {product.seller.is_verified && (
                    <span className="text-blue-500" title="Verified Seller">✓</span>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-3 sm:mt-4 gap-3">
              <div className="flex items-center gap-2">
                <span className="text-lg sm:text-xl font-bold text-gray-900">
                  {formatPrice(product.price, product.currency)}
                </span>
                {hasDiscount && (
                  <span className="text-xs sm:text-sm text-gray-400 line-through">
                    {formatPrice(product.compare_at_price, product.currency)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 sm:gap-3">
                <span className={`text-xs sm:text-sm font-medium ${
                  product.is_in_stock ? "text-green-600" : "text-red-500"
                }`}>
                  {product.is_in_stock ? "In Stock" : "Out of Stock"}
                </span>
                {product.is_in_stock && (
                  <button
                    onClick={handleAddToCart}
                    disabled={addingToCart}
                    className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-medium rounded-lg transition-colors disabled:bg-blue-400"
                  >
                    <ShoppingCart className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${addingToCart ? 'animate-bounce' : ''}`} />
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
          {/* Image loading skeleton */}
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
              <Package className="w-12 h-12 text-gray-400" />
            </div>
          )}
          
          {/* Error state with alt text */}
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
            onError={(e) => {
              setImageError(true);
              e.target.style.display = 'none';
            }}
          />
          
          {/* Overlay badges */}
          <div className="absolute top-2 sm:top-3 left-2 sm:left-3 flex flex-col gap-1.5 sm:gap-2">
            {hasDiscount && (
              <span className="bg-red-500 text-white text-[10px] sm:text-xs font-bold px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-full shadow-lg">
                -{discountPercentage}% OFF
              </span>
            )}
            {!product.is_in_stock && (
              <span className="bg-gray-800/90 text-white text-[10px] sm:text-xs font-medium px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-full">
                Out of Stock
              </span>
            )}
          </div>
          
          {/* Favorite button */}
          <button
            onClick={handleFavoriteToggle}
            className={`absolute top-2 sm:top-3 right-2 sm:right-3 p-1.5 sm:p-2.5 rounded-full shadow-lg transition-all ${
              isFavorited
                ? "bg-red-500 text-white scale-110"
                : "bg-white/90 text-gray-600 hover:bg-white hover:text-red-500"
            }`}
          >
            <Heart className={`w-4 sm:w-5 h-4 sm:h-5 ${isFavorited ? "fill-current" : ""}`} />
          </button>
          
          {/* Quick actions - always visible on mobile, hover on desktop */}
          {product.is_in_stock && (
            <div
              className={`absolute bottom-2 sm:bottom-3 left-2 sm:left-3 right-2 sm:right-3 flex gap-1.5 sm:gap-2 transition-all duration-200 sm:opacity-0 sm:translate-y-4 ${
                isHovered ? 'sm:opacity-100 sm:translate-y-0' : ''
              }`}
            >
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  navigate(`/el-mercado/products/${product.slug}`);
                }}
                className="flex-1 bg-white/95 hover:bg-white text-gray-800 font-semibold py-2 sm:py-2.5 px-2 sm:px-3 rounded-lg flex items-center justify-center gap-1 sm:gap-2 transition-colors shadow-lg text-xs sm:text-sm"
              >
                <span className="hidden xs:inline">Quick</span> View
              </button>
              <button 
                onClick={handleAddToCart}
                disabled={addingToCart}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 sm:py-2.5 px-2 sm:px-3 rounded-lg flex items-center justify-center gap-1 sm:gap-2 transition-colors shadow-lg text-xs sm:text-sm disabled:bg-blue-400"
              >
                <ShoppingCart className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${addingToCart ? 'animate-bounce' : ''}`} />
                <span className="hidden xs:inline">{addingToCart ? 'Added!' : 'Add'}</span>
              </button>
            </div>
          )}
        </div>
        
        {/* Content */}
        <div className="p-3 sm:p-4">
          {/* Category & Type */}
          <div className="flex items-center gap-1.5 sm:gap-2 mb-1.5 sm:mb-2 flex-wrap">
            <span className={`text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full ${
              product.listing_type === "PRODUCT" 
                ? "bg-blue-50 text-blue-700"
                : product.listing_type === "DIGITAL"
                ? "bg-purple-50 text-purple-700"
                : "bg-green-50 text-green-700"
            }`}>
              {product.listing_type_display || product.listing_type}
            </span>
            <span className="text-[10px] sm:text-xs text-gray-400 truncate">
              {product.category_name}
            </span>
          </div>
          
          {/* Title */}
          <h3 className="font-medium sm:font-semibold text-sm sm:text-base text-gray-900 line-clamp-2 mb-1.5 sm:mb-2 group-hover:text-blue-600 transition-colors">
            {product.title}
          </h3>
          
          {/* Rating */}
          <div className="flex items-center gap-1 sm:gap-2 mb-2 sm:mb-3">
            {product.average_rating > 0 ? (
              <>
                <div className="flex items-center gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-3 sm:w-3.5 h-3 sm:h-3.5 ${
                        i < Math.floor(product.average_rating)
                          ? "text-yellow-400 fill-yellow-400"
                          : "text-gray-300"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-xs sm:text-sm text-gray-500">
                  ({product.review_count})
                </span>
              </>
            ) : (
              <span className="text-[10px] sm:text-xs text-gray-400">No reviews yet</span>
            )}
          </div>
          
          {/* Seller */}
          {product.seller && (
            <div className="flex items-center gap-1 sm:gap-1.5 mb-2 sm:mb-3 text-xs sm:text-sm text-gray-500">
              <Store className="w-3 sm:w-3.5 h-3 sm:h-3.5 flex-shrink-0" />
              <span className="truncate">{product.seller.business_name}</span>
              {product.seller.is_verified && (
                <span className="text-blue-500 text-[10px] sm:text-xs">✓</span>
              )}
            </div>
          )}
          
          {/* Price */}
          <div className="flex items-baseline gap-1.5 sm:gap-2">
            <span className="text-base sm:text-lg font-bold text-gray-900">
              {formatPrice(product.price, product.currency)}
            </span>
            {hasDiscount && (
              <span className="text-xs sm:text-sm text-gray-400 line-through">
                {formatPrice(product.compare_at_price, product.currency)}
              </span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// Category Sidebar Component
function CategorySidebar({ categories, selectedCategory, onCategoryChange, isMobile, onClose }) {
  const [expandedCategories, setExpandedCategories] = useState([]);

  const toggleCategory = (categoryId) => {
    setExpandedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const renderCategory = (category, level = 0) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expandedCategories.includes(category.id);
    const isSelected = selectedCategory === category.id.toString();

    return (
      <div key={category.id}>
        <div
          className={`flex items-center gap-1.5 sm:gap-2 py-1.5 sm:py-2 px-2.5 sm:px-3 rounded-lg cursor-pointer transition-colors text-xs sm:text-sm ${
            isSelected
              ? "bg-blue-100 text-blue-700"
              : "hover:bg-gray-100 text-gray-700"
          }`}
          style={{ paddingLeft: `${level * 10 + 10}px` }}
          onClick={() => {
            onCategoryChange(category.id.toString());
            if (isMobile) onClose?.();
          }}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleCategory(category.id);
              }}
              className="p-0.5 hover:bg-gray-200 rounded"
            >
              <ChevronRight
                className={`w-3 sm:w-4 h-3 sm:h-4 transition-transform ${
                  isExpanded ? "rotate-90" : ""
                }`}
              />
            </button>
          )}
          <span className="flex-1 font-medium truncate">{category.name}</span>
          {category.listing_count > 0 && (
            <span className="text-[10px] sm:text-xs text-gray-400">
              ({category.listing_count})
            </span>
          )}
        </div>
        
        {hasChildren && isExpanded && (
          <div className="ml-2">
            {category.children.map((child) => renderCategory(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4">
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <h3 className="text-sm sm:text-base font-semibold text-gray-900 flex items-center gap-1.5 sm:gap-2">
          <Tag className="w-4 sm:w-5 h-4 sm:h-5 text-blue-600" />
          Categories
        </h3>
        {isMobile && (
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
      
      {/* All Products option */}
      <div
        className={`flex items-center gap-1.5 sm:gap-2 py-1.5 sm:py-2 px-2.5 sm:px-3 rounded-lg cursor-pointer transition-colors mb-2 text-sm ${
          !selectedCategory
            ? "bg-blue-100 text-blue-700"
            : "hover:bg-gray-100 text-gray-700"
        }`}
        onClick={() => {
          onCategoryChange("");
          if (isMobile) onClose?.();
        }}
      >
        <Package className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
        <span className="flex-1 text-xs sm:text-sm font-medium">All Products</span>
      </div>
      
      <div className="border-t border-gray-100 my-1.5 sm:my-2" />
      
      {/* Categories list */}
      <div className="space-y-0.5 sm:space-y-1 max-h-[300px] sm:max-h-[400px] overflow-y-auto custom-scrollbar">
        {categories.map((category) => renderCategory(category))}
      </div>
    </div>
  );
}

// Filters Panel Component
function FiltersPanel({ filters, onFilterChange, onReset }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4 space-y-3 sm:space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm sm:text-base font-semibold text-gray-900 flex items-center gap-1.5 sm:gap-2">
          <SlidersHorizontal className="w-4 sm:w-5 h-4 sm:h-5 text-blue-600" />
          Filters
        </h3>
        <button
          onClick={onReset}
          className="text-xs sm:text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
        >
          <RefreshCw className="w-3 sm:w-4 h-3 sm:h-4" />
          Reset
        </button>
      </div>
      
      {/* Listing Type */}
      <div>
        <label className="text-xs sm:text-sm font-medium text-gray-700 block mb-1.5 sm:mb-2">
          Product Type
        </label>
        <select
          value={filters.listing_type || ""}
          onChange={(e) => onFilterChange("listing_type", e.target.value)}
          className="w-full px-2.5 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {LISTING_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>
      
      {/* Condition */}
      <div>
        <label className="text-xs sm:text-sm font-medium text-gray-700 block mb-1.5 sm:mb-2">
          Condition
        </label>
        <select
          value={filters.condition || ""}
          onChange={(e) => onFilterChange("condition", e.target.value)}
          className="w-full px-2.5 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {CONDITIONS.map((condition) => (
            <option key={condition.value} value={condition.value}>
              {condition.label}
            </option>
          ))}
        </select>
      </div>
      
      {/* Price Range */}
      <div>
        <label className="text-xs sm:text-sm font-medium text-gray-700 block mb-1.5 sm:mb-2">
          Price Range (GHS)
        </label>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.min_price || ""}
            onChange={(e) => onFilterChange("min_price", e.target.value)}
            className="w-full px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <span className="text-gray-400 text-xs sm:text-sm">-</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.max_price || ""}
            onChange={(e) => onFilterChange("max_price", e.target.value)}
            className="w-full px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
}

// Empty State Component
function EmptyState({ searchQuery, onReset }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 md:p-12 text-center"
    >
      <div className="w-14 sm:w-16 md:w-20 h-14 sm:h-16 md:h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
        <ShoppingBag className="w-7 sm:w-8 md:w-10 h-7 sm:h-8 md:h-10 text-gray-400" />
      </div>
      <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-1.5 sm:mb-2">
        {searchQuery ? "No products found" : "No products available"}
      </h3>
      <p className="text-sm sm:text-base text-gray-500 mb-4 sm:mb-6 max-w-md mx-auto px-2">
        {searchQuery
          ? `We couldn't find any products matching "${searchQuery}". Try adjusting your search or filters.`
          : "There are no products available at the moment. Check back later or become a seller!"}
      </p>
      <div className="flex flex-col xs:flex-row items-center justify-center gap-2 sm:gap-4">
        {searchQuery && (
          <button
            onClick={onReset}
            className="w-full xs:w-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm sm:text-base"
          >
            Clear Filters
          </button>
        )}
        <Link
          to="/el-mercado/become-a-seller"
          className="w-full xs:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base text-center"
        >
          Become a Seller
        </Link>
      </div>
    </motion.div>
  );
}

// Showcase Section Component - Modern collapsible tabs for Best Sellers & New Arrivals
function ShowcaseSection({ featuredListings, recentListings, trendingListings, featuredReady, recentReady, trendingReady, onViewAll }) {
  const [activeTab, setActiveTab] = useState('bestsellers');
  const [isExpanded, setIsExpanded] = useState(false);

  const tabs = [
    {
      id: 'bestsellers',
      label: 'Best Sellers',
      icon: Flame,
      color: 'orange',
      listings: featuredListings,
      ready: featuredReady,
      orderKey: '-order_count',
      gradient: 'from-orange-500 to-red-500',
      bgLight: 'bg-orange-50',
      textColor: 'text-orange-600',
      borderColor: 'border-orange-200',
      count: featuredListings?.length || 0,
    },
    {
      id: 'newarrivals',
      label: 'New Arrivals',
      icon: Clock,
      color: 'blue',
      listings: recentListings,
      ready: recentReady,
      orderKey: '-created_at',
      gradient: 'from-blue-500 to-indigo-500',
      bgLight: 'bg-blue-50',
      textColor: 'text-blue-600',
      borderColor: 'border-blue-200',
      count: recentListings?.length || 0,
    },
    {
      id: 'trending',
      label: 'Trending',
      icon: TrendingUp,
      color: 'purple',
      listings: trendingListings,
      ready: trendingReady,
      orderKey: '-view_count',
      gradient: 'from-purple-500 to-pink-500',
      bgLight: 'bg-purple-50',
      textColor: 'text-purple-600',
      borderColor: 'border-purple-200',
      count: trendingListings?.length || 0,
    },
  ];

  const currentTab = tabs.find(t => t.id === activeTab);

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-10"
    >
      {/* Header with tabs and toggle */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Tab Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 gap-3 sm:gap-0 border-b border-gray-100">
          {/* Tab Pills */}
          <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative flex items-center gap-1 sm:gap-2 px-2.5 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl font-medium text-xs sm:text-sm transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? `bg-gradient-to-r ${tab.gradient} text-white shadow-lg shadow-${tab.color}-500/25`
                      : `${tab.bgLight} ${tab.textColor} hover:shadow-md`
                  }`}
                >
                  <Icon className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${isActive ? 'animate-pulse' : ''}`} />
                  <span className="hidden xs:inline sm:inline">{tab.label}</span>
                  <span className="xs:hidden sm:hidden">{tab.label.split(' ')[0]}</span>
                  {tab.count > 0 && (
                    <span className={`ml-0.5 sm:ml-1 px-1 sm:px-1.5 py-0.5 text-[10px] sm:text-xs rounded-full ${
                      isActive ? 'bg-white/20' : 'bg-white'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                  {isActive && (
                    <motion.div
                      layoutId="activeShowcaseTab"
                      className="absolute inset-0 rounded-lg sm:rounded-xl -z-10"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Right side actions */}
          <div className="flex items-center justify-end gap-2 sm:gap-3">
            <button
              onClick={() => onViewAll("ordering", currentTab?.orderKey)}
              className="hidden sm:flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              View All
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-all duration-200 text-xs sm:text-sm ${
                isExpanded 
                  ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' 
                  : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
              }`}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                  <span className="font-medium">Hide</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                  <span className="font-medium">Show</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="p-4 sm:p-6">
                <AnimatePresence mode="wait">
                  {!currentTab?.ready ? (
                    <motion.div
                      key="skeleton"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6"
                    >
                      <ProductGridSkeleton viewMode="grid" count={4} />
                    </motion.div>
                  ) : currentTab?.listings?.length > 0 ? (
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, x: activeTab === 'bestsellers' ? -20 : 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: activeTab === 'bestsellers' ? 20 : -20 }}
                      transition={{ duration: 0.3 }}
                      className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6"
                    >
                      {currentTab.listings.slice(0, 4).map((product, index) => (
                        <motion.div
                          key={product.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05, duration: 0.3 }}
                        >
                          <ProductCard product={product} viewMode="grid" />
                        </motion.div>
                      ))}
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-center py-12"
                    >
                      <div className={`w-16 h-16 ${currentTab?.bgLight} rounded-full flex items-center justify-center mx-auto mb-4`}>
                        {currentTab && <currentTab.icon className={`w-8 h-8 ${currentTab.textColor}`} />}
                      </div>
                      <p className="text-gray-500">No products in this category yet</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Mobile View All Button */}
                <button
                  onClick={() => onViewAll("ordering", currentTab?.orderKey)}
                  className="sm:hidden w-full mt-4 py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  View All {currentTab?.label}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed State Preview */}
        {!isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="px-3 sm:px-4 py-2.5 sm:py-3 bg-gradient-to-r from-gray-50 to-white flex items-center justify-between gap-2"
          >
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className={`flex -space-x-2 flex-shrink-0`}>
                {currentTab?.listings?.slice(0, 3).map((product, i) => (
                  <div
                    key={product.id}
                    className="w-8 sm:w-10 h-8 sm:h-10 rounded-full border-2 border-white overflow-hidden bg-gray-200"
                    style={{ zIndex: 3 - i }}
                  >
                    <img
                      src={product.main_image_url || product.main_image || '/images/placeholder-product.jpg'}
                      alt=""
                      className="w-full h-full object-cover"
                      onError={(e) => e.target.src = '/images/placeholder-product.jpg'}
                    />
                  </div>
                ))}
                {(currentTab?.listings?.length || 0) > 3 && (
                  <div className="w-8 sm:w-10 h-8 sm:h-10 rounded-full border-2 border-white bg-gray-100 flex items-center justify-center text-[10px] sm:text-xs font-medium text-gray-600">
                    +{currentTab.listings.length - 3}
                  </div>
                )}
              </div>
              <span className="text-xs sm:text-sm text-gray-600 truncate">
                {currentTab?.listings?.length || 0} <span className="hidden xs:inline">products in</span> {currentTab?.label}
              </span>
            </div>
            <button
              onClick={() => setIsExpanded(true)}
              className={`text-xs sm:text-sm font-medium ${currentTab?.textColor} hover:underline whitespace-nowrap`}
            >
              <span className="hidden sm:inline">Expand to view</span>
              <span className="sm:hidden">View</span>
            </button>
          </motion.div>
        )}
      </div>
    </motion.section>
  );
}

// Pagination Component - Responsive numbered pagination
function Pagination({ currentPage, totalPages, totalItems, pageSize, onPageChange, isLoading }) {
  // Generate page numbers to display with ellipsis logic
  const getPageNumbers = () => {
    const pages = [];

    if (totalPages <= 7) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }

    // Always show first page
    pages.push(1);

    if (currentPage > 3) {
      pages.push("...");
    }

    // Pages around current
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (currentPage < totalPages - 2) {
      pages.push("...");
    }

    // Always show last page
    pages.push(totalPages);

    return pages;
  };

  // Compact page numbers for mobile (show fewer)
  const getMobilePageNumbers = () => {
    const pages = [];

    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }

    pages.push(1);

    if (currentPage > 2) {
      pages.push("...");
    }

    if (currentPage !== 1 && currentPage !== totalPages) {
      pages.push(currentPage);
    }

    if (currentPage < totalPages - 1) {
      pages.push("...");
    }

    pages.push(totalPages);

    return pages;
  };

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const desktopPages = getPageNumbers();
  const mobilePages = getMobilePageNumbers();

  return (
    <div className="mt-8 sm:mt-10">
      {/* Results summary */}
      <div className="text-center mb-3 sm:mb-4">
        <p className="text-xs sm:text-sm text-gray-500">
          Showing <span className="font-medium text-gray-700">{startItem}</span> -{" "}
          <span className="font-medium text-gray-700">{endItem}</span> of{" "}
          <span className="font-medium text-gray-700">{totalItems}</span> products
        </p>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-center gap-1 sm:gap-1.5">
        {/* Previous button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1 || isLoading}
          className={`flex items-center gap-1 px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
            currentPage <= 1 || isLoading
              ? "text-gray-300 cursor-not-allowed"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          }`}
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">Prev</span>
        </button>

        {/* Desktop page numbers */}
        <div className="hidden sm:flex items-center gap-1">
          {desktopPages.map((page, index) =>
            page === "..." ? (
              <span
                key={`ellipsis-${index}`}
                className="px-2 py-2 text-sm text-gray-400 select-none"
              >
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                disabled={isLoading}
                className={`min-w-[36px] h-9 px-2.5 rounded-lg text-sm font-medium transition-all ${
                  page === currentPage
                    ? "bg-blue-600 text-white shadow-md shadow-blue-600/25"
                    : isLoading
                    ? "text-gray-300 cursor-not-allowed"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
                aria-label={`Go to page ${page}`}
                aria-current={page === currentPage ? "page" : undefined}
              >
                {page}
              </button>
            )
          )}
        </div>

        {/* Mobile page numbers (compact) */}
        <div className="flex sm:hidden items-center gap-0.5">
          {mobilePages.map((page, index) =>
            page === "..." ? (
              <span
                key={`m-ellipsis-${index}`}
                className="px-1.5 py-1.5 text-xs text-gray-400 select-none"
              >
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                disabled={isLoading}
                className={`min-w-[32px] h-8 px-2 rounded-lg text-xs font-medium transition-all ${
                  page === currentPage
                    ? "bg-blue-600 text-white shadow-md shadow-blue-600/25"
                    : isLoading
                    ? "text-gray-300 cursor-not-allowed"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
                aria-label={`Go to page ${page}`}
                aria-current={page === currentPage ? "page" : undefined}
              >
                {page}
              </button>
            )
          )}
        </div>

        {/* Next button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || isLoading}
          className={`flex items-center gap-1 px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
            currentPage >= totalPages || isLoading
              ? "text-gray-300 cursor-not-allowed"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          }`}
          aria-label="Next page"
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Quick jump (desktop only, when many pages) */}
      {totalPages > 7 && (
        <div className="hidden md:flex items-center justify-center mt-3 gap-2">
          <span className="text-xs text-gray-400">Go to page:</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            defaultValue={currentPage}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const val = parseInt(e.target.value, 10);
                if (val >= 1 && val <= totalPages) {
                  onPageChange(val);
                }
              }
            }}
            className="w-16 px-2 py-1 text-sm text-center border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <span className="text-xs text-gray-400">of {totalPages}</span>
        </div>
      )}
    </div>
  );
}

// Main Browse Products Page
export function BrowseProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useContext(UserContext);
  
  const {
    listings,
    categories,
    loading,
    error,
    fetchListings,
    fetchCategories,
    fetchFeaturedListings,
    fetchRecentListings,
    fetchTrendingListings,
  } = useElMercado();

  // Local state
  const [viewMode, setViewMode] = useState("grid");
  const [showFilters, setShowFilters] = useState(false);
  const [showMobileCategories, setShowMobileCategories] = useState(false);
  const [featuredListings, setFeaturedListings] = useState([]);
  const [recentListings, setRecentListings] = useState([]);
  const [trendingListings, setTrendingListings] = useState([]);
  const [featuredReady, setFeaturedReady] = useState(false);
  const [recentReady, setRecentReady] = useState(false);
  const [trendingReady, setTrendingReady] = useState(false);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [isFiltering, setIsFiltering] = useState(false);
  
  // Ref to track the previous filters for comparison
  const prevFiltersRef = useRef(null);
  // Ref to track debounce timeout
  const debounceRef = useRef(null);
  // Ref to store displayed listings (prevents flickering)
  const [displayedListings, setDisplayedListings] = useState([]);
  // Track if content is ready to show (with small delay for smooth transition)
  const [contentReady, setContentReady] = useState(false);

  const PAGE_SIZE = 20;

  // Get filters from URL params - stable reference
  const filters = useMemo(() => ({
    search: searchParams.get("search") || "",
    category: searchParams.get("category") || "",
    listing_type: searchParams.get("type") || "",
    condition: searchParams.get("condition") || "",
    min_price: searchParams.get("min_price") || "",
    max_price: searchParams.get("max_price") || "",
    ordering: searchParams.get("sort") || "-created_at",
    page: parseInt(searchParams.get("page") || "1", 10),
  }), [searchParams]);

  // Derived pagination values
  const currentPage = filters.page;
  const totalPages = Math.ceil(pagination.count / PAGE_SIZE);

  // Update URL params when filters change (with transition)
  const updateFilters = useCallback((key, value) => {
    setIsFiltering(true);
    const newParams = new URLSearchParams(searchParams);
    const paramKey = key === "listing_type" ? "type" : key === "ordering" ? "sort" : key;
    if (value) {
      newParams.set(paramKey, value);
    } else {
      newParams.delete(paramKey);
    }
    // Reset to page 1 when any filter other than page itself changes
    if (key !== "page") {
      newParams.delete("page");
    }
    setSearchParams(newParams, { replace: true });
  }, [searchParams, setSearchParams]);

  // Navigate to a specific page
  const goToPage = useCallback((page) => {
    if (page < 1 || page > totalPages || page === currentPage) return;
    updateFilters("page", page > 1 ? String(page) : "");
    // Scroll to top of product listing area
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [totalPages, currentPage, updateFilters]);

  // Reset all filters
  const resetFilters = useCallback(() => {
    setIsFiltering(true);
    setSearchParams(new URLSearchParams(), { replace: true });
  }, [setSearchParams]);

  // Consolidated data fetching - runs once on mount
  useEffect(() => {
    if (dataLoaded) return;
    
    const loadAllData = async () => {
      try {
        // Fetch categories first
        await fetchCategories();
        
        // Then fetch featured, recent, and trending in parallel
        const [featured, recent, trending] = await Promise.all([
          fetchFeaturedListings(),
          fetchRecentListings(),
          fetchTrendingListings(),
        ]);
        
        setFeaturedListings(featured || []);
        setRecentListings(recent || []);
        setTrendingListings(trending || []);
        
        // Set ready states with small delays for smooth transitions
        setTimeout(() => setFeaturedReady(true), 150);
        setTimeout(() => setRecentReady(true), 200);
        setTimeout(() => setTrendingReady(true), 250);
        
        setDataLoaded(true);
      } catch (err) {
        console.error("Error loading initial data:", err);
        setDataLoaded(true); // Still mark as loaded to prevent retries
        setFeaturedReady(true);
        setRecentReady(true);
        setTrendingReady(true);
      }
    };
    
    loadAllData();
  }, [dataLoaded, fetchCategories, fetchFeaturedListings, fetchRecentListings, fetchTrendingListings]);

  // Fetch listings when filters change (debounced to prevent flickering)
  useEffect(() => {
    // Don't fetch until initial data is loaded
    if (!dataLoaded) return;
    
    // Create a stable filter string for comparison
    const filterString = JSON.stringify(filters);
    
    // Skip if filters haven't actually changed
    if (prevFiltersRef.current === filterString) {
      return;
    }
    
    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    // Set filtering state for visual feedback
    setIsFiltering(true);
    
    // Debounce the API call (100ms for instant filters, longer for price)
    const debounceTime = filters.min_price || filters.max_price ? 300 : 100;
    
    debounceRef.current = setTimeout(async () => {
      prevFiltersRef.current = filterString;
      
      const result = await fetchListings(filters);
      if (result) {
        setPagination({
          count: result.count || 0,
          next: result.next,
          previous: result.previous,
        });
      }
      setIsInitialLoad(false);
      setIsFiltering(false);
    }, debounceTime);
    
    // Cleanup timeout on unmount or filter change
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [filters, dataLoaded, fetchListings]);

  // Update displayed listings smoothly (only when we have new data)
  useEffect(() => {
    // Only update displayed listings when:
    // 1. We have new listings data
    // 2. Not actively filtering (to prevent flickering)
    // 3. Or when loading completes with no results
    if (!isFiltering && (!loading || listings.length === 0)) {
      setContentReady(false);
      setDisplayedListings(listings);
      // Small delay to prevent flickering when content changes
      setTimeout(() => {
        setContentReady(true);
      }, 150);
    }
  }, [listings, loading, isFiltering]);

  useEffect(() => {
    scrollToTop();
  }, []);

  // Determine if we're showing filtered results or home view
  // Include non-default ordering as an active filter (so "View All" buttons work)
  const hasActiveFilters = filters.search || filters.category || filters.listing_type || filters.condition || filters.min_price || filters.max_price || (filters.ordering && filters.ordering !== "-created_at");

  return (
    <>
      <Helmet>
        <title>Browse Products | El Mercado - BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Browse and discover amazing products from sellers in the KNUST community. Find electronics, books, services, and more!"
        />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content={`${window.location.origin}/el-mercado/browse`} />
        <meta property="og:title" content="El Mercado - KNUST's Official Marketplace" />
        <meta property="og:description" content="Browse and discover amazing products from sellers in the KNUST community. Find electronics, books, services, and more!" />
        <meta property="og:image" content={`${window.location.origin}/images/el-mercado-og.jpg`} />
        <meta property="og:site_name" content="El Mercado - BIO-CHEM KNUST" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content={`${window.location.origin}/el-mercado/browse`} />
        <meta name="twitter:title" content="El Mercado - KNUST's Official Marketplace" />
        <meta name="twitter:description" content="Browse and discover amazing products from sellers in the KNUST community." />
        <meta name="twitter:image" content={`${window.location.origin}/images/el-mercado-og.jpg`} />
        
        {/* Additional SEO */}
        <link rel="canonical" href={`${window.location.origin}/el-mercado/browse`} />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          {/* Hero Section */}
          <section className="py-6 sm:py-8 md:py-12 px-4 relative overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10">
              <div
                className="absolute inset-0"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                }}
              />
            </div>
            
            <div className="max-w-7xl mx-auto relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-4 sm:mb-6 md:mb-8"
              >
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 sm:mb-3">
                  Discover Amazing Products
                </h1>
                <p className="text-sm sm:text-base text-blue-800 max-w-2xl mx-auto px-2">
                  Browse through thousands of products from verified sellers in the KNUST community
                </p>
              </motion.div>
              
              {/* Search Bar */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="max-w-2xl mx-auto"
              >
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    updateFilters("search", formData.get("search"));
                  }}
                  className="relative"
                >
                  <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 w-4 sm:w-5 h-4 sm:h-5 text-gray-400" />
                  <input
                    type="text"
                    name="search"
                    defaultValue={filters.search}
                    placeholder="Search products..."
                    className="w-full pl-10 sm:pl-12 pr-20 sm:pr-24 py-3 sm:py-4 rounded-xl text-sm sm:text-base text-gray-900 placeholder-gray-400 bg-white shadow-lg focus:ring-4 focus:ring-white/30 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="absolute right-1.5 sm:right-2 top-1/2 -translate-y-1/2 px-3 sm:px-6 py-1.5 sm:py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm sm:text-base font-semibold rounded-lg transition-colors"
                  >
                    <Search className="w-4 h-4 sm:hidden" />
                    <span className="hidden sm:inline">Search</span>
                  </button>
                </form>

                {/* Quick Action Links */}
                {user && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="flex justify-center gap-2 sm:gap-4 mt-3 sm:mt-4 flex-wrap"
                  >
                    <Link
                      to="/el-mercado/favorites"
                      className="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-white/90 backdrop-blur-sm text-gray-700 rounded-lg shadow hover:bg-white transition-colors text-xs sm:text-sm"
                    >
                      <Heart className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-red-500" />
                      <span className="font-medium">Favorites</span>
                    </Link>
                    <Link
                      to="/el-mercado/following"
                      className="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-white/90 backdrop-blur-sm text-gray-700 rounded-lg shadow hover:bg-white transition-colors text-xs sm:text-sm"
                    >
                      <Users className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-purple-600" />
                      <span className="font-medium">Following</span>
                    </Link>
                    <Link
                      to="/el-mercado/messages"
                      className="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-white/90 backdrop-blur-sm text-gray-700 rounded-lg shadow hover:bg-white transition-colors text-xs sm:text-sm"
                    >
                      <MessageCircle className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-blue-600" />
                      <span className="font-medium">Messages</span>
                    </Link>
                  </motion.div>
                )}
              </motion.div>
            </div>
          </section>

          <div className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6 md:py-8">
            {/* Featured & Recent Showcase Section (only show on home view without filters) */}
            {!hasActiveFilters && !isInitialLoad && (featuredListings.length > 0 || recentListings.length > 0 || trendingListings.length > 0) && (
              <ShowcaseSection
                featuredListings={featuredListings}
                recentListings={recentListings}
                trendingListings={trendingListings}
                featuredReady={featuredReady}
                recentReady={recentReady}
                trendingReady={trendingReady}
                onViewAll={updateFilters}
              />
            )}

            {/* Main Browse Section */}
            <section>
              {/* Toolbar */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4 mb-4 sm:mb-6">
                <div className="flex flex-col gap-3 sm:gap-4">
                  {/* Left side - Results count and active filters */}
                  <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
                    <span className="text-xs sm:text-sm text-gray-600 flex items-center gap-1.5 sm:gap-2">
                      {isFiltering ? (
                        <>
                          <Loader2 className="w-3.5 sm:w-4 h-3.5 sm:h-4 animate-spin text-blue-600" />
                          <span className="text-blue-600">Filtering...</span>
                        </>
                      ) : (
                        <>
                          <span className="font-semibold text-gray-900">{pagination.count || displayedListings.length}</span> products found
                        </>
                      )}
                    </span>
                    
                    {/* Active filter badges */}
                    {hasActiveFilters && (
                      <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                        {filters.search && (
                          <span className="inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 sm:py-1 bg-blue-100 text-blue-700 rounded-full text-[10px] sm:text-xs">
                            <span className="max-w-[80px] sm:max-w-none truncate">Search: {filters.search}</span>
                            <button onClick={() => updateFilters("search", "")}>
                              <X className="w-2.5 sm:w-3 h-2.5 sm:h-3" />
                            </button>
                          </span>
                        )}
                        {filters.category && (
                          <span className="inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 sm:py-1 bg-green-100 text-green-700 rounded-full text-[10px] sm:text-xs">
                            Category
                            <button onClick={() => updateFilters("category", "")}>
                              <X className="w-2.5 sm:w-3 h-2.5 sm:h-3" />
                            </button>
                          </span>
                        )}
                        {filters.listing_type && (
                          <span className="inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 sm:py-1 bg-purple-100 text-purple-700 rounded-full text-[10px] sm:text-xs">
                            {LISTING_TYPES.find((t) => t.value === filters.listing_type)?.label}
                            <button onClick={() => updateFilters("listing_type", "")}>
                              <X className="w-2.5 sm:w-3 h-2.5 sm:h-3" />
                            </button>
                          </span>
                        )}
                        <button
                          onClick={resetFilters}
                          className="text-[10px] sm:text-xs text-red-600 hover:text-red-700 font-medium"
                        >
                          Clear all
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* Right side - Controls */}
                  <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                    {/* Messages link - hidden on small mobile */}
                    <Link
                      to="/el-mercado/messages"
                      className="hidden xs:flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-colors"
                    >
                      <MessageCircle className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                      <span className="hidden md:inline">Messages</span>
                    </Link>
                    
                    {/* Favorites link - hidden on small mobile */}
                    <Link
                      to="/el-mercado/favorites"
                      className="hidden xs:flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-colors"
                    >
                      <Heart className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                      <span className="hidden md:inline">Favorites</span>
                    </Link>
                    
                    {/* Mobile filter buttons */}
                    <button
                      onClick={() => setShowMobileCategories(true)}
                      className="lg:hidden flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-gray-50"
                    >
                      <Tag className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                      <span className="hidden xs:inline">Categories</span>
                    </button>
                    <button
                      onClick={() => setShowFilters(!showFilters)}
                      className="lg:hidden flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-gray-50"
                    >
                      <Filter className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
                      <span className="hidden xs:inline">Filters</span>
                    </button>
                    
                    {/* Sort */}
                    <div className="relative flex-1 sm:flex-none min-w-0">
                      <select
                        value={filters.ordering}
                        onChange={(e) => updateFilters("ordering", e.target.value)}
                        className="appearance-none w-full sm:w-auto pl-2 sm:pl-3 pr-8 sm:pr-10 py-1.5 sm:py-2 border border-gray-200 rounded-lg text-xs sm:text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white cursor-pointer"
                      >
                        {SORT_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <ArrowUpDown className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 w-3.5 sm:w-4 h-3.5 sm:h-4 text-gray-400 pointer-events-none" />
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
              </div>

              {/* Main Content Grid */}
              <div className="flex gap-4 sm:gap-6">
                {/* Sidebar - Categories & Filters (Desktop) */}
                <div className="hidden lg:block w-56 xl:w-64 flex-shrink-0 space-y-4 sm:space-y-6">
                  <CategorySidebar
                    categories={categories}
                    selectedCategory={filters.category}
                    onCategoryChange={(cat) => updateFilters("category", cat)}
                  />
                  <FiltersPanel
                    filters={filters}
                    onFilterChange={updateFilters}
                    onReset={resetFilters}
                  />
                </div>

                {/* Products Grid */}
                <div className="flex-1">
                  {(loading && isInitialLoad) || !dataLoaded ? (
                    <ProductGridSkeleton viewMode={viewMode} />
                  ) : error ? (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                      <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
                      <h3 className="font-semibold text-red-700 mb-2">Error loading products</h3>
                      <p className="text-red-600 text-sm mb-4">{error}</p>
                      <button
                        onClick={() => fetchListings(filters)}
                        className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                      >
                        Try Again
                      </button>
                    </div>
                  ) : displayedListings.length === 0 ? (
                    <EmptyState searchQuery={filters.search} onReset={resetFilters} />
                  ) : (
                    <div className="relative">
                      {/* Loading overlay when filtering */}
                      {isFiltering && (
                        <div className="absolute inset-0 bg-white/70 backdrop-blur-[2px] z-10 flex items-center justify-center rounded-xl">
                          <div className="flex flex-col items-center gap-3 bg-white px-6 py-4 rounded-lg shadow-lg">
                            <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
                            <span className="text-sm font-medium text-gray-700">Updating results...</span>
                          </div>
                        </div>
                      )}
                      
                      <AnimatePresence mode="wait">
                        <motion.div
                          key={displayedListings.length}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: contentReady ? 1 : 0 }}
                          transition={{ duration: 0.3 }}
                          className={
                            viewMode === "list"
                              ? "space-y-3 sm:space-y-4"
                              : "grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-2 sm:gap-4 lg:gap-6"
                          }
                        >
                          {displayedListings.map((product, index) => (
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
                      </AnimatePresence>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <Pagination
                          currentPage={currentPage}
                          totalPages={totalPages}
                          totalItems={pagination.count}
                          pageSize={PAGE_SIZE}
                          onPageChange={goToPage}
                          isLoading={isFiltering || loading}
                        />
                      )}
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>

          {/* Mobile Category Sidebar */}
          <AnimatePresence>
            {showMobileCategories && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                  onClick={() => setShowMobileCategories(false)}
                />
                <motion.div
                  initial={{ x: -300 }}
                  animate={{ x: 0 }}
                  exit={{ x: -300 }}
                  className="fixed left-0 top-0 bottom-0 w-[85vw] max-w-xs sm:w-80 bg-white z-50 lg:hidden overflow-y-auto"
                >
                  <div className="p-4">
                    <CategorySidebar
                      categories={categories}
                      selectedCategory={filters.category}
                      onCategoryChange={(cat) => updateFilters("category", cat)}
                      isMobile
                      onClose={() => setShowMobileCategories(false)}
                    />
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Mobile Filters Panel */}
          <AnimatePresence>
            {showFilters && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                  onClick={() => setShowFilters(false)}
                />
                <motion.div
                  initial={{ y: "100%" }}
                  animate={{ y: 0 }}
                  exit={{ y: "100%" }}
                  className="fixed left-0 right-0 bottom-0 bg-white z-50 lg:hidden rounded-t-2xl max-h-[85vh] overflow-y-auto"
                >
                  {/* Drag handle for mobile */}
                  <div className="sticky top-0 bg-white pt-2 pb-1 flex justify-center">
                    <div className="w-10 h-1 bg-gray-300 rounded-full" />
                  </div>
                  <div className="p-3 sm:p-4">
                    <div className="flex items-center justify-between mb-3 sm:mb-4">
                      <h3 className="text-base sm:text-lg font-semibold">Filters</h3>
                      <button
                        onClick={() => setShowFilters(false)}
                        className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full"
                      >
                        <X className="w-4 sm:w-5 h-4 sm:h-5" />
                      </button>
                    </div>
                    <FiltersPanel
                      filters={filters}
                      onFilterChange={updateFilters}
                      onReset={() => {
                        resetFilters();
                        setShowFilters(false);
                      }}
                    />
                    <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-gray-100">
                      <button
                        onClick={() => setShowFilters(false)}
                        className="w-full py-2.5 sm:py-3 bg-blue-600 text-white text-sm sm:text-base font-semibold rounded-xl hover:bg-blue-700 transition-colors"
                      >
                        Apply Filters
                      </button>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default BrowseProductsPage;
