import React from 'react';
import { Calendar, User, Clock } from 'lucide-react';


export function BlogHeader({ title, author, date, readTime = 5 }) {
  return (
    <div className="max-w-4xl mx-auto text-center mb-12">
      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">{title}</h1>
      
     <div className="flex flex-col md:flex-row items-start md:items-center justify-start md:justify-center gap-4 md:gap-6 text-gray-600 text-sm">
  <div className="flex items-center gap-2">
    <User className="w-5 h-5 text-blue-600" />
    <span>
      By <span className="font-medium">{author}</span>
    </span>
  </div>

  <div className="flex items-center gap-2">
    <Calendar className="w-5 h-5 text-blue-600" />
    <span>
      {new Date(date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })}
    </span>
  </div>

  <div className="flex items-center gap-2">
    <Clock className="w-5 h-5 text-blue-600" />
    <span>{readTime} min read</span>
  </div>
</div> 
    </div>
  );
}
