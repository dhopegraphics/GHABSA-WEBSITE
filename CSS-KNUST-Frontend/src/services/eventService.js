/**
 * Event Service
 * API service for event-related operations including registration and payments
 */
import api from "./api";
import { BACKEND_HOST } from "../utils/config";

const BASE_URL = `${BACKEND_HOST}/events`;

/**
 * Get all events with optional filters
 * @param {Object} params - Query parameters (filter, type, search)
 * @returns {Promise} API response
 */
export const getEvents = async (params = {}) => {
  try {
    const response = await api.get(`${BASE_URL}/`, { params });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get event details by ID
 * @param {string} eventId - Event UUID
 * @returns {Promise} API response
 */
export const getEventById = async (eventId) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get user's RSVP status for an event
 * @param {string} eventId - Event UUID
 * @returns {Promise} API response
 */
export const getMyRSVP = async (eventId) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/rsvp/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Create or update RSVP for an event
 * @param {string} eventId - Event UUID
 * @param {Object} data - RSVP data { status, reminder, notes }
 * @returns {Promise} API response
 */
export const updateRSVP = async (eventId, data) => {
  try {
    const response = await api.post(`${BASE_URL}/${eventId}/rsvp/`, data);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get event attendees
 * @param {string} eventId - Event UUID
 * @param {string} status - Optional status filter (attending, maybe, not_attending)
 * @returns {Promise} API response
 */
export const getEventAttendees = async (eventId, status = null) => {
  try {
    const params = status ? { status } : {};
    const response = await api.get(`${BASE_URL}/${eventId}/attendees/`, { params });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

// ========== REGISTRATION ==========

/**
 * Register for an event
 * @param {string} eventId - Event UUID
 * @param {Object} data - Registration data
 * @returns {Promise} API response
 */
export const registerForEvent = async (eventId, data) => {
  try {
    const response = await api.post(`${BASE_URL}/${eventId}/register/`, data);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get user's registration for an event
 * @param {string} eventId - Event UUID
 * @returns {Promise} API response - returns null response if no registration found (404)
 */
export const getMyRegistration = async (eventId) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/my-registration/`);
    return { response: response.data, error: null };
  } catch (error) {
    // 404 means no registration found - this is expected, not an error
    if (error.response?.status === 404) {
      return { response: null, error: null };
    }
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get all registrations for an event (admin)
 * @param {string} eventId - Event UUID
 * @param {Object} params - Query parameters (status)
 * @returns {Promise} API response
 */
export const getEventRegistrations = async (eventId, params = {}) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/registrations/`, { params });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

// ========== PAYMENT PACKAGES ==========

/**
 * Get available payment packages for an event
 * @param {string} eventId - Event UUID
 * @returns {Promise} API response
 */
export const getEventPackages = async (eventId) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/packages/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get payment package details
 * @param {string} packageId - Package UUID
 * @returns {Promise} API response
 */
export const getPackageById = async (packageId) => {
  try {
    const response = await api.get(`${BASE_URL}/packages/${packageId}/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

// ========== PAYMENTS ==========

/**
 * Initialize payment for a registration
 * @param {Object} data - Payment data { registration_id, amount, payment_gateway, callback_url }
 * @returns {Promise} API response
 */
export const initializePayment = async (data) => {
  try {
    const response = await api.post(`${BASE_URL}/payments/initialize/`, data);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Verify payment transaction
 * @param {string} reference - Transaction reference
 * @returns {Promise} API response
 */
export const verifyPayment = async (reference) => {
  try {
    const response = await api.post(`${BASE_URL}/payments/verify/`, { reference });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get user's event payment history
 * @returns {Promise} API response
 */
export const getMyPayments = async () => {
  try {
    const response = await api.get(`${BASE_URL}/payments/my-payments/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get payments for a specific registration
 * @param {string} registrationId - Registration UUID
 * @returns {Promise} API response
 */
export const getRegistrationPayments = async (registrationId) => {
  try {
    const response = await api.get(`${BASE_URL}/registrations/${registrationId}/payments/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Request a refund for a transaction
 * @param {Object} data - Refund request data { transaction_id, reason }
 * @returns {Promise} API response
 */
export const requestRefund = async (data) => {
  try {
    const response = await api.post(`${BASE_URL}/payments/refund/`, data);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get user's refund requests
 * @returns {Promise} API response
 */
export const getMyRefunds = async () => {
  try {
    const response = await api.get(`${BASE_URL}/payments/my-refunds/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

// ========== SYNC MEMO (PHOTO GALLERY) ==========

/**
 * Get Sync Memo statistics
 * @returns {Promise} API response
 */
export const getSyncMemoStats = async () => {
  try {
    const response = await api.get(`${BASE_URL}/sync-memo/stats/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get Sync Memo albums
 * @param {string} eventId - Optional event ID to filter
 * @returns {Promise} API response
 */
export const getSyncMemoAlbums = async (eventId = null) => {
  try {
    const params = eventId ? { event_id: eventId } : {};
    const response = await api.get(`${BASE_URL}/sync-memo/albums/`, { params });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get photos for an event album
 * @param {string} eventId - Event UUID
 * @param {Object} params - Query parameters (sort: latest, most_liked, oldest)
 * @returns {Promise} API response
 */
export const getEventPhotos = async (eventId, params = {}) => {
  try {
    const response = await api.get(`${BASE_URL}/${eventId}/sync-memo/photos/`, { params });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Upload photo to event album
 * @param {string} eventId - Event UUID
 * @param {FormData} formData - Photo data (photo file, caption, share_to_feed)
 * @returns {Promise} API response
 */
export const uploadPhoto = async (eventId, formData) => {
  try {
    const response = await api.post(`${BASE_URL}/${eventId}/sync-memo/upload/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Like/unlike a photo
 * @param {string} photoId - Photo UUID
 * @param {string} action - 'like' or 'unlike'
 * @returns {Promise} API response
 */
export const togglePhotoLike = async (photoId, action = "like") => {
  try {
    const response = await api.post(`${BASE_URL}/sync-memo/photos/${photoId}/like/`, { action });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Get comments for a photo
 * @param {string} photoId - Photo UUID
 * @returns {Promise} API response
 */
export const getPhotoComments = async (photoId) => {
  try {
    const response = await api.get(`${BASE_URL}/sync-memo/photos/${photoId}/comments/`);
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

/**
 * Add comment to a photo
 * @param {string} photoId - Photo UUID
 * @param {string} comment - Comment text
 * @returns {Promise} API response
 */
export const addPhotoComment = async (photoId, comment) => {
  try {
    const response = await api.post(`${BASE_URL}/sync-memo/photos/${photoId}/comments/create/`, { comment });
    return { response: response.data, error: null };
  } catch (error) {
    return { response: null, error: error.response?.data || error.message };
  }
};

export default {
  // Events
  getEvents,
  getEventById,
  
  // RSVP
  getMyRSVP,
  updateRSVP,
  getEventAttendees,
  
  // Registration
  registerForEvent,
  getMyRegistration,
  getEventRegistrations,
  
  // Packages
  getEventPackages,
  getPackageById,
  
  // Payments
  initializePayment,
  verifyPayment,
  getMyPayments,
  getRegistrationPayments,
  requestRefund,
  getMyRefunds,
  
  // Sync Memo
  getSyncMemoStats,
  getSyncMemoAlbums,
  getEventPhotos,
  uploadPhoto,
  togglePhotoLike,
  getPhotoComments,
  addPhotoComment,
};
