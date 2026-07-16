import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  AlertCircle,
  Loader2,
  BookOpen,
  Clock,
  Users,
  MapPin,
  Wifi,
  Award,
  Coffee,
  DollarSign,
  FileText,
  Star,
  Calendar,
  Video,
  User,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useMentorship } from "../../Context/MentorshipContext";

const STEPS = [
  { id: 1, title: "Areas & Skills", icon: BookOpen },
  { id: 2, title: "Preferences", icon: Award },
  { id: 3, title: "Availability", icon: Clock },
  { id: 4, title: "Resources", icon: MapPin },
  { id: 5, title: "Interview", icon: Calendar },
  { id: 6, title: "Review", icon: FileText },
];

const INCENTIVE_OPTIONS = [
  { value: "certification", label: "Certification", icon: Award },
  {
    value: "publication",
    label: "Publication (Subject to T&C)",
    icon: FileText,
  },
  { value: "food_refreshments", label: "Food & Refreshments", icon: Coffee },
  { value: "monetary", label: "Monetary Compensation", icon: DollarSign },
  { value: "recognition", label: "Recognition by Society", icon: Star },
  { value: "none", label: "No Incentive", icon: null },
];

const SESSION_TYPES = [
  { value: "physical", label: "Physical", description: "In-person sessions" },
  { value: "virtual", label: "Virtual", description: "Online sessions" },
  { value: "hybrid", label: "Hybrid", description: "Mix of both" },
];

const CAPACITY_OPTIONS = [
  { value: "1-5", label: "1-5 Mentees" },
  { value: "6-10", label: "6-10 Mentees" },
  { value: "11-20", label: "11-20 Mentees" },
  { value: "20+", label: "20+ Mentees" },
];

const DAYS_OF_WEEK = [
  { value: "monday", label: "Mon" },
  { value: "tuesday", label: "Tue" },
  { value: "wednesday", label: "Wed" },
  { value: "thursday", label: "Thu" },
  { value: "friday", label: "Fri" },
  { value: "saturday", label: "Sat" },
  { value: "sunday", label: "Sun" },
];

export function ApplyMentorPage() {
  const navigate = useNavigate();
  const {
    areas,
    interviewers,
    eligibility,
    fetchAreas,
    fetchInterviewers,
    checkEligibility,
    submitMentorApplication,
    getAreaTags,
    loading,
  } = useMentorship();

  const [currentStep, setCurrentStep] = useState(1);
  const [availableTags, setAvailableTags] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [expandedInterviewer, setExpandedInterviewer] = useState(null);

  const [formData, setFormData] = useState({
    // Step 1: Areas & Skills
    areas: [],
    skills: [],
    additional_skills: "",
    experience_description: "",

    // Step 2: Preferences
    incentive_preferences: [],
    session_type: "hybrid",
    mentee_capacity: "1-5",

    // Step 3: Availability
    available_days: [],
    sessions_per_semester: 1,
    available_time_start: "09:00",
    available_time_end: "17:00",

    // Step 4: Resources
    needs_classroom: false,
    needs_data_support: false,
    other_resources: "",

    // Step 5: Interview Schedule
    selected_schedule_id: null,
    selected_interviewer_id: null,
  });

  useEffect(() => {
    fetchAreas();
    checkEligibility();
    fetchInterviewers();
  }, []);

  // Fetch tags when areas change
  useEffect(() => {
    const fetchTags = async () => {
      const allTags = [];
      for (const areaId of formData.areas) {
        const tags = await getAreaTags(areaId);
        allTags.push(...tags);
      }
      setAvailableTags(allTags);
    };

    if (formData.areas.length > 0) {
      fetchTags();
    } else {
      setAvailableTags([]);
    }
  }, [formData.areas]);

  const handleAreaToggle = (areaId) => {
    setFormData((prev) => ({
      ...prev,
      areas: prev.areas.includes(areaId)
        ? prev.areas.filter((id) => id !== areaId)
        : [...prev.areas, areaId],
      // Clear skills when areas change
      skills: prev.areas.includes(areaId)
        ? prev.skills.filter(
            (s) => !availableTags.find((t) => t.id === s)?.area === areaId
          )
        : prev.skills,
    }));
  };

  const handleSkillToggle = (skillId) => {
    setFormData((prev) => ({
      ...prev,
      skills: prev.skills.includes(skillId)
        ? prev.skills.filter((id) => id !== skillId)
        : [...prev.skills, skillId],
    }));
  };

  const handleIncentiveToggle = (value) => {
    setFormData((prev) => ({
      ...prev,
      incentive_preferences: prev.incentive_preferences.includes(value)
        ? prev.incentive_preferences.filter((v) => v !== value)
        : [...prev.incentive_preferences, value],
    }));
  };

  const handleDayToggle = (day) => {
    setFormData((prev) => ({
      ...prev,
      available_days: prev.available_days.includes(day)
        ? prev.available_days.filter((d) => d !== day)
        : [...prev.available_days, day],
    }));
  };

  const handleScheduleSelect = (interviewerId, scheduleId) => {
    setFormData((prev) => ({
      ...prev,
      selected_interviewer_id: interviewerId,
      selected_schedule_id: scheduleId,
    }));
  };

  const getSelectedScheduleDetails = () => {
    if (!formData.selected_schedule_id || !formData.selected_interviewer_id) {
      return null;
    }
    const interviewer = safeInterviewers.find(
      (i) => i.id === formData.selected_interviewer_id
    );
    if (!interviewer) return null;
    const schedules = Array.isArray(interviewer.schedules)
      ? interviewer.schedules
      : [];
    const schedule = schedules.find(
      (s) => s.id === formData.selected_schedule_id
    );
    return schedule ? { interviewer, schedule } : null;
  };

  // Ensure interviewers is always an array
  const safeInterviewers = Array.isArray(interviewers) ? interviewers : [];

  const validateStep = (step) => {
    switch (step) {
      case 1:
        return (
          formData.areas.length > 0 &&
          formData.experience_description.trim().length > 20
        );
      case 2:
        return (
          formData.incentive_preferences.length > 0 && formData.session_type
        );
      case 3:
        return (
          formData.available_days.length > 0 &&
          formData.sessions_per_semester > 0
        );
      case 4:
        return true; // Resources are optional
      case 5:
        return formData.selected_schedule_id !== null; // Must select an interview schedule
      case 6:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep) && currentStep < 6) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError(null);

    const result = await submitMentorApplication(formData);

    if (result.success) {
      setSubmitSuccess(true);
      setTimeout(() => {
        navigate("/dashboard/mentorship/my-applications");
      }, 2000);
    } else {
      setSubmitError(result.error);
    }

    setSubmitting(false);
  };

  // Check eligibility
  if (!eligibility?.is_eligible) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl p-8 shadow-lg max-w-md text-center"
        >
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Not Eligible</h2>
          <p className="text-gray-600 mb-6">
            {eligibility?.message ||
              "First-year students cannot apply as mentors. Please check back when you advance to the next year."}
          </p>
          <Link
            to="/dashboard/mentorship"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Mentorship
          </Link>
        </motion.div>
      </div>
    );
  }

  // Success screen
  if (submitSuccess) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl p-8 shadow-lg max-w-md text-center"
        >
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Application Submitted!
          </h2>
          <p className="text-gray-600 mb-4">
            Your mentor application has been submitted successfully. You'll need
            to schedule an interview to complete the process.
          </p>
          <p className="text-sm text-gray-500">Redirecting...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/dashboard/mentorship"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Mentorship
        </Link>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Become a Mentor
        </h1>
        <p className="text-gray-600">
          Complete your application to start mentoring
        </p>
      </div>

      {/* Progress Steps */}
      <div className="bg-white rounded-xl p-4 mb-6 shadow-sm">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    currentStep >= step.id
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-400"
                  }`}
                >
                  {currentStep > step.id ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <step.icon className="w-5 h-5" />
                  )}
                </div>
                <span
                  className={`text-xs mt-1 hidden md:block ${
                    currentStep >= step.id
                      ? "text-blue-600 font-medium"
                      : "text-gray-400"
                  }`}
                >
                  {step.title}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 rounded ${
                    currentStep > step.id ? "bg-blue-600" : "bg-gray-100"
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
        <AnimatePresence mode="wait">
          {/* Step 1: Areas & Skills */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Select Mentorship Areas
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  Choose the areas you want to mentor in
                </p>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {areas?.map((area) => (
                    <button
                      key={area.id}
                      onClick={() => handleAreaToggle(area.id)}
                      className={`p-3 rounded-xl border-2 text-left transition-all ${
                        formData.areas.includes(area.id)
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-100 hover:border-gray-200"
                      }`}
                      title={`${area.name}: ${area.tag_count || 0} skill${
                        (area.tag_count || 0) !== 1 ? "s" : ""
                      } available to select`}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: area.color }}
                        />
                        <span className="font-medium text-sm text-gray-900">
                          {area.name}
                        </span>
                      </div>
                      <p
                        className="text-xs text-gray-500 mt-1"
                        title={`${
                          area.tag_count || 0
                        } skills you can select from this area`}
                      >
                        {area.tag_count || 0} skills
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {availableTags.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">
                    Select Your Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {availableTags.map((tag) => (
                      <button
                        key={tag.id}
                        onClick={() => handleSkillToggle(tag.id)}
                        className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                          formData.skills.includes(tag.id)
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                      >
                        {tag.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <label className="block font-medium text-gray-900 mb-2">
                  Additional Skills (optional)
                </label>
                <input
                  type="text"
                  value={formData.additional_skills}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      additional_skills: e.target.value,
                    }))
                  }
                  placeholder="Other skills not listed above..."
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-900 mb-2">
                  Experience Description *
                </label>
                <textarea
                  value={formData.experience_description}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      experience_description: e.target.value,
                    }))
                  }
                  placeholder="Describe your experience in the selected areas. Include projects, courses, or real-world applications..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum 20 characters
                </p>
              </div>
            </motion.div>
          )}

          {/* Step 2: Preferences */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Incentive Preferences
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  What would you like in return for mentoring?
                </p>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {INCENTIVE_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handleIncentiveToggle(option.value)}
                      className={`p-3 rounded-xl border-2 text-left transition-all ${
                        formData.incentive_preferences.includes(option.value)
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-100 hover:border-gray-200"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {option.icon && (
                          <option.icon className="w-4 h-4 text-gray-600" />
                        )}
                        <span className="font-medium text-sm text-gray-900">
                          {option.label}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">
                  Preferred Session Type
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {SESSION_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() =>
                        setFormData((prev) => ({
                          ...prev,
                          session_type: type.value,
                        }))
                      }
                      className={`p-4 rounded-xl border-2 text-center transition-all ${
                        formData.session_type === type.value
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-100 hover:border-gray-200"
                      }`}
                    >
                      <span className="font-medium text-gray-900">
                        {type.label}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        {type.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">
                  Mentee Capacity
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {CAPACITY_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      onClick={() =>
                        setFormData((prev) => ({
                          ...prev,
                          mentee_capacity: option.value,
                        }))
                      }
                      className={`p-3 rounded-xl border-2 text-center transition-all ${
                        formData.mentee_capacity === option.value
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-100 hover:border-gray-200"
                      }`}
                    >
                      <span className="font-medium text-sm text-gray-900">
                        {option.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 3: Availability */}
          {currentStep === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Your Availability
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  When can you meet with mentees?
                </p>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">
                  Available Days *
                </h3>
                <div className="flex flex-wrap gap-2">
                  {DAYS_OF_WEEK.map((day) => (
                    <button
                      key={day.value}
                      onClick={() => handleDayToggle(day.value)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        formData.available_days.includes(day.value)
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {day.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-medium text-gray-900 mb-2">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={formData.available_time_start}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        available_time_start: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-900 mb-2">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={formData.available_time_end}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        available_time_end: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-gray-900 mb-2">
                  Sessions per Semester
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.sessions_per_semester}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      sessions_per_semester: parseInt(e.target.value) || 1,
                    }))
                  }
                  className="w-32 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  How many sessions can you conduct per semester?
                </p>
              </div>
            </motion.div>
          )}

          {/* Step 4: Resources */}
          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Resource Requirements
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  What do you need to conduct effective mentoring sessions?
                </p>
              </div>

              <div className="space-y-3">
                <label className="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.needs_classroom}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        needs_classroom: e.target.checked,
                      }))
                    }
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-gray-600" />
                    <div>
                      <span className="font-medium text-gray-900">
                        Classroom / Meeting Space
                      </span>
                      <p className="text-xs text-gray-500">
                        Need a physical space for sessions
                      </p>
                    </div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.needs_data_support}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        needs_data_support: e.target.checked,
                      }))
                    }
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex items-center gap-2">
                    <Wifi className="w-5 h-5 text-gray-600" />
                    <div>
                      <span className="font-medium text-gray-900">
                        Data / Internet Support
                      </span>
                      <p className="text-xs text-gray-500">
                        Need data bundles for virtual sessions
                      </p>
                    </div>
                  </div>
                </label>
              </div>

              <div>
                <label className="block font-medium text-gray-900 mb-2">
                  Other Resources (optional)
                </label>
                <textarea
                  value={formData.other_resources}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      other_resources: e.target.value,
                    }))
                  }
                  placeholder="Any other resources you might need..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
            </motion.div>
          )}

          {/* Step 5: Interview Scheduling */}
          {currentStep === 5 && (
            <motion.div
              key="step5"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Schedule Your Interview
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  Select an interviewer and choose an available time slot for
                  your interview
                </p>
              </div>

              {safeInterviewers.length === 0 ? (
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">
                    No interviewers available at the moment
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    Please check back later or contact the admin
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {safeInterviewers.map((interviewer) => {
                    const schedules = Array.isArray(interviewer.schedules)
                      ? interviewer.schedules.filter((s) => s.is_available)
                      : [];
                    const isExpanded = expandedInterviewer === interviewer.id;

                    return (
                      <div
                        key={interviewer.id}
                        className={`border-2 rounded-xl overflow-hidden transition-all ${
                          formData.selected_interviewer_id === interviewer.id
                            ? "border-blue-500 bg-blue-50/50"
                            : "border-gray-100 hover:border-gray-200"
                        }`}
                      >
                        {/* Interviewer Header */}
                        <button
                          onClick={() =>
                            setExpandedInterviewer(
                              isExpanded ? null : interviewer.id
                            )
                          }
                          className="w-full p-4 flex items-center justify-between text-left"
                        >
                          <div className="flex items-center gap-3">
                            {interviewer.profile_image ? (
                              <img
                                src={interviewer.profile_image}
                                alt={interviewer.full_name || "Interviewer"}
                                className="w-12 h-12 rounded-full object-cover"
                              />
                            ) : (
                              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                                {interviewer.full_name?.charAt(0) ||
                                  interviewer.user?.first_name?.charAt(0) ||
                                  "I"}
                              </div>
                            )}
                            <div>
                              <h3 className="font-semibold text-gray-900">
                                {interviewer.full_name ||
                                  `${interviewer.user?.first_name || ""} ${
                                    interviewer.user?.last_name || ""
                                  }`}
                              </h3>
                              <div
                                className="flex items-center gap-2 text-sm text-gray-500"
                                title={`${
                                  schedules.length
                                } interview time slot${
                                  schedules.length !== 1 ? "s" : ""
                                } available for booking`}
                              >
                                <Calendar className="w-4 h-4" />
                                <span>
                                  {schedules.length} available slot
                                  {schedules.length !== 1 ? "s" : ""}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {formData.selected_interviewer_id ===
                              interviewer.id && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                                Selected
                              </span>
                            )}
                            {isExpanded ? (
                              <ChevronUp className="w-5 h-5 text-gray-400" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-gray-400" />
                            )}
                          </div>
                        </button>

                        {/* Interviewer Details & Schedules */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: "auto", opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="border-t border-gray-100"
                            >
                              <div className="p-4 bg-gray-50/50">
                                {/* Areas of expertise */}
                                {interviewer.areas &&
                                  interviewer.areas.length > 0 && (
                                    <div className="mb-4">
                                      <p className="text-xs text-gray-500 mb-2">
                                        Areas of Expertise
                                      </p>
                                      <div className="flex flex-wrap gap-2">
                                        {interviewer.areas.map((area) => (
                                          <span
                                            key={area.id || area}
                                            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                                          >
                                            {area.name || area}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                {/* Bio */}
                                {interviewer.bio && (
                                  <p className="text-sm text-gray-600 mb-4">
                                    {interviewer.bio}
                                  </p>
                                )}

                                {/* Available Schedules */}
                                <div>
                                  <p className="text-xs text-gray-500 mb-2">
                                    Available Time Slots
                                  </p>
                                  {schedules.length === 0 ? (
                                    <p className="text-sm text-gray-400">
                                      No available slots for this interviewer
                                    </p>
                                  ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                      {schedules.map((schedule) => (
                                        <button
                                          key={schedule.id}
                                          onClick={() =>
                                            handleScheduleSelect(
                                              interviewer.id,
                                              schedule.id
                                            )
                                          }
                                          className={`p-3 rounded-lg border text-left transition-all ${
                                            formData.selected_schedule_id ===
                                            schedule.id
                                              ? "border-blue-500 bg-blue-100"
                                              : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50"
                                          }`}
                                        >
                                          <div className="flex items-center justify-between mb-1">
                                            <span className="font-medium text-gray-900 text-sm">
                                              {new Date(
                                                schedule.date
                                              ).toLocaleDateString("en-US", {
                                                weekday: "short",
                                                month: "short",
                                                day: "numeric",
                                              })}
                                            </span>
                                            <span
                                              className={`px-2 py-0.5 text-xs rounded-full ${
                                                schedule.interview_type ===
                                                "virtual"
                                                  ? "bg-purple-100 text-purple-700"
                                                  : schedule.interview_type ===
                                                    "physical"
                                                  ? "bg-green-100 text-green-700"
                                                  : "bg-blue-100 text-blue-700"
                                              }`}
                                            >
                                              {schedule.interview_type_display ||
                                                schedule.interview_type}
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-1 text-gray-600 text-sm">
                                            <Clock className="w-3 h-3" />
                                            <span>
                                              {schedule.start_time?.slice(0, 5)}{" "}
                                              - {schedule.end_time?.slice(0, 5)}
                                            </span>
                                          </div>
                                          {schedule.location && (
                                            <div className="flex items-center gap-1 text-gray-500 text-xs mt-1">
                                              <MapPin className="w-3 h-3" />
                                              <span>{schedule.location}</span>
                                            </div>
                                          )}
                                          {formData.selected_schedule_id ===
                                            schedule.id && (
                                            <div className="flex items-center gap-1 text-blue-600 text-xs mt-2">
                                              <Check className="w-3 h-3" />
                                              <span>Selected</span>
                                            </div>
                                          )}
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Selected Schedule Summary */}
              {formData.selected_schedule_id && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-green-800">
                        Interview Scheduled
                      </p>
                      {(() => {
                        const details = getSelectedScheduleDetails();
                        if (!details) return null;
                        return (
                          <div className="text-sm text-green-700 mt-1">
                            <p>
                              <strong>Interviewer:</strong>{" "}
                              {details.interviewer.full_name ||
                                `${
                                  details.interviewer.user?.first_name || ""
                                } ${details.interviewer.user?.last_name || ""}`}
                            </p>
                            <p>
                              <strong>Date:</strong>{" "}
                              {new Date(
                                details.schedule.date
                              ).toLocaleDateString("en-US", {
                                weekday: "long",
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                              })}
                            </p>
                            <p>
                              <strong>Time:</strong>{" "}
                              {details.schedule.start_time?.slice(0, 5)} -{" "}
                              {details.schedule.end_time?.slice(0, 5)}
                            </p>
                            <p>
                              <strong>Type:</strong>{" "}
                              {details.schedule.interview_type_display ||
                                details.schedule.interview_type}
                            </p>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Step 6: Review */}
          {currentStep === 6 && (
            <motion.div
              key="step6"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">
                  Review Your Application
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                  Please review your information before submitting
                </p>
              </div>

              {submitError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800">Submission Error</p>
                    <p className="text-sm text-red-600">
                      {typeof submitError === "object"
                        ? JSON.stringify(submitError)
                        : submitError}
                    </p>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h3 className="font-medium text-gray-900 mb-2">
                    Areas & Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {formData.areas.map((areaId) => {
                      const area = areas?.find((a) => a.id === areaId);
                      return area ? (
                        <span
                          key={areaId}
                          className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                        >
                          {area.name}
                        </span>
                      ) : null;
                    })}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {formData.experience_description}
                  </p>
                </div>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <h3 className="font-medium text-gray-900 mb-2">
                    Preferences
                  </h3>
                  <p className="text-sm text-gray-600">
                    <strong>Incentives:</strong>{" "}
                    {formData.incentive_preferences.join(", ")}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Session Type:</strong> {formData.session_type}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Mentee Capacity:</strong> {formData.mentee_capacity}
                  </p>
                </div>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <h3 className="font-medium text-gray-900 mb-2">
                    Availability
                  </h3>
                  <p className="text-sm text-gray-600">
                    <strong>Days:</strong> {formData.available_days.join(", ")}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Time:</strong> {formData.available_time_start} -{" "}
                    {formData.available_time_end}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Sessions/Semester:</strong>{" "}
                    {formData.sessions_per_semester}
                  </p>
                </div>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <h3 className="font-medium text-gray-900 mb-2">Resources</h3>
                  <p className="text-sm text-gray-600">
                    {formData.needs_classroom && "✓ Classroom needed  "}
                    {formData.needs_data_support && "✓ Data support needed"}
                    {!formData.needs_classroom &&
                      !formData.needs_data_support &&
                      "No special resources needed"}
                  </p>
                  {formData.other_resources && (
                    <p className="text-sm text-gray-600 mt-1">
                      {formData.other_resources}
                    </p>
                  )}
                </div>

                {/* Interview Schedule */}
                <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <h3 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    Interview Schedule
                  </h3>
                  {(() => {
                    const details = getSelectedScheduleDetails();
                    if (!details) {
                      return (
                        <p className="text-sm text-gray-500">
                          No interview scheduled
                        </p>
                      );
                    }
                    return (
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          <strong>Interviewer:</strong>{" "}
                          {details.interviewer.full_name ||
                            `${details.interviewer.user?.first_name || ""} ${
                              details.interviewer.user?.last_name || ""
                            }`}
                        </p>
                        <p>
                          <strong>Date:</strong>{" "}
                          {new Date(details.schedule.date).toLocaleDateString(
                            "en-US",
                            {
                              weekday: "long",
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            }
                          )}
                        </p>
                        <p>
                          <strong>Time:</strong>{" "}
                          {details.schedule.start_time?.slice(0, 5)} -{" "}
                          {details.schedule.end_time?.slice(0, 5)}
                        </p>
                        <p>
                          <strong>Type:</strong>{" "}
                          {details.schedule.interview_type_display ||
                            details.schedule.interview_type}
                        </p>
                        {details.schedule.location && (
                          <p>
                            <strong>Location:</strong>{" "}
                            {details.schedule.location}
                          </p>
                        )}
                      </div>
                    );
                  })()}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            currentStep === 1
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        {currentStep < 6 ? (
          <button
            onClick={handleNext}
            disabled={!validateStep(currentStep)}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${
              validateStep(currentStep)
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Submit Application
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default ApplyMentorPage;
