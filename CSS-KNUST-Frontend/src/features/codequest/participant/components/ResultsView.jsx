const ResultsView = ({ groupData }) => {
  const results = groupData?.final_score || null;

  return (
    <div className="max-w-4xl mx-auto">
      {results ? (
        <div className="space-y-6">
          {/* Score Header */}
          <div className="bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl shadow-lg p-8 text-white text-center">
            <div className="text-6xl mb-4">
              {results.rank === 1
                ? "🥇"
                : results.rank === 2
                ? "🥈"
                : results.rank === 3
                ? "🥉"
                : "🏆"}
            </div>
            <h2 className="text-4xl font-bold mb-2">
              {results.total_score}/100
            </h2>
            <p className="text-2xl text-yellow-100">
              Rank: {results.rank}
              {results.rank === 1
                ? "st"
                : results.rank === 2
                ? "nd"
                : results.rank === 3
                ? "rd"
                : "th"}{" "}
              Place
            </p>
          </div>

          {/* Score Breakdown */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">
              Score Breakdown
            </h3>
            <div className="space-y-4">
              {results.criteria_scores?.map((criterion, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">
                      {criterion.name}
                    </span>
                    <span className="font-bold text-blue-600">
                      {criterion.score}/{criterion.max_points} (
                      {Math.round(
                        (criterion.score / criterion.max_points) * 100
                      )}
                      %)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all"
                      style={{
                        width: `${
                          (criterion.score / criterion.max_points) * 100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Facilitator Comments */}
          {results.comments && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Facilitator Comments
              </h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 italic">
                  &quot;{results.comments}&quot;
                </p>
              </div>
            </div>
          )}

          {/* Congratulations Card */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 text-center">
            <p className="text-lg text-gray-700">
              🎉 Congratulations on completing Code Quest! 🎉
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Results Not Published Yet
          </h3>
          <p className="text-gray-600">
            The final scores will be published after the presentation day.
            You&apos;ll be notified via email when results are available.
          </p>
        </div>
      )}
    </div>
  );
};

export default ResultsView;
