const ProjectView = ({ groupData }) => {
  const project = groupData?.project || {};

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Project Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-start gap-6">
          <div className="w-24 h-24 bg-white/20 rounded-xl flex items-center justify-center text-4xl">
            📱
          </div>
          <div className="flex-1">
            <h2 className="text-3xl font-bold mb-2">
              {project?.app_name || "Project Name"}
            </h2>
            <p className="text-blue-100 mb-4">
              {project?.tagline || "Building something amazing"}
            </p>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                {project?.category || "Mobile App"}
              </span>
              {project?.status === "approved" && (
                <span className="px-3 py-1 bg-green-500 rounded-full text-sm font-medium">
                  ✓ Approved by Admin
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Project Description */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-3">Description</h3>
        <p className="text-gray-700 leading-relaxed">
          {project?.description ||
            "A comprehensive mobile application designed to solve real-world problems and provide value to users."}
        </p>
      </div>

      {/* Tech Stack */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Tech Stack</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-2">Frontend</p>
            <div className="flex flex-wrap gap-2">
              {project?.frontend_stack?.split(", ").map((tech, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium"
                >
                  {tech}
                </span>
              )) || <span className="text-gray-500">Not specified</span>}
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-2">Backend</p>
            <div className="flex flex-wrap gap-2">
              {project?.backend_stack?.split(", ").map((tech, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium"
                >
                  {tech}
                </span>
              )) || <span className="text-gray-500">Not specified</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Project Links</h3>
        <div className="space-y-3">
          {project?.github_url && (
            <a
              href={project.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span className="text-2xl">💻</span>
              <div>
                <p className="font-medium text-gray-900">GitHub Repository</p>
                <p className="text-sm text-blue-600">{project.github_url}</p>
              </div>
            </a>
          )}
          {project?.demo_url && (
            <a
              href={project.demo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span className="text-2xl">🌐</span>
              <div>
                <p className="font-medium text-gray-900">Live Demo</p>
                <p className="text-sm text-blue-600">{project.demo_url}</p>
              </div>
            </a>
          )}
          {project?.documentation_url && (
            <a
              href={project.documentation_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span className="text-2xl">📖</span>
              <div>
                <p className="font-medium text-gray-900">Documentation</p>
                <p className="text-sm text-blue-600">
                  {project.documentation_url}
                </p>
              </div>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectView;
