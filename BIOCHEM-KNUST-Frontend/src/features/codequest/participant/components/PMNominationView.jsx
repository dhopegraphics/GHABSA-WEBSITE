import { useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";

const PMNominationView = ({ groupData, userData, onNominationSubmit }) => {
  const [showNominationModal, setShowNominationModal] = useState(false);
  const [statement, setStatement] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isNominee = groupData?.nominees?.some(
    (n) => n.student_id === userData?.student_id
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const accessKey =
        localStorage.getItem("cq_access_key") ||
        sessionStorage.getItem("cq_access_key");

      await axios.post("/codequest/pm/nominate/", {
        access_key: accessKey,
        statement: statement,
      });

      setShowNominationModal(false);
      onNominationSubmit();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to submit nomination");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Nomination Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <span className="text-5xl">📢</span>
          <div>
            <h2 className="text-3xl font-bold mb-2">
              Project Manager Election Open!
            </h2>
            <p className="text-blue-100">
              Nomination Deadline:{" "}
              {groupData?.nomination_deadline
                ? new Date(groupData.nomination_deadline).toLocaleString()
                : "TBD"}
            </p>
          </div>
        </div>
        {!isNominee && (
          <button
            onClick={() => setShowNominationModal(true)}
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            Nominate Yourself as PM
          </button>
        )}
      </div>

      {/* Current Nominees */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Current Nominees ({groupData?.nominees?.length || 0})
        </h3>
        {groupData?.nominees?.length > 0 ? (
          <div className="space-y-3">
            {groupData.nominees.map((nominee, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-2 ${
                  nominee.student_id === userData?.student_id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                      {nominee.name?.charAt(0) || "N"}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">
                        {nominee.name}
                        {nominee.student_id === userData?.student_id && (
                          <span className="ml-2 text-blue-600 text-sm">
                            (You)
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-gray-600">
                        {nominee.student_id}
                      </p>
                    </div>
                  </div>
                </div>
                {nominee.statement && (
                  <p className="text-gray-700 text-sm italic mt-2">
                    &quot;{nominee.statement}&quot;
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">
            No nominations yet. Be the first to nominate yourself!
          </p>
        )}
      </div>

      {/* Nomination Modal */}
      {showNominationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Nominate Yourself as PM
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={userData?.student_name || ""}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Student ID
                </label>
                <input
                  type="text"
                  value={userData?.student_id || ""}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Why do you want to be PM? *
                </label>
                <textarea
                  value={statement}
                  onChange={(e) => setStatement(e.target.value)}
                  rows={5}
                  required
                  maxLength={200}
                  placeholder="Share your motivation and what makes you a good candidate..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-sm text-gray-500 mt-1">
                  {statement.length}/200 characters
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowNominationModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || statement.length < 10}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition-colors"
                >
                  {loading ? "Submitting..." : "Submit Nomination"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default PMNominationView;
