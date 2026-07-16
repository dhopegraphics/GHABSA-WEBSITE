import { useState } from "react";

const MyTasksView = ({ userData, groupData }) => {
  const [tasks] = useState([
    {
      id: 1,
      title: "Setup Project Repository",
      description: "Create GitHub repository and initialize project structure",
      due_date: "2025-02-15",
      priority: "High",
      status: "completed",
      assigned_to: userData?.student_name,
    },
    {
      id: 2,
      title: "Implement User Authentication",
      description: "Build login and registration functionality",
      due_date: "2025-02-25",
      priority: "High",
      status: "in_progress",
      assigned_to: userData?.student_name,
    },
    {
      id: 3,
      title: "Design Database Schema",
      description: "Create ER diagram and database tables",
      due_date: "2025-03-01",
      priority: "Medium",
      status: "todo",
      assigned_to: userData?.student_name,
    },
  ]);

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-700 border-green-300";
      case "in_progress":
        return "bg-blue-100 text-blue-700 border-blue-300";
      case "todo":
        return "bg-gray-100 text-gray-700 border-gray-300";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "High":
        return "bg-red-100 text-red-700";
      case "Medium":
        return "bg-yellow-100 text-yellow-700";
      case "Low":
        return "bg-green-100 text-green-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const completedTasks = tasks.filter((t) => t.status === "completed");
  const inProgressTasks = tasks.filter((t) => t.status === "in_progress");
  const todoTasks = tasks.filter((t) => t.status === "todo");

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">To Do</p>
              <p className="text-3xl font-bold text-gray-900">
                {todoTasks.length}
              </p>
            </div>
            <span className="text-4xl">📋</span>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">In Progress</p>
              <p className="text-3xl font-bold text-blue-600">
                {inProgressTasks.length}
              </p>
            </div>
            <span className="text-4xl">🔄</span>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Completed</p>
              <p className="text-3xl font-bold text-green-600">
                {completedTasks.length}
              </p>
            </div>
            <span className="text-4xl">✅</span>
          </div>
        </div>
      </div>

      {/* Task Lists */}
      <div className="space-y-6">
        {/* In Progress Tasks */}
        {inProgressTasks.length > 0 && (
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
              In Progress ({inProgressTasks.length})
            </h3>
            <div className="space-y-3">
              {inProgressTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  getStatusColor={getStatusColor}
                  getPriorityColor={getPriorityColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Todo Tasks */}
        {todoTasks.length > 0 && (
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-3 h-3 bg-gray-500 rounded-full"></span>
              To Do ({todoTasks.length})
            </h3>
            <div className="space-y-3">
              {todoTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  getStatusColor={getStatusColor}
                  getPriorityColor={getPriorityColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              Completed ({completedTasks.length})
            </h3>
            <div className="space-y-3">
              {completedTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  getStatusColor={getStatusColor}
                  getPriorityColor={getPriorityColor}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const TaskCard = ({ task, getStatusColor, getPriorityColor }) => {
  const isOverdue =
    new Date(task.due_date) < new Date() && task.status !== "completed";

  return (
    <div className="bg-white rounded-lg shadow-md p-5 border-l-4 border-blue-500 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 text-lg mb-1">
            {task.title}
          </h4>
          <p className="text-gray-600 text-sm">{task.description}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(
            task.priority
          )}`}
        >
          {task.priority}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            📅 Due: {new Date(task.due_date).toLocaleDateString()}
          </span>
          {isOverdue && (
            <span className="text-red-600 font-medium">⚠️ Overdue</span>
          )}
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium border-2 ${getStatusColor(
            task.status
          )}`}
        >
          {task.status === "in_progress"
            ? "In Progress"
            : task.status === "completed"
            ? "Completed"
            : "To Do"}
        </span>
      </div>

      {task.status !== "completed" && (
        <div className="mt-4">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
            Mark as Complete
          </button>
        </div>
      )}
    </div>
  );
};

export default MyTasksView;
