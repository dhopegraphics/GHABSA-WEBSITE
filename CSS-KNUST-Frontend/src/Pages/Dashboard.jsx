import { useContext, useEffect, useState } from "react";
import { WelcomeCard } from "../Components/Dashboard/WelcomeCard";
import { StatsGrid } from "../Components/Dashboard/StatsGrid";
import { ActivityChart } from "../Components/Dashboard/ActivityChart";
import { ResourcesOverview } from "../Components/Dashboard/ResourcesOverview";
import { ExamCalendar } from "../Components/Dashboard/ExamCalendar";
import { NextClassSchedule } from "../Components/Dashboard/NextClassSchedule";
import { SemesterResourcesSection } from "../Components/Dashboard/AcademicResources/SemesterResourcesSection";
import { UserContext } from "../Context/UserContext";
import { useCourses } from "../Context/CoursesContext";
import { useCourseResources } from "../Hooks/useCourseResources";
import { scrollToTop } from "../utils/scrollToTop";
import { Alert, AlertTitle } from "@mui/material";
import { MapResource } from "../Components/Dashboard/MapResource";
import { Link } from "react-router-dom";
import PhoneVerification from "./PhoneVerification";
import useAxiosWithRefresh from "../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../utils/config";
import { getData } from "../utils/apiHandler";
import { Loader, ShieldCheck, Smartphone } from "lucide-react";
import { ProfileCompletionOverlay } from "../Components/Dashboard/ProfileCompletionOverlay";
import NotificationPermissionPrompt from "../Components/NotificationPermissionPrompt";
import {
  initializePushNotifications,
  isPushNotificationSupported,
  getNotificationPermissionStatus,
} from "../services/pushNotificationService";
import { CalendarSyncButton } from "../Components/CalendarSync/CalendarSyncModal";

export function DashboardPage() {
  const { user } = useContext(UserContext);
  const { courses, setCourses } = useCourses();
  const { enrichedCourses, loading: resourcesLoading } =
    useCourseResources(courses);
  const [show, setShow] = useState(true);
  const [showProgramAlert, setShowProgramAlert] = useState(true);
  const [showProfileCompletionAlert, setShowProfileCompletionAlert] =
    useState(true);
  const [showProfileOverlay, setShowProfileOverlay] = useState(false);
  const [isOpenVerify, setIsOpenVerify] = useState(false);
  const [verifyError, setVerifyError] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [showNotificationPrompt, setShowNotificationPrompt] = useState(false);
  const axiosInstance = useAxiosWithRefresh();

  // Fetch the single programme curriculum; year/semester filtering happens in the UI.
  useEffect(() => {
    const fetchCourses = async () => {
      if (!courses || courses.length === 0) {
        const { response, error } = await getData(`/academics/courses/`);
        if (error) {
          console.error("Error fetching courses:", error);
        }
        if (response) {
          setCourses(response);
        }
      }
    };
    fetchCourses();
  }, [courses, setCourses]);

  // Check for incomplete profile fields
  const getIncompleteFields = () => {
    const fields = [];
    if (!user?.user?.student_id) fields.push("Student ID");
    if (!user?.user?.index_number) fields.push("Index Number");
    if (!user?.user?.personal_email) fields.push("Personal Email");
    if (!user?.user?.student_email) fields.push("Student Email");
    if (!user?.user?.gender) fields.push("Gender");
    return fields;
  };

  const incompleteFields = getIncompleteFields();

  // Auto-show profile overlay when there are incomplete fields
  useEffect(() => {
    if (incompleteFields.length > 0 && user?.user) {
      // Check if user has dismissed overlay before (using sessionStorage)
      const dismissed = sessionStorage.getItem("profileOverlayDismissed");
      if (!dismissed) {
        // Show overlay after a short delay for better UX
        const timer = setTimeout(() => {
          setShowProfileOverlay(true);
        }, 1500);
        return () => clearTimeout(timer);
      }
    }
  }, [incompleteFields.length, user]);

  // Check and show notification permission prompt
  useEffect(() => {
    const checkNotificationPermission = () => {
      // Only show if browser supports push notifications
      if (!isPushNotificationSupported()) {
        return;
      }

      const permissionStatus = getNotificationPermissionStatus();
      const isRegistered = localStorage.getItem("push-subscription-registered");
      const lastDismissed = localStorage.getItem(
        "notification-prompt-dismissed"
      );

      // Show prompt if:
      // 1. Permission is default (not granted or denied)
      // 2. Not already registered
      // 3. Not dismissed recently (within 7 days)
      if (permissionStatus === "default" && !isRegistered) {
        if (lastDismissed) {
          const daysSinceDismissed =
            (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24);
          if (daysSinceDismissed < 7) {
            return; // Don't show if dismissed within last 7 days
          }
        }
        // Delay showing the prompt to avoid overwhelming user
        setTimeout(() => {
          setShowNotificationPrompt(true);
        }, 3000);
      }
    };

    checkNotificationPermission();
  }, [user]);

  const handleNotificationPermissionGranted = async () => {
    try {
      await initializePushNotifications(axiosInstance);

      setShowNotificationPrompt(false);
    } catch (error) {
      console.error("Failed to initialize push notifications:", error);
    }
  };

  const handleNotificationPermissionDenied = () => {
    setShowNotificationPrompt(false);
  };

  useEffect(() => {
    scrollToTop();
  }, []);

  const handleClose = () => {
    setShow(false);
  };

  const handleProgramAlertClose = () => {
    setShowProgramAlert(false);
  };

  const [selectedExam, setSelectedExam] = useState({
    course: { course_name: "Loading", course_code: "Loading" },
    time: "2025-01-10T16:25:35Z",
    college: "Loading",
    room: "Loading",
    geolocation: "6.673137532517488,-1.5671843379287753",
    date: "2025-01-01",
  });

  return (
    <>
      {/* Notification Permission Prompt */}
      {showNotificationPrompt && (
        <NotificationPermissionPrompt
          onPermissionGranted={handleNotificationPermissionGranted}
          onPermissionDenied={handleNotificationPermissionDenied}
          onClose={() => setShowNotificationPrompt(false)}
        />
      )}

      {/* Profile Completion Overlay - Rendered at root level to be on top of everything */}
      {showProfileOverlay && incompleteFields.length > 0 && (
        <ProfileCompletionOverlay
          incompleteFields={incompleteFields}
          onClose={() => {
            setShowProfileOverlay(false);
            sessionStorage.setItem("profileOverlayDismissed", "true");
          }}
        />
      )}

      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8">
            {show && !user?.user?.phone_confirm && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-xl p-6 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="bg-blue-500 p-3 rounded-full animate-pulse">
                      <Smartphone className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-xl font-bold text-gray-900">
                        Phone Verification Required
                      </h3>
                      <span className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full animate-bounce">
                        ACTION NEEDED
                      </span>
                    </div>
                    <p className="text-gray-700 mb-4">
                      Verify your phone number to receive important
                      notifications, exam alerts, and event updates. This helps
                      us keep you informed about everything happening in CSS
                      KNUST.
                    </p>
                    <div className="flex flex-wrap gap-3">
                      <button
                        onClick={async () => {
                          setIsVerifying(true);
                          setVerifyError("");
                          try {
                            const url = `${BACKEND_HOST}/accounts/request-sms-verification/`;
                            const formData = new FormData();
                            formData.append("phone", user?.user?.phone);

                            await axiosInstance.post(url, formData, {
                              headers: {
                                Authorization: `Bearer ${user?.access}`,
                              },
                            });
                            setVerifyError("");
                            setIsOpenVerify(true);
                          } catch (err) {
                            console.error(
                              "Error sending verification code:",
                              err
                            );
                            if (
                              err?.response?.status === 429 ||
                              err?.response?.data?.error_type === "rate_limit"
                            ) {
                              const cooldown =
                                err?.response?.data?.data?.cooldown_seconds ||
                                60;
                              setVerifyError(
                                `Please wait ${cooldown} seconds before requesting another code.`
                              );
                            } else {
                              setVerifyError(
                                err?.response?.data?.message ||
                                  "Error sending code"
                              );
                            }
                            setIsOpenVerify(true);
                          } finally {
                            setIsVerifying(false);
                          }
                        }}
                        disabled={isVerifying}
                        className={`bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105 flex items-center gap-2 ${
                          isVerifying ? "opacity-70 cursor-not-allowed" : ""
                        }`}
                      >
                        {isVerifying ? (
                          <>
                            <Loader className="w-5 h-5 animate-spin" />
                            Sending Code...
                          </>
                        ) : (
                          <>
                            <ShieldCheck className="w-5 h-5" />
                            Verify Phone Now
                          </>
                        )}
                      </button>
                      <Link
                        to="/dashboard/account"
                        className="bg-white border-2 border-blue-300 hover:border-blue-400 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-blue-50 transition-all flex items-center gap-2"
                      >
                        Update Phone Number
                      </Link>
                      <button
                        onClick={handleClose}
                        className="text-gray-600 hover:text-gray-800 font-medium py-3 px-4 rounded-lg hover:bg-gray-100 transition-all"
                      >
                        Dismiss
                      </button>
                    </div>
                    {verifyError && (
                      <div className="mt-3 bg-red-100 border border-red-300 text-red-700 px-4 py-2 rounded-lg text-sm">
                        {verifyError}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {showProgramAlert && !user?.user?.program && (
              <Alert
                onClose={handleProgramAlertClose}
                severity={"info"}
                sx={{ width: "100%" }}
              >
                <AlertTitle>Update Required</AlertTitle>
                Please select your program to complete your profile.{" "}
                <Link className="underline" to="/dashboard/account">
                  Click here
                </Link>
              </Alert>
            )}

            {showProfileCompletionAlert && incompleteFields.length > 0 && (
              <div className="bg-blue-50 border-2 border-blue-300 rounded-xl p-5 shadow-md">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-bold text-gray-900">
                        Complete Your Profile
                      </h3>
                      <span className="bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                        {incompleteFields.length} field
                        {incompleteFields.length > 1 ? "s" : ""}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">
                      Update the following fields to access all features and get
                      a personalized experience:
                    </p>
                    <ul className="list-disc ml-5 mb-3 text-sm text-gray-700">
                      {incompleteFields.slice(0, 3).map((field, index) => (
                        <li key={index}>{field}</li>
                      ))}
                      {incompleteFields.length > 3 && (
                        <li>
                          and {incompleteFields.length - 3} more field
                          {incompleteFields.length - 3 > 1 ? "s" : ""}
                        </li>
                      )}
                    </ul>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setShowProfileOverlay(true)}
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold py-2 px-4 rounded-lg shadow hover:shadow-lg transition-all text-sm"
                      >
                        View Details
                      </button>
                      <Link
                        to="/dashboard/account"
                        className="bg-white border-2 border-blue-300 hover:border-blue-400 text-gray-700 font-semibold py-2 px-4 rounded-lg hover:bg-blue-50 transition-all text-sm"
                      >
                        Update Now
                      </Link>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowProfileCompletionAlert(false)}
                    className="text-gray-400 hover:text-gray-600 p-1"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {user?.user?.has_completed_program && (
              <Alert severity="success" sx={{ width: "100%" }}>
                <AlertTitle>🎓 Congratulations!</AlertTitle>
                <div>
                  You have successfully completed all 8 semesters of your
                  program! Your academic journey at KNUST is complete.
                </div>
              </Alert>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              <div className="lg:col-span-3">
                <WelcomeCard
                  name={`${user?.user?.first_name} ${user?.user?.last_name}`}
                  year={user?.user?.graduation_year}
                  program={`${
                    user?.user?.program_display || "Program not set"
                  }`}
                  currentSemester={user?.user?.current_semester}
                />
              </div>
              <div className="lg:col-span-2">
                <StatsGrid />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-4">
                <NextClassSchedule />
              </div>
              <div className="lg:col-span-4 grid place-items-center lg:place-items-start">
                <ExamCalendar setSelectedExam={setSelectedExam} />
              </div>
              <div className="lg:col-span-4">
                <MapResource selectedExam={selectedExam} />
              </div>
            </div>

            {/* Calendar Sync Section */}
            <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-2xl p-6 shadow-lg text-white">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-white/20 rounded-xl">
                    <svg
                      className="w-8 h-8"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">
                      📱 Sync Your Schedule to Phone
                    </h3>
                    <p className="text-blue-100 text-sm mt-1">
                      Add your class timetable, exam schedule, and events directly to your phone&apos;s calendar app
                    </p>
                  </div>
                </div>
                <CalendarSyncButton
                  calendarTypes={["classes", "exams", "events", "full"]}
                  variant="default"
                  className="bg-white text-indigo-600 hover:bg-gray-100 shadow-lg"
                />
              </div>
            </div>

            {/* Academic Resources Section - Current Semester Only */}
            {enrichedCourses &&
              enrichedCourses.length > 0 &&
              user?.user?.year && (
                <div className="relative">
                  {resourcesLoading && (
                    <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-10 rounded-xl">
                      <div className="flex flex-col items-center gap-3">
                        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                        <p className="text-sm text-gray-600 font-medium">
                          Loading course resources...
                        </p>
                      </div>
                    </div>
                  )}
                  <SemesterResourcesSection
                    courses={enrichedCourses}
                    userYear={user?.user?.year}
                    currentSemester={user?.user?.current_semester || 1}
                    showOnlyCurrentSemester={true}
                  />
                </div>
              )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <ActivityChart />
              </div>
              <ResourcesOverview />
            </div>
          </div>
        </div>
      </div>

      {isOpenVerify && (
        <PhoneVerification
          resend={async () => {
            try {
              const url = `${BACKEND_HOST}/accounts/request-sms-verification/`;
              const formData = new FormData();
              formData.append("phone", user?.user?.phone);
              await axiosInstance.post(url, formData, {
                headers: { Authorization: `Bearer ${user?.access}` },
              });
            } catch (err) {
              console.error(err);
            }
          }}
          onClose={() => setIsOpenVerify(false)}
        />
      )}
    </>
  );
}
