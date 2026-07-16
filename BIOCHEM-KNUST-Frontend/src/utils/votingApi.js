import axios from "axios";
import { BACKEND_HOST } from "./config";

const createAuthHeaders = (token) => ({
  "Content-Type": "application/json",
  ...(token && { Authorization: `Bearer ${token}` }),
});

// Create headers - only add auth if token exists
const getHeaders = (token) => {
  if (token) {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }
  return { "Content-Type": "application/json" };
};

// Get user token from localStorage
const getUserToken = () => {
  const userData = localStorage.getItem("user");
  if (userData) {
    try {
      const parsed = JSON.parse(userData);
      return parsed.access || parsed.token;
    } catch {
      return null;
    }
  }
  return null;
};

// Check if error is a token validation error (any 401 that's not a visibility restriction)
const isTokenError = (error) => {
  // Retry without auth for any 401 error (expired token, invalid token, etc.)
  // This allows public endpoints to work even with a bad token
  return error.response?.status === 401;
};

// Check if error is a visibility/permission error (403)
const isVisibilityError = (error) => {
  return error.response?.status === 403 && 
         (error.response?.data?.visibility || error.response?.data?.requires_login);
};

// Voting Events
export const getVotingEvents = async (filters = {}) => {
  try {
    const token = getUserToken();
    const params = new URLSearchParams();

    if (filters.status) params.append("status", filters.status);
    if (filters.event_type) params.append("event_type", filters.event_type);
    if (filters.search) params.append("search", filters.search);

    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/?${params.toString()}`,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If token is invalid, retry without auth (for public events)
    if (isTokenError(error)) {
      try {
        const params = new URLSearchParams();
        if (filters.status) params.append("status", filters.status);
        if (filters.event_type) params.append("event_type", filters.event_type);
        if (filters.search) params.append("search", filters.search);
        
        const response = await axios.get(
          `${BACKEND_HOST}/voting/events/?${params.toString()}`,
          { headers: { "Content-Type": "application/json" } }
        );
        return { data: response.data, error: null };
      } catch (retryError) {
        return { data: null, error: retryError.response?.data || retryError.message };
      }
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getVotingEventDetail = async (slug) => {
  try {
    const token = getUserToken();
    const response = await axios.get(`${BACKEND_HOST}/voting/events/${slug}/`, {
      headers: getHeaders(token),
    });
    return { data: response.data, error: null };
  } catch (error) {
    // If it's a visibility error, don't retry - return the error info
    if (isVisibilityError(error)) {
      return { 
        data: null, 
        error: error.response?.data,
        requiresLogin: error.response?.data?.requires_login,
        visibility: error.response?.data?.visibility
      };
    }
    // If token is invalid, retry without auth
    if (isTokenError(error)) {
      try {
        const response = await axios.get(`${BACKEND_HOST}/voting/events/${slug}/`, {
          headers: { "Content-Type": "application/json" },
        });
        return { data: response.data, error: null };
      } catch (retryError) {
        // Check if the retry error is a visibility error
        if (isVisibilityError(retryError)) {
          return { 
            data: null, 
            error: retryError.response?.data,
            requiresLogin: retryError.response?.data?.requires_login,
            visibility: retryError.response?.data?.visibility
          };
        }
        return { data: null, error: retryError.response?.data || retryError.message };
      }
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getEventCandidates = async (slug) => {
  try {
    const token = getUserToken();
    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/${slug}/candidates/`,
      { headers: getHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If it's a visibility error, don't retry - return the error info
    if (isVisibilityError(error)) {
      return { 
        data: null, 
        error: error.response?.data,
        requiresLogin: error.response?.data?.requires_login,
        visibility: error.response?.data?.visibility
      };
    }
    // If token is invalid, retry without auth
    if (isTokenError(error)) {
      try {
        const response = await axios.get(
          `${BACKEND_HOST}/voting/events/${slug}/candidates/`,
          { headers: { "Content-Type": "application/json" } }
        );
        return { data: response.data, error: null };
      } catch (retryError) {
        // Check if the retry error is a visibility error
        if (isVisibilityError(retryError)) {
          return { 
            data: null, 
            error: retryError.response?.data,
            requiresLogin: retryError.response?.data?.requires_login,
            visibility: retryError.response?.data?.visibility
          };
        }
        return { data: null, error: retryError.response?.data || retryError.message };
      }
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

/**
 * Get poll options for a poll/referendum event
 * @param {string} slug - Event slug
 * @returns {Promise<{data: Object|null, error: any}>}
 */
export const getEventPollOptions = async (slug) => {
  try {
    const token = getUserToken();
    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/${slug}/poll_options/`,
      { headers: getHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If token is invalid, retry without auth
    if (isTokenError(error)) {
      try {
        const response = await axios.get(
          `${BACKEND_HOST}/voting/events/${slug}/poll_options/`,
          { headers: { "Content-Type": "application/json" } }
        );
        return { data: response.data, error: null };
      } catch (retryError) {
        return { data: null, error: retryError.response?.data || retryError.message };
      }
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getMyEligibility = async (slug) => {
  try {
    const token = getUserToken();
    // This endpoint requires authentication - skip if no token
    if (!token) {
      return { data: null, error: null };
    }
    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/${slug}/my_eligibility/`,
      { headers: getHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getEventResults = async (slug) => {
  try {
    const token = getUserToken();
    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/${slug}/results/`,
      { headers: getHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If token is invalid, retry without auth (results are public)
    if (isTokenError(error)) {
      try {
        const response = await axios.get(
          `${BACKEND_HOST}/voting/events/${slug}/results/`,
          { headers: { "Content-Type": "application/json" } }
        );
        return { data: response.data, error: null };
      } catch (retryError) {
        return { data: null, error: retryError.response?.data || retryError.message };
      }
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getEventStatistics = async (slug) => {
  try {
    const token = getUserToken();
    const response = await axios.get(
      `${BACKEND_HOST}/voting/events/${slug}/statistics/`,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Voting
export const castVote = async (voteData, forceAnonymous = false) => {
  try {
    // Don't use token if forceAnonymous is true
    const token = forceAnonymous ? null : getUserToken();
    // For anonymous voting, don't send Authorization header at all
    const headers = token 
      ? createAuthHeaders(token)
      : { "Content-Type": "application/json" };
    
  
    const response = await axios.post(
      `${BACKEND_HOST}/voting/votes/`,
      voteData,
      { headers }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If we got a token error and haven't tried anonymous yet, retry without token
    if (isTokenError(error) && !forceAnonymous) {
      console.log("🔄 Token invalid, retrying as anonymous...");
      return castVote(voteData, true);
    }
    console.error("❌ castVote error response:", error.response?.data);
    return { data: null, error: error.response?.data || error.message };
  }
};

/**
 * Check if a user (anonymous OR authenticated) has already voted in an event
 * Uses device fingerprint, IP address, and user account for comprehensive detection
 * This is a ROBUST check that catches cross-device/login-status vote attempts
 */
export const checkVoteStatus = async (eventSlug, deviceFingerprint, sessionId) => {
  try {
    // Include token if available - backend will check user account too
    const token = getUserToken();
    const headers = token 
      ? createAuthHeaders(token)
      : { "Content-Type": "application/json" };
    
    const response = await axios.post(
      `${BACKEND_HOST}/voting/votes/check_anonymous_vote/`,
      {
        event_slug: eventSlug,
        device_fingerprint: deviceFingerprint,
        session_id: sessionId
      },
      { headers }
    );
    return { data: response.data, error: null };
  } catch (error) {
    console.error("❌ checkVoteStatus error:", error.response?.data);
    return { data: null, error: error.response?.data || error.message };
  }
};

// Keep old function for backwards compatibility
export const checkAnonymousVoteStatus = checkVoteStatus;

/**
 * Batch check vote status for multiple events at once
 * Called when VotingPage loads to pre-check all visible events
 * Returns a map of event slugs to their vote status
 */
export const batchCheckVoteStatus = async (eventSlugs = [], deviceFingerprint, sessionId) => {
  try {
    // Include token if available - backend will check user account too
    const token = getUserToken();
    const headers = token 
      ? createAuthHeaders(token)
      : { "Content-Type": "application/json" };
    
    const response = await axios.post(
      `${BACKEND_HOST}/voting/votes/batch_check_vote_status/`,
      {
        event_slugs: eventSlugs,
        device_fingerprint: deviceFingerprint,
        session_id: sessionId
      },
      { headers }
    );
    return { data: response.data, error: null };
  } catch (error) {
    console.error("❌ batchCheckVoteStatus error:", error.response?.data);
    return { data: null, error: error.response?.data || error.message };
  }
};

export const castBulkVote = async (votes, forceAnonymous = false) => {
  try {
    // Don't use token if forceAnonymous is true
    const token = forceAnonymous ? null : getUserToken();
    // For anonymous voting, don't send Authorization header at all
    const headers = token 
      ? createAuthHeaders(token)
      : { "Content-Type": "application/json" };
    
    const response = await axios.post(
      `${BACKEND_HOST}/voting/votes/bulk_vote/`,
      { votes },
      { headers }
    );
    return { data: response.data, error: null };
  } catch (error) {
    // If we got a token error and haven't tried anonymous yet, retry without token
    if (isTokenError(error) && !forceAnonymous) {
      console.log("🔄 Token invalid, retrying bulk vote as anonymous...");
      return castBulkVote(votes, true);
    }
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getMyVotes = async () => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    const response = await axios.get(`${BACKEND_HOST}/voting/votes/my_votes/`, {
      headers: createAuthHeaders(token),
    });
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Candidates
export const getCandidates = async (filters = {}) => {
  try {
    const token = getUserToken();
    const params = new URLSearchParams();

    if (filters.event) params.append("event", filters.event);
    if (filters.category) params.append("category", filters.category);
    if (filters.program) params.append("program", filters.program);
    if (filters.year) params.append("year", filters.year);

    const response = await axios.get(
      `${BACKEND_HOST}/voting/candidates/?${params.toString()}`,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const registerAsCandidate = async (candidateData, profileImageFile = null) => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    let requestData;
    let headers = createAuthHeaders(token);

    // If there's a file, use FormData
    if (profileImageFile) {
      requestData = new FormData();
      
      // Append all candidate data fields
      Object.keys(candidateData).forEach(key => {
        if (candidateData[key] !== undefined && candidateData[key] !== null && candidateData[key] !== "") {
          requestData.append(key, candidateData[key]);
        }
      });
      
      // Append the image file
      requestData.append("profile_image", profileImageFile);
      
      // For FormData, let axios set the content-type with boundary
      headers = {
        ...headers,
        "Content-Type": "multipart/form-data",
      };
    } else {
      // No file, use regular JSON
      requestData = candidateData;
    }

    const response = await axios.post(
      `${BACKEND_HOST}/voting/candidates/register/`,
      requestData,
      { headers }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getMyCandidacies = async () => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    const response = await axios.get(
      `${BACKEND_HOST}/voting/candidates/my_candidacies/`,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

// Payment (Universal Payment System)
export const initializePayment = async (paymentData) => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    const response = await axios.post(
      `${BACKEND_HOST}/voting/payments/initialize/`,
      paymentData,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const verifyPayment = async (reference) => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    const response = await axios.post(
      `${BACKEND_HOST}/voting/payments/verify/`,
      { reference },
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};

export const getPaymentStatus = async (reference) => {
  try {
    const token = getUserToken();
    if (!token) {
      return { data: null, error: "Authentication required" };
    }

    const response = await axios.get(
      `${BACKEND_HOST}/voting/payments/${reference}/status/`,
      { headers: createAuthHeaders(token) }
    );
    return { data: response.data, error: null };
  } catch (error) {
    return { data: null, error: error.response?.data || error.message };
  }
};
