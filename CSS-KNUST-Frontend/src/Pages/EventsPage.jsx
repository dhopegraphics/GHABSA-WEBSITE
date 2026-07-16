import  { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import { Event } from "../Components/Events/Event";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import Login from "./Login";
import { getData } from "../utils/apiHandler";
import { useEvents } from "../Context/EventsContext";
import { EventSkeleton } from "../Components/Events/EventSkeleton";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { useNavigate } from "react-router-dom";
import ExecutiveLogin from "./ExecutiveLogin";
import { Helmet } from "react-helmet-async";
import { Calendar, Filter, X, Smartphone } from "lucide-react";
import { PublicEventsCalendarButton } from "../Components/CalendarSync/CalendarSyncModal";

export function EventsPage() {
  const { events, setEvents } = useEvents();
  const [selectedYear, setSelectedYear] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [availableYears, setAvailableYears] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);

  const fetchEvents = async () => {
    // Fetch all events with a high limit to get all pages including past events
    const { response, error } = await getData("/events?limit=100");
    if (error) {
      console.error("Error fetching events:", error);
    }
    if (response) {
      // Handle paginated response - extract results array
      const eventsData = response.results || response;
      // Events are already sorted optimally by backend: upcoming first (nearest), then ongoing, then past (recent first)
      setEvents(eventsData);

      // Extract unique years from events
      const years = [
        ...new Set(
          eventsData.map((event) => new Date(event.event_date).getFullYear())
        ),
      ].sort((a, b) => b - a);

      setAvailableYears(years);
    }
  };

  useEffect(() => {
    scrollToTop();
    fetchEvents();
  }, []);

  // Filter events based on selected year and status
  useEffect(() => {
    if (!events) return;

    let filtered = [...events];

    // Filter by year
    if (selectedYear !== "all") {
      filtered = filtered.filter(
        (event) =>
          new Date(event.event_date).getFullYear() === parseInt(selectedYear)
      );
    }

    // Filter by status
    if (selectedStatus !== "all") {
      filtered = filtered.filter(
        (event) => event.event_status === selectedStatus
      );
    }

    // Events are already sorted optimally by backend: upcoming first (nearest), then ongoing, then past (recent first)
    setFilteredEvents(filtered);
  }, [events, selectedYear, selectedStatus]);

  const getStatusCount = (status) => {
    if (!events) return 0;
    if (status === "all") return events.length;
    return events.filter((e) => e.event_status === status).length;
  };

  const navigate = useNavigate();

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
    setIsExecutiveOpen(false);
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };
  return (
    <>
      <Helmet>
        <title>Events | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Stay updated with upcoming tech events, workshops, and conferences by the Biochemistry Society, KNUST."
        />
        <meta
          name="keywords"
          content="BIO-CHEM KNUST events, tech events KNUST, biochemknust events"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="BIO-CHEM KNUST - Events" />
        <meta
          property="og:description"
          content="Join exciting tech events, workshops, and activities hosted by BIO-CHEM KNUST."
        />
        <meta
          property="og:image"
          content="https://biochemknust.com/images/logo.png"
        />
        <meta property="og:url" content="https://biochemknust.com/events" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Event",
            name: "BIO-CHEM KNUST Tech Events",
            description:
              "Tech-focused events organized by BIO-CHEM KNUST including workshops, talks, and networking sessions.",
            image: "https://biochemknust.com/images/logo.png",
          })}
        </script>
      </Helmet>

      <div className="relative mt-[70px]">
        <Navbar onSignInClick={handleOpenLoginModal} />
        <div className="max-w-6xl mx-auto px-4 py-16">
          <motion.h1
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="text-4xl md:text-5xl mb-6 font-bold text-gray-900 text-center"
          >
            Browse{" "}
            <span className="relative text-blue-600">
              {" "}
              Events
              <motion.div
                variants={underlineAnimation(0.7)}
                initial="offscreen"
                whileInView="onscreen"
                exit="reverse"
                className="absolute left-0 bottom-0 h-1 bg-blue-600"
                style={{ width: "0%", height: "3px" }}
              />
            </span>
          </motion.h1>
          <p className="text-center text-gray-600 mb-8">
            Join us in celebrating knowledge, innovation, and collaboration
            through a variety of events. From coding hackathons to insightful
            workshops, networking opportunities to inspiring guest lectures, our
            events are designed to foster learning, creativity, and community
            spirit.
          </p>

          {/* Sync to Calendar Button */}
          <div className="flex justify-center mb-8">
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-full">
                  <Smartphone className="w-6 h-6 text-purple-600" />
                </div>
                <div className="text-center sm:text-left">
                  <p className="font-semibold text-gray-900">Never miss an event!</p>
                  <p className="text-sm text-gray-600">Sync all BIO-CHEM KNUST events to your phone calendar</p>
                </div>
              </div>
              <PublicEventsCalendarButton />
            </div>
          </div>

          {/* Filters Section */}
          <div className="mb-12 space-y-6">
            {/* Status Tabs */}
            <div className="flex flex-wrap gap-3 justify-center">
              <button
                onClick={() => setSelectedStatus("all")}
                className={`px-6 py-2.5 rounded-full font-semibold transition-all ${
                  selectedStatus === "all"
                    ? "bg-blue-600 text-white shadow-lg scale-105"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                All Events ({getStatusCount("all")})
              </button>
              <button
                onClick={() => setSelectedStatus("ongoing")}
                className={`px-6 py-2.5 rounded-full font-semibold transition-all flex items-center gap-2 ${
                  selectedStatus === "ongoing"
                    ? "bg-green-600 text-white shadow-lg scale-105"
                    : "bg-green-50 text-green-700 hover:bg-green-100"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    selectedStatus === "ongoing" ? "bg-white" : "bg-green-500"
                  }`}
                ></span>
                Ongoing ({getStatusCount("ongoing")})
              </button>
              <button
                onClick={() => setSelectedStatus("upcoming")}
                className={`px-6 py-2.5 rounded-full font-semibold transition-all flex items-center gap-2 ${
                  selectedStatus === "upcoming"
                    ? "bg-blue-600 text-white shadow-lg scale-105"
                    : "bg-blue-50 text-blue-700 hover:bg-blue-100"
                }`}
              >
                <Calendar className="w-4 h-4" />
                Upcoming ({getStatusCount("upcoming")})
              </button>
              <button
                onClick={() => setSelectedStatus("past")}
                className={`px-6 py-2.5 rounded-full font-semibold transition-all ${
                  selectedStatus === "past"
                    ? "bg-gray-700 text-white shadow-lg scale-105"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                Past ({getStatusCount("past")})
              </button>
            </div>

            {/* Year Filter */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <div className="flex items-center gap-2 text-gray-700 font-medium">
                <Filter className="w-5 h-5" />
                <span>Filter by Year:</span>
              </div>
              <button
                onClick={() => setSelectedYear("all")}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  selectedYear === "all"
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-white border-2 border-gray-200 text-gray-700 hover:border-blue-300"
                }`}
              >
                All Years
              </button>
              {availableYears.map((year) => (
                <button
                  key={year}
                  onClick={() => setSelectedYear(year.toString())}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedYear === year.toString()
                      ? "bg-blue-600 text-white shadow-md"
                      : "bg-white border-2 border-gray-200 text-gray-700 hover:border-blue-300"
                  }`}
                >
                  {year}
                </button>
              ))}
            </div>

            {/* Active Filters Display */}
            {(selectedYear !== "all" || selectedStatus !== "all") && (
              <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                <span className="text-sm text-gray-600">Active filters:</span>
                {selectedYear !== "all" && (
                  <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                    Year: {selectedYear}
                    <button
                      onClick={() => setSelectedYear("all")}
                      className="hover:bg-blue-100 rounded-full p-0.5"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                {selectedStatus !== "all" && (
                  <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                    Status: {selectedStatus}
                    <button
                      onClick={() => setSelectedStatus("all")}
                      className="hover:bg-blue-100 rounded-full p-0.5"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                <button
                  onClick={() => {
                    setSelectedYear("all");
                    setSelectedStatus("all");
                  }}
                  className="text-sm text-red-600 hover:text-red-700 font-medium underline"
                >
                  Clear all filters
                </button>
              </div>
            )}

            {/* Results Count */}
            <div className="text-center text-gray-600 text-sm">
              Showing{" "}
              <span className="font-bold text-gray-900">
                {filteredEvents.length}
              </span>{" "}
              event{filteredEvents.length !== 1 ? "s" : ""}
            </div>
          </div>

          <div className="relative">
            {!events ? (
              Array(5)
                .fill(0)
                .map((_, index) => <EventSkeleton key={index} />)
            ) : filteredEvents.length > 0 ? (
              filteredEvents.map((event) => (
                <Event
                  key={event?.event_id}
                  eventId={event?.event_id}
                  date={event?.event_date}
                  title={event?.event_name}
                  description={event?.description}
                  by={event?.organised_by}
                  imageUrl={[event?.event_image_1, event?.event_image_2]}
                  timeline={event?.timeline}
                  link={event?.registration_link}
                  eventStatus={event?.event_status}
                  mediaLink={event?.media_link}
                  // New props for enhanced events
                  requiresRegistration={event?.registration?.required}
                  requiresPayment={event?.payment?.required}
                  isEarlyBird={event?.payment?.is_early_bird_active}
                  lowestPrice={event?.payment?.lowest_price}
                  venue={event?.location?.venue}
                  attendeeCount={event?.attendance?.total_attending}
                  maxAttendees={event?.attendance?.capacity}
                  isFull={event?.registration?.is_full}
                />
              ))
            ) : (
              <div className="text-center py-16">
                <div className="mb-4 text-gray-400">
                  <Calendar className="w-16 h-16 mx-auto mb-4" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No events found
                </h3>
                <p className="text-gray-600 mb-6">
                  Try adjusting your filters to see more events
                </p>
                <button
                  onClick={() => {
                    setSelectedYear("all");
                    setSelectedStatus("all");
                  }}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>
        </div>
        <Footer />
        {isLoginModalOpen && (
          <Login
            onClose={handleCloseModals}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
            action={() => navigate("/dashboard/home")}
            switchToExecutive={handleExecutiveOpen}
          />
        )}

        {isSignupModalOpen && (
          <SignUp
            onClose={handleCloseModals}
            switchToLogin={handleOpenLoginModal}
          />
        )}
        {isOpen && (
          <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
        )}
        {isExecutiveOpen && (
          <ExecutiveLogin
            onClose={handleOpenLoginModal}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
          />
        )}
      </div>
    </>
  );
}
