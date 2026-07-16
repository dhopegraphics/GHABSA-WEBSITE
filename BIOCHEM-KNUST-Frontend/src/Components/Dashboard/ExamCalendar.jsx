import React, { useCallback, useContext, useEffect, useState } from "react";
import { Calendar as CalendarIcon, Clock, MapPin } from "lucide-react";
import { format, isToday } from "date-fns";
import { Calendar } from "react-date-range";
import "react-date-range/dist/styles.css";
import "react-date-range/dist/theme/default.css";
import { useExams } from "../../Context/ExamsContext";
import { UserContext } from "../../Context/UserContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { scrollToTop } from "../../utils/scrollToTop";
import { BACKEND_HOST } from "../../utils/config";

export function ExamCalendar({ setSelectedExam }) {
  const { exams, setExams } = useExams();
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredExam, setHoveredExam] = useState(null);

  const fetchExams = useCallback(async () => {
    if (user?.access) {
      try {
        setIsLoading(true);
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/timetable_system/schedules/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );

        // New endpoint returns {status, message, data, meta}
        const examsData = response.data?.data || [];
        const formattedExams = examsData.map((exam) => ({
          course: exam.course,
          time: exam.time,
          college: exam.college,
          room: exam.room,
          geolocation: exam.geolocation,
          date: exam.time.split("T")[0],
        }));
        setExams(formattedExams || []);
      } catch (error) {
        console.error("Failed to fetch exams:", error);
        setExams([]);
      } finally {
        setIsLoading(false);
      }
    }
  }, [user, axiosInstance, setExams]);

  useEffect(() => {
    scrollToTop();
    fetchExams();
  }, []);

  const renderCustomDay = (day) => {
    const exam = exams?.find(
      (exam) =>
        format(new Date(exam.date), "yyyy-MM-dd") === format(day, "yyyy-MM-dd")
    );

    return (
      <div
        className={`relative text-center w-full rounded-xl z-40`}
        onMouseOver={() => exam && setHoveredExam(exam)}
        onMouseLeave={() => setHoveredExam(null)}
        onClick={() => {
          exam && setSelectedExam(exam);
        }}
      >
        <p
          className={`${
            isToday(day)
              ? "text-blue-600 bg-blue-200 rounded-xl font-bold"
              : "text-black"
          } ${exam && "bg-blue-200 text-blue-600 rounded-xl font-semibold"}`}
        >
          {format(day, "d")}
        </p>
        {exam && (
          <div className="absolute -top-1 -left-1 rounded-full">
            <Clock className="w-4 h-4" />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white h-full z-10 w-full rounded-xl p-6 shadow-lg border border-gray-100 flex flex-col">
      <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
        <CalendarIcon className="w-6 h-6 text-blue-600" />
        Upcoming Exams
      </h2>
      <p className="text-gray-400 text-sm">Click on exam to show on map</p>
      <p className="text-gray-400 text-sm">
        Click here to{" "}
        <span
          onClick={() => fetchExams()}
          className={`underline cursor-pointer ${
            isLoading ? "text-gray-400" : "text-blue-400"
          }`}
        >
          {" "}
          refresh
        </span>
      </p>

      <div className="relative flex-1">
        <Calendar
          onChange={() => {}}
          dayContentRenderer={renderCustomDay}
          color="#2563eb"
        />

        {hoveredExam && (
          <div className="absolute -top-10 z-50 left-1/2 transform -translate-x-1/2 bg-white shadow-md rounded-lg p-4 w-64 border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-2">
              {hoveredExam.course.course_name} ({hoveredExam.course.course_code}
              )
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
              <Clock className="w-4 h-4 text-blue-600" />
              <span>{format(new Date(hoveredExam.time), "hh:mm a")}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
              <CalendarIcon className="w-4 h-4 text-blue-600" />
              <span>{format(new Date(hoveredExam.date), "MMMM d, yyyy")}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4 text-blue-600" />
              {hoveredExam.college} - <span>{hoveredExam.room}</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="mt-auto pt-2 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-blue-50 rounded-lg p-1 text-center">
            <p className="text-xl font-bold text-blue-600">
              {exams?.length || 0}
            </p>
            <p className="text-xs text-gray-600">Total Exams</p>
          </div>
          <div className="bg-green-50 rounded-lg p-1 text-center">
            <p className="text-xl font-bold text-green-600">
              {exams?.filter((exam) => new Date(exam.date) > new Date())
                .length || 0}
            </p>
            <p className="text-xs text-gray-600">Upcoming</p>
          </div>
        </div>
        {exams?.length > 0 && (
          <p className="text-xs text-gray-500 text-center ">
            Next exam:{" "}
            {format(
              new Date(
                exams.sort(
                  (a, b) => new Date(a.date) - new Date(b.date)
                )[0]?.date
              ),
              "MMM d, yyyy"
            )}
          </p>
        )}
      </div>
    </div>
  );
}
