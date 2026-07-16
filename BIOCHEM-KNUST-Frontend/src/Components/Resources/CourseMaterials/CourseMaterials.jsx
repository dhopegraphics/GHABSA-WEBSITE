import React, { useCallback, useContext, useEffect } from 'react';
import { FileText, Link as LinkIcon, Download } from 'lucide-react';
import { MaterialCard } from './MaterialCard';
import { BACKEND_HOST } from '../../../utils/config';
import { UserContext } from '../../../Context/UserContext';
import useAxiosWithRefresh from '../../../Hooks/useAxiosWithRefresh';
import { useSavedResources } from '../../../Context/SavedResourcesContext';
import MaterialCardSkeleton from './MaterialCardSkeleton';

export function CourseMaterials({ title, description, resources, isLoading, type }) {
  const getIcon = (type) => {
    switch (type) {
      case 'slides':
        return FileText;
      case 'past_questions':
        return Download;
      case 'tutorials':
        return LinkIcon;
      default:
        return FileText;
    }
  };

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
  

  const checkSaved = (type, id) => {
    let save = false
    if(type == 'slides'){
      save = savedResources?.slides?.slides?.find((item) => item?.id == id);
    }else if (type == 'past_questions'){
      save = savedResources?.past_questions?.past_questions?.find((item) => item?.id == id);
    }else{
      save = savedResources?.online_tutorial_tips?.online_tips?.find((item) => item?.id == id);
    }
    return save ? true : false;
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <div className="flex items-center gap-3 mb-4">
        {React.createElement(getIcon(type), { className: "w-5 h-5 text-blue-600" })}
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
      </div>
      
      <p className="text-gray-600 mb-6">{description}</p>
      { isLoading ?
      <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, idx) => (
      <MaterialCardSkeleton key={idx} />
    ))}
    </div> :
      resources?.length != 0 ? (
        <div className="space-y-4">
        {resources?.map((resource) => (
          <MaterialCard
            key={resource?.id}
            resource={resource}
            type={type}
            saved={checkSaved(type, resource?.id)}
          />
        ))}
      </div>
      ) : 
      <p className="text-center text-gray-500 py-8">
      No resources available yet
    </p>
      }
    </div>
  );
}