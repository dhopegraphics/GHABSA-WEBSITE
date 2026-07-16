import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Award,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { getData } from "../../../utils/apiHandler";
import { Link, useParams } from "react-router-dom";

export function LecturerProfile({ lecturer }) {
  const { id: currentCourseId } = useParams(); // Get current course ID from URL
  const [isExpanded, setIsExpanded] = useState(false);
  const [coursesCount, setCoursesCount] = useState(0);
  const [lecturerCourses, setLecturerCourses] = useState([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(false);

  // Fetch courses when lecturer is available
  useEffect(() => {
    const fetchLecturerCourses = async () => {
      if (!lecturer?.lecturer_id) return;

      setIsLoadingCourses(true);
      const { response, error } = await getData(
        `/academics/lecturers/${lecturer.lecturer_id}/courses/`
      );

      if (error) {
        console.error("Error fetching lecturer courses:", error);
      }

      if (response) {
        setLecturerCourses(response);
        setCoursesCount(response.length);
      }

      setIsLoadingCourses(false);
    };

    fetchLecturerCourses();
  }, [lecturer?.lecturer_id]);

  if (!lecturer) return null;

  return (
    <div className="max-w-4xl mx-auto mb-8">
      {/* Collapsed View - Minimal Info */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6">
          <div className="flex items-start gap-4">
            {/* Lecturer Photo */}
            <div className="flex-shrink-0">
              {lecturer.profile_image ? (
                <img
                  src={lecturer.profile_image}
                  alt={lecturer.full_name}
                  className="w-20 h-20 rounded-full object-cover border-4 border-white shadow-lg"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-white flex items-center justify-center border-4 border-white shadow-lg">
                  <User className="w-10 h-10 text-blue-600" />
                </div>
              )}
            </div>

            {/* Lecturer Basic Info */}
            <div className="flex-1 text-white">
              <p className="text-sm font-medium opacity-90 mb-1">
                Course Instructor
              </p>
              <h3 className="text-2xl font-bold mb-2">{lecturer.full_name}</h3>
              {lecturer.specialization && (
                <div className="flex items-center gap-2 mb-2">
                  <Award className="w-4 h-4" />
                  <p className="text-sm opacity-90">
                    {lecturer.specialization}
                  </p>
                </div>
              )}
              <div className="flex items-center gap-2 text-sm opacity-90">
                <BookOpen className="w-4 h-4" />
                <span>
                  Teaching {coursesCount}{" "}
                  {coursesCount === 1 ? "course" : "courses"}
                </span>
              </div>
            </div>

            {/* Expand Button */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-shrink-0 p-2 hover:bg-white/10 rounded-lg transition-colors"
              aria-label={isExpanded ? "Show less" : "Show more"}
            >
              {isExpanded ? (
                <ChevronUp className="w-6 h-6 text-white" />
              ) : (
                <ChevronDown className="w-6 h-6 text-white" />
              )}
            </button>
          </div>

          {/* Quick Contact - Always Visible */}
          <div className="flex flex-wrap gap-3 mt-4">
            {lecturer.email && (
              <a
                href={`mailto:${lecturer.email}`}
                className="flex items-center gap-2 px-3 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm text-white transition-colors"
              >
                <Mail className="w-4 h-4" />
                <span className="hidden sm:inline">Email</span>
              </a>
            )}
            {lecturer.phone && (
              <a
                href={`tel:${lecturer.phone}`}
                className="flex items-center gap-2 px-3 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm text-white transition-colors"
              >
                <Phone className="w-4 h-4" />
                <span className="hidden sm:inline">Call</span>
              </a>
            )}
          </div>
        </div>

        {/* Expanded Details */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="p-6 space-y-6">
                {/* Biography */}
                {lecturer.bio && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">
                      About
                    </h4>
                    <p className="text-gray-700 leading-relaxed">
                      {lecturer.bio}
                    </p>
                  </div>
                )}

                {/* Contact Information */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    Contact Information
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {lecturer.email && (
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        <Mail className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500 font-medium mb-1">
                            Email
                          </p>
                          <a
                            href={`mailto:${lecturer.email}`}
                            className="text-sm text-gray-900 hover:text-blue-600 flex items-center gap-1"
                          >
                            {lecturer.email}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    )}
                    {lecturer.phone && (
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        <Phone className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500 font-medium mb-1">
                            Phone
                          </p>
                          <a
                            href={`tel:${lecturer.phone}`}
                            className="text-sm text-gray-900 hover:text-blue-600"
                          >
                            {lecturer.phone}
                          </a>
                        </div>
                      </div>
                    )}
                    {lecturer.office_location && (
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        <MapPin className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500 font-medium mb-1">
                            Office Location
                          </p>
                          <p className="text-sm text-gray-900">
                            {lecturer.office_location}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Specialization & Expertise */}
                {lecturer.specialization && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">
                      Area of Expertise
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {lecturer.specialization.split(",").map((spec, index) => (
                        <span
                          key={index}
                          className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                        >
                          {spec.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Courses Teaching */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    Courses Teaching
                  </h4>
                  {isLoadingCourses ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : lecturerCourses.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {lecturerCourses.map((course) => {
                        const isCurrentCourse =
                          course.course_id === currentCourseId;

                        return isCurrentCourse ? (
                          // Current course - not clickable, show "Currently Viewing" badge
                          <div
                            key={course.course_id}
                            className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border-2 border-green-400 relative"
                          >
                            <div className="absolute top-2 right-2">
                              <span className="px-2 py-1 bg-green-600 text-white rounded-full text-xs font-medium">
                                Currently Viewing
                              </span>
                            </div>
                            <div className="flex items-start gap-3 mt-6">
                              <div className="flex-shrink-0 p-2 bg-green-600 rounded-lg">
                                <BookOpen className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h5 className="font-semibold text-gray-900 text-sm mb-1">
                                  {course.course_code}
                                </h5>
                                <p className="text-xs text-gray-700 mb-2 line-clamp-1">
                                  {course.course_name}
                                </p>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="px-2 py-1 bg-white text-green-700 rounded text-xs font-medium">
                                    Year {course.year}
                                  </span>
                                  <span className="px-2 py-1 bg-white text-emerald-700 rounded text-xs font-medium">
                                    {course.semester_display}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          // Other courses - clickable
                          <Link
                            key={course.course_id}
                            to={`/resources/courses/${course.course_id}`}
                            className="group p-4 bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 rounded-lg border border-blue-200 hover:border-blue-400 transition-all duration-200 hover:shadow-md"
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 p-2 bg-blue-600 rounded-lg group-hover:scale-110 transition-transform">
                                <BookOpen className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h5 className="font-semibold text-gray-900 text-sm mb-1 group-hover:text-blue-700 transition-colors">
                                  {course.course_code}
                                </h5>
                                <p className="text-xs text-gray-700 mb-2 line-clamp-1">
                                  {course.course_name}
                                </p>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="px-2 py-1 bg-white text-blue-700 rounded text-xs font-medium">
                                    Year {course.year}
                                  </span>
                                  <span className="px-2 py-1 bg-white text-indigo-700 rounded text-xs font-medium">
                                    {course.semester_display}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </Link>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">No courses assigned yet</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

LecturerProfile.propTypes = {
  lecturer: PropTypes.shape({
    lecturer_id: PropTypes.string,
    full_name: PropTypes.string,
    profile_image: PropTypes.string,
    specialization: PropTypes.string,
    bio: PropTypes.string,
    email: PropTypes.string,
    phone: PropTypes.string,
    office_location: PropTypes.string,
  }),
};
