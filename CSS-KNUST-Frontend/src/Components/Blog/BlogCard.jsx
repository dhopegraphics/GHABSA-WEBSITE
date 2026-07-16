import { Calendar, User, Sparkles, Clock } from "lucide-react";
import { Link } from "react-router-dom";

export function BlogCard({ blog, saved, isRecent, daysAgo }) {
  const getTimeLabel = (days) => {
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days <= 7) return `${days} days ago`;
    if (days <= 30) return `${Math.floor(days / 7)} weeks ago`;
    if (days <= 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  return (
    <div className="bg-white overflow-hidden transition-transform group shadow-lg rounded-lg relative">
      {/* NEW Badge for recent blogs */}
      {isRecent && (
        <div className="absolute top-4 right-4 z-10 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-lg animate-pulse">
          <Sparkles className="w-3 h-3" />
          NEW
        </div>
      )}

      {/* Age indicator for older blogs */}
      {!isRecent && daysAgo > 7 && (
        <div className="absolute top-4 right-4 z-10 bg-gray-500/80 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 shadow-md">
          <Clock className="w-3 h-3" />
          {getTimeLabel(daysAgo)}
        </div>
      )}

      <div className="h-48 overflow-hidden relative">
        <img
          src={blog?.head_image_url}
          alt={blog?.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute w-full scale-x-0 h-full bg-[#18192e77] top-0 left-0 group-hover:scale-x-100 transition-all duration-500 origin-left"></div>
      </div>

      <div className="p-6">
        <div className="flex items-center text-sm text-gray-600 mb-3">
          <div className="flex items-center gap-1 w-full">
            <Calendar className="w-4 h-4 text-blue-600" />
            <span className="text-[12px]">
              {new Date(blog?.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          </div>
          <div className="flex items-center gap-1 w-full">
            <User className="w-4 h-4 text-blue-600" />
            <span className="text-[12px]">by {blog?.reported_by}</span>
          </div>
        </div>
        <h3 className="text-xl font-semibold mb-2 text-gray-900 line-clamp-2">
          {blog?.title}
        </h3>
        <p className="text-gray-600 mb-4 line-clamp-3">{blog?.report}</p>
        <Link
          to={`/blog/${blog?.news_id}`}
          state={{ blog, saved }}
          className="text-blue-600 font-medium hover:text-blue-700"
        >
          Read More →
        </Link>
      </div>
    </div>
  );
}
