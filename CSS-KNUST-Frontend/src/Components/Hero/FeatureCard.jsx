import React from "react";
// import { LucideIcon } from 'lucide-react';

export function FeatureCard({ icon: Icon, title, description }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="text-blue-600 text-xl">
          <Icon />
        </div>
        <span className="font-semibold text-white">{title}</span>
      </div>
      <p className="text-[12px] md:text-sm text-white text-left font-light">
        {description}
      </p>
    </div>
  );
}
