import { createContext, useContext, useState, useCallback } from 'react';
import LoginModal from '../Pages/Login';
import SignUpModal from '../Pages/SignUp';
import ForgotPasswordModal from '../Pages/ForgotPasswordModal';
import ExecutiveLoginModal from '../Pages/ExecutiveLogin';

// Create the context
const AuthModalsContext = createContext(null);

// Custom hook to use the auth modals
export const useAuthModals = () => {
  const context = useContext(AuthModalsContext);
  if (!context) {
    throw new Error('useAuthModals must be used within an AuthModalsProvider');
  }
  return context;
};

// Provider component
export const AuthModalsProvider = ({ children }) => {
  // Modal states
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignUpModal, setShowSignUpModal] = useState(false);
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [showExecutiveLoginModal, setShowExecutiveLoginModal] = useState(false);

  // Open modals
  const openLoginModal = useCallback(() => {
    setShowSignUpModal(false);
    setShowForgotPasswordModal(false);
    setShowExecutiveLoginModal(false);
    setShowLoginModal(true);
  }, []);

  const openSignUpModal = useCallback(() => {
    setShowLoginModal(false);
    setShowForgotPasswordModal(false);
    setShowExecutiveLoginModal(false);
    setShowSignUpModal(true);
  }, []);

  const openForgotPasswordModal = useCallback(() => {
    setShowLoginModal(false);
    setShowSignUpModal(false);
    setShowExecutiveLoginModal(false);
    setShowForgotPasswordModal(true);
  }, []);

  const openExecutiveLoginModal = useCallback(() => {
    setShowLoginModal(false);
    setShowSignUpModal(false);
    setShowForgotPasswordModal(false);
    setShowExecutiveLoginModal(true);
  }, []);

  // Close all modals
  const closeAllModals = useCallback(() => {
    setShowLoginModal(false);
    setShowSignUpModal(false);
    setShowForgotPasswordModal(false);
    setShowExecutiveLoginModal(false);
  }, []);

  // Context value
  const value = {
    // States
    showLoginModal,
    showSignUpModal,
    showForgotPasswordModal,
    showExecutiveLoginModal,
    // Open functions
    openLoginModal,
    openSignUpModal,
    openForgotPasswordModal,
    openExecutiveLoginModal,
    // Close function
    closeAllModals,
  };

  return (
    <AuthModalsContext.Provider value={value}>
      {children}
      
      {/* Global Auth Modals - Only render when open */}
      {showLoginModal && (
        <LoginModal
          onClose={closeAllModals}
          switchToSignup={openSignUpModal}
          switchToForgot={openForgotPasswordModal}
          switchToExecutive={openExecutiveLoginModal}
        />
      )}

      {showSignUpModal && (
        <SignUpModal
          onClose={closeAllModals}
          switchToLogin={openLoginModal}
        />
      )}

      {showForgotPasswordModal && (
        <ForgotPasswordModal
          isOpen={true}
          onClose={closeAllModals}
          switchToLogin={openLoginModal}
        />
      )}

      {showExecutiveLoginModal && (
        <ExecutiveLoginModal
          onClose={closeAllModals}
          switchToLogin={openLoginModal}
        />
      )}
    </AuthModalsContext.Provider>
  );
};

export default AuthModalsContext;
