import { useState, useEffect, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Vote,
  Loader,
  CheckCircle,
  AlertCircle,
  User,
  ChevronDown,
  ChevronUp,
  Award,
  BarChart3,
  FileQuestion,
} from "lucide-react";
import toast from "react-hot-toast";
import { getEventCandidates, getEventPollOptions, castVote } from "../../utils/votingApi";
import { getVotingIdentifiers } from "../../utils/deviceFingerprint";
import { UserContext } from "../../Context/UserContext";

export const QuickVoteModal = ({ isOpen, onClose, event, onSuccess }) => {
  const { user } = useContext(UserContext);
  const [candidates, setCandidates] = useState({});
  const [pollOptions, setPollOptions] = useState(null);
  const [selectedVotes, setSelectedVotes] = useState({}); // {categoryId: candidateId} or {questionKey: option}
  const [votedCategories, setVotedCategories] = useState([]); // Track voted categories
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState({});

  // Check if this is a poll/referendum event
  const isPollEvent = ['poll', 'referendum'].includes(event?.event_type);

  // Load voted categories from localStorage on mount
  useEffect(() => {
    if (isOpen && event?.slug) {
      try {
        const storageKey = `voted_categories_${event.slug}`;
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          setVotedCategories(JSON.parse(stored));
        } else {
          setVotedCategories([]);
        }
      } catch {
        setVotedCategories([]);
      }
    }
  }, [isOpen, event?.slug]);

  useEffect(() => {
    if (isOpen && event) {
      const fetchData = async () => {
        setLoading(true);

        if (isPollEvent) {
          // Fetch poll options for poll/referendum events
          const { data, error } = await getEventPollOptions(event.slug);

          if (error) {
            toast.error("Failed to load poll options");
            setLoading(false);
            return;
          }

          setPollOptions(data);
          setCandidates({});

          // Expand all categories by default
          if (data && !data.options) {
            const expanded = {};
            Object.keys(data).forEach((key) => {
              expanded[key] = true;
            });
            setExpandedCategories(expanded);
          }
        } else {
          // Fetch candidates for election/awards events
          const { data, error } = await getEventCandidates(event.slug);

          if (error) {
            toast.error("Failed to load candidates");
            setLoading(false);
            return;
          }

          // Normalize response - handle both array and object responses
          let candidatesData = data;
          if (data && typeof data === "object" && !Array.isArray(data)) {
            if (data.results) {
              candidatesData = data.results;
            } else if (data.candidates) {
              candidatesData = data.candidates;
            }
          }

          // Group candidates by category
          const grouped = {};
          if (Array.isArray(candidatesData)) {
            candidatesData.forEach((candidate) => {
              const categoryId = candidate.category || "uncategorized";
              const categoryName = candidate.category_name || "General";

              if (!grouped[categoryId]) {
                grouped[categoryId] = {
                  id: categoryId,
                  name: categoryName,
                  candidates: [],
                };
              }
              grouped[categoryId].candidates.push(candidate);
            });
          } else if (typeof candidatesData === "object") {
            // Already grouped by category name
            Object.entries(candidatesData).forEach(([categoryName, categoryData]) => {
              const categoryId = categoryData.category_id || categoryName;
              grouped[categoryId] = {
                id: categoryId,
                name: categoryName,
                candidates: Array.isArray(categoryData) ? categoryData : (categoryData.candidates || []),
              };
            });
          }

          setCandidates(grouped);
          setPollOptions(null);

          // Expand all categories by default
          const expanded = {};
          Object.keys(grouped).forEach((key) => {
            expanded[key] = true;
          });
          setExpandedCategories(expanded);
        }

        setLoading(false);
      };

      fetchData();
    }
  }, [isOpen, event, isPollEvent]);

  const handleSelectCandidate = (categoryId, candidate) => {
    // Check if already voted in this category
    if (votedCategories.includes(String(categoryId)) || votedCategories.includes(candidate.category_name)) {
      toast.error("You have already voted in this category");
      return;
    }

    setSelectedVotes((prev) => {
      // If already selected, deselect
      if (prev[categoryId]?.id === candidate.id) {
        const newVotes = { ...prev };
        delete newVotes[categoryId];
        return newVotes;
      }
      // Select new candidate
      return {
        ...prev,
        [categoryId]: candidate,
      };
    });
  };

  const handleSelectPollOption = (questionKey, option) => {
    // Check if already voted in this question/category
    if (votedCategories.includes(questionKey)) {
      toast.error("You have already voted in this category");
      return;
    }

    setSelectedVotes((prev) => {
      // If already selected, deselect
      if (prev[questionKey]?.id === option.id) {
        const newVotes = { ...prev };
        delete newVotes[questionKey];
        return newVotes;
      }
      // Select new option
      return {
        ...prev,
        [questionKey]: option,
      };
    });
  };

  const toggleCategory = (categoryId) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  // Helper to extract error message from DRF responses
  const extractErrorMessage = (error) => {
    if (!error) return "An error occurred";
    if (typeof error === "string") return error;
    if (Array.isArray(error)) return error[0] || "An error occurred";
    if (error.non_field_errors) {
      return Array.isArray(error.non_field_errors)
        ? error.non_field_errors[0]
        : error.non_field_errors;
    }
    if (error.detail) {
      return Array.isArray(error.detail) ? error.detail[0] : error.detail;
    }
    if (error.message) return error.message;
    const keys = Object.keys(error);
    if (keys.length > 0) {
      const firstError = error[keys[0]];
      return Array.isArray(firstError) ? firstError[0] : firstError;
    }
    return "An error occurred";
  };

  const handleSubmitVotes = async () => {
    if (Object.keys(selectedVotes).length === 0) {
      toast.error(isPollEvent ? "Please select at least one option" : "Please select at least one candidate");
      return;
    }

    // Check if event has ended
    const isEventEnded = ['completed', 'results_published', 'voting_closed'].includes(event.status);
    if (isEventEnded) {
      toast.error("This voting event has ended. You cannot vote anymore.");
      onClose();
      return;
    }

    // Check if voting is still open
    if (!event.is_voting_open) {
      toast.error("Voting is not currently open for this event.");
      onClose();
      return;
    }

    // Check authentication for private events
    const requiresAuth = event.requires_authentication !== false;
    if (!user && requiresAuth) {
      toast.error("Please login to vote in this event");
      onClose();
      return;
    }

    setVoting(true);

    try {
      // Get device identifiers for vote tracking
      const identifiers = await getVotingIdentifiers();

      // Cast votes for each selection
      const votePromises = Object.entries(selectedVotes).map(
        ([key, selection]) => {
          const votePayload = {
            event: event.id,
            vote_quantity: 1,
            ...identifiers,
          };

          if (isPollEvent) {
            // Poll/referendum vote
            votePayload.poll_option = selection.id;
            votePayload.category = selection.category_id || selection.category || null;
          } else {
            // Election/awards vote
            votePayload.candidate = selection.id;
            votePayload.category = key !== "uncategorized" ? key : null;
          }

          return castVote(votePayload);
        }
      );

      const results = await Promise.all(votePromises);
      const errors = results.filter((r) => r.error);

      if (errors.length > 0) {
        const errorMessage = extractErrorMessage(errors[0].error);
        toast.error(errorMessage);
        setVoting(false);
        return;
      }

      // Store voted categories for this event
      try {
        const storageKey = `voted_categories_${event.slug}`;
        const newVotedCategories = [...votedCategories];

        Object.keys(selectedVotes).forEach((key) => {
          if (!newVotedCategories.includes(key)) {
            newVotedCategories.push(key);
          }
        });

        localStorage.setItem(storageKey, JSON.stringify(newVotedCategories));
        setVotedCategories(newVotedCategories);

        // Also track voted events
        const votedEvents = JSON.parse(localStorage.getItem('voted_events') || '[]');
        if (!votedEvents.includes(event.id)) {
          votedEvents.push(event.id);
          localStorage.setItem('voted_events', JSON.stringify(votedEvents));
        }
      } catch {
        // Ignore localStorage errors
      }

      toast.success(
        `Successfully voted for ${Object.keys(selectedVotes).length} ${isPollEvent ? 'option(s)' : 'candidate(s)'}!`
      );
      setSelectedVotes({});
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error("Voting error:", error);
      toast.error("An error occurred while voting");
    } finally {
      setVoting(false);
    }
  };

  // Calculate voting status
  const getTotalCategories = () => {
    if (isPollEvent) {
      return pollOptions?.options ? 1 : Object.keys(pollOptions || {}).length;
    }
    return Object.keys(candidates).length;
  };

  const getVotedCount = () => votedCategories.length;
  const totalCategories = getTotalCategories();
  const allVoted = getVotedCount() >= totalCategories && totalCategories > 0;
  const someVoted = getVotedCount() > 0 && getVotedCount() < totalCategories;

  // Get event type icon
  const getEventIcon = () => {
    switch (event?.event_type) {
      case 'poll':
        return <BarChart3 size={28} />;
      case 'referendum':
        return <FileQuestion size={28} />;
      case 'awards':
        return <Award size={28} />;
      default:
        return <Vote size={28} />;
    }
  };

  // Get event type label
  const getEventTypeLabel = () => {
    switch (event?.event_type) {
      case 'poll':
        return 'Poll';
      case 'referendum':
        return 'Referendum';
      case 'awards':
        return 'Awards';
      default:
        return 'Election';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header - changes color based on voting status */}
          <div className={`p-6 text-white ${
            allVoted
              ? 'bg-gradient-to-r from-green-600 to-emerald-600'
              : 'bg-gradient-to-r from-indigo-600 to-purple-600'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {allVoted ? <CheckCircle size={28} /> : getEventIcon()}
                <div>
                  <h2 className="text-xl font-bold">
                    {allVoted ? 'Thank You!' : `Quick ${getEventTypeLabel()}`}
                  </h2>
                  <p className={`text-sm ${allVoted ? 'text-green-100' : 'text-indigo-100'}`}>
                    {event?.title}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Voted Status Banner */}
          {allVoted && (
            <div className="bg-green-50 border-b border-green-200 p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-green-900">
                    You have voted in all {totalCategories} {totalCategories === 1 ? 'category' : 'categories'}!
                  </p>
                  <p className="text-sm text-green-700">
                    {event.show_live_results
                      ? 'You can view the results on the event page.'
                      : 'Results will be published after voting closes.'
                    }
                  </p>
                </div>
              </div>
            </div>
          )}

          {someVoted && (
            <div className="bg-amber-50 border-b border-amber-200 p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="text-amber-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-amber-900">
                    Voting in Progress: {getVotedCount()} of {totalCategories} categories voted
                  </p>
                  <p className="text-sm text-amber-700">
                    {totalCategories - getVotedCount()} {totalCategories - getVotedCount() === 1 ? 'category remains' : 'categories remain'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader className="animate-spin text-indigo-600 mb-4" size={40} />
                <p className="text-gray-600">Loading {isPollEvent ? 'options' : 'candidates'}...</p>
              </div>
            ) : isPollEvent ? (
              /* Poll/Referendum Content */
              !pollOptions || (pollOptions.options?.length === 0 && Object.keys(pollOptions).length === 0) ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <AlertCircle className="text-gray-400 mb-4" size={48} />
                  <p className="text-gray-600">No options available</p>
                </div>
              ) : pollOptions.options ? (
                /* Single-question poll */
                <div className="space-y-4">
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-4">
                    <h3 className="font-semibold text-indigo-900 mb-1">{pollOptions.question || event.title}</h3>
                    {pollOptions.description && (
                      <p className="text-sm text-indigo-700">{pollOptions.description}</p>
                    )}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {pollOptions.options.map((option) => {
                      const isSelected = selectedVotes[event.title]?.id === option.id;
                      const hasVotedHere = votedCategories.includes(event.title);

                      return (
                        <motion.div
                          key={option.id}
                          whileHover={{ scale: hasVotedHere ? 1 : 1.02 }}
                          whileTap={{ scale: hasVotedHere ? 1 : 0.98 }}
                          onClick={() => !hasVotedHere && handleSelectPollOption(event.title, option)}
                          className={`relative rounded-lg border-2 p-4 transition-all ${
                            hasVotedHere
                              ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                              : isSelected
                              ? 'border-indigo-500 bg-indigo-50 shadow-md cursor-pointer'
                              : 'border-gray-200 hover:border-gray-300 hover:shadow cursor-pointer'
                          }`}
                        >
                          {isSelected && !hasVotedHere && (
                            <div className="absolute top-2 right-2 bg-indigo-600 text-white rounded-full p-1">
                              <CheckCircle size={16} />
                            </div>
                          )}
                          {hasVotedHere && (
                            <div className="absolute top-2 right-2 bg-green-600 text-white rounded-full p-1">
                              <CheckCircle size={16} />
                            </div>
                          )}
                          <p className="font-medium text-gray-900">{option.option_text}</p>
                          {option.description && (
                            <p className="text-sm text-gray-500 mt-1">{option.description}</p>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                /* Multi-question poll */
                <div className="space-y-4">
                  {Object.entries(pollOptions).map(([questionName, questionData]) => {
                    const hasVotedHere = votedCategories.includes(questionName);

                    return (
                      <div
                        key={questionData.category_id || questionName}
                        className="border border-gray-200 rounded-lg overflow-hidden"
                      >
                        {/* Question Header */}
                        <button
                          onClick={() => toggleCategory(questionName)}
                          className={`w-full flex items-center justify-between p-4 transition-colors ${
                            hasVotedHere
                              ? 'bg-green-50 hover:bg-green-100'
                              : 'bg-gray-50 hover:bg-gray-100'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900">
                              {questionData.question || questionName}
                            </span>
                            {hasVotedHere && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                                <CheckCircle size={12} />
                                Voted
                              </span>
                            )}
                            {selectedVotes[questionName] && !hasVotedHere && (
                              <CheckCircle size={18} className="text-indigo-600 ml-2" />
                            )}
                          </div>
                          {expandedCategories[questionName] ? (
                            <ChevronUp size={20} className="text-gray-500" />
                          ) : (
                            <ChevronDown size={20} className="text-gray-500" />
                          )}
                        </button>

                        {/* Options Grid */}
                        {expandedCategories[questionName] && (
                          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {(questionData.options || []).map((option) => {
                              const isSelected = selectedVotes[questionName]?.id === option.id;

                              return (
                                <motion.div
                                  key={option.id}
                                  whileHover={{ scale: hasVotedHere ? 1 : 1.02 }}
                                  whileTap={{ scale: hasVotedHere ? 1 : 0.98 }}
                                  onClick={() => !hasVotedHere && handleSelectPollOption(questionName, option)}
                                  className={`relative rounded-lg border-2 p-4 transition-all ${
                                    hasVotedHere
                                      ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                                      : isSelected
                                      ? 'border-indigo-500 bg-indigo-50 shadow-md cursor-pointer'
                                      : 'border-gray-200 hover:border-gray-300 hover:shadow cursor-pointer'
                                  }`}
                                >
                                  {isSelected && !hasVotedHere && (
                                    <div className="absolute top-2 right-2 bg-indigo-600 text-white rounded-full p-1">
                                      <CheckCircle size={16} />
                                    </div>
                                  )}
                                  <p className="font-medium text-gray-900">{option.option_text}</p>
                                  {option.description && (
                                    <p className="text-sm text-gray-500 mt-1">{option.description}</p>
                                  )}
                                </motion.div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )
            ) : (
              /* Election/Awards Content */
              Object.keys(candidates).length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <AlertCircle className="text-gray-400 mb-4" size={48} />
                  <p className="text-gray-600">No candidates available</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Instructions */}
                  {!allVoted && (
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-4">
                      <p className="text-sm text-indigo-800">
                        <strong>Tip:</strong> Click on a candidate to select them.
                        You can select one candidate per category.
                      </p>
                    </div>
                  )}

                  {/* Categories with Candidates */}
                  {Object.values(candidates).map((category) => {
                    const hasVotedHere = votedCategories.includes(String(category.id)) || votedCategories.includes(category.name);

                    return (
                      <div
                        key={category.id}
                        className="border border-gray-200 rounded-lg overflow-hidden"
                      >
                        {/* Category Header */}
                        <button
                          onClick={() => toggleCategory(category.id)}
                          className={`w-full flex items-center justify-between p-4 transition-colors ${
                            hasVotedHere
                              ? 'bg-green-50 hover:bg-green-100'
                              : 'bg-gray-50 hover:bg-gray-100'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900">
                              {category.name}
                            </span>
                            <span className="text-sm text-gray-500">
                              ({category.candidates.length} candidates)
                            </span>
                            {hasVotedHere && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-medium ml-2">
                                <CheckCircle size={12} />
                                Voted
                              </span>
                            )}
                            {selectedVotes[category.id] && !hasVotedHere && (
                              <CheckCircle size={18} className="text-indigo-600 ml-2" />
                            )}
                          </div>
                          {expandedCategories[category.id] ? (
                            <ChevronUp size={20} className="text-gray-500" />
                          ) : (
                            <ChevronDown size={20} className="text-gray-500" />
                          )}
                        </button>

                        {/* Candidates Grid */}
                        {expandedCategories[category.id] && (
                          <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {category.candidates.map((candidate) => {
                              const isSelected = selectedVotes[category.id]?.id === candidate.id;

                              return (
                                <motion.div
                                  key={candidate.id}
                                  whileHover={{ scale: hasVotedHere ? 1 : 1.02 }}
                                  whileTap={{ scale: hasVotedHere ? 1 : 0.98 }}
                                  onClick={() => !hasVotedHere && handleSelectCandidate(category.id, candidate)}
                                  className={`relative cursor-pointer rounded-lg border-2 overflow-hidden transition-all ${
                                    hasVotedHere
                                      ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                                      : isSelected
                                      ? 'border-indigo-500 bg-indigo-50 shadow-md'
                                      : 'border-gray-200 hover:border-gray-300 hover:shadow'
                                  }`}
                                >
                                  {/* Candidate Image */}
                                  <div className="h-24 bg-gradient-to-br from-gray-100 to-gray-200">
                                    {candidate.profile_picture || candidate.profile_image || candidate.profile_image_url ? (
                                      <img
                                        src={candidate.profile_picture || candidate.profile_image || candidate.profile_image_url}
                                        alt={candidate.candidate_name}
                                        className="w-full h-full object-cover"
                                      />
                                    ) : (
                                      <div className="w-full h-full flex items-center justify-center">
                                        <User size={32} className="text-gray-400" />
                                      </div>
                                    )}
                                  </div>

                                  {/* Selected Checkmark */}
                                  {isSelected && !hasVotedHere && (
                                    <div className="absolute top-2 right-2 bg-indigo-600 text-white rounded-full p-1">
                                      <CheckCircle size={16} />
                                    </div>
                                  )}

                                  {/* Voted Checkmark */}
                                  {hasVotedHere && (
                                    <div className="absolute top-2 right-2 bg-green-600 text-white rounded-full p-1">
                                      <CheckCircle size={16} />
                                    </div>
                                  )}

                                  {/* Candidate Info */}
                                  <div className="p-2">
                                    <p className="font-medium text-sm text-gray-900 truncate">
                                      {candidate.candidate_name}
                                    </p>
                                    {candidate.program && (
                                      <p className="text-xs text-gray-500 truncate">
                                        {candidate.program}
                                      </p>
                                    )}
                                  </div>
                                </motion.div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )
            )}
          </div>

          {/* Footer */}
          <div className="border-t bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {allVoted ? (
                  <span className="text-green-600 font-medium flex items-center gap-1">
                    <CheckCircle size={16} />
                    Voting complete
                  </span>
                ) : (
                  <>
                    <span className="font-medium text-indigo-600">
                      {Object.keys(selectedVotes).length}
                    </span>{" "}
                    {isPollEvent ? 'option(s)' : 'candidate(s)'} selected
                  </>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  {allVoted ? 'Close' : 'Cancel'}
                </button>
                {!allVoted && (
                  <button
                    onClick={handleSubmitVotes}
                    disabled={voting || Object.keys(selectedVotes).length === 0}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                  >
                    {voting ? (
                      <>
                        <Loader className="animate-spin" size={18} />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Vote size={18} />
                        Submit {isPollEvent ? 'Vote' : 'Votes'}
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
