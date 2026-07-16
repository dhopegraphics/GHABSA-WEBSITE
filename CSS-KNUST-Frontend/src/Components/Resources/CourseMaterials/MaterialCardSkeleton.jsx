import React from 'react'

function MaterialCardSkeleton() {
  return (
    <div
        className="p-4 bg-white rounded-lg shadow animate-pulse flex items-center gap-4"
      >
        <div className="h-12 w-12 bg-gray-200 rounded"></div>
        <div className="flex-1 space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
  )
}

export default MaterialCardSkeleton