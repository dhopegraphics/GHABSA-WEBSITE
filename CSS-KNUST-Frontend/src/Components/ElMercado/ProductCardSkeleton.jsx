

/**
 * ProductCardSkeleton Component
 * Reusable loading skeleton for product cards in El Mercado
 * Supports both grid and list view modes
 */
export function ProductCardSkeleton({ viewMode = "grid" }) {
  if (viewMode === "list") {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse">
        <div className="flex">
          {/* Image Skeleton */}
          <div className="w-48 h-48 flex-shrink-0 bg-gray-200" />
          
          {/* Content Skeleton */}
          <div className="flex-1 p-4 flex flex-col justify-between">
            <div>
              {/* Type & Condition badges */}
              <div className="flex items-center gap-2 mb-2">
                <div className="h-5 w-20 bg-gray-200 rounded-full" />
                <div className="h-4 w-16 bg-gray-200 rounded" />
              </div>
              
              {/* Title */}
              <div className="h-5 bg-gray-200 rounded mb-2 w-3/4" />
              <div className="h-5 bg-gray-200 rounded mb-2 w-1/2" />
              
              {/* Category */}
              <div className="h-4 bg-gray-200 rounded mb-2 w-1/3" />
              
              {/* Rating */}
              <div className="flex items-center gap-2 mb-2">
                <div className="flex gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="w-4 h-4 bg-gray-200 rounded" />
                  ))}
                </div>
                <div className="h-4 w-12 bg-gray-200 rounded" />
              </div>
              
              {/* Seller */}
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-200 rounded" />
                <div className="h-4 w-32 bg-gray-200 rounded" />
              </div>
            </div>
            
            {/* Price & Actions */}
            <div className="flex items-center justify-between mt-4">
              <div className="flex items-center gap-2">
                <div className="h-7 w-24 bg-gray-200 rounded" />
                <div className="h-4 w-20 bg-gray-200 rounded" />
              </div>
              <div className="flex items-center gap-3">
                <div className="h-4 w-16 bg-gray-200 rounded" />
                <div className="h-9 w-20 bg-gray-200 rounded-lg" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Grid view (default)
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse">
      {/* Image Container */}
      <div className="relative aspect-square bg-gray-200">
        {/* Badges placeholder */}
        <div className="absolute top-3 left-3 space-y-2">
          <div className="h-6 w-20 bg-gray-300 rounded-full" />
        </div>
        
        {/* Favorite button placeholder */}
        <div className="absolute top-3 right-3 w-10 h-10 bg-gray-300 rounded-full" />
      </div>
      
      {/* Content */}
      <div className="p-4">
        {/* Type & Category badges */}
        <div className="flex items-center gap-2 mb-2">
          <div className="h-5 w-16 bg-gray-200 rounded-full" />
          <div className="h-4 w-24 bg-gray-200 rounded" />
        </div>
        
        {/* Title */}
        <div className="h-5 bg-gray-200 rounded mb-2 w-full" />
        <div className="h-5 bg-gray-200 rounded mb-3 w-2/3" />
        
        {/* Rating */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="w-3.5 h-3.5 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="h-4 w-10 bg-gray-200 rounded" />
        </div>
        
        {/* Seller */}
        <div className="flex items-center gap-1.5 mb-3">
          <div className="w-3.5 h-3.5 bg-gray-200 rounded" />
          <div className="h-4 w-28 bg-gray-200 rounded flex-1" />
        </div>
        
        {/* Price */}
        <div className="flex items-baseline gap-2">
          <div className="h-6 w-20 bg-gray-200 rounded" />
          <div className="h-4 w-16 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}

/**
 * ProductGridSkeleton Component
 * Renders multiple ProductCardSkeletons in a grid or list layout
 */
export function ProductGridSkeleton({ viewMode = "grid", count = 8 }) {
  return (
    <div
      className={
        viewMode === "list"
          ? "space-y-4"
          : "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      }
    >
      {[...Array(count)].map((_, i) => (
        <ProductCardSkeleton key={i} viewMode={viewMode} />
      ))}
    </div>
  );
}

export default ProductCardSkeleton;
