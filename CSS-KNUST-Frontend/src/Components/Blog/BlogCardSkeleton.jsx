import React from 'react';
import { Calendar, User } from 'lucide-react';

export function BlogCardSkeleton() {
  return (
    <div className="bg-white overflow-hidden animate-pulse">
      
      <div className="h-48 bg-gray-200 relative">
        <div className="absolute w-full h-full bg-gray-300"></div>
      </div>

      <div className="p-6">
        
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4 text-gray-400" />
            <div className="w-20 h-4 bg-gray-300 rounded"></div>
          </div>
          <div className="flex items-center gap-1">
            <User className="w-4 h-4 text-gray-400" />
            <div className="w-24 h-4 bg-gray-300 rounded"></div>
          </div>
        </div>

        <div className="w-3/4 h-6 bg-gray-300 rounded mb-2"></div>

        <div className="space-y-2 mb-4">
          <div className="w-full h-4 bg-gray-300 rounded"></div>
          <div className="w-5/6 h-4 bg-gray-300 rounded"></div>
        </div>

        <div className="w-24 h-4 bg-gray-300 rounded"></div>
      </div>
    </div>
  );
}
