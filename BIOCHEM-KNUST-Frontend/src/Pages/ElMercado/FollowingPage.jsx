import { useEffect, useState, useCallback, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Users,
  ShoppingCart,
  UserMinus,
  Package,
  Star,
  Store,
  ArrowLeft,
  Loader2,
  AlertCircle,
  ShoppingBag,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { useCart } from "../../Context/CartContext";
import { UserContext } from "../../Context/UserContext";
import { useAuthModals } from "../../Context/AuthModalsContext";

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

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

// Followed Seller Card Component
function FollowedSellerCard({ follow, onUnfollow }) {
  const [unfollowing, setUnfollowing] = useState(false);
  const seller = follow.seller;

  if (!seller) return null;

  const handleUnfollow = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setUnfollowing(true);
    await onUnfollow(seller.slug);
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      layout
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-lg transition-all"
    >
      <Link to={`/el-mercado/store/${seller.slug}`} className="block">
        <div className="flex items-center gap-4">
          {/* Seller Logo */}
          <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center overflow-hidden border-2 border-white shadow">
            {seller.logo_url ? (
              <img
                src={seller.logo_url}
                alt={seller.display_name}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-2xl font-bold text-blue-600">
                {seller.display_name?.charAt(0)?.toUpperCase() || "S"}
              </span>
            )}
          </div>

          {/* Seller Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900 truncate">
                {seller.display_name}
              </h3>
              {seller.is_verified && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                  ✓
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">
              {seller.seller_type_display || seller.seller_type}
            </p>
            {seller.average_rating > 0 && (
              <div className="flex items-center gap-1 mt-1">
                <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                <span className="text-sm text-gray-600">
                  {parseFloat(seller.average_rating).toFixed(1)} ({seller.total_reviews} reviews)
                </span>
              </div>
            )}
          </div>

          {/* Unfollow Button */}
          <button
            onClick={handleUnfollow}
            disabled={unfollowing}
            className="p-2 rounded-lg bg-gray-100 hover:bg-red-100 text-gray-600 hover:text-red-600 transition-colors"
          >
            {unfollowing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <UserMinus className="w-5 h-5" />
            )}
          </button>
        </div>
      </Link>
    </motion.div>
  );
}

// Listing Card for followed sellers' products
function ListingCard({ listing, onAddToCart }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);

  const imageUrl = listing.main_image_url || listing.main_image || "/images/placeholder-product.jpg";
  const discountPercentage = listing.discount_percentage || 0;
  const hasDiscount = discountPercentage > 0;

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
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
              <Package className="w-12 h-12 text-gray-400" />
            </div>
          )}
          
          {imageError && (
            <div className="absolute inset-0 bg-gray-100 flex flex-col items-center justify-center p-4 text-center">
              <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-2">
                <Package className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-xs text-gray-500 font-medium line-clamp-2">{listing.title}</p>
            </div>
          )}
          
          <img
            src={imageUrl}
            alt={listing.title}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${
              imageLoaded && !imageError ? "opacity-100" : "opacity-0"
            }`}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />

          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-1">
            {hasDiscount && (
              <span className="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded">
                -{Math.round(discountPercentage)}%
              </span>
            )}
            {!listing.is_in_stock && (
              <span className="px-2 py-1 bg-gray-900 text-white text-xs font-bold rounded">
                Out of Stock
              </span>
            )}
          </div>

          {/* Quick Add to Cart */}
          {listing.listing_type === "PRODUCT" && listing.is_in_stock && (
            <button
              onClick={handleAddToCart}
              disabled={addingToCart}
              className="absolute bottom-2 right-2 p-2 bg-white/90 backdrop-blur rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-all hover:bg-blue-600 hover:text-white disabled:opacity-50"
            >
              {addingToCart ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ShoppingCart className="w-4 h-4" />
              )}
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Seller Info */}
          <Link
            to={`/el-mercado/store/${listing.seller_slug || listing.seller?.slug}`}
            className="flex items-center gap-2 mb-2 text-xs text-gray-500 hover:text-blue-600"
            onClick={(e) => e.stopPropagation()}
          >
            <Store className="w-3 h-3" />
            <span className="truncate">{listing.seller_name || listing.seller?.display_name}</span>
          </Link>

          {/* Title */}
          <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
            {listing.title}
          </h3>

          {/* Rating */}
          {listing.average_rating > 0 && (
            <div className="flex items-center gap-1 mb-2">
              <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
              <span className="text-sm text-gray-600">
                {parseFloat(listing.average_rating).toFixed(1)}
              </span>
              <span className="text-xs text-gray-400">({listing.review_count || 0})</span>
            </div>
          )}

          {/* Price */}
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-blue-600">
              {formatPrice(listing.effective_price || listing.price)}
            </span>
            {hasDiscount && (
              <span className="text-sm text-gray-400 line-through">
                {formatPrice(listing.price)}
              </span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// Main Following Page
export function FollowingPage() {
  const { user } = useContext(UserContext);
  const { 
    fetchFollowedSellers, 
    fetchFollowedSellersListings, 
    unfollowSeller 
  } = useElMercado();
  const { addToCart } = useCart();
  const { openLoginModal } = useAuthModals();

  const [activeTab, setActiveTab] = useState("listings"); // "listings" or "sellers"
  const [followedSellers, setFollowedSellers] = useState([]);
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sellersResult, listingsResult] = await Promise.all([
        fetchFollowedSellers(),
        fetchFollowedSellersListings(),
      ]);

      if (sellersResult.success) {
        setFollowedSellers(sellersResult.data);
      }
      if (listingsResult.success) {
        setListings(listingsResult.data);
      }
    } catch (err) {
      console.error("Error fetching following data:", err);
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [fetchFollowedSellers, fetchFollowedSellersListings]);

  useEffect(() => {
    scrollToTop();
    fetchData();
  }, [fetchData]);

  // Handle unfollow
  const handleUnfollow = async (slug) => {
    const result = await unfollowSeller(slug);
    if (result.success) {
      // Remove from local state
      setFollowedSellers(prev => prev.filter(f => f.seller?.slug !== slug));
      // Refresh listings to remove unfollowed seller's products
      const listingsResult = await fetchFollowedSellersListings();
      if (listingsResult.success) {
        setListings(listingsResult.data);
      }
    }
  };

  // Handle add to cart
  const handleAddToCart = (listing) => {
    addToCart({
      id: listing.id,
      slug: listing.slug,
      title: listing.title,
      price: listing.effective_price || listing.price,
      image: listing.main_image_url || listing.main_image,
      seller_slug: listing.seller_slug || listing.seller?.slug,
      seller_name: listing.seller_name || listing.seller?.display_name,
      listing_type: listing.listing_type,
    });
  };

  // Not logged in state
  if (!user) {
    return (
      <>
        <Helmet>
          <title>Following | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20">
          <div className="max-w-7xl mx-auto px-4 py-16 text-center">
            <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-gray-400" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Sign In Required</h2>
              <p className="text-gray-600 mb-6">
                Please sign in to see sellers you follow and their products.
              </p>
              <button
                onClick={openLoginModal}
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>Following | El Mercado - BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="View products from sellers you follow on El Mercado."
        />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          <div className="max-w-7xl mx-auto px-4">
            {/* Header */}
            <div className="mb-8">
              <Link
                to="/el-mercado/browse"
                className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600 mb-4"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Browse
              </Link>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Following</h1>
                  <p className="text-gray-600 mt-1">
                    Products and sellers you follow
                  </p>
                </div>

                {/* Tab Buttons */}
                <div className="flex gap-2 bg-gray-100 p-1 rounded-xl">
                  <button
                    onClick={() => setActiveTab("listings")}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      activeTab === "listings"
                        ? "bg-white shadow text-blue-600"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Package className="w-4 h-4" />
                      Products ({listings.length})
                    </span>
                  </button>
                  <button
                    onClick={() => setActiveTab("sellers")}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      activeTab === "sellers"
                        ? "bg-white shadow text-blue-600"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Store className="w-4 h-4" />
                      Sellers ({followedSellers.length})
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <p className="text-red-600">{error}</p>
                <button
                  onClick={fetchData}
                  className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Content */}
            {!loading && !error && (
              <AnimatePresence mode="wait">
                {activeTab === "listings" ? (
                  // Listings Tab
                  <motion.div
                    key="listings"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {listings.length === 0 ? (
                      <div className="text-center py-16">
                        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <Package className="w-12 h-12 text-gray-300" />
                        </div>
                        <h2 className="text-xl font-bold text-gray-900 mb-2">
                          No Products Yet
                        </h2>
                        <p className="text-gray-600 mb-6 max-w-md mx-auto">
                          {followedSellers.length > 0
                            ? "The sellers you follow haven't posted any products yet."
                            : "Follow sellers to see their products here."}
                        </p>
                        <Link
                          to="/el-mercado/browse"
                          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
                        >
                          <ShoppingBag className="w-5 h-5" />
                          Browse Products
                        </Link>
                      </div>
                    ) : (
                      <motion.div
                        variants={staggerContainer}
                        initial="initial"
                        animate="animate"
                        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
                      >
                        {listings.map((listing) => (
                          <ListingCard
                            key={listing.id || listing.slug}
                            listing={listing}
                            onAddToCart={handleAddToCart}
                          />
                        ))}
                      </motion.div>
                    )}
                  </motion.div>
                ) : (
                  // Sellers Tab
                  <motion.div
                    key="sellers"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {followedSellers.length === 0 ? (
                      <div className="text-center py-16">
                        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <Users className="w-12 h-12 text-gray-300" />
                        </div>
                        <h2 className="text-xl font-bold text-gray-900 mb-2">
                          No Followed Sellers
                        </h2>
                        <p className="text-gray-600 mb-6 max-w-md mx-auto">
                          Follow sellers to stay updated with their latest products and offers.
                        </p>
                        <Link
                          to="/el-mercado/browse"
                          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
                        >
                          <Store className="w-5 h-5" />
                          Discover Sellers
                        </Link>
                      </div>
                    ) : (
                      <motion.div
                        variants={staggerContainer}
                        initial="initial"
                        animate="animate"
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                      >
                        {followedSellers.map((follow) => (
                          <FollowedSellerCard
                            key={follow.id}
                            follow={follow}
                            onUnfollow={handleUnfollow}
                          />
                        ))}
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            )}
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}
