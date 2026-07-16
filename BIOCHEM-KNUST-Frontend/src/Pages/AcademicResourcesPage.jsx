import { useContext, useEffect } from "react";
import { UserContext } from "../Context/UserContext";
import { useCourses } from "../Context/CoursesContext";
import { useCourseResources } from "../Hooks/useCourseResources";
import { SemesterResourcesSection } from "../Components/Dashboard/AcademicResources/SemesterResourcesSection";
import { getData } from "../utils/apiHandler";
import { scrollToTop } from "../utils/scrollToTop";
import { BookOpen, GraduationCap, Loader } from "lucide-react";

export function AcademicResourcesPage() {
  const { user } = useContext(UserContext);
  const { courses, setCourses } = useCourses();

  // Fetch detailed resources for all courses
  const { enrichedCourses, loading: resourcesLoading } =
    useCourseResources(courses);

  useEffect(() => {
    scrollToTop();
  }, []);

  // The department has one programme; courses are organised by year/semester.
  useEffect(() => {
    const fetchCourses = async () => {
      if (!courses || courses.length === 0) {
        const { response, error } = await getData(`/academics/courses/`);
        if (error) {
          console.error("Error fetching courses:", error);
        }
        if (response) {
          setCourses(response);
        }
      }
    };
    fetchCourses();
  }, [courses, setCourses]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-blue-100 rounded-lg">
              <BookOpen className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Academic Resources
              </h1>
              <p className="text-gray-600 mt-1">
                Access course materials, past questions, slides, and tutorials
                organized by semester
              </p>
            </div>
          </div>

          {/* User Info Card */}
          <div className="mt-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <GraduationCap className="w-12 h-12" />
                <div>
                  <h2 className="text-xl font-bold">
                    {user?.user?.first_name} {user?.user?.last_name}
                  </h2>
                  <p className="text-blue-100 mt-1">
                    Year {user?.user?.year || "N/A"} • Semester{" "}
                    {user?.user?.current_semester || "N/A"}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">
                  {user?.user?.completed_semesters || 0}/8
                </div>
                <div className="text-sm text-blue-100">Semesters Completed</div>
              </div>
            </div>
          </div>
        </div>

        {/* Resources Section */}
        {enrichedCourses && enrichedCourses.length > 0 && user?.user?.year ? (
          <div className="relative">
            {resourcesLoading && (
              <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-10 rounded-xl">
                <div className="flex flex-col items-center gap-3">
                  <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                  <p className="text-sm text-gray-600 font-medium">
                    Loading course resources...
                  </p>
                </div>
              </div>
            )}
            <SemesterResourcesSection
              courses={enrichedCourses}
              userYear={user?.user?.year}
              currentSemester={user?.user?.current_semester || 1}
            />
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              {courses && courses.length > 0
                ? "Loading Resources..."
                : "No Courses Available"}
            </h3>
            <p className="text-gray-500">
              {courses && courses.length > 0
                ? "Please wait while we fetch your academic resources"
                : "Please check back later or contact support"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
