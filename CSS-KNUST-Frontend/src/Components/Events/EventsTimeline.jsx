import { Event } from "./Event";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../../utils/framerVariants";
import { FiArrowUpRight } from "react-icons/fi";
import { Link } from "react-router-dom";
import { getData } from "../../utils/apiHandler";
import { useEvents } from "../../Context/EventsContext";
import { useEffect, useState } from "react";
import { EventSkeleton } from "./EventSkeleton";

export function EventsTimeline() {
  const { events, setEvents } = useEvents();
  const [categorizedEvents, setCategorizedEvents] = useState({
    ongoing: [],
    upcoming: [],
    past: [],
  });

  const fetchEvents = async () => {
    const { response, error } = await getData("/events/");
    if (error) {
      console.error("Error fetching events:", error);
    }
    if (response) {
      // Handle paginated response - extract results array
      const eventsData = response.results || response;
      setEvents(eventsData);

      // Categorize events by status
      const ongoing = eventsData.filter((e) => e.event_status === "ongoing");
      const upcoming = eventsData.filter((e) => e.event_status === "upcoming");
      const past = eventsData.filter((e) => e.event_status === "past");

      setCategorizedEvents({ ongoing, upcoming, past });
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  // Get the 3 events to display:
  // 1. First ongoing event (or first upcoming if no ongoing)
  // 2. Next 2 upcoming events
  const getEventsToDisplay = () => {
    const eventsToShow = [];

    // Priority 1: Show first ongoing event
    if (categorizedEvents.ongoing.length > 0) {
      eventsToShow.push(categorizedEvents.ongoing[0]);
    }

    // Priority 2: Fill remaining slots with upcoming events
    const remainingSlots = 3 - eventsToShow.length;
    const upcomingToAdd = categorizedEvents.upcoming.slice(
      0,
      remainingSlots + (eventsToShow.length === 0 ? 0 : 2)
    );
    eventsToShow.push(...upcomingToAdd);

    // If we still don't have 3 events, show recent past events
    if (eventsToShow.length < 3) {
      const neededPast = 3 - eventsToShow.length;
      eventsToShow.push(...categorizedEvents.past.slice(0, neededPast));
    }

    return eventsToShow.slice(0, 3);
  };

  const displayEvents = getEventsToDisplay();

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <motion.h1
        variants={fadeIn("up", 0.5, 0)}
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0 }}
        className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
      >
        <span className="relative text-blue-600">
          Event
          <motion.div
            variants={underlineAnimation(0.7)}
            initial="offscreen"
            whileInView="onscreen"
            exit="reverse"
            className="absolute left-0 bottom-0 h-1 bg-blue-600"
            style={{ width: "0%", height: "3px" }}
          />
        </span>{" "}
        Timeline
      </motion.h1>
      <p className="text-center text-gray-600 mb-12">
        Join us in celebrating knowledge, innovation, and collaboration through
        a variety of events. From coding hackathons to insightful workshops,
        networking opportunities to inspiring guest lectures.
      </p>

      <div className="relative">
        {!events
          ? Array(3)
              .fill(0)
              .map((_, index) => <EventSkeleton key={index} />)
          : displayEvents.map((event) => (
              <Event
                key={event?.event_id}
                date={event?.event_date}
                title={event?.event_name}
                description={event?.description}
                link={event?.registration_link}
                by={event?.organised_by}
                imageUrl={[event?.event_image_1, event?.event_image_2]}
                timeline={event?.timeline}
                eventStatus={event?.event_status}
                mediaLink={event?.media_link}
              />
            ))}
      </div>

      <div className="mt-12  text-center justify-center md:justify-start">
        <Link
          to={"/events"}
          className="border-2 border-blue-700 text-blue-700 px-6 py-3 font-medium rounded hover:bg-blue-700 hover:text-white transition"
        >
          See More <FiArrowUpRight className="inline" />
        </Link>
      </div>
    </div>
  );
}
