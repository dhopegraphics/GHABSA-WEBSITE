import { createContext, useContext, useState } from "react";

const ExamsContext = createContext();

export const ExamsProvider = ({ children }) => {
  const [exams, setExams] = useState([]);

  return (
    <ExamsContext.Provider value={{ exams, setExams }}>
      {children}
    </ExamsContext.Provider>
  );
};

export const useExams = () => useContext(ExamsContext);
