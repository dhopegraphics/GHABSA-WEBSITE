const GroupDetailView = ({ group, onBack }) => {
  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
      >
        ← Back to Groups
      </button>

      {/* Project Info */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-start gap-6">
          <div className="w-24 h-24 bg-white/20 rounded-xl flex items-center justify-center text-4xl">
            📱
          </div>
          <div className="flex-1">
            <h2 className="text-3xl font-bold mb-2">
              {group.project?.app_name || "Project Name"}
            </h2>
            <p className="text-blue-100 mb-4">
              {group.project?.tagline || "Building something amazing"}
            </p>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                {group.project?.category || "Mobile App"}
              </span>
              {group.project?.status === "approved" && (
                <span className="px-3 py-1 bg-green-500 rounded-full text-sm font-medium">
                  ✓ Approved
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Members */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Team Members</h3>
          <div className="space-y-3">
            {group.members?.map((member, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                  {member.name?.charAt(0) || "M"}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">
                    {member.name}
                    {member.is_pm && (
                      <span className="ml-2 text-yellow-600">⭐ PM</span>
                    )}
                  </p>
                  <p className="text-sm text-gray-600">{member.student_id}</p>
                </div>
                {member.role && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {member.role}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Project Details */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Project Details
          </h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-2">Description</p>
              <p className="text-gray-800">
                {group.project?.description || "No description provided yet."}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Tech Stack</p>
              <div className="flex flex-wrap gap-2">
                {group.project?.frontend_stack?.split(", ").map((tech, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm"
                  >
                    {tech}
                  </span>
                ))}
                {group.project?.backend_stack?.split(", ").map((tech, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Project Links</h3>
        <div className="space-y-3">
          {group.project?.github_url && (
            <a
              href={group.project.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span className="text-2xl">💻</span>
              <div>
                <p className="font-medium text-gray-900">GitHub Repository</p>
                <p className="text-sm text-blue-600">
                  {group.project.github_url}
                </p>
              </div>
            </a>
          )}
          {group.project?.demo_url && (
            <a
              href={group.project.demo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span className="text-2xl">🌐</span>
              <div>
                <p className="font-medium text-gray-900">Live Demo</p>
                <p className="text-sm text-blue-600">
                  {group.project.demo_url}
                </p>
              </div>
            </a>
          )}
        </div>
      </div>

      {/* Tasks Overview */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Tasks Overview</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-3xl font-bold text-gray-600">
              {group.tasks?.filter((t) => t.status === "todo").length || 0}
            </p>
            <p className="text-sm text-gray-600 mt-1">To Do</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <p className="text-3xl font-bold text-blue-600">
              {group.tasks?.filter((t) => t.status === "in_progress").length ||
                0}
            </p>
            <p className="text-sm text-gray-600 mt-1">In Progress</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <p className="text-3xl font-bold text-green-600">
              {group.tasks?.filter((t) => t.status === "completed").length || 0}
            </p>
            <p className="text-sm text-gray-600 mt-1">Completed</p>
          </div>
        </div>
      </div>

      {/* Final Score (if available) */}
      {group.final_score && (
        <div className="bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl shadow-lg p-6 text-white text-center">
          <h3 className="text-xl font-bold mb-2">Final Score</h3>
          <p className="text-4xl font-bold">
            {group.final_score.total_score}/100
          </p>
          <p className="text-yellow-100 mt-2">
            Rank: {group.final_score.rank}
            {group.final_score.rank === 1
              ? "st"
              : group.final_score.rank === 2
              ? "nd"
              : group.final_score.rank === 3
              ? "rd"
              : "th"}
          </p>
        </div>
      )}
    </div>
  );
};

export default GroupDetailView;
