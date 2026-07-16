

export function MerchandiseCardSkeleton() {
  return (
    <div className="group bg-white rounded-xl overflow-hidden transition-all duration-300 hover:shadow-xl">
      
      <div className="relative h-48 rounded-xl overflow-hidden bg-gray-200 animate-pulse"></div>

      <div className="p-4 flex flex-col gap-3">
        
        <div className="h-6 bg-gray-200 rounded-md animate-pulse"></div>

        
        <div className="flex items-center justify-between">
          <div className="h-6 w-16 bg-gray-200 rounded-md animate-pulse"></div>
          <div className="h-10 w-24 bg-gray-200 rounded-md animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
