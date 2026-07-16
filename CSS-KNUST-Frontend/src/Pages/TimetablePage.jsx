import { useState, useEffect, useContext } from "react";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { Link } from "react-router-dom";
import {
  Calendar,
  Clock,
  BookOpen,
  MapPin,
  Users,
  AlertCircle,
  ChevronRight,
  ChevronLeft,
  FileText,
  GraduationCap,
  X,
  User,
  Info,
} from "lucide-react";
import { Alert, AlertTitle, Snackbar } from "@mui/material";
import { Hourglass } from "react-loader-spinner";
import { CalendarSyncButton } from "../Components/CalendarSync/CalendarSyncModal";

// Schedule Detail Popup Component
function ScheduleDetailPopup({ schedule, onClose, formatTime, dayName }) {
  if (!schedule) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-xs sm:text-sm opacity-90 mb-1">{dayName}</div>
              <h3 className="font-bold text-lg sm:text-xl">
                {schedule.course.course_code}
              </h3>
              <p className="text-sm sm:text-base text-blue-100 mt-1">
                {schedule.course.course_name}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-white/20 rounded-full transition flex-shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-5 space-y-4">
          {/* Time */}
          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-xs text-gray-500">Time</div>
              <div className="font-semibold text-gray-900">
                {formatTime(schedule.start_time)} - {formatTime(schedule.end_time)}
              </div>
            </div>
          </div>

          {/* Room/Location */}
          {schedule.room && (
            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-xl">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Location</div>
                <div className="font-semibold text-gray-900">{schedule.room}</div>
              </div>
            </div>
          )}

          {/* Lecturer if available */}
          {schedule.course.lecturer_name && (
            <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-xl">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Lecturer</div>
                <div className="font-semibold text-gray-900">{schedule.course.lecturer_name}</div>
              </div>
            </div>
          )}

          {/* Notes if available */}
          {schedule.notes && (
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl">
              <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Info className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Notes</div>
                <div className="text-sm text-gray-900">{schedule.notes}</div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 p-4 sm:p-5">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition active:scale-[0.98]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export function TimetablePage() {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [loading, setLoading] = useState(true);
  const [timetableData, setTimetableData] = useState(null);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(user?.user?.group || "");
  const [savingGroup, setSavingGroup] = useState(false);

  const [notification, setNotification] = useState({
    open: false,
    message: "",
    severity: "info",
  });

  // For mobile day navigation
  const [selectedDayIndex, setSelectedDayIndex] = useState(
    new Date().getDay() === 0 ? 6 : new Date().getDay() - 1 // Default to today (Mon=0, Sun=6)
  );

  // For schedule detail popup
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [selectedScheduleDay, setSelectedScheduleDay] = useState("");

  const daysOfWeek = [
    { id: 1, name: "Monday", short: "Mon", tiny: "M" },
    { id: 2, name: "Tuesday", short: "Tue", tiny: "T" },
    { id: 3, name: "Wednesday", short: "Wed", tiny: "W" },
    { id: 4, name: "Thursday", short: "Thu", tiny: "T" },
    { id: 5, name: "Friday", short: "Fri", tiny: "F" },
    { id: 6, name: "Saturday", short: "Sat", tiny: "S" },
    { id: 7, name: "Sunday", short: "Sun", tiny: "S" },
  ];

  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  const fetchTimetable = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(
        `${BACKEND_HOST}/timetable_system/timetable/`,
        {
          headers: { Authorization: `Bearer ${user.access}` },
        }
      );

      setTimetableData(response.data);

      // Check if user needs to select a group (only for CS students)
      // IT students don't have groups, so skip the modal for them
      const userProgram = response.data.user_info?.program;
      const requiresGroup = response.data.class_schedules?.requires_group_selection;
      
      if (requiresGroup && userProgram === "CS") {
        setShowGroupModal(true);
      }

      if (response.data.status === "success") {
        showNotification("Timetable loaded successfully", "success");
      }
    } catch (error) {
      console.error("Error fetching timetable:", error);
      showNotification(
        error.response?.data?.message || "Failed to load timetable",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimetable();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const saveGroup = async () => {
    if (!selectedGroup) {
      showNotification("Please select a group", "warning");
      return;
    }

    try {
      setSavingGroup(true);
      await axiosInstance.put(
        `${BACKEND_HOST}/accounts/update-account/`,
        { group: selectedGroup },
        {
          headers: { Authorization: `Bearer ${user.access}` },
        }
      );

      showNotification("Group saved successfully!", "success");
      setShowGroupModal(false);

      // Refresh timetable with new group
      fetchTimetable();
    } catch (error) {
      console.error("Error saving group:", error);
      showNotification("Failed to save group selection", "error");
    } finally {
      setSavingGroup(false);
    }
  };

  const closeNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const groupSchedulesByDay = (schedules) => {
    const grouped = {};
    daysOfWeek.forEach((day) => {
      grouped[day.id] = [];
    });

    schedules?.forEach((schedule) => {
      if (grouped[schedule.day_of_week]) {
        grouped[schedule.day_of_week].push(schedule);
      }
    });

    return grouped;
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return "";
    return new Date(`1970-01-01T${timeStr}`).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatExamDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <div className="text-center">
          <Hourglass colors={["#3B82F6", "#3B82F6"]} width="50" height={50} />
          <p className="mt-4 text-gray-600 text-sm sm:text-base">Loading your timetable...</p>
        </div>
      </div>
    );
  }

  const classSchedules = groupSchedulesByDay(
    timetableData?.class_schedules?.data || []
  );
  const examSchedules = timetableData?.exam_schedules?.data || [];
  const userInfo = timetableData?.user_info || {};

  // Navigation helpers for mobile
  const goToPrevDay = () => {
    setSelectedDayIndex((prev) => (prev === 0 ? 6 : prev - 1));
  };

  const goToNextDay = () => {
    setSelectedDayIndex((prev) => (prev === 6 ? 0 : prev + 1));
  };

  const selectedDay = daysOfWeek[selectedDayIndex];

  // Open schedule detail popup
  const openScheduleDetail = (schedule, dayName) => {
    setSelectedSchedule(schedule);
    setSelectedScheduleDay(dayName);
  };

  const closeScheduleDetail = () => {
    setSelectedSchedule(null);
    setSelectedScheduleDay("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 py-4 sm:py-6 lg:py-8 px-2 sm:px-4 md:px-6 lg:px-8">
      {/* Schedule Detail Popup */}
      {selectedSchedule && (
        <ScheduleDetailPopup
          schedule={selectedSchedule}
          onClose={closeScheduleDetail}
          formatTime={formatTime}
          dayName={selectedScheduleDay}
        />
      )}

      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={closeNotification}
      >
        <Alert
          onClose={closeNotification}
          severity={notification.severity}
          sx={{ width: "100%" }}
        >
          <AlertTitle>
            {notification.severity === "success"
              ? "Success"
              : notification.severity === "error"
              ? "Error"
              : "Info"}
          </AlertTitle>
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Group Selection Modal - Only for CS students */}
      {showGroupModal && userInfo?.program === "CS" && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-md p-6 sm:p-8 max-h-[90vh] overflow-y-auto">
            <div className="text-center mb-4 sm:mb-6">
              <Users className="w-12 h-12 sm:w-16 sm:h-16 text-blue-600 mx-auto mb-3 sm:mb-4" />
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                Select Your Group
              </h2>
              <p className="text-sm sm:text-base text-gray-600">
                As a Computer Science student, please select your class group to view personalized schedules
              </p>
            </div>

            <div className="space-y-3 sm:space-y-4 mb-4 sm:mb-6">
              <button
                onClick={() => setSelectedGroup("G1")}
                className={`w-full p-3 sm:p-4 rounded-xl border-2 transition-all active:scale-[0.98] ${
                  selectedGroup === "G1"
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-gray-200 hover:border-blue-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm sm:text-base">Group 1</span>
                  {selectedGroup === "G1" && (
                    <ChevronRight className="w-5 h-5 text-blue-600" />
                  )}
                </div>
              </button>

              <button
                onClick={() => setSelectedGroup("G2")}
                className={`w-full p-3 sm:p-4 rounded-xl border-2 transition-all active:scale-[0.98] ${
                  selectedGroup === "G2"
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-gray-200 hover:border-blue-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm sm:text-base">Group 2</span>
                  {selectedGroup === "G2" && (
                    <ChevronRight className="w-5 h-5 text-blue-600" />
                  )}
                </div>
              </button>
            </div>

            <button
              onClick={saveGroup}
              disabled={savingGroup || !selectedGroup}
              className="w-full py-3 sm:py-3.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition active:scale-[0.98] flex items-center justify-center gap-2 text-sm sm:text-base"
            >
              {savingGroup ? (
                <>
                  <Hourglass
                    colors={["#ffffff", "#ffffff"]}
                    width="18"
                    height={18}
                  />
                  Saving...
                </>
              ) : (
                "Save Selection"
              )}
            </button>

            <Link
              to="/dashboard/account"
              className="block text-center text-xs sm:text-sm text-gray-600 hover:text-blue-600 mt-3 transition"
            >
              Or update in Account Settings
            </Link>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Header */}
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg p-4 sm:p-6">
          <div className="flex flex-col gap-4">
            {/* Title and user info */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex w-12 h-12 lg:w-14 lg:h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl items-center justify-center">
                  <GraduationCap className="w-6 h-6 lg:w-7 lg:h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    My Timetable
                  </h1>
                  <p className="text-xs sm:text-sm lg:text-base text-gray-600 mt-0.5 sm:mt-1">
                    {userInfo.program_display} • Year {userInfo.year}
                    {userInfo.group_display && ` • ${userInfo.group_display}`}
                  </p>
                </div>
              </div>
              
              {/* Calendar sync button - visible on larger screens */}
              <div className="hidden sm:block">
                <CalendarSyncButton
                  calendarTypes={["classes", "exams"]}
                  variant="default"
                  className="flex items-center gap-2"
                />
              </div>
            </div>

            {/* Info badges and mobile calendar sync */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              {/* Mobile calendar sync */}
              <div className="sm:hidden w-full mb-2">
                <CalendarSyncButton
                  calendarTypes={["classes", "exams"]}
                  variant="default"
                  className="flex items-center justify-center gap-2 w-full"
                />
              </div>
              
              <div className="flex-1 min-w-[100px] px-3 py-2 sm:px-4 sm:py-2.5 bg-blue-50 rounded-lg sm:rounded-xl">
                <span className="text-[10px] sm:text-xs text-gray-500 block">Academic Year</span>
                <p className="font-semibold text-blue-900 text-xs sm:text-sm lg:text-base truncate">
                  {userInfo.academic_year}
                </p>
              </div>
              <div className="flex-1 min-w-[80px] px-3 py-2 sm:px-4 sm:py-2.5 bg-green-50 rounded-lg sm:rounded-xl">
                <span className="text-[10px] sm:text-xs text-gray-500 block">Semester</span>
                <p className="font-semibold text-green-900 text-xs sm:text-sm lg:text-base">
                  {userInfo.current_semester}
                </p>
              </div>
              {userInfo.group && (
                <div className="flex-1 min-w-[70px] px-3 py-2 sm:px-4 sm:py-2.5 bg-purple-50 rounded-lg sm:rounded-xl">
                  <span className="text-[10px] sm:text-xs text-gray-500 block">Group</span>
                  <p className="font-semibold text-purple-900 text-xs sm:text-sm lg:text-base">
                    {userInfo.group_display}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Class Schedules */}
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg p-4 sm:p-6">
          <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 mb-4 sm:mb-6 flex items-center gap-2">
            <Calendar className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-blue-600" />
            Class Schedule
          </h2>

          {timetableData?.class_schedules?.status === "error" ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 sm:p-6 flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
              <AlertCircle className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 mb-1 text-sm sm:text-base">
                  Profile Update Required
                </h3>
                <p className="text-yellow-700 mb-3 text-xs sm:text-sm">
                  {timetableData.class_schedules.message}
                </p>
                <div className="flex flex-wrap gap-2">
                  {timetableData.class_schedules.requires_group_selection && (
                    <button
                      onClick={() => setShowGroupModal(true)}
                      className="px-3 sm:px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition text-xs sm:text-sm active:scale-[0.98]"
                    >
                      Select Group
                    </button>
                  )}
                  <Link
                    to="/dashboard/account"
                    className="inline-block px-3 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-xs sm:text-sm"
                  >
                    Update Profile
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Mobile Day Selector */}
              <div className="lg:hidden mb-4">
                {/* Day pills - horizontal scroll on mobile */}
                <div className="flex gap-1 sm:gap-2 overflow-x-auto pb-2 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
                  {daysOfWeek.map((day, index) => (
                    <button
                      key={day.id}
                      onClick={() => setSelectedDayIndex(index)}
                      className={`flex-shrink-0 px-3 sm:px-4 py-2 rounded-full text-xs sm:text-sm font-medium transition-all active:scale-95 ${
                        selectedDayIndex === index
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      <span className="sm:hidden">{day.short}</span>
                      <span className="hidden sm:inline">{day.name}</span>
                    </button>
                  ))}
                </div>

                {/* Selected day card - mobile */}
                <div className="mt-4">
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-3 sm:p-4 rounded-t-xl flex items-center justify-between">
                    <button
                      onClick={goToPrevDay}
                      className="p-1.5 sm:p-2 hover:bg-white/20 rounded-full transition active:scale-90"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="text-center">
                      <div className="text-xs sm:text-sm opacity-90">{selectedDay.short}</div>
                      <div className="font-bold text-base sm:text-lg">{selectedDay.name}</div>
                    </div>
                    <button
                      onClick={goToNextDay}
                      className="p-1.5 sm:p-2 hover:bg-white/20 rounded-full transition active:scale-90"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="border-x border-b border-gray-200 rounded-b-xl min-h-[180px] sm:min-h-[200px] p-3 sm:p-4 space-y-3">
                    {classSchedules[selectedDay.id]?.length > 0 ? (
                      classSchedules[selectedDay.id].map((schedule) => (
                        <div
                          key={schedule.id}
                          onClick={() => openScheduleDetail(schedule, selectedDay.name)}
                          className="bg-blue-50 border border-blue-200 rounded-xl p-3 sm:p-4 hover:shadow-md hover:bg-blue-100/80 transition cursor-pointer active:scale-[0.98] group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="font-bold text-blue-900 text-sm sm:text-base group-hover:text-blue-700">
                                {schedule.course.course_code}
                              </div>
                              <div className="text-xs sm:text-sm text-gray-700 truncate">
                                {schedule.course.course_name}
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <div className="flex items-center gap-1 text-xs sm:text-sm text-blue-700 font-medium">
                                <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
                                {formatTime(schedule.start_time)}
                              </div>
                              <div className="text-[10px] sm:text-xs text-gray-500">
                                to {formatTime(schedule.end_time)}
                              </div>
                            </div>
                          </div>
                          {schedule.room && (
                            <div className="flex items-center gap-1 text-xs text-gray-600 mt-2 bg-white/60 rounded-lg px-2 py-1.5 w-fit">
                              <MapPin className="w-3 h-3" />
                              {schedule.room}
                            </div>
                          )}
                          {/* Tap hint */}
                          <div className="text-[10px] text-blue-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity text-center">
                            Tap for details
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-gray-400 py-12 sm:py-16">
                        <Calendar className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 opacity-50" />
                        <p className="text-sm sm:text-base">No classes on {selectedDay.name}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Desktop/Tablet Week View */}
              <div className="hidden lg:block overflow-x-auto">
                <div className="grid grid-cols-7 gap-2 xl:gap-4 min-w-[900px]">
                  {daysOfWeek.map((day) => (
                    <div key={day.id} className="min-w-[120px] xl:min-w-[140px]">
                      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-2 xl:p-3 rounded-t-xl text-center font-semibold">
                        <div className="text-[10px] xl:text-xs opacity-90">{day.short}</div>
                        <div className="text-sm xl:text-base">{day.name}</div>
                      </div>
                      <div className="border-x border-b border-gray-200 rounded-b-xl min-h-[200px] xl:min-h-[250px] p-1.5 xl:p-2 space-y-1.5 xl:space-y-2">
                        {classSchedules[day.id]?.length > 0 ? (
                          classSchedules[day.id].map((schedule) => (
                            <div
                              key={schedule.id}
                              onClick={() => openScheduleDetail(schedule, day.name)}
                              className="bg-blue-50 border border-blue-200 rounded-lg p-2 xl:p-3 hover:shadow-lg hover:bg-blue-100 hover:border-blue-300 hover:scale-[1.02] transition-all cursor-pointer group relative"
                              title="Click to view details"
                            >
                              <div className="font-semibold text-blue-900 text-[11px] xl:text-sm mb-0.5 xl:mb-1 truncate group-hover:text-blue-700">
                                {schedule.course.course_code}
                              </div>
                              <div className="text-[10px] xl:text-xs text-gray-700 mb-1.5 xl:mb-2 line-clamp-2">
                                {schedule.course.course_name}
                              </div>
                              <div className="flex items-center gap-1 text-[10px] xl:text-xs text-gray-600 mb-0.5 xl:mb-1">
                                <Clock className="w-2.5 h-2.5 xl:w-3 xl:h-3 flex-shrink-0" />
                                <span className="truncate">
                                  {formatTime(schedule.start_time)} - {formatTime(schedule.end_time)}
                                </span>
                              </div>
                              {schedule.room && (
                                <div className="flex items-center gap-1 text-[10px] xl:text-xs text-gray-600">
                                  <MapPin className="w-2.5 h-2.5 xl:w-3 xl:h-3 flex-shrink-0" />
                                  <span className="truncate">{schedule.room}</span>
                                </div>
                              )}
                              {/* Hover tooltip indicator */}
                              <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-md">
                                <Info className="w-3 h-3 text-white" />
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center text-gray-400 py-8 xl:py-12 text-[11px] xl:text-sm">
                            No classes
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Exam Schedules */}
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg p-4 sm:p-6">
          <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 mb-4 sm:mb-6 flex items-center gap-2">
            <FileText className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-red-600" />
            Exam Schedule
          </h2>

          {examSchedules.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3 sm:gap-4">
              {examSchedules.map((exam) => (
                <div
                  key={exam.id}
                  className="bg-gradient-to-br from-red-50 to-orange-50 border border-red-200 rounded-xl p-3 sm:p-4 hover:shadow-lg transition active:scale-[0.99]"
                >
                  <div className="flex items-start justify-between mb-2 sm:mb-3 gap-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-bold text-red-900 text-base sm:text-lg truncate">
                        {exam.course.course_code}
                      </h3>
                      <p className="text-xs sm:text-sm text-gray-700 line-clamp-2">
                        {exam.course.course_name}
                      </p>
                    </div>
                    <BookOpen className="w-5 h-5 sm:w-6 sm:h-6 text-red-600 flex-shrink-0" />
                  </div>

                  <div className="space-y-1.5 sm:space-y-2 text-xs sm:text-sm">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Calendar className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-red-600 flex-shrink-0" />
                      <span className="font-medium truncate">
                        {formatExamDate(exam.time)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-700">
                      <MapPin className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-red-600 flex-shrink-0" />
                      <span className="truncate">
                        {exam.college} {exam.room && `- ${exam.room}`}
                      </span>
                    </div>
                    {exam.index_number_start && exam.index_number_end && (
                      <div className="text-[10px] sm:text-xs bg-white/60 rounded-lg p-2 mt-2">
                        <span className="font-medium">Index Range:</span>{" "}
                        <span className="text-gray-600">
                          {exam.index_number_start} - {exam.index_number_end}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6 sm:p-8 lg:p-12 text-center">
              <FileText className="w-10 h-10 sm:w-12 sm:h-12 text-gray-400 mx-auto mb-2 sm:mb-3" />
              <p className="text-sm sm:text-base text-gray-600">No upcoming exams scheduled</p>
              <p className="text-xs sm:text-sm text-gray-500 mt-1">
                Check back later for updates
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
