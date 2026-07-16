import { Loader } from "lucide-react";

export const VotingSkeleton = () => {
  return (
    <div className="animate-pulse">
      <div className="bg-gray-200 rounded-xl h-48 mb-4"></div>
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
};

export const LoadingSpinner = ({ message = "Loading..." }) => {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Loader className="animate-spin text-indigo-600 mb-4" size={48} />
      <p className="text-gray-600">{message}</p>
    </div>
  );
};
