import { useCallback, useContext, useEffect, useState } from "react";
import { ArrowLeft, Bookmark } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { BlogHeader } from "../Components/Blog/BlogDetail/BlogHeader";
import { Footer } from "../Components/Footer/Footer";
import Login from "./Login";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { FaBookmark } from "react-icons/fa";
import { debounce } from "lodash";
import { BACKEND_HOST } from "../utils/config";
import { useSavedBlogs } from "../Context/SavedBlogsContext";
import ExecutiveLogin from "./ExecutiveLogin";

export function BlogDetailPage() {
  const location = useLocation();
  const { blog, saved } = location.state || {};
  const { user } = useContext(UserContext);

  const axiosInstance = useAxiosWithRefresh();
  const navigate = useNavigate();

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const [newSaved, setNewSaved] = useState(saved);

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

  useEffect(() => {
    scrollToTop();
  }, []);

  const { savedBlogs, setSavedBlogs } = useSavedBlogs();

  const fetchSaved = useCallback(async () => {
    if (user?.access) {
      try {
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-blogs/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        const save = response.data?.data?.blogs.find(
          (a) => a?.news_id == blog?.news_id
        );

        save ? setNewSaved(true) : setNewSaved(false);
        setSavedBlogs(response.data?.data?.blogs || []);
      } catch (error) {
        console.error("Failed to fetch saved blogs:", error);
      }
    }
  }, [user, axiosInstance]);

  const saveBlog = useCallback(
    debounce(async (id) => {
      try {
        // console.log('saving')
        const response = await axiosInstance.post(
          `${BACKEND_HOST}/accounts/save-blog/`,
          { blogs: [id] },
          { headers: { Authorization: `Bearer ${user.access}` } }
        );

        fetchSaved();
      } catch (error) {
        console.error("Error saving blog:", error);
      }
    }, 300),
    [user, axiosInstance]
  );

  const unSaveBlog = useCallback(
    debounce(async (id) => {
      try {
        // console.log('unsaving')
        const response = await axiosInstance.delete(
          `${BACKEND_HOST}/accounts/removed-saved-blog/${id}`,
          { headers: { Authorization: `Bearer ${user.access}` } }
        );
        fetchSaved();
      } catch (error) {
        console.error("Error unsaving blog:", error);
      }
    }, 300),
    [user, axiosInstance]
  );

  const handleSaveClick = (id) => {
    if (user) {
      if (newSaved) {
        unSaveBlog(id);
      } else {
        saveBlog(id);
      }
    } else {
      handleOpenLoginModal();
    }
  };

  return (
    <div className="relative mt-[50px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <div className="min-h-screen bg-white py-12 px-4">
        <div className="max-w-7xl mx-auto mb-8">
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Blogs</span>
          </button>
        </div>

        <div className="relative md:h-[60vh] max-w-7xl mx-auto md:mb-12 rounded-2xl overflow-hidden">
          <img
            src={blog?.head_image_url}
            alt={blog?.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/00 to-transparent" />
        </div>

        <div className="max-w-4xl py-6 md:p-0 mx-auto md:mb-12 flex justify-end gap-4">
          {/* <button className="p-2 rounded-full hover:bg-gray-100 transition-colors"> */}
          {/* <Share2 className="w-6 h-6 text-gray-600" /> */}
          {/* </button> */}

          <button
            onClick={() => handleSaveClick(blog?.news_id)}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            {newSaved ? (
              <FaBookmark className="w-6 h-5 text-gray-600" />
            ) : (
              <Bookmark className="w-6 h-6 text-gray-600" />
            )}
          </button>
        </div>

        <div className="max-w-4xl mx-auto px-4">
          <BlogHeader
            title={blog?.title}
            author={blog?.reported_by}
            date={blog?.created_at}
            // readTime={CalculateReadTime(blog?.report)}
            readTime={blog?.minutes_read}
          />
          <article className="prose prose-lg max-w-4xl mx-auto">
            <div className="whitespace-pre-wrap">{blog?.report}</div>
          </article>
        </div>

        {blog?.back_image_url && (
          <div className="max-w-5xl mx-auto mt-12 rounded-xl overflow-hidden">
            <img
              src={blog?.back_image_url}
              alt="Article background"
              className="w-full h-auto"
            />
          </div>
        )}
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
  );
}
