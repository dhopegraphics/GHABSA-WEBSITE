/**
 * Donation Service
 * API functions for the public donation system
 */
import axios from "axios";
import { BACKEND_HOST } from "../utils/config";

const DONATION_BASE_URL = `${BACKEND_HOST}/donations`;

/**
 * Create an axios instance for public (unauthenticated) requests
 */
const publicAxios = axios.create({
  baseURL: DONATION_BASE_URL,
});

/**
 * Get auth token from localStorage if user is logged in
 * @returns {string|null} Auth token or null
 */
const getAuthToken = () => {
  try {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      return userData?.access || null;
    }
  } catch (e) {
    console.error("Error getting auth token:", e);
  }
  return null;
};

/**
 * Create axios config with optional auth header
 * @returns {Object} Axios config object
 */
const getAuthConfig = () => {
  const token = getAuthToken();
  if (token) {
    return {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };
  }
  return {};
};

/**
 * Get public donation data (stats, recent donations, withdrawals, top donors)
 * @returns {Promise<Object>} Public donation data
 */
export const getPublicDonationData = async () => {
  try {
    const response = await publicAxios.get("/public/");
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error fetching public donation data:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch donation data",
    };
  }
};

/**
 * Initialize a donation payment
 * @param {Object} donationData - Donation details
 * @param {number} donationData.amount - Amount in GHS
 * @param {string} donationData.email - Donor's email
 * @param {string} [donationData.donor_name] - Donor's name (optional)
 * @param {string} [donationData.phone] - Donor's phone (optional)
 * @param {string} [donationData.message] - Donation message (optional)
 * @param {boolean} [donationData.is_anonymous] - Hide donor identity (default: false)
 * @param {boolean} [donationData.show_amount] - Show amount publicly (default: true)
 * @param {string} [donationData.callback_url] - URL to redirect after payment
 * @returns {Promise<Object>} Payment initialization result
 */
export const initializeDonation = async (donationData) => {
  try {
    // Include auth token if user is logged in - this links the donation to their account
    const config = getAuthConfig();
    const response = await publicAxios.post(
      "/initialize/",
      donationData,
      config
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error initializing donation:", error);
    return {
      success: false,
      error:
        error.response?.data?.error ||
        error.response?.data?.errors ||
        "Failed to initialize donation",
    };
  }
};

/**
 * Verify a donation payment
 * @param {string} reference - Donation reference
 * @returns {Promise<Object>} Verification result
 */
export const verifyDonation = async (reference) => {
  try {
    // Include auth token if available for consistency
    const config = getAuthConfig();
    const response = await publicAxios.get(`/verify/${reference}/`, config);
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error verifying donation:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to verify donation",
    };
  }
};

/**
 * Get user's own donations (requires authentication)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @returns {Promise<Object>} User's donations
 */
export const getMyDonations = async (axiosInstance) => {
  try {
    const response = await axiosInstance.get(
      `${DONATION_BASE_URL}/donations/my_donations/`
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error fetching user donations:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch your donations",
    };
  }
};

/**
 * Get user's donor profile (requires authentication)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @returns {Promise<Object>} User's donor profile
 */
export const getMyDonorProfile = async (axiosInstance) => {
  try {
    const response = await axiosInstance.get(
      `${DONATION_BASE_URL}/donations/my_profile/`
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error fetching donor profile:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch donor profile",
    };
  }
};

/**
 * Create a withdrawal (admin only)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @param {Object} withdrawalData - Withdrawal details
 * @returns {Promise<Object>} Withdrawal result
 */
export const createWithdrawal = async (axiosInstance, withdrawalData) => {
  try {
    const response = await axiosInstance.post(
      `${DONATION_BASE_URL}/withdrawals/`,
      withdrawalData
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error creating withdrawal:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to create withdrawal",
    };
  }
};

/**
 * Upload receipt for a withdrawal (admin only)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @param {string} withdrawalId - Withdrawal ID
 * @param {File} receiptFile - Receipt file
 * @returns {Promise<Object>} Upload result
 */
export const uploadWithdrawalReceipt = async (
  axiosInstance,
  withdrawalId,
  receiptFile
) => {
  try {
    const formData = new FormData();
    formData.append("receipt_image", receiptFile);

    const response = await axiosInstance.post(
      `${DONATION_BASE_URL}/withdrawals/${withdrawalId}/upload_receipt/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error uploading receipt:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to upload receipt",
    };
  }
};

/**
 * Get admin donation statistics (admin only)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @returns {Promise<Object>} Admin statistics
 */
export const getAdminDonationStats = async (axiosInstance) => {
  try {
    const response = await axiosInstance.get(
      `${DONATION_BASE_URL}/admin/stats/`
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error fetching admin stats:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch admin statistics",
    };
  }
};

/**
 * Get all transactions (admin only)
 * @param {Object} axiosInstance - Axios instance with auth headers
 * @returns {Promise<Object>} All transactions
 */
export const getAllTransactions = async (axiosInstance) => {
  try {
    const response = await axiosInstance.get(
      `${DONATION_BASE_URL}/transactions/`
    );
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch transactions",
    };
  }
};

export default {
  getPublicDonationData,
  initializeDonation,
  verifyDonation,
  getMyDonations,
  getMyDonorProfile,
  createWithdrawal,
  uploadWithdrawalReceipt,
  getAdminDonationStats,
  getAllTransactions,
};
