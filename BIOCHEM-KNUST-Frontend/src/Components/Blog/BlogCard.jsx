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
    <article className="group relative h-full overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.05)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_20px_50px_rgba(15,23,42,0.09)]">
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

      <div className="relative h-56 overflow-hidden">
        <img
          src={blog?.head_image_url}
          alt={blog?.title}
          className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/35 to-transparent" />
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
        <h3 className="mb-3 line-clamp-2 text-xl font-semibold leading-snug tracking-tight text-slate-950">
          {blog?.title}
        </h3>
        <p className="mb-5 line-clamp-3 text-sm leading-6 text-slate-600">{blog?.report}</p>
        <Link
          to={`/blog/${blog?.news_id}`}
          state={{ blog, saved }}
          className="inline-flex items-center font-semibold text-blue-700 hover:text-blue-800"
        >
          Read story&nbsp; →
        </Link>
      </div>
    </article>
  );
}
