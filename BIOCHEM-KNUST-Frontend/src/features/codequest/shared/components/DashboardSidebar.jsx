import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import PropTypes from "prop-types";

const DashboardSidebar = ({ items, userInfo, onLogout, phase }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("cq_access_key");
    localStorage.removeItem("cq_user_data");
    sessionStorage.removeItem("cq_access_key");
    sessionStorage.removeItem("cq_user_data");
    if (onLogout) {
      onLogout();
    } else {
      navigate("/code-quest-portal/login");
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      {/* User Info */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
            {userInfo?.name?.charAt(0) || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {userInfo?.name || "User"}
            </h3>
            <p className="text-sm text-gray-500 truncate">
              {userInfo?.student_id || ""}
            </p>
            {userInfo?.is_pm && (
              <span className="inline-flex items-center gap-1 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full mt-1">
                ⭐ Project Manager
              </span>
            )}
          </div>
        </div>
        {userInfo?.access_key && (
          <div className="bg-blue-50 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-600 mb-1">Access Key</p>
            <p className="text-sm font-mono font-bold text-blue-600">
              {userInfo.access_key}
            </p>
          </div>
        )}
      </div>

      {/* Current Phase Badge */}
      {phase && (
        <div className="px-4 py-3 border-b border-gray-100">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Current Phase</p>
            <p className="text-sm font-semibold text-blue-700">{phase.label}</p>
          </div>
        </div>
      )}

      {/* Navigation Items */}
      <nav className="flex-1 p-4 space-y-1">
        {items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">Menu will appear once your group is formed</p>
          </div>
        ) : (
          items.map((item, index) => {
            return (
              <motion.button
                key={item.id || index}
                onClick={item.onClick}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  item.active
                    ? "bg-blue-50 text-blue-600 font-semibold"
                    : "text-gray-700 hover:bg-gray-50"
                }`}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
                {item.badge !== undefined && item.badge !== null && (
                  <span className={`ml-auto text-xs px-2 py-1 rounded-full ${
                    item.badge === "✓" 
                      ? "bg-green-100 text-green-700" 
                      : item.badge === "!" 
                        ? "bg-orange-100 text-orange-700"
                        : "bg-red-500 text-white"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </motion.button>
            );
          })
        )}
      </nav>

      {/* Logout Button */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
        >
          <span className="text-xl">🚪</span>
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
};

DashboardSidebar.propTypes = {
  items: PropTypes.array,
  userInfo: PropTypes.object,
  onLogout: PropTypes.func,
  phase: PropTypes.object,
};

DashboardSidebar.defaultProps = {
  items: [],
  userInfo: {},
};

export default DashboardSidebar;
