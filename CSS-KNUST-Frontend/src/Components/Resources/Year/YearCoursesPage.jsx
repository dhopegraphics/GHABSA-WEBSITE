import { useState, useMemo, useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import { SearchBar } from "./SearchBar";
import { scrollToTop } from "../../../utils/scrollToTop";
import { CourseCard } from "./CourseCard";
import { Footer } from "../../Footer/Footer";
import Login from "../../../Pages/Login";
import Navbar from "../../Navbar";
import SignUp from "../../../Pages/SignUp";
import ForgotPasswordModal from "../../../Pages/ForgotPasswordModal";
import ExecutiveLogin from "../../../Pages/ExecutiveLogin";
import { getData } from "../../../utils/apiHandler";
import { courseMatchesSemester, normalizeCourses, SEMESTERS } from "../../../utils/courseSchema";

export function YearCoursesPage() {
  const navigate = useNavigate();

  const location = useLocation();
  const { courses: stateCourses } = location.state || {};
  const [courses, setCourses] = useState(() => normalizeCourses(stateCourses));
  const [isLoading, setIsLoading] = useState(!stateCourses);

  const [searchParams] = useSearchParams();
  const paramValue = searchParams.get("year");

  useEffect(() => {
    if (paramValue && paramValue !== "") {
      setYear(parseInt(paramValue));
    }
    scrollToTop();
  }, [paramValue]);

  useEffect(() => {
    if (stateCourses) {
      setCourses(normalizeCourses(stateCourses));
      setIsLoading(false);
      return;
    }

    const fetchCourses = async () => {
      setIsLoading(true);
      const { response, error } = await getData(
        `/academics/courses/${paramValue ? `?year=${paramValue}` : ""}`
      );
      if (error) console.error("Error fetching courses:", error);
      setCourses(normalizeCourses(response));
      setIsLoading(false);
    };

    fetchCourses();
  }, [paramValue, stateCourses]);

  const [searchTerm, setSearchTerm] = useState("");
  const [year, setYear] = useState("");
  const [selectedSemester, setSelectedSemester] = useState("all");

  const filteredCourses = useMemo(() => {
    return courses?.filter((course) => {
      const matchesSearch =
        course.course_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        course.course_code.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesSearch && courseMatchesSemester(course, selectedSemester);
    });
  }, [courses, searchTerm, selectedSemester]);

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
    <div className="relative bg-[#f5f7fa] pt-[60px] sm:pt-[65px] md:pt-[70px] lg:pt-[75px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <div className="min-h-screen px-5 py-16 sm:px-8 lg:px-10">
        <div className="max-w-7xl mx-auto">
          <a
            href="/#resources"
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors mb-8"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Resources</span>
          </a>

          <div className="mb-12 max-w-3xl">
            <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">
              Year {year} resources
            </h1>
            <p className="mt-4 text-lg text-slate-600">
              {courses?.length} {courses?.length === 1 ? "Course" : "Courses"}{" "}
              available across two semesters.
            </p>
          </div>

          <div className="mb-6 max-w-xl">
            <SearchBar searchTerm={searchTerm} onSearchChange={setSearchTerm} />
          </div>

          {/* Semester Filter Tabs */}
          <div className="mb-10 flex overflow-x-auto">
            <div className="inline-flex rounded-full border border-slate-200 bg-white p-1.5 shadow-sm">
              {SEMESTERS.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setSelectedSemester(filter.value)}
                  className={`whitespace-nowrap rounded-full px-5 py-2.5 text-sm font-semibold transition-all ${
                    selectedSemester === filter.value
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Active Filters Display */}
          {selectedSemester !== "all" && (
            <div className="flex justify-center mb-6 gap-3">
              {selectedSemester !== "all" && (
                <div className="inline-flex items-center gap-2 bg-purple-50 text-purple-700 px-4 py-2 rounded-full text-sm font-medium border border-purple-200">
                  <span>
                    {selectedSemester === "1"
                      ? "1st Semester"
                      : selectedSemester === "2"
                      ? "2nd Semester"
                      : "Both Semesters"}
                  </span>
                  <button
                    onClick={() => setSelectedSemester("all")}
                    className="hover:bg-purple-100 rounded-full p-0.5 transition-colors"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Results Counter */}
          <div className="text-center mb-6">
            <p className="text-gray-600 font-medium">
              Showing {filteredCourses?.length || 0} of {courses?.length || 0}{" "}
              courses
            </p>
          </div>

          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {isLoading ? (
              Array.from({ length: 6 }).map((_, index) => <div key={index} className="h-72 animate-pulse rounded-[28px] bg-slate-200" />)
            ) : filteredCourses?.length > 0 ? (
              filteredCourses.map((course) => (
                <CourseCard key={course.course_id} course={course} />
              ))
            ) : (
              <div className="col-span-full text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                  <GraduationCap className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-600 text-lg font-medium mb-2">
                  No courses found
                </p>
                <p className="text-gray-500 text-sm">
                  Try adjusting your filters or search term
                </p>
              </div>
            )}
          </div>

          {!filteredCourses && (
            <div className="text-center py-12">
              <p className="text-gray-600">
                No courses found matching your search.
              </p>
            </div>
          )}
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
