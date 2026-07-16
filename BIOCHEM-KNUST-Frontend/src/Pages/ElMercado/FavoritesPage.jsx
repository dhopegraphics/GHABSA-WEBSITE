import { useEffect, useState, useCallback, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Heart,
  ShoppingCart,
  Trash2,
  Package,
  Star,
  Store,
  ArrowLeft,
  Loader2,
  AlertCircle,
  ShoppingBag,
  MessageCircle,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { useCart } from "../../Context/CartContext";
import { UserContext } from "../../Context/UserContext";

// Format price with currency
const formatPrice = (price, currency = "GHS") => {
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: currency,
  }).format(price);
};

// Animation variants
const cardVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1, transition: { duration: 0.3 } },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } },
};

// Favorite Item Card
function FavoriteCard({ favorite, onRemove, onAddToCart }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);

  const listing = favorite.listing;
  if (!listing) return null;

  const imageUrl = listing.main_image_url || listing.main_image || "/images/placeholder-product.jpg";
  const discountPercentage = listing.discount_percentage || 0;
  const hasDiscount = discountPercentage > 0;

  const handleRemove = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setRemoving(true);
    await onRemove(listing.slug);
  };

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!listing.is_in_stock || addingToCart) return;
    
    setAddingToCart(true);
    onAddToCart(listing);
    setTimeout(() => setAddingToCart(false), 500);
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      layout
      className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all group"
    >
      <Link to={`/el-mercado/products/${listing.slug}`}>
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
              <p className="text-xs text-gray-500 font-medium line-clamp-2">{listing.title}</p>
              <span className="text-[10px] text-gray-400 mt-1">Image unavailable</span>
            </div>
          )}
          
          <img
            src={imageUrl}
            alt={listing.title}
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
            {!listing.is_in_stock && (
              <span className="bg-gray-800/90 text-white text-xs font-medium px-2.5 py-1 rounded-full">
                Out of Stock
              </span>
            )}
          </div>
          
          {/* Remove from favorites button */}
          <button
            onClick={handleRemove}
            disabled={removing}
            className="absolute top-3 right-3 p-2.5 rounded-full shadow-lg transition-all bg-red-500 text-white hover:bg-red-600 disabled:opacity-50"
          >
            {removing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Heart className="w-5 h-5 fill-current" />
            )}
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4">
          {/* Category & Type */}
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              listing.listing_type === "PRODUCT" 
                ? "bg-blue-50 text-blue-700"
                : listing.listing_type === "DIGITAL"
                ? "bg-purple-50 text-purple-700"
                : "bg-green-50 text-green-700"
            }`}>
              {listing.listing_type_display || listing.listing_type}
            </span>
            <span className="text-xs text-gray-400 truncate">
              {listing.category_name}
            </span>
          </div>
          
          {/* Title */}
          <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
            {listing.title}
          </h3>
          
          {/* Rating */}
          <div className="flex items-center gap-2 mb-3">
            {listing.average_rating > 0 ? (
              <>
                <div className="flex items-center gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-3.5 h-3.5 ${
                        i < Math.floor(listing.average_rating)
                          ? "text-yellow-400 fill-yellow-400"
                          : "text-gray-300"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-500">
                  ({listing.review_count})
                </span>
              </>
            ) : (
              <span className="text-xs text-gray-400">No reviews yet</span>
            )}
          </div>
          
          {/* Seller */}
          {listing.seller && (
            <div className="flex items-center gap-1.5 mb-3 text-sm text-gray-500">
              <Store className="w-3.5 h-3.5" />
              <span className="truncate">{listing.seller.business_name}</span>
              {listing.seller.is_verified && (
                <span className="text-blue-500 text-xs">✓</span>
              )}
            </div>
          )}
          
          {/* Price */}
          <div className="flex items-baseline gap-2 mb-4">
            <span className="text-lg font-bold text-gray-900">
              {formatPrice(listing.price, listing.currency)}
            </span>
            {hasDiscount && (
              <span className="text-sm text-gray-400 line-through">
                {formatPrice(listing.compare_at_price, listing.currency)}
              </span>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={handleAddToCart}
              disabled={!listing.is_in_stock || addingToCart}
              className={`flex-1 py-2.5 px-4 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-colors ${
                listing.is_in_stock
                  ? "bg-blue-600 hover:bg-blue-700 text-white"
                  : "bg-gray-200 text-gray-500 cursor-not-allowed"
              }`}
            >
              <ShoppingCart className={`w-4 h-4 ${addingToCart ? 'animate-bounce' : ''}`} />
              {addingToCart ? 'Added!' : listing.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
            </button>
            <button
              onClick={handleRemove}
              disabled={removing}
              className="p-2.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-colors"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// Empty State
function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center py-16"
    >
      <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <Heart className="w-12 h-12 text-gray-400" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-3">No Favorites Yet</h2>
      <p className="text-gray-500 mb-8 max-w-md mx-auto">
        Start exploring and save items you love by clicking the heart icon on any product.
      </p>
      <Link
        to="/el-mercado/browse"
        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
      >
        <ShoppingBag className="w-5 h-5" />
        Start Shopping
      </Link>
    </motion.div>
  );
}

// Login Required State
function LoginRequired() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center py-16"
    >
      <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <AlertCircle className="w-12 h-12 text-blue-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-3">Login Required</h2>
      <p className="text-gray-500 mb-8 max-w-md mx-auto">
        Please log in to view and manage your favorite items.
      </p>
      <Link
        to="/login"
        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
      >
        Log In
      </Link>
    </motion.div>
  );
}

// Loading Skeleton
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="bg-white rounded-xl overflow-hidden border border-gray-100">
          <div className="aspect-square bg-gray-200 animate-pulse" />
          <div className="p-4 space-y-3">
            <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
            <div className="h-5 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
            <div className="h-10 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Main Favorites Page
export function FavoritesPage() {
  const { fetchFavorites, removeFromFavorites } = useElMercado();
  const { addToCart } = useCart();
  const { user } = useContext(UserContext);
  const isAuthenticated = !!user;
  
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    scrollToTop();
  }, []);

  const loadFavorites = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const result = await fetchFavorites();
    
    if (result.success) {
      setFavorites(result.data);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  }, [fetchFavorites, isAuthenticated]);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const handleRemoveFavorite = async (slug) => {
    const result = await removeFromFavorites(slug);
    
    if (result.success) {
      setFavorites(prev => prev.filter(fav => fav.listing?.slug !== slug));
    }
  };

  const handleAddToCart = (listing) => {
    const cartItem = {
      id: listing.id,
      slug: listing.slug,
      title: listing.title,
      price: listing.price,
      currency: listing.currency,
      main_image: listing.main_image_url || listing.main_image,
      stock_quantity: listing.stock_quantity,
      seller: listing.seller,
    };
    
    addToCart(cartItem, 1);
  };

  const handleAddAllToCart = () => {
    const inStockFavorites = favorites.filter(fav => fav.listing?.is_in_stock);
    
    inStockFavorites.forEach(fav => {
      handleAddToCart(fav.listing);
    });
  };

  return (
    <>
      <Helmet>
        <title>My Favorites | El Mercado - BIO-CHEM KNUST</title>
        <meta name="description" content="View and manage your favorite items on El Mercado" />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          <div className="max-w-7xl mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <Link
                  to="/el-mercado/browse"
                  className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Back to Browse
                </Link>
                
                {/* Messages link */}
                <Link
                  to="/el-mercado/messages"
                  className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-colors"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span className="hidden sm:inline">Messages</span>
                </Link>
              </div>
              
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Heart className="w-8 h-8 text-red-500 fill-red-500" />
                    My Favorites
                  </h1>
                  {isAuthenticated && favorites.length > 0 && (
                    <p className="text-gray-500 mt-1">
                      {favorites.length} item{favorites.length !== 1 ? 's' : ''} saved
                    </p>
                  )}
                </div>
                
                {isAuthenticated && favorites.length > 0 && (
                  <button
                    onClick={handleAddAllToCart}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
                  >
                    <ShoppingCart className="w-5 h-5" />
                    Add All to Cart
                  </button>
                )}
              </div>
            </div>

            {/* Content */}
            {!isAuthenticated ? (
              <LoginRequired />
            ) : loading ? (
              <LoadingSkeleton />
            ) : error ? (
              <div className="text-center py-16">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <p className="text-gray-500">{error}</p>
                <button
                  onClick={loadFavorites}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Try Again
                </button>
              </div>
            ) : favorites.length === 0 ? (
              <EmptyState />
            ) : (
              <AnimatePresence mode="popLayout">
                <motion.div
                  layout
                  className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                >
                  {favorites.map((favorite) => (
                    <FavoriteCard
                      key={favorite.id}
                      favorite={favorite}
                      onRemove={handleRemoveFavorite}
                      onAddToCart={handleAddToCart}
                    />
                  ))}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default FavoritesPage;
