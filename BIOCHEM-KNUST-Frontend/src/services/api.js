/**
 * General API Service
 * Axios instance configured for backend API calls
 */
import axios from "axios";
import { BACKEND_HOST, API_BASE_URL } from "../utils/config";

/**
 * Create an axios instance for API requests
 */
const api = axios.create({
  baseURL: BACKEND_HOST || API_BASE_URL,
});

/**
 * Get user data from localStorage
 * @returns {Object|null} User data or null
 */
const getUserData = () => {
  try {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      return JSON.parse(storedUser);
    }
  } catch (e) {
    console.error("Error getting user data:", e);
  }
  return null;
};

/**
 * Update access token in localStorage
 * @param {string} newToken - New access token
 */
const updateStoredAccessToken = (newToken) => {
  try {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      userData.access = newToken;
      localStorage.setItem("user", JSON.stringify(userData));
    }
  } catch (e) {
    console.error("Error updating token:", e);
  }
};

/**
 * Refresh the access token using refresh token
 * @returns {Promise<string|null>} New access token or null
 */
const refreshAccessToken = async () => {
  const userData = getUserData();
  if (!userData?.refresh) return null;

  try {
    const response = await axios.post(`${BACKEND_HOST || API_BASE_URL}/accounts/token/refresh/`, {
      refresh: userData.refresh,
    });
    return response.data.access;
  } catch (error) {
    console.error("Token refresh failed:", error);
    // Clear invalid user data
    localStorage.removeItem("user");
    return null;
  }
};

/**
 * Request interceptor to add auth token to headers
 */
api.interceptors.request.use(
  (config) => {
    const userData = getUserData();
    if (userData?.access) {
      config.headers.Authorization = `Bearer ${userData.access}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling and token refresh
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, try refreshing the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const newAccessToken = await refreshAccessToken();

      if (newAccessToken) {
        // Update stored token
        updateStoredAccessToken(newAccessToken);
        
        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } else {
        // Token refresh failed - redirect to login or clear state
        console.error("Session expired - please log in again");
        // Optionally trigger a logout event
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
    }

    return Promise.reject(error);
  }
);

export default api;
