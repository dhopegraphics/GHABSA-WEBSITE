import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import axios from "axios";
import DashboardSidebar from "../shared/components/DashboardSidebar";
import DashboardHeader from "../shared/components/DashboardHeader";
import WaitingForGroup from "./components/WaitingForGroup";
import SelfGroupingView from "./components/SelfGroupingView";
import MyGroupView from "./components/MyGroupView";
import MyTasksView from "./components/MyTasksView";
import ProjectView from "./components/ProjectView";
import ConsultantView from "./components/ConsultantView";
import ResultsView from "./components/ResultsView";
import VotingView from "./components/VotingView";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ParticipantDashboard = () => {
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState("group");
  const [userData, setUserData] = useState(null);
  const [groupData, setGroupData] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [consultantData, setConsultantData] = useState(null);
  const [tasksData, setTasksData] = useState([]);
  const [eventData, setEventData] = useState(null);
  const [pmElection, setPmElection] = useState(null);
  const [phase, setPhase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchParticipantData = useCallback(async () => {
    try {
      const accessKey =
        localStorage.getItem("cq_access_key") ||
        sessionStorage.getItem("cq_access_key");

      if (!accessKey) {
        navigate("/code-quest-portal/login");
        return;
      }

      const response = await axios.get(
        `${API_BASE_URL}/codequest/participant/dashboard/?access_key=${accessKey}`
      );

      const data = response.data;
      
      setUserData(data.participant);
      setGroupData(data.group);
      setProjectData(data.project);
      setConsultantData(data.consultant);
      setTasksData(data.tasks || []);
      setEventData(data.event);
      setPmElection(data.pm_election);
      setPhase(data.phase);
      
      // Set initial view based on phase
      if (data.phase?.name === 'waiting') {
        setActiveView('waiting');
      } else if (data.phase?.name === 'voting' && !data.pm_election?.has_voted) {
        setActiveView('voting');
      } else {
        setActiveView('group');
      }
      
    } catch (err) {
      console.error("Failed to fetch participant data:", err);
      if (err.response?.status === 401) {
        // Invalid access key - redirect to login
        localStorage.removeItem("cq_access_key");
        sessionStorage.removeItem("cq_access_key");
        navigate("/code-quest-portal/login");
      } else {
        setError(err.response?.data?.error || "Failed to load dashboard");
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchParticipantData();
  }, [fetchParticipantData]);

  const handleLogout = () => {
    localStorage.removeItem("cq_access_key");
    localStorage.removeItem("cq_user_data");
    sessionStorage.removeItem("cq_access_key");
    sessionStorage.removeItem("cq_user_data");
    navigate("/code-quest-portal/login");
  };

  const sidebarItems = [
    {
      id: "group",
      icon: "👥",
      label: "My Group",
      onClick: () => setActiveView("group"),
      active: activeView === "group",
    },
    {
      id: "tasks",
      icon: "🎯",
      label: "My Tasks",
      onClick: () => setActiveView("tasks"),
      badge: userData?.pending_tasks || 0,
      active: activeView === "tasks",
    },
    {
      id: "project",
      icon: "📱",
      label: "Our Project",
      onClick: () => setActiveView("project"),
      active: activeView === "project",
    },
    {
      id: "consultant",
      icon: "👨‍🏫",
      label: "Our Consultant",
      onClick: () => setActiveView("consultant"),
      active: activeView === "consultant",
    },
    {
      id: "results",
      icon: "📊",
      label: "Results",
      onClick: () => setActiveView("results"),
      active: activeView === "results",
    },
  ];

  // Add voting item if election is open
  if (pmElection?.voting_open && !pmElection?.winner) {
    sidebarItems.splice(1, 0, {
      id: "voting",
      icon: "🗳️",
      label: "PM Election",
      onClick: () => setActiveView("voting"),
      badge: pmElection?.has_voted ? "✓" : "!",
      active: activeView === "voting",
    });
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Waiting Phase - Before group is formed
  if (phase?.name === "waiting") {
    // Check if self-grouping is enabled
    const selfGroupingEnabled = eventData?.allow_self_grouping;
    
    // Sidebar items for self-grouping mode
    const waitingPhaseSidebarItems = selfGroupingEnabled
      ? [
          {
            id: "self-grouping",
            icon: "🤝",
            label: "Form Team",
            onClick: () => setActiveView("self-grouping"),
            active: activeView === "self-grouping",
          },
          {
            id: "waiting",
            icon: "⏳",
            label: "Status",
            onClick: () => setActiveView("waiting"),
            active: activeView === "waiting",
          },
        ]
      : [];

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex">
          <DashboardSidebar
            items={waitingPhaseSidebarItems}
            userInfo={{
              name: userData?.student_name,
              student_id: userData?.student_id,
              access_key: userData?.access_key,
            }}
            onLogout={handleLogout}
          />
          <div className="flex-1">
            <DashboardHeader
              title={selfGroupingEnabled && activeView === "self-grouping" ? "Form Your Team" : "Welcome to Code Quest!"}
              subtitle={selfGroupingEnabled && activeView === "self-grouping" ? "Find teammates and create your group" : (phase?.description || "Your group is being formed")}
            />
            {selfGroupingEnabled && activeView === "self-grouping" ? (
              <SelfGroupingView
                userData={userData}
                eventData={eventData}
                onGroupFormed={fetchParticipantData}
              />
            ) : (
              <WaitingForGroup userData={userData} eventData={eventData} selfGroupingEnabled={selfGroupingEnabled} onStartSelfGrouping={() => setActiveView("self-grouping")} />
            )}
          </div>
        </div>
      </div>
    );
  }

  // Active Phase - Full Dashboard
  const renderContent = () => {
    switch (activeView) {
      case "group":
        return <MyGroupView groupData={groupData} userData={userData} pmElection={pmElection} />;
      case "voting":
        return (
          <VotingView
            groupData={groupData}
            userData={userData}
            pmElection={pmElection}
            onVoteSubmit={fetchParticipantData}
          />
        );
      case "tasks":
        return <MyTasksView userData={userData} groupData={groupData} tasks={tasksData} onRefresh={fetchParticipantData} />;
      case "project":
        return <ProjectView groupData={groupData} userData={userData} projectData={projectData} onRefresh={fetchParticipantData} />;
      case "consultant":
        return <ConsultantView groupData={groupData} consultantData={consultantData} />;
      case "results":
        return <ResultsView groupData={groupData} projectData={projectData} />;
      default:
        return <MyGroupView groupData={groupData} userData={userData} pmElection={pmElection} />;
    }
  };

  const getHeaderInfo = () => {
    switch (activeView) {
      case "group":
        return { title: "My Group", subtitle: groupData?.group_name || `Group ${groupData?.group_number}` };
      case "voting":
        return { title: "PM Election", subtitle: pmElection?.has_voted ? "You have voted" : "Cast your vote" };
      case "tasks":
        return { title: "My Tasks", subtitle: `${userData?.pending_tasks || 0} pending tasks` };
      case "project":
        return { title: "Our Project", subtitle: projectData?.app_name || "No project yet" };
      case "consultant":
        return { title: "Our Consultant", subtitle: consultantData?.student_name || "Not assigned yet" };
      case "results":
        return { title: "Results", subtitle: "View your scores" };
      default:
        return { title: "Dashboard", subtitle: "" };
    }
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <DashboardSidebar
          items={groupData ? sidebarItems : []}
          userInfo={{
            name: userData?.student_name,
            student_id: userData?.student_id,
            access_key: userData?.access_key,
            is_pm: userData?.is_project_manager,
          }}
          onLogout={handleLogout}
          phase={phase}
        />
        <div className="flex-1">
          <DashboardHeader
            title={headerInfo.title}
            subtitle={headerInfo.subtitle}
            phase={phase}
          />
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="p-6"
          >
            {renderContent()}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ParticipantDashboard;
