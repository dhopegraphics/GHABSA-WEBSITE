import { useEffect, useState, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { fadeIn } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import {
  getVotingEventDetail,
  getEventCandidates,
  getEventPollOptions,
  getMyEligibility,
  getMyCandidacies,
  castVote,
  initializePayment,
  checkAnonymousVoteStatus,
} from "../utils/votingApi";
import { getVotingIdentifiers } from "../utils/deviceFingerprint";
import { UserContext } from "../Context/UserContext";
import { useVoting } from "../Context/VotingContext";
import { CandidateCard } from "../Components/Voting/CandidateCard";
import { CandidateDetailModal } from "../Components/Voting/CandidateDetailModal";
import { PollOptionCard, PollQuestionSection } from "../Components/Voting/PollOptionCard";
import { Helmet } from "react-helmet-async";
import {
  Calendar,
  Users,
  Vote as VoteIcon,
  Clock,
  Award,
  AlertCircle,
  CheckCircle,
  Loader,
  ArrowLeft,
  DollarSign,
} from "lucide-react";
import Login from "./Login";
import SignUp from "./SignUp";
import toast from "react-hot-toast";
import { PaymentModal } from "../Components/Voting/PaymentModal";
import { CandidateRegistrationModal } from "../Components/Voting/CandidateRegistrationModal";
import { UserPlus } from "lucide-react";

export function VotingDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  const { getVoteDetailsForEvent, markEventAsVoted } = useVoting();

  const [event, setEvent] = useState(null);
  const [candidates, setCandidates] = useState({});
  const [pollOptions, setPollOptions] = useState(null); // For poll/referendum events
  const [eligibility, setEligibility] = useState(null);
  const [isUserCandidate, setIsUserCandidate] = useState(false);
  const [userCandidacy, setUserCandidacy] = useState(null); // User's candidacy for this event
  const [selectedVotes, setSelectedVotes] = useState({}); // {category: {candidate, quantity}} or {question: option}
  const [votedCategories, setVotedCategories] = useState([]); // Track categories already voted in
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);

  // Auth modals
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  // Candidate registration modal
  const [isRegistrationModalOpen, setIsRegistrationModalOpen] = useState(false);

  // Candidate detail modal
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  // Payment modal
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [paymentData, setPaymentData] = useState(null);

  // Handle viewing candidate details
  const handleViewCandidateDetails = (candidate) => {
    setSelectedCandidate(candidate);
    setIsCandidateDetailOpen(true);
  };

  // Track if anonymous user has voted (checked from backend)
  const [anonymousHasVoted, setAnonymousHasVoted] = useState(false);
  const [checkingAnonymousVote, setCheckingAnonymousVote] = useState(false);
  const [voteDetectionReason, setVoteDetectionReason] = useState(null); // Why vote was blocked
  
  // Track if event requires login due to visibility restrictions
  const [requiresLogin, setRequiresLogin] = useState(false);
  const [accessError, setAccessError] = useState(null);

  // Check vote status from BACKEND on mount
  // This uses device fingerprint, IP address, and user account for robust detection
  // IMPORTANT: This runs for BOTH anonymous AND logged-in users because:
  // - A logged-in user might have voted anonymously earlier
  // - An anonymous user might have voted when logged in on another device
  useEffect(() => {
    const checkVoteStatusOnMount = async () => {
      if (!slug) return;
      
      // First, check if we have pre-loaded data from VotingPage context
      const contextVoteDetails = getVoteDetailsForEvent(slug);
      if (contextVoteDetails?.has_voted) {
        setAnonymousHasVoted(true);
        if (contextVoteDetails.voted_categories?.length > 0) {
          setVotedCategories(contextVoteDetails.voted_categories);
        }
        if (contextVoteDetails.reason) {
          setVoteDetectionReason(contextVoteDetails.reason);
        }
        console.log("📊 Vote status from context:", contextVoteDetails);
        return; // No need to make API call, we already have the data
      }
      
      // If not in context, check with backend
      setCheckingAnonymousVote(true);
      try {
        // Get device identifiers
        const identifiers = await getVotingIdentifiers();
        
        // Check with backend using fingerprint, IP, and user token
        const { data, error } = await checkAnonymousVoteStatus(
          slug,
          identifiers.device_fingerprint,
          identifiers.session_id
        );
        
        if (!error && data) {
          setAnonymousHasVoted(data.has_voted);
          if (data.voted_categories && data.voted_categories.length > 0) {
            setVotedCategories(data.voted_categories);
          }
          // Store the reason for blocking if present
          if (data.reason) {
            setVoteDetectionReason(data.reason);
          }
          console.log("📊 Vote status check:", data);
        }
      } catch (err) {
        console.error("Error checking vote status:", err);
      } finally {
        setCheckingAnonymousVote(false);
      }
    };
    
    checkVoteStatusOnMount();
  }, [slug, user, getVoteDetailsForEvent]); // Re-check when user logs in/out

  // Helper to extract error message from DRF responses
  const extractErrorMessage = (error) => {
    if (!error) return "An error occurred";
    
    // If it's a string, return it directly
    if (typeof error === "string") return error;
    
    // If it's an array, get the first element
    if (Array.isArray(error)) {
      return error[0] || "An error occurred";
    }
    
    // Check common DRF error formats
    if (error.non_field_errors) {
      return Array.isArray(error.non_field_errors) 
        ? error.non_field_errors[0] 
        : error.non_field_errors;
    }
    
    if (error.detail) {
      return Array.isArray(error.detail) ? error.detail[0] : error.detail;
    }
    
    if (error.message) {
      return error.message;
    }
    
    // If it's an object with field errors, get the first one
    const keys = Object.keys(error);
    if (keys.length > 0) {
      const firstError = error[keys[0]];
      return Array.isArray(firstError) ? firstError[0] : firstError;
    }
    
    return "An error occurred";
  };

  const fetchEventDetails = async () => {
    setLoading(true);
    setRequiresLogin(false);
    setAccessError(null);

    // First fetch event details to determine type
    const eventRes = await getVotingEventDetail(slug);
    
    if (eventRes.error) {
      console.error("❌ Error fetching event:", eventRes.error);
      
      // Check if this is a visibility/login requirement error
      if (eventRes.requiresLogin) {
        setRequiresLogin(true);
        setAccessError(eventRes.error?.detail || "Authentication required to access this event.");
        setLoading(false);
        return;
      }
      
      toast.error("Failed to load event details");
      setLoading(false);
      return;
    }

    setEvent(eventRes.data);
    
    const isPollEvent = ['poll', 'referendum'].includes(eventRes.data?.event_type);

    // Fetch appropriate data based on event type
    const [dataRes, eligibilityRes, candidaciesRes] = await Promise.all([
      isPollEvent 
        ? getEventPollOptions(slug)
        : getEventCandidates(slug),
      user
        ? getMyEligibility(slug)
        : Promise.resolve({ data: null, error: null }),
      user && !isPollEvent
        ? getMyCandidacies()
        : Promise.resolve({ data: null, error: null }),
    ]);

    if (isPollEvent) {
      // Handle poll options
    
      
      if (dataRes.error) {
        console.error("❌ Error fetching poll options:", dataRes.error);
        toast.error("Failed to load poll options");
      } else {
       
        setPollOptions(dataRes.data);
      }
    } else {
      // Handle candidates (existing logic)
    
      
      if (dataRes.error) {
        console.error("❌ Error fetching candidates:", dataRes.error);
        toast.error("Failed to load candidates");
      } else {
        // Normalize candidates data structure
        let normalizedCandidates = dataRes.data || {};
        
        if (Array.isArray(dataRes.data)) {
          // Event has no categories - wrap in "Candidates" key
          normalizedCandidates = {
            "Candidates": dataRes.data
          };
       
        } else {
          console.log(
            "✅ Candidates loaded:",
            Object.keys(dataRes.data || {}).length,
            "categories"
          );
        }
        
        setCandidates(normalizedCandidates);

       
        

        // Check if current user is a candidate in this event
        if (user && normalizedCandidates) {
          const allCandidates = Object.values(normalizedCandidates).flat();
          const userIsCandidate = allCandidates.some(
            (candidate) => candidate.user_account === user.id
          );
 
          setIsUserCandidate(userIsCandidate);
        }
      }
    }


    if (user && eligibilityRes.data) {
    
      setEligibility(eligibilityRes.data);
    } else if (user && !eligibilityRes.data) {
      console.log("⚠️ User logged in but no eligibility data returned");
    }

    // Check if user has registered as candidate for this event (only for non-poll events)
    if (!isPollEvent && user && candidaciesRes.data && eventRes.data) {
      const eventCandidacy = candidaciesRes.data.find(
        (c) => c.event === eventRes.data.id
      );
      if (eventCandidacy) {
      
        setUserCandidacy(eventCandidacy);
        setIsUserCandidate(true);
      }
    }

    setLoading(false);
  };

  useEffect(() => {
    scrollToTop();
    fetchEventDetails();
  }, [slug, user]);

  const handleVoteSelection = (category, candidate) => {
    setSelectedVotes((prev) => ({
      ...prev,
      [category]: { candidate, quantity: prev[category]?.quantity || 1 },
    }));
  };

  // Handler for poll option selection
  const handlePollOptionSelect = (questionKey, option) => {
    setSelectedVotes((prev) => ({
      ...prev,
      [questionKey]: { option, quantity: 1 },
    }));
  };

  const handleQuantityChange = (category, quantity) => {
    setSelectedVotes((prev) => {
      if (!prev[category]) return prev;
      return {
        ...prev,
        [category]: {
          ...prev[category],
          quantity: Math.max(1, parseInt(quantity) || 1),
        },
      };
    });
  };

  const handleSubmitVotes = async () => {
    // Check if event has ended
    if (isEventEnded) {
      toast.error("This voting event has ended. You cannot vote anymore.");
      return;
    }

    // Check if voting is still open
    if (!isVotingOpen) {
      toast.error("Voting is not currently open for this event.");
      return;
    }

    // Check if event requires authentication
    const requiresAuth = event.requires_authentication !== false; // Default to true
    
    // For public events (requires_authentication=false), allow anonymous users
    const canVoteAnonymously = !requiresAuth && event.visibility === "public";

    if (!user && !canVoteAnonymously) {
      toast.error("This event requires authentication. Please log in to vote.");
      setIsLoginModalOpen(true);
      return;
    }

    if (Object.keys(selectedVotes).length === 0) {
      toast.error(isPollEvent ? "Please select an option" : "Please select at least one candidate");
      return;
    }

    const totalVotes = Object.values(selectedVotes).reduce((sum, vote) => {
      return sum + vote.quantity;
    }, 0);

    const totalAmount = Object.values(selectedVotes).reduce((sum, vote) => {
      return sum + vote.quantity * parseFloat(event.voting_fee || 0);
    }, 0);

    // Check if this is a truly anonymous event (no auth required, no payment, allows anonymous voting)
    const isTrulyAnonymousEvent = 
      event.anonymous_voting && 
      !event.requires_authentication && 
      !event.requires_payment;

    // If payment required, open payment modal for payment processing
    if (event.requires_payment) {
      setPaymentData({
        totalVotes,
        totalAmount,
        currency: event.currency || "GHS",
        eventTitle: event.title,
        requiresPayment: true,
        isAnonymous: !user,
      });
      setIsPaymentModalOpen(true);
      return;
    }

    // If not logged in AND NOT a truly anonymous event, we need user details
    if (!user && !isTrulyAnonymousEvent) {
      setPaymentData({
        totalVotes,
        totalAmount,
        currency: event.currency || "GHS",
        eventTitle: event.title,
        requiresPayment: false,
        isAnonymous: true,
      });
      setIsPaymentModalOpen(true);
      return;
    }

    // For truly anonymous events or logged-in users - proceed directly without modal
    setVoting(true);

    try {
      // Get device identifiers for vote tracking
      const identifiers = await getVotingIdentifiers();
      console.log("📱 Device identifiers:", identifiers);
      
      // Step 1: Cast votes
      const votePromises = Object.entries(selectedVotes).map(([categoryKey, voteData]) => {
        // Build vote payload based on event type
        const votePayload = {
          event: event.id,
          vote_quantity: voteData.quantity,
          ...identifiers, // Include device_fingerprint and session_id
        };
        
        // For poll events, include poll_option instead of candidate
        if (isPollEvent && voteData.option) {
          votePayload.poll_option = voteData.option.id;
          // Use category_id (UUID) or category (FK ID) from poll option
          votePayload.category = voteData.option.category_id || voteData.option.category || null;
        } else if (voteData.candidate) {
          votePayload.candidate = voteData.candidate.id;
          votePayload.category = voteData.candidate.category || null;
        }
        
        console.log("📤 Vote payload:", votePayload);
        return castVote(votePayload);
      });

      const results = await Promise.all(votePromises);
      const errors = results.filter((r) => r.error);

      if (errors.length > 0) {
        const errorMessage = extractErrorMessage(errors[0].error);
        toast.error(errorMessage);
        setVoting(false);
        return;
      }

      // No payment required - votes are immediately counted
      toast.success(`${totalVotes} vote(s) cast successfully!`);
      
      // Update local state to show voted status immediately
      const newVotedCategories = [...votedCategories];
      Object.keys(selectedVotes).forEach((questionKey) => {
        if (!newVotedCategories.includes(questionKey)) {
          newVotedCategories.push(questionKey);
        }
      });
      setVotedCategories(newVotedCategories);
      
      // Mark as voted in both local state and context
      setAnonymousHasVoted(true);
      markEventAsVoted(slug, {
        reason: "You have successfully voted in this event.",
        voted_categories: newVotedCategories
      });
      
      setSelectedVotes({});
      fetchEventDetails(); // Refresh to update vote counts
      setVoting(false);
    } catch (error) {
      console.error("Voting error:", error);
      toast.error("An error occurred while voting");
      setVoting(false);
    }
  };

  const handlePaymentSubmit = async (customerDetails) => {
    setVoting(true);
    
    // Determine if this is a poll event
    const isPollEvent = ['poll', 'referendum'].includes(event?.event_type);

    try {
      // Get device identifiers for vote tracking
      const identifiers = await getVotingIdentifiers();
      
      // Step 1: Cast votes first
      const votePromises = Object.entries(selectedVotes).map(([, voteData]) => {
        // Build vote payload based on event type
        const votePayload = {
          event: event.id,
          vote_quantity: voteData.quantity,
          ...identifiers, // Include device_fingerprint and session_id
        };

        // For poll events, include poll_option instead of candidate
        if (isPollEvent && voteData.option) {
          votePayload.poll_option = voteData.option.id;
          // Use category_id (UUID) or category (FK ID) from poll option
          votePayload.category = voteData.option.category_id || voteData.option.category || null;
        } else if (voteData.candidate) {
          votePayload.candidate = voteData.candidate.id;
          votePayload.category = voteData.candidate.category;
        }

        // Add guest info for anonymous users (when payment modal collected details)
        if (!user && customerDetails) {
          votePayload.guest_email = customerDetails.email;
          votePayload.guest_phone = customerDetails.phone;
          votePayload.guest_name = customerDetails.name;
        }

        return castVote(votePayload);
      });

      const results = await Promise.all(votePromises);
      const errors = results.filter((r) => r.error);

      if (errors.length > 0) {
        const errorMessage = extractErrorMessage(errors[0].error);
        toast.error(errorMessage);
        setVoting(false);
        setIsPaymentModalOpen(false);
        return;
      }

      // If no payment required, we're done
      if (!event.requires_payment) {
        toast.success(`Vote(s) cast successfully!`);
        
        // Update local state to show voted status immediately
        const newVotedCategories = [...votedCategories];
        Object.keys(selectedVotes).forEach((questionKey) => {
          if (!newVotedCategories.includes(questionKey)) {
            newVotedCategories.push(questionKey);
          }
        });
        setVotedCategories(newVotedCategories);
        
        // Mark as voted in both local state and context
        setAnonymousHasVoted(true);
        markEventAsVoted(slug, {
          reason: "You have successfully voted in this event.",
          voted_categories: newVotedCategories
        });
        
        setSelectedVotes({});
        fetchEventDetails(); // Refresh to update vote counts
        setVoting(false);
        setIsPaymentModalOpen(false);
        return;
      }

      // Step 2: Initialize payment with customer details (only if payment required)
      const totalVotes = Object.values(selectedVotes).reduce(
        (sum, vote) => sum + vote.quantity,
        0
      );

      toast(`${totalVotes} vote(s) cast. Redirecting to payment...`, {
        icon: "💳",
      });

      const callbackUrl = `${window.location.origin}/voting/${slug}?payment_callback=true`;

      const { data, error } = await initializePayment({
        event_slug: slug,
        currency: customerDetails.currency || event.currency || "GHS",
        gateway: "paystack",
        callback_url: callbackUrl,
        customer_email: customerDetails.email,
        customer_phone: customerDetails.phone,
        customer_name: customerDetails.name,
      });

      if (error) {
        const errorMessage =
          error.message || error.detail || "Failed to initialize payment";
        toast.error(errorMessage);
        setVoting(false);
        setIsPaymentModalOpen(false);
        return;
      }

      // Store reference and redirect to payment gateway
      if (data?.data?.authorization_url) {
        if (data?.data?.reference) {
          localStorage.setItem(
            "pending_payment_reference",
            data.data.reference
          );
        }
        window.location.href = data.data.authorization_url;
      } else {
        toast.error("Payment URL not received");
        setVoting(false);
        setIsPaymentModalOpen(false);
      }
    } catch (error) {
      console.error("Payment error:", error);
      toast.error("Payment initialization failed");
      setVoting(false);
      setIsPaymentModalOpen(false);
    }
  };

  // Handle payment callback from payment gateway
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentCallback = urlParams.get("payment_callback");
    const reference = urlParams.get("reference");
    const trxref = urlParams.get("trxref"); // Paystack uses trxref

    if (paymentCallback === "true") {
      const paymentRef =
        reference ||
        trxref ||
        localStorage.getItem("pending_payment_reference");

      if (paymentRef) {
        // Clear the reference from localStorage
        localStorage.removeItem("pending_payment_reference");

        // Show success message
        toast.success("Payment successful! Your votes have been recorded.");
        
        // Store in localStorage for anonymous vote tracking
        try {
          const votedEvents = JSON.parse(localStorage.getItem('voted_events') || '[]');
          if (event?.id && !votedEvents.includes(event.id)) {
            votedEvents.push(event.id);
            localStorage.setItem('voted_events', JSON.stringify(votedEvents));
          }
        } catch {
          // Ignore localStorage errors
        }

        // Clean URL
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);

        // Refresh event details to show updated status
        fetchEventDetails();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const handlePayment = async () => {
    if (!user) {
      setIsLoginModalOpen(true);
      return;
    }

    try {
      const callbackUrl = `${window.location.origin}/voting/${slug}?payment_callback=true`;

      const { data, error } = await initializePayment({
        event_slug: slug,
        currency: event.currency || "GHS",
        gateway: "paystack",
        callback_url: callbackUrl,
      });

      if (error) {
        const errorMessage =
          error.message || error.detail || "Failed to initialize payment";
        toast.error(errorMessage);
        return;
      }

      if (data?.data?.authorization_url) {
        // Store reference for later verification
        if (data?.data?.reference) {
          localStorage.setItem(
            "pending_payment_reference",
            data.data.reference
          );
        }
        window.location.href = data.data.authorization_url;
      } else {
        toast.error("Payment URL not received");
      }
    } catch (err) {
      console.error("Payment error:", err);
      toast.error("Payment initialization failed");
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <>
        <Navbar
          onSignInClick={() => setIsLoginModalOpen(true)}
        />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <Loader
              className="animate-spin text-indigo-600 mx-auto mb-4"
              size={48}
            />
            <p className="text-gray-600">Loading event details...</p>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  if (!event) {
    // Check if login is required to view this event
    if (requiresLogin) {
      return (
        <>
          <Navbar onSignInClick={() => setIsLoginModalOpen(true)} />
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center max-w-md mx-auto p-8">
              <div className="bg-amber-100 rounded-full p-4 w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                <AlertCircle className="text-amber-600" size={40} />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Login Required
              </h2>
              <p className="text-gray-600 mb-6">
                {accessError || "You need to log in to view this event."}
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => setIsLoginModalOpen(true)}
                  className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
                >
                  Log In to Continue
                </button>
                <button
                  onClick={() => navigate("/voting")}
                  className="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100"
                >
                  Back to Events
                </button>
              </div>
            </div>
          </div>
          
          {/* Login Modal */}
          {isLoginModalOpen && (
            <Login
              onClose={() => setIsLoginModalOpen(false)}
              switchToSignup={() => {
                setIsLoginModalOpen(false);
                setIsSignupModalOpen(true);
              }}
              action={() => setIsLoginModalOpen(false)}
            />
          )}
          
          {/* Signup Modal */}
          {isSignupModalOpen && (
            <SignUp
              onClose={() => setIsSignupModalOpen(false)}
              switchToLogin={() => {
                setIsSignupModalOpen(false);
                setIsLoginModalOpen(true);
              }}
            />
          )}
          
          <Footer />
        </>
      );
    }
    
    return (
      <>
        <Navbar
          onSignInClick={() => setIsLoginModalOpen(true)}
        />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="text-red-600 mx-auto mb-4" size={64} />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Event Not Found
            </h2>
            <button
              onClick={() => navigate("/voting")}
              className="mt-4 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Back to Events
            </button>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  // Use computed values from API (already accounts for both boolean switch AND date range)
  const isVotingOpen = event.is_voting_open;
  const isRegistrationOpen = event.is_registration_open;
  
  // Check if user has voted - for authenticated users use API, for anonymous check localStorage
  const hasVoted = user 
    ? (eligibility?.has_voted || false) 
    : anonymousHasVoted;
  
  // Check if this is a poll/referendum event
  const isPollEvent = ['poll', 'referendum'].includes(event.event_type);
  
  // Check if event is in a final state (no voting allowed)
  const isEventEnded = ['completed', 'results_published', 'voting_closed'].includes(event.status);

  // Determine eligibility
  // Priority order:
  // 1. If event is public (no restrictions), all logged-in users are eligible
  // 2. If eligibility API returned data, use that
  // 3. Otherwise use event-level user_is_eligible flag
  const isPublicEvent =
    (!event.eligible_levels || event.eligible_levels.length === 0) &&
    (!event.eligible_programs || event.eligible_programs.length === 0);

  const isEligible =
    user && isPublicEvent
      ? true // Public event - all logged-in users eligible
      : eligibility?.is_eligible !== undefined
      ? eligibility.is_eligible
      : event.user_is_eligible !== undefined
      ? event.user_is_eligible
      : false;

  const requiresPayment = event.requires_payment;
  const paymentVerified = eligibility?.payment_verified || false;

  // For vote purchasing: Users can select candidates BEFORE payment
  // Anonymous users can select candidates for public events
  // Block if event has ended (completed, results_published, voting_closed)
  const canSelectCandidates =
    isVotingOpen && !hasVoted && !isEventEnded && (user ? isEligible : isPublicEvent);

  return (
    <>
      <Helmet>
        <title>{event.title} | BIO-CHEM KNUST Voting</title>
        <meta
          name="description"
          content={event.description || "Vote in this event"}
        />
      </Helmet>

      <Navbar
        onSignInClick={() => setIsLoginModalOpen(true)}
      />

      {/* Event Header */}
      <motion.section
        variants={fadeIn("down", 0.2)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-12"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <button
            onClick={() => navigate("/voting")}
            className="flex items-center gap-2 text-indigo-100 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Events
          </button>

          {event.banner && (
            <div className="mb-6 rounded-xl overflow-hidden">
              <img
                src={event.banner}
                alt={event.title}
                className="w-full h-64 object-cover"
              />
            </div>
          )}

          <h1 className="text-4xl font-bold mb-4">{event.title}</h1>
          {event.description && (
            <p className="text-xl text-indigo-100 mb-6">{event.description}</p>
          )}

          {/* Event Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <Users className="mb-2" size={24} />
              <p className="text-2xl font-bold">
                {event.total_registered_candidates || 0}
              </p>
              <p className="text-sm text-indigo-100">Candidates</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <VoteIcon className="mb-2" size={24} />
              <p className="text-2xl font-bold">
                {event.total_votes_cast || 0}
              </p>
              <p className="text-sm text-indigo-100">Votes Cast</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <Calendar className="mb-2" size={24} />
              <p className="text-sm font-medium">
                {formatDate(event.voting_start_date)}
              </p>
              <p className="text-xs text-indigo-100">Start Date</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <Clock className="mb-2" size={24} />
              <p className="text-sm font-medium">
                {formatDate(event.voting_end_date)}
              </p>
              <p className="text-xs text-indigo-100">End Date</p>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Eligibility Status - show for both authenticated and anonymous users */}
      {(user || (!user && isPublicEvent)) && (
        <motion.section
          variants={fadeIn("up", 0.3)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        >
          {/* Anonymous user notice for public events */}
          {!user && isPublicEvent && isVotingOpen && !hasVoted && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3 mb-4">
              <CheckCircle className="text-blue-600 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-bold text-blue-900 mb-1">
                  Guest Voting Available
                </h3>
                <p className="text-blue-700 text-sm">
                  This is a public event! You can vote without logging in. Just
                  select your candidates and provide your contact details when
                  prompted.
                </p>
              </div>
            </div>
          )}
          
          {/* Anonymous user already voted */}
          {!user && hasVoted && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3 mb-4">
              <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-bold text-green-900 mb-1">
                  Vote Already Recorded
                </h3>
                <p className="text-green-700 text-sm">
                  {voteDetectionReason || "A vote has already been cast from this device/network."}
                </p>
                <p className="text-green-600 text-xs mt-1">
                  Thank you for participating!
                </p>
              </div>
            </div>
          )}

          {user && !isEligible &&
            isUserCandidate &&
            !event.allow_candidate_self_voting && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle
                  className="text-amber-600 flex-shrink-0"
                  size={24}
                />
                <div>
                  <h3 className="font-bold text-amber-900 mb-1">
                    Candidate Restriction
                  </h3>
                  <p className="text-amber-700 text-sm">
                    You are a candidate in this event. Candidates are not
                    allowed to vote in this event per the event organizer's
                    rules.
                  </p>
                </div>
              </div>
            )}

          {user && !isEligible && !isUserCandidate && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-bold text-red-900 mb-1">Not Eligible</h3>
                <p className="text-red-700 text-sm">
                  You are not eligible to vote in this event.{" "}
                  {eligibility?.eligibility_reason}
                </p>
              </div>
            </div>
          )}

          {isUserCandidate &&
            event.allow_candidate_self_voting &&
            isEligible &&
            !hasVoted && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
                <CheckCircle
                  className="text-blue-600 flex-shrink-0"
                  size={24}
                />
                <div>
                  <h3 className="font-bold text-blue-900 mb-1">
                    You Can Vote!
                  </h3>
                  <p className="text-blue-700 text-sm">
                    Even though you are a candidate in this event, you are
                    allowed to vote. You can vote for any candidate including
                    yourself.
                  </p>
                </div>
              </div>
            )}

          {user && hasVoted && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-bold text-green-900 mb-1">
                  Vote Already Recorded
                </h3>
                <p className="text-green-700 text-sm">
                  {voteDetectionReason || "You have already voted in this event."}
                </p>
                <p className="text-green-600 text-xs mt-1">
                  Thank you for participating!
                </p>
              </div>
            </div>
          )}

          {requiresPayment &&
            !paymentVerified &&
            isEligible &&
            !hasVoted &&
            Object.keys(selectedVotes).length === 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                <DollarSign
                  className="text-amber-600 flex-shrink-0"
                  size={24}
                />
                <div className="flex-1">
                  <h3 className="font-bold text-amber-900 mb-1">
                    Payment Required
                  </h3>
                  <p className="text-amber-700 text-sm mb-3">
                    This event requires a voting fee of GHS{" "}
                    {parseFloat(event.voting_fee || 0).toFixed(2)} per vote.
                    {event.allow_multiple_vote_purchase &&
                      " Select candidates and vote quantities below, then proceed to payment."}
                  </p>
                  {!event.allow_multiple_vote_purchase && (
                    <button
                      onClick={handlePayment}
                      className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium transition-colors"
                    >
                      Pay Now
                    </button>
                  )}
                </div>
              </div>
            )}

          {!isVotingOpen && !hasVoted && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-start gap-3">
              <Clock className="text-gray-600 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-bold text-gray-900 mb-1">Voting Closed</h3>
                <p className="text-gray-700 text-sm">
                  Voting for this event is currently closed.
                </p>
              </div>
            </div>
          )}
        </motion.section>
      )}

      {/* Candidate Registration Section - Show when registration is open */}
      {isRegistrationOpen && (
        <motion.section
          variants={fadeIn("up", 0.3)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        >
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-green-100 rounded-full">
                  <UserPlus className="text-green-600" size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-green-900 mb-1">
                    {userCandidacy ? "Your Candidacy Status" : "Candidate Registration Open!"}
                  </h3>
                  {userCandidacy ? (
                    <div>
                      <p className="text-green-700">
                        You have registered as a candidate for this event.
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-sm text-gray-600">Status:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          userCandidacy.status === 'approved' 
                            ? 'bg-green-100 text-green-800'
                            : userCandidacy.status === 'pending'
                            ? 'bg-amber-100 text-amber-800'
                            : userCandidacy.status === 'rejected'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {userCandidacy.status === 'approved' && '✓ Approved'}
                          {userCandidacy.status === 'pending' && '⏳ Pending Approval'}
                          {userCandidacy.status === 'rejected' && '✗ Rejected'}
                          {userCandidacy.status === 'disqualified' && '⚠ Disqualified'}
                        </span>
                      </div>
                      {userCandidacy.category_name && (
                        <p className="text-sm text-gray-600 mt-1">
                          Category: <strong>{userCandidacy.category_name}</strong>
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-green-700">
                      Want to run for a position? Register now to become a candidate.
                    </p>
                  )}
                  {!userCandidacy && event.registration_end_date && (
                    <p className="text-sm text-green-600 mt-2">
                      Registration closes: {formatDate(event.registration_end_date)}
                    </p>
                  )}
                </div>
              </div>
              {!userCandidacy && (
                user ? (
                  <button
                    onClick={() => setIsRegistrationModalOpen(true)}
                    className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 font-medium flex items-center gap-2 transition-all transform hover:scale-105 shadow-lg"
                  >
                    <UserPlus size={20} />
                    Register as Candidate
                  </button>
                ) : (
                  <button
                    onClick={() => setIsLoginModalOpen(true)}
                    className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 font-medium flex items-center gap-2 transition-all"
                  >
                    Login to Register
                  </button>
                )
              )}
            </div>
          </div>
        </motion.section>
      )}

      {/* Login Required - Only show if event requires authentication and user is not logged in */}
      {!user && isVotingOpen && event.requires_authentication && (
        <motion.section
          variants={fadeIn("up", 0.3)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        >
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="text-blue-600 flex-shrink-0" size={24} />
            <div className="flex-1">
              <h3 className="font-bold text-blue-900 mb-1">Login Required</h3>
              <p className="text-blue-700 text-sm mb-3">
                Please login to participate in this voting event.
              </p>
              <button
                onClick={() => setIsLoginModalOpen(true)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Login to Vote
              </button>
            </div>
          </div>
        </motion.section>
      )}

      {/* Voting Instructions */}
      {/* Voting Instructions / Status */}
      {isPollEvent && pollOptions && (
        <motion.section
          variants={fadeIn("up", 0.35)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4"
        >
          {(() => {
            // Calculate total categories and voted categories
            const totalCategories = pollOptions.options 
              ? 1 // Single-question poll
              : Object.keys(pollOptions).length; // Multi-question poll
            const votedCount = votedCategories.length;
            const allVoted = votedCount >= totalCategories && totalCategories > 0;
            const someVoted = votedCount > 0 && votedCount < totalCategories;
            const noneVoted = votedCount === 0;

            // All categories voted - Thank You message
            if (allVoted) {
              return (
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-green-900 mb-3 flex items-center gap-2">
                    <CheckCircle className="text-green-600" size={24} />
                    Thank You for Voting!
                  </h3>
                  <p className="text-green-800 mb-2">
                    You have successfully voted in all {totalCategories} {totalCategories === 1 ? 'category' : 'categories'} of this {event.event_type}.
                  </p>
                  <p className="text-sm text-green-700">
                    Your responses have been recorded. {event.show_live_results ? 'You can view the live results below.' : 'Results will be published after voting closes.'}
                  </p>
                </div>
              );
            }

            // Some categories voted - Partial completion message
            if (someVoted) {
              const remainingCount = totalCategories - votedCount;
              return (
                <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-amber-900 mb-3 flex items-center gap-2">
                    <AlertCircle className="text-amber-600" size={24} />
                    Voting in Progress
                  </h3>
                  <p className="text-amber-800 mb-2">
                    You have voted in <strong>{votedCount}</strong> out of <strong>{totalCategories}</strong> {totalCategories === 1 ? 'category' : 'categories'}.
                  </p>
                  <p className="text-sm text-amber-700">
                    {remainingCount} {remainingCount === 1 ? 'category remains' : 'categories remain'}. Continue voting below to complete your participation.
                  </p>
                </div>
              );
            }

            // No categories voted yet - Show instructions (only if can vote)
            if (noneVoted && canSelectCandidates) {
              return (
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-indigo-900 mb-3 flex items-center gap-2">
                    <VoteIcon className="text-indigo-600" size={24} />
                    How to Participate
                  </h3>
                  <ol className="list-decimal list-inside space-y-2 text-indigo-800">
                    <li className="text-sm">
                      <strong>Read the {event.event_type === 'referendum' ? 'referendum' : 'poll'} question(s):</strong> Review the options carefully before making your choice
                    </li>
                    <li className="text-sm">
                      <strong>Select your choice:</strong> Click on the option that best represents your opinion
                    </li>
                    <li className="text-sm">
                      <strong>Submit your vote:</strong> Click the "Submit Vote" button to record your choice
                    </li>
                    {requiresPayment && (
                      <li className="text-sm">
                        <strong>Payment:</strong> You'll be redirected to complete payment of GHS {parseFloat(event.voting_fee || 0).toFixed(2)}
                      </li>
                    )}
                  </ol>
                  {Object.keys(selectedVotes).length === 0 && (
                    <div className="mt-4 p-3 bg-white rounded-lg border border-indigo-200">
                      <p className="text-sm text-indigo-700 font-medium">
                        ℹ️ No option selected yet. Click on an option below to begin.
                      </p>
                    </div>
                  )}
                </div>
              );
            }

            return null;
          })()}
        </motion.section>
      )}

      {/* Non-Poll Voting Instructions */}
      {!isPollEvent && canSelectCandidates && Object.keys(candidates).length > 0 && (
        <motion.section
          variants={fadeIn("up", 0.35)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4"
        >
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
            <h3 className="text-lg font-bold text-indigo-900 mb-3 flex items-center gap-2">
              <VoteIcon className="text-indigo-600" size={24} />
              How to Vote
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-indigo-800">
              <li className="text-sm">
                <strong>Select your candidates:</strong> Click the "Select" button on your preferred candidate in each category
              </li>
              <li className="text-sm">
                <strong>Review your selections:</strong> Selected candidates will show a blue border and "Selected" badge
              </li>
              <li className="text-sm">
                <strong>Submit your vote:</strong> Click the "Submit Votes" button that appears at the bottom of the page
              </li>
              {requiresPayment && (
                <li className="text-sm">
                  <strong>Payment:</strong> You'll be redirected to complete payment of GHS {parseFloat(event.voting_fee || 0).toFixed(2)}
                </li>
              )}
            </ol>
            {Object.keys(selectedVotes).length === 0 && (
              <div className="mt-4 p-3 bg-white rounded-lg border border-indigo-200">
                <p className="text-sm text-indigo-700 font-medium">
                  ℹ️ No candidates selected yet. Click "Select" on any candidate below to begin voting.
                </p>
              </div>
            )}
          </div>
        </motion.section>
      )}

      {/* Poll/Referendum Content */}
      {isPollEvent && (
        <motion.section
          variants={fadeIn("up", 0.4)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-screen"
        >
          {!pollOptions || (pollOptions.options?.length === 0 && Object.keys(pollOptions).length === 0) ? (
            <div className="text-center py-20">
              <VoteIcon size={64} className="mx-auto text-gray-400 mb-4" />
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                No Options Available
              </h3>
              <p className="text-gray-600">
                Poll options will appear here once they are added.
              </p>
            </div>
          ) : pollOptions.options ? (
            // Single-question poll
            <PollQuestionSection
              question={pollOptions.question || event.title}
              description={pollOptions.description || event.description}
              options={pollOptions.options || []}
              selectedOption={selectedVotes[event.title]?.option}
              onSelectOption={(option) => handlePollOptionSelect(event.title, option)}
              canVote={canSelectCandidates && !votedCategories.includes(event.title)}
              hasVotedInCategory={votedCategories.includes(event.title)}
              showResults={event.show_live_results}
              eventType={event.event_type}
            />
          ) : (
            // Multi-question poll (grouped by categories)
            Object.entries(pollOptions).map(([questionName, questionData]) => (
              <PollQuestionSection
                key={questionData.category_id || questionName}
                question={questionData.question || questionName}
                description={questionData.description}
                options={questionData.options || []}
                selectedOption={selectedVotes[questionName]?.option}
                onSelectOption={(option) => handlePollOptionSelect(questionName, option)}
                canVote={canSelectCandidates && !votedCategories.includes(questionName)}
                hasVotedInCategory={votedCategories.includes(questionName)}
                showResults={event.show_live_results}
                eventType={event.event_type}
              />
            ))
          )}

          {/* Poll Submit Button */}
          {canSelectCandidates && Object.keys(selectedVotes).length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-purple-600 to-indigo-600 border-t-4 border-purple-700 shadow-2xl p-5 z-50"
            >
              <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="text-white">
                  <p className="font-bold text-lg flex items-center gap-2">
                    <CheckCircle size={24} />
                    {Object.keys(selectedVotes).length} selection{Object.keys(selectedVotes).length > 1 ? "s" : ""} made
                  </p>
                  <p className="text-sm text-purple-100">
                    {requiresPayment
                      ? `Payment Required: GHS ${parseFloat(event.voting_fee || 0).toFixed(2)}`
                      : "Ready to submit your vote"}
                  </p>
                </div>
                <button
                  onClick={handleSubmitVotes}
                  disabled={voting}
                  className="px-10 py-4 bg-white text-purple-600 rounded-lg hover:bg-purple-50 font-bold text-lg flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all shadow-lg"
                >
                  {voting ? (
                    <>
                      <Loader className="animate-spin" size={24} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <VoteIcon size={24} />
                      {requiresPayment
                        ? `Pay GHS ${parseFloat(event.voting_fee || 0).toFixed(2)}`
                        : "Submit Vote"}
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          )}
        </motion.section>
      )}

      {/* Candidates by Category (Election/Awards only) */}
      {!isPollEvent && (
        <motion.section
          variants={fadeIn("up", 0.4)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-screen"
        >
        {Object.keys(candidates).length === 0 ? (
          <div className="text-center py-20">
            <Users size={64} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              No Candidates Yet
            </h3>
            <p className="text-gray-600">
              Candidates will appear here once they register.
            </p>
          </div>
        ) : (
          Object.entries(candidates).map(
            ([categoryName, categoryCanDidates]) => (
              <div key={categoryName} className="mb-12">
                <div className="flex items-center gap-3 mb-6">
                  <Award className="text-indigo-600" size={28} />
                  <h2 className="text-2xl font-bold text-gray-900">
                    {categoryName}
                  </h2>
                  <span className="text-gray-500">
                    ({categoryCanDidates.length} candidates)
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {categoryCanDidates.map((candidate) => {
                    const voteData = selectedVotes[categoryName];
                    const isThisCandidateSelected =
                      voteData?.candidate?.id === candidate.id;

                    return (
                      <CandidateCard
                        key={candidate.id}
                        candidate={candidate}
                        onVote={
                          canSelectCandidates
                            ? () => handleVoteSelection(categoryName, candidate)
                            : null
                        }
                        onViewDetails={handleViewCandidateDetails}
                        isSelected={isThisCandidateSelected}
                        voteQuantity={
                          isThisCandidateSelected ? voteData.quantity : 1
                        }
                        onQuantityChange={
                          isThisCandidateSelected
                            ? (qty) => handleQuantityChange(categoryName, qty)
                            : null
                        }
                        allowMultipleVotes={event.allow_multiple_vote_purchase}
                        pricePerVote={parseFloat(event.voting_fee || 0)}
                        hasVoted={hasVoted}
                        showVoteCount={
                          event.show_live_results ||
                          event.status === "results_published"
                        }
                      />
                    );
                  })}
                </div>
              </div>
            )
          )
        )}

        {/* Submit Votes Button */}
        {canSelectCandidates &&
          Object.keys(selectedVotes).length > 0 &&
          (() => {
            const totalVotes = Object.values(selectedVotes).reduce(
              (sum, vote) => sum + vote.quantity,
              0
            );
            const totalAmount = Object.values(selectedVotes).reduce(
              (sum, vote) => {
                return sum + vote.quantity * parseFloat(event.voting_fee || 0);
              },
              0
            );

            return (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-indigo-600 to-purple-600 border-t-4 border-indigo-700 shadow-2xl p-5 z-50"
              >
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="text-white">
                    <p className="font-bold text-lg flex items-center gap-2">
                      <CheckCircle size={24} />
                      {totalVotes} vote{totalVotes > 1 ? "s" : ""} for{" "}
                      {Object.keys(selectedVotes).length} candidate
                      {Object.keys(selectedVotes).length > 1 ? "s" : ""}
                    </p>
                    <p className="text-sm text-indigo-100">
                      {requiresPayment
                        ? `Total Payment: GHS ${totalAmount.toFixed(2)}`
                        : "Ready to submit your votes"}
                    </p>
                  </div>
                  <button
                    onClick={handleSubmitVotes}
                    disabled={voting}
                    className="px-10 py-4 bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 font-bold text-lg flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all shadow-lg"
                  >
                    {voting ? (
                      <>
                        <Loader className="animate-spin" size={24} />
                        Processing...
                      </>
                    ) : (
                      <>
                        <VoteIcon size={24} />
                        {requiresPayment
                          ? `Pay GHS ${totalAmount.toFixed(2)}`
                          : `Submit ${totalVotes} Vote${
                              totalVotes > 1 ? "s" : ""
                            }`}
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            );
          })()}
      </motion.section>
      )}

      <Footer />

      {/* Auth Modals */}
      {isLoginModalOpen && (
        <Login
          onClose={() => setIsLoginModalOpen(false)}
          switchToSignup={() => {
            setIsLoginModalOpen(false);
            setIsSignupModalOpen(true);
          }}
          action={() => setIsLoginModalOpen(false)}
        />
      )}

      {isSignupModalOpen && (
        <SignUp
          onClose={() => setIsSignupModalOpen(false)}
          switchToLogin={() => {
            setIsSignupModalOpen(false);
            setIsLoginModalOpen(true);
          }}
        />
      )}

      {/* Payment Modal */}
      {paymentData && (
        <PaymentModal
          isOpen={isPaymentModalOpen}
          onClose={() => {
            setIsPaymentModalOpen(false);
            setVoting(false);
          }}
          totalVotes={paymentData.totalVotes}
          totalAmount={paymentData.totalAmount}
          currency={paymentData.currency}
          eventTitle={paymentData.eventTitle}
          requiresPayment={paymentData.requiresPayment}
          isAnonymous={paymentData.isAnonymous}
          onSubmit={handlePaymentSubmit}
        />
      )}

      {/* Candidate Registration Modal */}
      {event && (
        <CandidateRegistrationModal
          isOpen={isRegistrationModalOpen}
          onClose={() => setIsRegistrationModalOpen(false)}
          event={event}
          categories={event.categories || []}
          onSuccess={() => {
            setIsRegistrationModalOpen(false);
            fetchEventDetails(); // Refresh data
          }}
        />
      )}

      {/* Candidate Detail Modal */}
      <CandidateDetailModal
        isOpen={isCandidateDetailOpen}
        onClose={() => {
          setIsCandidateDetailOpen(false);
          setSelectedCandidate(null);
        }}
        candidate={selectedCandidate}
        onVote={(candidate) => {
          // Find the category for this candidate
          const categoryEntry = Object.entries(candidates).find(([, cats]) =>
            cats.some((c) => c.id === candidate.id)
          );
          if (categoryEntry) {
            handleVoteSelection(categoryEntry[0], candidate);
          }
        }}
        isSelected={
          selectedCandidate
            ? Object.values(selectedVotes).some(
                (v) => v.candidate?.id === selectedCandidate.id
              )
            : false
        }
        canVote={canSelectCandidates}
        hasVoted={hasVoted}
        showVoteCount={
          event?.show_live_results || event?.status === "results_published"
        }
      />
    </>
  );
}
