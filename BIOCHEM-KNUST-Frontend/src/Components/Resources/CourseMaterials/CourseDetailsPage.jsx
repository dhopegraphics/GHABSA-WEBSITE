import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { CourseMaterials } from "./CourseMaterials";
import { CourseHeader } from "./CourseHeader";
import { Footer } from "../../Footer/Footer";
import Login from "../../../Pages/Login";
import Navbar from "../../Navbar";
import { scrollToTop } from "../../../utils/scrollToTop";
import { getData } from "../../../utils/apiHandler";
import SignUp from "../../../Pages/SignUp";
import ForgotPasswordModal from "../../../Pages/ForgotPasswordModal";
import ExecutiveLogin from "../../../Pages/ExecutiveLogin";

export function CourseDetailsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id: courseId } = useParams(); // Get course ID from URL
  const { course: stateCourse } = location.state || {}; // Optional course from state

  const [resources, setResources] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMaterials = async () => {
    // Use courseId from URL params instead of relying on state
    if (!courseId) {
      console.error("No course ID available");
      return;
    }

    setIsLoading(true);
    const { response, error } = await getData(
      `/academics/courses/${courseId}/`
    );
    if (error) {
      console.error("Error fetching materials:", error);
    }
    if (response) {
      setResources(response);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    scrollToTop();
    fetchMaterials();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]); // Re-fetch when courseId changes

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

  return (
    <div className="relative mt-[50px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors mb-8"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Course List</span>
          </button>

          <CourseHeader
            materials={resources?.slides?.length || 0}
            past_questions={resources?.past_questions?.length || 0}
            online={resources?.online_tutorial_tips?.length || 0}
            courseCode={resources?.course?.course_code || ""}
            courseName={resources?.course?.course_name || ""}
            course={resources?.course || stateCourse}
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12">
            <CourseMaterials
              title="Course Materials"
              description="Access lecture slides and study materials"
              resources={resources?.slides}
              isLoading={isLoading}
              type="slides"
            />

            <CourseMaterials
              title="Past Questions"
              description="Practice with previous exam questions"
              resources={resources?.past_questions}
              isLoading={isLoading}
              type="past_questions"
            />

            <CourseMaterials
              title="Online Resources"
              description="Additional learning materials and tutorials"
              resources={resources?.online_tutorial_tips}
              isLoading={isLoading}
              type="tutorials"
            />
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
  );
}
