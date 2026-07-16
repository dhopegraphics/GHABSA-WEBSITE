import { createContext, useContext, useState } from "react";

const InternshipsContext = createContext();

export const InternshipsProvider = ({ children }) => {
  const [internships, setInternships] = useState([]);

  return (
    <InternshipsContext.Provider value={{ internships, setInternships }}>
      {children}
    </InternshipsContext.Provider>
  );
};

export const useInternships = () => useContext(InternshipsContext);
