import { useState } from "react";
import { Eye, BookOpen, Calendar } from "lucide-react";
import { CourseResourceCard } from "./CourseResourceCard";
import { motion, AnimatePresence } from "framer-motion";

export function SemesterResourcesSection({
  courses,
  userYear,
  currentSemester,
  showOnlyCurrentSemester = false,
}) {
  const [isPeeking, setIsPeeking] = useState(false);
  const [peekYear, setPeekYear] = useState(null);

  // User year is now 1, 2, 3, 4 directly from backend
  const currentYear = userYear ? parseInt(userYear) : 1;
  const nextYear = currentYear < 4 ? currentYear + 1 : null;

  // Filter courses by year and semester
  const filterCoursesByYearAndSemester = (year, semester) => {
    return courses.filter(
      (course) =>
        parseInt(course.year) === year &&
        (parseInt(course.semester) === semester || course.semester === "both")
    );
  };

  // Get courses for current year
  const currentYearSem1 = filterCoursesByYearAndSemester(currentYear, 1);
  const currentYearSem2 = filterCoursesByYearAndSemester(currentYear, 2);

  // Get courses for next year (if exists)
  const nextYearSem1 = nextYear
    ? filterCoursesByYearAndSemester(nextYear, 1)
    : [];
  const nextYearSem2 = nextYear
    ? filterCoursesByYearAndSemester(nextYear, 2)
    : [];

  const handlePeek = (year) => {
    if (peekYear === year && isPeeking) {
      setIsPeeking(false);
      setPeekYear(null);
    } else {
      setIsPeeking(true);
      setPeekYear(year);
    }
  };

  const SemesterCard = ({
    semester,
    courses,
    isCurrentSemester,
    year,
    isPeekView = false,
  }) => {
    const totalCredits = courses.reduce(
      (sum, course) => sum + (course.credit_hours || 0),
      0
    );

    return (
      <div className={`space-y-4 ${isPeekView ? "opacity-90" : ""}`}>
        {/* Semester Header */}
        <div
          className={`
            rounded-lg p-4 
            ${
              isCurrentSemester && !isPeekView
                ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white"
                : "bg-gradient-to-r from-gray-700 to-gray-800 text-white"
            }
          `}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                <h3 className="text-lg font-bold">
                  Semester {semester}
                  {isCurrentSemester && !isPeekView && (
                    <span className="ml-2 text-xs bg-white/20 px-2 py-1 rounded">
                      Active
                    </span>
                  )}
                </h3>
              </div>
              <p className="text-sm opacity-90 mt-1">
                Year {year} • {courses.length} Courses • {totalCredits} Credits
              </p>
            </div>
            <BookOpen className="w-6 h-6 opacity-50" />
          </div>
        </div>

        {/* Courses Grid */}
        {courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <CourseResourceCard
                key={course.course_id}
                course={course}
                isCurrentSemester={isCurrentSemester && !isPeekView}
                isPeek={isPeekView}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <BookOpen className="w-12 h-12 mx-auto mb-2 opacity-30" />
            <p>No courses available for this semester</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {showOnlyCurrentSemester
              ? "Current Semester Resources"
              : "Academic Resources"}
          </h2>
          <p className="text-gray-600 mt-1">
            Year {currentYear}
            {showOnlyCurrentSemester && ` • Semester ${currentSemester}`}
          </p>
        </div>

        {/* Peek Next Year Button - Hide if showing only current semester */}
        {nextYear && !showOnlyCurrentSemester && (
          <button
            onClick={() => handlePeek(nextYear)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
              ${
                isPeeking && peekYear === nextYear
                  ? "bg-purple-600 text-white shadow-lg"
                  : "bg-purple-100 text-purple-700 hover:bg-purple-200"
              }
            `}
          >
            <Eye className="w-4 h-4" />
            {isPeeking && peekYear === nextYear ? "Hide" : "Peek"} Next Year
            Courses || Year {nextYear}
          </button>
        )}
      </div>

      {/* Current Year Resources */}
      <div className="bg-white rounded-xl shadow-md p-6 space-y-8">
        {!showOnlyCurrentSemester && (
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1 h-6 bg-blue-600 rounded-full"></div>
            <h3 className="text-xl font-bold text-gray-900">
              Current Year - Year {currentYear}
            </h3>
          </div>
        )}

        {/* Show only current semester or both semesters */}
        {showOnlyCurrentSemester ? (
          <SemesterCard
            key={`current-${currentSemester}`}
            semester={currentSemester}
            courses={filterCoursesByYearAndSemester(
              currentYear,
              currentSemester
            )}
            isCurrentSemester={true}
            year={currentYear}
          />
        ) : (
          <>
            {/* Semester 1 */}
            <SemesterCard
              key={`year-${currentYear}-sem-1`}
              semester={1}
              courses={currentYearSem1}
              isCurrentSemester={currentSemester === 1}
              year={currentYear}
            />

            {/* Semester 2 */}
            <SemesterCard
              key={`year-${currentYear}-sem-2`}
              semester={2}
              courses={currentYearSem2}
              isCurrentSemester={currentSemester === 2}
              year={currentYear}
            />
          </>
        )}
      </div>

      {/* Peek View - Next Year Resources - Hide if showing only current semester */}
      {!showOnlyCurrentSemester && (
        <AnimatePresence>
          {isPeeking && peekYear === nextYear && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl shadow-lg p-6 space-y-8 border-2 border-purple-300 relative z-10"
            >
              {/* Peek Header */}
              <div className="flex items-center gap-3">
                <div className="w-1 h-6 bg-purple-600 rounded-full"></div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-purple-900 flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Preview: Next Year - Year {nextYear}
                  </h3>
                  <p className="text-purple-700 text-sm mt-1">
                    Get a sneak peek at upcoming courses and plan ahead
                  </p>
                </div>
                <button
                  onClick={() => handlePeek(nextYear)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                >
                  Close Preview
                </button>
              </div>

              {/* Next Year Semester 1 */}
              <SemesterCard
                key={`peek-year-${nextYear}-sem-1`}
                semester={1}
                courses={nextYearSem1}
                isCurrentSemester={false}
                year={nextYear}
                isPeekView={true}
              />

              {/* Next Year Semester 2 */}
              <SemesterCard
                key={`peek-year-${nextYear}-sem-2`}
                semester={2}
                courses={nextYearSem2}
                isCurrentSemester={false}
                year={nextYear}
                isPeekView={true}
              />

              {/* Peek Footer */}
              <div className="bg-purple-100 rounded-lg p-4 text-center">
                <p className="text-sm text-purple-800">
                  <strong>Note:</strong> These are the courses you&apos;ll take
                  in your next academic year. Use this preview to prepare ahead
                  and understand the curriculum flow.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* Progress Indicator - Hide if showing only current semester */}
      {!showOnlyCurrentSemester && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Academic Progress
          </h4>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((year) => (
              <div key={year} className="flex-1">
                <div
                  className={`
                    h-2 rounded-full transition-all
                    ${
                      year < currentYear
                        ? "bg-green-500"
                        : year === currentYear
                        ? "bg-blue-500"
                        : "bg-gray-300"
                    }
                  `}
                />
                <p
                  className={`text-xs mt-1 text-center ${
                    year === currentYear
                      ? "font-bold text-blue-600"
                      : "text-gray-500"
                  }`}
                >
                  Year {year}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
