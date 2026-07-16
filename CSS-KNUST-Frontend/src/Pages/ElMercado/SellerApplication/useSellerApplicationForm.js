import { useState, useEffect, useContext, useCallback } from "react";
import { useElMercado } from "../../../Context/ElMercadoContext";
import { UserContext } from "../../../Context/UserContext";
import { INITIAL_FORM_DATA, INITIAL_FILE_NAMES } from "./constants";

export function useSellerApplicationForm() {
  const { user } = useContext(UserContext);
  const {
    categories,
    fetchCategories,
    submitSellerApplication,
    updateSellerApplication,
    fetchMyApplications,
  } = useElMercado();

  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [existingApplication, setExistingApplication] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  const [formData, setFormData] = useState(INITIAL_FORM_DATA);
  const [fileNames, setFileNames] = useState(INITIAL_FILE_NAMES);

  // Fetch categories and existing applications on mount
  useEffect(() => {
    fetchCategories();
    
    if (user) {
      fetchMyApplications().then((apps) => {
        const editable = apps?.find(
          (app) => ["PENDING", "UNDER_REVIEW", "REVISION_REQUESTED", "APPROVED", "REJECTED"].includes(app.status)
        );
        if (editable) {
          setExistingApplication(editable);
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Pre-fill user data (only if not in edit mode)
  useEffect(() => {
    if (user && user.user && !isEditMode) {
      const userData = user.user; // Extract actual user data from auth object
      
      // Construct full name with all available name parts
      const nameParts = [
        userData.first_name,
        userData.middle_name,
        userData.last_name
      ].filter(part => part && part.trim() !== ''); // Remove empty/null parts
      
      const fullName = nameParts.join(' ').trim();
      
      // Use personal_email only
      const emailAddress = userData.personal_email || '';
      
      setFormData((prev) => ({
        ...prev,
        is_student: 'student', // Auto-set as student for logged-in users
        applicant_name: fullName || '',
        applicant_email: emailAddress,
        applicant_phone: userData.phone || '',
      }));
    }
  }, [user, isEditMode]);

  // Populate form with existing application data
  const populateFormWithExistingData = useCallback((application) => {
    setFormData({
      seller_type: application.seller_type || "",
      applicant_name: application.applicant_name || "",
      applicant_email: application.applicant_email || "",
      applicant_phone: application.applicant_phone || "",
      address_line_1: application.address_line_1 || "",
      address_line_2: application.address_line_2 || "",
      city: application.city || "",
      region: application.region || "",
      country: application.country || "Ghana",
      id_document: null,
      id_document_type: application.id_document_type || "",
      proof_of_address: null,
      business_name: application.business_name || "",
      business_registration_number: application.business_registration_number || "",
      business_type: application.business_type || "",
      business_document: null,
      description: application.description || "",
      categories_of_interest: application.categories_of_interest || [],
    });
    
    setFileNames({
      id_document: application.id_document ? "Existing document uploaded" : "",
      proof_of_address: application.proof_of_address ? "Existing document uploaded" : "",
      business_document: application.business_document ? "Existing document uploaded" : "",
    });
  }, []);

  // Enter edit mode
  const enterEditMode = useCallback(() => {
    if (existingApplication) {
      populateFormWithExistingData(existingApplication);
      setIsEditMode(true);
      setCurrentStep(1);
    }
  }, [existingApplication, populateFormWithExistingData]);

  // Cancel edit mode
  const cancelEditMode = useCallback(() => {
    setIsEditMode(false);
    setSubmitError(null);
    
    // Reconstruct user data same as in the useEffect
    let resetData = { ...INITIAL_FORM_DATA };
    
    if (user && user.user) {
      const userData = user.user;
      const nameParts = [
        userData.first_name,
        userData.middle_name,
        userData.last_name
      ].filter(part => part && part.trim() !== '');
      const fullName = nameParts.join(' ').trim();
      
      resetData = {
        ...resetData,
        is_student: 'student',
        applicant_name: fullName || '',
        applicant_email: userData.email || '',
        applicant_phone: userData.phone_number || userData.phone || '',
      };
    }
    
    setFormData(resetData);
    setFileNames(INITIAL_FILE_NAMES);
  }, [user]);

  // Handle input changes - updated to handle both event objects and direct values
  const handleInputChange = useCallback((eventOrField, value) => {
    if (typeof eventOrField === 'string') {
      // Direct field/value call
      setFormData((prev) => ({ ...prev, [eventOrField]: value }));
    } else {
      // Event object
      const field = eventOrField.target.name;
      const val = eventOrField.target.value;
      setFormData((prev) => ({ ...prev, [field]: val }));
    }
    setSubmitError(null);
  }, []);

  // Handle file changes
  const handleFileChange = useCallback((field, event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setSubmitError(`File ${file.name} is too large. Maximum size is 5MB.`);
        return;
      }
      setFormData((prev) => ({ ...prev, [field]: file }));
      setFileNames((prev) => ({ ...prev, [field]: file.name }));
      setSubmitError(null);
    }
  }, []);

  // Handle category toggle
  const handleCategoryToggle = useCallback((categoryId) => {
    setFormData((prev) => ({
      ...prev,
      categories_of_interest: prev.categories_of_interest.includes(categoryId)
        ? prev.categories_of_interest.filter((id) => id !== categoryId)
        : [...prev.categories_of_interest, categoryId],
    }));
  }, []);

  // Validate current step
  const validateStep = useCallback((step) => {
    switch (step) {
      case 1:
        return !!formData.is_student;
      case 2:
        return !!formData.seller_type;
      case 3:
        return (
          formData.applicant_name.trim() !== "" &&
          formData.applicant_email.trim() !== "" &&
          formData.applicant_phone.trim() !== ""
        );
      case 4:
        return (
          formData.address_line_1.trim() !== "" &&
          formData.city.trim() !== "" &&
          formData.region.trim() !== ""
        );
      case 5:
        if (isEditMode && existingApplication?.id_document) {
          return formData.id_document_type !== "";
        }
        return formData.id_document !== null && formData.id_document_type !== "";
      case 6:
        if (formData.seller_type === "BUSINESS") {
          const hasBusinessDoc = isEditMode && existingApplication?.business_document;
          return (
            formData.business_name.trim() !== "" &&
            (hasBusinessDoc || formData.business_document !== null) &&
            formData.description.trim() !== ""
          );
        }
        return formData.description.trim() !== "";
      default:
        return true;
    }
  }, [formData, isEditMode, existingApplication]);

  // Navigation
  const nextStep = useCallback(() => {
    if (validateStep(currentStep) && currentStep < 7) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep, validateStep]);

  const prevStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((step) => {
    if (step >= 1 && step <= 7) {
      setCurrentStep(step);
    }
  }, []);

  // Submit form
  const handleSubmit = useCallback(async () => {
    setSubmitting(true);
    setSubmitError(null);

    try {
      let result;
      
      if (isEditMode && existingApplication) {
        result = await updateSellerApplication(existingApplication.id, formData);
        
        if (result.success) {
          setUpdateSuccess(true);
          setIsEditMode(false);
          const apps = await fetchMyApplications();
          const updated = apps?.find((app) => app.id === existingApplication.id);
          if (updated) {
            setExistingApplication(updated);
          }
        } else {
          setSubmitError(result.error || "Failed to update application. Please try again.");
        }
      } else {
        result = await submitSellerApplication(formData);

        if (result.success) {
          setSubmitSuccess(true);
        } else {
          setSubmitError(result.error || "Failed to submit application. Please try again.");
        }
      }
    } catch {
      setSubmitError("An unexpected error occurred. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }, [isEditMode, existingApplication, formData, updateSellerApplication, submitSellerApplication, fetchMyApplications]);

  // Copy tracking code
  const copyTrackingCode = useCallback((code) => {
    navigator.clipboard.writeText(code);
  }, []);

  // Dismiss update success
  const dismissUpdateSuccess = useCallback(() => {
    setUpdateSuccess(false);
  }, []);

  return {
    // State
    user,
    categories,
    currentStep,
    submitting,
    submitError,
    submitSuccess,
    existingApplication,
    isEditMode,
    updateSuccess,
    formData,
    fileNames,
    
    // Actions
    setCurrentStep,
    enterEditMode,
    cancelEditMode,
    handleInputChange,
    handleFileChange,
    handleCategoryToggle,
    validateStep,
    nextStep,
    prevStep,
    goToStep,
    handleSubmit,
    copyTrackingCode,
    dismissUpdateSuccess,
  };
}

export default useSellerApplicationForm;
