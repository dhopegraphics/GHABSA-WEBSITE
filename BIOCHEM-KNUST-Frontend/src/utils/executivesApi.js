import axios from "axios";
import { BACKEND_HOST } from "./config";

// Current Administration (Executives + Committees)
export const getCurrentAdministration = async () => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/executives/current-administration/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Executives
export const getCurrentExecutives = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/executives/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getPastExecutives = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/executives/past/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getExecutivesByYear = async (year) => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/executives/year/${year}/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getAvailableYears = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/executives/years/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Committees
export const getCommittees = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/executives/committees/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getCommitteeDetail = async (committeeId) => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/executives/committees/${committeeId}/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Appointees
export const getAppointees = async () => {
  return getAppointeesByParams();
};

export const getAppointeesByParams = async (
  year = null,
  includeInactive = false
) => {
  try {
    let url = `${BACKEND_HOST}/executives/appointees/`;
    const params = [];
    if (year) params.push(`year=${encodeURIComponent(year)}`);
    if (includeInactive) params.push(`include_inactive=1`);
    if (params.length) url = `${url}?${params.join("&")}`;

    const response = await axios.get(url);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getAppointeesByCommittee = async (committeeId) => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/executives/appointees/committee/${committeeId}/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Society History
export const getSocietyHistory = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/history/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getHistoryDetail = async (historyId) => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/history/${historyId}/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getHistoryByCategory = async (category) => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/history/category/${category}/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getHistoryByYear = async (year) => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/history/year/${year}/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getHistoryCategories = async () => {
  try {
    const response = await axios.get(
      `${BACKEND_HOST}/history/meta/categories/`
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getHistoryYears = async () => {
  try {
    const response = await axios.get(`${BACKEND_HOST}/history/meta/years/`);
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};
