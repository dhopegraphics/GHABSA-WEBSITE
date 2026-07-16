import { motion } from "framer-motion";
import { GraduationCap, ArrowRight, ArrowLeft, User, Lock } from "lucide-react";
import Navbar from "../../../../Components/Navbar";
import { Footer } from "../../../../Components/Footer/Footer";
import Login from "../../../Login";
import SignUp from "../../../SignUp";
import { useState } from "react";

export function LoginPromptView({ onBackToUserType, onLoginSuccess }) {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const handleLoginSuccess = (user) => {
    setShowLogin(false);
    if (onLoginSuccess) {
      onLoginSuccess(user);
    }
  };

  const switchToSignup = () => {
    setShowLogin(false);
    setShowSignup(true);
  };

  const switchToLogin = () => {
    setShowSignup(false);
    setShowLogin(true);
  };

  const closeModals = () => {
    setShowLogin(false);
    setShowSignup(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-4xl mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8 text-center"
        >
          {/* Header */}
          <div className="mb-8">
            <div className="bg-blue-100 p-4 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <GraduationCap className="w-10 h-10 text-blue-600" />
            </div>
            
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Student Login Required
            </h1>
            
            <p className="text-lg text-gray-600">
              Since you're a KNUST student, please log in to continue with your seller application. 
              This helps us verify your student status and link your seller profile to your student account.
            </p>
          </div>

          {/* Benefits */}
          <div className="bg-blue-50 rounded-xl p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Why do students need to log in?
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start space-x-3">
                <div className="bg-blue-100 p-2 rounded-full mt-1">
                  <User className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Verified Identity</h4>
                  <p className="text-sm text-gray-600">
                    Links your seller profile to your verified student account
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-blue-100 p-2 rounded-full mt-1">
                  <Lock className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Trust & Safety</h4>
                  <p className="text-sm text-gray-600">
                    Builds trust with other students and community members
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setShowLogin(true)}
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <User className="w-5 h-5" />
                Log In
                <ArrowRight className="w-5 h-5" />
              </button>
              
              <button
                onClick={() => setShowSignup(true)}
                className="w-full py-3 border-2 border-blue-600 text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
              >
                <GraduationCap className="w-5 h-5" />
                Create Account
              </button>
            </div>
            
            <button
              onClick={onBackToUserType}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mx-auto"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to User Type Selection
            </button>
          </div>
        </motion.div>
      </div>

      <Footer />

      {/* Login Modal */}
      {showLogin && (
        <Login 
          onClose={closeModals}
          onLoginSuccess={handleLoginSuccess}
          switchToSignup={switchToSignup}
        />
      )}

      {/* Signup Modal */}
      {showSignup && (
        <SignUp 
          onClose={closeModals}
          switchToLogin={switchToLogin}
        />
      )}
    </div>
  );
}