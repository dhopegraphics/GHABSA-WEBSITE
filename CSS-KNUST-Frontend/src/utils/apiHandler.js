import axios from 'axios';
import { BACKEND_HOST } from './config';

const api = axios.create({
  baseURL: BACKEND_HOST,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getData = async (endpoint) => {
  let response = null;
  let error = null;
  let loading = true;

  try {
    const res = await api.get(endpoint);
    response = res.data;
  } catch (err) {
    error = err.response ? err.response.data : err.message;
  } finally {
    loading = false;
  }

  return { response, error, loading };
};

export const postData = async (endpoint, payload) => {
  let response = null;
  let error = null;
  let loading = true;

  try {
    const res = await api.post(endpoint, payload);
    response = res.data;
  } catch (err) {
    error = err.response ? err.response.data : err.message;
  } finally {
    loading = false;
  }

  return { response, error, loading };
};
