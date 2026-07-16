import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { fadeIn } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import { getVotingEventDetail, getEventResults } from "../utils/votingApi";
import { Helmet } from "react-helmet-async";
import {
  Trophy,
  TrendingUp,
  Users,
  ArrowLeft,
  Loader,
  Award,
  Medal,
  BarChart3,
  CheckCircle2,
  PieChart,
} from "lucide-react";
import { CandidateCard } from "../Components/Voting/CandidateCard";
import { CandidateDetailModal } from "../Components/Voting/CandidateDetailModal";

// Component for rendering poll/referendum results
function PollResultCard({ result }) {
  // Handle both direct options array and nested detailed_results structure
  const options = result.options || result.detailed_results?.options || [];
  const winningOption = result.winning_option || result.detailed_results?.winning_option || 
    (options.length > 0 ? options.reduce((prev, curr) => 
      (curr.vote_count || 0) > (prev.vote_count || 0) ? curr : prev
    ) : null);
  const totalVotes = result.total_votes || result.total_votes_cast || 
    options.reduce((sum, opt) => sum + (opt.vote_count || 0), 0);
  const question = result.question || result.detailed_results?.question || result.category_name || "Poll Results";

  // Sort options by vote count (descending)
  const sortedOptions = [...options].sort((a, b) => (b.vote_count || 0) - (a.vote_count || 0));

  return (
    <div className="mb-12">
      {/* Question Header */}
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="text-purple-500" size={32} />
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {question}
          </h2>
          <p className="text-gray-600">
            {totalVotes} vote{totalVotes !== 1 ? "s" : ""} cast
          </p>
        </div>
      </div>

      {/* No votes message */}
      {totalVotes === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <BarChart3 className="text-gray-400 mx-auto mb-3" size={48} />
          <p className="text-gray-600">No votes have been cast yet.</p>
        </div>
      )}

      {/* Winning Option Highlight */}
      {winningOption && totalVotes > 0 && (
        <div className="mb-6">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Trophy className="text-green-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">
                Winning Option
              </h3>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-start gap-4">
                {winningOption.image && (
                  <img
                    src={winningOption.image}
                    alt={winningOption.option_text}
                    className="w-16 h-16 rounded-lg object-cover"
                  />
                )}
                {winningOption.color && !winningOption.image && (
                  <div
                    className="w-16 h-16 rounded-lg flex-shrink-0"
                    style={{ backgroundColor: winningOption.color }}
                  />
                )}
                <div className="flex-1">
                  <h4 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    {winningOption.option_text}
                    <CheckCircle2 className="text-green-500" size={20} />
                  </h4>
                  {winningOption.description && (
                    <p className="text-gray-600 mt-1">{winningOption.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-2xl font-bold text-green-600">
                      {winningOption.percentage?.toFixed(1) || 
                        (totalVotes > 0 ? ((winningOption.vote_count || 0) / totalVotes * 100).toFixed(1) : 0)}%
                    </span>
                    <span className="text-gray-500">
                      ({winningOption.vote_count || 0} votes)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* All Options */}
      {sortedOptions.length > 0 && totalVotes > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <PieChart size={20} className="text-indigo-600" />
            All Options
          </h3>
          
          {sortedOptions.map((option, index) => {
            const isWinner = winningOption && (option.id === winningOption.id || option.option_text === winningOption.option_text);
            const percentage = option.percentage || (totalVotes > 0 ? ((option.vote_count || 0) / totalVotes) * 100 : 0);
            
            return (
              <div
                key={option.id || index}
                className={`relative bg-white rounded-xl border-2 p-4 transition-all ${
                  isWinner 
                    ? "border-green-400 shadow-lg" 
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {/* Ranking Badge */}
                <div className={`absolute -top-3 -left-3 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  index === 0 
                    ? "bg-yellow-400 text-yellow-900" 
                    : index === 1 
                    ? "bg-gray-300 text-gray-700"
                    : index === 2 
                    ? "bg-amber-600 text-white"
                    : "bg-gray-200 text-gray-600"
                }`}>
                  #{index + 1}
                </div>

                <div className="flex items-start gap-4">
                  {/* Option Image */}
                  {option.image && (
                    <img
                      src={option.image}
                      alt={option.option_text}
                      className="w-14 h-14 rounded-lg object-cover"
                    />
                  )}

                  {/* Color Indicator */}
                  {option.color && !option.image && (
                    <div
                      className="w-14 h-14 rounded-lg flex-shrink-0"
                      style={{ backgroundColor: option.color }}
                    />
                  )}

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                        {option.option_text}
                        {isWinner && <CheckCircle2 className="text-green-500" size={16} />}
                      </h4>
                      <div className="text-right">
                        <span className="text-lg font-bold text-gray-900">
                          {percentage.toFixed(1)}%
                        </span>
                        <span className="text-sm text-gray-500 ml-2">
                          ({option.vote_count || 0} votes)
                        </span>
                      </div>
                    </div>

                    {option.description && (
                      <p className="text-sm text-gray-600 mb-2">{option.description}</p>
                    )}

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-100 rounded-full h-3">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className={`h-3 rounded-full ${
                          isWinner
                            ? "bg-gradient-to-r from-green-500 to-emerald-500"
                            : "bg-gradient-to-r from-indigo-500 to-purple-500"
                        }`}
                        style={option.color ? { backgroundColor: option.color } : {}}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function VotingResultsPage() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resultsError, setResultsError] = useState(null);

  // Candidate detail modal state
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  // Handle viewing candidate details
  const handleViewCandidate = (candidate) => {
    setSelectedCandidate(candidate);
    setIsCandidateDetailOpen(true);
  };

  const fetchResults = async () => {
    setLoading(true);
    setResultsError(null);

    const [eventRes, resultsRes] = await Promise.all([
      getVotingEventDetail(slug),
      getEventResults(slug),
    ]);

    if (eventRes.error) {
      console.error("Error fetching event:", eventRes.error);
    } else {
      setEvent(eventRes.data);
    }

    if (resultsRes.error) {
      console.error("Error fetching results:", resultsRes.error);
      // Extract error message from response
      const errorDetail = resultsRes.error?.detail || resultsRes.error;
      setResultsError(errorDetail);
      setResults([]);
    } else {
      setResults(resultsRes.data || []);
    }

    setLoading(false);
  };

  useEffect(() => {
    scrollToTop();
    fetchResults();
  }, [slug]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <Loader
              className="animate-spin text-indigo-600 mx-auto mb-4"
              size={48}
            />
            <p className="text-gray-600">Loading results...</p>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  if (!event) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
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

  // Check if this is a poll event
  const isPollEvent = event?.event_type === "poll" || event?.event_type === "referendum";

  return (
    <>
      <Helmet>
        <title>{event.title} - Results | BIO-CHEM KNUST Voting</title>
        <meta name="description" content={`View results for ${event.title}`} />
      </Helmet>

      <Navbar />

      {/* Header */}
      <motion.section
        variants={fadeIn("down", 0.2)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className={`text-white py-12 ${
          isPollEvent 
            ? "bg-gradient-to-r from-indigo-600 to-purple-600"
            : "bg-gradient-to-r from-purple-600 to-pink-600"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <button
            onClick={() => navigate("/voting")}
            className="flex items-center gap-2 text-purple-100 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Events
          </button>

          <div className="flex items-center gap-4 mb-4">
            {isPollEvent ? <BarChart3 size={48} /> : <Trophy size={48} />}
            <div>
              <h1 className="text-4xl font-bold">{event.title}</h1>
              <p className="text-purple-100 mt-2">
                {isPollEvent ? "Poll/Referendum Results" : "Official Results"}
              </p>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Overall Stats */}
      <motion.section
        variants={fadeIn("up", 0.3)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <Users className="text-indigo-600" size={24} />
              <h3 className="font-semibold text-gray-700">Total Votes</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {event.total_votes_cast || 0}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              {isPollEvent ? (
                <BarChart3 className="text-purple-600" size={24} />
              ) : (
                <Award className="text-purple-600" size={24} />
              )}
              <h3 className="font-semibold text-gray-700">
                {isPollEvent ? "Questions" : "Categories"}
              </h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">{results.length}</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="text-green-600" size={24} />
              <h3 className="font-semibold text-gray-700">Voter Turnout</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {results[0]?.voter_turnout_percentage
                ? `${parseFloat(results[0].voter_turnout_percentage).toFixed(1)}%`
                : "N/A"}
            </p>
            {results[0]?.total_eligible_voters > 0 && (
              <p className="text-sm text-gray-500 mt-1">
                {event.total_votes_cast || 0} of {results[0].total_eligible_voters} eligible voters
              </p>
            )}
          </div>
        </div>
      </motion.section>

      {/* Results by Category */}
      <motion.section
        variants={fadeIn("up", 0.4)}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20"
      >
        {resultsError ? (
          <div className="text-center py-20">
            <Trophy size={64} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Results Not Available
            </h3>
            <p className="text-gray-600">
              {typeof resultsError === 'string' 
                ? resultsError 
                : resultsError?.detail || "Results are not yet available for this event."}
            </p>
            <button
              onClick={() => navigate("/voting")}
              className="mt-6 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Back to Events
            </button>
          </div>
        ) : results.length === 0 ? (
          <div className="text-center py-20">
            <Trophy size={64} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Results Not Yet Published
            </h3>
            <p className="text-gray-600">
              Results will be available once the event is completed.
            </p>
          </div>
        ) : (
          results.map((result, index) => {
            // Check if this is a poll/referendum result - check both top level and nested
            const isPollResult = result.type === "poll" || 
              result.detailed_results?.type === "poll" ||
              isPollEvent;

            if (isPollResult) {
              // Extract poll data from either top level or nested structure
              const pollData = result.detailed_results?.type === "poll" 
                ? {
                    ...result,
                    question: result.detailed_results.question || result.category_name,
                    options: result.detailed_results.options || [],
                    winning_option: result.detailed_results.winning_option,
                    total_votes: result.total_votes_cast || result.detailed_results.options?.reduce((sum, opt) => sum + (opt.vote_count || 0), 0) || 0,
                    type: "poll"
                  }
                : result;

              return <PollResultCard key={index} result={pollData} />;
            }

            // Election result rendering
            return (
            <div key={index} className="mb-12">
              {/* Category Header */}
              <div className="flex items-center gap-3 mb-6">
                <Medal className="text-yellow-500" size={32} />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {result.category_name || event.title}
                  </h2>
                  <p className="text-gray-600">
                    {result.total_votes_cast} votes cast
                    {result.voter_turnout_percentage && parseFloat(result.voter_turnout_percentage) > 0 && (
                      <span className="ml-2">
                        •{" "}
                        {parseFloat(result.voter_turnout_percentage).toFixed(1)}
                        % turnout
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* Winner Card */}
              {result.winner_details && (
                <div className="mb-8">
                  <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-300 rounded-xl p-4 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Trophy className="text-yellow-600" size={24} />
                      <h3 className="text-lg font-bold text-gray-900">
                        Winner
                      </h3>
                    </div>
                  </div>
                  <div 
                    className="cursor-pointer transition-transform hover:scale-[1.02]"
                    onClick={() => handleViewCandidate({
                      ...result.winner_details,
                      candidate_name: result.winner_details.candidate_name || result.winner_details.name,
                      vote_count: result.winner_details.vote_count || result.winner_details.votes,
                      is_winner: true,
                    })}
                  >
                    <CandidateCard
                      candidate={{
                        ...result.winner_details,
                        candidate_name: result.winner_details.candidate_name || result.winner_details.name,
                        vote_count: result.winner_details.vote_count || result.winner_details.votes,
                        is_winner: true,
                      }}
                      showVoteCount={true}
                    />
                  </div>
                </div>
              )}

              {/* All Candidates in Category */}
              {result.detailed_results?.candidates &&
                result.detailed_results.candidates.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      All Candidates
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {result.detailed_results.candidates.map((candidate, candIndex) => {
                        // Normalize field names from backend
                        const voteCount = candidate.vote_count || candidate.votes || 0;
                        const candidateName = candidate.candidate_name || candidate.name;
                        const profileImage = candidate.profile_image || candidate.photo;
                        
                        const normalizedCandidate = {
                          ...candidate,
                          candidate_name: candidateName,
                          profile_image: profileImage,
                          vote_count: voteCount,
                          is_winner: candIndex === 0,
                        };
                        
                        return (
                          <div 
                            key={candidate.candidate_id || candIndex} 
                            className="relative cursor-pointer transition-transform hover:scale-[1.02]"
                            onClick={() => handleViewCandidate(normalizedCandidate)}
                          >
                            {/* Ranking Badge */}
                            <div className="absolute top-2 left-2 z-10 bg-white rounded-full px-3 py-1 shadow-md">
                              <span className="font-bold text-gray-900">
                                #{candIndex + 1}
                              </span>
                            </div>
                            <CandidateCard
                              candidate={normalizedCandidate}
                              showVoteCount={true}
                            />

                            {/* Vote Percentage */}
                            {result.total_votes_cast > 0 && (
                              <div className="mt-2 bg-gray-100 rounded-lg p-3">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm text-gray-600">
                                    Vote Share
                                  </span>
                                  <span className="text-sm font-bold text-gray-900">
                                    {candidate.percentage?.toFixed(1) || 
                                      ((voteCount / result.total_votes_cast) * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-indigo-600 h-2 rounded-full"
                                    style={{
                                      width: `${candidate.percentage || 
                                        (voteCount / result.total_votes_cast) * 100}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
            </div>
            );
          })
        )}
      </motion.section>

      {/* Candidate Detail Modal */}
      <CandidateDetailModal
        isOpen={isCandidateDetailOpen}
        onClose={() => {
          setIsCandidateDetailOpen(false);
          setSelectedCandidate(null);
        }}
        candidate={selectedCandidate}
        canVote={false}
        hasVoted={true}
        showVoteCount={true}
      />

      <Footer />
    </>
  );
}
