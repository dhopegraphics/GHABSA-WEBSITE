import React from 'react';
import { Building2, Calendar, Clock, ExternalLink, Info, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

export function InternshipCard({ internship }) {
  const deadline = new Date(internship?.application_deadline);
  const isDeadlineSoon = new Date()?.getTime() + (7 * 24 * 60 * 60 * 1000) > deadline?.getTime();

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100 hover:border-blue-500 transition-all duration-300">
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            
            <div className="flex items-center gap-2 mb-2">
              <div className=" p-2 rounded-md bg-blue-50">
              <Building2 className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-base line-clamp-1 font-semibold text-gray-900">{internship?.campany_name}</h3>
            </div>

            <div className="flex flex-col gap-2 mb-4">
              <span className={`
                inline-flex items-center gap-1 px-3 py-1 rounded-full text-[12px] font-medium w-max
                ${isDeadlineSoon ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}
              `}>
                <Calendar className="w-4 h-4" />
                Deadline: {deadline?.toDateString()}
              </span>
              <span className="inline-flex items-center gap-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                Posted: {new Date(internship?.created_at)?.toDateString()}
              </span>
            </div>

            <p className="text-gray-600 mb-6 line-clamp-3">{internship?.description}</p>

            <div className="flex flex-row justify-between items-center w-full">
            <Link to={`/internship/${internship?.internship_id}`} state={{ internship }}
              className="inline-flex  hover:underline items-center gap-2 text-blue-600"
            >
              Read more
            </Link>

            <a
              href={internship?.registration_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex hover:underline items-center gap-2 font-semibold text-blue-600"
            >
              Apply Now
              <ExternalLink className="w-4 h-4" />
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
    </div>
  );
}