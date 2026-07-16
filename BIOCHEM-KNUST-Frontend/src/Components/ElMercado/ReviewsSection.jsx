import { Star, CheckCircle, User, AlertCircle, RefreshCw, PenSquare } from "lucide-react";
import { motion } from "framer-motion";


export function ReviewsSection({ product, reviews, loading, error, onRetry, canReview, onWriteReview }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Reviews</h3>
        <p className="text-gray-500 mb-4">{error}</p>
        {onRetry && (
          <button 
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        )}
      </div>
    );
  }

  if (!reviews || reviews.length === 0) {
    return (
      <div className="text-center py-12">
        <Star className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Reviews Yet</h3>
        <p className="text-gray-500 mb-4">Be the first to review this product!</p>
        {canReview && (
          <button
            onClick={onWriteReview}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
          >
            <PenSquare className="w-5 h-5" />
            Write a Review
          </button>
        )}
      </div>
    );
  }

  // Calculate rating breakdown
  const ratingCounts = [5, 4, 3, 2, 1].map(rating => 
    reviews.filter(r => r.rating === rating).length
  );
  const totalReviews = reviews.length;
  
  return (
    <div className="space-y-8">
      {/* Write Review Button - Only for eligible buyers */}
      {canReview && (
        <div className="flex justify-end">
          <button
            onClick={onWriteReview}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
          >
            <PenSquare className="w-5 h-5" />
            Write a Review
          </button>
        </div>
      )}

      {/* Rating Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Average Rating */}
        <div className="text-center p-6 bg-gray-50 rounded-xl">
          <div className="text-5xl font-bold text-gray-900 mb-2">
            {parseFloat(product.average_rating || 0).toFixed(1)}
          </div>
          <div className="flex items-center justify-center gap-1 mb-2">
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
          <p className="text-sm text-gray-600">{totalReviews} review{totalReviews !== 1 ? 's' : ''}</p>
        </div>

        {/* Rating Breakdown */}
        <div className="md:col-span-2 space-y-2">
          {[5, 4, 3, 2, 1].map((rating, index) => {
            const count = ratingCounts[index];
            const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
            
            return (
              <div key={rating} className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700 w-12">
                  {rating} <Star className="w-3 h-3 inline text-yellow-400 fill-yellow-400" />
                </span>
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-yellow-400 transition-all"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Reviews List */}
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-gray-900">Customer Reviews</h3>
        
        {reviews.map((review, index) => (
          <motion.div
            key={review.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="border-b border-gray-100 pb-6 last:border-0"
          >
            {/* Reviewer Info */}
            <div className="flex items-start gap-4 mb-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                {review.reviewer_name ? review.reviewer_name.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-gray-900">
                    {review.reviewer_name || 'Anonymous'}
                  </span>
                  {review.is_verified_purchase && (
                    <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                      <CheckCircle className="w-3 h-3" />
                      Verified Purchase
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-0.5">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-4 h-4 ${
                          i < review.rating
                            ? "text-yellow-400 fill-yellow-400"
                            : "text-gray-300"
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(review.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
              </div>
            </div>

            {/* Review Content */}
            {review.title && (
              <h4 className="font-semibold text-gray-900 mb-2">{review.title}</h4>
            )}
            <p className="text-gray-700 mb-3">{review.content}</p>

            {/* Seller Response */}
            {review.seller_response && (
              <div className="mt-4 pl-4 border-l-2 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-semibold text-blue-900">Seller Response</span>
                  {review.seller_responded_at && (
                    <span className="text-xs text-blue-600">
                      {new Date(review.seller_responded_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <p className="text-sm text-blue-900">{review.seller_response}</p>
              </div>
            )}

            {/* Helpful Count */}
            {review.helpful_count > 0 && (
              <div className="mt-3 text-sm text-gray-500">
                {review.helpful_count} {review.helpful_count === 1 ? 'person' : 'people'} found this helpful
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export default ReviewsSection;
