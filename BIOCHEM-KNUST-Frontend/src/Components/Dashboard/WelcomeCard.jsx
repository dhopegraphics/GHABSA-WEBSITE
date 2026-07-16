import React, { useContext } from "react";
import { GraduationCap, Calendar, Award, Clock } from "lucide-react";
import { FcGraduationCap } from "react-icons/fc";
import { UserContext } from "../../Context/UserContext";

export function WelcomeCard({ name, year, program, currentSemester }) {
  const { user } = useContext(UserContext);

  // Get academic status from user data
  const academicStatus = user?.user?.academic_status || {};
  const semesterDisplay = user?.user?.semester_display || "";
  const semesterStatus = user?.user?.semester_status || "active";
  const isGraduated = user?.user?.is_graduated || false;
  const yearNum = user?.user?.year || academicStatus?.year || 1;

  // Get semester display text
  const getSemesterDisplay = () => {
    // Use the semester_display from backend if available
    if (semesterDisplay) {
      return semesterDisplay;
    }

    // Fallback to basic display
    if (!currentSemester) return "Semester N/A";
    return currentSemester === 1 ? "First Semester" : "Second Semester";
  };

  // Get year display with proper handling
  const getYearDisplay = () => {
    if (isGraduated) {
      return "Graduated";
    }
    return `Year ${yearNum}`;
  };

  const completedSemesters = user?.user?.completed_semesters || 0;
  const hasCompleted = user?.user?.has_completed_program || false;

  // Determine status color based on semester status
  const getStatusColor = () => {
    switch (semesterStatus) {
      case "not_started":
        return "text-yellow-200";
      case "completed":
        return "text-green-200";
      default:
        return "text-white";
    }
  };

  return (
    <div className="bg-gradient-to-br relative from-blue-200 to-blue-600 rounded-xl p-6 shadow-lg overflow-hidden">
      <FcGraduationCap className="text-white/10 -rotate-12 text-[250px] absolute z-0 -bottom-20 -right-20" />
      <div className="flex items-start justify-between">
        <div className="z-20 w-full">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {name}!
          </h1>
          <p className="text-white mt-1">
            {program}, {getYearDisplay()}
          </p>

          <div className="flex items-center gap-6 mt-4 flex-wrap">
            <div className="flex items-center gap-2 text-white">
              <GraduationCap className="w-5 h-5" />
              <span>Class of {year}</span>
            </div>
            <div className={`flex items-center gap-2 ${getStatusColor()}`}>
              {semesterStatus === "not_started" ? (
                <Clock className="w-5 h-5" />
              ) : (
                <Calendar className="w-5 h-5" />
              )}
              <span>{getSemesterDisplay()}</span>
            </div>
            <div className="flex items-center gap-2 text-white">
              <Award className="w-5 h-5" />
              <span>
                {completedSemesters} / 8 Semesters
                {hasCompleted && " ✓ COMPLETED"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
