import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import DashboardSidebar from "../shared/components/DashboardSidebar";
import DashboardHeader from "../shared/components/DashboardHeader";
import GroupsListView from "./components/GroupsListView";
import GroupDetailView from "./components/GroupDetailView";

const ConsultantDashboard = () => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [activeView, setActiveView] = useState("groups");
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const accessKey =
        localStorage.getItem("cq_access_key") ||
        sessionStorage.getItem("cq_access_key");

      if (!accessKey) {
        navigate("/code-quest-portal/login");
        return;
      }

      const response = await axios.get(
        `/codequest/consultant/dashboard/?access_key=${accessKey}`
      );

      setUserData(response.data.consultant);
      setGroups(response.data.groups);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      if (error.response?.status === 401) {
        navigate("/code-quest-portal/login");
      }
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("cq_access_key");
    sessionStorage.removeItem("cq_access_key");
    navigate("/code-quest-portal/login");
  };

  const handleGroupSelect = (group) => {
    setSelectedGroup(group);
    setActiveView("group-detail");
  };

  const handleBackToGroups = () => {
    setSelectedGroup(null);
    setActiveView("groups");
  };

  const sidebarItems = [
    {
      id: "groups",
      label: "My Groups",
      icon: "👥",
      active: activeView === "groups",
      onClick: () => handleBackToGroups(),
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <DashboardSidebar
        user={{
          name: userData?.student_name || "Consultant",
          studentId: userData?.student_id || "",
          accessKey:
            localStorage.getItem("cq_access_key") ||
            sessionStorage.getItem("cq_access_key"),
          avatar: userData?.profile_picture || null,
        }}
        navItems={sidebarItems}
        onLogout={handleLogout}
      />

      <div className="flex-1 ml-64">
        <div className="p-8">
          <DashboardHeader
            title={
              activeView === "groups"
                ? "My Groups"
                : `Group ${selectedGroup?.group_number || ""}`
            }
            subtitle={
              activeView === "groups"
                ? `Consulting for ${groups.length} ${
                    groups.length === 1 ? "group" : "groups"
                  }`
                : selectedGroup?.group_name || ""
            }
          />

          <div className="mt-8">
            {activeView === "groups" && (
              <GroupsListView
                groups={groups}
                onGroupSelect={handleGroupSelect}
              />
            )}
            {activeView === "group-detail" && (
              <GroupDetailView
                group={selectedGroup}
                onBack={handleBackToGroups}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsultantDashboard;
