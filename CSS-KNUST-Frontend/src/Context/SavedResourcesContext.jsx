import { createContext, useContext, useState } from "react";

const SavedResourcesContext = createContext();

export const SavedResourcesProvider = ({ children }) => {
  const [savedResources, setSavedResources] = useState();

  return (
    <SavedResourcesContext.Provider value={{ savedResources, setSavedResources }}>
      {children}
    </SavedResourcesContext.Provider>
  );
};

export const useSavedResources = () => useContext(SavedResourcesContext);
