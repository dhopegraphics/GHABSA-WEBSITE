import { useContext, useEffect, useState } from "react";
import {
  Calendar,
  Clock,
  MapPin,
  BookOpen,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { UserContext } from "../../Context/UserContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../../utils/config";

export function NextClassSchedule() {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const [classSchedules, setClassSchedules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [meta, setMeta] = useState(null);

  const daysOfWeek = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
  const currentDayIndex = new Date().getDay() || 7; // Sunday = 0, convert to 7

  const fetchClassSchedules = async () => {
    if (!user?.access) return;

    try {
      setIsLoading(true);
      setError(null);
      const response = await axiosInstance.get(
        `${BACKEND_HOST}/timetable_system/class-schedules/`,
        {
          headers: { Authorization: `Bearer ${user.access}` },
        }
      );

      // New endpoint returns {status, message, data, meta}
      if (response.data?.status === "success") {
        setClassSchedules(response.data?.data || []);
        setMeta(response.data?.meta || null);
      } else {
        setError(response.data?.message || "Failed to load class schedules");
      }
    } catch (error) {
      console.error("Failed to fetch class schedules:", error);
      if (error.response?.data?.message) {
        setError(error.response.data.message);
      } else {
        setError("Unable to load class schedules. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClassSchedules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Get today's classes
  const getTodayClasses = () => {
    return classSchedules.filter(
      (schedule) => schedule.day_of_week === currentDayIndex
    );
  };

  // Get next class (today or upcoming)
  const getNextClass = () => {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    // Check today's classes first
    const todayClasses = getTodayClasses();
    for (const classItem of todayClasses) {
      const [hours, minutes] = classItem.start_time.split(":").map(Number);
      const classTime = hours * 60 + minutes;
      if (classTime > currentTime) {
        return { ...classItem, isToday: true };
      }
    }

    // If no more classes today, find next day's first class
    for (let i = 1; i <= 7; i++) {
      const nextDay = ((currentDayIndex + i - 1) % 7) + 1;
      const nextDayClasses = classSchedules.filter(
        (schedule) => schedule.day_of_week === nextDay
      );
      if (nextDayClasses.length > 0) {
        return { ...nextDayClasses[0], isToday: false };
      }
    }

    return null;
  };

  // Get upcoming classes (next 3 classes)
  const getUpcomingClasses = () => {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    const upcoming = [];

    // Today's remaining classes
    const todayClasses = getTodayClasses();
    for (const classItem of todayClasses) {
      const [hours, minutes] = classItem.start_time.split(":").map(Number);
      const classTime = hours * 60 + minutes;
      if (classTime > currentTime) {
        upcoming.push({ ...classItem, dayLabel: "Today" });
      }
    }

    // Future days' classes
    for (let i = 1; i <= 6 && upcoming.length < 3; i++) {
      const nextDay = ((currentDayIndex + i - 1) % 7) + 1;
      const dayLabel = daysOfWeek[nextDay - 1];
      const nextDayClasses = classSchedules.filter(
        (schedule) => schedule.day_of_week === nextDay
      );

      for (const classItem of nextDayClasses) {
        if (upcoming.length < 3) {
          upcoming.push({ ...classItem, dayLabel });
        }
      }
    }

    return upcoming.slice(0, 3);
  };

  const nextClass = getNextClass();
  const upcomingClasses = getUpcomingClasses();

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(":");
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-600" />
          Class Schedule
        </h2>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <AlertCircle className="w-12 h-12 text-orange-500 mb-4" />
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchClassSchedules}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (classSchedules.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-600" />
          Class Schedule
        </h2>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <BookOpen className="w-12 h-12 text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">No class schedules available</p>
          <p className="text-sm text-gray-500">
            Class schedules will appear here once they are published
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white  rounded-xl p-6 shadow-lg border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-600" />
          Class Schedule
        </h2>
        <button
          onClick={fetchClassSchedules}
          className="p-2 rounded-lg hover:bg-gray-100 transition"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {meta && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            <span className="font-semibold">{meta.program_display}</span> Year{" "}
            {meta.year} {meta.group_display} • Semester {meta.current_semester}
          </p>
        </div>
      )}

      {/* Next Class Highlight */}
      {nextClass && (
        <div className="mb-6  p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-semibold text-blue-700">
                {nextClass.isToday ? "Next Class Today" : "Next Class"}
              </span>
            </div>
            <span className="text-xs font-medium text-blue-600 bg-white px-2 py-1 rounded-full">
              {nextClass.course.course_code}
            </span>
          </div>

          <h3 className="text-lg font-bold text-gray-900 mb-3">
            {nextClass.course.course_name}
          </h3>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2  text-gray-700">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="font-medium w-full">
                {formatTime(nextClass.start_time)} -{" "}
                {formatTime(nextClass.end_time)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-gray-700">
              <Calendar className="w-4 h-4 text-blue-600" />
              <span>
                {nextClass.isToday
                  ? "Today"
                  : daysOfWeek[nextClass.day_of_week - 1]}
              </span>
            </div>
            {nextClass.room && (
              <div className="flex items-center gap-2 text-gray-700 col-span-2">
                <MapPin className="w-4 h-4 text-blue-600" />
                <span>{nextClass.room}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upcoming Classes */}
      {upcomingClasses.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Upcoming Classes
          </h3>
          <div className="space-y-3">
            {upcomingClasses.map((classItem, index) => (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 text-sm">
                    {classItem.course.course_name}
                  </h4>
                  <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded">
                    {classItem.course.course_code}
                  </span>
                </div>

                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{formatTime(classItem.start_time)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>{classItem.dayLabel}</span>
                  </div>
                  {classItem.room && (
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      <span>{classItem.room}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Total Classes Info */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          {classSchedules.length}{" "}
          {classSchedules.length === 1 ? "class" : "classes"} this week
        </p>
      </div>
    </div>
  );
}
