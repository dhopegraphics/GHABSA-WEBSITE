import { Link } from "react-router-dom";

export function ResourceCard({
  year,
  courses,
  icon: Icon,
  description,
  topics,
}) {
  return (
    <Link
      to={`/resources?year=${year}`}
      state={{ courses }}
      className="bg-white group overflow-hidden relative cursor-pointer rounded-xl shadow-lg p-6 border border-gray-100 hover:border-blue-500 transition-colors"
    >
      <div className="absolute group-hover:-bottom-12 group-hover:-right-12 -bottom-48 -right-48 transition-all duration-500 ">
        <Icon className="opacity-20 md:w-[200px] md:h-[200px] w-[180px] h-[180px] text-blue-700" />
      </div>

      <div className="flex items-center gap-4 mb-4 z-10">
        <div className="p-3 bg-blue-50 rounded-lg">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Year {year}</h3>
          <p className="text-blue-600 font-medium">{courses?.length} Courses</p>
        </div>
      </div>

      <p className="text-gray-600 mb-4 z-10">{description}</p>

      <div className="flex flex-wrap gap-2 z-10">
        {courses?.slice(1, 3).map((topic, index) => (
          <p
            key={index}
            className="px-3 py-1 bg-blue-50 text-gray-600 text-[12px] w-max rounded-full"
          >
            {topic?.course_name}
          </p>
        ))}
        {courses?.length > 0 && (
          <p className="px-3 py-1 bg-blue-50 text-gray-600 text-[12px] w-max rounded-full">
            + {courses?.length >= 2 ? courses?.length - 2 : courses?.length}{" "}
            more
          </p>
        )}
      </div>
    </Link>
  );
}
