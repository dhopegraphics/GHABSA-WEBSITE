import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  MapPin,
  Users,
  Clock,
  Trophy,
  Rocket,
  AlertCircle,
  Loader2,
  ChevronDown,
  Code,
  UserCheck,
  CalendarClock,
} from "lucide-react";
import ParticipantRegistrationForm from "../features/codequest/registration/components/ParticipantRegistrationForm";
import ConsultantRegistrationForm from "../features/codequest/registration/components/ConsultantRegistrationForm";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const CodeQuestPage = () => {
  const [activeTab, setActiveTab] = useState("participant");
  const [loading, setLoading] = useState(true);
  const [eventData, setEventData] = useState(null);
  const [isAvailable, setIsAvailable] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusReason, setStatusReason] = useState("");
  const [hasFetched, setHasFetched] = useState(false);

  // Fetch active CodeQuest event
  useEffect(() => {
    if (hasFetched) return;
    
    const fetchActiveEvent = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/codequest/active-event/`);
        const data = response.data;
        
        setIsAvailable(data.available);
        setStatusMessage(data.message);
        setStatusReason(data.reason);
        setEventData(data.event || data.last_event || null);
        setHasFetched(true);
      } catch (error) {
        console.error("Error fetching CodeQuest event:", error);
        setIsAvailable(false);
        setStatusMessage("Unable to load CodeQuest information. Please try again later.");
        setStatusReason("error");
      } finally {
        setLoading(false);
      }
    };

    fetchActiveEvent();
  }, [hasFetched]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-white animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading Code Quest...</p>
        </div>
      </div>
    );
  }

  // No event available
  if (!isAvailable && statusReason !== "coming_soon") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <NoEventState 
          reason={statusReason} 
          message={statusMessage} 
          lastEvent={eventData}
        />
      </div>
    );
  }

  // Coming soon state
  if (statusReason === "coming_soon" && eventData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <ComingSoonState event={eventData} />
      </div>
    );
  }

  // Active event - show full page
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section with Event Info */}
      <HeroSection event={eventData} />

      {/* Event Details Section */}
      <EventInfoSection event={eventData} />

      {/* Registration Section - Only show if registration is open */}
      {eventData?.registration_status === "open" && (
        <section className="py-16">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              {/* Tab Switcher */}
              <div className="flex gap-4 mb-8">
                <TabButton
                  active={activeTab === "participant"}
                  onClick={() => setActiveTab("participant")}
                  icon="🎓"
                  title="I'm a Participant"
                  description="Year 2 or Deferred Student"
                />
                <TabButton
                  active={activeTab === "consultant"}
                  onClick={() => setActiveTab("consultant")}
                  icon="👨‍🏫"
                  title="I'm a Consultant"
                  description="Year 3/4 Mentor"
                />
              </div>

              {/* Tab Content */}
              <motion.div
                className="bg-white rounded-2xl shadow-xl p-8 md:p-12"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <AnimatePresence mode="wait">
                  {activeTab === "participant" ? (
                    <motion.div
                      key="participant"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ParticipantRegistrationForm eventId={eventData?.id} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="consultant"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ConsultantRegistrationForm eventId={eventData?.id} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </div>
          </div>
        </section>
      )}

      {/* Registration Closed Message */}
      {eventData?.registration_status === "closed" && (
        <section className="py-16">
          <div className="container mx-auto px-4">
            <div className="max-w-2xl mx-auto bg-orange-50 border border-orange-200 rounded-2xl p-8 text-center">
              <AlertCircle className="w-12 h-12 text-orange-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-orange-800 mb-2">Registration Closed</h3>
              <p className="text-orange-700">
                Registration for Code Quest {eventData.academic_year} has ended. 
                If you&apos;re already registered, check your email for your access key.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* FAQ Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Frequently Asked Questions
            </h2>
            <FAQAccordion />
          </div>
        </div>
      </section>
    </div>
  );
};

// ========== Hero Section ==========
const HeroSection = ({ event }) => {
  const formatDate = (dateString) => {
    if (!dateString) return "TBA";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <section className="relative bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 py-20 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/5 to-transparent"></div>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 mb-6"
          >
            <Trophy className="w-5 h-5 text-yellow-400" />
            <span className="text-white font-medium">
              {event?.course_code} • {event?.academic_year}
            </span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold text-white mb-4"
          >
            CODE <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500">QUEST</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl md:text-2xl text-blue-200 mb-2"
          >
            {event?.course_name}
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-gray-300 mb-8"
          >
            {event?.semester}
          </motion.p>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto"
          >
            <StatCard
              icon={<Users className="w-5 h-5" />}
              value={event?.participant_count || 0}
              label="Participants"
            />
            <StatCard
              icon={<UserCheck className="w-5 h-5" />}
              value={event?.consultant_count || 0}
              label="Consultants"
            />
            <StatCard
              icon={<Calendar className="w-5 h-5" />}
              value={formatDate(event?.presentation_date)}
              label="Presentation"
            />
            <StatCard
              icon={<Clock className="w-5 h-5" />}
              value={event?.days_until_presentation || 0}
              label="Days Left"
            />
          </motion.div>

          {/* Current Phase Badge */}
          {event?.current_phase && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-8"
            >
              <span className="inline-flex items-center gap-2 bg-green-500/20 border border-green-400/30 text-green-300 px-6 py-3 rounded-full font-semibold">
                <Rocket className="w-5 h-5" />
                Current Phase: {event.current_phase.label}
              </span>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
};

// Stat Card Component
const StatCard = ({ icon, value, label }) => (
  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-4">
    <div className="flex items-center justify-center gap-2 text-white mb-1">
      {icon}
      <span className="text-2xl font-bold">{value}</span>
    </div>
    <p className="text-blue-200 text-sm">{label}</p>
  </div>
);

// ========== Event Info Section ==========
const EventInfoSection = ({ event }) => {
  const formatDateTime = (dateString) => {
    if (!dateString) return "TBA";
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const timelineEvents = [
    { label: "Registration Opens", date: event?.registration_start_date, icon: CalendarClock },
    { label: "Registration Closes", date: event?.registration_end_date, icon: AlertCircle },
    { label: "Group Formation", date: event?.grouping_date, icon: Users },
    { label: "PM Election Starts", date: event?.voting_start_date, icon: UserCheck },
    { label: "PM Election Ends", date: event?.voting_end_date, icon: UserCheck },
    { label: "Submission Deadline", date: event?.project_submission_deadline, icon: Code },
    { label: "Presentation Day", date: event?.presentation_date, icon: Trophy },
  ];

  return (
    <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          {/* Event Details Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Calendar className="w-6 h-6 text-blue-600" />
              Event Details
            </h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Venue</p>
                    <p className="font-medium text-gray-900">
                      {event?.venue || "TBA"}{event?.building && `, ${event.building}`}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Users className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Organized By</p>
                    <p className="font-medium text-gray-900">{event?.organised_by || "CSS KNUST"}</p>
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Trophy className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Presentation Day</p>
                    <p className="font-medium text-gray-900">{formatDateTime(event?.presentation_date)}</p>
                  </div>
                </div>
                
                {event?.venue_details && (
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Additional Info</p>
                      <p className="font-medium text-gray-900">{event.venue_details}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Clock className="w-6 h-6 text-blue-600" />
              Event Timeline
            </h2>
            
            <div className="space-y-4">
              {timelineEvents.map((item, index) => {
                const Icon = item.icon;
                const isPast = item.date && new Date(item.date) < new Date();
                
                return (
                  <div 
                    key={index}
                    className={`flex items-center gap-4 p-4 rounded-xl transition-colors ${
                      isPast ? "bg-gray-50" : "bg-blue-50"
                    }`}
                  >
                    <div className={`p-2 rounded-lg ${isPast ? "bg-gray-200" : "bg-blue-100"}`}>
                      <Icon className={`w-5 h-5 ${isPast ? "text-gray-500" : "text-blue-600"}`} />
                    </div>
                    <div className="flex-1">
                      <p className={`font-medium ${isPast ? "text-gray-500" : "text-gray-900"}`}>
                        {item.label}
                      </p>
                    </div>
                    <p className={`text-sm ${isPast ? "text-gray-400" : "text-gray-600"}`}>
                      {formatDateTime(item.date)}
                    </p>
                    {isPast && (
                      <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">Done</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// ========== No Event State ==========
const NoEventState = ({ reason, message, lastEvent }) => (
  <div className="min-h-screen flex items-center justify-center px-4">
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-3xl p-12 max-w-lg text-center"
    >
      <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
        <Trophy className="w-10 h-10 text-white" />
      </div>
      
      <h1 className="text-4xl font-bold text-white mb-4">Code Quest</h1>
      
      {reason === "completed" && lastEvent && (
        <div className="mb-6 p-4 bg-white/5 rounded-xl">
          <p className="text-blue-200 text-sm mb-1">Last Event</p>
          <p className="text-white font-medium">{lastEvent.academic_year} - {lastEvent.semester}</p>
        </div>
      )}
      
      <p className="text-blue-200 text-lg mb-8">{message}</p>
      
      <div className="inline-flex items-center gap-2 text-yellow-400">
        <AlertCircle className="w-5 h-5" />
        <span className="text-sm">Check back later for updates</span>
      </div>
    </motion.div>
  </div>
);

// ========== Coming Soon State ==========
const ComingSoonState = ({ event }) => {
  const formatDate = (dateString) => {
    if (!dateString) return "TBA";
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-3xl p-12 max-w-2xl text-center"
      >
        <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
          <Rocket className="w-10 h-10 text-white" />
        </div>
        
        <h1 className="text-4xl font-bold text-white mb-2">Code Quest</h1>
        <p className="text-2xl text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 font-bold mb-4">
          Coming Soon!
        </p>
        
        <div className="bg-white/5 rounded-xl p-6 mb-8">
          <p className="text-blue-200 text-sm mb-2">Academic Year</p>
          <p className="text-white text-xl font-bold mb-4">{event.academic_year} - {event.semester}</p>
          
          <p className="text-blue-200 text-sm mb-2">Registration Opens</p>
          <p className="text-white text-lg font-medium">{formatDate(event.registration_start_date)}</p>
        </div>
        
        <p className="text-blue-200 mb-6">
          {event.course_code}: {event.course_name}
        </p>
        
        <div className="inline-flex items-center gap-2 text-yellow-400 bg-yellow-400/10 px-6 py-3 rounded-full">
          <Clock className="w-5 h-5" />
          <span className="font-medium">Registration Not Yet Open</span>
        </div>
      </motion.div>
    </div>
  );
};

// ========== Tab Button Component ==========
const TabButton = ({ active, onClick, icon, title, description }) => {
  return (
    <button
      onClick={onClick}
      className={`
        flex-1 p-6 rounded-xl border-2 transition-all duration-300 text-left
        ${
          active
            ? "border-blue-600 bg-blue-50 shadow-lg scale-105"
            : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
        }
      `}
    >
      <div className="flex items-start gap-4">
        <span className="text-4xl">{icon}</span>
        <div>
          <h3
            className={`text-lg font-bold mb-1 ${
              active ? "text-blue-600" : "text-gray-900"
            }`}
          >
            {title}
          </h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </button>
  );
};

// ========== FAQ Accordion Component ==========
const FAQAccordion = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: "Who can participate in Code Quest?",
      answer:
        "All Year 2 students and deferred students (Year 3/4) who need to complete the Mobile App Development course can participate.",
    },
    {
      question: "How are groups formed?",
      answer:
        "Groups are formed automatically by the admin based on your registration details. Regular students and deferred students are grouped separately.",
    },
    {
      question: "What happens after I register?",
      answer:
        "You will receive an access key via email. Use this key to login to your participant portal where you can view your group, vote for PM, and track your progress.",
    },
    {
      question: "Can I be a consultant and participant?",
      answer:
        "No, you can only register as either a participant or a consultant, not both.",
    },
    {
      question: "What if I lose my access key?",
      answer:
        "Contact the admin team at admin@thecssknust.com to recover your access key.",
    },
  ];

  return (
    <div className="space-y-4">
      {faqs.map((faq, index) => (
        <div
          key={index}
          className="border border-gray-200 rounded-lg overflow-hidden"
        >
          <button
            onClick={() => setOpenIndex(openIndex === index ? null : index)}
            className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <span className="font-semibold text-gray-900">{faq.question}</span>
            <ChevronDown
              className={`w-5 h-5 text-gray-500 transition-transform ${
                openIndex === index ? "rotate-180" : ""
              }`}
            />
          </button>
          <AnimatePresence>
            {openIndex === index && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: "auto" }}
                exit={{ height: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="p-4 pt-0 text-gray-600">{faq.answer}</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
};

export default CodeQuestPage;
