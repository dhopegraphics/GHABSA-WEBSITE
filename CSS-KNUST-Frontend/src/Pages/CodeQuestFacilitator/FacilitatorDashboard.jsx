import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import ProjectCard from "../../features/codequest/facilitator/components/ProjectCard";
import ScoringModal from "../../features/codequest/facilitator/components/ScoringModal";

const FacilitatorDashboard = () => {
  const navigate = useNavigate();
  const [facilitatorData, setFacilitatorData] = useState(null);
  const [projects, setProjects] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [scoredProjects, setScoredProjects] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showScoringModal, setShowScoringModal] = useState(false);

  const accessCode =
    localStorage.getItem("facilitator_access_code") ||
    sessionStorage.getItem("facilitator_access_code");

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch projects
      const projectsResponse = await axios.get(
        `/codequest/scoring/projects/?access_code=${accessCode}`
      );

      // Fetch criteria
      const criteriaResponse = await axios.get(
        `/codequest/scoring/criteria/?access_code=${accessCode}`
      );

      // Fetch facilitator's scores
      const scoresResponse = await axios.get(
        `/codequest/scoring/my-scores/?access_code=${accessCode}`
      );

      setProjects(projectsResponse.data.projects || []);
      setCriteria(criteriaResponse.data.criteria || []);

      // Track which projects have been fully scored
      const scored = new Set();
      scoresResponse.data.scores?.forEach((score) => {
        const key = `${score.project}`;
        scored.add(key);
      });
      setScoredProjects(scored);

      setLoading(false);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError("Failed to load dashboard data");
      setLoading(false);

      if (err.response?.status === 401) {
        navigate("/code-quest-facilitators/login");
      }
    }
  };

  useEffect(() => {
    if (!accessCode) {
      navigate("/code-quest-facilitators/login");
      return;
    }

    const storedData = localStorage.getItem("facilitator_data");
    if (storedData) {
      setFacilitatorData(JSON.parse(storedData));
    }

    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessCode, navigate]);

  const handleLogout = () => {
    localStorage.removeItem("facilitator_access_code");
    sessionStorage.removeItem("facilitator_access_code");
    localStorage.removeItem("facilitator_data");
    navigate("/code-quest-facilitators/login");
  };

  const handleScoreProject = (project) => {
    setSelectedProject(project);
    setShowScoringModal(true);
  };

  const handleScoreSubmitted = (projectId) => {
    setScoredProjects((prev) => new Set([...prev, `${projectId}`]));
    setShowScoringModal(false);
    setSelectedProject(null);
    fetchDashboardData(); // Refresh data
  };

  const handleCloseModal = () => {
    setShowScoringModal(false);
    setSelectedProject(null);
  };

  const totalProjects = projects.length;
  const scoredCount = scoredProjects.size;
  const progressPercentage =
    totalProjects > 0 ? (scoredCount / totalProjects) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-1">
                Welcome, {facilitatorData?.name || "Facilitator"}! 👋
              </h1>
              <p className="text-purple-100">
                Code Quest {facilitatorData?.event?.academic_year} -{" "}
                {facilitatorData?.event?.semester}
              </p>
              <p className="text-purple-200 text-sm mt-1">
                Presentation Day Scoring
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg font-medium transition-colors backdrop-blur-sm"
            >
              Logout
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-purple-100">
                Scoring Progress
              </span>
              <span className="text-sm font-bold text-white">
                {scoredCount} / {totalProjects} Projects Scored
              </span>
            </div>
            <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden backdrop-blur-sm">
              <motion.div
                className="bg-white h-3 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progressPercentage}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div
            className="bg-white rounded-xl shadow-md p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                📊
              </div>
              <div>
                <p className="text-gray-600 text-sm">Total Projects</p>
                <p className="text-3xl font-bold text-gray-900">
                  {totalProjects}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="bg-white rounded-xl shadow-md p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
                ✅
              </div>
              <div>
                <p className="text-gray-600 text-sm">Scored</p>
                <p className="text-3xl font-bold text-green-600">
                  {scoredCount}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="bg-white rounded-xl shadow-md p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center text-2xl">
                ⏳
              </div>
              <div>
                <p className="text-gray-600 text-sm">Remaining</p>
                <p className="text-3xl font-bold text-orange-600">
                  {totalProjects - scoredCount}
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Projects Grid */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Projects to Score
          </h2>

          {projects.length === 0 ? (
            <div className="bg-white rounded-xl shadow-md p-12 text-center">
              <div className="text-6xl mb-4">📱</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                No Projects Available
              </h3>
              <p className="text-gray-600">
                Projects will appear here once they are submitted and approved.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project, index) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  isScored={scoredProjects.has(`${project.id}`)}
                  onScoreClick={() => handleScoreProject(project)}
                  index={index}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Scoring Modal */}
      <AnimatePresence>
        {showScoringModal && selectedProject && (
          <ScoringModal
            project={selectedProject}
            criteria={criteria}
            accessCode={accessCode}
            onClose={handleCloseModal}
            onScoreSubmitted={handleScoreSubmitted}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default FacilitatorDashboard;
