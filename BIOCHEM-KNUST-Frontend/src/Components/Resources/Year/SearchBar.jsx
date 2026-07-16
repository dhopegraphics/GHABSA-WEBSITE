import React from 'react';
import { Search } from 'lucide-react';

export function SearchBar({ searchTerm, onSearchChange }) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
      <input
        type="text"
        placeholder="Search courses..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}