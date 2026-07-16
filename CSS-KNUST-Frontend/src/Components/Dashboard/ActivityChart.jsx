import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function ActivityChart() {
  const data = [
    { name: 'Wk 1', resources: 0 },
    { name: 'Wk 2', resources: 0 },
    { name: 'Wk 3', resources: 0 },
    { name: 'Wk 4', resources: 0 },
    { name: 'Wk 5', resources: 0 },
    { name: 'Wk 6', resources: 0 },
  ];

  return (
    <div className="bg-white h-full rounded-xl p-6 pl-0 shadow-lg border border-gray-100">
      <h2 className="text-xl pl-6 font-bold text-gray-900 mb-6">Resource Activity</h2>
      
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Area 
              type="monotone" 
              dataKey="resources" 
              stroke="#3b82f6" 
              fill="#93c5fd" 
              name="Resources Saved"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}