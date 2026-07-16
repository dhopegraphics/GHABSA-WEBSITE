import { createContext, useContext, useState } from "react";
import { normalizeCourses } from "../utils/courseSchema";

const CoursesContext = createContext();

export const CoursesProvider = ({ children }) => {
  const [courses, setCourseState] = useState([]);
  const setCourses = (newCourses) => setCourseState(normalizeCourses(newCourses));

  return (
    <CoursesContext.Provider value={{ 
      courses, 
      setCourses, 
    }}>
      {children}
    </CoursesContext.Provider>
  );
};

export const useCourses = () => useContext(CoursesContext);
