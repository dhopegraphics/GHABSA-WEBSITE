import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Helmet } from "react-helmet-async";
import { 
  ArrowLeft, 
  Star, 
  Package, 
  AlertCircle,
  Loader2,
  CheckCircle,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { useElMercado } from "../../Context/ElMercadoContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { scrollToTop } from "../../utils/scrollToTop";

export function WriteReviewPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { fetchListingBySlug } = useElMercado();
  const axiosInstance = useAxiosWithRefresh();
  
  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewStatus, setReviewStatus] = useState(null); // 'already_reviewed', 'not_purchased', etc.
  
  // Review form state
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    scrollToTop();
  }, []);

  useEffect(() => {
    const loadProduct = async () => {
      setIsLoading(true);
      setError(null);
      
      const data = await fetchListingBySlug(slug);
      
      if (data) {
        // Use detailed review eligibility information if available
        const eligibility = data.review_eligibility || {};
        
        if (!data.can_review) {
          // Store the status for conditional rendering
          setReviewStatus(eligibility.status || 'unknown');
          
          // Use specific reason from backend, or fall back to generic message
          const errorMessage = eligibility.reason || 
            "You cannot review this product. You can only review products you have purchased and received.";
          setError(errorMessage);
        } else {
          setProduct(data);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (rating === 0) {
      setSubmitError("Please select a rating");
      return;
    }
    
    if (!content.trim()) {
      setSubmitError("Please write a review");
      return;
    }
    
    setIsSubmitting(true);
    setSubmitError(null);
    
    try {
      await axiosInstance.post(
        `/marketplace/listings/${slug}/reviews/`,
        {
          listing: product.id,
          rating,
          title: title.trim() || undefined,
          content: content.trim(),
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      setSubmitSuccess(true);
      
      // Redirect after a delay
      setTimeout(() => {
        navigate(`/el-mercado/products/${slug}`, { 
          state: { openTab: 'reviews', reviewAdded: true } 
        });
      }, 2000);
      
    } catch (err) {
      console.error('Failed to submit review:', err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.detail ||
                          err.response?.data?.non_field_errors?.[0] ||
                          'Failed to submit review. Please try again.';
      setSubmitError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const ratingLabels = [
    "",
    "Poor",
    "Fair",
    "Good",
    "Very Good",
    "Excellent"
  ];

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20 flex items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        </div>
        <Footer />
      </>
    );
  }

  if (error || !product) {
    return (
      <>
        <Helmet>
          <title>Cannot Write Review | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <div className="pt-20 pb-16 px-4">
            <div className="max-w-lg mx-auto text-center py-20">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-10 h-10 text-red-500" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Cannot Write Review</h1>
              <p className="text-gray-500 mb-6">
                {error || "Something went wrong"}
              </p>
              
              {/* Conditional action buttons based on status */}
              {reviewStatus === 'already_reviewed' ? (
                <div className="space-y-3">
                  <Link
                    to={`/el-mercado/products/${slug}#reviews`}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                  >
                    View Your Review
                  </Link>
                  <div className="text-sm text-gray-500">
                    You can edit or delete your review from the product page
                  </div>
                </div>
              ) : reviewStatus === 'not_delivered' ? (
                <div className="space-y-3">
                  <Link
                    to="/account/orders"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                  >
                    View Your Orders
                  </Link>
                  <Link
                    to="/el-mercado/browse"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors ml-3"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Continue Shopping
                  </Link>
                </div>
              ) : (
                <Link
                  to="/el-mercado/browse"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                  {reviewStatus === 'not_purchased' ? 'Browse Products' : 'Back to Browse'}
                </Link>
              )}
            </div>
          </div>
          <Footer />
        </div>
      </>
    );
  }

  if (submitSuccess) {
    return (
      <>
        <Helmet>
          <title>Review Submitted | El Mercado - BIO-CHEM KNUST</title>
        </Helmet>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <div className="pt-20 pb-16 px-4">
            <div className="max-w-lg mx-auto text-center py-20">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4"
              >
                <CheckCircle className="w-10 h-10 text-green-500" />
              </motion.div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Review Submitted!</h1>
              <p className="text-gray-500 mb-6">
                Thank you for your feedback. Your review helps others make better decisions.
              </p>
              <p className="text-sm text-gray-400">Redirecting to product page...</p>
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
        <title>Write Review for {product.title} | El Mercado - BIO-CHEM KNUST</title>
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          <div className="max-w-2xl mx-auto px-4 py-8">
            {/* Back Button */}
            <Link
              to={`/el-mercado/products/${slug}`}
              className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Product
            </Link>

            {/* Product Summary */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-8">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  {product.main_image_url ? (
                    <img
                      src={product.main_image_url}
                      alt={product.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Package className="w-8 h-8 text-gray-400" />
                    </div>
                  )}
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">{product.title}</h2>
                  <p className="text-sm text-gray-500">by {product.seller?.business_name}</p>
                </div>
              </div>
            </div>

            {/* Review Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
            >
              <h1 className="text-2xl font-bold text-gray-900 mb-6">Write Your Review</h1>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Rating */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Rating *
                  </label>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRating(star)}
                          onMouseEnter={() => setHoverRating(star)}
                          onMouseLeave={() => setHoverRating(0)}
                          className="p-1 focus:outline-none"
                        >
                          <Star
                            className={`w-8 h-8 transition-colors ${
                              (hoverRating || rating) >= star
                                ? "text-yellow-400 fill-yellow-400"
                                : "text-gray-300"
                            }`}
                          />
                        </button>
                      ))}
                    </div>
                    {(hoverRating || rating) > 0 && (
                      <span className="text-sm font-medium text-gray-700">
                        {ratingLabels[hoverRating || rating]}
                      </span>
                    )}
                  </div>
                </div>

                {/* Title (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Review Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Summarize your experience"
                    maxLength={100}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Review *
                  </label>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Share your experience with this product. What did you like or dislike?"
                    rows={5}
                    maxLength={2000}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  />
                  <p className="text-xs text-gray-400 mt-1 text-right">
                    {content.length}/2000
                  </p>
                </div>

                {/* Error Message */}
                {submitError && (
                  <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span>{submitError}</span>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    "Submit Review"
                  )}
                </button>
              </form>
            </motion.div>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default WriteReviewPage;
