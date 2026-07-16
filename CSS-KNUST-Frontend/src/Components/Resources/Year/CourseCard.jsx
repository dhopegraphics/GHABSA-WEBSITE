import { useState } from "react";
import PropTypes from "prop-types";
import {
  BookOpen,
  Code,
  Clock,
  User,
  ChevronRight,
  FileText,
} from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export function CourseCard({ course }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine semester badge color and text
  const getSemesterBadge = () => {
    if (!course?.semester) return null;

    const badges = {
      1: {
        text: "1st Semester",
        color: "bg-blue-100 text-blue-700 border-blue-200",
      },
      2: {
        text: "2nd Semester",
        color: "bg-purple-100 text-purple-700 border-purple-200",
      },
      both: {
        text: "Both Semesters",
        color: "bg-green-100 text-green-700 border-green-200",
      },
    };

    return badges[course.semester] || badges["both"];
  };

  // Determine program badge color and text
  const getProgramBadge = () => {
    if (!course?.program) return null;

    const badges = {
      CS: {
        text: "CS",
        color: "bg-indigo-100 text-indigo-700 border-indigo-200",
        icon: "💻",
      },
      IT: {
        text: "IT",
        color: "bg-cyan-100 text-cyan-700 border-cyan-200",
        icon: "🌐",
      },
    };

    return badges[course.program] || badges["CS"];
  };

  const semesterBadge = getSemesterBadge();
  const programBadge = getProgramBadge();

  // Calculate total files count
  const getTotalFilesCount = () => {
    // Use count fields if available, otherwise count arrays
    const slides = course?.slides_count ?? course?.slides?.length ?? 0;
    const pastQuestions =
      course?.past_questions_count ?? course?.past_questions?.length ?? 0;
    const tutorials =
      course?.online_tutorial_tips_count ??
      course?.online_tutorial_tips?.length ??
      0;
    return slides + pastQuestions + tutorials;
  };

  const totalFiles = getTotalFilesCount();

  // Get individual counts with fallback
  const slidesCount = course?.slides_count ?? course?.slides?.length ?? 0;
  const pastQuestionsCount =
    course?.past_questions_count ?? course?.past_questions?.length ?? 0;
  const tutorialsCount =
    course?.online_tutorial_tips_count ??
    course?.online_tutorial_tips?.length ??
    0;

  // Truncate description for preview
  const getDescription = () => {
    if (!course?.description) return null;
    const maxLength = 150;
    if (course.description.length <= maxLength) return course.description;
    return isExpanded
      ? course.description
      : `${course.description.substring(0, maxLength)}...`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="group"
    >
      <Link
        to={`/resources/courses/${course?.course_id}`}
        state={{ course }}
        className="block bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-6 border border-gray-100 hover:border-blue-300"
      >
        {/* Header: Course Code and Badges */}
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-semibold text-blue-600">
              {course.course_code}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {programBadge && (
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium border ${programBadge.color} flex items-center gap-1`}
              >
                <span>{programBadge.icon}</span>
                {programBadge.text}
              </span>
            )}
            {semesterBadge && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium border ${semesterBadge.color}`}
              >
                {semesterBadge.text}
              </span>
            )}
          </div>
        </div>

        {/* Course Title */}
        <h3 className="text-lg font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">
          {course.course_name}
        </h3>

        {/* Description */}
        {course?.description && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 leading-relaxed">
              {getDescription()}
            </p>
            {course.description.length > 150 && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  setIsExpanded(!isExpanded);
                }}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-1 flex items-center gap-1"
              >
                {isExpanded ? "Show less" : "Read more"}
                <ChevronRight
                  className={`w-3 h-3 transition-transform ${
                    isExpanded ? "rotate-90" : ""
                  }`}
                />
              </button>
            )}
          </div>
        )}

        {/* Lecturer Section - Minimal Info */}
        {course?.lecturer && (
          <div className="flex items-center gap-2 mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
            {/* Lecturer Photo */}
            {course.lecturer.profile_image ? (
              <img
                src={course.lecturer.profile_image}
                alt={course.lecturer.full_name}
                className="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-blue-200 flex items-center justify-center border-2 border-white shadow-sm">
                <User className="w-5 h-5 text-blue-700" />
              </div>
            )}
            {/* Lecturer Name */}
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 font-medium">Lecturer</p>
              <p className="text-sm font-bold text-gray-900 truncate">
                {course.lecturer.full_name}
              </p>
            </div>
          </div>
        )}

        {/* Prerequisites */}
        {course?.prerequisites && course.prerequisites.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Prerequisites
            </p>
            <div className="flex flex-wrap gap-2">
              {course.prerequisites.map((prereq) => (
                <span
                  key={prereq.course_id}
                  className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-xs font-medium border border-gray-200"
                >
                  {prereq.course_code}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Files Count Section */}
        <div className="mb-4">
          {totalFiles > 0 ? (
            <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
              <FileText className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-green-800">
                  {totalFiles} {totalFiles === 1 ? "File" : "Files"} Available
                </p>
                <p className="text-xs text-green-600">
                  {slidesCount > 0 && `${slidesCount} Slides`}
                  {slidesCount > 0 &&
                    (pastQuestionsCount > 0 || tutorialsCount > 0) &&
                    " • "}
                  {pastQuestionsCount > 0 &&
                    `${pastQuestionsCount} Past Questions`}
                  {pastQuestionsCount > 0 && tutorialsCount > 0 && " • "}
                  {tutorialsCount > 0 && `${tutorialsCount} Tutorials`}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <FileText className="w-5 h-5 text-gray-400" />
              <p className="text-sm text-gray-500 font-medium">
                No files uploaded yet
              </p>
            </div>
          )}
        </div>

        {/* Course Meta Info */}
        <div className="flex items-center gap-4 text-sm text-gray-600 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1">
            <BookOpen className="w-4 h-4" />
            <span>{course?.credit_hours} Credit hours</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>16 Weeks</span>
          </div>
        </div>

        {/* Hover Arrow */}
        <div className="mt-4 flex items-center justify-end text-blue-600 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
          View Details
          <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
        </div>
      </Link>
    </motion.div>
  );
}

CourseCard.propTypes = {
  course: PropTypes.shape({
    course_id: PropTypes.number,
    course_code: PropTypes.string,
    course_name: PropTypes.string,
    semester: PropTypes.string,
    program: PropTypes.string,
    description: PropTypes.string,
    credit_hours: PropTypes.number,
    slides_count: PropTypes.number,
    past_questions_count: PropTypes.number,
    online_tutorial_tips_count: PropTypes.number,
    lecturer: PropTypes.shape({
      full_name: PropTypes.string,
      profile_image: PropTypes.string,
      specialization: PropTypes.string,
      email: PropTypes.string,
      phone: PropTypes.string,
    }),
    prerequisites: PropTypes.arrayOf(
      PropTypes.shape({
        course_id: PropTypes.number,
        course_code: PropTypes.string,
      })
    ),
  }),
};
