import { useCallback, useContext, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  fadeIn,
  scaleCenter,
  underlineAnimation,
} from "../utils/framerVariants";
import { BlogCard } from "../Components/Blog/BlogCard";
import { Footer } from "../Components/Footer/Footer";
import Login from "./Login";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useBlogs } from "../Context/BlogsContext";
import { BlogCardSkeleton } from "../Components/Blog/BlogCardSkeleton";
import { getData } from "../utils/apiHandler";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { BACKEND_HOST } from "../utils/config";
import { useSavedBlogs } from "../Context/SavedBlogsContext";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import ExecutiveLogin from "./ExecutiveLogin";
import { Helmet } from "react-helmet-async";

export function BlogsPage() {
  const { blogs, setBlogs } = useBlogs();
  const { savedBlogs, setSavedBlogs } = useSavedBlogs();

  const { user } = useContext(UserContext);

  const axiosInstance = useAxiosWithRefresh();

  const fetchBlogs = async () => {
    const { response, error, loading } = await getData("/news/");
    if (error) {
      console.error("Error fetching blogs:", error);
    }
    if (response) {
      setBlogs(
        response?.sort(
          (a, b) => new Date(b?.created_at) - new Date(a?.created_at)
        )
      );
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

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
    setIsExecutiveOpen(false);
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const paramValue = searchParams.get("page");

  const [pageNumber, setPageNumber] = useState(1);

  useEffect(() => {
    if (paramValue && paramValue !== "") {
      setPageNumber(parseInt(paramValue));
    }
    scrollToTop();
  }, [paramValue]);

  const goToNextPage = () => {
    navigate(`/blogs?page=${pageNumber + 1}`);
  };

  const goToPrevPage = () => {
    navigate(`/blogs?page=${pageNumber - 1}`);
  };

  const checkSaved = (id) => {
    const save = savedBlogs?.find((item) => item?.news_id == id);
    return save ? true : false;
  };

  const renderBlogs = () => {
    const startIndex = (pageNumber - 1) * 6;
    const endIndex = Math.min(pageNumber * 6, blogs?.length);
    return blogs
      ? blogs?.slice(startIndex, endIndex).map((post) => (
          <li key={post?.news_id} className="flex">
            <BlogCard
              blog={post}
              saved={checkSaved(post?.news_id)}
              isRecent={post?.is_recent}
              daysAgo={post?.days_ago}
            />
          </li>
        ))
      : Array(6)
          .fill(0)
          .map((_, index) => <BlogCardSkeleton key={index} />);
  };

  return (
    <>
      <Helmet>
        <title>Blogs | CSS KNUST</title>
        <meta
          name="description"
          content="Explore tech articles, stories, and updates from the Computer Science Society of KNUST. Learn, grow, and stay informed."
        />
        <meta
          name="keywords"
          content="CSS KNUST Blogs, KNUST Tech Blogs, Computer Science Articles, CSS KNUST Updates, thecssknust blogs"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="CSS KNUST - Blogs" />
        <meta
          property="og:description"
          content="Tech insights and student stories from the CSS KNUST community."
        />
        <meta
          property="og:image"
          content="https://thecssknust.com/images/css.png"
        />
        <meta property="og:url" content="https://thecssknust.com/blogs" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "CSS KNUST Blogs",
            description:
              "A collection of tech stories, tutorials, and community highlights by CSS KNUST students.",
            url: "https://thecssknust.com/blogs",
          })}
        </script>
      </Helmet>

      <div className="relative mt-[70px]">
        <Navbar onSignInClick={handleOpenLoginModal} />
        <div className="py-16 px-4 md:px-16 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
            >
              Discover Our{" "}
              <span className="relative text-blue-600">
                Blogs
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
            <p className="text-center text-gray-600 mb-12">
              Discover the latest in computer science, technology trends, and
              innovations. Dive into insights, tutorials, and stories that
              inspire growth, spark creativity, and fuel your passion for
              problem-solving. Join us as we share knowledge and build a future
              driven by curiosity and collaboration.
            </p>

            <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {renderBlogs()}
            </ul>

            <div className="mt-16 flex justify-between items-center gap-5">
              <motion.div
                variants={fadeIn("left", 0.5, 0)}
                initial="offscreen"
                whileInView="onscreen"
                viewport={{ once: true, amount: 0 }}
              >
                <button
                  disabled={pageNumber <= 1}
                  className={`py-2 px-6 rounded text-white font-medium transition ${
                    pageNumber <= 1
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-blue-700 hover:bg-blue-800"
                  }`}
                  onClick={goToPrevPage}
                >
                  Previous
                </button>
              </motion.div>

              <motion.p
                variants={scaleCenter(0.5, 0)}
                initial="offscreen"
                whileInView="onscreen"
                viewport={{ once: true, amount: 0 }}
                className="text-lg font-semibold text-gray-700"
              >
                Page {pageNumber} of {Math.ceil(blogs?.length / 6)}
              </motion.p>

              <motion.div
                variants={fadeIn("right", 0.5, 0)}
                initial="offscreen"
                whileInView="onscreen"
                viewport={{ once: true, amount: 0 }}
              >
                <button
                  disabled={pageNumber >= Math.ceil(blogs?.length / 6)}
                  className={`py-2 px-6 rounded text-white font-medium transition ${
                    pageNumber >= Math.ceil(blogs?.length / 6)
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-blue-700 hover:bg-blue-800"
                  }`}
                  onClick={goToNextPage}
                >
                  Next
                </button>
              </motion.div>
            </div>
          </div>
        </div>
        <Footer />

        {isLoginModalOpen && (
          <Login
            onClose={handleCloseModals}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
            action={() => navigate("/dashboard/home")}
            switchToExecutive={handleExecutiveOpen}
          />
        )}

        {isSignupModalOpen && (
          <SignUp
            onClose={handleCloseModals}
            switchToLogin={handleOpenLoginModal}
          />
        )}
        {isOpen && (
          <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
        )}
        {isExecutiveOpen && (
          <ExecutiveLogin
            onClose={handleOpenLoginModal}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
          />
        )}
      </div>
    </>
  );
}
