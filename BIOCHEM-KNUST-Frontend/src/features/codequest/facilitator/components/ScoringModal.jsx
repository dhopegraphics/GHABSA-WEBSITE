import { useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import PropTypes from "prop-types";

const ScoringModal = ({
  project,
  criteria,
  accessCode,
  onClose,
  onScoreSubmitted,
}) => {
  const [scores, setScores] = useState({});
  const [comments, setComments] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleScoreChange = (criteriaId, value) => {
    const criterion = criteria.find((c) => c.id === criteriaId);
    const numValue = parseFloat(value);

    if (numValue > criterion.max_points) {
      setError(
        `Score for "${criterion.name}" cannot exceed ${criterion.max_points} points`
      );
      return;
    }

    setError("");
    setScores({
      ...scores,
      [criteriaId]: numValue,
    });
  };

  const handleCommentChange = (criteriaId, value) => {
    setComments({
      ...comments,
      [criteriaId]: value,
    });
  };

  const calculateTotal = () => {
    return Object.values(scores).reduce((sum, score) => sum + (score || 0), 0);
  };

  const calculateWeightedTotal = () => {
    let total = 0;
    criteria.forEach((criterion) => {
      const score = scores[criterion.id] || 0;
      const percentage =
        (score / criterion.max_points) *
        (criterion.weight_percentage / 100) *
        100;
      total += percentage;
    });
    return total.toFixed(2);
  };

  const isFormValid = () => {
    return criteria.every((criterion) => {
      const score = scores[criterion.id];
      return score !== undefined && score !== null && score >= 0;
    });
  };

  const handleSubmit = async () => {
    if (!isFormValid()) {
      setError("Please score all criteria before submitting");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Submit all scores
      const promises = criteria.map((criterion) =>
        axios.post("/codequest/scoring/submit/", {
          access_code: accessCode,
          project: project.id,
          criteria: criterion.id,
          score: scores[criterion.id],
          comments: comments[criterion.id] || "",
        })
      );

      await Promise.all(promises);

      onScoreSubmitted(project.id);
    } catch (err) {
      console.error("Error submitting scores:", err);
      setError(
        err.response?.data?.error ||
          "Failed to submit scores. Please try again."
      );
      setLoading(false);
    }
  };

  const handleSubmitClick = () => {
    if (isFormValid()) {
      setShowConfirmation(true);
    } else {
      setError("Please score all criteria before submitting");
    }
  };

  return (
    <motion.div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <motion.div
        className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 rounded-t-2xl z-10">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {project.logo_url ? (
                  <img
                    src={project.logo_url}
                    alt={project.app_name}
                    className="w-16 h-16 rounded-lg border-2 border-white/30"
                  />
                ) : (
                  <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center text-3xl">
                    📱
                  </div>
                )}
                <div>
                  <h2 className="text-2xl font-bold">
                    Group {project.group?.group_number} - {project.app_name}
                  </h2>
                  <p className="text-purple-100">{project.group?.group_name}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm text-purple-100">
                <span>
                  👤 PM: {project.group?.project_manager?.student_name || "TBA"}
                </span>
                <span>👥 {project.group?.members?.length || 0} members</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Project Description */}
          {project.description && (
            <div className="mt-4 p-3 bg-white/10 rounded-lg backdrop-blur-sm">
              <p className="text-sm text-white">{project.description}</p>
            </div>
          )}
        </div>

        {/* Scoring Form */}
        <div className="p-6">
          {error && (
            <motion.div
              className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <span>⚠️</span>
              <span>{error}</span>
            </motion.div>
          )}

          {/* Criteria Cards */}
          <div className="space-y-4 mb-6">
            {criteria.map((criterion, index) => (
              <motion.div
                key={criterion.id}
                className="bg-gray-50 rounded-xl p-5 border-2 border-gray-200 hover:border-purple-300 transition-colors"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-1">
                      {criterion.name}
                    </h3>
                    {criterion.description && (
                      <p className="text-sm text-gray-600 mb-2">
                        {criterion.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-purple-600 font-medium">
                        Max Points: {criterion.max_points}
                      </span>
                      <span className="text-indigo-600 font-medium">
                        Weight: {criterion.weight_percentage}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Score Input */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Score (0 - {criterion.max_points})
                    </label>
                    <input
                      type="number"
                      min="0"
                      max={criterion.max_points}
                      step="0.5"
                      value={scores[criterion.id] || ""}
                      onChange={(e) =>
                        handleScoreChange(criterion.id, e.target.value)
                      }
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-lg font-semibold"
                      placeholder="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Comments (optional)
                    </label>
                    <input
                      type="text"
                      value={comments[criterion.id] || ""}
                      onChange={(e) =>
                        handleCommentChange(criterion.id, e.target.value)
                      }
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Add comments..."
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Total Score Preview */}
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6 mb-6 border-2 border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Points</p>
                <p className="text-3xl font-bold text-gray-900">
                  {calculateTotal().toFixed(2)} /{" "}
                  {criteria.reduce((sum, c) => sum + c.max_points, 0)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600 mb-1">Weighted Score</p>
                <p className="text-3xl font-bold text-purple-600">
                  {calculateWeightedTotal()} / 100
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitClick}
              disabled={loading || !isFormValid()}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transform hover:scale-105 disabled:scale-100"
            >
              {loading ? "Submitting..." : "Submit Score"}
            </button>
          </div>
        </div>

        {/* Confirmation Dialog */}
        {showConfirmation && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center p-4 rounded-2xl">
            <motion.div
              className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
            >
              <div className="text-center mb-6">
                <div className="text-5xl mb-4">⚠️</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Confirm Submission
                </h3>
                <p className="text-gray-600">
                  Are you sure you want to submit this score? This action cannot
                  be undone.
                </p>
              </div>

              <div className="bg-purple-50 rounded-lg p-4 mb-6">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">
                    Final Score:
                  </span>
                  <span className="text-2xl font-bold text-purple-600">
                    {calculateWeightedTotal()} / 100
                  </span>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirmation(false)}
                  disabled={loading}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:from-gray-400 disabled:to-gray-400"
                >
                  {loading ? "Submitting..." : "Confirm"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

ScoringModal.propTypes = {
  project: PropTypes.object.isRequired,
  criteria: PropTypes.array.isRequired,
  accessCode: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  onScoreSubmitted: PropTypes.func.isRequired,
};

export default ScoringModal;
