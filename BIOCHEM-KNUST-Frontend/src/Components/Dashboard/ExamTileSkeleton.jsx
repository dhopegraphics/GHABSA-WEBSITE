import React from "react";

const ExamTileSkeleton = () => {
  return (
    <div className="flex relative justify-between p-5 overflow-hidden rounded-lg shadow-md bg-white border border-gray-200 animate-pulse">
      
      <div className="absolute -bottom-48 -left-48 transition-all duration-500">
        <p className="opacity-10 text-[120px] text-gray-300">XXXX</p>
      </div>

      <div className="flex flex-col gap-3 z-10 w-2/3">
        <div className="flex items-center gap-2">
          <div className="p-3 bg-gray-100 rounded-lg">
            <div className="w-4 h-4 bg-gray-300 rounded"></div>
          </div>
          <div className="h-4 bg-gray-300 rounded w-1/2"></div>
        </div>

        <div className="flex gap-4 items-center">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 rounded"></div>
            <div className="h-4 bg-gray-300 rounded w-24"></div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 rounded"></div>
            <div className="h-4 bg-gray-300 rounded w-20"></div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-300 rounded"></div>
          <div className="h-4 bg-gray-300 rounded w-40"></div>
        </div>
      </div>

      <div className="flex flex-col justify-around gap-6 z-10 w-1/3 items-end">
        <div className="h-4 bg-gray-300 rounded w-12"></div>
        <div className="p-3 bg-gray-100 rounded-md">
          <div className="w-5 h-5 bg-gray-300 rounded"></div>
        </div>
      </div>
    </div>
  );
};

export default ExamTileSkeleton;
