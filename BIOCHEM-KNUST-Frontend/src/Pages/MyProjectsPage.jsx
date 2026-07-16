import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  ExternalLink,
  Github,
  Calendar,
  Code,
  Users,
  Loader2,
  AlertCircle,
  Sparkles,
  Edit,
  Trash2,
  Send,
  RotateCcw,
  X,
  FileEdit,
  AlertTriangle,
} from "lucide-react";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

const STATUS_CONFIG = {
  pending: {
    label: "Pending Review",
    color: "bg-yellow-100 text-yellow-800 border-yellow-300",
    icon: Clock,
    iconColor: "text-yellow-600",
    description: "Awaiting approval from an executive",
  },
  approved: {
    label: "Approved",
    color: "bg-green-100 text-green-800 border-green-300",
    icon: CheckCircle,
    iconColor: "text-green-600",
    description: "Your project is live on the public page",
  },
  rejected: {
    label: "Needs Changes",
    color: "bg-red-100 text-red-800 border-red-300",
    icon: XCircle,
    iconColor: "text-red-600",
    description: "Please review feedback and resubmit",
  },
  update_pending: {
    label: "Update Requested",
    color: "bg-purple-100 text-purple-800 border-purple-300",
    icon: Send,
    iconColor: "text-purple-600",
    description: "Waiting for admin to approve your update request",
  },
  update_in_progress: {
    label: "Update In Progress",
    color: "bg-orange-100 text-orange-800 border-orange-300",
    icon: FileEdit,
    iconColor: "text-orange-600",
    description: "You can now edit. Mark complete when done.",
  },
};

export function MyProjectsPage() {
  const navigate = useNavigate();
  const axiosInstance = useAxiosWithRefresh();
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({ total: 0, approved: 0, pending: 0, update_pending: 0, update_in_progress: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedProject, setSelectedProject] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  
  // Action states
  const [actionLoading, setActionLoading] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showUpdateRequestModal, setShowUpdateRequestModal] = useState(null);
  const [updateReason, setUpdateReason] = useState("");

  useEffect(() => {
    if (hasFetched) return;
    
    const fetchMyProjects = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await axiosInstance.get("/projects/my-projects/");
        setProjects(response.data.projects || []);
        setStats(response.data.stats || { total: 0, approved: 0, pending: 0, update_pending: 0, update_in_progress: 0 });
      } catch (err) {
        console.error("Error fetching projects:", err);
        setError("Failed to load your projects. Please try again.");
      } finally {
        setLoading(false);
        setHasFetched(true);
      }
    };
    
    fetchMyProjects();
  }, [axiosInstance, hasFetched]);

  const getProjectStatus = (project) => {
    if (project.update_status === 'pending') return "update_pending";
    if (project.update_status === 'in_progress') return "update_in_progress";
    if (project.is_approved) return "approved";
    return "pending";
  };

  const openProjectDetails = (project) => {
    setSelectedProject(project);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedProject(null);
  };

  // Delete project
  const handleDelete = async (projectId) => {
    setActionLoading(projectId);
    try {
      await axiosInstance.delete(`/projects/${projectId}/`);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      setStats(prev => ({ ...prev, total: prev.total - 1, pending: prev.pending - 1 }));
      setShowDeleteConfirm(null);
    } catch (err) {
      console.error("Error deleting project:", err);
      setError(err.response?.data?.error || "Failed to delete project.");
    } finally {
      setActionLoading(null);
    }
  };

  // Request update
  const handleRequestUpdate = async (projectId) => {
    if (!updateReason.trim()) {
      setError("Please provide a reason for the update request.");
      return;
    }
    
    setActionLoading(projectId);
    try {
      await axiosInstance.post(`/projects/${projectId}/request-update/`, { reason: updateReason });
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, update_status: 'pending', update_request_reason: updateReason } : p
      ));
      setStats(prev => ({ ...prev, update_pending: (prev.update_pending || 0) + 1 }));
      setShowUpdateRequestModal(null);
      setUpdateReason("");
    } catch (err) {
      console.error("Error requesting update:", err);
      setError(err.response?.data?.error || "Failed to request update.");
    } finally {
      setActionLoading(null);
    }
  };

  // Cancel update request
  const handleCancelUpdateRequest = async (projectId) => {
    setActionLoading(projectId);
    try {
      await axiosInstance.post(`/projects/${projectId}/cancel-update/`);
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, update_status: 'none', update_request_reason: '' } : p
      ));
      setStats(prev => ({ ...prev, update_pending: Math.max(0, (prev.update_pending || 0) - 1) }));
    } catch (err) {
      console.error("Error cancelling update request:", err);
      setError(err.response?.data?.error || "Failed to cancel update request.");
    } finally {
      setActionLoading(null);
    }
  };

  // Complete update
  const handleCompleteUpdate = async (projectId) => {
    setActionLoading(projectId);
    try {
      await axiosInstance.post(`/projects/${projectId}/complete-update/`);
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, update_status: 'none', is_approved: false } : p
      ));
      setStats(prev => ({ 
        ...prev, 
        update_in_progress: Math.max(0, (prev.update_in_progress || 0) - 1),
        approved: Math.max(0, prev.approved - 1),
        pending: prev.pending + 1
      }));
    } catch (err) {
      console.error("Error completing update:", err);
      setError(err.response?.data?.error || "Failed to complete update.");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <Code className="w-6 h-6 text-white" />
              </div>
              My Projects
            </h1>
            <p className="text-gray-600 mt-1">
              Track and manage your submitted projects
            </p>
          </div>
          <button
            onClick={() => navigate("/dashboard/submit-project")}
            className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
          >
            <Plus className="w-5 h-5" />
            Submit New Project
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">Total</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.total}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-xl">
                <Code className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">Approved</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{stats.approved}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">Pending</p>
                <p className="text-3xl font-bold text-yellow-600 mt-1">{stats.pending}</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-xl">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">Updating</p>
                <p className="text-3xl font-bold text-orange-600 mt-1">
                  {(stats.update_pending || 0) + (stats.update_in_progress || 0)}
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-xl">
                <FileEdit className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-800 flex-1">{error}</p>
            <button onClick={() => setError("")} className="text-red-600 hover:text-red-800">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
            <p className="text-gray-600">Loading your projects...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && projects.length === 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full mb-6">
              <Sparkles className="w-10 h-10 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              No Projects Yet
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Start showcasing your amazing work to the CS KNUST community!
              Submit your first project and inspire fellow students.
            </p>
            <button
              onClick={() => navigate("/dashboard/submit-project")}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg"
            >
              <Plus className="w-5 h-5" />
              Submit Your First Project
            </button>
          </div>
        )}

        {/* Projects List */}
        {!loading && projects.length > 0 && (
          <div className="space-y-4">
            {projects.map((project) => {
              const status = getProjectStatus(project);
              const statusConfig = STATUS_CONFIG[status];
              const StatusIcon = statusConfig.icon;
              const canEdit = project.can_edit;
              const canDelete = project.can_delete;

              return (
                <div
                  key={project.id}
                  className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 group"
                >
                  <div className="flex flex-col lg:flex-row">
                    {/* Project Image */}
                    <div className="lg:w-64 h-48 lg:h-auto relative overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600">
                      {project.image ? (
                        <img
                          src={project.image}
                          alt={project.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Code className="w-16 h-16 text-white/50" />
                        </div>
                      )}
                      {project.is_featured && (
                        <div className="absolute top-3 left-3">
                          <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            Featured
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Project Info */}
                    <div className="flex-1 p-6">
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                        <div className="flex-1">
                          {/* Status Badge */}
                          <div className="flex items-center gap-3 mb-3 flex-wrap">
                            <span
                              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${statusConfig.color}`}
                            >
                              <StatusIcon
                                className={`w-4 h-4 ${statusConfig.iconColor}`}
                              />
                              {statusConfig.label}
                            </span>
                            <span className="text-sm text-gray-500">
                              {statusConfig.description}
                            </span>
                          </div>

                          {/* Update Request Reason */}
                          {project.update_status === 'pending' && project.update_request_reason && (
                            <div className="mb-3 bg-purple-50 border border-purple-100 rounded-lg p-3 text-sm">
                              <p className="text-purple-700 font-medium">Update Reason:</p>
                              <p className="text-purple-600">{project.update_request_reason}</p>
                            </div>
                          )}

                          {/* Title */}
                          <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                            {project.title}
                          </h3>

                          {/* Category */}
                          <span className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-sm font-medium rounded-lg mb-3">
                            {project.category_display}
                          </span>

                          {/* Description */}
                          <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                            {project.short_description || project.description}
                          </p>

                          {/* Meta Info */}
                          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                            <div className="flex items-center gap-1.5">
                              <Calendar className="w-4 h-4" />
                              <span>{project.academic_year}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Users className="w-4 h-4" />
                              <span>{project.team_size || project.members?.length || 0} member(s)</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Clock className="w-4 h-4" />
                              <span>
                                Submitted{" "}
                                {new Date(
                                  project.created_at
                                ).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-wrap sm:flex-col gap-2">
                          <button
                            onClick={() => openProjectDetails(project)}
                            className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
                          >
                            <Eye className="w-4 h-4" />
                            View
                          </button>
                          
                          {/* Edit Button */}
                          {canEdit && (
                            <button
                              onClick={() => navigate(`/dashboard/edit-project/${project.id}`)}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors font-medium text-sm"
                            >
                              <Edit className="w-4 h-4" />
                              Edit
                            </button>
                          )}
                          
                          {/* Request Update Button (for approved projects without pending request) */}
                          {status === 'approved' && project.update_status === 'none' && (
                            <button
                              onClick={() => setShowUpdateRequestModal(project.id)}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors font-medium text-sm"
                            >
                              <Send className="w-4 h-4" />
                              Request Update
                            </button>
                          )}
                          
                          {/* Cancel Update Request */}
                          {project.update_status === 'pending' && (
                            <button
                              onClick={() => handleCancelUpdateRequest(project.id)}
                              disabled={actionLoading === project.id}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm disabled:opacity-50"
                            >
                              {actionLoading === project.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <RotateCcw className="w-4 h-4" />
                              )}
                              Cancel Request
                            </button>
                          )}
                          
                          {/* Complete Update Button */}
                          {project.update_status === 'in_progress' && (
                            <button
                              onClick={() => handleCompleteUpdate(project.id)}
                              disabled={actionLoading === project.id}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors font-medium text-sm disabled:opacity-50"
                            >
                              {actionLoading === project.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <CheckCircle className="w-4 h-4" />
                              )}
                              Complete Update
                            </button>
                          )}
                          
                          {/* Delete Button (only for non-approved) */}
                          {canDelete && (
                            <button
                              onClick={() => setShowDeleteConfirm(project.id)}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium text-sm"
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete
                            </button>
                          )}
                          
                          {/* View Public Link */}
                          {project.is_approved && project.update_status === 'none' && (
                            <a
                              href={`/projects#${project.id}`}
                              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                            >
                              <ExternalLink className="w-4 h-4" />
                              View Public
                            </a>
                          )}
                        </div>
                      </div>

                      {/* Technologies */}
                      <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                        {project.technology_list?.slice(0, 5).map((tech, index) => (
                          <span
                            key={index}
                            className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg font-medium"
                          >
                            {tech}
                          </span>
                        ))}
                        {project.technology_list?.length > 5 && (
                          <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-xs rounded-lg">
                            +{project.technology_list.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Delete Project?</h3>
                  <p className="text-gray-600 text-sm">This action cannot be undone.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="flex-1 py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(showDeleteConfirm)}
                  disabled={actionLoading === showDeleteConfirm}
                  className="flex-1 py-2 px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {actionLoading === showDeleteConfirm ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Update Request Modal */}
        {showUpdateRequestModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-purple-100 rounded-full">
                  <Send className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Request Update</h3>
                  <p className="text-gray-600 text-sm">Tell us why you need to update this project.</p>
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Reason for Update</label>
                <textarea
                  value={updateReason}
                  onChange={(e) => setUpdateReason(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                  placeholder="e.g., Need to update project images, add new features, fix description..."
                />
              </div>
              <p className="text-sm text-gray-500 mb-4">
                Once approved, your project will be temporarily hidden from the public until you complete the update.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowUpdateRequestModal(null); setUpdateReason(""); }}
                  className="flex-1 py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleRequestUpdate(showUpdateRequestModal)}
                  disabled={actionLoading === showUpdateRequestModal || !updateReason.trim()}
                  className="flex-1 py-2 px-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {actionLoading === showUpdateRequestModal ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  Submit Request
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project Details Modal */}
        {showModal && selectedProject && (
          <ProjectDetailsModal
            project={selectedProject}
            onClose={closeModal}
            status={getProjectStatus(selectedProject)}
            navigate={navigate}
          />
        )}
      </div>
    </div>
  );
}

function ProjectDetailsModal({ project, onClose, status, navigate }) {
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div
        className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header with Image */}
        <div className="relative h-64 bg-gradient-to-br from-blue-600 to-purple-700 overflow-hidden">
          {project.image ? (
            <img
              src={project.image}
              alt={project.title}
              className="w-full h-full object-cover opacity-90"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Code className="w-24 h-24 text-white/30" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-white/20 hover:bg-white/30 rounded-full text-white transition-colors backdrop-blur-sm"
          >
            <XCircle className="w-6 h-6" />
          </button>
          <div className="absolute bottom-6 left-6 right-6">
            <div className="flex items-center gap-3 mb-3">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${statusConfig.color}`}
              >
                <StatusIcon className={`w-4 h-4 ${statusConfig.iconColor}`} />
                {statusConfig.label}
              </span>
              <span className="inline-block px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full backdrop-blur-sm">
                {project.category_display}
              </span>
            </div>
            <h2 className="text-3xl font-bold text-white">{project.title}</h2>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-16rem)]">
          {/* Update status info */}
          {project.update_status === 'in_progress' && (
            <div className="mb-6 bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-orange-800 font-medium">Update Mode Active</p>
                <p className="text-orange-600 text-sm">This project is temporarily hidden. Edit it and mark the update as complete to re-submit for approval.</p>
              </div>
            </div>
          )}

          {/* Description */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Description
            </h3>
            <p className="text-gray-600 leading-relaxed">
              {project.description}
            </p>
          </div>

          {/* Project Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Academic Year */}
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Calendar className="w-4 h-4" />
                <span className="text-sm font-medium">Academic Year</span>
              </div>
              <p className="text-lg font-semibold text-gray-900">
                {project.academic_year}
              </p>
            </div>

            {/* Team Size */}
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Users className="w-4 h-4" />
                <span className="text-sm font-medium">Team Size</span>
              </div>
              <p className="text-lg font-semibold text-gray-900">
                {project.team_size || project.members?.length || 0} member(s)
              </p>
            </div>
          </div>

          {/* Team Members */}
          {project.members && project.members.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Team Members
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {project.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 bg-gray-50 rounded-xl p-3"
                  >
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                      {member.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {member.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {member.year_display} • {member.program_display}
                        {member.role && ` • ${member.role}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technologies */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Technologies Used
            </h3>
            <div className="flex flex-wrap gap-2">
              {project.technology_list?.map((tech, index) => (
                <span
                  key={index}
                  className="px-3 py-1.5 bg-blue-50 text-blue-700 text-sm font-medium rounded-lg"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* Links */}
          <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
            {project.github_url && (
              <a
                href={project.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-colors font-medium"
              >
                <Github className="w-5 h-5" />
                View on GitHub
              </a>
            )}
            {project.demo_url && (
              <a
                href={project.demo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium"
              >
                <ExternalLink className="w-5 h-5" />
                View Demo
              </a>
            )}
            {project.can_edit && (
              <button
                onClick={() => { onClose(); navigate(`/dashboard/edit-project/${project.id}`); }}
                className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium"
              >
                <Edit className="w-5 h-5" />
                Edit Project
              </button>
            )}
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium ml-auto"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MyProjectsPage;
