import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Building2, 
  Calendar, 
  Clock, 
  MapPin, 
  ExternalLink,
  Globe,
  Briefcase,
  GraduationCap
} from 'lucide-react';
import { scrollToTop } from '../utils/scrollToTop';
import Navbar from '../Components/Navbar';
import { Footer } from '../Components/Footer/Footer';
import Login from './Login';
import SignUp from './SignUp';
import ForgotPasswordModal from './ForgotPasswordModal';
import ExecutiveLogin from './ExecutiveLogin';

export function InternshipDetailPage() {
    const location = useLocation();
    const { internship } = location?.state || {};
  const navigate = useNavigate();
  const deadline = new Date(internship?.application_deadline);
  const isDeadlineSoon = new Date()?.getTime() + (7 * 24 * 60 * 60 * 1000) > deadline?.getTime();

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

  useEffect(() => {
    scrollToTop();
  }, []);

  return (
    <div className="relative mt-[50px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors mb-8"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Internships</span>
        </button>

        <div className="">

        <div className="relative md:h-[60vh] max-w-7xl mx-auto md:mb-12 rounded-2xl overflow-hidden">
          <img
            src={internship?.image}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/00 to-transparent" />
        </div>
          
          <div className="py-8 md:px-8 border-b border-gray-200">
            <div className="flex items-center gap-3 mb-4">
            <div className=" p-2 rounded-md bg-blue-50">
              <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">{internship?.campany_name}</h1>
            </div>

            <div className="flex flex-wrap gap-4 mt-6">
              
              <span className={`
                inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium
                ${isDeadlineSoon ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}
              `}>
                <Calendar className="w-4 h-4" />
                Deadline: {deadline?.toDateString()}
              </span>

              <span className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-full text-sm">
                <Clock className="w-4 h-4" />
                Posted: {new Date(internship?.created_at)?.toDateString()}
              </span>
            </div>
          </div>

          <div className="py-8 md:px-8 space-y-8">

            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">About the Role</h2>
              <p className="text-gray-600 leading-relaxed whitespace-pre-wrap">
                {internship?.description}
              </p>
            </div>

            <div className="pt-4">
              <a
                href={internship?.registration_link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 w-full justify-end text-blue-600 text-base hover:underline font-medium"
              >
                Apply for this Position
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>
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
  );
}

function DetailCard({ icon: Icon, title, value }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center gap-3 mb-2">
        <Icon className="w-5 h-5 text-blue-600" />
        <span className="text-sm font-medium text-gray-600">{title}</span>
      </div>
      <p className="text-gray-900 font-medium">{value}</p>
    </div>
  );
}