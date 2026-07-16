import { ArrowUpRight, Building2, Calendar, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

export function InternshipCard({ internship }) {
  const deadline = new Date(internship?.application_deadline);
  const isDeadlineSoon = new Date()?.getTime() + (7 * 24 * 60 * 60 * 1000) > deadline?.getTime();

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.05)] transition-all duration-300 hover:-translate-y-1 hover:border-emerald-200 hover:shadow-[0_20px_50px_rgba(15,23,42,0.09)]">
      <div className="flex h-full flex-col p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            
            <div className="flex items-center gap-2 mb-2">
              <div className="rounded-2xl bg-emerald-50 p-3">
              <Building2 className="h-5 w-5 text-emerald-700" />
              </div>
              <h3 className="line-clamp-2 text-lg font-semibold tracking-tight text-slate-950">{internship?.campany_name}</h3>
            </div>

            <div className="flex flex-col gap-2 mb-4">
              <span className={`
                inline-flex items-center gap-1 px-3 py-1 rounded-full text-[12px] font-medium w-max
                ${isDeadlineSoon ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}
              `}>
                <Calendar className="w-4 h-4" />
                Deadline: {deadline?.toDateString()}
              </span>
              <span className="inline-flex items-center gap-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                Posted: {new Date(internship?.created_at)?.toDateString()}
              </span>
            </div>

            <p className="mb-6 line-clamp-3 text-sm leading-6 text-slate-600">{internship?.description}</p>

            <div className="mt-auto flex w-full flex-row items-center justify-between border-t border-slate-100 pt-5">
            <Link to={`/internship/${internship?.internship_id}`} state={{ internship }}
              className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-950"
            >
              Read more
            </Link>

            <a
              href={internship?.registration_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-700 hover:text-emerald-800"
            >
              Apply Now
              <ArrowUpRight className="h-4 w-4" />
            </a>
            </div>
          </div>
        </div>
      </div>
      {/* <div className="bg-blue-50 p-4 flex items-center justify-between">
        <span className="text-sm text-gray-700 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-500" />
          Be part of our team and grow your career!
        </span>
      </div> */}
    </article>
  );
}
