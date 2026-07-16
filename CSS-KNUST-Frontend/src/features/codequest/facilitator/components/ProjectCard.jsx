import { motion } from "framer-motion";
import PropTypes from "prop-types";

const ProjectCard = ({ project, isScored, onScoreClick, index }) => {
  return (
    <motion.div
      className={`bg-white rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer overflow-hidden ${
        isScored ? "opacity-60" : ""
      }`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={!isScored ? { scale: 1.02 } : {}}
    >
      {/* Header with Status Badge */}
      <div
        className={`p-4 ${
          isScored
            ? "bg-green-50"
            : "bg-gradient-to-r from-purple-50 to-indigo-50"
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-bold text-gray-900">
            Group {project.group?.group_number || "N/A"}
          </h3>
          {isScored && (
            <span className="px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full flex items-center gap-1">
              ✓ Scored
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600">
          {project.group?.group_name || "Team Name"}
        </p>
      </div>

      {/* Project Info */}
      <div className="p-6">
        <div className="flex items-start gap-3 mb-4">
          {project.logo_url ? (
            <img
              src={project.logo_url}
              alt={project.app_name}
              className="w-16 h-16 rounded-lg object-cover"
            />
          ) : (
            <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-indigo-400 rounded-lg flex items-center justify-center text-white text-2xl">
              📱
            </div>
          )}
          <div className="flex-1">
            <h4 className="font-bold text-gray-900 mb-1">
              {project.app_name || "Project Name"}
            </h4>
            <p className="text-sm text-gray-600 line-clamp-2">
              {project.description || "No description available"}
            </p>
          </div>
        </div>

        {/* Project Details */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>👤</span>
            <span>
              PM: {project.group?.project_manager?.student_name || "TBA"}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>👥</span>
            <span>{project.group?.members?.length || 0} members</span>
          </div>
          {project.inspiration_app && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>💡</span>
              <span>Inspired by: {project.inspiration_app}</span>
            </div>
          )}
        </div>

        {/* Tech Stack */}
        {(project.frontend_stack || project.backend_stack) && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2">Tech Stack:</p>
            <div className="flex flex-wrap gap-1">
              {project.frontend_stack
                ?.split(",")
                .slice(0, 2)
                .map((tech, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded"
                  >
                    {tech.trim()}
                  </span>
                ))}
              {project.backend_stack
                ?.split(",")
                .slice(0, 2)
                .map((tech, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded"
                  >
                    {tech.trim()}
                  </span>
                ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={onScoreClick}
          disabled={isScored}
          className={`w-full py-3 rounded-lg font-semibold transition-all ${
            isScored
              ? "bg-gray-200 text-gray-500 cursor-not-allowed"
              : "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white transform hover:scale-105"
          }`}
        >
          {isScored ? "✓ Scored" : "Score Now"}
        </button>
      </div>
    </motion.div>
  );
};

ProjectCard.propTypes = {
  project: PropTypes.object.isRequired,
  isScored: PropTypes.bool.isRequired,
  onScoreClick: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

export default ProjectCard;
