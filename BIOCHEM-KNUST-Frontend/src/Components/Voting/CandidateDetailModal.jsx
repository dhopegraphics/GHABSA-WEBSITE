import { motion, AnimatePresence } from "framer-motion";
import { X, User, Award, GraduationCap, Vote, CheckCircle } from "lucide-react";

export const CandidateDetailModal = ({
  isOpen,
  onClose,
  candidate,
  onVote,
  isSelected,
  canVote,
  hasVoted,
  showVoteCount,
}) => {
  if (!isOpen || !candidate) return null;

  const profileImage = candidate.profile_picture || candidate.profile_image || candidate.profile_image_url;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
          >
            <X size={20} />
          </button>

          {/* Profile Image - Full Size */}
          <div className="relative w-full aspect-square bg-gradient-to-br from-indigo-100 to-purple-100">
            {profileImage ? (
              <img
                src={profileImage}
                alt={candidate.candidate_name}
                className="w-full h-full object-cover object-top"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <User size={120} className="text-gray-300" />
              </div>
            )}

            {/* Winner Badge */}
            {candidate.is_winner && (
              <div className="absolute top-4 left-4 bg-yellow-500 text-white px-4 py-2 rounded-full flex items-center gap-2 font-medium shadow-lg">
                <Award size={20} />
                Winner
              </div>
            )}

            {/* Selected Badge */}
            {isSelected && (
              <div className="absolute top-4 left-4 bg-indigo-600 text-white px-4 py-2 rounded-full flex items-center gap-2 font-medium shadow-lg">
                <CheckCircle size={20} />
                Selected
              </div>
            )}
          </div>

          {/* Candidate Details */}
          <div className="p-6">
            {/* Name */}
            <h2 className="text-2xl font-bold text-gray-900 mb-1">
              {candidate.candidate_name}
            </h2>

            {/* Candidate ID */}
            {candidate.candidate_id && (
              <p className="text-gray-500 mb-3 flex items-center gap-2">
                <GraduationCap size={16} />
                {candidate.candidate_id}
              </p>
            )}

            {/* Program & Year Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              {candidate.program && (
                <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  {candidate.program}
                </span>
              )}
              {candidate.year && (
                <span className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  Year {candidate.year}
                </span>
              )}
              {candidate.category_name && (
                <span className="px-3 py-1.5 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                  {candidate.category_name}
                </span>
              )}
            </div>

            {/* Bio / Manifesto */}
            {candidate.bio && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                  Bio / Manifesto
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {candidate.bio}
                  </p>
                </div>
              </div>
            )}

            {/* Vote Count */}
            {showVoteCount && candidate.vote_count !== undefined && (
              <div className="flex items-center justify-between py-3 border-t border-gray-200 mb-4">
                <span className="text-gray-600 font-medium">Total Votes:</span>
                <span className="text-2xl font-bold text-indigo-600">
                  {candidate.vote_count}
                </span>
              </div>
            )}

            {/* Vote Button */}
            {canVote && !hasVoted && (
              <button
                onClick={() => {
                  onVote?.(candidate);
                  onClose();
                }}
                className={`w-full py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                  isSelected
                    ? "bg-indigo-100 text-indigo-700 border-2 border-indigo-500"
                    : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl"
                }`}
              >
                {isSelected ? (
                  <>
                    <CheckCircle size={20} />
                    Selected
                  </>
                ) : (
                  <>
                    <Vote size={20} />
                    Select Candidate
                  </>
                )}
              </button>
            )}

            {hasVoted && (
              <div className="w-full py-3 bg-green-100 text-green-700 rounded-lg font-medium flex items-center justify-center gap-2">
                <CheckCircle size={20} />
                You have already voted
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
