import  { useEffect, useState, useContext } from "react";
import { ArrowDown, PackageCheck, ShieldCheck, ShoppingBag } from "lucide-react";
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
    <div className="relative bg-[#f5f7fa] pt-[60px] sm:pt-[65px] md:pt-[70px] lg:pt-[75px]">
      <Navbar onSignInClick={handleOpenLoginModal} />
      <header className="relative overflow-hidden bg-[#07162f] px-5 py-20 text-white sm:px-8 sm:py-24 lg:px-10 lg:py-28">
        <div className="absolute -right-24 -top-44 h-[430px] w-[430px] rounded-full border-[70px] border-blue-400/10" />
        <div className="absolute bottom-0 right-[20%] h-52 w-52 rounded-full bg-blue-500/20 blur-[90px]" />
        <div className="relative mx-auto max-w-7xl lg:grid lg:grid-cols-[1fr_0.55fr] lg:items-end">
          <div>
            <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-[-0.05em] sm:text-6xl lg:text-7xl">Wear the community.<br /><span className="text-blue-400">Carry the story.</span></h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">Thoughtfully selected apparel and essentials created for Biochemistry students, alumni and supporters.</p>
          </div>
          <a href="#collection" className="mt-9 inline-flex items-center gap-3 rounded-full bg-lime-300 px-6 py-4 font-semibold text-[#07162f] hover:bg-lime-200 lg:justify-self-end">Shop the collection <ArrowDown className="h-5 w-5" /></a>
        </div>
      </header>

      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl grid-cols-1 divide-y divide-slate-200 px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 sm:px-8 lg:px-10">
          {[{ icon: ShoppingBag, text: "Official society products" }, { icon: ShieldCheck, text: "Secure Paystack checkout" }, { icon: PackageCheck, text: "Clear stock availability" }].map(({ icon: Icon, text }) => (
            <div key={text} className="flex items-center justify-center gap-3 py-5 text-sm font-medium text-slate-600"><Icon className="h-5 w-5 text-blue-600" />{text}</div>
          ))}
        </div>
      </div>

      <section id="collection" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-24 lg:px-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <h2 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">Made to belong.</h2>
          <p className="max-w-md text-sm leading-6 text-slate-600">Choose your product, select available variants and check out securely.</p>
        </div>

        <ul className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {merchandise?.length == 0
            ? Array.from({ length: 4 }).map((_, index) => (
                <MerchandiseCardSkeleton key={index} />
              ))
            : merchandise?.map((item) => (
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
      </section>
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
