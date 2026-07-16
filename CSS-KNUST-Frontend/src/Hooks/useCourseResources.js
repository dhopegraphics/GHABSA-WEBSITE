import { useState, useEffect } from "react";
import { getData } from "../utils/apiHandler";

/**
 * Custom hook to fetch detailed course resources
 * Fetches slides, past questions, and online tutorial tips for courses
 */
export function useCourseResources(courses) {
  const [enrichedCourses, setEnrichedCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!courses || courses.length === 0) {
      setLoading(false);
      return;
    }

    const fetchAllResources = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch resources for all courses in parallel
        const resourcePromises = courses.map(async (course) => {
          try {
            const { response, error } = await getData(
              `/academics/courses/${course.course_id}/`
            );

            if (error) {
              console.warn(
                `Failed to fetch resources for ${course.course_code}:`,
                error
              );
              // Return course without resources if fetch fails
              return {
                ...course,
                slides: [],
                past_questions: [],
                online_tutorial_tips: [],
              };
            }

            // Merge course data with fetched resources
            return {
              ...course,
              slides: response.slides || [],
              past_questions: response.past_questions || [],
              online_tutorial_tips: response.online_tutorial_tips || [],
            };
          } catch (err) {
            console.warn(
              `Error fetching resources for ${course.course_code}:`,
              err
            );
            return {
              ...course,
              slides: [],
              past_questions: [],
              online_tutorial_tips: [],
            };
          }
        });

        const coursesWithResources = await Promise.all(resourcePromises);
        setEnrichedCourses(coursesWithResources);
      } catch (err) {
        console.error("Error fetching course resources:", err);
        setError(err.message);
        // Set courses without resources on error
        setEnrichedCourses(
          courses.map((course) => ({
            ...course,
            slides: [],
            past_questions: [],
            online_tutorial_tips: [],
          }))
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAllResources();
  }, [courses]);

  return { enrichedCourses, loading, error };
}
