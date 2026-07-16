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

export function YearCoursesPage() {
  const navigate = useNavigate();

  const location = useLocation();
  const { courses } = location.state || {};

  const [searchParams] = useSearchParams();
  const paramValue = searchParams.get("year");

  useEffect(() => {
    if (paramValue && paramValue !== "") {
      setYear(parseInt(paramValue));
    }
    scrollToTop();
  }, [paramValue]);

  const [searchTerm, setSearchTerm] = useState("");
  const [year, setYear] = useState("");
  const [selectedSemester, setSelectedSemester] = useState("all");
  const [selectedProgram, setSelectedProgram] = useState("all");

  const filteredCourses = useMemo(() => {
    return courses?.filter((course) => {
      const matchesSearch =
        course.course_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        course.course_code.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesSemester =
        selectedSemester === "all" ||
        course.semester === selectedSemester ||
        course.semester === "both";

      const matchesProgram =
        selectedProgram === "all" || course.program === selectedProgram;

      return matchesSearch && matchesSemester && matchesProgram;
    });
  }, [courses, searchTerm, selectedSemester, selectedProgram]);

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
          <a
            href="/#resources"
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors mb-8"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Resources</span>
          </a>

          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
              <GraduationCap className="w-8 h-8 text-blue-600" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Year {year} Courses
            </h1>
            <p className="text-gray-600">
              {courses?.length} {courses?.length === 1 ? "Course" : "Courses"}{" "}
              Available
            </p>
          </div>

          <div className="max-w-xl mx-auto mb-12">
            <SearchBar searchTerm={searchTerm} onSearchChange={setSearchTerm} />
          </div>

          {/* Program Filter Tabs */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex bg-white rounded-lg shadow-md p-1 border border-gray-200">
              {[
                { value: "all", label: "All Programs", icon: "🎓" },
                { value: "CS", label: "Computer Science", icon: "💻" },
                { value: "IT", label: "Information Technology", icon: "🌐" },
              ].map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setSelectedProgram(filter.value)}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                    selectedProgram === filter.value
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <span>{filter.icon}</span>
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Semester Filter Tabs */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex bg-white rounded-lg shadow-md p-1 border border-gray-200">
              {[
                { value: "all", label: "All Semesters" },
                { value: "1", label: "1st Semester" },
                { value: "2", label: "2nd Semester" },
              ].map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setSelectedSemester(filter.value)}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    selectedSemester === filter.value
                      ? "bg-purple-600 text-white shadow-sm"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Active Filters Display */}
          {(selectedProgram !== "all" || selectedSemester !== "all") && (
            <div className="flex justify-center mb-6 gap-3">
              {selectedProgram !== "all" && (
                <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium border border-blue-200">
                  <span>
                    {selectedProgram === "CS"
                      ? "💻 Computer Science"
                      : "🌐 Information Technology"}
                  </span>
                  <button
                    onClick={() => setSelectedProgram("all")}
                    className="hover:bg-blue-100 rounded-full p-0.5 transition-colors"
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses?.length > 0 ? (
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
