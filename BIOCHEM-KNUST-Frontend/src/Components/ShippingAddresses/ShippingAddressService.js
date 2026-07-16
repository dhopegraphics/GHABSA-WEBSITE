/**
 * Shipping Address Service
 * API calls for managing user shipping addresses
 * Functions accept axiosInstance from useAxiosWithRefresh hook
 */

import { BACKEND_HOST } from "../../utils/config";

const ENDPOINTS = {
  LIST: `${BACKEND_HOST}/accounts/shipping-addresses/`,
  CREATE: `${BACKEND_HOST}/accounts/shipping-addresses/`,
  DETAIL: (id) => `${BACKEND_HOST}/accounts/shipping-addresses/${id}/`,
  SET_DEFAULT: (id) => `${BACKEND_HOST}/accounts/shipping-addresses/${id}/set_default/`,
  DEFAULT: `${BACKEND_HOST}/accounts/shipping-addresses/default/`,
  MINIMAL: `${BACKEND_HOST}/accounts/shipping-addresses/minimal/`,
};

/**
 * Get all shipping addresses for the current user
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 */
export const getShippingAddresses = async (axiosInstance) => {
  const response = await axiosInstance.get(ENDPOINTS.LIST);
  return response;
};

/**
 * Get minimal list of addresses (for dropdowns)
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 */
export const getShippingAddressesMinimal = async (axiosInstance) => {
  const response = await axiosInstance.get(ENDPOINTS.MINIMAL);
  return response;
};

/**
 * Get a single shipping address by ID
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {string} id - Address UUID
 */
export const getShippingAddress = async (axiosInstance, id) => {
  const response = await axiosInstance.get(ENDPOINTS.DETAIL(id));
  return response;
};

/**
 * Get the default shipping address
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 */
export const getDefaultShippingAddress = async (axiosInstance) => {
  try {
    const response = await axiosInstance.get(ENDPOINTS.DEFAULT);
    return response;
  } catch (error) {
    if (error.response?.status === 404) {
      return { data: null };
    }
    throw error;
  }
};

/**
 * Create a new shipping address
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {Object} addressData - Address data
 */
export const createShippingAddress = async (axiosInstance, addressData) => {
  const response = await axiosInstance.post(ENDPOINTS.CREATE, addressData);
  return response;
};

/**
 * Update an existing shipping address
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {string} id - Address UUID
 * @param {Object} addressData - Updated address data
 */
export const updateShippingAddress = async (axiosInstance, id, addressData) => {
  const response = await axiosInstance.put(ENDPOINTS.DETAIL(id), addressData);
  return response;
};

/**
 * Partially update a shipping address
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {string} id - Address UUID
 * @param {Object} addressData - Partial address data
 */
export const patchShippingAddress = async (axiosInstance, id, addressData) => {
  const response = await axiosInstance.patch(ENDPOINTS.DETAIL(id), addressData);
  return response;
};

/**
 * Delete a shipping address
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {string} id - Address UUID
 */
export const deleteShippingAddress = async (axiosInstance, id) => {
  const response = await axiosInstance.delete(ENDPOINTS.DETAIL(id));
  return response;
};

/**
 * Set an address as the default
 * @param {Object} axiosInstance - Axios instance from useAxiosWithRefresh
 * @param {string} id - Address UUID
 */
export const setDefaultShippingAddress = async (axiosInstance, id) => {
  const response = await axiosInstance.post(ENDPOINTS.SET_DEFAULT(id));
  return response;
};

const ShippingAddressService = {
  getShippingAddresses,
  getShippingAddressesMinimal,
  getShippingAddress,
  getDefaultShippingAddress,
  createShippingAddress,
  updateShippingAddress,
  patchShippingAddress,
  deleteShippingAddress,
  setDefaultShippingAddress,
};

export default ShippingAddressService;
