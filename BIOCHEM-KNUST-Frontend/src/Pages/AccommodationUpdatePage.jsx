import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  Building2,
  MapPin,
  Phone,
  User,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Loader2,
  Building,
  DoorOpen,
  MessageCircle,
  ExternalLink,
  XCircle,
  RefreshCw,
} from "lucide-react";
import { postData } from "../utils/apiHandler";
import { BACKEND_HOST } from "../utils/config";

const AccommodationUpdatePage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [alreadySubmitted, setAlreadySubmitted] = useState(null); // Stores data if already submitted

  // Step 1: Identity verification data
  const [identityData, setIdentityData] = useState({
    applicant_id: "",
    phone_number: "",
  });

  // Step 2: Name verification data
  const [nameData, setNameData] = useState({
    first_name: "",
    last_name: "",
    other_names: "",
  });

  // Step 3: Accommodation data
  const [accommodationData, setAccommodationData] = useState({
    accommodation_type: "",
    campus_status: "",
    hall_name: "",
    hostel_name: "",
    room_number: "",
  });

  // Stored data from API responses
  const [verifiedInfo, setVerifiedInfo] = useState(null);
  const [finalResult, setFinalResult] = useState(null);
  const [joiningGroup, setJoiningGroup] = useState(false);

  // Secure function to join WhatsApp group (prevents link copying)
  const handleJoinGroup = async (applicantId, token) => {
    if (!applicantId || !token) return;
    
    setJoiningGroup(true);
    
    // Build the secure redirect URL
    const redirectUrl = `${BACKEND_HOST}/admissions/accommodation/join-group/${applicantId}/${encodeURIComponent(token)}/`;
    
    // Open in new window (harder to copy than href)
    const newWindow = window.open(redirectUrl, '_blank', 'noopener,noreferrer');
    
    // If popup blocked, try direct navigation
    if (!newWindow) {
      window.location.href = redirectUrl;
    }
    
    setTimeout(() => setJoiningGroup(false), 2000);
  };

  // Refresh token for already submitted users
  const handleRefreshToken = async () => {
    const applicantId = alreadySubmitted?.applicant_id || finalResult?.applicant_id;
    if (!applicantId) return;
    
    setJoiningGroup(true);
    const { response, error: apiError } = await postData(
      "/admissions/accommodation/get-group-access/",
      { applicant_id: applicantId }
    );
    setJoiningGroup(false);
    
    if (response?.status === "success" && response.data?.token) {
      // Now join with new token
      handleJoinGroup(applicantId, response.data.token);
    } else {
      setError(apiError?.message || response?.message || "Failed to get group access");
    }
  };

  const steps = [
    { number: 1, title: "Verify Identity", icon: User },
    { number: 2, title: "Confirm Name", icon: CheckCircle },
    { number: 3, title: "Accommodation Details", icon: Home },
  ];

  const accommodationTypes = [
    { value: "TRADITIONAL_HALL", label: "Traditional Hall", icon: Building },
    { value: "HOSTEL", label: "Hostel", icon: Building2 },
    { value: "OFF_CAMPUS", label: "Off Campus", icon: MapPin },
  ];

  const hallOptions = [
    { value: "UNITY_HALL", label: "Unity Hall (Conti)" },
    { value: "QUEENS_HALL", label: "Queen's Hall" },
    { value: "INDEPENDENCE_HALL", label: "Independence Hall (Indece)" },
    { value: "AFRICA_HALL", label: "Africa Hall" },
    { value: "REPUBLIC_HALL", label: "Republic Hall (Rep)" },
    { value: "UNIVERSITY_HALL", label: "University Hall (Katanga)" },
    { value: "OTHER", label: "Other" },
  ];

  const handleIdentitySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { response, error: apiError } = await postData(
      "/admissions/accommodation/verify-identity/",
      identityData
    );

    setLoading(false);

    if (apiError) {
      // Check if it's "already submitted" response
      if (apiError.status === "already_submitted") {
        setAlreadySubmitted(apiError.data);
        return;
      }
      setError(apiError.message || "Failed to verify identity. Please check your details.");
      return;
    }

    if (response?.status === "already_submitted") {
      setAlreadySubmitted(response.data);
      return;
    }

    if (response?.status === "success") {
      setVerifiedInfo(response.data);
      setCurrentStep(2);
    } else {
      setError(response?.message || "Verification failed");
    }
  };

  const handleNameSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { response, error: apiError } = await postData(
      "/admissions/accommodation/verify-name/",
      {
        applicant_id: identityData.applicant_id,
        ...nameData,
      }
    );

    setLoading(false);

    if (apiError) {
      setError(apiError.message || "Name verification failed. Please enter your name exactly as it appears on your admission letter.");
      return;
    }

    if (response?.status === "success") {
      setVerifiedInfo((prev) => ({ ...prev, ...response.data }));
      setCurrentStep(3);
    } else {
      setError(response?.message || "Name does not match our records");
    }
  };

  const handleAccommodationSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      applicant_id: identityData.applicant_id,
      phone_number: identityData.phone_number,
      ...accommodationData,
    };

    // Clean up unnecessary fields based on accommodation type
    if (accommodationData.accommodation_type === "TRADITIONAL_HALL") {
      delete payload.hostel_name;
    } else if (accommodationData.accommodation_type === "HOSTEL") {
      delete payload.hall_name;
    } else if (accommodationData.accommodation_type === "OFF_CAMPUS") {
      delete payload.hall_name;
      delete payload.hostel_name;
      delete payload.room_number;
    }

    const { response, error: apiError } = await postData(
      "/admissions/accommodation/update/",
      payload
    );

    setLoading(false);

    if (apiError) {
      setError(apiError.message || apiError.errors ? Object.values(apiError.errors).flat().join(", ") : "Failed to update accommodation");
      return;
    }

    if (response?.status === "success") {
      setFinalResult(response.data);
      setSuccess(true);
    } else {
      setError(response?.message || "Update failed");
    }
  };

  const resetForm = () => {
    setCurrentStep(1);
    setIdentityData({ applicant_id: "", phone_number: "" });
    setNameData({ first_name: "", last_name: "", other_names: "" });
    setAccommodationData({
      accommodation_type: "",
      campus_status: "",
      hall_name: "",
      hostel_name: "",
      room_number: "",
    });
    setVerifiedInfo(null);
    setFinalResult(null);
    setAlreadySubmitted(null);
    setError(null);
    setSuccess(false);
  };

  // Auto-set campus_status based on accommodation type
  const handleAccommodationTypeChange = (type) => {
    let newStatus = accommodationData.campus_status;
    if (type === "TRADITIONAL_HALL") {
      newStatus = "ON_CAMPUS";
    } else if (type === "OFF_CAMPUS") {
      newStatus = "OFF_CAMPUS";
    }
    setAccommodationData({
      ...accommodationData,
      accommodation_type: type,
      campus_status: newStatus,
      // Reset hall/hostel when type changes
      hall_name: type === "TRADITIONAL_HALL" ? accommodationData.hall_name : "",
      hostel_name: type === "HOSTEL" ? accommodationData.hostel_name : "",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-red-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex justify-center mb-4">
            <div className="bg-red-600 p-4 rounded-full">
              <Home className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Fresher Registration
          </h1>
          <p className="text-gray-600">
            Register your accommodation details & join your official class WhatsApp group
          </p>
        </motion.div>

        {/* Success State */}
        {success && finalResult && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-xl p-8 text-center"
          >
            <div className="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {finalResult.success_message}
            </h2>
            <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
              <h3 className="font-semibold text-gray-900 mb-3">Your Details:</h3>
              <div className="space-y-2 text-gray-700">
                <p><span className="font-medium">Name:</span> {finalResult.student_name}</p>
                <p><span className="font-medium">Programme:</span> {finalResult.programme}</p>
                <p><span className="font-medium">Accommodation:</span> {finalResult.accommodation?.display}</p>
                <p><span className="font-medium">Phone:</span> {finalResult.phone_number}</p>
              </div>
            </div>

            {/* WhatsApp Group Link (Secure) */}
            {finalResult.whatsapp_group?.available && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <MessageCircle className="w-6 h-6 text-green-600" />
                  <h3 className="font-semibold text-green-800">
                    Join Your Official WhatsApp Group!
                  </h3>
                </div>
                <p className="text-green-700 text-sm mb-4">
                  {finalResult.whatsapp_group.description || `Welcome to the ${finalResult.whatsapp_group.name || 'your academic WhatsApp group'}! Click below to join your class group.`}
                </p>
                <button
                  onClick={() => {
                    if (finalResult.whatsapp_group.token) {
                      handleJoinGroup(finalResult.applicant_id, finalResult.whatsapp_group.token);
                    } else {
                      handleRefreshToken();
                    }
                  }}
                  disabled={joiningGroup}
                  className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {joiningGroup ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Opening...
                    </>
                  ) : (
                    <>
                      <MessageCircle className="w-5 h-5" />
                      Join {finalResult.whatsapp_group.name || 'WhatsApp Group'}
                      <ExternalLink className="w-4 h-4" />
                    </>
                  )}
                </button>
                <p className="text-xs text-gray-500 mt-3">
                  🔒 Secure link - opens your WhatsApp group directly
                </p>
              </div>
            )}

            <p className="text-sm text-gray-500 mb-4">
              ⚠️ This is a one-time submission. For any changes, contact the CSS President.
            </p>
            <button
              onClick={resetForm}
              className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Check Another Student
            </button>
          </motion.div>
        )}

        {/* Already Submitted State */}
        {alreadySubmitted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-xl p-8 text-center"
          >
            <div className="bg-yellow-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-12 h-12 text-yellow-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Already Submitted
            </h2>
            <p className="text-gray-600 mb-6">
              Accommodation details have already been submitted for this application ID.
            </p>
            <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
              <h3 className="font-semibold text-gray-900 mb-3">Submitted Details:</h3>
              <div className="space-y-2 text-gray-700">
                <p><span className="font-medium">Name:</span> {alreadySubmitted.student_name}</p>
                <p><span className="font-medium">Programme:</span> {alreadySubmitted.programme}</p>
                <p><span className="font-medium">Accommodation Type:</span> {alreadySubmitted.accommodation?.type}</p>
                {alreadySubmitted.accommodation?.hall && (
                  <p><span className="font-medium">Hall:</span> {alreadySubmitted.accommodation.hall}</p>
                )}
                {alreadySubmitted.accommodation?.hostel && (
                  <p><span className="font-medium">Hostel:</span> {alreadySubmitted.accommodation.hostel}</p>
                )}
                {alreadySubmitted.accommodation?.room && (
                  <p><span className="font-medium">Room:</span> {alreadySubmitted.accommodation.room}</p>
                )}
                <p><span className="font-medium">Phone:</span> {alreadySubmitted.phone_number}</p>
                {alreadySubmitted.updated_at && (
                  <p><span className="font-medium">Submitted:</span> {new Date(alreadySubmitted.updated_at).toLocaleDateString()}</p>
                )}
              </div>
            </div>
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-lg mb-6 text-left">
              <p className="text-yellow-800 text-sm">
                <strong>Note:</strong> {alreadySubmitted.help_text || "Each student can only submit once. If you need to make changes, please contact the President of the Biochemistry Society, KNUST."}
              </p>
            </div>

            {/* WhatsApp Group Join for Already Submitted Users */}
            {alreadySubmitted.whatsapp_group?.available && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <MessageCircle className="w-6 h-6 text-green-600" />
                  <h3 className="font-semibold text-green-800">
                  Couldn&apos;t Join the Group?
                  </h3>
                </div>
                <p className="text-green-700 text-sm mb-4">
                  {alreadySubmitted.whatsapp_group.description || "Click below to join your official academic WhatsApp group."}
                </p>
                <button
                  onClick={handleRefreshToken}
                  disabled={joiningGroup}
                  className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {joiningGroup ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Opening...
                    </>
                  ) : (
                    <>
                      <MessageCircle className="w-5 h-5" />
                      Click Here to Join
                      <ExternalLink className="w-4 h-4" />
                    </>
                  )}
                </button>
                <p className="text-xs text-gray-500 mt-3">
                  🔒 Secure link - opens your WhatsApp group directly
                </p>
              </div>
            )}

            <button
              onClick={resetForm}
              className="bg-red-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-red-700 transition-colors"
            >
              Check Another Student
            </button>
          </motion.div>
        )}

        {/* Form Steps */}
        {!success && !alreadySubmitted && (
          <>
            {/* Progress Steps */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                {steps.map((step, index) => (
                  <div key={step.number} className="flex items-center flex-1">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-colors ${
                          currentStep >= step.number
                            ? "bg-red-600 text-white"
                            : "bg-gray-200 text-gray-500"
                        }`}
                      >
                        {currentStep > step.number ? (
                          <CheckCircle className="w-6 h-6" />
                        ) : (
                          <step.icon className="w-6 h-6" />
                        )}
                      </div>
                      <span className="text-xs mt-2 text-gray-600 text-center hidden sm:block">
                        {step.title}
                      </span>
                    </div>
                    {index < steps.length - 1 && (
                      <div
                        className={`flex-1 h-1 mx-2 rounded ${
                          currentStep > step.number ? "bg-red-600" : "bg-gray-200"
                        }`}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Error Display */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg mb-6"
                >
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-red-800 font-medium">Error</p>
                      <p className="text-red-700 text-sm">{error}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setError(null)}
                    className="mt-2 text-red-600 text-sm underline"
                  >
                    Dismiss
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form Card */}
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white rounded-2xl shadow-xl overflow-hidden"
            >
              {/* Step 1: Identity Verification */}
              {currentStep === 1 && (
                <form onSubmit={handleIdentitySubmit}>
                  <div className="p-6 bg-gradient-to-r from-red-600 to-red-700 text-white">
                    <h2 className="text-xl font-bold">Step 1: Verify Your Identity</h2>
                    <p className="text-red-100 text-sm mt-1">
                      Enter your application ID and phone number
                    </p>
                  </div>
                  <div className="p-6 space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Application ID <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={identityData.applicant_id}
                        onChange={(e) =>
                          setIdentityData({
                            ...identityData,
                            applicant_id: e.target.value.toUpperCase(),
                          })
                        }
                        placeholder="e.g., 12345678"
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Your 8-digit KNUST application ID
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone Number <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="tel"
                          value={identityData.phone_number}
                          onChange={(e) =>
                            setIdentityData({
                              ...identityData,
                              phone_number: e.target.value,
                            })
                          }
                          placeholder="0241234567"
                          required
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-shadow"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Enter your 10-digit phone number
                      </p>
                    </div>

                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        <>
                          Verify Identity
                          <ArrowRight className="w-5 h-5" />
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}

              {/* Step 2: Name Verification */}
              {currentStep === 2 && (
                <form onSubmit={handleNameSubmit}>
                  <div className="p-6 bg-gradient-to-r from-red-600 to-red-700 text-white">
                    <h2 className="text-xl font-bold">Step 2: Confirm Your Name</h2>
                    <p className="text-red-100 text-sm mt-1">
                      Programme: {verifiedInfo?.programme}
                    </p>
                  </div>
                  <div className="p-6 space-y-6">
                    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                      <p className="text-blue-800 text-sm">
                        Enter your name exactly as it appears on your admission letter
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          First Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={nameData.first_name}
                          onChange={(e) =>
                            setNameData({ ...nameData, first_name: e.target.value })
                          }
                          placeholder="e.g., Kwame"
                          required
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Last Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={nameData.last_name}
                          onChange={(e) =>
                            setNameData({ ...nameData, last_name: e.target.value })
                          }
                          placeholder="e.g., Asante"
                          required
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Other Names (Optional)
                      </label>
                      <input
                        type="text"
                        value={nameData.other_names}
                        onChange={(e) =>
                          setNameData({ ...nameData, other_names: e.target.value })
                        }
                        placeholder="Middle name(s)"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      />
                    </div>

                    <div className="flex gap-4">
                      <button
                        type="button"
                        onClick={() => setCurrentStep(1)}
                        className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                      >
                        <ArrowLeft className="w-5 h-5" />
                        Back
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Verifying...
                          </>
                        ) : (
                          <>
                            Verify Name
                            <ArrowRight className="w-5 h-5" />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </form>
              )}

              {/* Step 3: Accommodation Details */}
              {currentStep === 3 && (
                <form onSubmit={handleAccommodationSubmit}>
                  <div className="p-6 bg-gradient-to-r from-red-600 to-red-700 text-white">
                    <h2 className="text-xl font-bold">Step 3: Accommodation Details</h2>
                    <p className="text-red-100 text-sm mt-1">
                      Welcome, {verifiedInfo?.verified_name}!
                    </p>
                  </div>
                  <div className="p-6 space-y-6">
                    {/* Accommodation Type */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Accommodation Type <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {accommodationTypes.map((type) => (
                          <button
                            key={type.value}
                            type="button"
                            onClick={() => handleAccommodationTypeChange(type.value)}
                            className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                              accommodationData.accommodation_type === type.value
                                ? "border-red-500 bg-red-50 text-red-700"
                                : "border-gray-200 hover:border-gray-300 text-gray-600"
                            }`}
                          >
                            <type.icon className="w-8 h-8" />
                            <span className="font-medium">{type.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Hall Name (for Traditional Hall) */}
                    {accommodationData.accommodation_type === "TRADITIONAL_HALL" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                      >
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Hall Name <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={accommodationData.hall_name}
                          onChange={(e) =>
                            setAccommodationData({
                              ...accommodationData,
                              hall_name: e.target.value,
                            })
                          }
                          required
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        >
                          <option value="">Select your hall</option>
                          {hallOptions.map((hall) => (
                            <option key={hall.value} value={hall.value}>
                              {hall.label}
                            </option>
                          ))}
                        </select>
                      </motion.div>
                    )}

                    {/* Hostel Name (for Hostel) */}
                    {accommodationData.accommodation_type === "HOSTEL" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                      >
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Hostel Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={accommodationData.hostel_name}
                          onChange={(e) =>
                            setAccommodationData({
                              ...accommodationData,
                              hostel_name: e.target.value,
                            })
                          }
                          placeholder="e.g., Ghana Hall, SRC Hostel"
                          required
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </motion.div>
                    )}

                    {/* Campus Status (for Hostel only) */}
                    {accommodationData.accommodation_type === "HOSTEL" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                      >
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Campus Status <span className="text-red-500">*</span>
                        </label>
                        <div className="flex gap-4">
                          {[
                            { value: "ON_CAMPUS", label: "On Campus" },
                            { value: "OFF_CAMPUS", label: "Off Campus" },
                          ].map((status) => (
                            <button
                              key={status.value}
                              type="button"
                              onClick={() =>
                                setAccommodationData({
                                  ...accommodationData,
                                  campus_status: status.value,
                                })
                              }
                              className={`flex-1 py-3 rounded-lg border-2 font-medium transition-all ${
                                accommodationData.campus_status === status.value
                                  ? "border-red-500 bg-red-50 text-red-700"
                                  : "border-gray-200 hover:border-gray-300 text-gray-600"
                              }`}
                            >
                              {status.label}
                            </button>
                          ))}
                        </div>
                      </motion.div>
                    )}

                    {/* Room Number (for on-campus) */}
                    {accommodationData.accommodation_type &&
                      accommodationData.accommodation_type !== "OFF_CAMPUS" && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                        >
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Room Number{" "}
                            {accommodationData.campus_status === "ON_CAMPUS" && (
                              <span className="text-red-500">*</span>
                            )}
                          </label>
                          <div className="relative">
                            <DoorOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                              type="text"
                              value={accommodationData.room_number}
                              onChange={(e) =>
                                setAccommodationData({
                                  ...accommodationData,
                                  room_number: e.target.value,
                                })
                              }
                              placeholder="e.g., A101, Block B Room 25"
                              required={accommodationData.campus_status === "ON_CAMPUS"}
                              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            />
                          </div>
                        </motion.div>
                      )}

                    <div className="flex gap-4 pt-4">
                      <button
                        type="button"
                        onClick={() => setCurrentStep(2)}
                        className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                      >
                        <ArrowLeft className="w-5 h-5" />
                        Back
                      </button>
                      <button
                        type="submit"
                        disabled={loading || !accommodationData.accommodation_type}
                        className="flex-1 bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Submitting...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-5 h-5" />
                            Submit
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </motion.div>
          </>
        )}

        {/* Info Card */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Important Information</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-red-500">•</span>
              This form is for newly admitted CS/IT students to register accommodation details and join official class groups.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500">•</span>
              Your Application ID can be found on your admission letter or KNUST online portal.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500">•</span>
              After successful registration, click on the button to join your official WhatsApp class group.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500">•</span>
              Ensure your phone number is active as it will be used for important communications.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500">•</span>
              <strong>Need help?</strong> Contact the President of the Biochemistry Society, KNUST.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AccommodationUpdatePage;
