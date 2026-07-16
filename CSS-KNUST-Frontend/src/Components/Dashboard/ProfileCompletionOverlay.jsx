import { motion, AnimatePresence } from "framer-motion";
import { useEffect } from "react";
import {
  X,
  UserCircle,
  Mail,
  IdCard,
  Users,
  Shield,
  CheckCircle,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  Target,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const fieldInfo = {
  student_id: {
    icon: IdCard,
    title: "Student ID",
    importance: "Essential for Academic Records",
    description:
      "Your Student ID links you to official university records, enables exam registration, and ensures accurate grade tracking.",
    benefits: [
      "Access to personalized exam schedules",
      "Accurate academic transcript generation",
      "Official CSS membership verification",
    ],
    color: "blue",
  },
  index_number: {
    icon: Shield,
    title: "Index Number",
    importance: "Critical for Examinations",
    description:
      "Your Index Number is required for all official examinations and academic assessments at KNUST.",
    benefits: [
      "Automatic exam timetable synchronization",
      "Real-time grade notifications",
      "Seamless exam hall location mapping",
    ],
    color: "purple",
  },
  personal_email: {
    icon: Mail,
    title: "Personal Email",
    importance: "Stay Connected Beyond Campus",
    description:
      "Your personal email ensures you receive important updates even after graduation and serves as a backup communication channel.",
    benefits: [
      "Alumni network access",
      "Important CSS announcements",
      "Account recovery options",
    ],
    color: "green",
  },
  student_email: {
    icon: Mail,
    title: "Student Email",
    importance: "Official KNUST Communication",
    description:
      "Your KNUST student email is the primary channel for official academic communications and university announcements.",
    benefits: [
      "Direct access to lecturer communications",
      "Academic policy updates",
      "Campus-wide event notifications",
    ],
    color: "orange",
  },
  gender: {
    icon: Users,
    title: "Gender",
    importance: "Personalized Experience",
    description:
      "Help us provide a more personalized and inclusive experience tailored to your preferences.",
    benefits: [
      "Relevant event recommendations",
      "Appropriate committee placements",
      "Inclusive community building",
    ],
    color: "pink",
  },
  program: {
    icon: Target,
    title: "Program (CS/IT)",
    importance: "Tailored Academic Content",
    description:
      "Your program selection ensures you receive course materials, resources, and opportunities specific to your field of study.",
    benefits: [
      "Program-specific course resources",
      "Relevant job and internship opportunities",
      "Specialized academic guidance",
    ],
    color: "indigo",
  },
};

const colorClasses = {
  blue: "from-blue-500 to-blue-600",
  purple: "from-purple-500 to-purple-600",
  green: "from-green-500 to-green-600",
  orange: "from-orange-500 to-orange-600",
  pink: "from-pink-500 to-pink-600",
  indigo: "from-indigo-500 to-indigo-600",
};

export function ProfileCompletionOverlay({ incompleteFields, onClose }) {
  const navigate = useNavigate();

  // Prevent scrolling when overlay is open
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, []);

  const getFieldKey = (fieldLabel) => {
    const mapping = {
      "Student ID": "student_id",
      "Index Number": "index_number",
      "Personal Email": "personal_email",
      "Student Email": "student_email",
      Gender: "gender",
      Program: "program",
    };
    return mapping[fieldLabel];
  };

  const handleUpdateProfile = () => {
    navigate("/dashboard/account");
    onClose();
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4 overflow-y-auto"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto my-8"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-2xl">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                    Complete Your Profile
                    <Sparkles className="w-6 h-6 text-yellow-300" />
                  </h2>
                  <p className="text-blue-100 text-sm">
                    {incompleteFields.length} field
                    {incompleteFields.length > 1 ? "s" : ""} need your attention
                    to unlock the full CSS experience
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white hover:bg-white/20 p-2 rounded-lg transition-all"
                aria-label="Close"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Why This Matters Section */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    Why Your Information Matters
                  </h3>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    The Computer Science Society uses your information to create
                    a personalized experience tailored just for you. From
                    relevant academic resources to timely exam notifications,
                    every piece of data helps us serve you better. Your privacy
                    is our priority - this information is used solely to enhance
                    your CSS experience.
                  </p>
                </div>
              </div>
            </div>

            {/* Missing Fields */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <UserCircle className="w-5 h-5 text-indigo-600" />
                Fields Requiring Your Attention
              </h3>
              <div className="space-y-4">
                {incompleteFields.map((fieldLabel, index) => {
                  const fieldKey = getFieldKey(fieldLabel);
                  const field = fieldInfo[fieldKey];
                  if (!field) return null;

                  const Icon = field.icon;
                  const gradientClass = colorClasses[field.color];

                  return (
                    <motion.div
                      key={fieldLabel}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-white border-2 border-gray-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-md transition-all"
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={`bg-gradient-to-br ${gradientClass} p-3 rounded-lg text-white flex-shrink-0`}
                        >
                          <Icon className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-bold text-gray-900">
                              {field.title}
                            </h4>
                            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                              Required
                            </span>
                          </div>
                          <p className="text-sm text-indigo-600 font-medium mb-2">
                            {field.importance}
                          </p>
                          <p className="text-sm text-gray-600 mb-3">
                            {field.description}
                          </p>
                          <div className="space-y-1.5">
                            <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                              Benefits for you:
                            </p>
                            {field.benefits.map((benefit, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 text-sm"
                              >
                                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                                <span className="text-gray-700">{benefit}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <button
                onClick={handleUpdateProfile}
                className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2"
              >
                <UserCircle className="w-5 h-5" />
                Update Profile Now
              </button>
              <button
                onClick={onClose}
                className="sm:w-auto px-6 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all"
              >
                Remind Me Later
              </button>
            </div>

            {/* Footer Note */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-xs text-gray-600">
                🔒 Your information is secured and used only to improve your CSS
                experience. We respect your privacy.
              </p>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
