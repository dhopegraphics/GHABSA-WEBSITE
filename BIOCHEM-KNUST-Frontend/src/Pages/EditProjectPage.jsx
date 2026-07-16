import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Upload,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  Users,
  X,
  Image as ImageIcon,
  ArrowLeft,
  Save,
} from "lucide-react";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

const CATEGORIES = [
  { value: "WEB", label: "Web Development" },
  { value: "MOBILE", label: "Mobile Development" },
  { value: "AI_ML", label: "Artificial Intelligence & Machine Learning" },
  { value: "DATA_SCIENCE", label: "Data Science & Analytics" },
  { value: "CYBERSECURITY", label: "Cybersecurity" },
  { value: "IOT", label: "Internet of Things" },
  { value: "GAME", label: "Game Development" },
  { value: "BLOCKCHAIN", label: "Blockchain" },
  { value: "CLOUD", label: "Cloud Computing" },
  { value: "OTHER", label: "Other" },
];

const YEARS_OPTIONS = [
  { value: "1", label: "Year 1" },
  { value: "2", label: "Year 2" },
  { value: "3", label: "Year 3" },
  { value: "4", label: "Year 4" },
  { value: "MASTERS", label: "Masters" },
  { value: "PHD", label: "PhD" },
  { value: "ALUMNI", label: "Alumni" },
];

const PROGRAMS = [
  { value: "CS", label: "Computer Science" },
  { value: "IT", label: "Information Technology" },
];

export function EditProjectPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const axiosInstance = useAxiosWithRefresh();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [years, setYears] = useState([]);
  const [project, setProject] = useState(null);
  const [hasFetched, setHasFetched] = useState(false);
  
  const [imageValidation, setImageValidation] = useState({
    image_url: { validating: false, valid: null, error: "", preview: "" },
    image2_url: { validating: false, valid: null, error: "", preview: "" },
    image3_url: { validating: false, valid: null, error: "", preview: "" },
  });
  const [imageFiles, setImageFiles] = useState({
    image: null,
    image2: null,
    image3: null,
  });
  const [imageMode, setImageMode] = useState({
    image: "url",
    image2: "url",
    image3: "url",
  });

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    short_description: "",
    academic_year: "",
    category: "",
    technologies: "",
    github_url: "",
    demo_url: "",
    image_url: "",
    image2_url: "",
    image3_url: "",
    members: [],
  });

  // Fetch project data and years
  useEffect(() => {
    if (hasFetched) return;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch project and years in parallel
        const [projectResponse, yearsResponse] = await Promise.all([
          axiosInstance.get(`/projects/${projectId}/`),
          axiosInstance.get("/projects/years/").catch(() => null)
        ]);
        
        const projectData = projectResponse.data;
        setProject(projectData);
        
        // Set years
        if (yearsResponse?.data?.years) {
          setYears(yearsResponse.data.years);
        } else {
          const currentYear = new Date().getFullYear();
          setYears([String(currentYear), String(currentYear + 1)]);
        }
        
        // Check if user can edit
        if (!projectData.can_edit) {
          setError("You cannot edit this project. It has been approved. Please request an update first.");
          return;
        }
        
        // Populate form data
        setFormData({
          title: projectData.title || "",
          description: projectData.description || "",
          short_description: projectData.short_description || "",
          academic_year: projectData.academic_year || "",
          category: projectData.category || "",
          technologies: projectData.technologies || "",
          github_url: projectData.github_url || "",
          demo_url: projectData.demo_url || "",
          image_url: projectData.image || "",
          image2_url: projectData.image2 || "",
          image3_url: projectData.image3 || "",
          members: projectData.members?.map((m, idx) => ({
            name: m.name || "",
            year: m.year || "",
            program: m.program || "CS",
            role: m.role || "",
            student_id: m.student_id || "",
            email: m.email || "",
            phone: m.phone || "",
            order: idx,
          })) || [{ name: "", year: "", program: "CS", role: "", student_id: "", email: "", phone: "", order: 0 }],
        });
        
        // Set image previews for existing images
        if (projectData.image) {
          setImageValidation(prev => ({
            ...prev,
            image_url: { validating: false, valid: true, error: "", preview: projectData.image }
          }));
        }
        if (projectData.image2) {
          setImageValidation(prev => ({
            ...prev,
            image2_url: { validating: false, valid: true, error: "", preview: projectData.image2 }
          }));
        }
        if (projectData.image3) {
          setImageValidation(prev => ({
            ...prev,
            image3_url: { validating: false, valid: true, error: "", preview: projectData.image3 }
          }));
        }
        
        setHasFetched(true);
      } catch (err) {
        console.error("Error fetching project:", err);
        if (err.response?.status === 404) {
          setError("Project not found or you don't have permission to view it.");
        } else {
          setError("Failed to load project. Please try again.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [projectId, axiosInstance, hasFetched]);

  const validateImageUrl = async (field, url) => {
    if (!url || !url.trim()) {
      setImageValidation((prev) => ({
        ...prev,
        [field]: { validating: false, valid: null, error: "", preview: "" },
      }));
      return;
    }

    setImageValidation((prev) => ({
      ...prev,
      [field]: { ...prev[field], validating: true, error: "" },
    }));

    try {
      const response = await axiosInstance.post("/projects/validate-image/", { url });

      if (response.data.valid) {
        const previewUrl = response.data.direct_url || url;
        setImageValidation((prev) => ({
          ...prev,
          [field]: { validating: false, valid: true, error: "", preview: previewUrl },
        }));
        
        if (response.data.direct_url && response.data.direct_url !== url) {
          setFormData((prev) => ({ ...prev, [field]: response.data.direct_url }));
        }
      } else {
        setImageValidation((prev) => ({
          ...prev,
          [field]: { validating: false, valid: false, error: response.data.error || "Invalid image URL", preview: "" },
        }));
      }
    } catch {
      setImageValidation((prev) => ({
        ...prev,
        [field]: { validating: false, valid: false, error: "Failed to validate image.", preview: "" },
      }));
    }
  };

  const handleImageUrlChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setImageValidation((prev) => ({
      ...prev,
      [field]: { validating: false, valid: null, error: "", preview: "" },
    }));

    if (value?.trim()) {
      setTimeout(() => validateImageUrl(field, value), 1000);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (field, file) => {
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError("Image file size should not exceed 5MB");
        return;
      }
      if (!file.type.startsWith('image/')) {
        setError("Please select a valid image file");
        return;
      }

      const imageField = field.replace('_url', '');
      setImageFiles((prev) => ({ ...prev, [imageField]: file }));

      const previewUrl = URL.createObjectURL(file);
      setImageValidation((prev) => ({
        ...prev,
        [field]: { validating: false, valid: true, error: "", preview: previewUrl },
      }));
    }
  };

  const toggleImageMode = (field) => {
    const imageField = field.replace('_url', '');
    const newMode = imageMode[imageField] === 'url' ? 'file' : 'url';
    
    setImageMode((prev) => ({ ...prev, [imageField]: newMode }));
    setFormData((prev) => ({ ...prev, [field]: '' }));
    setImageFiles((prev) => ({ ...prev, [imageField]: null }));
    setImageValidation((prev) => ({
      ...prev,
      [field]: { validating: false, valid: null, error: "", preview: "" },
    }));
  };

  const handleMemberChange = (index, field, value) => {
    const updatedMembers = [...formData.members];
    updatedMembers[index][field] = value;
    setFormData((prev) => ({ ...prev, members: updatedMembers }));
  };

  const addMember = () => {
    setFormData((prev) => ({
      ...prev,
      members: [
        ...prev.members,
        { name: "", year: "", program: "CS", role: "", student_id: "", email: "", phone: "", order: prev.members.length },
      ],
    }));
  };

  const removeMember = (index) => {
    if (formData.members.length > 1) {
      const updatedMembers = formData.members.filter((_, i) => i !== index);
      updatedMembers.forEach((member, i) => { member.order = i; });
      setFormData((prev) => ({ ...prev, members: updatedMembers }));
    }
  };

  const validateForm = () => {
    if (!formData.title.trim()) { setError("Project title is required"); return false; }
    if (!formData.description.trim()) { setError("Project description is required"); return false; }
    if (!formData.category) { setError("Please select a project category"); return false; }
    if (!formData.technologies.trim()) { setError("Please list the technologies used"); return false; }
    if (!formData.academic_year) { setError("Please select the academic year"); return false; }
    
    const hasMainImageFile = imageMode.image === 'file' && imageFiles.image;
    const hasMainImageUrl = imageMode.image === 'url' && formData.image_url?.trim();
    
    if (!hasMainImageFile && !hasMainImageUrl) {
      setError("Main project image is required");
      return false;
    }
    
    if (imageMode.image === 'url' && formData.image_url?.trim() && imageValidation.image_url.validating) {
      setError("Please wait for image URL validation to complete");
      return false;
    }
    
    if (formData.members.length === 0) {
      setError("At least one team member is required");
      return false;
    }

    for (let i = 0; i < formData.members.length; i++) {
      const member = formData.members[i];
      if (!member.name.trim()) { setError(`Team member ${i + 1}: Name is required`); return false; }
      if (!member.year) { setError(`Team member ${i + 1}: Year is required`); return false; }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) return;

    setSaving(true);

    try {
      const submitData = new FormData();
      
      submitData.append('title', formData.title);
      submitData.append('description', formData.description);
      submitData.append('short_description', formData.short_description);
      submitData.append('academic_year', formData.academic_year);
      submitData.append('category', formData.category);
      submitData.append('technologies', formData.technologies);
      
      if (formData.github_url) submitData.append('github_url', formData.github_url);
      if (formData.demo_url) submitData.append('demo_url', formData.demo_url);

      if (imageMode.image === 'file' && imageFiles.image) {
        submitData.append('image', imageFiles.image);
      } else if (imageMode.image === 'url' && formData.image_url?.trim()) {
        submitData.append('image_url', formData.image_url.trim());
      }

      if (imageMode.image2 === 'file' && imageFiles.image2) {
        submitData.append('image2', imageFiles.image2);
      } else if (imageMode.image2 === 'url' && formData.image2_url?.trim()) {
        submitData.append('image2_url', formData.image2_url.trim());
      }

      if (imageMode.image3 === 'file' && imageFiles.image3) {
        submitData.append('image3', imageFiles.image3);
      } else if (imageMode.image3 === 'url' && formData.image3_url?.trim()) {
        submitData.append('image3_url', formData.image3_url.trim());
      }

      submitData.append('members', JSON.stringify(formData.members));

      const response = await axiosInstance.patch(`/projects/${projectId}/`, submitData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 200) {
        setSuccess(true);
        setTimeout(() => navigate("/dashboard/my-projects"), 2000);
      }
    } catch (err) {
      console.error("Error updating project:", err);
      let errorMessage = "Failed to update project. Please try again.";
      
      if (err.response?.data) {
        const data = err.response.data;
        if (data.error) errorMessage = data.error;
        else if (data.message) errorMessage = data.message;
      }
      
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 py-8 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-red-800 mb-2">Error</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={() => navigate("/dashboard/my-projects")}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Back to My Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center animate-fadeIn">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Project Updated!</h2>
          <p className="text-gray-600 mb-6">
            {project?.update_status === 'in_progress' 
              ? "Your changes have been saved. Don't forget to mark the update as complete when you're done!"
              : "Your changes have been saved successfully."}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate("/dashboard/my-projects")}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to My Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate("/dashboard/my-projects")}
            className="p-2 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Edit Project</h1>
            <p className="text-gray-600">Update your project information</p>
          </div>
        </div>

        {/* Update Status Banner */}
        {project?.update_status === 'in_progress' && (
          <div className="mb-6 bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-orange-800 font-medium">Update Mode Active</p>
              <p className="text-orange-600 text-sm">
                Your project is temporarily hidden from the public while you make updates. 
                Once you&apos;re done editing, go back to My Projects and click &quot;Complete Update&quot; to re-submit for approval.
              </p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-800">{error}</p>
            <button onClick={() => setError("")} className="ml-auto">
              <X className="w-5 h-5 text-red-600" />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Information */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Basic Information</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  placeholder="My Awesome Project"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Short Description
                </label>
                <input
                  type="text"
                  name="short_description"
                  value={formData.short_description}
                  onChange={handleChange}
                  maxLength={200}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  placeholder="Brief summary for project cards (max 200 characters)"
                />
                <p className="text-xs text-gray-500 mt-1">{formData.short_description.length}/200</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={5}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  placeholder="Describe your project in detail..."
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  >
                    <option value="">Select a category</option>
                    {CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Academic Year <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="academic_year"
                    value={formData.academic_year}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  >
                    <option value="">Select year</option>
                    {years.map((year) => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Technologies Used <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="technologies"
                  value={formData.technologies}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  placeholder="React, Node.js, MongoDB, etc. (comma-separated)"
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    GitHub URL
                  </label>
                  <input
                    type="url"
                    name="github_url"
                    value={formData.github_url}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    placeholder="https://github.com/..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Demo URL
                  </label>
                  <input
                    type="url"
                    name="demo_url"
                    value={formData.demo_url}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    placeholder="https://your-demo.com"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Images Section */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-100 rounded-lg">
                <ImageIcon className="w-5 h-5 text-purple-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Project Images</h2>
            </div>
            
            {['image_url', 'image2_url', 'image3_url'].map((field, index) => {
              const imageField = field.replace('_url', '');
              const isMain = index === 0;
              
              return (
                <div key={field} className="mb-6 last:mb-0">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {isMain ? 'Main Image' : `Image ${index + 1}`} {isMain && <span className="text-red-500">*</span>}
                    </label>
                    <button
                      type="button"
                      onClick={() => toggleImageMode(field)}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Switch to {imageMode[imageField] === 'url' ? 'File Upload' : 'URL'}
                    </button>
                  </div>
                  
                  {imageMode[imageField] === 'url' ? (
                    <div className="space-y-2">
                      <input
                        type="url"
                        value={formData[field]}
                        onChange={(e) => handleImageUrlChange(field, e.target.value)}
                        className={`w-full px-4 py-3 rounded-xl border ${
                          imageValidation[field].valid === false ? 'border-red-300' : 
                          imageValidation[field].valid === true ? 'border-green-300' : 'border-gray-200'
                        } focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all`}
                        placeholder="https://drive.google.com/... or paste image URL"
                      />
                      {imageValidation[field].validating && (
                        <p className="text-sm text-blue-600 flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" /> Validating...
                        </p>
                      )}
                      {imageValidation[field].error && (
                        <p className="text-sm text-red-600">{imageValidation[field].error}</p>
                      )}
                    </div>
                  ) : (
                    <div className="border-2 border-dashed border-gray-200 rounded-xl p-4 text-center hover:border-blue-400 transition-colors">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange(field, e.target.files?.[0])}
                        className="hidden"
                        id={`file-${field}`}
                      />
                      <label htmlFor={`file-${field}`} className="cursor-pointer">
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
                        <p className="text-xs text-gray-400">PNG, JPG, GIF up to 5MB</p>
                      </label>
                    </div>
                  )}
                  
                  {imageValidation[field].preview && (
                    <div className="mt-3">
                      <img
                        src={imageValidation[field].preview}
                        alt={`Preview ${index + 1}`}
                        className="w-32 h-32 object-cover rounded-lg border"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Team Members */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="w-5 h-5 text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900">Team Members</h2>
              </div>
              <button
                type="button"
                onClick={addMember}
                className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Member
              </button>
            </div>
            
            <div className="space-y-4">
              {formData.members.map((member, index) => (
                <div key={index} className="bg-gray-50 rounded-xl p-4 relative">
                  {formData.members.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeMember(index)}
                      className="absolute top-2 right-2 p-1 text-red-500 hover:bg-red-100 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={member.name}
                        onChange={(e) => handleMemberChange(index, 'name', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        placeholder="Full name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Year <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={member.year}
                        onChange={(e) => handleMemberChange(index, 'year', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      >
                        <option value="">Select year</option>
                        {YEARS_OPTIONS.map((y) => (
                          <option key={y.value} value={y.value}>{y.label}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Program</label>
                      <select
                        value={member.program}
                        onChange={(e) => handleMemberChange(index, 'program', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      >
                        {PROGRAMS.map((p) => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <input
                        type="text"
                        value={member.role}
                        onChange={(e) => handleMemberChange(index, 'role', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        placeholder="e.g., Team Lead, Developer"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Student ID</label>
                      <input
                        type="text"
                        value={member.student_id}
                        onChange={(e) => handleMemberChange(index, 'student_id', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        placeholder="Optional"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={member.email}
                        onChange={(e) => handleMemberChange(index, 'email', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        placeholder="Optional"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <input
                        type="tel"
                        value={member.phone}
                        onChange={(e) => handleMemberChange(index, 'phone', e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        placeholder="Optional"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => navigate("/dashboard/my-projects")}
              className="flex-1 py-4 px-6 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-4 px-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditProjectPage;
