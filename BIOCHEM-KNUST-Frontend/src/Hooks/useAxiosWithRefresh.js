import axios from "axios";
import { useContext } from "react";
import { UserContext } from "../Context/UserContext";
import useRefreshToken from "./useRefreshToken";
import { BACKEND_HOST } from "../utils/config";

const useAxiosWithRefresh = () => {
  const { user, updateAccessToken, logout } = useContext(UserContext);
  const refreshAccessToken = useRefreshToken();

  const axiosInstance = axios.create({
    baseURL: BACKEND_HOST,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  axiosInstance.interceptors.request.use(
    async (config) => {
      if (user?.access) {
        config.headers.Authorization = `Bearer ${user?.access}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        user?.refresh
      ) {
        originalRequest._retry = true;

        const newAccessToken = await refreshAccessToken();

        if (newAccessToken) {
          updateAccessToken(newAccessToken);

          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return axiosInstance(originalRequest);
        } else {
          logout();
        }
      }

      return Promise.reject(error);
    }
  );

  return axiosInstance;
};

export default useAxiosWithRefresh;
