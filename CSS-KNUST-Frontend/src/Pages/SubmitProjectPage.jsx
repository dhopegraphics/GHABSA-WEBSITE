import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  Users,
  Info,
  X,
  Image as ImageIcon,
  Check,
  AlertTriangle,
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

const YEARS = [
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

export function SubmitProjectPage() {
  const navigate = useNavigate();
  const axiosInstance = useAxiosWithRefresh();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [showInfo, setShowInfo] = useState(true);
  const [years, setYears] = useState([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);
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
    image: "url", // 'url' or 'file'
    image2: "url",
    image3: "url",
  });

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    short_description: "",
    academic_year: new Date().getFullYear().toString(),
    category: "",
    technologies: "",
    github_url: "",
    demo_url: "",
    image_url: "",
    image2_url: "",
    image3_url: "",
    members: [
      {
        name: "",
        year: "",
        program: "CS",
        role: "",
        student_id: "",
        email: "",
        phone: "",
        order: 0,
      },
    ],
  });

  // Fetch available years on component mount
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const response = await axiosInstance.get("/projects/years/");
        if (response.data && response.data.years) {
          setYears(response.data.years);
        }
      } catch (err) {
        console.error("Error fetching years:", err);
        // Fallback to current year if fetch fails
        const currentYear = new Date().getFullYear();
        setYears([String(currentYear), String(currentYear + 1)]);
      }
    };
    fetchYears();
  }, [axiosInstance]);

  // Check if user has seen onboarding before
  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem(
      "projectSubmissionOnboarding"
    );
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  const completeOnboarding = () => {
    localStorage.setItem("projectSubmissionOnboarding", "true");
    setShowOnboarding(false);
  };

  const skipOnboarding = () => {
    localStorage.setItem("projectSubmissionOnboarding", "true");
    setShowOnboarding(false);
  };

  const onboardingSteps = [
    {
      title: "Welcome to Project Submission! 🎉",
      description:
        "Showcase your amazing projects to the CS KNUST community! This is your chance to display your hard work and inspire fellow students.",
      icon: "🚀",
    },
    {
      title: "How It Works",
      description:
        "Fill out this form with your project details, add your team members, and submit. An executive will review and approve your project before it goes live on the main website.",
      icon: "📝",
    },
    {
      title: "What You'll Need",
      description:
        "Project title, description, technologies used, team member details, and at least one project image. GitHub and demo links are optional but recommended!",
      icon: "📋",
    },
    {
      title: "Image Requirements",
      description:
        "Upload images to Google Drive or Dropbox and paste the shareable link. Make sure links are publicly accessible! We'll verify images before accepting your submission.",
      icon: "🖼️",
    },
    {
      title: "After Submission",
      description:
        "Your project will be in 'Pending Approval' status. Once an executive approves it, your project will be visible on the public projects page for everyone to see!",
      icon: "✅",
    },
  ];

  const nextStep = () => {
    if (onboardingStep < onboardingSteps.length - 1) {
      setOnboardingStep(onboardingStep + 1);
    } else {
      completeOnboarding();
    }
  };

  const prevStep = () => {
    if (onboardingStep > 0) {
      setOnboardingStep(onboardingStep - 1);
    }
  };

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
      const response = await axiosInstance.post("/projects/validate-image/", {
        url: url,
      });

      if (response.data.valid) {
        // Use the direct_url if provided (for Google Drive/Dropbox links)
        const previewUrl = response.data.direct_url || url;
        
        setImageValidation((prev) => ({
          ...prev,
          [field]: {
            validating: false,
            valid: true,
            error: "",
            preview: previewUrl,
          },
        }));
        
        // Update formData with the converted URL if it was changed
        if (response.data.direct_url && response.data.direct_url !== url) {
          setFormData((prev) => ({
            ...prev,
            [field]: response.data.direct_url,
          }));
        }
      } else {
        setImageValidation((prev) => ({
          ...prev,
          [field]: {
            validating: false,
            valid: false,
            error: response.data.error || "Invalid image URL",
            preview: "",
          },
        }));
      }
    } catch (err) {
      console.error("Error validating image:", err);
      setImageValidation((prev) => ({
        ...prev,
        [field]: {
          validating: false,
          valid: false,
          error: "Failed to validate image. Please try again.",
          preview: "",
        },
      }));
    }
  };

  const handleImageUrlChange = (field, value) => {
    handleChange({ target: { name: field, value } });

    // Clear previous validation
    setImageValidation((prev) => ({
      ...prev,
      [field]: { validating: false, valid: null, error: "", preview: "" },
    }));

    // Debounce validation
    if (value && value.trim()) {
      const timeoutId = setTimeout(() => {
        validateImageUrl(field, value);
      }, 1000);
      return () => clearTimeout(timeoutId);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (field, file) => {
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError("Image file size should not exceed 5MB");
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError("Please select a valid image file");
        return;
      }

      // Store file and create preview
      const imageField = field.replace('_url', '');
      setImageFiles((prev) => ({
        ...prev,
        [imageField]: file,
      }));

      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setImageValidation((prev) => ({
        ...prev,
        [field]: {
          validating: false,
          valid: true,
          error: "",
          preview: previewUrl,
        },
      }));
    }
  };

  const toggleImageMode = (field) => {
    const imageField = field.replace('_url', '');
    const newMode = imageMode[imageField] === 'url' ? 'file' : 'url';
    
    setImageMode((prev) => ({
      ...prev,
      [imageField]: newMode,
    }));

    // Clear both file and URL when switching
    setFormData((prev) => ({
      ...prev,
      [field]: '',
    }));
    setImageFiles((prev) => ({
      ...prev,
      [imageField]: null,
    }));
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
        {
          name: "",
          year: "",
          program: "CS",
          role: "",
          student_id: "",
          email: "",
          phone: "",
          order: prev.members.length,
        },
      ],
    }));
  };

  const removeMember = (index) => {
    if (formData.members.length > 1) {
      const updatedMembers = formData.members.filter((_, i) => i !== index);
      // Update order values
      updatedMembers.forEach((member, i) => {
        member.order = i;
      });
      setFormData((prev) => ({ ...prev, members: updatedMembers }));
    }
  };

  const validateForm = () => {
    if (!formData.title.trim()) {
      setError("Project title is required");
      return false;
    }
    if (!formData.description.trim()) {
      setError("Project description is required");
      return false;
    }
    if (!formData.category) {
      setError("Please select a project category");
      return false;
    }
    if (!formData.technologies.trim()) {
      setError("Please list the technologies used");
      return false;
    }
    if (!formData.academic_year) {
      setError("Please select the academic year");
      return false;
    }
    
    // Check for main image - either file upload or URL is required
    const hasMainImageFile = imageMode.image === 'file' && imageFiles.image;
    const hasMainImageUrl = imageMode.image === 'url' && formData.image_url && formData.image_url.trim();
    
    console.log('Image validation:', { 
      imageMode: imageMode.image, 
      hasMainImageFile, 
      hasMainImageUrl, 
      imageUrl: formData.image_url,
      imageFile: imageFiles.image 
    });
    
    if (!hasMainImageFile && !hasMainImageUrl) {
      setError("Main project image is required. Upload a file or provide a URL.");
      return false;
    }
    
    // Check if URL validation is still in progress
    if (imageMode.image === 'url' && formData.image_url.trim() && imageValidation.image_url.validating) {
      setError("Please wait for image URL validation to complete");
      return false;
    }
    
    // Only validate URL if in URL mode and URL is provided
    if (imageMode.image === 'url' && formData.image_url.trim() && imageValidation.image_url.valid === false) {
      setError("Please fix the main image URL error before submitting");
      return false;
    }
    // Only validate optional image URLs if in URL mode and URL is provided
    if (imageMode.image2 === 'url' && formData.image2_url.trim() && imageValidation.image2_url.valid === false) {
      setError("Please fix the image 2 URL error or remove it");
      return false;
    }
    if (imageMode.image3 === 'url' && formData.image3_url.trim() && imageValidation.image3_url.valid === false) {
      setError("Please fix the image 3 URL error or remove it");
      return false;
    }

    // Validate at least one member
    if (formData.members.length === 0) {
      setError("At least one team member is required");
      return false;
    }

    // Validate all members have required fields
    for (let i = 0; i < formData.members.length; i++) {
      const member = formData.members[i];
      if (!member.name.trim()) {
        setError(`Team member ${i + 1}: Name is required`);
        return false;
      }
      if (!member.year) {
        setError(`Team member ${i + 1}: Year is required`);
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Create FormData for multipart/form-data submission
      const submitData = new FormData();

      // Add text fields
      submitData.append('title', formData.title);
      submitData.append('description', formData.description);
      submitData.append('short_description', formData.short_description);
      submitData.append('academic_year', formData.academic_year);
      submitData.append('category', formData.category);
      submitData.append('technologies', formData.technologies);
      
      if (formData.github_url) submitData.append('github_url', formData.github_url);
      if (formData.demo_url) submitData.append('demo_url', formData.demo_url);

      // Add image files or URLs - only send what's actually provided
      if (imageMode.image === 'file' && imageFiles.image) {
        submitData.append('image', imageFiles.image);
      } else if (imageMode.image === 'url' && formData.image_url && formData.image_url.trim()) {
        submitData.append('image_url', formData.image_url.trim());
      }

      if (imageMode.image2 === 'file' && imageFiles.image2) {
        submitData.append('image2', imageFiles.image2);
      } else if (imageMode.image2 === 'url' && formData.image2_url && formData.image2_url.trim()) {
        submitData.append('image2_url', formData.image2_url.trim());
      }

      if (imageMode.image3 === 'file' && imageFiles.image3) {
        submitData.append('image3', imageFiles.image3);
      } else if (imageMode.image3 === 'url' && formData.image3_url && formData.image3_url.trim()) {
        submitData.append('image3_url', formData.image3_url.trim());
      }

      // Add team members as JSON string
      submitData.append('members', JSON.stringify(formData.members));

      const response = await axiosInstance.post("/projects/submit/", submitData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 201) {
        setSuccess(true);
        setTimeout(() => {
          navigate("/dashboard/home");
        }, 3000);
      }
    } catch (err) {
      console.error("Error submitting project:", err);
      console.error("Error response data:", err.response?.data);
      
      // Better error parsing
      let errorMessage = "Failed to submit project. Please try again.";
      
      if (err.response?.data) {
        const data = err.response.data;
        if (data.message) {
          errorMessage = data.message;
        } else if (data.image && Array.isArray(data.image)) {
          errorMessage = data.image[0];
        } else if (data.members && Array.isArray(data.members)) {
          errorMessage = `Team members: ${data.members[0]}`;
        } else if (typeof data === 'object') {
          // Get the first error message from any field
          const firstError = Object.entries(data).find(([key, value]) => value);
          if (firstError) {
            const [field, value] = firstError;
            errorMessage = Array.isArray(value) ? `${field}: ${value[0]}` : `${field}: ${value}`;
          }
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Onboarding Overlay
  if (showOnboarding) {
    const currentStep = onboardingSteps[onboardingStep];
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
        <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full p-8 relative animate-slideUp">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">
                Step {onboardingStep + 1} of {onboardingSteps.length}
              </span>
              <button
                onClick={skipOnboarding}
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Skip tutorial
              </button>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${
                    ((onboardingStep + 1) / onboardingSteps.length) * 100
                  }%`,
                }}
              />
            </div>
          </div>

          {/* Icon */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full mb-4">
              <span className="text-5xl">{currentStep.icon}</span>
            </div>
          </div>

          {/* Content */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {currentStep.title}
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed">
              {currentStep.description}
            </p>
          </div>

          {/* Navigation Buttons */}
          <div className="flex gap-4">
            {onboardingStep > 0 && (
              <button
                onClick={prevStep}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
            )}
            <button
              onClick={nextStep}
              className={`${
                onboardingStep === 0 ? "w-full" : "flex-1"
              } px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl`}
            >
              {onboardingStep === onboardingSteps.length - 1
                ? "Get Started! 🚀"
                : "Next"}
            </button>
          </div>

          {/* Dots Indicator */}
          <div className="flex justify-center gap-2 mt-6">
            {onboardingSteps.map((_, index) => (
              <button
                key={index}
                onClick={() => setOnboardingStep(index)}
                className={`w-2 h-2 rounded-full transition-all ${
                  index === onboardingStep
                    ? "bg-blue-600 w-8"
                    : "bg-gray-300 hover:bg-gray-400"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="mb-6 flex justify-center">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Project Submitted Successfully!
          </h2>
          <p className="text-gray-600 mb-6">
            Your project has been submitted and is pending approval from an
            executive. You&apos;ll be notified once it&apos;s approved and
            visible on the website.
          </p>
          <button
            onClick={() => navigate("/dashboard/my-projects")}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            View My Projects
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Submit Your Project
          </h1>
          <p className="text-lg text-gray-600">
            Showcase your amazing work to the CS community
          </p>
        </div>

        {/* Info Alert */}
        {showInfo && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Your project will be reviewed by an
                executive before being published on the main website. Make sure
                all information is accurate and complete.
              </p>
            </div>
            <button
              onClick={() => setShowInfo(false)}
              className="text-blue-600 hover:text-blue-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <button
              onClick={() => setError("")}
              className="text-red-600 hover:text-red-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Project Information Card */}
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">
                Project Information
              </h2>
            </div>

            <div className="space-y-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="e.g., BIO-CHEM KNUST Management System"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  required
                />
              </div>

              {/* Category and Year */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    required
                  >
                    <option value="">Select Category</option>
                    {CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Academic Year <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="academic_year"
                    value={formData.academic_year}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    required
                  >
                    {years.length === 0 ? (
                      <option value={new Date().getFullYear()}>
                        {new Date().getFullYear()}
                      </option>
                    ) : (
                      years.map((year) => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              {/* Short Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Short Description
                </label>
                <input
                  type="text"
                  name="short_description"
                  value={formData.short_description}
                  onChange={handleChange}
                  placeholder="Brief one-line summary (max 200 characters)"
                  maxLength={200}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.short_description.length}/200 characters
                </p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Full Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Describe your project in detail - what it does, the problem it solves, key features, etc."
                  rows={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                  required
                />
              </div>

              {/* Technologies */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Technologies Used <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="technologies"
                  value={formData.technologies}
                  onChange={handleChange}
                  placeholder="e.g., React, Node.js, MongoDB, Python, TensorFlow"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Separate multiple technologies with commas
                </p>
              </div>

              {/* URLs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    GitHub URL
                  </label>
                  <input
                    type="url"
                    name="github_url"
                    value={formData.github_url}
                    onChange={handleChange}
                    placeholder="https://github.com/username/repo"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Demo/Video URL
                  </label>
                  <input
                    type="url"
                    name="demo_url"
                    value={formData.demo_url}
                    onChange={handleChange}
                    placeholder="https://your-demo.com or YouTube link"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* Image URLs */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Project Images
                </label>
                <p className="text-xs text-gray-500 mb-4">
                  Upload images directly or provide URLs from Google Drive, Dropbox, etc.
                </p>
                <div className="space-y-4">
                  {/* Main Image - Required */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">
                          Main Image <span className="text-red-500">*</span>
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleImageMode('image_url')}
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        {imageMode.image === 'url' ? 'Switch to File Upload' : 'Switch to URL'}
                      </button>
                    </div>
                    
                    {imageMode.image === 'url' ? (
                      <div className="relative">
                        <input
                          type="url"
                          name="image_url"
                          value={formData.image_url}
                          onChange={(e) =>
                            handleImageUrlChange("image_url", e.target.value)
                          }
                          placeholder="Image URL (Google Drive, Dropbox, or direct link)"
                          className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                            imageValidation.image_url.valid === false
                              ? "border-red-300 bg-red-50"
                              : imageValidation.image_url.valid === true
                              ? "border-green-300 bg-green-50"
                              : "border-gray-300"
                          }`}
                        />
                        {imageValidation.image_url.validating && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                          </div>
                        )}
                        {imageValidation.image_url.valid === true && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <Check className="w-5 h-5 text-green-600" />
                          </div>
                        )}
                        {imageValidation.image_url.valid === false && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileChange('image_url', e.target.files[0])}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        />
                        <p className="text-xs text-gray-500 mt-1">Max file size: 5MB</p>
                      </div>
                    )}
                    
                    {imageValidation.image_url.error && (
                      <p className="text-xs text-red-600 mt-1 flex items-start gap-1">
                        <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        <span>{imageValidation.image_url.error}</span>
                      </p>
                    )}
                    {imageValidation.image_url.preview && (
                      <div className="mt-3 border border-green-200 rounded-lg p-2 bg-green-50">
                        <img
                          src={imageValidation.image_url.preview}
                          alt="Preview"
                          className="w-full h-48 object-cover rounded"
                          onError={() => {
                            setImageValidation((prev) => ({
                              ...prev,
                              image_url: {
                                ...prev.image_url,
                                valid: false,
                                error: "Failed to load image preview",
                              },
                            }));
                          }}
                        />
                        <p className="text-xs text-green-700 mt-1 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Image loaded successfully
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Additional Image 2 - Optional */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">
                          Additional Image 2 (Optional)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleImageMode('image2_url')}
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        {imageMode.image2 === 'url' ? 'Switch to File Upload' : 'Switch to URL'}
                      </button>
                    </div>
                    
                    {imageMode.image2 === 'url' ? (
                      <div className="relative">
                        <input
                          type="url"
                          name="image2_url"
                          value={formData.image2_url}
                          onChange={(e) =>
                            handleImageUrlChange("image2_url", e.target.value)
                          }
                          placeholder="Image URL (Google Drive, Dropbox, or direct link)"
                          className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                            imageValidation.image2_url.valid === false
                              ? "border-red-300 bg-red-50"
                              : imageValidation.image2_url.valid === true
                              ? "border-green-300 bg-green-50"
                              : "border-gray-300"
                          }`}
                        />
                      {imageValidation.image2_url.validating && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                        </div>
                      )}
                      {imageValidation.image2_url.valid === true && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          <Check className="w-5 h-5 text-green-600" />
                        </div>
                      )}
                        {imageValidation.image2_url.valid === false && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileChange('image2_url', e.target.files[0])}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        />
                        <p className="text-xs text-gray-500 mt-1">Max file size: 5MB</p>
                      </div>
                    )}
                    {imageValidation.image2_url.error && (
                      <p className="text-xs text-red-600 mt-1 flex items-start gap-1">
                        <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        <span>{imageValidation.image2_url.error}</span>
                      </p>
                    )}
                    {imageValidation.image2_url.preview && (
                      <div className="mt-3 border border-green-200 rounded-lg p-2 bg-green-50">
                        <img
                          src={imageValidation.image2_url.preview}
                          alt="Preview 2"
                          className="w-full h-48 object-cover rounded"
                        />
                      </div>
                    )}
                  </div>

                  {/* Additional Image 3 - Optional */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">
                          Additional Image 3 (Optional)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleImageMode('image3_url')}
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        {imageMode.image3 === 'url' ? 'Switch to File Upload' : 'Switch to URL'}
                      </button>
                    </div>
                    
                    {imageMode.image3 === 'url' ? (
                      <div className="relative">
                        <input
                          type="url"
                          name="image3_url"
                          value={formData.image3_url}
                          onChange={(e) =>
                            handleImageUrlChange("image3_url", e.target.value)
                          }
                          placeholder="Image URL (Google Drive, Dropbox, or direct link)"
                          className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                            imageValidation.image3_url.valid === false
                              ? "border-red-300 bg-red-50"
                              : imageValidation.image3_url.valid === true
                              ? "border-green-300 bg-green-50"
                              : "border-gray-300"
                          }`}
                        />
                      {imageValidation.image3_url.validating && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                        </div>
                      )}
                      {imageValidation.image3_url.valid === true && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          <Check className="w-5 h-5 text-green-600" />
                        </div>
                      )}
                        {imageValidation.image3_url.valid === false && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileChange('image3_url', e.target.files[0])}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        />
                        <p className="text-xs text-gray-500 mt-1">Max file size: 5MB</p>
                      </div>
                    )}
                    
                    {imageValidation.image3_url.error && (
                      <p className="text-xs text-red-600 mt-1 flex items-start gap-1">
                        <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        <span>{imageValidation.image3_url.error}</span>
                      </p>
                    )}
                    {imageValidation.image3_url.preview && (
                      <div className="mt-3 border border-green-200 rounded-lg p-2 bg-green-50">
                        <img
                          src={imageValidation.image3_url.preview}
                          alt="Preview 3"
                          className="w-full h-48 object-cover rounded"
                        />
                      </div>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  💡 Tip: Upload images to Google Drive or Dropbox and paste the
                  shareable link. Make sure the link is publicly accessible (no
                  login required).
                </p>
                <p className="text-xs text-amber-600 mt-2 flex items-start gap-1">
                  <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>
                    Google Drive links must be shared with &quot;Anyone with the
                    link&quot; permission. We&apos;ll check if the image is
                    accessible before accepting your submission.
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Team Members Card */}
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Team Members
                </h2>
              </div>
              <button
                type="button"
                onClick={addMember}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Member
              </button>
            </div>

            <div className="space-y-6">
              {formData.members.map((member, index) => (
                <div
                  key={index}
                  className="p-6 border-2 border-gray-200 rounded-xl hover:border-blue-300 transition-colors relative"
                >
                  {/* Remove button */}
                  {formData.members.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeMember(index)}
                      className="absolute top-4 right-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Remove member"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}

                  <h3 className="text-lg font-semibold text-gray-800 mb-4">
                    Team Member {index + 1}
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Name */}
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Full Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={member.name}
                        onChange={(e) =>
                          handleMemberChange(index, "name", e.target.value)
                        }
                        placeholder="Enter full name"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        required
                      />
                    </div>

                    {/* Year */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Year <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={member.year}
                        onChange={(e) =>
                          handleMemberChange(index, "year", e.target.value)
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        required
                      >
                        <option value="">Select Year</option>
                        {YEARS.map((year) => (
                          <option key={year.value} value={year.value}>
                            {year.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Program */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Program <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={member.program}
                        onChange={(e) =>
                          handleMemberChange(index, "program", e.target.value)
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        required
                      >
                        {PROGRAMS.map((prog) => (
                          <option key={prog.value} value={prog.value}>
                            {prog.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Role */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Role
                      </label>
                      <input
                        type="text"
                        value={member.role}
                        onChange={(e) =>
                          handleMemberChange(index, "role", e.target.value)
                        }
                        placeholder="e.g., Team Lead, Backend Developer"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      />
                    </div>

                    {/* Student ID */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Student ID
                      </label>
                      <input
                        type="text"
                        value={member.student_id}
                        onChange={(e) =>
                          handleMemberChange(
                            index,
                            "student_id",
                            e.target.value
                          )
                        }
                        placeholder="e.g., 12345678"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      />
                    </div>

                    {/* Email */}
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={member.email}
                        onChange={(e) =>
                          handleMemberChange(index, "email", e.target.value)
                        }
                        placeholder="student@knust.edu.gh"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      />
                    </div>

                    {/* Phone */}
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Phone Number
                        {index === 0 && (
                          <span className="text-xs text-blue-600 ml-1">(Helps link your account)</span>
                        )}
                      </label>
                      <input
                        type="tel"
                        value={member.phone}
                        onChange={(e) =>
                          handleMemberChange(index, "phone", e.target.value)
                        }
                        placeholder="+233 XX XXX XXXX"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
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
              onClick={() => navigate("/dashboard/home")}
              className="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Submit Project
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
