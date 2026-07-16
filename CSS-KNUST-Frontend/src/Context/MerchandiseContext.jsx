import { createContext, useContext, useState } from "react";

const MerchandiseContext = createContext();

export const MerchandiseProvider = ({ children }) => {
  const [merchandise, setMerchandise] = useState([]);

  return (
    <MerchandiseContext.Provider value={{ merchandise, setMerchandise }}>
      {children}
    </MerchandiseContext.Provider>
  );
};

export const useMerchandise = () => useContext(MerchandiseContext);
