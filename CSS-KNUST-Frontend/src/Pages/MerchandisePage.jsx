import  { useEffect, useState, useContext } from "react";
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
import { getData } from "../utils/apiHandler";
import { useMerchandise } from "../Context/MerchandiseContext";
import { MerchandiseCard } from "../Components/Merchandise/MerchandiseCard";
import { MerchandiseCardSkeleton } from "../Components/Merchandise/MerchandiseCardSkeleton";
import { UserContext } from "../Context/UserContext";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";

export function MerchandisePage() {
  const { merchandise, setMerchandise } = useMerchandise();
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const fetchMerchandise = async () => {
    try {
      // Use authenticated request if user is logged in, otherwise use public endpoint
      if (user?.access) {
        const res = await axiosInstance.get("/products/products/");
        setMerchandise(res.data);
      } else {
        const { response, error } = await getData("/products/products/");
        if (error) {
          console.error("Error fetching Merchandise:", error);
        }
        if (response) {
          setMerchandise(response);
        }
      }
    } catch (error) {
      console.error("Error fetching Merchandise:", error);
    }
  };

  useEffect(() => {
    scrollToTop();
    fetchMerchandise();
  }, [user]); // Re-fetch when user login state changes
  const navigate = useNavigate();

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
  return (
    <div className="relative mt-[70px] bg-gray-50">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <div className="max-w-7xl mx-auto px-4 py-16">
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
        >
          Our{" "}
          <span className="relative text-blue-600">
            {" "}
            Merchandise
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
        <p className="text-center text-gray-600 mb-12">
          Discover unique apparel and accessories that let you express yourself.
          Crafted with care, designed for you—our merchandise celebrates your
          individuality and style.
        </p>

        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {merchandise?.length == 0
            ? Array.from({ length: 4 }).map((_, index) => (
                <MerchandiseCardSkeleton key={index} />
              ))
            : merchandise?.map((item, index) => (
                <li key={item?.product_id}>
                  <MerchandiseCard
                    product_image={item?.product_image}
                    product_id={item?.product_id}
                    price={item?.price}
                    product_name={item?.product_name}
                    type_of_product={item?.type_of_product}
                    stock_quantity={item?.stock_quantity}
                    status={item?.status}
                    availability_message={item?.availability_message}
                    is_available_for_purchase={item?.is_available_for_purchase}
                    is_low_stock={item?.is_low_stock}
                    has_colors={item?.has_colors}
                    has_sizes={item?.has_sizes}
                    available_colors={item?.available_colors}
                    available_sizes={item?.available_sizes}
                    // Dynamic variant stock mapping - enables filtering sizes by color
                    variant_stock_map={item?.variant_stock_map}
                    // Eligibility fields
                    eligibility_info={item?.eligibility_info}
                    target_audience={item?.target_audience}
                    // Discount fields (price is already discounted)
                    original_price={item?.original_price}
                    has_discount={item?.has_discount}
                    discount_info={item?.discount_info}
                    onLoginRequired={handleOpenLoginModal}
                  />
                </li>
              ))}
        </ul>
      </div>
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
  );
}
