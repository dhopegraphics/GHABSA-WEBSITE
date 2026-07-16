import { useContext, useEffect, useState } from "react";
import { FaBars, FaTimes, FaChevronDown } from "react-icons/fa";
import logo from "../assets/logo.png";
import { Link } from "react-router-dom";
import { UserContext } from "../Context/UserContext";
import { useAuthModals } from "../Context/AuthModalsContext";
import { BRAND } from "../config/brand";

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isFloating, setIsFloating] = useState(false);
  const { openLoginModal } = useAuthModals();

  useEffect(() => {
    const handleScroll = () => {
      setIsFloating((currentlyFloating) => {
        // Different thresholds keep the navbar from flickering at the boundary.
        if (!currentlyFloating && window.scrollY > 48) return true;
        if (currentlyFloating && window.scrollY < 16) return false;
        return currentlyFloating;
      });
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };
  
  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen);
  };
  
  const { user } = useContext(UserContext);

  // Priority navigation items (always visible)
  const priorityNavItems = [
    { to: "/events", label: "Events" },
    { href: "/#resources", label: "Resources" },
    { to: "/purchase-merchandise", label: "Merchandise" },
  ];

  // Secondary navigation items (in dropdown on smaller screens)
  const secondaryNavItems = [
    { to: "/current-administration", label: "Current Admins" },
    { to: "/contact-us", label: "Contact us" },
  ];

  return (
    <nav
      className={`fixed left-1/2 z-50 flex h-[60px] -translate-x-1/2 flex-row items-center justify-between bg-[#ffffffd9] px-3 backdrop-blur-xl transition-[top,width,border-radius,box-shadow] duration-500 ease-out sm:h-[65px] sm:px-4 md:h-[70px] md:px-6 lg:h-[75px] lg:px-8 xl:px-10 2xl:px-12 ${
        isFloating
          ? "top-3 w-[calc(100%-1.5rem)] rounded-full shadow-[0_12px_35px_rgba(15,23,42,0.18)] sm:top-4 sm:w-[calc(100%-2rem)] lg:w-[min(1180px,calc(100%-3rem))]"
          : "top-0 w-full rounded-none shadow"
      }`}
      aria-label="Main navigation"
    >
      <Link to={"/"} className="w-[55px] sm:w-[65px] md:w-[75px] lg:w-[80px] flex-shrink-0">
        <img src={logo} className="object-contain w-full h-auto" alt={`${BRAND.shortName} Logo`} />
      </Link>

      <div className="hidden lg:flex xl:space-x-6 2xl:space-x-8 space-x-4 items-center flex-wrap justify-center">
        {/* Priority items - always visible */}
        {priorityNavItems.map((item, index) => (
          item.to ? (
            <Link
              key={index}
              to={item.to}
              className="text-gray-700 hover:text-blue-700 font-medium text-sm xl:text-base transition-colors duration-200 whitespace-nowrap"
            >
              {item.label}
            </Link>
          ) : (
            <a
              key={index}
              href={item.href}
              className="text-gray-700 hover:text-blue-700 font-medium text-sm xl:text-base transition-colors duration-200 whitespace-nowrap"
            >
              {item.label}
            </a>
          )
        ))}
        
        {/* View Others dropdown for secondary items */}
        <div className="relative">
          <button
            onClick={toggleDropdown}
            className="text-gray-700 hover:text-blue-700 font-medium text-sm xl:text-base transition-colors duration-200 whitespace-nowrap flex items-center gap-1"
          >
            View Others
            <FaChevronDown className={`text-xs transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>
          
          {dropdownOpen && (
            <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-2 z-50">
              {secondaryNavItems.map((item, index) => (
                <Link
                  key={index}
                  to={item.to}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-700 transition-colors duration-200"
                  onClick={() => setDropdownOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="hidden lg:flex items-center flex-shrink-0">
        {!user ? (
          <button
            onClick={openLoginModal}
            className="px-3 py-1.5 sm:px-4 sm:py-2 lg:px-5 lg:py-2 xl:px-6 xl:py-2.5 rounded bg-blue-700 font-bold hover:bg-blue-800 text-white text-sm xl:text-base transition-all duration-200 whitespace-nowrap"
          >
            Sign in
          </button>
        ) : (
          <Link
            to={"/dashboard/home"}
            className="px-3 py-1.5 sm:px-4 sm:py-2 lg:px-5 lg:py-2 xl:px-6 xl:py-2.5 rounded bg-blue-700 font-bold hover:bg-blue-800 text-white text-sm xl:text-base transition-all duration-200 whitespace-nowrap"
          >
            Dashboard
          </Link>
        )}
      </div>

      <div className="lg:hidden flex-shrink-0">
        <button onClick={toggleMenu} className="text-gray-700 text-xl sm:text-2xl hover:text-blue-700 transition-colors duration-200 p-1">
          {menuOpen ? <FaTimes /> : <FaBars />}
        </button>
      </div>

      {menuOpen && (
        <div className="absolute top-[60px] sm:top-[65px] md:top-[70px] lg:top-[75px] left-0 w-full bg-white shadow-lg z-30 flex flex-col items-center space-y-2 sm:space-y-3 md:space-y-4 py-4 sm:py-5 md:py-6 lg:hidden max-h-[calc(100vh-60px)] sm:max-h-[calc(100vh-65px)] md:max-h-[calc(100vh-70px)] overflow-y-auto">
          {/* Priority items */}
          {priorityNavItems.map((item, index) => (
            item.to ? (
              <Link
                key={index}
                to={item.to}
                className="text-gray-700 hover:text-blue-700 font-medium text-sm sm:text-base md:text-lg transition-colors duration-200 py-1 px-4"
                onClick={toggleMenu}
              >
                {item.label}
              </Link>
            ) : (
              <a
                key={index}
                href={item.href}
                className="text-gray-700 hover:text-blue-700 font-medium text-sm sm:text-base md:text-lg transition-colors duration-200 py-1 px-4"
                onClick={toggleMenu}
              >
                {item.label}
              </a>
            )
          ))}
          
          {/* Secondary items */}
          {secondaryNavItems.map((item, index) => (
            <Link
              key={index}
              to={item.to}
              className="text-gray-700 hover:text-blue-700 font-medium text-sm sm:text-base md:text-lg transition-colors duration-200 py-1 px-4"
              onClick={toggleMenu}
            >
              {item.label}
            </Link>
          ))}
          
          <Link
            to={"/internships"}
            className="text-gray-700 hover:text-blue-700 font-medium text-sm sm:text-base md:text-lg transition-colors duration-200 py-1 px-4"
            onClick={toggleMenu}
          >
            Internships
          </Link>
          {!user ? (
            <button
              onClick={() => {
                toggleMenu();
                openLoginModal();
              }}
              className="px-6 py-2 sm:px-8 sm:py-2.5 md:px-10 md:py-3 rounded bg-blue-700 font-bold hover:bg-blue-800 text-white text-sm sm:text-base md:text-lg transition-all duration-200 mt-2 sm:mt-3"
            >
              Sign in
            </button>
          ) : (
            <Link
              to={"/dashboard/home"}
              className="px-6 py-2 sm:px-8 sm:py-2.5 md:px-10 md:py-3 rounded bg-blue-700 font-bold hover:bg-blue-800 text-white text-sm sm:text-base md:text-lg transition-all duration-200 mt-2 sm:mt-3"
            >
              Dashboard
            </Link>
          )}
        </div>
      )}
    </nav>
  );
}

export default Navbar;
