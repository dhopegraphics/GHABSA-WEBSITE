import { useEffect, useState } from "react";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import ContactForm from "../Components/Contact/ContactForm";
import Login from "./Login";
import { scrollToTop } from "../utils/scrollToTop";
import ForgotPasswordModal from "./ForgotPasswordModal";
import SignUp from "./SignUp";
import { useNavigate } from "react-router-dom";
import ExecutiveLogin from "./ExecutiveLogin";
import { Helmet } from "react-helmet-async";

export function ContactPage() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(true);
    setIsExecutiveOpen(false);
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(true);
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false);
  };
  useEffect(() => {
    scrollToTop();
  }, []);
  return (
    <>
      <Helmet>
        <title>Contact Us | CSS KNUST</title>
        <meta
          name="description"
          content="Have a question or collaboration in mind? Reach out to the Computer Science Society of KNUST today."
        />
        <meta
          name="keywords"
          content="Contact CSS KNUST, cssknust, thecssknust"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="CSS KNUST - Contact Us" />
        <meta
          property="og:description"
          content="Connect with the tech minds of KNUST!"
        />
        <meta
          property="og:image"
          content="https://thecssknust.com/images/css.png"
        />
        <meta property="og:url" content="https://thecssknust.com/contact-us" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Organization",
            name: "Computer Science Society, KNUST",
            url: "https://thecssknust.com/contact-us",
            logo: "https://thecssknust.com/images/css.png",
            contactPoint: {
              "@type": "ContactPoint",
              telephone: "+233 59 795 9032",
              contactType: "Student Support",
              email: "info@thecssknust.com",
              areaServed: "GH",
              availableLanguage: ["English"],
            },
          })}
        </script>
      </Helmet>

      <div className="relative">
        <Navbar onSignInClick={handleOpenLoginModal} />
        <ContactForm />
        <Footer />

        {isLoginModalOpen && (
          <Login
            onClose={handleCloseModals}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
            action={() => navigate("/dashboard/home")}
            switchToExecutive={handleExecutiveOpen}
          />
        )}

        {isSignupModalOpen && (
          <SignUp
            onClose={handleCloseModals}
            switchToLogin={handleOpenLoginModal}
          />
        )}
        {isOpen && (
          <ForgotPasswordModal onClose={handleOpenLoginModal} isOpen={isOpen} />
        )}
        {isExecutiveOpen && (
          <ExecutiveLogin
            onClose={handleOpenLoginModal}
            switchToSignup={handleOpenSignupModal}
            switchToForgot={handleOpen}
          />
        )}
      </div>
    </>
  );
}
