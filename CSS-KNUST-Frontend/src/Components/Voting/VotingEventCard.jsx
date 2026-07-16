import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Users,
  Vote,
  Trophy,
  Clock,
  CheckCircle,
  UserPlus,
  Lock,
  Unlock,
  AlertCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useVoting } from "../../Context/VotingContext";

// Helper to check if user has voted locally (for anonymous users) - fallback only
const getLocalVotedEvents = () => {
  try {
    const stored = localStorage.getItem('voted_events');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const VotingEventCard = ({ event, onRegisterClick, onVoteClick, user, onLoginRequired }) => {
  const navigate = useNavigate();
  const { hasVotedForEvent, getVoteDetailsForEvent } = useVoting();
  const [hasVotedLocally, setHasVotedLocally] = useState(false);

  // Check if event requires authentication - based on both requires_authentication AND visibility
  // Events with visibility !== 'public' require auth
  const isPublicVisibility = event.visibility === 'public';
  const requiresAuth = event.requires_authentication !== false || !isPublicVisibility;

  useEffect(() => {
    // Check if user has voted in this event (stored locally for anonymous users) - fallback
    const votedEvents = getLocalVotedEvents();
    setHasVotedLocally(votedEvents.includes(event.id));
  }, [event.id]);

  // Get vote status from context (pre-checked on page load) OR fallback to local storage
  const voteDetails = getVoteDetailsForEvent(event.slug);
  const hasVotedFromContext = hasVotedForEvent(event.slug);

  const getStatusColor = (status) => {
    switch (status) {
      case "voting_open":
        return "bg-green-100 text-green-800";
      case "registration_open":
        return "bg-blue-100 text-blue-800";
      case "results_published":
        return "bg-purple-100 text-purple-800";
      case "completed":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-yellow-100 text-yellow-800";
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case "election":
        return "bg-indigo-100 text-indigo-800";
      case "awards":
        return "bg-pink-100 text-pink-800";
      case "poll":
        return "bg-cyan-100 text-cyan-800";
      case "referendum":
        return "bg-amber-100 text-amber-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Use computed values from API (is_registration_open, is_voting_open)
  // These already account for both the boolean switch AND the date range
  const isVotingOpen = event.is_voting_open;
  const isRegistrationOpen = event.is_registration_open;
  
  // Check if user has voted - priority: context (batch check) > API > local storage
  // Context is populated when VotingPage loads via batch_check_vote_status
  const hasVoted = hasVotedFromContext || event.user_has_voted || hasVotedLocally;
  
  // Get the reason from context if available
  const voteReason = voteDetails?.reason || null;
  
  // Check if event is in a final state (no voting allowed)
  const isEventEnded = ['completed', 'results_published', 'voting_closed'].includes(event.status);
  
  // Can user vote? Must be open, not ended, and not already voted
  const canVote = isVotingOpen && !isEventEnded && !hasVoted;

  const getButtonStyle = () => {
    if (canVote) {
      return "bg-indigo-600 text-white hover:bg-indigo-700";
    }
    if (hasVoted || event.status === "results_published") {
      return "bg-purple-600 text-white hover:bg-purple-700";
    }
    if (isRegistrationOpen && !isEventEnded) {
      return "bg-green-600 text-white hover:bg-green-700";
    }
    if (event.status === "upcoming") {
      return "bg-amber-500 text-white hover:bg-amber-600";
    }
    if (isEventEnded) {
      return "bg-gray-500 text-white";
    }
    return "bg-gray-600 text-white hover:bg-gray-700";
  };

  const getButtonText = () => {
    // If event is completed or results published, always show View Results
    if (event.status === "results_published" || event.status === "completed") {
      return "View Results";
    }
    if (hasVoted) return "View Results";
    if (canVote) {
      if (requiresAuth && !user) return "Login to Vote";
      return "Vote Now";
    }
    if (event.status === "voting_closed") return "Voting Closed";
    if (isRegistrationOpen && !isEventEnded) {
      if (!user) return "Login to Register";
      return "Register as Candidate";
    }
    if (event.status === "upcoming") return "Coming Soon";
    return "View Details";
  };

  // Check if should navigate to results page
  const shouldShowResults = hasVoted || 
    event.status === "results_published" || 
    event.status === "completed";

  const handleButtonClick = (e) => {
    e.stopPropagation(); // Prevent card click navigation
    
    // If event ended or user has voted, go to results page
    if (shouldShowResults) {
      navigate(`/voting/${event.slug}/results`);
      return;
    }
    
    // Check authentication requirement for voting
    if (canVote) {
      if (requiresAuth && !user) {
        // Require login before voting
        onLoginRequired?.(event);
        return;
      }
      if (onVoteClick) {
        onVoteClick(event);
        return;
      }
    }
    
    // Check authentication requirement for registration
    if (isRegistrationOpen && !isEventEnded) {
      if (!user) {
        onLoginRequired?.(event);
        return;
      }
      if (onRegisterClick) {
        onRegisterClick(event);
        return;
      }
    }
    
    // Navigate to detail page for all other actions
    navigate(`/voting/${event.slug}`);
  };

  const handleCardClick = () => {
    navigate(`/voting/${event.slug}`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-xl shadow-lg overflow-hidden cursor-pointer"
      onClick={handleCardClick}
    >
      {/* Banner Image */}
      {event.banner && (
        <div className="h-48 overflow-hidden">
          <img
            src={event.banner}
            alt={event.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="p-6">
        {/* Title */}
        <h3 className="text-xl font-bold text-gray-900 mb-2">{event.title}</h3>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
              event.status
            )}`}
          >
            {event.status?.replace("_", " ").toUpperCase()}
          </span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${getTypeColor(
              event.event_type
            )}`}
          >
            {event.event_type?.toUpperCase()}
          </span>
          {hasVoted && (
            <span 
              className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 flex items-center gap-1"
              title={voteReason || "You have already voted in this event"}
            >
              <CheckCircle size={12} />
              VOTED
            </span>
          )}
          {requiresAuth && !user && isVotingOpen && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 flex items-center gap-1">
              <Lock size={12} />
              LOGIN REQUIRED
            </span>
          )}
          {isPublicVisibility && isVotingOpen && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800 flex items-center gap-1">
              <Unlock size={12} />
              PUBLIC
            </span>
          )}
          {!isPublicVisibility && event.visibility && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 flex items-center gap-1">
              <Lock size={12} />
              {event.visibility === 'year' ? `YEAR ${event.eligible_years?.join(', ') || 'SPECIFIC'}` : 
               event.visibility === 'program' ? 'PROGRAM SPECIFIC' : 
               event.visibility.toUpperCase()}
            </span>
          )}
        </div>

        {/* Description */}
        {event.description && (
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">
            {event.description}
          </p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Users size={16} />
            <span>{event.total_registered_candidates || 0} Candidates</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Vote size={16} />
            <span>{event.total_votes_cast || 0} Votes</span>
          </div>
        </div>

        {/* Dates */}
        {event.voting_start_date && event.voting_end_date && (
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <Calendar size={16} />
            <span>
              {formatDate(event.voting_start_date)} -{" "}
              {formatDate(event.voting_end_date)}
            </span>
          </div>
        )}

        {/* Payment Info */}
        {event.requires_payment && (
          <div className="flex items-center gap-2 text-sm text-amber-600 mb-4">
            <Trophy size={16} />
            <span>
              Voting Fee: GHS {parseFloat(event.voting_fee || 0).toFixed(2)}
            </span>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={handleButtonClick}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${getButtonStyle()}`}
        >
          {requiresAuth && !user && (canVote || isRegistrationOpen) && <Lock size={18} />}
          {isRegistrationOpen && user && <UserPlus size={18} />}
          {getButtonText()}
        </button>
      </div>
    </motion.div>
  );
};
