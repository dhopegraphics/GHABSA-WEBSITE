import React from 'react';
import { BiCalendar } from 'react-icons/bi';

export function EventSkeleton() {
  return (
    <div className="relative pl-8 pb-32 group last:pb-0 animate-pulse">
        
      <div className="sticky top-20">
        <div className="text-4xl font-bold mb-8 text-gray-300 bg-gray-200 rounded w-1/2 h-6"></div>
      </div>

      <div className="absolute left-0 top-0 h-full">
        <div className="w-8 h-8 bg-gray-300 text-white -translate-x-[14px] flex items-center justify-center rounded-full sticky top-20 left-0 z-10">
          <BiCalendar className="text-gray-400" />
        </div>
        <div className="absolute top-3 w-1 h-full bg-gray-300"></div>
      </div>

      <div className="overflow-hidden">
        <div className="p-2 md:p-6">
          <div className="bg-gray-200 rounded w-3/4 h-6 mb-2"></div>
          <div className="bg-gray-200 rounded w-full h-4 mb-2"></div>
          <div className="bg-gray-200 rounded w-5/6 h-4"></div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="w-full aspect-[3/2] bg-gray-200 rounded-lg"></div>
          <div className="w-full aspect-[3/2] bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
}
