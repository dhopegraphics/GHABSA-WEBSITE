import { ArrowLeft, ArrowRight, Check, Loader2, Save } from "lucide-react";

export function FormNavigation({
  currentStep,
  isEditMode,
  submitting,
  isStepValid,
  onPrevStep,
  onNextStep,
  onSubmit,
}) {
  const isLastStep = currentStep === 7;

  return (
    <div className="flex justify-between mt-8 pt-6 border-t">
      <button
        onClick={onPrevStep}
        disabled={currentStep === 1}
        className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
          currentStep === 1
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        <ArrowLeft className="w-5 h-5" />
        Previous
      </button>

      {isLastStep ? (
        <button
          onClick={onSubmit}
          disabled={submitting}
          className={`flex items-center gap-2 px-8 py-3 ${
            isEditMode ? "bg-orange-600 hover:bg-orange-700" : "bg-blue-600 hover:bg-blue-700"
          } text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {submitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {isEditMode ? "Updating..." : "Submitting..."}
            </>
          ) : (
            <>
              {isEditMode ? (
                <>
                  <Save className="w-5 h-5" />
                  Update Application
                </>
              ) : (
                <>
                  Submit Application
                  <Check className="w-5 h-5" />
                </>
              )}
            </>
          )}
        </button>
      ) : (
        <button
          onClick={onNextStep}
          disabled={!isStepValid}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
            isStepValid
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
        >
          Next Step
          <ArrowRight className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}

export default FormNavigation;
