import React, { useEffect, useState } from 'react';
import { FAQSection } from '../Components/FAQ/FAQSection';
import { faqData } from '../Components/FAQ/faqData';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../Components/Navbar';
import Login from './Login';
import SignUp from './SignUp';
import ForgotPasswordModal from './ForgotPasswordModal';
import ExecutiveLogin from './ExecutiveLogin';
import { Footer } from '../Components/Footer/Footer';
import { scrollToTop } from '../utils/scrollToTop';
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from '../utils/framerVariants';
import { Helmet } from 'react-helmet-async';

export function FAQPage() {

  const navigate = useNavigate();
    
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [isExecutiveOpen, setIsExecutiveOpen] = useState(false);

  const handleOpenLoginModal = () => {
    setIsLoginModalOpen(true);
    setIsSignupModalOpen(false);
    setIsOpen(false);
    setIsExecutiveOpen(false)
  };

  const handleOpenSignupModal = () => {
    setIsSignupModalOpen(true);
    setIsLoginModalOpen(false); 
    setIsOpen(false); 
    setIsExecutiveOpen(false)
  };

  const handleOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false); 
    setIsOpen(true); 
    setIsExecutiveOpen(false)
  };
  const handleExecutiveOpen = () => {
    setIsSignupModalOpen(false);
    setIsLoginModalOpen(false); 
    setIsOpen(false); 
    setIsExecutiveOpen(true)
  };

  const handleCloseModals = () => {
    setIsLoginModalOpen(false);
    setIsSignupModalOpen(false);
    setIsOpen(false)
    setIsExecutiveOpen(false)
  };

  useEffect(() =>{
    scrollToTop()
  }, [])

  return (
    <>
    <Helmet>
  <title>FAQs | BIO-CHEM KNUST</title>
  <meta name="description" content="Got questions? Find quick answers about the Biochemistry Society, KNUST, memberships, events and more." />
  <meta name="keywords" content="FAQ BIO-CHEM KNUST, BIO-CHEM KNUST Questions, BIO-CHEM KNUST Help, biochem knust, biochemknust" />
  <meta name="robots" content="index, nofollow" />
  <meta property="og:title" content="BIO-CHEM KNUST - Frequently Asked Questions" />
  <meta property="og:description" content="Everything you need to know about BIO-CHEM KNUST!" />
  <meta property="og:image" content="https://biochemknust.com/images/logo.png" />
  <meta property="og:url" content="https://biochemknust.com/faq" />
</Helmet>

    <div className='relative mt-[70px] bg-gray-50'>
        <Navbar onSignInClick={handleOpenLoginModal} />
    <div className="min-h-screen bg-gray-50 py-16 px-4">
      <div className="max-w-4xl mx-auto">
        
      <motion.h1 
                variants={fadeIn("up", 0.5, 0)}
                initial="offscreen"
                whileInView="onscreen"
                viewport={{ once: true, amount: 0 }} className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center">
        Frequently Asked <span className="relative text-blue-600"> Questions
        <motion.div
            variants={underlineAnimation(0.7)}
            initial="offscreen"
            whileInView="onscreen"
            exit="reverse"
            className="absolute left-0 bottom-0 h-1 bg-blue-600"
            style={{ width: "0%", height: "3px" }}
          />
          </span>
      </motion.h1>
        <div className="text-center mb-12">
          <p className=" text-gray-600 ">
            Find answers to common questions about our platform, resources, and services.
          </p>
        </div>

        <div className="space-y-8">
          {faqData.map((section) => (
            <FAQSection key={section.category} {...section} />
          ))}
        </div>

        <div className="mt-16 text-center  p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Still have questions?</h2>
          <p className="text-gray-600 mb-6">
            Can't find the answer you're looking for? Please reach out to our support team.
          </p>
          <Link
            to={'/contact-us'}
            className="inline-flex hover:underline items-center justify-center text-blue-600 hover:text-blue-700 transition-colors"
          >
            Contact Support
          </Link>
        </div>
      </div>
    </div>

    <Footer />
{isLoginModalOpen && (
  <Login
    onClose={handleCloseModals}
    switchToSignup={handleOpenSignupModal}  
    switchToForgot={handleOpen}
    action={()=>navigate('/dashboard/home')}
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
  <ForgotPasswordModal
    onClose={handleOpenLoginModal}
    isOpen={isOpen} 
  />
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
