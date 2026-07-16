import { createContext, useContext, useState } from "react";

const SavedBlogsContext = createContext();

export const SavedBlogsProvider = ({ children }) => {
  const [savedBlogs, setSavedBlogs] = useState();

  return (
    <SavedBlogsContext.Provider value={{ savedBlogs, setSavedBlogs }}>
      {children}
    </SavedBlogsContext.Provider>
  );
};

export const useSavedBlogs = () => useContext(SavedBlogsContext);
