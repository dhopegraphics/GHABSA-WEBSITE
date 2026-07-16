import { motion } from "framer-motion";
import { User, Award, CheckCircle, Eye } from "lucide-react";

export const CandidateCard = ({
  candidate,
  onVote,
  onViewDetails,
  isSelected,
  hasVoted,
  showVoteCount = false,
  voteQuantity = 1,
  onQuantityChange,
  allowMultipleVotes = false,
  pricePerVote = 0,
}) => {
  const canVote = !hasVoted && onVote;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03 }}
      className={`bg-white rounded-lg shadow-md overflow-hidden transition-all ${
        isSelected ? "ring-4 ring-indigo-500" : ""
      } cursor-pointer hover:shadow-xl`}
      onClick={() => onViewDetails?.(candidate)}
    >
      {/* Profile Image */}
      <div className="relative h-48 bg-gradient-to-br from-indigo-100 to-purple-100">
        {candidate.profile_picture || candidate.profile_image || candidate.profile_image_url ? (
          <img
            src={candidate.profile_picture || candidate.profile_image || candidate.profile_image_url}
            alt={candidate.candidate_name}
            className="w-full h-full object-cover object-top"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <User size={64} className="text-gray-400" />
          </div>
        )}

        {/* View Details Hint */}
        <div className="absolute inset-0 bg-black/0 hover:bg-black/30 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
          <div className="bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full flex items-center gap-2 text-gray-700 font-medium">
            <Eye size={18} />
            View Details
          </div>
        </div>

        {/* Winner Badge */}
        {candidate.is_winner && (
          <div className="absolute top-2 right-2 bg-yellow-500 text-white px-3 py-1 rounded-full flex items-center gap-1 font-medium text-sm">
            <Award size={16} />
            Winner
          </div>
        )}

        {/* Selected Badge */}
        {isSelected && (
          <div className="absolute top-2 left-2 bg-indigo-600 text-white px-3 py-1 rounded-full flex items-center gap-1 font-medium text-sm">
            <CheckCircle size={16} />
            Selected
          </div>
        )}
      </div>

      <div className="p-4">
        {/* Candidate Name */}
        <h3 className="text-lg font-bold text-gray-900 mb-1">
          {candidate.candidate_name}
        </h3>

        {/* Candidate ID */}
        {candidate.candidate_id && (
          <p className="text-sm text-gray-500 mb-2">{candidate.candidate_id}</p>
        )}

        {/* Program & Year */}
        <div className="flex flex-wrap gap-2 mb-3">
          {candidate.program && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
              {candidate.program}
            </span>
          )}
          {candidate.year && (
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
              Year {candidate.year}
            </span>
          )}
        </div>

        {/* Bio */}
        {candidate.bio && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-3">
            {candidate.bio}
          </p>
        )}

        {/* Vote Count */}
        {showVoteCount && candidate.vote_count !== undefined && (
          <div className="flex items-center justify-between pt-3 border-t">
            <span className="text-sm text-gray-600">Votes:</span>
            <span className="text-lg font-bold text-indigo-600">
              {candidate.vote_count}
            </span>
          </div>
        )}

        {/* Vote Quantity Input */}
        {canVote && isSelected && allowMultipleVotes && (
          <div className="mt-3 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
            <label className="block text-sm font-medium text-indigo-900 mb-2">
              Number of votes to buy:
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onQuantityChange(Math.max(1, voteQuantity - 1));
                }}
                className="w-10 h-10 flex items-center justify-center bg-white border-2 border-indigo-300 text-indigo-600 rounded-lg hover:bg-indigo-100 font-bold"
              >
                −
              </button>
              <input
                type="number"
                min="1"
                value={voteQuantity}
                onChange={(e) => {
                  e.stopPropagation();
                  onQuantityChange(parseInt(e.target.value) || 1);
                }}
                className="flex-1 text-center text-lg font-bold border-2 border-indigo-300 rounded-lg py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onQuantityChange(voteQuantity + 1);
                }}
                className="w-10 h-10 flex items-center justify-center bg-white border-2 border-indigo-300 text-indigo-600 rounded-lg hover:bg-indigo-100 font-bold"
              >
                +
              </button>
            </div>
            {pricePerVote > 0 && (
              <p className="text-sm text-indigo-700 mt-2 font-medium">
                Total: GHS {(voteQuantity * pricePerVote).toFixed(2)}
              </p>
            )}
          </div>
        )}

        {/* Vote Button */}
        {canVote && (
          <button
            className={`w-full mt-3 py-3 px-4 rounded-lg font-bold transition-all transform hover:scale-105 ${
              isSelected
                ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg"
                : "bg-indigo-100 text-indigo-700 hover:bg-indigo-200 border-2 border-indigo-300"
            }`}
            onClick={(e) => {
              e.stopPropagation();
              onVote(candidate);
            }}
          >
            {isSelected ? "✓ Selected" : "Select to Vote"}
          </button>
        )}

        {/* Already Voted Indicator */}
        {hasVoted && !canVote && (
          <div className="mt-3 py-2 px-4 bg-green-100 text-green-800 rounded-lg text-center font-medium text-sm">
            You voted in this category
          </div>
        )}
      </div>
    </motion.div>
  );
};
