import { motion } from "framer-motion";
import { Check, Vote } from "lucide-react";

/**
 * PollOptionCard - Display a single poll/referendum option
 * For poll events where users vote on options rather than candidates
 */
export function PollOptionCard({
  option,
  isSelected,
  onSelect,
  canVote,
  showResults,
  totalVotes,
  eventType,
}) {
  // Calculate percentage
  const percentage =
    showResults && totalVotes > 0
      ? Math.round((option.vote_count / totalVotes) * 100)
      : option.percentage || 0;

  // Determine display color (use option color or default based on position)
  const optionColor = option.color || "#6366f1"; // Default to indigo

  return (
    <motion.div
      whileHover={{ scale: canVote ? 1.02 : 1 }}
      whileTap={{ scale: canVote ? 0.98 : 1 }}
      className={`relative bg-white rounded-xl shadow-md overflow-hidden border-2 transition-all duration-300 ${
        isSelected
          ? "border-indigo-500 ring-2 ring-indigo-200"
          : canVote
          ? "border-gray-200 hover:border-indigo-300 cursor-pointer"
          : "border-gray-200"
      }`}
      onClick={() => canVote && onSelect && onSelect(option)}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-3 right-3 bg-indigo-600 text-white rounded-full p-1 z-10">
          <Check size={16} />
        </div>
      )}

      {/* Option Image (if available) */}
      {(option.image_url_display || option.image) && (
        <div className="relative h-40 bg-gray-100">
          <img
            src={option.image_url_display || option.image}
            alt={option.option_text}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="p-4">
        {/* Option Text */}
        <div className="flex items-start gap-3 mb-3">
          {!option.image_url_display && !option.image && (
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: `${optionColor}20` }}
            >
              <Vote size={20} style={{ color: optionColor }} />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">
              {option.option_text}
            </h3>
            {option.description && (
              <p className="text-sm text-gray-600 mt-1">{option.description}</p>
            )}
          </div>
        </div>

        {/* Results Bar (show when results are visible) */}
        {showResults && (
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">
                {option.vote_count || 0} votes
              </span>
              <span className="text-sm font-bold" style={{ color: optionColor }}>
                {percentage}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="h-full rounded-full"
                style={{ backgroundColor: optionColor }}
              />
            </div>
          </div>
        )}

        {/* Vote Button (when voting is open and no results shown) */}
        {canVote && !showResults && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect && onSelect(option);
            }}
            className={`w-full mt-4 py-2.5 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              isSelected
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-indigo-50 hover:text-indigo-600"
            }`}
          >
            {isSelected ? (
              <>
                <Check size={18} />
                Selected
              </>
            ) : (
              <>
                <Vote size={18} />
                Select
              </>
            )}
          </button>
        )}
      </div>

      {/* Referendum-specific styling */}
      {eventType === "referendum" && (
        <div
          className="h-1 w-full"
          style={{ backgroundColor: optionColor }}
        />
      )}
    </motion.div>
  );
}

/**
 * PollQuestionSection - Renders a poll question with its options
 */
export function PollQuestionSection({
  question,
  description,
  options,
  selectedOption,
  onSelectOption,
  canVote,
  hasVotedInCategory = false,
  showResults,
  eventType,
}) {
  // Calculate total votes for this question
  const totalVotes = options.reduce(
    (sum, opt) => sum + (opt.vote_count || 0),
    0
  );

  return (
    <div className="mb-10">
      {/* Question Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-2xl font-bold text-gray-900">{question}</h2>
          {hasVotedInCategory && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
              <Check size={14} />
              Voted
            </span>
          )}
        </div>
        {description && (
          <p className="text-gray-600 mt-2">{description}</p>
        )}
        {showResults && (
          <p className="text-sm text-indigo-600 font-medium mt-2">
            Total votes: {totalVotes}
          </p>
        )}
        {hasVotedInCategory && !showResults && (
          <p className="text-sm text-green-600 mt-2">
            You have already voted in this category.
          </p>
        )}
      </div>

      {/* Options Grid */}
      <div className={`grid gap-4 ${
        options.length <= 2 
          ? "grid-cols-1 sm:grid-cols-2" 
          : options.length === 3 
          ? "grid-cols-1 sm:grid-cols-3" 
          : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
      }`}>
        {options.map((option) => (
          <PollOptionCard
            key={option.id}
            option={option}
            isSelected={selectedOption?.id === option.id}
            onSelect={onSelectOption}
            canVote={canVote && !hasVotedInCategory}
            showResults={showResults}
            totalVotes={totalVotes}
            eventType={eventType}
          />
        ))}
      </div>
    </div>
  );
}

export default PollOptionCard;
