import React, { useCallback, useContext, useEffect } from 'react';
import { FileText, BookOpen, Globe } from 'lucide-react';
import { useSavedResources } from '../../Context/SavedResourcesContext';
import { UserContext } from '../../Context/UserContext';
import useAxiosWithRefresh from '../../Hooks/useAxiosWithRefresh';
import { BACKEND_HOST } from '../../utils/config';

export function StatsGrid() {
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
  const stats = [
    { label: 'Past Questions', value: savedResources?.past_questions?.length || 0, icon: FileText, color: 'text-purple-600', bgcolor: 'bg-purple-100' },
    { label: 'Course Slides', value: savedResources?.slides?.length || 0, icon: BookOpen, color: 'text-blue-600', bgcolor: 'bg-blue-100' },
    { label: 'Online Resources', value: savedResources?.online_tutorial_tips?.length || 0, icon: Globe, color: 'text-green-600', bgcolor: 'bg-green-100' },
  ];

  return (
    <div className="grid grid-cols-3 gap-4 md:gap-2 h-full">
      {stats.map((stat) => (
        <div key={stat.label} className={`${stat.bgcolor} rounded-xl grid place-items-center p-4 shadow-lg border border-gray-100`}>
          <div className="flex flex-col items-center text-center">
            <stat.icon className={`w-8 h-8 ${stat.color} mb-2`} />
            <span className="text-xl font-bold text-gray-900">{stat.value}</span>
            <span className="text-sm text-gray-600">{stat.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}