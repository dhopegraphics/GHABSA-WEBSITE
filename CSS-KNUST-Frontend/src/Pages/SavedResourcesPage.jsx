import React, { useEffect, useState, useContext, useCallback } from "react";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react'
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { MaterialCard } from "../Components/Resources/CourseMaterials/MaterialCard";
import { UserContext } from "../Context/UserContext";
import { useSavedResources } from "../Context/SavedResourcesContext";
import MaterialCardSkeleton from "../Components/Resources/CourseMaterials/MaterialCardSkeleton";
import { useCourses } from "../Context/CoursesContext";
import { getData } from "../utils/apiHandler";

export function SavedResourcesPage() {
  const { user } = useContext(UserContext);
  const [isLoading, setIsLoading] = useState(true);

  const axiosInstance = useAxiosWithRefresh();
  const { savedResources, setSavedResources } = useSavedResources();

  const fetchSavedResources = useCallback(async () => {
    if (user?.access) {
      try {
        setIsLoading(true);
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/accounts/saved-resources/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );
        setSavedResources(
          response.data?.data || []
        );
      } catch (error) {
        console.error("Failed to fetch saved resources:", error);
      } finally {
        setIsLoading(false);
      }
    }
  }, [axiosInstance, user]);

  const { setCourses } = useCourses();

  // Fetch courses filtered by user's program
  const fetchCourses = async () => {
    const userProgram = user?.user?.program;
    if (!userProgram) return;
    
    const { response, error } = await getData(
      `/academics/courses/?program=${userProgram}`
    );
    if (error) {
      console.error("Error fetching Courses:", error);
    }
    if (response) {
      setCourses(response);
    }
  };

  useEffect(() => {
    fetchSavedResources();
    if (user?.user?.program) {
      fetchCourses();
    }
  }, [user?.user?.program]);

  const renderSkeletons = () =>
    Array.from({ length: 6 }).map((_, idx) => (
      <MaterialCardSkeleton key={idx} />
    ));

  return (
    <div className="min-h-screen bg-gray-50 px-4 md:px-8 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-6">
          Saved Resources
        </h1>

        <TabGroup>
          <TabList className="flex gap-4">
            <Tab 
            className="rounded-full py-1 px-3 text-sm/6 font-semibold text-gray-800 focus:outline-none data-[selected]:bg-blue-600/10 data-[selected]:text-blue-600 data-[hover]:bg-blue-600/5 data-[selected]:data-[hover]:bg-blue-600/10"
            >Slides</Tab>
            <Tab
            className="rounded-full py-1 px-3 text-sm/6 font-semibold text-gray-800 focus:outline-none data-[selected]:bg-blue-600/10 data-[selected]:text-blue-600 data-[hover]:bg-blue-600/5 data-[selected]:data-[hover]:bg-blue-600/10"
            >Past Questions</Tab>
            <Tab
            className="rounded-full py-1 px-3 text-sm/6 font-semibold text-gray-800 focus:outline-none data-[selected]:bg-blue-600/10 data-[selected]:text-blue-600 data-[hover]:bg-blue-600/5 data-[selected]:data-[hover]:bg-blue-600/10"
            >Tutorials</Tab>
          </TabList>

          <TabPanels>
          {/* Slides Tab */}
          <TabPanel className="mt-3">
            {isLoading && savedResources?
            (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.slides?.map((slide) => (
                  <MaterialCard
                    key={slide.id}
                    resource={slide}
                    type="slides"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )
            :isLoading ? (
              <div className="grid md:grid-cols-2 gap-4">
              {renderSkeletons()}
              </div>
            ) : savedResources?.slides?.length === 0 || !savedResources?.slides ? (
              <p className="text-gray-600 text-center mt-16 text-2xl font-bold">No saved slides yet.</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.slides?.map((slide) => (
                  <MaterialCard
                    key={slide.id}
                    resource={slide}
                    type="slides"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )}
          </TabPanel>

          {/* Past Questions Tab */}
          <TabPanel className="mt-3">
            {isLoading && savedResources?
            (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.past_questions?.map((question) => (
                  <MaterialCard
                    key={question.id}
                    resource={question}
                    type="past_questions"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )
            : isLoading ? (
              <div className="grid md:grid-cols-2 gap-4">
              {renderSkeletons()}
              </div>
            ) : savedResources?.past_questions?.length === 0 || !savedResources?.past_questions ? (
              <p className="text-gray-600 text-center mt-16 text-2xl font-bold">No saved past questions yet.</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.past_questions?.map((question) => (
                  <MaterialCard
                    key={question.id}
                    resource={question}
                    type="past_questions"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )}
          </TabPanel>

          {/* Tutorials Tab */}
          <TabPanel className="mt-3">
            {isLoading && savedResources ?
            (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.online_tutorial_tips?.map((tutorial) => (
                  <MaterialCard
                    key={tutorial.id}
                    resource={tutorial}
                    type="tutorials"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )
            : isLoading ? (
              <div className="grid md:grid-cols-2 gap-4">
              {renderSkeletons()}
              </div>
            ) : savedResources?.online_tutorial_tips?.length === 0 ||!savedResources?.online_tutorial_tips ? (
              <p className="text-gray-600 text-center mt-16 text-2xl font-bold">No saved tutorials yet.</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {savedResources?.online_tutorial_tips?.map((tutorial) => (
                  <MaterialCard
                    key={tutorial.id}
                    resource={tutorial}
                    type="tutorials"
                    saved={true}
                    showCourse
                    refetch={fetchSavedResources}
                  />
                ))}
              </div>
            )}
          </TabPanel>
          </TabPanels>
        </TabGroup>
      </div>
    </div>
  );
}
