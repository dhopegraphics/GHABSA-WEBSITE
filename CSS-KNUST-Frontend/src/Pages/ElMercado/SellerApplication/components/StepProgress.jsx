import { Fragment } from "react";
import { Check } from "lucide-react";
import { STEPS } from "../constants";

export function StepProgress({ currentStep, sellerType, onStepClick }) {
  return (
    <div className="max-w-4xl mx-auto px-4 -mt-8">
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between overflow-x-auto">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            const isBusinessStep = step.id === 5;
            const shouldShowStep =
              !isBusinessStep || sellerType === "BUSINESS" || currentStep >= 5;

            if (!shouldShowStep && isBusinessStep) return null;

            return (
              <Fragment key={step.id}>
                <div
                  className={`flex flex-col items-center min-w-[80px] cursor-pointer ${
                    isActive
                      ? "text-purple-600"
                      : isCompleted
                      ? "text-green-600"
                      : "text-gray-400"
                  }`}
                  onClick={() => isCompleted && onStepClick(step.id)}
                >
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${
                      isActive
                        ? "bg-purple-100 ring-4 ring-purple-200"
                        : isCompleted
                        ? "bg-green-100"
                        : "bg-gray-100"
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-6 h-6" />
                    ) : (
                      <Icon className="w-6 h-6" />
                    )}
                  </div>
                  <span className="text-xs font-medium text-center hidden sm:block">
                    {step.title}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 rounded hidden sm:block ${
                      currentStep > step.id ? "bg-green-400" : "bg-gray-200"
                    }`}
                  />
                )}
              </Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default StepProgress;
