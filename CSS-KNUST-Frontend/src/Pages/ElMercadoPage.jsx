import { useState, useEffect, useContext } from "react";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { Footer } from "../Components/Footer/Footer";
import Navbar from "../Components/Navbar";
import { scrollToTop } from "../utils/scrollToTop";
import Login from "./Login";
import SignUp from "./SignUp";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { useNavigate } from "react-router-dom";
import ExecutiveLogin from "./ExecutiveLogin";
import { Helmet } from "react-helmet-async";
import { ShoppingBag, Store, TrendingUp, Users } from "lucide-react";
import { UserContext } from "../Context/UserContext";

export function ElMercadoPage() {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
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
        <title>El Mercado | CSS KNUST</title>
        <meta
          name="description"
          content="El Mercado - Your campus marketplace for buying and selling products within the KNUST community."
        />
        <meta
          name="keywords"
          content="El Mercado, CSS KNUST marketplace, campus marketplace, KNUST buy and sell"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="CSS KNUST - El Mercado" />
        <meta
          property="og:description"
          content="Buy and sell products within the KNUST community on El Mercado."
        />
        <meta
          property="og:image"
          content="https://thecssknust.com/images/css.png"
        />
        <meta property="og:url" content="https://thecssknust.com/el-mercado" />
      </Helmet>

      <div className="relative mt-[70px]">
        <Navbar onSignInClick={handleOpenLoginModal} />
        
        {/* Hero Section */}
        <div className=" py-20">
          <div className="max-w-6xl mx-auto px-4">
            <motion.div
              variants={fadeIn("up", 0.3, 0)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="text-center"
            >
              <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
                Welcome to{" "}
                <span className="relative text-blue-600">
                  El Mercado
                  <motion.div
                    variants={underlineAnimation(0.7)}
                    initial="offscreen"
                    whileInView="onscreen"
                    exit="reverse"
                    className="absolute left-0 bottom-0 h-1 bg-blue-600"
                    style={{ width: "0%", height: "3px" }}
                  />
                </span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Your campus marketplace for buying and selling products within the KNUST community. 
                Connect with fellow students and make campus life easier.
              </p>
            </motion.div>
          </div>
        </div>

        {/* Features Section */}
        <div className="max-w-6xl mx-auto px-4 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            <motion.div
              variants={fadeIn("up", 0.3, 0.1)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="bg-blue-100 w-14 h-14 rounded-full flex items-center justify-center mb-4">
                <ShoppingBag className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Buy Products
              </h3>
              <p className="text-gray-600">
                Browse and purchase products from verified sellers within the KNUST community.
              </p>
            </motion.div>

            <motion.div
              variants={fadeIn("up", 0.3, 0.2)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="bg-indigo-100 w-14 h-14 rounded-full flex items-center justify-center mb-4">
                <Store className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Become a Seller
              </h3>
              <p className="text-gray-600">
                Start your own shop and sell products to thousands of students on campus.
              </p>
            </motion.div>

            <motion.div
              variants={fadeIn("up", 0.3, 0.3)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="bg-blue-100 w-14 h-14 rounded-full flex items-center justify-center mb-4">
                <TrendingUp className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Track Orders
              </h3>
              <p className="text-gray-600">
                Monitor your purchases and sales with our easy-to-use tracking system.
              </p>
            </motion.div>

            <motion.div
              variants={fadeIn("up", 0.3, 0.4)}
              initial="offscreen"
              whileInView="onscreen"
              viewport={{ once: true, amount: 0 }}
              className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="bg-indigo-100 w-14 h-14 rounded-full flex items-center justify-center mb-4">
                <Users className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Community Trust
              </h3>
              <p className="text-gray-600">
                Buy and sell with confidence in a verified community of KNUST students.
              </p>
            </motion.div>
          </div>

          {/* Call to Action Buttons */}
          <motion.div
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="flex flex-col md:flex-row gap-4 justify-center items-center flex-wrap"
          >
            <button
              onClick={() => navigate("/el-mercado/browse")}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
            >
              Browse Products
            </button>
            {user && (
              <button
                onClick={() => navigate("/el-mercado/following")}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold py-4 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105 flex items-center gap-2"
              >
                <Users className="w-5 h-5" />
                Following
              </button>
            )}
            <button
              onClick={() => navigate("/el-mercado/become-a-seller")}
              className="bg-white hover:bg-gray-50 text-blue-600 border-2 border-blue-600 font-semibold py-4 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
            >
              Become a Seller
            </button>
          </motion.div>

          {/* Info Section */}
          <motion.div
            variants={fadeIn("up", 0.5, 0.2)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="mt-16 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8"
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-4 text-center">
              How It Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
              <div className="text-center">
                <div className="bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  1
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Sign Up
                </h3>
                <p className="text-gray-600">
                  Create your account and verify your KNUST student status.
                </p>
              </div>
              <div className="text-center">
                <div className="bg-indigo-600 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  2
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Browse or Sell
                </h3>
                <p className="text-gray-600">
                  Explore products or list your own items for sale.
                </p>
              </div>
              <div className="text-center">
                <div className="bg-blue-700 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  3
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Connect & Trade
                </h3>
                <p className="text-gray-600">
                  Complete transactions safely within the campus community.
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        <Footer />

        {/* Modals */}
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
