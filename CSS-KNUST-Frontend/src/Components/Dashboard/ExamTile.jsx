import React from "react";
import { Calendar, Clock, MapPin, BookOpen } from "lucide-react";

const ExamTile = ({ exam, onClick, openModal }) => {
  return (
    <div
      className="flex relative justify-between p-5 overflow-hidden rounded-lg shadow-md bg-white border border-gray-200 group"
      
    >
        <div className="absolute group-hover:-bottom-12 group-hover:-left-12 -bottom-48 -left-48 transition-all duration-500 ">
    <p className='opacity-20 text-[100px] md:text-[120px] text-blue-700' >{exam.course.course_code}</p>
    </div>
      <div className="flex flex-col gap-3 z-10">
        <h3 className="text-sm md:text-base font-semibold text-gray-900 flex items-center gap-2">
        <div className="p-3 bg-blue-50 rounded-lg flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-blue-600" />
              </div>
          {exam.course.course_name}
        </h3>
        <div className="flex gap-4 items-center">
        <div className="text-sm flex items-center gap-2 text-gray-600">
          <Calendar className="w-4 h-4 text-blue-500" />
          {new Date(exam.time).toDateString()}
        </div>
        <div className="text-sm flex items-center gap-2 text-gray-600">
          <Clock className="w-4 h-4 text-blue-500" />
          {new Date(exam.time).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
        </div>
        <div className="text-sm flex items-center gap-2 text-gray-600">
          <MapPin className="w-4 h-4 text-blue-500" />
          <span>{exam.room}</span>, <span>{exam.college}</span>
        </div>
      </div>

      <div className="flex flex-col justify-around gap-6 z-10">
        <p className="text-sm text-gray-600 flex items-center gap-2">
          {new Date(exam.time) < new Date() ?
          <span className="bg-red-50 text-red-600 py-1 px-3 rounded-lg text-xs font-medium">
          Past
        </span> :
            <span className="bg-blue-50 text-blue-600 py-1 px-2 rounded-lg text-xs font-medium">
            {exam.course.course_code}
          </span>}
        </p>
      <div onClick={() =>{onClick(); openModal()}} className="flex cursor-pointer items-center justify-center p-3 bg-blue-50 rounded-md">
        <MapPin className="w-5 h-5 text-blue-600" />
      </div>
      </div>
    </div>
  );
};

export default ExamTile;
