import { useEffect, useState, useContext } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import { getVotingEvents, batchCheckVoteStatus } from "../utils/votingApi";
import { getVotingIdentifiers } from "../utils/deviceFingerprint";
import { useVoting } from "../Context/VotingContext";
import { VotingEventCard } from "../Components/Voting/VotingEventCard";
import { CandidateRegistrationModal } from "../Components/Voting/CandidateRegistrationModal";
import { QuickVoteModal } from "../Components/Voting/QuickVoteModal";
import { Helmet } from "react-helmet-async";
import { Vote, Filter, Search, Loader } from "lucide-react";
import { UserContext } from "../Context/UserContext";
import Login from "./Login";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";

export function VotingPage() {
  const { votingEvents, setVotingEvents, loading, setLoading, setVotedEventsMap } = useVoting();
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Auth modals
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  // Registration modal
  const [isRegistrationModalOpen, setIsRegistrationModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Quick vote modal
  const [isVoteModalOpen, setIsVoteModalOpen] = useState(false);
  const [selectedVoteEvent, setSelectedVoteEvent] = useState(null);

  // Reusable fetch function for success handlers
  const refreshEvents = async () => {
    const { data, error } = await getVotingEvents();
    if (error) {
      // Ignore abort errors
      if (error !== "Request aborted" && !error?.message?.includes("aborted")) {
        console.error("Error fetching voting events:", error);
      }
      return;
    }
    if (data) {
      const eventsData = data.results || data;
      setVotingEvents(eventsData);
    }
  };

  // Batch check vote status for all events
  const checkVoteStatusForAllEvents = async (events) => {
    try {
      // Get device identifiers
      const identifiers = await getVotingIdentifiers();
      
      // Get all event slugs
      const eventSlugs = events.map(e => e.slug);
      
      // Batch check vote status
      const { data, error } = await batchCheckVoteStatus(
        eventSlugs,
        identifiers.device_fingerprint,
        identifiers.session_id
      );
      
      if (!error && data?.voted_events) {
        // Update the voted events map in context
        setVotedEventsMap(data.voted_events);
        console.log("📊 Pre-checked vote status for", data.checked_count, "events. Voted in:", data.voted_count);
      }
    } catch (err) {
      console.error("Error batch checking vote status:", err);
    }
  };

  useEffect(() => {
    let isMounted = true;
    
    const fetchEvents = async () => {
      setLoading(true);
      const { data, error } = await getVotingEvents();
      
      // Only update state if component is still mounted
      if (!isMounted) return;
      
      if (error) {
        // Ignore abort errors
        if (error !== "Request aborted" && !error?.message?.includes("aborted")) {
          console.error("Error fetching voting events:", error);
        }
      }
      if (data) {
        const eventsData = data.results || data;
        setVotingEvents(eventsData);
        
        // After fetching events, check vote status for all of them
        checkVoteStatusForAllEvents(eventsData);
      }
      setLoading(false);
    };
    
    scrollToTop();
    fetchEvents();
    
    return () => {
      isMounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-check vote status when user logs in/out
  useEffect(() => {
    if (votingEvents && votingEvents.length > 0) {
      checkVoteStatusForAllEvents(votingEvents);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    if (!votingEvents) return;

    let filtered = [...votingEvents];

    // Get the actual user data (user object has structure { access, refresh, user })
    const userData = user?.user;

    // Helper function to check if user's year matches eligible years
    // Handles type coercion (string "4" vs number 4)
    const userYearMatches = (eligibleYears) => {
      const userYear = userData?.year || userData?.level;
      if (!userYear) return false;
      const userYearNum = parseInt(userYear, 10);
      return eligibleYears.some((year) => parseInt(year, 10) === userYearNum);
    };

    // Filter by visibility and user eligibility
    filtered = filtered.filter((event) => {
      // Public events are always visible
      if (event.visibility === "public") {
        return true;
      }

      // For non-public events, check if user is logged in
      if (!userData) {
        // Anonymous users can only see public events
        return false;
      }

      // For year-specific events
      if (event.visibility === "year") {
        // Check if event has eligible_years and user's year matches
        if (event.eligible_years && event.eligible_years.length > 0) {
          if (!userYearMatches(event.eligible_years)) {
            return false;
          }
        }
        return true;
      }

      // For program-specific events
      if (event.visibility === "program") {
        // Check if event has eligible_programs and user's program matches
        if (event.eligible_programs && event.eligible_programs.length > 0) {
          const userProgram = userData.program || userData.department;
          if (!userProgram || !event.eligible_programs.some(
            (prog) => prog.toLowerCase() === userProgram.toLowerCase()
          )) {
            return false;
          }
        }
        return true;
      }

      // For private events - only show if user would be eligible
      if (event.visibility === "private") {
        // Check both year and program if specified
        let isEligible = true;
        
        if (event.eligible_years && event.eligible_years.length > 0) {
          if (!userYearMatches(event.eligible_years)) {
            isEligible = false;
          }
        }
        
        if (event.eligible_programs && event.eligible_programs.length > 0) {
          const userProgram = userData.program || userData.department;
          if (!userProgram || !event.eligible_programs.some(
            (prog) => prog.toLowerCase() === userProgram.toLowerCase()
          )) {
            isEligible = false;
          }
        }
        
        return isEligible;
      }

      // Default: show the event
      return true;
    });

    // Filter by status - use computed values for open states
    if (statusFilter !== "all") {
      if (statusFilter === "voting_open") {
        filtered = filtered.filter((event) => event.is_voting_open);
      } else if (statusFilter === "registration_open") {
        // Show events with registration open but voting not yet open
        filtered = filtered.filter((event) => event.is_registration_open && !event.is_voting_open);
      } else if (statusFilter === "completed") {
        // Combine completed, voting_closed, and results_published
        filtered = filtered.filter((event) => 
          event.status === "completed" || 
          event.status === "voting_closed" || 
          event.status === "results_published"
        );
      } else {
        filtered = filtered.filter((event) => event.status === statusFilter);
      }
    }

    // Filter by type
    if (typeFilter !== "all") {
      filtered = filtered.filter((event) => event.event_type === typeFilter);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(
        (event) =>
          event.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          event.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredEvents(filtered);
  }, [votingEvents, statusFilter, typeFilter, searchQuery, user]);

  // Get the actual user data (user object has structure { access, refresh, user })
  const userData = user?.user;

  // Helper function to check if user's year matches (handles type coercion)
  const checkUserYearMatches = (eligibleYears) => {
    const userYear = userData?.year || userData?.level;
    if (!userYear) return false;
    const userYearNum = parseInt(userYear, 10);
    return eligibleYears.some((year) => parseInt(year, 10) === userYearNum);
  };

  // Helper function to check if user can see an event (for status counts)
  const canUserSeeEvent = (event) => {
    if (event.visibility === "public") return true;
    if (!userData) return false;
    
    if (event.visibility === "year") {
      if (event.eligible_years && event.eligible_years.length > 0) {
        return checkUserYearMatches(event.eligible_years);
      }
      return true;
    }
    
    if (event.visibility === "program") {
      if (event.eligible_programs && event.eligible_programs.length > 0) {
        const userProgram = userData.program || userData.department;
        return userProgram && event.eligible_programs.some(
          (prog) => prog.toLowerCase() === userProgram.toLowerCase()
        );
      }
      return true;
    }
    
    if (event.visibility === "private") {
      let isEligible = true;
      if (event.eligible_years && event.eligible_years.length > 0) {
        if (!checkUserYearMatches(event.eligible_years)) isEligible = false;
      }
      if (event.eligible_programs && event.eligible_programs.length > 0) {
        const userProgram = userData.program || userData.department;
        if (!userProgram || !event.eligible_programs.some(
          (prog) => prog.toLowerCase() === userProgram.toLowerCase()
        )) isEligible = false;
      }
      return isEligible;
    }
    
    return true;
  };

  const getStatusCount = (status) => {
    if (!votingEvents) return 0;
    
    // First filter by visibility
    const visibleEvents = votingEvents.filter(canUserSeeEvent);
    
    if (status === "all") return visibleEvents.length;
    
    // Use computed values for open states
    if (status === "voting_open") {
      return visibleEvents.filter((e) => e.is_voting_open).length;
    }
    if (status === "registration_open") {
      return visibleEvents.filter((e) => e.is_registration_open && !e.is_voting_open).length;
    }
    // Combine voting_closed, completed, and results_published
    if (status === "completed") {
      return visibleEvents.filter((e) => 
        e.status === "completed" || 
        e.status === "voting_closed" || 
        e.status === "results_published"
      ).length;
    }
    
    return visibleEvents.filter((e) => e.status === status).length;
  };

  const handleOpenLoginModal = () => {
    console.log("🔓 Opening login modal");
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsForgotPasswordOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    console.log("📝 Opening signup modal");
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsForgotPasswordOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenForgotPassword = () => {
    setIsForgotPasswordOpen(true);
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenExecutiveLogin = () => {
    setIsExecutiveOpen(true);
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsForgotPasswordOpen(false);
  };

  const handleRegisterClick = (event) => {
    if (!user) {
      // Open login modal if user is not logged in
      handleOpenLoginModal();
      return;
    }
    setSelectedEvent(event);
    setIsRegistrationModalOpen(true);
  };

  const handleVoteClick = (event) => {
    // For events requiring authentication, check if user is logged in
    if (event.requires_authentication !== false && !user) {
      handleOpenLoginModal();
      return;
    }
    setSelectedVoteEvent(event);
    setIsVoteModalOpen(true);
  };

  const handleLoginRequired = (event) => {
    // Store the event the user wanted to interact with
    console.log("🔒 Login required for event:", event.title);
    handleOpenLoginModal();
  };

  const handleVoteSuccess = () => {
    // Refresh events to update vote counts
    refreshEvents();
  };

  const handleRegistrationSuccess = () => {
    // Refresh events to update candidate count
    refreshEvents();
  };

  return (
    <>
      <Helmet>
        <title>Voting & Elections | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Participate in departmental elections, course rep voting, and awards. Make your voice heard in the CSS community."
        />
      </Helmet>

      <Navbar
        onSignInClick={handleOpenLoginModal}
      />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-block mb-4"
            >
              <Vote size={64} className="mx-auto text-indigo-600" />
            </motion.div>
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-4xl md:text-5xl mb-4 font-bold text-gray-900"
            >
              Voting &{" "}
              <span className="relative text-indigo-600">
                Elections
                <motion.div
                  variants={underlineAnimation(0.7)}
                  initial="offscreen"
                  whileInView="onscreen"
                  exit="reverse"
                  className="absolute left-0 bottom-0 h-1 bg-indigo-600"
                  style={{ width: "0%", height: "3px" }}
                />
              </span>
            </motion.h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Participate in departmental elections, vote for your course
              representatives, and make your voice heard in the CSS community.
            </p>
          </div>
        </div>
      </section>

      {/* Filters Section */}
      <motion.section
        variants={fadeIn("up", 0.3)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        {/* Status Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { value: "all", label: "All Events", count: getStatusCount("all") },
            {
              value: "voting_open",
              label: "🗳️ Voting Open",
              count: getStatusCount("voting_open"),
            },
            {
              value: "registration_open",
              label: "📝 Registration Open",
              count: getStatusCount("registration_open"),
            },
            {
              value: "results_published",
              label: "📊 Results",
              count: getStatusCount("results_published"),
            },
            {
              value: "completed",
              label: "✓ Completed",
              count: getStatusCount("completed"),
            },
          ].map((status) => (
            <button
              key={status.value}
              onClick={() => setStatusFilter(status.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                statusFilter === status.value
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {status.label} ({status.count})
            </button>
          ))}
        </div>

        {/* Search and Type Filter */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              size={20}
            />
            <input
              type="text"
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Type Filter */}
          <div className="relative">
            <Filter
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              size={20}
            />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent appearance-none"
            >
              <option value="all">All Types</option>
              <option value="election">Elections</option>
              <option value="awards">Awards</option>
              <option value="poll">Polls</option>
              <option value="referendum">Referendum</option>
            </select>
          </div>
        </div>
      </motion.section>

      {/* Events Grid */}
      <motion.section
        variants={fadeIn("up", 0.4)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-screen"
      >
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader className="animate-spin text-indigo-600 mb-4" size={48} />
            <p className="text-gray-600">Loading voting events...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-20">
            <Vote size={64} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              No Events Found
            </h3>
            <p className="text-gray-600">
              {searchQuery || statusFilter !== "all" || typeFilter !== "all"
                ? "Try adjusting your filters"
                : "Check back later for upcoming voting events"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredEvents.map((event) => (
              <VotingEventCard 
                key={event.id} 
                event={event} 
                user={user}
                onRegisterClick={handleRegisterClick}
                onVoteClick={handleVoteClick}
                onLoginRequired={handleLoginRequired}
              />
            ))}
          </div>
        )}
      </motion.section>

      <Footer />

      {/* Auth Modals */}
      {isLoginModalOpen && (
        <Login
          onClose={() => setIsLoginModalOpen(false)}
          switchToSignup={() => {
            setIsLoginModalOpen(false);
            setIsSignupModalOpen(true);
          }}
          action={() => {
            setIsLoginModalOpen(false);
            refreshEvents(); // Refresh to show user-specific data
          }}
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

      {isForgotPasswordOpen && (
        <ForgotPasswordModal
          isOpen={isForgotPasswordOpen}
          onClose={() => setIsForgotPasswordOpen(false)}
        />
      )}

      {isExecutiveOpen && (
        <ExecutiveLogin onClose={() => setIsExecutiveOpen(false)} />
      )}

      {/* Candidate Registration Modal */}
      {selectedEvent && (
        <CandidateRegistrationModal
          isOpen={isRegistrationModalOpen}
          onClose={() => {
            setIsRegistrationModalOpen(false);
            setSelectedEvent(null);
          }}
          event={selectedEvent}
          categories={selectedEvent.categories || []}
          onSuccess={handleRegistrationSuccess}
        />
      )}

      {/* Quick Vote Modal */}
      {selectedVoteEvent && (
        <QuickVoteModal
          isOpen={isVoteModalOpen}
          onClose={() => {
            setIsVoteModalOpen(false);
            setSelectedVoteEvent(null);
          }}
          event={selectedVoteEvent}
          onSuccess={handleVoteSuccess}
        />
      )}
    </>
  );
}
