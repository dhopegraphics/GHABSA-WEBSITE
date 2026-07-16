import { useState, useContext, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  User,
  Mail,
  Phone,
  BookOpen,
  GraduationCap,
  FileText,
  Loader,
  CheckCircle,
  AlertCircle,
  Image as ImageIcon,
  Calendar,
  Award,
  Upload,
  Link as LinkIcon,
  Trash2,
} from "lucide-react";
import { registerAsCandidate } from "../../utils/votingApi";
import { UserContext } from "../../Context/UserContext";
import toast from "react-hot-toast";

// Available programs and years
const PROGRAMS = [
  { value: "Computer Science", label: "Computer Science" },
  { value: "Information Technology", label: "Information Technology" },
];

const YEARS = [
  { value: 1, label: "Year 1" },
  { value: 2, label: "Year 2" },
  { value: 3, label: "Year 3" },
  { value: 4, label: "Year 4" },
];

export const CandidateRegistrationModal = ({
  isOpen,
  onClose,
  event,
  categories = [],
  onSuccess,
}) => {
  const { user } = useContext(UserContext);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // Multi-step form
  const [formData, setFormData] = useState({
    category: "",
    candidate_name: "",
    candidate_id: "",
    email: "",
    phone: "",
    program: "",
    year: "",
    bio: "",
    profile_image_url: "",
  });

  // Image upload states
  const [imageMode, setImageMode] = useState("upload"); // "upload" or "url"
  const [profileImage, setProfileImage] = useState(null); // File object
  const [imagePreview, setImagePreview] = useState(null); // Preview URL for uploaded file
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  // Determine if this event has categories
  const hasCategories = categories && categories.length > 0;
  
  // Get available programs and years based on event eligibility
  const availablePrograms = event?.eligible_programs?.length > 0
    ? PROGRAMS.filter(p => event.eligible_programs.includes(p.value))
    : PROGRAMS;
  
  const availableYears = event?.eligible_years?.length > 0
    ? YEARS.filter(y => event.eligible_years.includes(y.value))
    : YEARS;

  // Track if form has been initialized to prevent re-initialization
  const [formInitialized, setFormInitialized] = useState(false);

  // Pre-fill form with user data on mount - only once when modal opens
  useEffect(() => {
    if (user && isOpen && !formInitialized) {
      const eligiblePrograms = event?.eligible_programs?.length > 0
        ? PROGRAMS.filter(p => event.eligible_programs.includes(p.value))
        : PROGRAMS;
      const eligibleYears = event?.eligible_years?.length > 0
        ? YEARS.filter(y => event.eligible_years.includes(y.value))
        : YEARS;
      
      const autoProgram = eligiblePrograms.length === 1 ? eligiblePrograms[0].value : "";
      const autoYear = eligibleYears.length === 1 ? eligibleYears[0].value : "";
      
      setFormData(prev => ({
        ...prev,
        candidate_name: user.full_name || (user.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : ""),
        candidate_id: user.student_id || user.index_number || "",
        email: user.email || "",
        phone: user.phone || user.phone_number || "",
        program: user.program || autoProgram,
        year: user.year || user.level || autoYear,
        profile_image_url: user.avatar || user.profile_picture || "",
      }));
      setFormInitialized(true);
      
      // If user has an existing avatar, set it as preview
      if (user.avatar || user.profile_picture) {
        setImagePreview(user.avatar || user.profile_picture);
        setImageMode("url"); // Show URL mode if they have existing avatar
      }
    }
  }, [user, isOpen, formInitialized, event?.eligible_programs, event?.eligible_years]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle image file selection
  const handleImageSelect = (file) => {
    if (!file) return;

    // Validate file type
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"];
    if (!validTypes.includes(file.type)) {
      toast.error("Please select a valid image file (JPEG, PNG, WebP, or GIF)");
      return;
    }

    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      toast.error("Image size must be less than 5MB");
      return;
    }

    setProfileImage(file);
    
    // Create preview URL
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);
    
    // Clear URL input when uploading file
    setFormData((prev) => ({ ...prev, profile_image_url: "" }));
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleImageSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleImageSelect(file);
  };

  const removeImage = () => {
    setProfileImage(null);
    if (imagePreview && !formData.profile_image_url) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const switchImageMode = (mode) => {
    setImageMode(mode);
    if (mode === "upload") {
      // Clear URL when switching to upload
      setFormData((prev) => ({ ...prev, profile_image_url: "" }));
    } else {
      // Clear uploaded file when switching to URL
      removeImage();
    }
  };

  const validateStep1 = () => {
    if (hasCategories && !formData.category) {
      toast.error("Please select a category");
      return false;
    }
    if (!formData.candidate_name.trim()) {
      toast.error("Please enter your name");
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    // Program and year might be required based on event settings
    if (event?.eligible_programs?.length > 0 && !formData.program) {
      toast.error("Please select your program");
      return false;
    }
    if (event?.eligible_years?.length > 0 && !formData.year) {
      toast.error("Please select your year");
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };

  const handleBack = () => {
    setStep(prev => Math.max(1, prev - 1));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep1() || !validateStep2()) return;

    setLoading(true);

    try {
      const registrationData = {
        event: event.id,
        candidate_name: formData.candidate_name.trim(),
        candidate_id: formData.candidate_id.trim() || undefined,
        email: formData.email.trim() || undefined,
        phone: formData.phone.trim() || undefined,
        program: formData.program || undefined,
        year: formData.year ? parseInt(formData.year) : undefined,
        bio: formData.bio.trim() || undefined,
        // Only include URL if no file is being uploaded
        profile_image_url: (!profileImage && formData.profile_image_url.trim()) || undefined,
      };

      // Only include category if event has categories
      if (hasCategories && formData.category) {
        registrationData.category = formData.category;
      }

      // Pass the profile image file if one was uploaded
      const { data, error } = await registerAsCandidate(registrationData, profileImage);

      if (error) {
        console.error("Registration error:", error);
        let errorMessage = "Failed to register as candidate";
        
        if (typeof error === "object") {
          // Handle DRF validation errors
          const messages = [];
          Object.values(error).forEach(value => {
            if (Array.isArray(value)) {
              messages.push(...value);
            } else if (typeof value === "string") {
              messages.push(value);
            }
          });
          if (messages.length > 0) {
            errorMessage = messages.join(". ");
          }
        } else if (typeof error === "string") {
          errorMessage = error;
        }
        
        toast.error(errorMessage);
        return;
      }

      toast.success("🎉 Registration submitted successfully! You will be notified once approved.");
      onSuccess?.(data);
      resetAndClose();
    } catch (error) {
      console.error("Registration error:", error);
      toast.error("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const resetAndClose = () => {
    setStep(1);
    setFormInitialized(false);
    setFormData({
      category: "",
      candidate_name: "",
      candidate_id: "",
      email: "",
      phone: "",
      program: "",
      year: "",
      bio: "",
      profile_image_url: "",
    });
    // Reset image upload states
    setImageMode("upload");
    if (profileImage && imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setProfileImage(null);
    setImagePreview(null);
    setIsDragging(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    onClose();
  };

  if (!isOpen) return null;

  // Format registration deadline
  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
        onClick={(e) => e.target === e.currentTarget && resetAndClose()}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-white rounded-xl sm:rounded-2xl shadow-2xl w-full max-w-2xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 sm:p-6 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-white/20 rounded-lg flex-shrink-0">
                  <Award size={20} className="sm:w-6 sm:h-6" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-lg sm:text-xl font-bold truncate">Register as Candidate</h2>
                  <p className="text-indigo-100 text-xs sm:text-sm mt-0.5 truncate">{event?.title}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={resetAndClose}
                className="p-2 hover:bg-white/20 rounded-full transition-colors flex-shrink-0 ml-2"
                aria-label="Close modal"
              >
                <X size={20} className="sm:w-6 sm:h-6" />
              </button>
            </div>
            
            {/* Progress Steps */}
            <div className="flex items-center justify-center gap-1 sm:gap-2 mt-3 sm:mt-4">
              {[1, 2, 3].map((s) => (
                <div key={s} className="flex items-center">
                  <button
                    type="button"
                    onClick={() => s < step && setStep(s)}
                    disabled={s >= step}
                    className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-medium transition-all ${
                      step >= s
                        ? "bg-white text-indigo-600"
                        : "bg-white/20 text-white"
                    } ${s < step ? "cursor-pointer hover:ring-2 hover:ring-white/50" : "cursor-default"}`}
                    aria-label={`Step ${s}`}
                  >
                    {step > s ? <CheckCircle size={14} className="sm:w-4 sm:h-4" /> : s}
                  </button>
                  {s < 3 && (
                    <div
                      className={`w-6 sm:w-8 h-0.5 sm:h-1 mx-0.5 sm:mx-1 rounded ${
                        step > s ? "bg-white" : "bg-white/20"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-center mt-2 text-[10px] sm:text-xs text-indigo-100">
              <span className={`${step === 1 ? "font-medium text-white" : ""} truncate`}>
                {hasCategories ? "Category" : "Basic"}
              </span>
              <span className="mx-2 sm:mx-4">•</span>
              <span className={`${step === 2 ? "font-medium text-white" : ""} truncate`}>
                Details
              </span>
              <span className="mx-2 sm:mx-4">•</span>
              <span className={`${step === 3 ? "font-medium text-white" : ""} truncate`}>
                Review
              </span>
            </div>
          </div>

          {/* Registration deadline notice */}
          {event?.registration_end_date && (
            <div className="bg-amber-50 border-b border-amber-100 px-4 sm:px-6 py-2 sm:py-3 flex items-center gap-2 text-amber-800 text-xs sm:text-sm flex-shrink-0">
              <Calendar size={14} className="sm:w-4 sm:h-4 flex-shrink-0" />
              <span className="truncate">
                Closes: <strong className="whitespace-nowrap">{formatDate(event.registration_end_date)}</strong>
              </span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={(e) => e.preventDefault()} className="p-4 sm:p-6 overflow-y-auto flex-1 min-h-0">
            {/* Step 1: Category & Name */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-5"
              >
                {/* Category Selection (only if event has categories) */}
                {hasCategories && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <BookOpen size={16} className="inline mr-2" />
                      Category <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-white"
                      required
                    >
                      <option value="">Select a category to contest in</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name} {cat.description ? `- ${cat.description}` : ""}
                        </option>
                      ))}
                    </select>
                    {categories.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        {categories.length} {categories.length === 1 ? "category" : "categories"} available
                      </p>
                    )}
                  </div>
                )}

                {/* Event type info for single-category events */}
                {!hasCategories && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 flex items-start gap-3">
                    <Award className="text-indigo-600 flex-shrink-0 mt-0.5" size={20} />
                    <div className="text-sm text-indigo-700">
                      <p className="font-medium">
                        {event?.event_type === "election" ? "Election Registration" : "Event Registration"}
                      </p>
                      <p className="mt-1 text-indigo-600">
                        This is a single-position {event?.event_type || "event"}. Complete the form below to register.
                      </p>
                    </div>
                  </div>
                )}

                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <User size={16} className="inline mr-2" />
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="candidate_name"
                    value={formData.candidate_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    placeholder="Enter your full name as it should appear on ballot"
                    required
                  />
                </div>

                {/* Student ID */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <GraduationCap size={16} className="inline mr-2" />
                    Student ID
                  </label>
                  <input
                    type="text"
                    name="candidate_id"
                    value={formData.candidate_id}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    placeholder="e.g., 10987654"
                  />
                </div>

                {/* Profile Photo - Upload or URL */}
                <div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                    <label className="block text-sm font-medium text-gray-700">
                      <ImageIcon size={16} className="inline mr-2" />
                      Profile Photo
                    </label>
                    {/* Mode Toggle */}
                    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1 self-start sm:self-auto">
                      <button
                        type="button"
                        onClick={() => switchImageMode("upload")}
                        className={`flex items-center gap-1.5 px-3 sm:px-4 py-2 sm:py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${
                          imageMode === "upload"
                            ? "bg-white text-indigo-600 shadow-sm"
                            : "text-gray-500 hover:text-gray-700 active:bg-gray-200"
                        }`}
                      >
                        <Upload size={14} />
                        Upload
                      </button>
                      <button
                        type="button"
                        onClick={() => switchImageMode("url")}
                        className={`flex items-center gap-1.5 px-3 sm:px-4 py-2 sm:py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${
                          imageMode === "url"
                            ? "bg-white text-indigo-600 shadow-sm"
                            : "text-gray-500 hover:text-gray-700 active:bg-gray-200"
                        }`}
                      >
                        <LinkIcon size={14} />
                        URL
                      </button>
                    </div>
                  </div>

                  {/* Upload Mode */}
                  {imageMode === "upload" && (
                    <div className="space-y-3">
                      {/* Hidden file input */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                        onChange={handleFileInputChange}
                        className="hidden"
                      />

                      {/* Drop Zone / Preview */}
                      {!imagePreview ? (
                        <div
                          onDragOver={handleDragOver}
                          onDragLeave={handleDragLeave}
                          onDrop={handleDrop}
                          onClick={() => fileInputRef.current?.click()}
                          className={`relative border-2 border-dashed rounded-xl p-4 sm:p-6 text-center cursor-pointer transition-all active:scale-[0.99] ${
                            isDragging
                              ? "border-indigo-500 bg-indigo-50"
                              : "border-gray-300 hover:border-indigo-400 hover:bg-gray-50 active:bg-gray-100"
                          }`}
                        >
                          <div className="flex flex-col items-center gap-2 sm:gap-3">
                            <div className={`p-2 sm:p-3 rounded-full transition-colors ${
                              isDragging ? "bg-indigo-100" : "bg-gray-100"
                            }`}>
                              <Upload
                                size={20}
                                className={`sm:w-6 sm:h-6 ${isDragging ? "text-indigo-600" : "text-gray-400"}`}
                              />
                            </div>
                            <div>
                              <p className={`text-sm sm:text-base font-medium ${isDragging ? "text-indigo-600" : "text-gray-700"}`}>
                                {isDragging ? "Drop your image here" : "Tap to upload photo"}
                              </p>
                              <p className="text-xs text-gray-500 mt-1 hidden sm:block">
                                or drag & drop
                              </p>
                              <p className="text-[10px] sm:text-xs text-gray-400 mt-1">
                                JPEG, PNG, WebP, GIF (max 5MB)
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="relative group">
                          <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 rounded-xl border border-gray-200">
                            <img
                              src={imagePreview}
                              alt="Profile preview"
                              className="w-16 h-16 sm:w-20 sm:h-20 object-cover object-top rounded-full border-2 border-indigo-200 flex-shrink-0"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs sm:text-sm font-medium text-gray-900 truncate">
                                {profileImage?.name || "Profile photo"}
                              </p>
                              {profileImage && (
                                <p className="text-xs text-gray-500 mt-1">
                                  {(profileImage.size / 1024).toFixed(1)} KB
                                </p>
                              )}
                              <div className="flex items-center gap-1 mt-2 text-green-600">
                                <CheckCircle size={12} className="sm:w-3.5 sm:h-3.5" />
                                <span className="text-xs font-medium">Ready to upload</span>
                              </div>
                            </div>
                            <div className="flex flex-row sm:flex-col gap-1 sm:gap-2">
                              <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="p-2 sm:p-2.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 active:bg-indigo-100 rounded-lg transition-colors"
                                title="Change image"
                                aria-label="Change image"
                              >
                                <Upload size={16} className="sm:w-[18px] sm:h-[18px]" />
                              </button>
                              <button
                                type="button"
                                onClick={removeImage}
                                className="p-2 sm:p-2.5 text-gray-500 hover:text-red-600 hover:bg-red-50 active:bg-red-100 rounded-lg transition-colors"
                                title="Remove image"
                                aria-label="Remove image"
                              >
                                <Trash2 size={16} className="sm:w-[18px] sm:h-[18px]" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* URL Mode */}
                  {imageMode === "url" && (
                    <div className="space-y-3">
                      <input
                        type="url"
                        name="profile_image_url"
                        value={formData.profile_image_url}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                        placeholder="https://example.com/your-photo.jpg"
                      />
                      {formData.profile_image_url && (
                        <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 rounded-xl border border-gray-200">
                          <img
                            src={formData.profile_image_url}
                            alt="Preview"
                            className="w-16 h-16 sm:w-20 sm:h-20 object-cover object-top rounded-full border-2 border-indigo-200 flex-shrink-0"
                            onError={(e) => {
                              e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' fill='%23e5e7eb'%3E%3Crect width='80' height='80' rx='40'/%3E%3Ctext x='50%25' y='55%25' font-size='12' fill='%239ca3af' text-anchor='middle'%3EError%3C/text%3E%3C/svg%3E";
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs sm:text-sm font-medium text-gray-900">External image</p>
                            <p className="text-xs text-gray-500 mt-1 truncate">
                              {formData.profile_image_url}
                            </p>
                            <div className="flex items-center gap-1 mt-2 text-green-600">
                              <CheckCircle size={12} className="sm:w-3.5 sm:h-3.5" />
                              <span className="text-xs font-medium">URL linked</span>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({ ...prev, profile_image_url: "" }))}
                            className="p-2 sm:p-2.5 text-gray-500 hover:text-red-600 hover:bg-red-50 active:bg-red-100 rounded-lg transition-colors flex-shrink-0"
                            title="Clear URL"
                            aria-label="Clear URL"
                          >
                            <Trash2 size={16} className="sm:w-[18px] sm:h-[18px]" />
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-gray-500 mt-2">
                    A clear profile photo helps voters identify you
                  </p>
                </div>
              </motion.div>
            )}

            {/* Step 2: Contact & Program Info */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-5"
              >
                {/* Email & Phone Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Mail size={16} className="inline mr-2" />
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      placeholder="your@email.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Phone size={16} className="inline mr-2" />
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      placeholder="0241234567"
                    />
                  </div>
                </div>

                {/* Program & Year Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Program
                      {event?.eligible_programs?.length > 0 && (
                        <span className="text-red-500"> *</span>
                      )}
                    </label>
                    <select
                      name="program"
                      value={formData.program}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-white"
                      required={event?.eligible_programs?.length > 0}
                    >
                      <option value="">Select program</option>
                      {availablePrograms.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                    {event?.eligible_programs?.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        This event is for {event.eligible_programs.join(", ")} students only
                      </p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Year
                      {event?.eligible_years?.length > 0 && (
                        <span className="text-red-500"> *</span>
                      )}
                    </label>
                    <select
                      name="year"
                      value={formData.year}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-white"
                      required={event?.eligible_years?.length > 0}
                    >
                      <option value="">Select year</option>
                      {availableYears.map((y) => (
                        <option key={y.value} value={y.value}>
                          {y.label}
                        </option>
                      ))}
                    </select>
                    {event?.eligible_years?.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        This event is for Year {event.eligible_years.join(", ")} students only
                      </p>
                    )}
                  </div>
                </div>

                {/* Event eligibility notice */}
                {(event?.eligible_programs?.length > 0 || event?.eligible_years?.length > 0) && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={18} />
                    <div className="text-sm text-blue-700">
                      <p className="font-medium">Eligibility Requirements</p>
                      <p className="mt-1">
                        This {event.event_type} is restricted to:
                        {event?.eligible_years?.length > 0 && (
                          <span className="block">• Year: {event.eligible_years.join(", ")}</span>
                        )}
                        {event?.eligible_programs?.length > 0 && (
                          <span className="block">• Programs: {event.eligible_programs.join(", ")}</span>
                        )}
                      </p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 3: Bio & Review */}
            {step === 3 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-5"
              >
                {/* Bio / Manifesto */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FileText size={16} className="inline mr-2" />
                    Bio / Manifesto
                  </label>
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleInputChange}
                    rows={5}
                    maxLength={500}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                    placeholder="Tell voters about yourself, your experience, goals, and why they should vote for you..."
                  />
                  <div className="flex justify-between mt-1">
                    <p className="text-xs text-gray-500">
                      A compelling bio can help you stand out!
                    </p>
                    <p className={`text-xs ${formData.bio.length > 450 ? "text-amber-600" : "text-gray-500"}`}>
                      {formData.bio.length}/500
                    </p>
                  </div>
                </div>

                {/* Registration Summary */}
                <div className="bg-gray-50 rounded-lg p-3 sm:p-4 border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2 text-sm sm:text-base">
                    <CheckCircle size={16} className="sm:w-[18px] sm:h-[18px] text-green-600" />
                    Registration Summary
                  </h4>
                  <div className="grid grid-cols-1 xs:grid-cols-2 gap-2 sm:gap-3 text-xs sm:text-sm">
                    <div>
                      <span className="text-gray-500">Name:</span>
                      <p className="font-medium text-gray-900 truncate">{formData.candidate_name || "-"}</p>
                    </div>
                    {hasCategories && (
                      <div>
                        <span className="text-gray-500">Category:</span>
                        <p className="font-medium text-gray-900 truncate">
                          {categories.find(c => c.id === formData.category)?.name || "-"}
                        </p>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Student ID:</span>
                      <p className="font-medium text-gray-900">{formData.candidate_id || "-"}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Program:</span>
                      <p className="font-medium text-gray-900 truncate">{formData.program || "-"}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Year:</span>
                      <p className="font-medium text-gray-900">{formData.year ? `Year ${formData.year}` : "-"}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Email:</span>
                      <p className="font-medium text-gray-900 truncate">{formData.email || "-"}</p>
                    </div>
                    <div className="xs:col-span-2">
                      <span className="text-gray-500">Profile Photo:</span>
                      <p className="font-medium text-gray-900 flex items-center gap-1">
                        {profileImage ? (
                          <>
                            <CheckCircle size={12} className="sm:w-3.5 sm:h-3.5 text-green-600" />
                            Uploaded
                          </>
                        ) : formData.profile_image_url ? (
                          <>
                            <CheckCircle size={12} className="sm:w-3.5 sm:h-3.5 text-green-600" />
                            URL linked
                          </>
                        ) : (
                          "-"
                        )}
                      </p>
                    </div>
                  </div>
                  {/* Photo Preview in Summary */}
                  {(imagePreview || formData.profile_image_url) && (
                    <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-gray-200 flex items-center gap-3 sm:gap-4">
                      <img
                        src={imagePreview || formData.profile_image_url}
                        alt="Profile preview"
                        className="w-12 h-12 sm:w-16 sm:h-16 object-cover object-top rounded-full border-2 border-indigo-200 flex-shrink-0"
                        onError={(e) => {
                          e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' fill='%23e5e7eb'%3E%3Crect width='64' height='64' rx='32'/%3E%3Ctext x='50%25' y='55%25' font-size='10' fill='%239ca3af' text-anchor='middle'%3EError%3C/text%3E%3C/svg%3E";
                        }}
                      />
                      <div className="text-xs sm:text-sm text-gray-600">
                        <p className="font-medium">Your ballot photo</p>
                        <p className="text-[10px] sm:text-xs text-gray-500">This will appear on the voting page</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Submission Notice */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 sm:p-4 flex items-start gap-2 sm:gap-3">
                  <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={16} />
                  <div className="text-xs sm:text-sm text-amber-800">
                    <p className="font-medium mb-1">Before submitting:</p>
                    <ul className="list-disc list-inside space-y-0.5 sm:space-y-1 text-amber-700">
                      <li>Your registration will be reviewed</li>
                      <li>You will receive a notification once approved</li>
                      <li>Ensure all information is accurate</li>
                      <li>False information may lead to disqualification</li>
                    </ul>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Navigation Buttons */}
            <div className="mt-4 sm:mt-6 pt-4 border-t flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-0">
              <div className="flex justify-center sm:justify-start">
                {step > 1 && (
                  <button
                    type="button"
                    onClick={handleBack}
                    className="px-4 sm:px-6 py-2.5 text-gray-600 hover:bg-gray-100 active:bg-gray-200 rounded-lg transition-colors flex items-center justify-center gap-2 w-full sm:w-auto"
                    disabled={loading}
                  >
                    ← Back
                  </button>
                )}
              </div>
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
                <button
                  type="button"
                  onClick={resetAndClose}
                  className="px-4 sm:px-6 py-2.5 text-gray-600 hover:bg-gray-100 active:bg-gray-200 rounded-lg transition-colors order-2 sm:order-1"
                  disabled={loading}
                >
                  Cancel
                </button>
                {step < 3 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="px-6 sm:px-8 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 active:from-indigo-800 active:to-purple-800 font-medium transition-all order-1 sm:order-2"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={loading}
                    className="px-6 sm:px-8 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 active:from-green-800 active:to-emerald-800 font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all order-1 sm:order-2"
                  >
                    {loading ? (
                      <>
                        <Loader className="animate-spin" size={18} />
                        <span className="hidden xs:inline">Submitting...</span>
                        <span className="xs:hidden">...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle size={18} />
                        <span className="hidden xs:inline">Submit Registration</span>
                        <span className="xs:hidden">Submit</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
