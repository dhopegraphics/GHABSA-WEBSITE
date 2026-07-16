import { createContext, useContext, useState, useRef } from "react";

const CoursesContext = createContext();

export const CoursesProvider = ({ children }) => {
  const [courses, setCourses] = useState([]);
  // Track which program the courses belong to, to prevent mixing
  const coursesProgram = useRef(null);

  const setCoursesForProgram = (newCourses, program) => {
    coursesProgram.current = program;
    setCourses(newCourses);
  };

  const clearCoursesIfDifferentProgram = (program) => {
    if (coursesProgram.current && coursesProgram.current !== program) {
      setCourses([]);
      coursesProgram.current = null;
    }
  };

  return (
    <CoursesContext.Provider value={{ 
      courses, 
      setCourses, 
      setCoursesForProgram,
      clearCoursesIfDifferentProgram,
      currentProgram: coursesProgram.current
    }}>
      {children}
    </CoursesContext.Provider>
  );
};

export const useCourses = () => useContext(CoursesContext);
