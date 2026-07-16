import React, { useEffect, useRef, useState } from "react";
import { BiCalendar } from "react-icons/bi";
import { motion, useScroll, useTransform } from "framer-motion";
import { ChevronLeft, ChevronRight, ExternalLink, Images, CreditCard, Ticket, Users, MapPin, Zap, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function Event({
  date,
  title,
  description,
  link,
  imageUrl,
  by,
  timeline,
  eventStatus,
  mediaLink,
  // New props for enhanced events
  eventId,
  requiresRegistration = false,
  requiresPayment = false,
  isEarlyBird = false,
  lowestPrice = null,
  venue = null,
  attendeeCount = 0,
  maxAttendees = null,
  isFull = false,
}) {
  const navigate = useNavigate();
  const [show, setShow] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [images, setImages] = useState([]);

  const eventRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: eventRef,
    offset: ["start end", "end start"],
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  const openModal = (index) => {
    setCurrentImageIndex(index);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  const nextImage = () => {
    if (currentImageIndex < images.length - 1) {
      setCurrentImageIndex(currentImageIndex + 1);
    }
  };

  const prevImage = () => {
    if (currentImageIndex > 0) {
      setCurrentImageIndex(currentImageIndex - 1);
    }
  };

  useEffect(() => {
    const allImages = [
      ...(imageUrl?.map((item) => ({ image: item })) || []),
      ...(timeline?.map((item) => ({ image: item.image })) || []),
    ];
    setImages(allImages);
  }, [imageUrl, timeline]);

  return (
    <>
      <div ref={eventRef} className="relative pl-8 pb-32 group last:pb-0">
        <div className="sticky top-20 z-40">
          <div
            className={`text-4xl font-bold mb-8 ${
              new Date(date) >= new Date() ? "text-blue-500" : "text-gray-300"
            }`}
          >
            {new Date(date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
        </div>

        <div className="absolute left-0 top-0 h-full">
          <div className="w-8 h-8 bg-blue-600 text-white -translate-x-[14px] flex items-center justify-center rounded-full sticky top-20 left-0 z-10">
            <BiCalendar />
          </div>
          <div className="absolute top-3 w-1 h-full bg-gray-300" />
          <motion.div
            className="absolute top-3 w-1 bg-blue-700"
            style={{
              height: lineHeight,
            }}
          />
        </div>

        <div className="overflow-hidden">
          {/* Status Badge and Event Info - Always visible */}
          <div className="p-2 md:p-6 sticky top-36 z-30 bg-white/95 backdrop-blur-sm rounded-lg mb-4">
            {/* Status Badges */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {eventStatus && (
                <>
                  {eventStatus === "ongoing" && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      Ongoing Event
                    </span>
                  )}
                  {eventStatus === "upcoming" && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                      <BiCalendar className="w-4 h-4" />
                      Upcoming Event
                    </span>
                  )}
                  {eventStatus === "past" && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-semibold">
                      Past Event
                    </span>
                  )}
                </>
              )}
              {/* Payment Badge */}
              {requiresPayment && eventStatus !== "past" && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-semibold">
                  <CreditCard className="w-4 h-4" />
                  Paid Event
                </span>
              )}
              {/* Early Bird Badge */}
              {isEarlyBird && eventStatus !== "past" && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold animate-pulse">
                  <Zap className="w-4 h-4" />
                  Early Bird!
                </span>
              )}
              {/* Full Event Badge */}
              {isFull && eventStatus !== "past" && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-semibold">
                  Event Full
                </span>
              )}
            </div>

            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {title}
            </h3>
            <h3 className="text-xl text-gray-400 mb-2">By {by}</h3>
            <p className="text-gray-600 mb-4">{description}</p>

            {/* Event Meta Info */}
            <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
              {venue && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {venue}
                </span>
              )}
              {(attendeeCount > 0 || maxAttendees) && (
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {attendeeCount}{maxAttendees ? ` / ${maxAttendees}` : ''} attending
                </span>
              )}
              {requiresPayment && lowestPrice && eventStatus !== "past" && (
                <span className="flex items-center gap-1 font-semibold text-blue-600">
                  From GH₵{lowestPrice}
                </span>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              {/* View Details / Register Button */}
              {eventId && eventStatus !== "past" && (requiresRegistration || requiresPayment) ? (
                <button
                  onClick={() => navigate(`/events/${eventId}`)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  <Ticket className="w-5 h-5" />
                  {requiresPayment ? "View & Register" : "Register Now"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : eventId && eventStatus !== "past" ? (
                <button
                  onClick={() => navigate(`/events/${eventId}`)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  View Details
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : null}
              
              {/* External Registration Link */}
              {link && eventStatus !== "past" && !requiresRegistration && (
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href={link}
                  className="inline-flex items-center gap-2 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium"
                >
                  External Registration
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}

              {/* Event Gallery Button - Only show for past events with media_link */}
              {eventStatus === "past" && mediaLink && (
                <a
                  href={mediaLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-md hover:shadow-lg font-medium"
                >
                  <Images className="w-5 h-5" />
                  View Event Gallery
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
              
              {/* View Details for past events */}
              {eventId && eventStatus === "past" && (
                <button
                  onClick={() => navigate(`/events/${eventId}`)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  View Details
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Event Images */}
          {imageUrl && (
            <div
              className={`grid mb-4 ${
                imageUrl.length === 2 ? "grid-cols-2 gap-4" : "grid-cols-1"
              }`}
            >
              {imageUrl.map((item, index) => (
                <div
                  key={index}
                  className="w-full relative z-0 rounded-lg overflow-hidden"
                >
                  <img
                    src={item}
                    alt={title}
                    className="w-full aspect-[3/2] object-cover cursor-pointer rounded-lg hover:scale-110 transition-transform"
                    onClick={() => openModal(index)}
                  />
                  {index === 1 && timeline?.length !== 0 && !show && (
                    <div className="absolute w-full h-full top-0 left-0 bg-black/70 z-10 flex items-center justify-center">
                      <p
                        onClick={() => setShow(true)}
                        className="text-white p-2 px-4 border border-white rounded cursor-pointer hover:bg-white hover:text-blue-600 transition-colors font-semibold"
                      >
                        See more
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {show && timeline?.length !== 0 && (
            <div className={`grid grid-cols-2 md:grid-cols-3 gap-4`}>
              {timeline?.map((item, index) => (
                <div key={index} className="w-full rounded-lg overflow-hidden">
                  <img
                    src={item?.image}
                    alt={item?.description}
                    className="w-full aspect-[3/2] object-cover rounded-lg cursor-pointer hover:scale-110 transition-transform"
                    onClick={() => openModal(index + imageUrl.length)}
                  />
                </div>
              ))}
            </div>
          )}
          {show && (
            <p
              onClick={() => setShow(false)}
              className="cursor-pointer text-center text-blue-600 font-semibold hover:underline my-4"
            >
              Hide all
            </p>
          )}
        </div>
      </div>
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="relative w-full max-w-5xl max-h-[90vh] overflow-hidden rounded-lg">
            <button
              onClick={closeModal}
              className="absolute top-2 right-2 font-bold rounded-full text-red-500 p-2 px-[14px] bg-black/50 hover:text-red-800"
            >
              ✕
            </button>

            <div className="flex items-center justify-center h-full">
              <img
                src={images[currentImageIndex]?.image}
                alt="Modal content"
                className="max-h-[85vh] max-w-full rounded-lg object-contain"
              />
            </div>

            <button
              onClick={prevImage}
              disabled={currentImageIndex === 0}
              className="absolute top-1/2 left-4 transform -translate-y-1/2 p-2 text-blue-500 rounded-full bg-black/50 hover:text-blue-800 disabled:text-gray-300"
            >
              <ChevronLeft />
            </button>

            <button
              onClick={nextImage}
              disabled={currentImageIndex === images?.length - 1}
              className="absolute top-1/2 right-4 transform -translate-y-1/2 p-2 text-blue-500 rounded-full bg-black/50 hover:text-blue-800 disabled:text-gray-300"
            >
              <ChevronRight />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
