import PropTypes from "prop-types";
import { BookOpen, Code, Calendar } from "lucide-react";
import { LecturerProfile } from "./LecturerProfile";

export function CourseHeader({
  courseCode,
  courseName,
  past_questions,
  materials,
  online,
  course,
}) {
  // Determine semester badge
  const getSemesterInfo = () => {
    if (!course?.semester) return null;

    const badges = {
      1: { text: "1st Semester", color: "bg-blue-600 text-white" },
      2: { text: "2nd Semester", color: "bg-purple-600 text-white" },
      both: { text: "Both Semesters", color: "bg-green-600 text-white" },
    };

    return badges[course.semester] || badges["both"];
  };

  // Determine program badge
  const getProgramInfo = () => {
    if (!course?.program) return null;

    const badges = {
      CS: {
        text: "Computer Science",
        color: "bg-indigo-600 text-white",
        icon: "💻",
      },
      IT: {
        text: "Information Technology",
        color: "bg-cyan-600 text-white",
        icon: "🌐",
      },
    };

    return badges[course.program] || badges["CS"];
  };

  const semesterInfo = getSemesterInfo();
  const programInfo = getProgramInfo();

  return (
    <div className="py-8">
      <div className="flex items-center gap-4 flex-col mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
          <BookOpen className="w-8 h-8 text-blue-600" />
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Code className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-blue-600">{courseCode}</span>
            </div>
            {programInfo && (
              <span
                className={`px-4 py-1 rounded-full text-xs font-semibold ${programInfo.color} flex items-center gap-2`}
              >
                <span>{programInfo.icon}</span>
                {programInfo.text}
              </span>
            )}
            {semesterInfo && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${semesterInfo.color} flex items-center gap-1`}
              >
                <Calendar className="w-3 h-3" />
                {semesterInfo.text}
              </span>
            )}
          </div>
          <h1 className="text-3xl text-center font-bold text-gray-900 mb-4">
            {courseName}
          </h1>

          {/* Course Description */}
          {course?.description && (
            <p className="text-gray-600 max-w-3xl mx-auto mt-4 leading-relaxed">
              {course.description}
            </p>
          )}
        </div>
      </div>

      {/* Lecturer Profile Component */}
      <LecturerProfile lecturer={course?.lecturer} />

      {/* Prerequisites */}
      {course?.prerequisites && course.prerequisites.length > 0 && (
        <div className="max-w-3xl mx-auto mb-8">
          <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3">
            Prerequisites
          </h3>
          <div className="flex flex-wrap gap-3">
            {course.prerequisites.map((prereq) => (
              <div
                key={prereq.course_id}
                className="px-4 py-2 bg-white rounded-lg border-2 border-gray-200 hover:border-blue-300 transition-colors shadow-sm"
              >
                <p className="text-sm font-semibold text-gray-900">
                  {prereq.course_code}
                </p>
                <p className="text-xs text-gray-600">{prereq.course_name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex gap-3 md:gap-20 justify-center mt-6">
        <StatCard label="Materials" value={materials} />
        <StatCard label="Questions" value={past_questions} />
        <StatCard label="Links" value={online} />
      </div>
    </div>
  );
}

CourseHeader.propTypes = {
  courseCode: PropTypes.string,
  courseName: PropTypes.string,
  past_questions: PropTypes.number,
  materials: PropTypes.number,
  online: PropTypes.number,
  course: PropTypes.shape({
    semester: PropTypes.string,
    program: PropTypes.string,
    description: PropTypes.string,
    lecturer: PropTypes.shape({
      full_name: PropTypes.string,
      profile_image: PropTypes.string,
      specialization: PropTypes.string,
      bio: PropTypes.string,
      email: PropTypes.string,
      phone: PropTypes.string,
      office_location: PropTypes.string,
    }),
    prerequisites: PropTypes.arrayOf(
      PropTypes.shape({
        course_id: PropTypes.number,
        course_code: PropTypes.string,
        course_name: PropTypes.string,
      })
    ),
  }),
};

function StatCard({ label, value }) {
  return (
    <div className="px-6 py-4 bg-blue-100 relative rounded-lg text-center">
      <p className="text-3xl absolute -top-4 text-blue-600 font-semibold">
        {value}
      </p>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string,
  value: PropTypes.number,
};
