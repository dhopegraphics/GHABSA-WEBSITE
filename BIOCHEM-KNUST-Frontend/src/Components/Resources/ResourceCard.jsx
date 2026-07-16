import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

export function ResourceCard({
  year,
  courses,
  icon: Icon,
  description,
}) {
  return (
    <Link
      to={`/resources?year=${year}`}
      state={{ courses }}
      className="group relative flex min-h-[330px] flex-1 cursor-pointer flex-col overflow-hidden rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_12px_40px_rgba(15,23,42,0.05)] transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-[0_20px_50px_rgba(15,23,42,0.09)]"
    >
      <div className="absolute -bottom-14 -right-12 transition-all duration-500 group-hover:-rotate-6 group-hover:scale-110">
        <Icon className="h-40 w-40 text-blue-50" />
      </div>

      <div className="z-10 flex items-center justify-between gap-4">
        <div className="rounded-2xl bg-blue-50 p-3">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">{courses?.length || 0} courses</span>
      </div>
      <p className="z-10 mt-8 text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Academic level</p>
      <h3 className="z-10 mt-2 text-3xl font-semibold tracking-[-0.03em] text-slate-950">Year {year}</h3>
      <p className="z-10 mt-3 text-sm leading-6 text-slate-600">{description}</p>

      <div className="z-10 mt-5 flex flex-wrap gap-2">
        {courses?.slice(1, 3).map((topic, index) => (
          <p
            key={index}
            className="w-max rounded-full bg-slate-100 px-3 py-1 text-[11px] text-slate-600"
          >
            {topic?.course_name}
          </p>
        ))}
        {courses?.length > 0 && (
          <p className="w-max rounded-full bg-slate-100 px-3 py-1 text-[11px] text-slate-600">
            + {courses?.length >= 2 ? courses?.length - 2 : courses?.length}{" "}
            more
          </p>
        )}
      </div>
      <span className="z-10 mt-auto flex items-center gap-2 pt-7 text-sm font-semibold text-blue-700">Open resources <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /></span>
    </Link>
  );
}
