import React, { useCallback, useContext, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { useSavedResources } from '../../Context/SavedResourcesContext';
import { UserContext } from '../../Context/UserContext';
import useAxiosWithRefresh from '../../Hooks/useAxiosWithRefresh';
import { BACKEND_HOST } from '../../utils/config';

export function ResourcesOverview() {
  const { user } = useContext(UserContext);

  const axiosInstance = useAxiosWithRefresh();

  const { savedResources, setSavedResources } = useSavedResources();

  const fetchSaved = useCallback(async () => {
    if (user?.access) {
      try {
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-resources/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        setSavedResources(response.data?.data || []);
        // console.log(response.data?.data)
      } catch (error) {
        console.error("Failed to fetch saved materials:", error);
      }
    }
  }, [user, axiosInstance]);

  useEffect(() => {
    fetchSaved()
  }, [])

  const data = [
    { name: 'Past Questions', value: savedResources?.past_questions?.length || 0, color: '#9333ea' },
    { name: 'Course Slides', value: savedResources?.slides?.length || 0, color: '#2563eb' },
    { name: 'Online Resources', value: savedResources?.online_tutorial_tips?.length || 0, color: '#16a34a' },
  ];

  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Resources Distribution</h2>
      
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}