import { useEffect, useState, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Helmet } from "react-helmet-async";
import {
  Calendar,
  MapPin,
  Users,
  Clock,
  ArrowLeft,
  Share2,
  CheckCircle,
  AlertCircle,
  CreditCard,
  Ticket,
  Loader,
  ExternalLink,
  Check,
  Zap,
  Copy,
  X,
  AlertTriangle,
} from "lucide-react";
import { UserContext } from "../Context/UserContext";
import { getEventById, getEventPackages, getMyRegistration } from "../services/eventService";
import api from "../services/api";
import { toast } from "react-hot-toast";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";
import Login from "./Login";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";
import EventRegistrationModal from "../Components/Events/EventRegistrationModal";
import { scrollToTop } from "../utils/scrollToTop";

export default function EventDetailPage() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  const [event, setEvent] = useState(null);
  const [packages, setPackages] = useState([]);
  const [myRegistration, setMyRegistration] = useState(null);
  const [myRsvp, setMyRsvp] = useState(null);
  const [rsvpLoading, setRsvpLoading] = useState(false);
  const [paymentTimeLeft, setPaymentTimeLeft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);
  const [isExecutiveLoginOpen, setIsExecutiveLoginOpen] = useState(false);
  const [isRegistrationModalOpen, setIsRegistrationModalOpen] = useState(false);
  const [isPendingPaymentModalOpen, setIsPendingPaymentModalOpen] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState(null);

  // Fetch event data
  const fetchEventData = async () => {
    setLoading(true);
    try {
      const { response: eventData, error: eventError } = await getEventById(eventId);
      if (eventError) {
        setError("Failed to load event details");
        return;
      }
      setEvent(eventData);

      // Fetch packages if event requires payment
      if (eventData?.payment?.required) {
        const { response: packagesData } = await getEventPackages(eventId);
        if (packagesData) {
          // Handle paginated response
          const packagesList = packagesData.results || packagesData;
          setPackages(packagesList);
        }
      }

      // Fetch user's registration if logged in
      if (user) {
        const { response: regData } = await getMyRegistration(eventId);
        if (regData) {
          setMyRegistration(regData);
        }
      }
    } catch (err) {
      setError("An error occurred while loading the event" , err);
    } finally {
      setLoading(false);
    }
  };

  // Only fetch when eventId changes, not when user object reference changes
  useEffect(() => {
    scrollToTop();
    fetchEventData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);
  
  // Fetch user's registration when user logs in/out
  useEffect(() => {
    if (user && event) {
      // Only fetch registration data, not the entire event
      const fetchUserRegistration = async () => {
        const { response: regData } = await getMyRegistration(eventId);
        if (regData) {
          setMyRegistration(regData);
        } else {
          setMyRegistration(null);
        }
      };
      fetchUserRegistration();
    } else if (!user) {
      setMyRegistration(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, event?.id]);

  // Fetch RSVP status when event data loads
  useEffect(() => {
    if (event && user && event.allows_rsvp) {
      fetchMyRsvp();
    }
    // Using specific IDs to prevent re-fetching when object references change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event?.id, user?.id]);

  // Show pending payment modal when registration needs payment (only once per registration)
  const [hasShownPaymentModal, setHasShownPaymentModal] = useState(false);
  
  useEffect(() => {
    // Only show once per pending registration, and not if modal is already open
    if (myRegistration && 
        myRegistration.status === "pending_payment" && 
        parseFloat(myRegistration.payment_info?.balance_due) > 0 &&
        !hasShownPaymentModal &&
        !isPendingPaymentModalOpen) {
      // Show payment modal after a short delay to let the page load
      const timer = setTimeout(() => {
        setIsPendingPaymentModalOpen(true);
        setHasShownPaymentModal(true);
      }, 1500);
      
      return () => clearTimeout(timer);
    }
    
    // Reset the flag when registration changes or is cleared
    if (!myRegistration || myRegistration.status !== "pending_payment") {
      setHasShownPaymentModal(false);
    }
    // Using specific properties to prevent loop when registration object updates
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [myRegistration?.id, myRegistration?.status, hasShownPaymentModal, isPendingPaymentModalOpen]);

  // Payment countdown timer
  const [timerExpired, setTimerExpired] = useState(false);
  
  useEffect(() => {
    if (!myRegistration || myRegistration.status !== "pending_payment") {
      setPaymentTimeLeft(null);
      setTimerExpired(false);
      return;
    }

    const calculateTimeLeft = () => {
      const createdAt = new Date(myRegistration.created_at);
      const expiresAt = new Date(createdAt.getTime() + (24 * 60 * 60 * 1000)); // 24 hours
      const now = new Date();
      const timeLeft = expiresAt - now;
      
      if (timeLeft <= 0) {
        return null; // Expired
      }
      
      const hours = Math.floor(timeLeft / (1000 * 60 * 60));
      const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
      
      return { hours, minutes, seconds, total: timeLeft };
    };

    // Initial calculation
    setPaymentTimeLeft(calculateTimeLeft());

    // Update every second
    const interval = setInterval(() => {
      const timeLeft = calculateTimeLeft();
      setPaymentTimeLeft(timeLeft);
      
      // Mark as expired when timer runs out (only once)
      if (!timeLeft && !timerExpired) {
        setTimerExpired(true);
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
    // Using specific properties to prevent timer reset on unrelated registration updates
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [myRegistration?.id, myRegistration?.created_at, myRegistration?.status, timerExpired]);
  
  // Handle expired timer separately to avoid loop
  useEffect(() => {
    if (timerExpired) {
      // Clear registration state since it's expired
      setMyRegistration(null);
      setIsPendingPaymentModalOpen(false);
      setTimerExpired(false);
    }
  }, [timerExpired]);

  // RSVP functions
  const handleRsvp = async (rsvpStatus, reminder = 'none', notes = '') => {
    // Debug logging
    console.log('HandleRSVP called with:', { rsvpStatus, reminder, notes, eventId, user: !!user, event: !!event });
    
    // Prevent multiple simultaneous calls
    if (rsvpLoading) {
      console.log('RSVP already in progress, skipping');
      return;
    }
    
    // Validate required parameters
    if (!rsvpStatus) {
      console.error('RSVP status is required');
      toast.error('RSVP status is required');
      return;
    }
    
    if (!eventId) {
      console.error('Event ID is missing');
      toast.error('Event ID is missing');
      return;
    }
    
    if (!user) {
      handleOpenLoginModal();
      return;
    }

    if (!event) {
      toast.error('Event data not loaded yet, please wait...');
      return;
    }

    if (!event.allows_rsvp) {
      toast.error('RSVP is not allowed for this event');
      return;
    }

    if (event.is_past) {
      toast.error('Cannot RSVP to past events');
      return;
    }

    setRsvpLoading(true);
    try {
      console.log('Sending RSVP request:', {
        url: `/events/${eventId}/rsvp/`,
        data: { status: rsvpStatus, reminder, notes }
      });
      
      const response = await api.post(`/events/${eventId}/rsvp/`, {
        status: rsvpStatus,
        reminder: reminder,
        notes: notes
      });

      console.log('RSVP response:', response.data);

      if (response.data && response.data.success) {
        // Update local RSVP state
        setMyRsvp({
          status: rsvpStatus,
          reminder: reminder,
          notes: notes,
          created_at: new Date().toISOString()
        });
        
        // Show success message
        toast.success(response.data.message || `RSVP updated to ${rsvpStatus}`);
      }
    } catch (error) {
      console.error('RSVP error:', error);
      console.error('Error response data:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Error headers:', error.response?.headers);
      
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to update RSVP';
      toast.error(errorMessage);
    } finally {
      setRsvpLoading(false);
    }
  };

  const fetchMyRsvp = async () => {
    if (!user) return;
    
    try {
      // Get current user's RSVP from the event's attendance data
      const userRsvpStatus = event?.attendance?.user_rsvp_status;
      if (userRsvpStatus && userRsvpStatus !== 'none') {
        setMyRsvp({ status: userRsvpStatus });
      }
    } catch (error) {
      console.error('Error fetching RSVP:', error);
    }
  };

  // Modal handlers
  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsForgotPasswordOpen(false);
    setIsExecutiveLoginOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsForgotPasswordOpen(false);
    setIsExecutiveLoginOpen(false);
  };

  const handleOpenForgotPassword = () => {
    setIsForgotPasswordOpen(true);
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsExecutiveLoginOpen(false);
  };

  const handleOpenExecutiveLogin = () => {
    setIsExecutiveLoginOpen(true);
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsForgotPasswordOpen(false);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsForgotPasswordOpen(false);
    setIsExecutiveLoginOpen(false);
    setIsPendingPaymentModalOpen(false);
  };

  // Registration handlers
  const handleRegisterClick = (pkg = null) => {
    if (!user) {
      handleOpenLoginModal();
      return;
    }
    setSelectedPackage(pkg);
    setIsRegistrationModalOpen(true);
  };

  const handleRegistrationSuccess = (registration) => {
    setMyRegistration(registration);
    setIsRegistrationModalOpen(false);
    fetchEventData(); // Refresh data
  };

  // Handle payment cancellation - remove the pending registration
  const handlePaymentCancel = async () => {
    if (!myRegistration || !user) return;
    
    try {
      const confirmCancel = window.confirm(
        "Are you sure you want to cancel this registration? You'll need to register again if you change your mind."
      );
      
      if (!confirmCancel) return;
      
      // Call API to cancel/delete the registration
      const response = await api.delete(`/events/${eventId}/my-registration/`);
      
      if (response.data.success) {
        setMyRegistration(null);
        setIsPendingPaymentModalOpen(false);
        toast.success("Registration cancelled successfully");
      }
    } catch (error) {
      console.error('Error cancelling registration:', error);
      toast.error("Failed to cancel registration. Please try again.");
    }
  };

  // Helper functions
  const formatDate = (dateString) => {
    if (!dateString) return "TBD";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = () => {
    if (!event) return null;
    const status = event.event_status;
    const configs = {
      ongoing: {
        bg: "bg-green-100",
        text: "text-green-700",
        icon: <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />,
        label: "Ongoing",
      },
      upcoming: {
        bg: "bg-blue-100",
        text: "text-blue-700",
        icon: <Calendar className="w-4 h-4" />,
        label: "Upcoming",
      },
      past: {
        bg: "bg-gray-100",
        text: "text-gray-700",
        icon: <CheckCircle className="w-4 h-4" />,
        label: "Past Event",
      },
    };
    const config = configs[status] || configs.upcoming;
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 ${config.bg} ${config.text} rounded-full text-sm font-semibold`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

  const getRegistrationStatusBadge = () => {
    if (!myRegistration) return null;
    const configs = {
      pending: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Pending" },
      pending_payment: { bg: "bg-orange-100", text: "text-orange-700", label: "Awaiting Payment" },
      confirmed: { bg: "bg-green-100", text: "text-green-700", label: "Confirmed" },
      cancelled: { bg: "bg-red-100", text: "text-red-700", label: "Cancelled" },
      waitlist: { bg: "bg-purple-100", text: "text-purple-700", label: "Waitlisted" },
      refunded: { bg: "bg-gray-100", text: "text-gray-700", label: "Refunded" },
    };
    const config = configs[myRegistration.status] || configs.pending;
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 ${config.bg} ${config.text} rounded-full text-sm font-semibold`}>
        {config.label}
      </span>
    );
  };

  const getRsvpStatusBadge = () => {
    if (!myRsvp) return null;

    const statusConfig = {
      attending: { color: 'bg-green-100 text-green-800', icon: '✓', text: 'Attending' },
      maybe: { color: 'bg-yellow-100 text-yellow-800', icon: '?', text: 'Maybe' },
      not_attending: { color: 'bg-red-100 text-red-800', icon: '✗', text: 'Not Attending' },
    };

    const config = statusConfig[myRsvp.status] || { color: 'bg-gray-100 text-gray-800', icon: '', text: 'Unknown' };
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        <span className="mr-1">{config.icon}</span>
        {config.text}
      </span>
    );
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-16 h-16 text-red-500" />
        <h1 className="text-2xl font-bold text-gray-900">{error || "Event not found"}</h1>
        <button onClick={() => navigate("/events")} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Back to Events
        </button>
      </div>
    );
  }

  const isRegistrationOpen = event.registration?.is_open && !event.registration?.is_full;
  const requiresPayment = event.payment?.required;
  const isEarlyBird = event.payment?.is_early_bird_active;

  return (
    <>
      <Helmet>
        <title>{event.event_name} | BIO-CHEM KNUST</title>
        <meta name="description" content={event.description?.slice(0, 160)} />
        <meta property="og:title" content={`${event.event_name} | BIO-CHEM KNUST`} />
        <meta property="og:description" content={event.description?.slice(0, 160)} />
        {event.event_image_1 && <meta property="og:image" content={event.event_image_1} />}
      </Helmet>

      <div className="relative mt-[70px] min-h-screen bg-gray-50">
        <Navbar onSignInClick={handleOpenLoginModal} />

        {/* Hero Section */}
        <div className="relative h-[300px] md:h-[400px] overflow-hidden">
          {event.event_image_1 ? (
            <img src={event.event_image_1} alt={event.event_name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-r from-blue-600 to-purple-600" />
          )}
          <div className="absolute inset-0 bg-black/50" />
          <div className="absolute inset-0 flex items-end">
            <div className="max-w-6xl mx-auto px-4 pb-8 w-full">
              <button onClick={() => navigate("/events")} className="flex items-center gap-2 text-white/80 hover:text-white mb-4 transition-colors">
                <ArrowLeft className="w-5 h-5" />
                Back to Events
              </button>
              <div className="flex flex-wrap items-center gap-3 mb-3">
                {getStatusBadge()}
                {requiresPayment && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-semibold">
                    <CreditCard className="w-4 h-4" />
                    Paid Event
                  </span>
                )}
                {isEarlyBird && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold animate-pulse">
                    <Zap className="w-4 h-4" />
                    Early Bird Active!
                  </span>
                )}
              </div>
              <h1 className="text-3xl md:text-5xl font-bold text-white mb-2">{event.event_name}</h1>
              <p className="text-white/80 text-lg">Organized by {event.organised_by}</p>
            </div>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Description */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">About This Event</h2>
                <p className="text-gray-600 leading-relaxed whitespace-pre-line">{event.description}</p>
              </motion.div>

              {/* Event Details */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Event Details</h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Calendar className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">Date</p>
                      <p className="text-gray-600">{formatDate(event.event_date)}</p>
                      {event.event_end_date && <p className="text-gray-500 text-sm">to {formatDate(event.event_end_date)}</p>}
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Clock className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">Time</p>
                      <p className="text-gray-600">{formatTime(event.event_date)}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <MapPin className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">Location</p>
                      <p className="text-gray-600">{event.location?.venue || "TBD"}</p>
                      {event.location?.building && <p className="text-gray-500 text-sm">{event.location.building}</p>}
                      {event.location?.type === "virtual" && event.location?.virtual_link && (
                        <a href={event.location.virtual_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm flex items-center gap-1 mt-1">
                          Join Online <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-orange-100 rounded-lg">
                      <Users className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">Capacity</p>
                      <p className="text-gray-600">
                        {event.attendance?.total_attending || 0}
                        {event.attendance?.capacity && ` / ${event.attendance.capacity}`} attending
                      </p>
                      {event.registration?.is_full && <p className="text-red-500 text-sm font-medium">Event is full</p>}
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Payment Packages */}
              {requiresPayment && packages.length > 0 && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Registration Packages</h2>
                    {isEarlyBird && (
                      <span className="text-sm text-green-600 font-medium">
                        Early bird ends {formatDate(event.payment?.early_bird_deadline)}
                      </span>
                    )}
                  </div>

                  {event.payment?.description && <p className="text-gray-600 mb-6">{event.payment.description}</p>}

                  <div className="grid md:grid-cols-2 gap-4">
                    {packages.map((pkg) => (
                      <div
                        key={pkg.id}
                        className={`relative border-2 rounded-xl p-6 transition-all ${
                          pkg.is_featured ? "border-blue-500 shadow-lg" : "border-gray-200 hover:border-blue-300"
                        } ${!pkg.is_available ? "opacity-60" : ""}`}
                      >
                        {pkg.is_featured && (
                          <span className="absolute -top-3 left-4 px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full">Most Popular</span>
                        )}

                        <h3 className="text-lg font-bold text-gray-900 mb-2">{pkg.name}</h3>
                        {pkg.description && <p className="text-gray-600 text-sm mb-4">{pkg.description}</p>}

                        <div className="mb-4">
                          {isEarlyBird && pkg.early_bird_price ? (
                            <div className="flex items-baseline gap-2">
                              <span className="text-2xl font-bold text-green-600">GH₵{pkg.early_bird_price}</span>
                              <span className="text-gray-400 line-through">GH₵{pkg.price}</span>
                            </div>
                          ) : (
                            <span className="text-2xl font-bold text-gray-900">GH₵{pkg.price}</span>
                          )}
                        </div>

                        {pkg.benefits && pkg.benefits.length > 0 && (
                          <ul className="space-y-2 mb-4">
                            {pkg.benefits.map((benefit, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                {benefit}
                              </li>
                            ))}
                          </ul>
                        )}

                        {pkg.max_slots && (
                          <p className="text-sm text-gray-500 mb-4">
                            {pkg.slots_remaining} of {pkg.max_slots} slots remaining
                          </p>
                        )}

                        <button
                          onClick={() => handleRegisterClick(pkg)}
                          disabled={!pkg.is_available || myRegistration}
                          className={`w-full py-3 rounded-lg font-semibold transition-colors ${
                            !pkg.is_available || myRegistration
                              ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                              : pkg.is_featured
                              ? "bg-blue-600 text-white hover:bg-blue-700"
                              : "bg-gray-900 text-white hover:bg-gray-800"
                          }`}
                        >
                          {myRegistration ? "Already Registered" : !pkg.is_available ? "Sold Out" : "Select Package"}
                        </button>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Registration Card */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-xl shadow-sm p-6 sticky top-24">
                {myRegistration ? (
                  // Show registration status
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-gray-900">Your Registration</h3>
                      {getRegistrationStatusBadge()}
                    </div>

                    <div className="space-y-3 mb-4">
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-gray-600">Registration #</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-medium">{myRegistration.registration_number}</span>
                          <button onClick={() => copyToClipboard(myRegistration.registration_number)} className="text-gray-400 hover:text-gray-600">
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {myRegistration.payment_package && (
                        <div className="flex items-center justify-between py-2 border-b">
                          <span className="text-gray-600">Package</span>
                          <span className="font-medium">{myRegistration.payment_info?.package_name}</span>
                        </div>
                      )}

                      {requiresPayment && (
                        <>
                          <div className="flex items-center justify-between py-2 border-b">
                            <span className="text-gray-600">Amount Due</span>
                            <span className="font-medium">GH₵{myRegistration.payment_info?.amount_due}</span>
                          </div>
                          <div className="flex items-center justify-between py-2 border-b">
                            <span className="text-gray-600">Amount Paid</span>
                            <span className="font-medium text-green-600">GH₵{myRegistration.payment_info?.amount_paid}</span>
                          </div>
                          {parseFloat(myRegistration.payment_info?.balance_due) > 0 && (
                            <div className="flex items-center justify-between py-2 border-b">
                              <span className="text-gray-600">Balance</span>
                              <span className="font-medium text-orange-600">GH₵{myRegistration.payment_info?.balance_due}</span>
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {/* Payment progress bar */}
                    {requiresPayment && (
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Payment Progress</span>
                          <span className="font-medium">{myRegistration.payment_info?.payment_percentage}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              myRegistration.payment_info?.is_fully_paid ? "bg-green-500" : "bg-blue-500"
                            }`}
                            style={{ width: `${myRegistration.payment_info?.payment_percentage}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Complete payment button */}
                    {myRegistration.status === "pending_payment" && parseFloat(myRegistration.payment_info?.balance_due) > 0 && (
                      <>
                        {/* Payment countdown timer */}
                        {paymentTimeLeft && (
                          <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                            <div className="flex items-center gap-2 text-orange-800">
                              <Clock className="w-4 h-4" />
                              <span className="text-sm font-medium">
                                Payment expires in: 
                                <span className="ml-1 font-mono text-orange-600">
                                  {String(paymentTimeLeft.hours).padStart(2, '0')}:
                                  {String(paymentTimeLeft.minutes).padStart(2, '0')}:
                                  {String(paymentTimeLeft.seconds).padStart(2, '0')}
                                </span>
                              </span>
                            </div>
                          </div>
                        )}
                        
                        <button
                          onClick={() => handleRegisterClick(null)}
                          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                        >
                          <CreditCard className="w-5 h-5" />
                          Complete Payment
                        </button>
                      </>
                    )}

                    {myRegistration.status === "confirmed" && (
                      <div className="flex items-center gap-2 text-green-600 bg-green-50 p-4 rounded-lg">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">You&apos;re all set! See you there.</span>
                      </div>
                    )}
                  </div>
                ) : (
                  // Show registration button
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      {event.registration?.required ? "Register for this Event" : "Interested in this Event?"}
                    </h3>

                    {event.registration?.required ? (
                      <>
                        {requiresPayment && event.payment?.lowest_price && (
                          <div className="mb-4">
                            <span className="text-gray-600">Starting from</span>
                            <p className="text-3xl font-bold text-gray-900">GH₵{event.payment.lowest_price}</p>
                          </div>
                        )}

                        {event.registration?.deadline && (
                          <p className="text-sm text-gray-600 mb-4">
                            <Clock className="w-4 h-4 inline mr-1" />
                            Registration closes {formatDate(event.registration.deadline)}
                          </p>
                        )}

                        {isRegistrationOpen ? (
                          <button
                            onClick={() => handleRegisterClick(null)}
                            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                          >
                            <Ticket className="w-5 h-5" />
                            {requiresPayment ? "Register & Pay" : "Register Now"}
                          </button>
                        ) : (
                          <div className="text-center">
                            <p className="text-red-500 font-medium mb-2">
                              {event.registration?.is_full ? "Event is Full" : "Registration Closed"}
                            </p>
                            {event.registration_link && (
                              <a
                                href={event.registration_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline flex items-center justify-center gap-1"
                              >
                                External Registration <ExternalLink className="w-4 h-4" />
                              </a>
                            )}
                          </div>
                        )}

                        {!user && (
                          <p className="text-sm text-gray-500 text-center mt-3">
                            You&apos;ll need to{" "}
                            <button onClick={handleOpenLoginModal} className="text-blue-600 hover:underline">
                              sign in
                            </button>{" "}
                            to register
                          </p>
                        )}
                      </>
                    ) : (
                      // External registration link
                      event.registration_link && (
                        <a
                          href={event.registration_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                        >
                          Register Now <ExternalLink className="w-5 h-5" />
                        </a>
                      )
                    )}
                  </div>
                )}
              </motion.div>

              {/* RSVP Card */}
              {event.allows_rsvp && !event.is_past && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  transition={{ delay: 0.25 }} 
                  className="bg-white rounded-xl shadow-sm p-6"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-green-50 rounded-lg">
                      <Users className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">RSVP</h3>
                      <p className="text-sm text-gray-600">Let us know if you&apos;re coming</p>
                    </div>
                  </div>

                  {myRsvp ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Your Response:</span>
                        {getRsvpStatusBadge()}
                      </div>
                      
                      <div className="text-sm text-gray-600 mb-3">
                        Update your response:
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 mb-4">
                      {user ? "Please let us know if you plan to attend:" : "Sign in to RSVP:"}
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-2 mb-4">
                    <button
                      onClick={() => {
                        console.log('Attending button clicked');
                        handleRsvp('attending');
                      }}
                      disabled={rsvpLoading || !event || !user}
                      className={`p-3 rounded-lg text-center transition-all text-sm font-medium ${
                        myRsvp?.status === 'attending'
                          ? 'bg-green-100 text-green-800 border-2 border-green-300'
                          : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-green-50 hover:text-green-700'
                      } ${rsvpLoading || !event || !user ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="text-lg mb-1">✓</div>
                      <div>Attending</div>
                    </button>
                    
                    <button
                      onClick={() => {
                        console.log('Maybe button clicked');
                        handleRsvp('maybe');
                      }}
                      disabled={rsvpLoading || !event || !user}
                      className={`p-3 rounded-lg text-center transition-all text-sm font-medium ${
                        myRsvp?.status === 'maybe'
                          ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-300'
                          : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-yellow-50 hover:text-yellow-700'
                      } ${rsvpLoading || !event || !user ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="text-lg mb-1">?</div>
                      <div>Maybe</div>
                    </button>
                    
                    <button
                      onClick={() => {
                        console.log('Not attending button clicked');
                        handleRsvp('not_attending');
                      }}
                      disabled={rsvpLoading || !event || !user}
                      className={`p-3 rounded-lg text-center transition-all text-sm font-medium ${
                        myRsvp?.status === 'not_attending'
                          ? 'bg-red-100 text-red-800 border-2 border-red-300'
                          : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-red-50 hover:text-red-700'
                      } ${rsvpLoading || !event || !user ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="text-lg mb-1">✗</div>
                      <div>Can&apos;t attend</div>
                    </button>
                  </div>

                  {event.attendance?.total_attending > 0 && (
                    <div className="text-xs text-gray-500 text-center">
                      {event.attendance.total_attending} people attending
                    </div>
                  )}

                  {!user && (
                    <p className="text-sm text-gray-500 text-center mt-3">
                      <button onClick={handleOpenLoginModal} className="text-blue-600 hover:underline">
                        Sign in
                      </button>{" "}
                      to RSVP for this event
                    </p>
                  )}
                </motion.div>
              )}

              {/* Share Card */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Share Event</h3>
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      navigator.share?.({ title: event.event_name, url: window.location.href });
                    }}
                    className="flex-1 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <Share2 className="w-4 h-4" />
                    Share
                  </button>
                  <button
                    onClick={() => copyToClipboard(window.location.href)}
                    className="flex-1 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Copy Link
                  </button>
                </div>
              </motion.div>
            </div>
          </div>
        </div>

        <Footer />
      </div>

      {/* Modals */}
      {isLoginModalOpen && (
        <Login
          onClose={handleCloseModals}
          switchToSignup={handleOpenSignupModal}
          switchToForgot={handleOpenForgotPassword}
          action={() => {setIsLoginModalOpen(false);}}
          switchToExecutive={handleOpenExecutiveLogin}
        />
      )}

      {isSignupModalOpen && <SignUp onClose={handleCloseModals} switchToLogin={handleOpenLoginModal} />}

      {isForgotPasswordOpen && <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isForgotPasswordOpen} />}

      {isExecutiveLoginOpen && (
        <ExecutiveLogin onClose={handleOpenLoginModal} switchToSignup={handleOpenSignupModal} switchToForgot={handleOpenForgotPassword} />
      )}

      {isRegistrationModalOpen && (
        <EventRegistrationModal
          event={event}
          packages={packages}
          selectedPackage={selectedPackage}
          existingRegistration={myRegistration}
          onClose={() => setIsRegistrationModalOpen(false)}
          onSuccess={handleRegistrationSuccess}
        />
      )}

      {/* Pending Payment Modal */}
      {isPendingPaymentModalOpen && myRegistration && myRegistration.status === "pending_payment" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-orange-500 to-red-500 px-6 py-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white">Payment Required</h3>
                <button
                  onClick={() => setIsPendingPaymentModalOpen(false)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-orange-100 rounded-full">
                  <Clock className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Complete Your Registration</h4>
                  <p className="text-sm text-gray-600">Payment is required to confirm your spot</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Event</span>
                  <span className="font-medium">{event.event_name}</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Registration ID</span>
                  <span className="font-mono text-sm">{myRegistration.registration_number}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Amount Due</span>
                  <span className="font-bold text-lg text-red-600">
                    GH₵ {parseFloat(myRegistration.payment_info?.balance_due || 0).toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-yellow-800 mb-2">
                      <strong>Important:</strong> Your registration will be automatically cancelled if payment 
                      is not completed within 24 hours.
                    </p>
                    {paymentTimeLeft && (
                      <div className="bg-white rounded px-3 py-2 border">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-orange-600" />
                          <span className="text-sm font-medium text-gray-900">
                            Time remaining: 
                            <span className="ml-1 font-mono text-orange-600">
                              {String(paymentTimeLeft.hours).padStart(2, '0')}:
                              {String(paymentTimeLeft.minutes).padStart(2, '0')}:
                              {String(paymentTimeLeft.seconds).padStart(2, '0')}
                            </span>
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setIsPendingPaymentModalOpen(false);
                    handleRegisterClick(null);
                  }}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                  <CreditCard className="w-5 h-5" />
                  Pay Now
                </button>
                <button
                  onClick={handlePaymentCancel}
                  className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel Registration
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </>
  );
}
