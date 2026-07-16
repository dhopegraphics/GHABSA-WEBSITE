import React from "react";

export function InternshipCardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100 animate-pulse">
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-5 h-5 bg-blue-100 rounded"></div>
              <div className="h-5 w-3/4 bg-gray-200 rounded"></div>
            </div>

            <div className="flex flex-col gap-4 mb-4">
              <div className="h-6 w-1/2 bg-gray-200 rounded"></div>
              <div className="h-5 w-1/3 bg-gray-200 rounded"></div>
            </div>

            <div className="space-y-2 mb-6">
              <div className="h-4 w-full bg-gray-200 rounded"></div>
              <div className="h-4 w-4/5 bg-gray-200 rounded"></div>
              <div className="h-4 w-2/3 bg-gray-200 rounded"></div>
            </div>

            <div className="h-5 w-1/4 bg-blue-100 rounded float-end"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
