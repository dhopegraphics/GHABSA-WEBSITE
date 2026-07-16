import { useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";

const VotingView = ({ groupData, userData, onVoteSubmit }) => {
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isNominee = groupData?.nominees?.some(
    (n) => n.student_id === userData?.student_id
  );

  const handleVote = async () => {
    setLoading(true);
    setError("");

    try {
      const accessKey =
        localStorage.getItem("cq_access_key") ||
        sessionStorage.getItem("cq_access_key");

      await axios.post("/codequest/pm/vote/", {
        access_key: accessKey,
        candidate_id: selectedCandidate,
      });

      setShowConfirmModal(false);
      onVoteSubmit();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to submit vote");
    } finally {
      setLoading(false);
    }
  };

  if (isNominee) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
          <div className="text-6xl mb-4">🗳️</div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            You&apos;re a Nominee
          </h3>
          <p className="text-gray-600">
            As a nominee for Project Manager, you cannot vote in this election.
            Good luck!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Voting Header */}
      <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-xl shadow-lg p-8 text-white text-center">
        <div className="text-5xl mb-4">🗳️</div>
        <h2 className="text-3xl font-bold mb-2">
          Vote for Your Project Manager
        </h2>
        <p className="text-green-100">
          Voting Deadline:{" "}
          {groupData?.voting_deadline
            ? new Date(groupData.voting_deadline).toLocaleString()
            : "TBD"}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Candidates */}
      <div className="space-y-4">
        {groupData?.nominees?.map((candidate, index) => (
          <motion.div
            key={index}
            className={`bg-white rounded-xl shadow-md p-6 border-2 cursor-pointer transition-all ${
              selectedCandidate === candidate.id
                ? "border-green-500 bg-green-50"
                : "border-gray-200 hover:border-green-300"
            }`}
            onClick={() => setSelectedCandidate(candidate.id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                  {candidate.name?.charAt(0) || "C"}
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-bold text-gray-900">
                    {candidate.name}
                  </h3>
                  {selectedCandidate === candidate.id && (
                    <span className="text-2xl">✓</span>
                  )}
                </div>
                <p className="text-gray-600 mb-3">{candidate.student_id}</p>
                {candidate.statement && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 italic">
                      &quot;{candidate.statement}&quot;
                    </p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Submit Vote Button */}
      <div className="flex justify-center">
        <button
          onClick={() => setShowConfirmModal(true)}
          disabled={!selectedCandidate}
          className="px-8 py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-semibold text-lg transition-colors"
        >
          Submit Vote
        </button>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Confirm Your Vote
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to vote for{" "}
              <span className="font-semibold">
                {
                  groupData?.nominees?.find((n) => n.id === selectedCandidate)
                    ?.name
                }
              </span>
              ? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleVote}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition-colors"
              >
                {loading ? "Submitting..." : "Confirm Vote"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default VotingView;
