import { useContext } from 'react';
import axios from 'axios';
import { BACKEND_HOST } from '../utils/config';
import { UserContext } from '../Context/UserContext';

const useRefreshToken = () => {
  const { user} = useContext(UserContext);

  const refreshAccessToken = async () => {
    try {
      const response = await axios.post(`${BACKEND_HOST}/accounts/refresh-token/`, {
        refresh: user?.refresh,
      });

      const newAccessToken = response.data?.access;

      return newAccessToken;
    } catch (error) {
      console.error('Failed to refresh access token:', error);
      return null;
    }
  };

  return refreshAccessToken;
};

export default useRefreshToken;
