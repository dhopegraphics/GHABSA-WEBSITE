import { createContext, useContext, useState, useCallback } from "react";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

const ElMercadoContext = createContext();

export const useElMercado = () => {
  const context = useContext(ElMercadoContext);
  if (!context) {
    throw new Error("useElMercado must be used within an ElMercadoProvider");
  }
  return context;
};

export const ElMercadoProvider = ({ children }) => {
  const axiosInstance = useAxiosWithRefresh();

  // State
  const [categories, setCategories] = useState([]);
  const [sellers, setSellers] = useState([]);
  const [listings, setListings] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ============================================================================
  // CATEGORIES
  // ============================================================================

  // Fetch marketplace categories (flat list)
  const fetchCategories = useCallback(async () => {
    setLoading(true);
    try {
      // First try to get hierarchical structure from root endpoint
      const response = await axiosInstance.get("/marketplace/categories/root/");
      const data = response.data?.results || response.data;
      setCategories(Array.isArray(data) ? data : []);
      setError(null);
      return data;
    } catch (err) {
      // Fallback to flat list
      try {
        const flatResponse = await axiosInstance.get("/marketplace/categories/");
        const flatData = flatResponse.data?.results || flatResponse.data;
        setCategories(Array.isArray(flatData) ? flatData : []);
        return flatData;
      } catch (fallbackErr) {
        setError(fallbackErr.response?.data?.message || "Failed to fetch categories");
        return [];
      }
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Fetch all categories (flat list)
  const fetchAllCategories = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/categories/");
      const data = response.data?.results || response.data;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Failed to fetch all categories:", err);
      return [];
    }
  }, [axiosInstance]);

  // Fetch root categories only (hierarchical with children)
  const fetchRootCategories = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/categories/root/");
      const data = response.data?.results || response.data;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Failed to fetch root categories:", err);
      return [];
    }
  }, [axiosInstance]);

  // ============================================================================
  // SELLER APPLICATIONS
  // ============================================================================

  // Helper function to format phone number to international format
  const formatPhoneNumber = (phone) => {
    if (!phone) return phone;
    
    // Remove all non-digit characters except +
    let cleaned = phone.replace(/[^\d+]/g, '');
    
    // If it starts with 0, assume Ghana and replace with +233
    if (cleaned.startsWith('0')) {
      cleaned = '+233' + cleaned.substring(1);
    }
    // If it doesn't start with +, assume Ghana
    else if (!cleaned.startsWith('+')) {
      // If it starts with 233, add +
      if (cleaned.startsWith('233')) {
        cleaned = '+' + cleaned;
      } else {
        // Assume it's a local number, add +233
        cleaned = '+233' + cleaned;
      }
    }
    
    return cleaned;
  };

  // Submit seller application
  const submitSellerApplication = useCallback(
    async (formData) => {
      setLoading(true);
      try {
        // Create FormData for file uploads
        const data = new FormData();
        
        // Append all fields
        Object.keys(formData).forEach((key) => {
          let value = formData[key];
          
          // Format phone number
          if (key === 'applicant_phone' && value) {
            value = formatPhoneNumber(value);
          }
          
          // Handle arrays (like categories_of_interest)
          if (Array.isArray(value)) {
            // Send as proper JSON array string
            data.append(key, JSON.stringify(value));
          }
          // Handle files
          else if (value instanceof File) {
            data.append(key, value);
          }
          // Handle other values (skip null/undefined)
          else if (value !== null && value !== undefined && value !== '') {
            data.append(key, value);
          }
        });

        const response = await axiosInstance.post(
          "/marketplace/seller-applications/",
          data,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMessage =
          err.response?.data?.message ||
          err.response?.data?.detail ||
          Object.values(err.response?.data || {}).flat().join(", ") ||
          "Failed to submit application";
        setError(errorMessage);
        return { success: false, error: errorMessage, errors: err.response?.data };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Fetch user's seller applications
  const fetchMyApplications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get("/marketplace/seller-applications/");
      const data = response.data?.results || response.data;
      setMyApplications(Array.isArray(data) ? data : []);
      setError(null);
      return data;
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch applications");
      return [];
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Get application status
  const getApplicationStatus = useCallback(
    async (applicationId) => {
      try {
        const response = await axiosInstance.get(
          `/marketplace/seller-applications/${applicationId}/`
        );
        return response.data;
      } catch (err) {
        console.error("Failed to get application status:", err);
        return null;
      }
    },
    [axiosInstance]
  );

  // Check application status by tracking code (public - no auth required)
  const checkApplicationByTrackingCode = useCallback(
    async (trackingCode) => {
      setLoading(true);
      try {
        const response = await axiosInstance.get(
          `/marketplace/seller-applications/check-status/?tracking_code=${trackingCode}`
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMessage =
          err.response?.data?.error ||
          err.response?.data?.message ||
          "Failed to find application";
        setError(errorMessage);
        return { success: false, error: errorMessage };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Update seller application (for editing before approval)
  const updateSellerApplication = useCallback(
    async (applicationId, formData) => {
      setLoading(true);
      try {
        // Create FormData for file uploads
        const data = new FormData();
        
        // Append all fields
        Object.keys(formData).forEach((key) => {
          let value = formData[key];
          
          // Format phone number
          if (key === 'applicant_phone' && value) {
            value = formatPhoneNumber(value);
          }
          
          // Handle arrays (like categories_of_interest)
          if (Array.isArray(value)) {
            // Send as proper JSON array string - always stringify arrays
            data.append(key, JSON.stringify(value));
          }
          // Handle files - only append if it's a new file
          else if (value instanceof File) {
            data.append(key, value);
          }
          // Special handling for categories_of_interest if it's somehow a string already
          else if (key === 'categories_of_interest') {
            // Ensure it's a valid JSON array string
            if (typeof value === 'string') {
              try {
                // Try to parse it - if valid JSON, use it, otherwise send empty array
                JSON.parse(value);
                data.append(key, value);
              } catch {
                data.append(key, '[]');
              }
            } else {
              data.append(key, '[]');
            }
          }
          // Handle other values - include empty strings too for updates
          else if (value !== null && value !== undefined) {
            data.append(key, value);
          }
        });

        const response = await axiosInstance.patch(
          `/marketplace/seller-applications/${applicationId}/`,
          data,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMessage =
          err.response?.data?.message ||
          err.response?.data?.detail ||
          Object.values(err.response?.data || {}).flat().join(", ") ||
          "Failed to update application";
        setError(errorMessage);
        return { success: false, error: errorMessage, errors: err.response?.data };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // ============================================================================
  // SELLERS
  // ============================================================================

  // Fetch sellers (for browsing)
  const fetchSellers = useCallback(
    async (filters = {}) => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.search) params.append("search", filters.search);
        if (filters.category) params.append("category", filters.category);
        if (filters.verified) params.append("is_verified", filters.verified);

        const response = await axiosInstance.get(`/marketplace/sellers/?${params}`);
        const data = response.data?.results || response.data;
        setSellers(Array.isArray(data) ? data : []);
        setError(null);
        return data;
      } catch (err) {
        setError(err.response?.data?.message || "Failed to fetch sellers");
        return [];
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Fetch single seller
  const fetchSellerBySlug = useCallback(
    async (slug) => {
      try {
        const response = await axiosInstance.get(`/marketplace/sellers/${slug}/`);
        return response.data;
      } catch (err) {
        console.error("Failed to fetch seller:", err);
        return null;
      }
    },
    [axiosInstance]
  );

  // ============================================================================
  // LISTINGS
  // ============================================================================

  // Fetch listings (marketplace browse)
  const fetchListings = useCallback(
    async (filters = {}) => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.search) params.append("search", filters.search);
        if (filters.category) params.append("category", filters.category);
        if (filters.seller) params.append("seller", filters.seller);
        if (filters.listing_type) params.append("listing_type", filters.listing_type);
        if (filters.min_price) params.append("min_price", filters.min_price);
        if (filters.max_price) params.append("max_price", filters.max_price);
        if (filters.condition) params.append("condition", filters.condition);
        if (filters.ordering) params.append("ordering", filters.ordering);
        if (filters.page && filters.page > 1) params.append("page", filters.page);

        const response = await axiosInstance.get(`/marketplace/listings/?${params}`);
        const data = response.data?.results || response.data;
        setListings(Array.isArray(data) ? data : []);
        setError(null);
        return response.data; // Return full response for pagination
      } catch (err) {
        setError(err.response?.data?.message || "Failed to fetch listings");
        return { results: [] };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Fetch single listing
  const fetchListingBySlug = useCallback(
    async (slug) => {
      try {
        const response = await axiosInstance.get(`/marketplace/listings/${slug}/`);
        return response.data;
      } catch (err) {
        console.error("Failed to fetch listing:", err);
        return null;
      }
    },
    [axiosInstance]
  );

  // Fetch featured listings (popular/best sellers)
  const fetchFeaturedListings = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/listings/featured/");
      const data = response.data?.results || response.data;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Failed to fetch featured listings:", err);
      return [];
    }
  }, [axiosInstance]);

  // Fetch recent listings (new arrivals)
  const fetchRecentListings = useCallback(async (days = 30) => {
    try {
      const response = await axiosInstance.get(`/marketplace/listings/recent/?days=${days}`);
      const data = response.data?.results || response.data;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Failed to fetch recent listings:", err);
      return [];
    }
  }, [axiosInstance]);

  // Fetch trending listings
  const fetchTrendingListings = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/listings/trending/");
      const data = response.data?.results || response.data;
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error("Failed to fetch trending listings:", err);
      return [];
    }
  }, [axiosInstance]);

  // Add to favorites
  const addToFavorites = useCallback(
    async (slug) => {
      try {
        await axiosInstance.post(`/marketplace/listings/${slug}/favorite/`);
        return { success: true };
      } catch (err) {
        console.error("Failed to add to favorites:", err);
        return { success: false, error: err.response?.data?.message || "Failed to add to favorites" };
      }
    },
    [axiosInstance]
  );

  // Remove from favorites
  const removeFromFavorites = useCallback(
    async (slug) => {
      try {
        await axiosInstance.delete(`/marketplace/listings/${slug}/unfavorite/`);
        return { success: true };
      } catch (err) {
        console.error("Failed to remove from favorites:", err);
        return { success: false, error: err.response?.data?.message || "Failed to remove from favorites" };
      }
    },
    [axiosInstance]
  );

  // Fetch user's favorites
  const fetchFavorites = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/favorites/");
      const data = response.data?.results || response.data;
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (err) {
      console.error("Failed to fetch favorites:", err);
      return { success: false, error: err.response?.data?.message || "Failed to fetch favorites", data: [] };
    }
  }, [axiosInstance]);

  // Check if a listing is favorited
  const checkIsFavorited = useCallback(
    async (listingId) => {
      try {
        const response = await axiosInstance.get("/marketplace/favorites/");
        const data = response.data?.results || response.data;
        const favorites = Array.isArray(data) ? data : [];
        return favorites.some(fav => fav.listing?.id === listingId || fav.listing?.slug === listingId);
      } catch (err) {
        console.error("Failed to check favorite status:", err);
        return false;
      }
    },
    [axiosInstance]
  );

  // ============================================
  // FOLLOW SELLER METHODS
  // ============================================

  // Follow a seller
  const followSeller = useCallback(
    async (slug) => {
      try {
        const response = await axiosInstance.post(`/marketplace/sellers/${slug}/follow/`);
        return { success: true, message: response.data?.message || "Now following seller" };
      } catch (err) {
        console.error("Failed to follow seller:", err);
        return { success: false, error: err.response?.data?.message || "Failed to follow seller" };
      }
    },
    [axiosInstance]
  );

  // Unfollow a seller
  const unfollowSeller = useCallback(
    async (slug) => {
      try {
        await axiosInstance.delete(`/marketplace/sellers/${slug}/unfollow/`);
        return { success: true, message: "Unfollowed seller" };
      } catch (err) {
        console.error("Failed to unfollow seller:", err);
        return { success: false, error: err.response?.data?.message || "Failed to unfollow seller" };
      }
    },
    [axiosInstance]
  );

  // Fetch followed sellers list
  const fetchFollowedSellers = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/follows/");
      const data = response.data?.results || response.data;
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (err) {
      console.error("Failed to fetch followed sellers:", err);
      return { success: false, error: err.response?.data?.message || "Failed to fetch followed sellers", data: [] };
    }
  }, [axiosInstance]);

  // Fetch listings from followed sellers
  const fetchFollowedSellersListings = useCallback(
    async (params = {}) => {
      try {
        const queryString = new URLSearchParams(params).toString();
        const url = `/marketplace/follows/listings/${queryString ? `?${queryString}` : ""}`;
        const response = await axiosInstance.get(url);
        return {
          success: true,
          data: response.data?.results || response.data || [],
          count: response.data?.count || 0,
          next: response.data?.next,
          previous: response.data?.previous,
        };
      } catch (err) {
        console.error("Failed to fetch followed sellers listings:", err);
        return { success: false, error: err.response?.data?.message || "Failed to fetch listings", data: [] };
      }
    },
    [axiosInstance]
  );

  // Check if user follows a specific seller
  const checkIsFollowing = useCallback(
    async (sellerSlug) => {
      try {
        const response = await axiosInstance.get(`/marketplace/follows/check/?seller=${sellerSlug}`);
        return response.data?.is_following || false;
      } catch (err) {
        // If not authenticated, return false
        console.error("Failed to check follow status:", err);
        return false;
      }
    },
    [axiosInstance]
  );

  // ============================================
  // CONVERSATION METHODS
  // ============================================

  // Fetch all conversations
  const fetchConversations = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/marketplace/conversations/");
      const data = response.data?.results || response.data;
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
      return { success: false, error: err.response?.data?.message || "Failed to fetch conversations", data: [] };
    }
  }, [axiosInstance]);

  // Fetch single conversation with messages
  const fetchConversation = useCallback(async (conversationId) => {
    try {
      const response = await axiosInstance.get(`/marketplace/conversations/${conversationId}/`);
      return { success: true, data: response.data };
    } catch (err) {
      console.error("Failed to fetch conversation:", err);
      return { success: false, error: err.response?.data?.message || "Failed to fetch conversation" };
    }
  }, [axiosInstance]);

  // Fetch messages for a conversation
  const fetchMessages = useCallback(async (conversationId) => {
    try {
      const response = await axiosInstance.get(`/marketplace/conversations/${conversationId}/messages/`);
      const data = response.data?.results || response.data;
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (err) {
      console.error("Failed to fetch messages:", err);
      return { success: false, error: err.response?.data?.message || "Failed to fetch messages", data: [] };
    }
  }, [axiosInstance]);

  // Start a new conversation or get existing one
  const startConversation = useCallback(async (sellerId, listingId = null, initialMessage = "") => {
    try {
      const response = await axiosInstance.post("/marketplace/conversations/start/", {
        seller_id: sellerId,
        listing_id: listingId,
        message: initialMessage
      });
      return { success: true, data: response.data };
    } catch (err) {
      console.error("Failed to start conversation:", err);
      return { success: false, error: err.response?.data?.message || "Failed to start conversation" };
    }
  }, [axiosInstance]);

  // Send a message in a conversation
  const sendMessage = useCallback(async (conversationId, content, attachment = null) => {
    try {
      const formData = new FormData();
      formData.append('content', content);
      if (attachment) {
        formData.append('attachment', attachment);
      }
      
      const response = await axiosInstance.post(
        `/marketplace/conversations/${conversationId}/send_message/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return { success: true, data: response.data };
    } catch (err) {
      console.error("Failed to send message:", err);
      return { success: false, error: err.response?.data?.message || "Failed to send message" };
    }
  }, [axiosInstance]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    // State
    categories,
    sellers,
    listings,
    myApplications,
    loading,
    error,

    // Category methods
    fetchCategories,
    fetchAllCategories,
    fetchRootCategories,

    // Application methods
    submitSellerApplication,
    updateSellerApplication,
    fetchMyApplications,
    getApplicationStatus,
    checkApplicationByTrackingCode,

    // Seller methods
    fetchSellers,
    fetchSellerBySlug,

    // Listing methods
    fetchListings,
    fetchListingBySlug,
    fetchFeaturedListings,
    fetchRecentListings,
    fetchTrendingListings,
    addToFavorites,
    removeFromFavorites,
    fetchFavorites,
    checkIsFavorited,

    // Conversation methods
    fetchConversations,
    fetchConversation,
    fetchMessages,
    startConversation,
    sendMessage,

    // Follow seller methods
    followSeller,
    unfollowSeller,
    fetchFollowedSellers,
    fetchFollowedSellersListings,
    checkIsFollowing,

    // Utility
    clearError,
  };

  return (
    <ElMercadoContext.Provider value={value}>
      {children}
    </ElMercadoContext.Provider>
  );
};

export default ElMercadoContext;
