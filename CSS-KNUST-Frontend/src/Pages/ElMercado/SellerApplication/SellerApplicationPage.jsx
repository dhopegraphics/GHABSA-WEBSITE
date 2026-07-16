import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../../../Components/Navbar";
import { Footer } from "../../../Components/Footer/Footer";

// Custom Hook
import { useSellerApplicationForm } from "./useSellerApplicationForm";

// Components
import {
  StepProgress,
  HeroSection,
  CheckStatusBanner,
  UserTypeStep,
  SellerTypeStep,
  PersonalInfoStep,
  AddressStep,
  DocumentsStep,
  BusinessInfoStep,
  ReviewStep,
  FormNavigation,
  ErrorDisplay,
  ApprovedStatusView,
  RejectedStatusView,
  PendingStatusView,
  SubmitSuccessView,
  LoginRequiredView,
  LoginPromptView,
} from "./components";

export function SellerApplicationPage() {
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  
  const {
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
    handleSubmit,
    copyTrackingCode,
    dismissUpdateSuccess,
  } = useSellerApplicationForm();

  // Handle student login requirement
  const handleStudentLoginRequired = () => {
    setShowLoginPrompt(true);
  };

  const handleBackToUserType = () => {
    setShowLoginPrompt(false);
    setCurrentStep(1);
    handleInputChange({ target: { name: 'is_student', value: '' } });
  };

  const handleLoginSuccess = (loggedInUser) => {
    setShowLoginPrompt(false);
    // Continue with the application flow
    setCurrentStep(2); // Skip to seller type step
  };

  // If user is already logged in, treat them as a student and skip user type selection
  // Set is_student to 'student' and start from step 2 (seller type)
  React.useEffect(() => {
    if (user && !formData.is_student && currentStep === 1) {
      handleInputChange({ target: { name: 'is_student', value: 'student' } });
      setCurrentStep(2); // Skip to seller type step
    }
  }, [user, formData.is_student, currentStep]);

  // Show login prompt for students (only if not already logged in)
  if (showLoginPrompt && !user) {
    return (
      <LoginPromptView 
        onBackToUserType={handleBackToUserType}
        onLoginSuccess={handleLoginSuccess}
      />
    );
  }

  // Show submit success view
  if (submitSuccess) {
    return <SubmitSuccessView />;
  }

  // Show existing application status views (if not in edit mode and user is student)
  if (existingApplication && !isEditMode && (user || formData.is_student === 'student')) {
    const { status } = existingApplication;

    if (status === "APPROVED") {
      return (
        <ApprovedStatusView 
          application={existingApplication} 
          onCopyTrackingCode={copyTrackingCode} 
        />
      );
    }

    if (status === "REJECTED") {
      return (
        <RejectedStatusView 
          application={existingApplication} 
          onCopyTrackingCode={copyTrackingCode} 
        />
      );
    }

    // PENDING, UNDER_REVIEW, REVISION_REQUESTED
    return (
      <PendingStatusView
        application={existingApplication}
        updateSuccess={updateSuccess}
        onDismissUpdateSuccess={dismissUpdateSuccess}
        onEnterEditMode={enterEditMode}
        onCopyTrackingCode={copyTrackingCode}
      />
    );
  }

  // Render current step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        // Only show user type step if user is not logged in
        if (!user) {
          return (
            <UserTypeStep 
              formData={formData} 
              onInputChange={handleInputChange}
              onStudentLoginRequired={handleStudentLoginRequired}
            />
          );
        }
        // If user is logged in, this case shouldn't render, but fallback to step 2
        return <SellerTypeStep formData={formData} onInputChange={handleInputChange} />;
      case 2:
        return <SellerTypeStep formData={formData} onInputChange={handleInputChange} />;
      case 3:
        return <PersonalInfoStep formData={formData} onInputChange={handleInputChange} />;
      case 4:
        return <AddressStep formData={formData} onInputChange={handleInputChange} />;
      case 5:
        return (
          <DocumentsStep
            formData={formData}
            fileNames={fileNames}
            isEditMode={isEditMode}
            existingApplication={existingApplication}
            onInputChange={handleInputChange}
            onFileChange={handleFileChange}
          />
        );
      case 6:
        return (
          <BusinessInfoStep
            formData={formData}
            fileNames={fileNames}
            categories={categories}
            onInputChange={handleInputChange}
            onFileChange={handleFileChange}
            onCategoryToggle={handleCategoryToggle}
          />
        );
      case 7:
        return (
          <ReviewStep
            formData={formData}
            fileNames={fileNames}
            categories={categories}
            isEditMode={isEditMode}
          />
        );
      default:
        return null;
    }
  };

  // Main application form
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Hero Section */}
      <HeroSection isEditMode={isEditMode} onCancelEdit={cancelEditMode} />

      {/* Check Application Status Link */}
      {!isEditMode && <CheckStatusBanner />}

      {/* Step Progress */}
      <StepProgress
        currentStep={currentStep}
        sellerType={formData.seller_type}
        onStepClick={setCurrentStep}
      />

      {/* Form Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-2xl shadow-lg p-8"
          >
            {/* Error Display */}
            <ErrorDisplay error={submitError} />

            {/* Step Content */}
            {renderStepContent()}

            {/* Navigation */}
            <FormNavigation
              currentStep={currentStep}
              isEditMode={isEditMode}
              submitting={submitting}
              isStepValid={validateStep(currentStep)}
              onPrevStep={prevStep}
              onNextStep={nextStep}
              onSubmit={handleSubmit}
            />
          </motion.div>
        </AnimatePresence>
      </div>

      <Footer />
    </div>
  );
}

export default SellerApplicationPage;
