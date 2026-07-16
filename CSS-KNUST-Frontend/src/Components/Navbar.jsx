import { useContext, useEffect, useState } from "react";
import { FaBars, FaTimes, FaChevronDown } from "react-icons/fa";
import { ArrowUpRight, LayoutDashboard, LogIn } from "lucide-react";
import logo from "../assets/logo.png";
import { Link, NavLink, useLocation } from "react-router-dom";
import { UserContext } from "../Context/UserContext";
import { useAuthModals } from "../Context/AuthModalsContext";
import { BRAND } from "../config/brand";

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isFloating, setIsFloating] = useState(false);
  const { openLoginModal } = useAuthModals();
  const location = useLocation();

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

      <div className="hidden items-center rounded-full border border-slate-200/80 bg-slate-100/70 p-1 lg:flex">
        {/* Priority items - always visible */}
        {priorityNavItems.map((item, index) => (
          item.to ? (
            <NavLink
              key={index}
              to={item.to}
              className={({ isActive }) => `relative whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 ${
                isActive
                  ? "bg-white text-blue-700 shadow-[0_4px_14px_rgba(15,23,42,0.09)]"
                  : "text-slate-600 hover:bg-white/70 hover:text-slate-950"
              }`}
            >
              {item.label}
            </NavLink>
          ) : (
            <a
              key={index}
              href={item.href}
              className={`relative whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 ${
                location.pathname === "/" && location.hash === "#resources"
                  ? "bg-white text-blue-700 shadow-[0_4px_14px_rgba(15,23,42,0.09)]"
                  : "text-slate-600 hover:bg-white/70 hover:text-slate-950"
              }`}
            >
              {item.label}
            </a>
          )
        ))}
        
        {/* View Others dropdown for secondary items */}
        <div className="relative">
          <button
            onClick={toggleDropdown}
            className={`flex items-center gap-1.5 whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 ${
              secondaryNavItems.some((item) => item.to === location.pathname)
                ? "bg-white text-blue-700 shadow-[0_4px_14px_rgba(15,23,42,0.09)]"
                : "text-slate-600 hover:bg-white/70 hover:text-slate-950"
            }`}
            aria-expanded={dropdownOpen}
            aria-haspopup="menu"
          >
            More
            <FaChevronDown className={`text-xs transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>
          
          {dropdownOpen && (
            <div className="absolute left-1/2 top-full z-50 mt-3 w-60 -translate-x-1/2 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_18px_50px_rgba(15,23,42,0.16)]" role="menu">
              {secondaryNavItems.map((item, index) => (
                <Link
                  key={index}
                  to={item.to}
                  className="group flex items-center justify-between rounded-xl px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700"
                  onClick={() => setDropdownOpen(false)}
                >
                  {item.label}<ArrowUpRight className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
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
            className="group inline-flex items-center gap-2 whitespace-nowrap rounded-full bg-[#07162f] px-5 py-3 text-sm font-semibold text-white shadow-[0_8px_22px_rgba(7,22,47,0.2)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-[0_12px_28px_rgba(37,99,235,0.25)]"
          >
            <LogIn className="h-4 w-4" /> Sign in
          </button>
        ) : (
          <Link
            to={"/dashboard/home"}
            className="group inline-flex items-center gap-2 whitespace-nowrap rounded-full bg-[#07162f] px-5 py-3 text-sm font-semibold text-white shadow-[0_8px_22px_rgba(7,22,47,0.2)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-blue-700"
          >
            <LayoutDashboard className="h-4 w-4" /> Dashboard
          </Link>
        )}
      </div>

      <div className="lg:hidden flex-shrink-0">
        <button onClick={toggleMenu} className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-lg text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700 sm:text-xl" aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={menuOpen}>
          {menuOpen ? <FaTimes /> : <FaBars />}
        </button>
      </div>

      {menuOpen && (
        <div className={`absolute left-0 top-[calc(100%+0.75rem)] z-30 flex max-h-[calc(100vh-90px)] w-full flex-col overflow-y-auto rounded-[24px] border border-slate-200 bg-white p-3 shadow-[0_20px_55px_rgba(15,23,42,0.18)] lg:hidden ${isFloating ? "" : "rounded-t-none"}`}>
          {/* Priority items */}
          {priorityNavItems.map((item, index) => (
            item.to ? (
              <Link
                key={index}
                to={item.to}
                className="rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700 sm:text-base"
                onClick={toggleMenu}
              >
                {item.label}
              </Link>
            ) : (
              <a
                key={index}
                href={item.href}
                className="rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700 sm:text-base"
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
              className="rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700 sm:text-base"
              onClick={toggleMenu}
            >
              {item.label}
            </Link>
          ))}
          
          <Link
            to={"/internships"}
            className="rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700 sm:text-base"
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
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-[#07162f] px-6 py-3.5 text-sm font-semibold text-white hover:bg-blue-700 sm:text-base"
            >
              <LogIn className="h-4 w-4" /> Sign in
            </button>
          ) : (
            <Link
              to={"/dashboard/home"}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-[#07162f] px-6 py-3.5 text-sm font-semibold text-white hover:bg-blue-700 sm:text-base"
            >
              <LayoutDashboard className="h-4 w-4" /> Dashboard
            </Link>
          )}
        </div>
      )}
    </nav>
  );
}

export default Navbar;
