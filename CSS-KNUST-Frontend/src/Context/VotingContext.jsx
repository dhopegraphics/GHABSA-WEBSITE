import React, { createContext, useState, useContext, useCallback } from "react";

export const VotingContext = createContext();

export const VotingProvider = ({ children }) => {
  const [votingEvents, setVotingEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [candidates, setCandidates] = useState({});
  const [eligibility, setEligibility] = useState(null);
  const [results, setResults] = useState([]);
  const [myVotes, setMyVotes] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Store vote status for each event (keyed by event slug)
  // Format: { 'event-slug': { has_voted: true, reason: '...', voted_categories: [...] } }
  const [votedEventsMap, setVotedEventsMap] = useState({});
  
  // Check if user has voted for a specific event
  const hasVotedForEvent = useCallback((eventSlug) => {
    return votedEventsMap[eventSlug]?.has_voted || false;
  }, [votedEventsMap]);
  
  // Get vote details for a specific event
  const getVoteDetailsForEvent = useCallback((eventSlug) => {
    return votedEventsMap[eventSlug] || null;
  }, [votedEventsMap]);
  
  // Mark an event as voted (called after successful vote)
  const markEventAsVoted = useCallback((eventSlug, details = {}) => {
    setVotedEventsMap(prev => ({
      ...prev,
      [eventSlug]: {
        has_voted: true,
        reason: details.reason || "You have already voted in this event.",
        voted_categories: details.voted_categories || []
      }
    }));
  }, []);

  return (
    <VotingContext.Provider
      value={{
        votingEvents,
        setVotingEvents,
        currentEvent,
        setCurrentEvent,
        candidates,
        setCandidates,
        eligibility,
        setEligibility,
        results,
        setResults,
        myVotes,
        setMyVotes,
        loading,
        setLoading,
        // Vote status tracking
        votedEventsMap,
        setVotedEventsMap,
        hasVotedForEvent,
        getVoteDetailsForEvent,
        markEventAsVoted,
      }}
    >
      {children}
    </VotingContext.Provider>
  );
};

export const useVoting = () => {
  const context = useContext(VotingContext);
  if (!context) {
    throw new Error("useVoting must be used within a VotingProvider");
  }
  return context;
};
