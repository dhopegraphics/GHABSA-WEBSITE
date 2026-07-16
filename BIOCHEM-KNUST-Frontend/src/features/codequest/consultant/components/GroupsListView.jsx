import { motion } from "framer-motion";

const GroupsListView = ({ groups, onGroupSelect }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case "in_progress":
        return "bg-blue-100 text-blue-700";
      case "completed":
        return "bg-green-100 text-green-700";
      case "pending":
        return "bg-yellow-100 text-yellow-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "in_progress":
        return "In Progress";
      case "completed":
        return "Completed";
      case "pending":
        return "Pending";
      default:
        return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
              👥
            </div>
            <div>
              <p className="text-gray-600 text-sm">Total Groups</p>
              <p className="text-2xl font-bold text-gray-900">
                {groups.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
              ✓
            </div>
            <div>
              <p className="text-gray-600 text-sm">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {groups.filter((g) => g.status === "completed").length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
              🔄
            </div>
            <div>
              <p className="text-gray-600 text-sm">In Progress</p>
              <p className="text-2xl font-bold text-gray-900">
                {groups.filter((g) => g.status === "in_progress").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group, index) => (
          <motion.div
            key={index}
            className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onGroupSelect(group)}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-1">
                    Group {group.group_number}
                  </h3>
                  <p className="text-gray-600 text-sm">{group.group_name}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    group.status
                  )}`}
                >
                  {getStatusLabel(group.status)}
                </span>
              </div>

              <div className="space-y-3 mb-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>📱</span>
                  <span className="truncate">
                    {group.project?.app_name || "No project yet"}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>👤</span>
                  <span>
                    {group.members?.length || 0}{" "}
                    {group.members?.length === 1 ? "member" : "members"}
                  </span>
                </div>
                {group.project_manager && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span>⭐</span>
                    <span className="truncate">
                      PM: {group.project_manager}
                    </span>
                  </div>
                )}
              </div>

              <button className="w-full py-2 bg-blue-50 text-blue-600 rounded-lg font-medium hover:bg-blue-100 transition-colors">
                View Details →
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {groups.length === 0 && (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <div className="text-6xl mb-4">👥</div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            No Groups Assigned Yet
          </h3>
          <p className="text-gray-600">
            You&apos;ll see your assigned groups here once they&apos;re ready.
          </p>
        </div>
      )}
    </div>
  );
};

export default GroupsListView;
