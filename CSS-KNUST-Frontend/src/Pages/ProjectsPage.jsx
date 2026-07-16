import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { motion, AnimatePresence } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import Navbar from "../Components/Navbar";
import { Footer } from "../Components/Footer/Footer";
import { BACKEND_HOST } from "../utils/config";
import {
  Github,
  ExternalLink,
  Calendar,
  Code,
  X,
  Search,
  Filter,
  Grid,
  List,
  ChevronDown,
  Sparkles,
  Eye,
  ArrowRight,
  Layers,
} from "lucide-react";
import Login from "./Login";
import SignUp from "./SignUp";
import { useNavigate } from "react-router-dom";
import ForgotPasswordModal from "./ForgotPasswordModal";
import ExecutiveLogin from "./ExecutiveLogin";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [filteredProjects, setFilteredProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // grid or list
  const [selectedProject, setSelectedProject] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortBy, setSortBy] = useState("newest"); // newest, oldest, featured

  const categories = [
    { value: "ALL", label: "All Projects" },
    { value: "WEB", label: "Web Development" },
    { value: "MOBILE", label: "Mobile Development" },
    { value: "AI_ML", label: "AI & Machine Learning" },
    { value: "DATA_SCIENCE", label: "Data Science" },
    { value: "CYBERSECURITY", label: "Cybersecurity" },
    { value: "IOT", label: "Internet of Things" },
    { value: "GAME", label: "Game Development" },
    { value: "BLOCKCHAIN", label: "Blockchain" },
    { value: "CLOUD", label: "Cloud Computing" },
    { value: "OTHER", label: "Other" },
  ];

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    let result = [...projects];

    // Filter by category
    if (selectedCategory !== "ALL") {
      result = result.filter((project) => project.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (project) =>
          project.title.toLowerCase().includes(query) ||
          project.description.toLowerCase().includes(query) ||
          project.technologies.toLowerCase().includes(query) ||
          project.members?.some((m) => m.name.toLowerCase().includes(query))
      );
    }

    // Sort
    if (sortBy === "newest") {
      result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sortBy === "oldest") {
      result.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (sortBy === "featured") {
      result.sort((a, b) => (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0));
    }

    setFilteredProjects(result);
  }, [selectedCategory, projects, searchQuery, sortBy]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_HOST}/projects/`);
      const data = await response.json();
      setProjects(data);
      setFilteredProjects(data);
    } catch (error) {
      console.error("Error fetching projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const getProjectCount = () => {
    return filteredProjects.length;
  };

  const navigate = useNavigate();

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
    setIsExecutiveOpen(false);
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const openProjectModal = (project) => {
    setSelectedProject(project);
    setShowModal(true);
  };

  const closeProjectModal = () => {
    setShowModal(false);
    setSelectedProject(null);
  };

  return (
    <>
      <Helmet>
        <title>Student Projects | CSS KNUST</title>
        <meta
          name="description"
          content="Explore innovative projects built by Computer Science students at KNUST. From web applications to AI systems, blockchain, IoT, and game development."
        />
        <meta
          name="keywords"
          content="KNUST projects, student projects, CS projects, web development, mobile apps, AI projects, machine learning, blockchain, IoT, game development, KNUST innovation"
        />
        <meta name="author" content="CSS KNUST" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cssknust.com/projects" />
        <meta property="og:title" content="Student Projects | CSS KNUST" />
        <meta
          property="og:description"
          content="Explore innovative projects built by Computer Science students at KNUST. Discover what our future tech leaders are creating."
        />
        <meta
          property="og:image"
          content="https://cssknust.com/og-projects.jpg"
        />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content="https://cssknust.com/projects" />
        <meta name="twitter:title" content="Student Projects | CSS KNUST" />
        <meta
          name="twitter:description"
          content="Explore innovative projects built by Computer Science students at KNUST."
        />
        <meta
          name="twitter:image"
          content="https://cssknust.com/og-projects.jpg"
        />

        {/* Additional Meta */}
        <link rel="canonical" href="https://cssknust.com/projects" />
        <meta name="robots" content="index, follow" />
        <meta name="language" content="English" />
        <meta name="revisit-after" content="7 days" />
      </Helmet>

      <Navbar onSignInClick={handleOpenLoginModal} />

      <div className="min-h-screen mt-12 bg-gradient-to-br from-slate-50 via-white to-blue-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-12">
            <motion.div
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-medium mb-4"
            >
              <Sparkles className="w-4 h-4" />
              Student Showcase
            </motion.div>
            <motion.h1
              variants={fadeIn("up", 0.5, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-4xl md:text-5xl mb-4 font-bold text-gray-900"
            >
              Student{" "}
              <span className="relative text-blue-600">
                Projects
                <motion.div
                  variants={underlineAnimation(0.7)}
                  initial="offscreen"
                  whileInView="onscreen"
                  exit="reverse"
                  className="absolute left-0 bottom-0 h-1 bg-blue-600"
                  style={{ width: "0%", height: "3px" }}
                />
              </span>
            </motion.h1>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Explore innovative projects built by our talented Computer Science
              students. From web applications to AI systems, discover what our
              future tech leaders are creating.
            </p>
          </div>

          {/* Search and Filter Bar */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search Input */}
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search projects, technologies, or team members..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              {/* Sort Dropdown */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="appearance-none pl-4 pr-10 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white cursor-pointer"
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="featured">Featured First</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
              </div>

              {/* View Mode Toggle */}
              <div className="flex bg-gray-100 rounded-xl p-1">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`p-2.5 rounded-lg transition-all ${
                    viewMode === "grid"
                      ? "bg-white shadow text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <Grid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={`p-2.5 rounded-lg transition-all ${
                    viewMode === "list"
                      ? "bg-white shadow text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Category Filters */}
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Filter by Category</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  key={category.value}
                  onClick={() => setSelectedCategory(category.value)}
                  className={`px-4 py-2.5 rounded-xl font-medium transition-all ${
                    selectedCategory === category.value
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-200"
                      : "bg-white text-gray-700 hover:bg-gray-50 shadow border border-gray-100"
                  }`}
                >
                  {category.label}
                  {selectedCategory === category.value && (
                    <span className="ml-2 text-sm bg-white/20 px-2 py-0.5 rounded-full">
                      {getProjectCount()}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Results Count */}
          {!loading && (
            <div className="flex items-center justify-between mb-6">
              <p className="text-gray-600">
                Showing{" "}
                <span className="font-semibold text-gray-900">
                  {filteredProjects.length}
                </span>{" "}
                {filteredProjects.length === 1 ? "project" : "projects"}
                {selectedCategory !== "ALL" && (
                  <span className="text-blue-600">
                    {" "}
                    in {categories.find((c) => c.value === selectedCategory)?.label}
                  </span>
                )}
              </p>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600"></div>
                <Code className="w-6 h-6 text-blue-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
              <p className="mt-4 text-gray-600 font-medium">Loading amazing projects...</p>
            </div>
          )}

          {/* Projects Grid View */}
          {!loading && filteredProjects.length > 0 && viewMode === "grid" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProjects.map((project, index) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <ProjectCard project={project} onClick={() => openProjectModal(project)} />
                </motion.div>
              ))}
            </div>
          )}

          {/* Projects List View */}
          {!loading && filteredProjects.length > 0 && viewMode === "list" && (
            <div className="space-y-4">
              {filteredProjects.map((project, index) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                >
                  <ProjectListItem project={project} onClick={() => openProjectModal(project)} />
                </motion.div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && filteredProjects.length === 0 && (
            <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mb-6">
                <Layers className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No Projects Found</h3>
              <p className="text-gray-600 max-w-md mx-auto">
                {searchQuery
                  ? `No projects match "${searchQuery}". Try adjusting your search.`
                  : "No projects in this category yet. Check back later!"}
              </p>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="mt-4 px-4 py-2 text-blue-600 font-medium hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Clear Search
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Project Details Modal */}
      <AnimatePresence>
        {showModal && selectedProject && (
          <ProjectModal project={selectedProject} onClose={closeProjectModal} />
        )}
      </AnimatePresence>

      <Footer />
      {isLoginModalOpen && (
        <Login
          onClose={handleCloseModals}
          switchToSignup={handleOpenSignupModal}
          switchToForgot={handleOpen}
          action={() => navigate("/dashboard/home")}
          switchToExecutive={handleExecutiveOpen}
        />
      )}

      {isSignupModalOpen && (
        <SignUp
          onClose={handleCloseModals}
          switchToLogin={handleOpenLoginModal}
        />
      )}
      {isOpen && (
        <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
      )}
      {isExecutiveOpen && (
        <ExecutiveLogin
          onClose={handleOpenLoginModal}
          switchToSignup={handleOpenSignupModal}
          switchToForgot={handleOpen}
        />
      )}
    </>
  );
}

function ProjectCard({ project, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer group flex flex-col h-full"
    >
      {/* Project Image */}
      <div className="relative h-52 bg-gradient-to-br from-blue-500 to-purple-600 overflow-hidden">
        {project.image ? (
          <img
            src={project.image}
            alt={project.title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Code className="w-16 h-16 text-white/30" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        {project.is_featured && (
          <div className="absolute top-3 right-3">
            <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1 shadow-lg">
              <Sparkles className="w-3 h-3" />
              Featured
            </span>
          </div>
        )}
        {/* View Details Overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="bg-white/90 backdrop-blur-sm text-gray-900 px-4 py-2 rounded-full font-medium flex items-center gap-2">
            <Eye className="w-4 h-4" />
            View Details
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col">
        {/* Category Badge */}
        <div className="mb-3">
          <span className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg">
            {project.category_display}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
          {project.title}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 flex-1 line-clamp-2">
          {project.short_description || project.description}
        </p>

        {/* Team Members Preview */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex -space-x-2">
            {project.members?.slice(0, 3).map((member) => (
              <div
                key={member.id}
                className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-white"
                title={member.name}
              >
                {member.name.charAt(0)}
              </div>
            ))}
            {project.members?.length > 3 && (
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-xs font-bold border-2 border-white">
                +{project.members.length - 3}
              </div>
            )}
          </div>
          <span className="text-xs text-gray-500">
            {project.members?.length || 0} team member{project.members?.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Technologies */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {project.technology_list?.slice(0, 3).map((tech, index) => (
            <span
              key={index}
              className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium"
            >
              {tech}
            </span>
          ))}
          {project.technology_list?.length > 3 && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
              +{project.technology_list.length - 3}
            </span>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Calendar className="w-3.5 h-3.5" />
            <span>{project.academic_year}</span>
          </div>
          <span className="flex items-center gap-1 text-blue-600 text-sm font-medium group-hover:gap-2 transition-all">
            View Project <ArrowRight className="w-4 h-4" />
          </span>
        </div>
      </div>
    </div>
  );
}

function ProjectListItem({ project, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group"
    >
      <div className="flex flex-col sm:flex-row">
        {/* Project Image */}
        <div className="sm:w-48 h-40 sm:h-auto relative overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0">
          {project.image ? (
            <img
              src={project.image}
              alt={project.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Code className="w-12 h-12 text-white/30" />
            </div>
          )}
          {project.is_featured && (
            <div className="absolute top-2 left-2">
              <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                Featured
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 p-5">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg">
                  {project.category_display}
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {project.academic_year}
                </span>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                {project.title}
              </h3>
              <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                {project.short_description || project.description}
              </p>

              {/* Technologies */}
              <div className="flex flex-wrap gap-1.5">
                {project.technology_list?.slice(0, 5).map((tech, index) => (
                  <span
                    key={index}
                    className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium"
                  >
                    {tech}
                  </span>
                ))}
                {project.technology_list?.length > 5 && (
                  <span className="px-2 py-0.5 text-gray-500 text-xs">
                    +{project.technology_list.length - 5} more
                  </span>
                )}
              </div>
            </div>

            {/* Team & Action */}
            <div className="flex sm:flex-col items-center sm:items-end gap-3">
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  {project.members?.slice(0, 3).map((member) => (
                    <div
                      key={member.id}
                      className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-white"
                      title={member.name}
                    >
                      {member.name.charAt(0)}
                    </div>
                  ))}
                </div>
                <span className="text-xs text-gray-500">
                  {project.members?.length || 0} members
                </span>
              </div>
              <button className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Eye className="w-4 h-4" />
                View
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProjectModal({ project, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        transition={{ type: "spring", duration: 0.5 }}
        className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header with Image */}
        <div className="relative h-72 bg-gradient-to-br from-blue-600 to-purple-700 overflow-hidden">
          {project.image ? (
            <img
              src={project.image}
              alt={project.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Code className="w-24 h-24 text-white/20" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2.5 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors backdrop-blur-sm"
          >
            <X className="w-6 h-6" />
          </button>

          {/* Featured Badge */}
          {project.is_featured && (
            <div className="absolute top-4 left-4">
              <span className="bg-yellow-400 text-yellow-900 text-sm font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" />
                Featured Project
              </span>
            </div>
          )}

          {/* Title Section */}
          <div className="absolute bottom-0 left-0 right-0 p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="inline-block px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full backdrop-blur-sm">
                {project.category_display}
              </span>
              <span className="inline-flex px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full backdrop-blur-sm items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" />
                {project.academic_year}
              </span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              {project.title}
            </h2>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-18rem)]">
          {/* Description */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-1 h-5 bg-blue-600 rounded-full"></div>
              About This Project
            </h3>
            <p className="text-gray-600 leading-relaxed whitespace-pre-line">
              {project.description}
            </p>
          </div>

          {/* Team Members */}
          {project.members && project.members.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <div className="w-1 h-5 bg-purple-600 rounded-full"></div>
                Team Members ({project.members.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {project.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-4 bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
                  >
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                      {member.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">
                        {member.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {member.year_display} • {member.program_display}
                      </p>
                      {member.role && (
                        <p className="text-xs text-blue-600 font-medium mt-0.5">
                          {member.role}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technologies */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <div className="w-1 h-5 bg-green-600 rounded-full"></div>
              Technologies Used
            </h3>
            <div className="flex flex-wrap gap-2">
              {project.technology_list?.map((tech, index) => (
                <span
                  key={index}
                  className="px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 text-gray-700 text-sm font-medium rounded-xl border border-blue-100"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* Additional Images */}
          {(project.image2 || project.image3) && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <div className="w-1 h-5 bg-orange-600 rounded-full"></div>
                More Screenshots
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {project.image2 && (
                  <img
                    src={project.image2}
                    alt={`${project.title} screenshot 2`}
                    className="w-full h-48 object-cover rounded-xl"
                  />
                )}
                {project.image3 && (
                  <img
                    src={project.image3}
                    alt={`${project.title} screenshot 3`}
                    className="w-full h-48 object-cover rounded-xl"
                  />
                )}
              </div>
            </div>
          )}

          {/* Action Links */}
          <div className="flex flex-wrap gap-3 pt-6 border-t border-gray-200">
            {project.github_url && (
              <a
                href={project.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-colors font-semibold shadow-lg hover:shadow-xl"
              >
                <Github className="w-5 h-5" />
                View Source Code
              </a>
            )}
            {project.demo_url && (
              <a
                href={project.demo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-colors font-semibold shadow-lg hover:shadow-xl"
              >
                <ExternalLink className="w-5 h-5" />
                View Live Demo
              </a>
            )}
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-semibold ml-auto"
            >
              Close
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
