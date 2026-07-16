import React, { createContext, useContext, useState, useCallback } from "react";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

const MentorshipContext = createContext();

export const useMentorship = () => {
  const context = useContext(MentorshipContext);
  if (!context) {
    throw new Error("useMentorship must be used within a MentorshipProvider");
  }
  return context;
};

export const MentorshipProvider = ({ children }) => {
  const axiosInstance = useAxiosWithRefresh();

  // State
  const [areas, setAreas] = useState([]);
  const [mentors, setMentors] = useState([]);
  const [interviewers, setInterviewers] = useState([]);
  const [eligibility, setEligibility] = useState(null);
  const [mentorDashboard, setMentorDashboard] = useState(null);
  const [menteeDashboard, setMenteeDashboard] = useState(null);
  const [myMentorApplications, setMyMentorApplications] = useState([]);
  const [myMenteeApplications, setMyMenteeApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch mentorship areas
  const fetchAreas = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get("/mentorship/areas/");
      // Backend returns { areas: [...] }
      const data =
        response.data?.areas ||
        response.data?.data ||
        response.data?.results ||
        response.data;
      setAreas(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch areas");
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Check mentor eligibility
  const checkEligibility = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get(
        "/mentorship/mentor/eligibility/"
      );
      setEligibility(response.data?.data || response.data);
      setError(null);
      return response.data?.data || response.data;
    } catch (err) {
      setError(err.response?.data?.message || "Failed to check eligibility");
      return null;
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Fetch approved mentors (for mentee browsing)
  const fetchMentors = useCallback(
    async (filters = {}) => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.area) params.append("area", filters.area);
        if (filters.search) params.append("search", filters.search);

        const response = await axiosInstance.get(
          `/mentorship/mentors/?${params}`
        );
        // Backend returns { mentors: [...] }
        const data =
          response.data?.mentors || response.data?.data || response.data;
        setMentors(Array.isArray(data) ? data : []);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to fetch mentors");
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Fetch single mentor by ID
  const fetchMentorById = useCallback(
    async (mentorId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/mentors/${mentorId}/`
        );
        // Backend may return { mentor: {...} } or just the mentor object
        return response.data?.mentor || response.data;
      } catch (err) {
        setError(err.response?.data?.message || "Failed to fetch mentor");
        return null;
      }
    },
    [axiosInstance]
  );

  // Fetch interviewers with schedules
  const fetchInterviewers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get("/mentorship/interviewers/");
      // Backend returns { interviewers: [...] }
      const data =
        response.data?.interviewers || response.data?.data || response.data;
      setInterviewers(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch interviewers");
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Submit mentor application
  const submitMentorApplication = useCallback(
    async (applicationData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          "/mentorship/mentor/apply/",
          applicationData
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message ||
          err.response?.data?.errors ||
          "Failed to submit application";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Schedule interview (select interviewer and time slot)
  const scheduleInterview = useCallback(
    async (applicationId, scheduleData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/mentor/applications/${applicationId}/schedule-interview/`,
          scheduleData
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to schedule interview";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Check mentee application eligibility for a specific mentor
  const checkMenteeEligibility = useCallback(
    async (mentorId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/mentee/eligibility/${mentorId}/`
        );
        return response.data;
      } catch (err) {
        console.error("Error checking mentee eligibility:", err);
        return {
          can_apply: false,
          reason: "error",
          message: err.response?.data?.message || "Failed to check eligibility",
          areas: [],
        };
      }
    },
    [axiosInstance]
  );

  // Submit mentee application
  const submitMenteeApplication = useCallback(
    async (applicationData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          "/mentorship/mentee/apply/",
          applicationData
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message ||
          err.response?.data?.errors ||
          "Failed to submit application";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Fetch mentor dashboard
  const fetchMentorDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get("/mentorship/dashboard/mentor/");
      setMentorDashboard(response.data?.data || response.data);
      setError(null);
    } catch (err) {
      setError(
        err.response?.data?.message || "Failed to fetch mentor dashboard"
      );
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Fetch mentee dashboard
  const fetchMenteeDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get("/mentorship/dashboard/mentee/");
      setMenteeDashboard(response.data?.data || response.data);
      setError(null);
    } catch (err) {
      setError(
        err.response?.data?.message || "Failed to fetch mentee dashboard"
      );
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Fetch my mentor applications
  const fetchMyMentorApplications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get(
        "/mentorship/mentor/applications/"
      );
      // Backend returns { applications: [...] }
      const data =
        response.data?.applications ||
        response.data?.data ||
        response.data?.results ||
        response.data;
      setMyMentorApplications(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch applications");
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Fetch my mentee applications
  const fetchMyMenteeApplications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get(
        "/mentorship/mentee/applications/"
      );
      // Backend returns { applications: [...] }
      const data =
        response.data?.applications ||
        response.data?.data ||
        response.data?.results ||
        response.data;
      setMyMenteeApplications(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch applications");
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Respond to mentee application (for mentors)
  const respondToMenteeApplication = useCallback(
    async (applicationId, action, message = "") => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/mentor/mentee-applications/${applicationId}/respond/`,
          { action, message }
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to respond to application";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Withdraw mentee application
  const withdrawMenteeApplication = useCallback(
    async (applicationId) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/mentee/applications/${applicationId}/withdraw/`
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to withdraw application";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Get mentor details
  const getMentorDetails = useCallback(
    async (mentorId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/mentors/${mentorId}/`
        );
        return response.data?.data || response.data;
      } catch (err) {
        return null;
      }
    },
    [axiosInstance]
  );

  // Get area tags
  const getAreaTags = useCallback(
    async (areaId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/areas/${areaId}/tags/`
        );
        // Backend returns { tags: [...] }
        const data =
          response.data?.tags || response.data?.data || response.data;
        return Array.isArray(data) ? data : [];
      } catch (err) {
        return [];
      }
    },
    [axiosInstance]
  );

  // Accept mentee application (alias for respondToMenteeApplication with 'accept')
  const acceptMentee = useCallback(
    async (applicationId) => {
      return respondToMenteeApplication(applicationId, "accept");
    },
    [respondToMenteeApplication]
  );

  // Reject mentee application (alias for respondToMenteeApplication with 'reject')
  const rejectMentee = useCallback(
    async (applicationId, message = "") => {
      return respondToMenteeApplication(applicationId, "reject", message);
    },
    [respondToMenteeApplication]
  );

  // Schedule a mentorship session
  const scheduleSession = useCallback(
    async (sessionData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          "/mentorship/sessions/create/",
          sessionData
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message ||
          err.response?.data?.errors ||
          "Failed to schedule session";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Get session details
  const getSessionDetails = useCallback(
    async (sessionId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/sessions/${sessionId}/`
        );
        return response.data;
      } catch (err) {
        return null;
      }
    },
    [axiosInstance]
  );

  // Complete a session (mentor only - adds session notes)
  const completeSession = useCallback(
    async (sessionId, mentorNotes) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/sessions/${sessionId}/complete/`,
          { mentor_notes: mentorNotes }
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to complete session";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Review a session (mentee only - adds feedback and rating)
  const reviewSession = useCallback(
    async (sessionId, reviewData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/sessions/${sessionId}/review/`,
          reviewData
        );
        setError(null);
        return { success: true, data: response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to submit review";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Check relationship with mentor (for donation eligibility)
  const checkMentorRelationship = useCallback(
    async (mentorId) => {
      try {
        const response = await axiosInstance.get(
          `/mentorship/mentors/${mentorId}/relationship/`
        );
        return response.data?.data || response.data;
      } catch (err) {
        return null;
      }
    },
    [axiosInstance]
  );

  // Donate to mentor
  const donateToMentor = useCallback(
    async (mentorId, donationData) => {
      setLoading(true);
      try {
        const response = await axiosInstance.post(
          `/mentorship/mentors/${mentorId}/donate/`,
          donationData
        );
        setError(null);
        return { success: true, data: response.data?.data || response.data };
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || "Failed to initiate donation";
        setError(errorMsg);
        return { success: false, error: errorMsg };
      } finally {
        setLoading(false);
      }
    },
    [axiosInstance]
  );

  // Get mentor wallet info (for mentors to see their donations)
  const getMentorWalletInfo = useCallback(async () => {
    try {
      const response = await axiosInstance.get("/mentorship/wallet/info/");
      return response.data?.data || response.data;
    } catch (err) {
      return null;
    }
  }, [axiosInstance]);

  // Fetch all my applications (both mentor and mentee)
  const fetchMyApplications = useCallback(async () => {
    setLoading(true);
    try {
      const [mentorRes, menteeRes] = await Promise.all([
        axiosInstance
          .get("/mentorship/mentor/applications/")
          .catch(() => ({ data: { applications: [] } })),
        axiosInstance
          .get("/mentorship/mentee/applications/")
          .catch(() => ({ data: { applications: [] } })),
      ]);

      // Backend returns { applications: [...] }
      const mentorApps =
        mentorRes.data?.applications ||
        mentorRes.data?.data ||
        mentorRes.data ||
        [];
      const menteeApps =
        menteeRes.data?.applications ||
        menteeRes.data?.data ||
        menteeRes.data ||
        [];

      const result = {
        mentor_applications: Array.isArray(mentorApps) ? mentorApps : [],
        mentee_applications: Array.isArray(menteeApps) ? menteeApps : [],
      };

      setMyMentorApplications(result.mentor_applications);
      setMyMenteeApplications(result.mentee_applications);
      setError(null);

      return result;
    } catch (err) {
      setError(err.response?.data?.message || "Failed to fetch applications");
      return { mentor_applications: [], mentee_applications: [] };
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  // Computed property for combined applications
  const myApplications = {
    mentor_applications: myMentorApplications,
    mentee_applications: myMenteeApplications,
  };

  const value = {
    // State
    areas,
    mentors,
    interviewers,
    eligibility,
    mentorDashboard,
    menteeDashboard,
    myMentorApplications,
    myMenteeApplications,
    myApplications,
    loading,
    error,

    // Actions
    fetchAreas,
    checkEligibility,
    fetchMentors,
    fetchMentorById,
    fetchInterviewers,
    submitMentorApplication,
    scheduleInterview,
    checkMenteeEligibility,
    submitMenteeApplication,
    fetchMentorDashboard,
    fetchMenteeDashboard,
    fetchMyMentorApplications,
    fetchMyMenteeApplications,
    fetchMyApplications,
    respondToMenteeApplication,
    acceptMentee,
    rejectMentee,
    withdrawMenteeApplication,
    getMentorDetails,
    getAreaTags,
    scheduleSession,
    getSessionDetails,
    completeSession,
    reviewSession,
    // Donation actions
    checkMentorRelationship,
    donateToMentor,
    getMentorWalletInfo,

    // Setters
    setError,
  };

  return (
    <MentorshipContext.Provider value={value}>
      {children}
    </MentorshipContext.Provider>
  );
};

export default MentorshipContext;
