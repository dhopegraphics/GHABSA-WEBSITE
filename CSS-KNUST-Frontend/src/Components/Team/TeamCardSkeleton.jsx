import React from "react";

export function TeamCardSkeleton() {
  return (
    <div className="relative group">
      <div className="relative overflow-hidden">
        
        <div className="w-full h-96 lg:h-80 bg-gray-300 animate-pulse"></div>

        <div className="absolute w-full scale-x-0 h-full bg-gray-400 top-0 left-0 group-hover:scale-x-100 transition-all duration-500 origin-left"></div>

        <div className="absolute bottom-0 left-[8%] opacity-50 group-hover:opacity-100 transition-all duration-500 group-hover:-translate-y-10">
          <div className="h-4 w-20 bg-gray-300 rounded animate-pulse mb-2"></div>
          <div className="h-6 w-36 bg-gray-300 rounded animate-pulse"></div>
        </div>

        <div className="absolute right-[6%] top-0 translate-y-[-125px] group-hover:delay-200 grid gap-2 transition-all duration-700 group-hover:translate-y-4">
          <div className="w-6 h-6 bg-gray-300 rounded-full animate-pulse"></div>
          <div className="w-6 h-6 bg-gray-300 rounded-full animate-pulse"></div>
          <div className="w-6 h-6 bg-gray-300 rounded-full animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
