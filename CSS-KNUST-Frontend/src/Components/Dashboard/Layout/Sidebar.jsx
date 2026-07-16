import { Link, NavLink } from "react-router-dom";
import { useContext } from "react";
import {
  Home,
  Calendar,
  BookOpen,
  FileText,
  BookMarked,
  X,
  Settings,
  Upload,
  ShoppingCart,
  ChevronLeft,
  ChevronRight,
  Users,
  FolderKanban,
  Package,
  ShoppingBag,
  Shield,
  Ticket,
} from "lucide-react";
import { useCart } from "../../../Context/CartContext";
import { UserContext } from "../../../Context/UserContext";
import logo from "../../../assets/css.png";

export function Sidebar({ isOpen, onClose, isCollapsed, onToggleCollapse }) {
  const { getCartCount } = useCart();
  const { user } = useContext(UserContext);
  const cartCount = getCartCount();
  const isStaff = user?.user?.is_staff;

  const navigation = [
    { name: "Home", icon: Home, href: "/dashboard/home" },
    {
      name: "Academic Resources",
      icon: BookOpen,
      href: "/dashboard/academic-resources",
    },
    { name: "Timetable", icon: Calendar, href: "/dashboard/timetable" },
    { name: "Saved Resources", icon: FileText, href: "/dashboard/resources" },
    { name: "Saved Blogs", icon: BookMarked, href: "/dashboard/blogs" },
    {
      name: "Mentorship",
      icon: Users,
      href: "/dashboard/mentorship",
      highlight: true,
    },
    {
      name: "My Cart",
      icon: ShoppingCart,
      href: "/dashboard/cart",
      highlight: true,
    },
    {
      name: "My Purchases",
      icon: Package,
      href: "/dashboard/purchases",
      highlight: true,
    },
    {
      name: "My Orders",
      icon: ShoppingBag,
      href: "/dashboard/orders",
      highlight: true,
    },
    {
      name: "Event Registrations",
      icon: Ticket,
      href: "/dashboard/event-registrations",
      highlight: true,
    },
    {
      name: "Submit Project",
      icon: Upload,
      href: "/dashboard/submit-project",
      highlight: true,
    },
    {
      name: "My Projects",
      icon: FolderKanban,
      href: "/dashboard/my-projects",
    },
    { name: "Settings", icon: Settings, href: "/dashboard/settings" },
    // Staff-only: Merchandise Validation
    ...(isStaff
      ? [
          {
            name: "Validate Merch",
            icon: Shield,
            href: "/dashboard/staff/validate",
            highlight: true,
            staffOnly: true,
          },
        ]
      : []),
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-900/50 lg:hidden z-[5000]"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
        fixed top-0 left-0 bottom-0 bg-white border-r border-gray-200
        transform transition-all duration-300 ease-in-out z-[5001]
        ${isCollapsed ? "w-20 hidden lg:block" : "w-64"}
        ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 mx-4 border-b border-gray-200">
          {!isCollapsed && (
            <Link to={"/"} className="w-[80px] mt-2">
              <img src={logo} className="object-contain" alt="CSS Logo" />
            </Link>
          )}
          {isCollapsed && (
            <Link to={"/"} className="w-8 mx-auto mt-2">
              <img src={logo} className="object-contain" alt="CSS Logo" />
            </Link>
          )}
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Navigation */}
        <nav
          className="p-4 space-y-1 overflow-y-auto"
          style={{ maxHeight: "calc(100vh - 8rem)" }}
        >
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={onClose}
              title={isCollapsed ? item.name : ""}
              className={({ isActive }) => `
                flex items-center rounded-lg transition-all relative group
                ${isCollapsed ? "justify-center p-3" : "gap-3 px-3 py-2"}
                ${
                  isActive
                    ? item.staffOnly
                      ? "bg-amber-50 text-amber-700"
                      : "bg-blue-50 text-blue-600"
                    : item.staffOnly
                    ? "text-amber-700 hover:bg-amber-50 font-medium"
                    : item.highlight
                    ? "text-purple-700 hover:bg-purple-50 font-medium"
                    : "text-gray-700 hover:bg-gray-50"
                }
              `}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
              {item.name === "My Cart" && cartCount > 0 && (
                <span
                  className={`
                  bg-blue-600 text-white text-xs font-bold rounded-full
                  flex items-center justify-center
                  ${
                    isCollapsed
                      ? "absolute -top-1 -right-1 w-5 h-5"
                      : "ml-auto w-5 h-5"
                  }
                `}
                >
                  {cartCount}
                </span>
              )}
              {/* Staff badge for staff-only items */}
              {item.staffOnly && !isCollapsed && (
                <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded">
                  STAFF
                </span>
              )}
              {/* Tooltip for collapsed state */}
              {isCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                  {item.name}
                  {item.staffOnly && (
                    <span className="ml-1 px-1 py-0.5 text-[9px] bg-amber-500 text-white rounded">
                      STAFF
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Desktop Toggle Button */}
        <button
          onClick={onToggleCollapse}
          className="hidden lg:flex absolute -right-3 top-20 bg-white border border-gray-200 rounded-full p-1.5 hover:bg-gray-50 transition-colors shadow-md"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>
    </>
  );
}
