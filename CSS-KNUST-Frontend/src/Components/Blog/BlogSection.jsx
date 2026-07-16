import { useCallback, useContext, useEffect, useState } from "react";
import { BlogCard } from "./BlogCard";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../../utils/framerVariants";
import { FiArrowUpRight } from "react-icons/fi";
import { Link } from "react-router-dom";
import { getData } from "../../utils/apiHandler";
import { useBlogs } from "../../Context/BlogsContext";
import { BlogCardSkeleton } from "./BlogCardSkeleton";
import { UserContext } from "../../Context/UserContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../../utils/config";
import { useSavedBlogs } from "../../Context/SavedBlogsContext";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function BlogSection() {
  const { blogs, setBlogs } = useBlogs();
  const { savedBlogs, setSavedBlogs } = useSavedBlogs();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const { user } = useContext(UserContext);

  const axiosInstance = useAxiosWithRefresh();

  const fetchBlogs = async () => {
    const { response, error } = await getData("/news/");
    if (error) {
      console.error("Error fetching blogs:", error);
    }
    if (response) {
      // Backend now orders by -created_at, so most recent first
      setBlogs(response);
    }
  };

  const fetchSaved = useCallback(async () => {
    if (user?.access) {
      try {
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-blogs/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        setSavedBlogs(response.data?.data?.blogs || []);
      } catch (error) {
        console.error("Failed to fetch saved blogs:", error);
      }
    }
  }, [user, axiosInstance]);

  useEffect(() => {
    fetchBlogs();
    fetchSaved();
  }, []);

  const checkSaved = (id) => {
    const save = savedBlogs?.find((item) => item?.news_id == id);
    return save ? true : false;
  };

  // Get top 3 blogs for carousel
  const displayBlogs = blogs ? blogs.slice(0, 3) : null;

  const handleNext = useCallback(() => {
    if (displayBlogs && displayBlogs.length > 0) {
      setCurrentIndex((prev) => (prev + 1) % displayBlogs.length);
    }
  }, [displayBlogs]);

  const handlePrev = () => {
    if (displayBlogs && displayBlogs.length > 0) {
      setCurrentIndex(
        (prev) => (prev - 1 + displayBlogs.length) % displayBlogs.length
      );
    }
  };

  const handleDotClick = (index) => {
    setCurrentIndex(index);
    setIsAutoPlaying(false); // Stop auto-play when user manually navigates
  };

  // Auto-rotate carousel every 5 seconds
  useEffect(() => {
    if (isAutoPlaying && displayBlogs && displayBlogs.length > 1) {
      const timer = setInterval(() => {
        handleNext();
      }, 5000);
      return () => clearInterval(timer);
    }
  }, [currentIndex, isAutoPlaying, displayBlogs, handleNext]);

  return (
    <section className="bg-[#f4f7fb] px-5 py-20 sm:px-8 sm:py-28 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="max-w-3xl text-4xl font-semibold leading-tight tracking-[-0.04em] text-slate-950 sm:text-5xl"
        >
          Stories from our{" "}
          <span className="relative text-blue-600">
            community.
            <motion.div
              variants={underlineAnimation(0.7)}
              initial="offscreen"
              whileInView="onscreen"
              exit="reverse"
              className="absolute left-0 bottom-0 h-1 bg-blue-600"
              style={{ width: "0%", height: "3px" }}
            />
          </span>
        </motion.h1>
        <p className="mb-12 mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
          Explore science, student life and new perspectives through stories
          created for the Biochemistry community.
        </p>

        {/* Carousel Container */}
        <div className="relative">
          {displayBlogs ? (
            <>
              <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
                {displayBlogs.map((blog) => {
                  return (
                    <motion.div
                      key={blog?.news_id}
                      initial={false}
                      animate={{
                        scale: 1,
                        opacity: 1,
                        zIndex: 1,
                        x: 0,
                      }}
                      transition={{
                        duration: 0.5,
                        ease: "easeInOut",
                      }}
                      className="h-full"
                    >
                      <BlogCard
                        blog={blog}
                        saved={checkSaved(blog?.news_id)}
                        isRecent={blog?.is_recent}
                        daysAgo={blog?.days_ago}
                      />
                    </motion.div>
                  );
                })}
              </div>

              {/* Navigation Controls */}
              <div className="mt-8 hidden items-center justify-center gap-4">
                <button
                  onClick={handlePrev}
                  onMouseEnter={() => setIsAutoPlaying(false)}
                  className="p-2 rounded-full bg-white shadow-md hover:bg-blue-50 transition"
                  aria-label="Previous blog"
                >
                  <ChevronLeft className="w-6 h-6 text-blue-600" />
                </button>

                {/* Dots Indicator */}
                <div className="flex gap-2">
                  {displayBlogs.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => handleDotClick(index)}
                      className={`h-2 rounded-full transition-all duration-300 ${
                        index === currentIndex
                          ? "w-8 bg-blue-600"
                          : "w-2 bg-gray-300 hover:bg-gray-400"
                      }`}
                      aria-label={`Go to blog ${index + 1}`}
                    />
                  ))}
                </div>

                <button
                  onClick={handleNext}
                  onMouseEnter={() => setIsAutoPlaying(false)}
                  className="p-2 rounded-full bg-white shadow-md hover:bg-blue-50 transition"
                  aria-label="Next blog"
                >
                  <ChevronRight className="w-6 h-6 text-blue-600" />
                </button>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {Array(3)
                .fill(0)
                .map((_, index) => (
                  <BlogCardSkeleton key={index} />
                ))}
            </div>
          )}
        </div>

        <div className="mt-12 text-center justify-center md:justify-start">
          <Link
            to={"/blogs?page=1"}
                  className="inline-flex items-center gap-2 rounded-full bg-[#0b2347] px-6 py-3 font-semibold text-white hover:bg-blue-800"
          >
            See More <FiArrowUpRight className="inline" />
          </Link>
        </div>
      </div>
    </section>
  );
}
