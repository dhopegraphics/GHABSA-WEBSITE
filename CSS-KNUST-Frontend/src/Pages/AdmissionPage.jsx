import { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  GraduationCap,
  BookOpen,
  Info,
  Calendar,
  HelpCircle,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageCircle,
  Lock,
} from "lucide-react";
import { getData, postData } from "../utils/apiHandler";

// Valid tab IDs for URL validation
const VALID_TABS = ["checker", "guides", "faqs", "dates", "helpdesk"];

const AdmissionPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    const tabParam = searchParams.get("tab");
    return VALID_TABS.includes(tabParam) ? tabParam : "checker";
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [guidelines, setGuidelines] = useState([]);
  const [faqs, setFaqs] = useState([]);
  const [dates, setDates] = useState([]);
  const [criteria, setCriteria] = useState([]);

  // WhatsApp Helpdesk state
  const [applicationId, setApplicationId] = useState("");
  const [helpdeskLoading, setHelpdeskLoading] = useState(false);
  const [helpdeskResult, setHelpdeskResult] = useState(null);

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone: "",
    shs_school: "",
    completion_year: "",
    program: "CS",
    admission_type: "REGULAR",
    subjects: {
      core_mathematics: "",
      english_language: "",
      integrated_science: "",
      social_studies: "",
      elective_mathematics: "",
      physics: "",
      chemistry: "",
      biology: "",
      elective_ict: "",
      other_elective_1_name: "",
      other_elective_1: "",
      other_elective_2_name: "",
      other_elective_2: "",
    },
  });

  const gradeOptions = ["A1", "B2", "B3", "C4", "C5", "C6", "D7", "E8", "F9"];

  // Check important dates for tab disabling
  const tabDisabledInfo = useMemo(() => {
    const allDates = [...(dates.upcoming || []), ...(dates.past || [])];
    
    // Check for admission results release (disables checker tab)
    const resultsEvent = allDates.find(
      (d) =>
        (d.title?.toLowerCase().includes("result") ||
          d.title?.toLowerCase().includes("admission letter")) &&
        new Date(d.event_date) < new Date()
    );

    // Check for application deadline (disables guides tab)
    const deadlineEvent = allDates.find(
      (d) =>
        (d.title?.toLowerCase().includes("application deadline") ||
          d.title?.toLowerCase().includes("last day to submit") ||
          (d.title?.toLowerCase().includes("deadline") && 
           d.title?.toLowerCase().includes("application"))) &&
        new Date(d.event_date) < new Date()
    );

    const checkerDisabled = !!resultsEvent;
    const guidesDisabled = !!deadlineEvent;

    // Determine default tab based on what's available
    let defaultTab = "checker";
    if (checkerDisabled && guidesDisabled) {
      defaultTab = "helpdesk";
    } else if (checkerDisabled) {
      defaultTab = "guides";
    }

    return {
      checker: {
        isDisabled: checkerDisabled,
        eventTitle: resultsEvent?.title,
        eventDate: resultsEvent?.event_date,
      },
      guides: {
        isDisabled: guidesDisabled,
        eventTitle: deadlineEvent?.title,
        eventDate: deadlineEvent?.event_date,
      },
      defaultTab,
    };
  }, [dates]);

  const isCheckerDisabled = tabDisabledInfo.checker.isDisabled;
  const isGuidesDisabled = tabDisabledInfo.guides.isDisabled;
  const defaultAvailableTab = tabDisabledInfo.defaultTab;

  // Handle tab change - updates both state and URL
  const handleTabChange = useCallback((tabId) => {
    // Prevent switching to disabled tabs
    if (tabId === "checker" && isCheckerDisabled) return;
    if (tabId === "guides" && isGuidesDisabled) return;
    
    setActiveTab(tabId);
    setSearchParams({ tab: tabId }, { replace: true });
  }, [setSearchParams, isCheckerDisabled, isGuidesDisabled]);

  // Sync tab state when URL changes (e.g., browser back/forward)
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (VALID_TABS.includes(tabParam) && tabParam !== activeTab) {
      // Redirect away from disabled tabs to the best available default
      if ((tabParam === "checker" && isCheckerDisabled) ||
          (tabParam === "guides" && isGuidesDisabled)) {
        setActiveTab(defaultAvailableTab);
        setSearchParams({ tab: defaultAvailableTab }, { replace: true });
      } else {
        setActiveTab(tabParam);
      }
    }
  }, [searchParams, activeTab, isCheckerDisabled, isGuidesDisabled, defaultAvailableTab, setSearchParams]);

  // Redirect if currently on a disabled tab
  useEffect(() => {
    if ((activeTab === "checker" && isCheckerDisabled) || 
        (activeTab === "guides" && isGuidesDisabled)) {
      setActiveTab(defaultAvailableTab);
      setSearchParams({ tab: defaultAvailableTab }, { replace: true });
    }
  }, [isCheckerDisabled, isGuidesDisabled, activeTab, defaultAvailableTab, setSearchParams]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const { response: guidelinesRes } = await getData(
        "/admissions/guidelines/"
      );
      const { response: faqsRes } = await getData("/admissions/faqs/");
      const { response: datesRes } = await getData(
        "/admissions/important-dates/"
      );
      const { response: criteriaRes } = await getData("/admissions/criteria/");

      setGuidelines(guidelinesRes?.data || []);
      setFaqs(faqsRes?.data || []);
      setDates(datesRes?.data || []);
      setCriteria(criteriaRes?.data || []);
    } catch (error) {
      console.error("Error fetching admission data:", error);
    }
  };

  const handleSubjectChange = (subject, grade) => {
    setFormData((prev) => ({
      ...prev,
      subjects: {
        ...prev.subjects,
        [subject]: grade,
      },
    }));
  };

  const checkEligibility = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      // Transform formData to match backend API format
      const payload = {
        full_name: formData.full_name,
        email: formData.email,
        phone: formData.phone,
        shs_school: formData.shs_school,
        completion_year: parseInt(formData.completion_year),
        preferred_program: formData.program,
        admission_type: formData.admission_type,
        core_math_grade: formData.subjects.core_mathematics,
        english_grade: formData.subjects.english_language,
        integrated_science_grade: formData.subjects.integrated_science,
        social_studies_grade: formData.subjects.social_studies,
        elective_math_grade: formData.subjects.elective_mathematics || "",
        physics_grade: formData.subjects.physics || "",
        chemistry_grade: formData.subjects.chemistry || "",
        biology_grade: formData.subjects.biology || "",
        elective_ict_grade: formData.subjects.elective_ict || "",
        other_elective_1: formData.subjects.other_elective_1_name || "",
        other_elective_1_grade: formData.subjects.other_elective_1 || "",
        other_elective_2: formData.subjects.other_elective_2_name || "",
        other_elective_2_grade: formData.subjects.other_elective_2 || "",
      };

      // Calculate aggregate score: Best 3 core + Best 3 electives
      const gradeMap = {
        A1: 1,
        B2: 2,
        B3: 3,
        C4: 4,
        C5: 5,
        C6: 6,
        D7: 7,
        E8: 8,
        F9: 9,
      };

      // Best 3 core subjects: English, Math, and best of (Science or Social Studies)
      const coreGrades = [
        gradeMap[formData.subjects.core_mathematics] || 99,
        gradeMap[formData.subjects.english_language] || 99,
        Math.min(
          gradeMap[formData.subjects.integrated_science] || 99,
          gradeMap[formData.subjects.social_studies] || 99
        ),
      ];

      // Best 3 electives
      const electiveGrades = [
        formData.subjects.elective_mathematics,
        formData.subjects.physics,
        formData.subjects.chemistry,
        formData.subjects.biology,
        formData.subjects.elective_ict,
        formData.subjects.other_elective_1,
        formData.subjects.other_elective_2,
      ]
        .filter((grade) => grade !== "")
        .map((grade) => gradeMap[grade] || 99)
        .sort((a, b) => a - b)
        .slice(0, 3);

      // Validate minimum 3 electives
      if (electiveGrades.length < 3) {
        setResult({
          is_eligible: false,
          message: "❌ Insufficient Elective Subjects",
          details: {
            error: `You must have at least 3 elective subjects. You provided ${electiveGrades.length}.`,
          },
          recommendations: [
            "Please provide grades for at least 3 elective subjects.",
            "Elective subjects include: Elective Mathematics, Physics, Chemistry, Biology, or other electives.",
          ],
        });
        setLoading(false);
        return;
      }

      payload.aggregate_score = [...coreGrades, ...electiveGrades].reduce(
        (sum, val) => sum + val,
        0
      );

      const { response, error } = await postData(
        "/admissions/eligibility-check/",
        payload
      );

      if (error) {
        // Display actual backend error message
        const errorMessage =
          typeof error === "string"
            ? error
            : error?.message ||
              error?.error ||
              JSON.stringify(error) ||
              "Unknown error occurred";

        setResult({
          is_eligible: false,
          message: "Unable to check eligibility",
          details: { error: errorMessage },
          recommendations: [errorMessage],
        });
      } else {
        // Extract the actual data from the response
        const checkData = response?.data;

        if (checkData) {
          setResult({
            is_eligible: checkData.is_eligible,
            message: checkData.is_eligible
              ? "🎉 Congratulations! You are eligible for this program!"
              : "❌ Unfortunately, you do not meet the requirements",
            details: checkData.eligibility_details || {},
            recommendations: checkData.recommendations
              ? typeof checkData.recommendations === "string"
                ? checkData.recommendations.split("\n").filter((r) => r.trim())
                : checkData.recommendations
              : [],
            aggregate_score: checkData.aggregate_score,
          });
        } else {
          setResult({
            is_eligible: false,
            message: "Error: Invalid response from server",
            details: { error: "No data received" },
          });
        }
      }
    } catch (error) {
      console.error("Error checking eligibility:", error);
      setResult({
        is_eligible: false,
        message: "Error checking eligibility. Please try again.",
        details: { error: error.message || "Unknown error" },
      });
    } finally {
      setLoading(false);
    }
  };

  const getWhatsAppLink = async (e) => {
    e.preventDefault();
    setHelpdeskLoading(true);
    setHelpdeskResult(null);

    try {
      const { response, error } = await postData(
        "/admissions/whatsapp-helpdesk/get_link/",
        { application_id: applicationId }
      );

      if (error) {
        setHelpdeskResult({
          success: false,
          message: error.message || "Application ID not found",
        });
      } else if (response?.data) {
        setHelpdeskResult({
          success: true,
          ...response.data,
        });
      }
    } catch (error) {
      console.error("Error fetching WhatsApp link:", error);
      setHelpdeskResult({
        success: false,
        message: "Error connecting to server. Please try again.",
      });
    } finally {
      setHelpdeskLoading(false);
    }
  };

  const currentCriteria = criteria.find((c) => c.program === formData.program);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <GraduationCap className="w-12 h-12 text-red-600" />
            <h1 className="text-4xl font-bold text-gray-900">
              KNUST Admission Portal
            </h1>
          </div>
          <p className="text-lg text-gray-600">
            Check your eligibility for Computer Science & IT programs
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-lg mb-8 overflow-hidden">
          <div className="flex border-b">
            {[
              {
                id: "checker",
                label: "Eligibility Checker",
                icon: CheckCircle,
              },
              { id: "guides", label: "Admission Guides", icon: BookOpen },
              { id: "faqs", label: "FAQs", icon: HelpCircle },
              { id: "dates", label: "Important Dates", icon: Calendar },
              {
                id: "helpdesk",
                label: "WhatsApp Helpdesk",
                icon: MessageCircle,
              },
            ].map((tab) => {
              const isDisabled = 
                (tab.id === "checker" && isCheckerDisabled) ||
                (tab.id === "guides" && isGuidesDisabled);
              const disabledReason = 
                tab.id === "checker" && isCheckerDisabled
                  ? tabDisabledInfo.checker.eventTitle || "Admission results released"
                  : tab.id === "guides" && isGuidesDisabled
                  ? tabDisabledInfo.guides.eventTitle || "Application deadline passed"
                  : null;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  disabled={isDisabled}
                  title={isDisabled ? `Closed: ${disabledReason}` : tab.label}
                  className={`flex-1 flex items-center justify-center gap-2 py-4 px-6 font-medium transition-colors ${
                    isDisabled
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : activeTab === tab.id
                      ? "bg-red-600 text-white"
                      : "text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {isDisabled ? <Lock className="w-5 h-5" /> : <tab.icon className="w-5 h-5" />}
                  <span className="hidden md:inline">{tab.label}</span>
                  {isDisabled && <span className="hidden lg:inline text-xs ml-1">(Closed)</span>}
                </button>
              );
            })}
          </div>

          <div className="p-6">
            {/* Eligibility Checker Tab */}
            {activeTab === "checker" && (
              <div>
                <div className="mb-8 bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                  <div className="flex gap-3">
                    <Info className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-semibold text-blue-900 mb-2">
                        Before You Start
                      </h3>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>
                          • Enter your WASSCE grades exactly as they appear on
                          your results
                        </li>
                        <li>
                          • Aggregate = Best 3 core subjects (English, Math,
                          Science/Social) + Best 3 electives
                        </li>
                        <li>• You MUST provide at least 3 elective subjects</li>
                        <li>
                          • Lower aggregate scores are better (e.g., 6 is better
                          than 11)
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <form onSubmit={checkEligibility} className="space-y-6">
                  {/* Student Information */}
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-4">
                      Personal Information
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Full Name <span className="text-red-600">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.full_name}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              full_name: e.target.value,
                            })
                          }
                          placeholder="Enter your full name"
                          required
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email Address{" "}
                            <span className="text-red-600">*</span>
                          </label>
                          <input
                            type="email"
                            value={formData.email}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                email: e.target.value,
                              })
                            }
                            placeholder="your.email@example.com"
                            required
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Phone Number <span className="text-red-600">*</span>
                          </label>
                          <input
                            type="tel"
                            value={formData.phone}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                phone: e.target.value,
                              })
                            }
                            placeholder="0XX XXX XXXX"
                            required
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            SHS School Attended{" "}
                            <span className="text-red-600">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.shs_school}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                shs_school: e.target.value,
                              })
                            }
                            placeholder="e.g., Prempeh College"
                            required
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Year Completed{" "}
                            <span className="text-red-600">*</span>
                          </label>
                          <input
                            type="number"
                            value={formData.completion_year}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                completion_year: e.target.value,
                              })
                            }
                            placeholder="e.g., 2024"
                            min="2000"
                            max="2030"
                            required
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Program Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Program
                    </label>
                    <select
                      value={formData.program}
                      onChange={(e) =>
                        setFormData({ ...formData, program: e.target.value })
                      }
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    >
                      <option value="CS">BSc Computer Science</option>
                      <option value="IT">BSc Information Technology</option>
                    </select>
                  </div>

                  {/* Admission Type Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Admission Type
                    </label>
                    <select
                      value={formData.admission_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          admission_type: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    >
                      <option value="REGULAR">
                        Regular Admission (Merit-based)
                      </option>
                      <option value="FEE_PAYING">
                        Fee-Paying/Parallel Program (Relaxed requirements,
                        higher fees)
                      </option>
                      <option value="MATURE">
                        Mature Applicant (25+ with 3 years experience)
                      </option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {formData.admission_type === "REGULAR" &&
                        "Most competitive pathway with standard fees"}
                      {formData.admission_type === "FEE_PAYING" &&
                        "Alternative pathway with slightly relaxed requirements but higher tuition fees"}
                      {formData.admission_type === "MATURE" &&
                        "For mature applicants aged 25+ with relevant work experience"}
                    </p>
                  </div>

                  {/* Current Criteria Display */}
                  {currentCriteria && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                      <h4 className="font-semibold text-amber-900 mb-2">
                        {currentCriteria.program === "CS"
                          ? "Computer Science"
                          : "Information Technology"}{" "}
                        Requirements ({currentCriteria.academic_year})
                      </h4>
                      <div className="text-sm text-amber-800 space-y-1">
                        <p>
                          • Aggregate Cutoff: {currentCriteria.aggregate_cutoff}{" "}
                          or better
                        </p>
                        <p>
                          • Core Math: {currentCriteria.core_math_min_grade} or
                          better
                        </p>
                        <p>
                          • English: {currentCriteria.english_min_grade} or
                          better
                        </p>
                        <p>
                          • Integrated Science:{" "}
                          {currentCriteria.integrated_science_min_grade} or
                          better
                        </p>
                        <p>
                          • Elective Math:{" "}
                          {currentCriteria.elective_math_required
                            ? `${currentCriteria.elective_math_min_grade} or better (Required)`
                            : "Not required"}
                        </p>
                        <p>
                          • Physics:{" "}
                          {currentCriteria.physics_required
                            ? `${currentCriteria.physics_min_grade} or better (Required)`
                            : "Recommended"}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Core Subjects */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <span className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center text-sm">
                        1
                      </span>
                      Core Subjects (Required)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        "core_mathematics",
                        "english_language",
                        "integrated_science",
                        "social_studies",
                      ].map((subject) => (
                        <div key={subject}>
                          <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                            {subject.replace(/_/g, " ")}
                          </label>
                          <select
                            value={formData.subjects[subject]}
                            onChange={(e) =>
                              handleSubjectChange(subject, e.target.value)
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            required
                          >
                            <option value="">Select grade</option>
                            {gradeOptions.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Elective Subjects */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <span className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center text-sm">
                        2
                      </span>
                      Elective Subjects
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        "elective_mathematics",
                        "physics",
                        "chemistry",
                        "biology",
                        "elective_ict",
                      ].map((subject) => (
                        <div key={subject}>
                          <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                            {subject.replace(/_/g, " ")}
                          </label>
                          <select
                            value={formData.subjects[subject]}
                            onChange={(e) =>
                              handleSubjectChange(subject, e.target.value)
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          >
                            <option value="">Select grade (optional)</option>
                            {gradeOptions.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </div>
                      ))}

                      {/* Other Elective 1 */}
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Other Elective 1 (Specify Subject Name)
                        </label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <input
                            type="text"
                            placeholder="e.g., Technical Drawing, Geography"
                            value={formData.subjects.other_elective_1_name}
                            onChange={(e) =>
                              handleSubjectChange(
                                "other_elective_1_name",
                                e.target.value
                              )
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                          <select
                            value={formData.subjects.other_elective_1}
                            onChange={(e) =>
                              handleSubjectChange(
                                "other_elective_1",
                                e.target.value
                              )
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          >
                            <option value="">Select grade (optional)</option>
                            {gradeOptions.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Other Elective 2 */}
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Other Elective 2 (Specify Subject Name)
                        </label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <input
                            type="text"
                            placeholder="e.g., Economics, Literature"
                            value={formData.subjects.other_elective_2_name}
                            onChange={(e) =>
                              handleSubjectChange(
                                "other_elective_2_name",
                                e.target.value
                              )
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          />
                          <select
                            value={formData.subjects.other_elective_2}
                            onChange={(e) =>
                              handleSubjectChange(
                                "other_elective_2",
                                e.target.value
                              )
                            }
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          >
                            <option value="">Select grade (optional)</option>
                            {gradeOptions.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <motion.button
                    type="submit"
                    disabled={loading}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-red-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? "Checking..." : "Check Eligibility"}
                  </motion.button>
                </form>

                {/* Results */}
                {result && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`mt-8 p-6 rounded-lg border-l-4 ${
                      result.is_eligible
                        ? "bg-green-50 border-green-600"
                        : "bg-red-50 border-red-600"
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      {result.is_eligible ? (
                        <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-8 h-8 text-red-600 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <h3
                          className={`text-xl font-bold mb-2 ${
                            result.is_eligible
                              ? "text-green-900"
                              : "text-red-900"
                          }`}
                        >
                          {result.message}
                        </h3>

                        {result.details && (
                          <div className="space-y-4 mt-4">
                            {/* Show error details if present */}
                            {result.details.error && (
                              <div className="bg-red-100 border border-red-300 rounded-lg p-4">
                                <p className="font-semibold text-red-900 mb-2">
                                  Error Details:
                                </p>
                                <p className="text-sm text-red-800">
                                  {result.details.error}
                                </p>
                              </div>
                            )}

                            {/* Aggregate Score Display */}
                            {result.aggregate_score && (
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <p className="font-semibold text-blue-900 mb-2">
                                  Your Aggregate Score
                                </p>
                                <p className="text-3xl font-bold text-blue-800 mb-2">
                                  {result.aggregate_score}
                                </p>
                                {result.details.criteria_used && (
                                  <p className="text-sm text-blue-700">
                                    Required:{" "}
                                    {
                                      result.details.criteria_used
                                        .aggregate_cutoff
                                    }{" "}
                                    or better
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Aggregate Calculation Breakdown */}
                            {result.details.aggregate_calculation && (
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                <p className="font-semibold text-gray-900 mb-3">
                                  Aggregate Calculation (Best 3 Core + Best 3
                                  Electives)
                                </p>

                                {/* Core Subjects Used */}
                                <div className="mb-3">
                                  <p className="text-sm font-medium text-gray-700 mb-2">
                                    Core Subjects:
                                  </p>
                                  <div className="space-y-1">
                                    {result.details.aggregate_calculation.core_used?.map(
                                      (item, idx) => (
                                        <div
                                          key={idx}
                                          className="flex justify-between text-sm"
                                        >
                                          <span>{item.subject}</span>
                                          <span className="font-semibold">
                                            {item.grade} ({item.points} points)
                                          </span>
                                        </div>
                                      )
                                    )}
                                  </div>
                                </div>

                                {/* Electives Used */}
                                <div>
                                  <p className="text-sm font-medium text-gray-700 mb-2">
                                    Elective Subjects:
                                  </p>
                                  <div className="space-y-1">
                                    {result.details.aggregate_calculation.electives_used?.map(
                                      (item, idx) => (
                                        <div
                                          key={idx}
                                          className="flex justify-between text-sm"
                                        >
                                          <span>{item.subject}</span>
                                          <span className="font-semibold">
                                            {item.grade} ({item.points} points)
                                          </span>
                                        </div>
                                      )
                                    )}
                                  </div>
                                </div>

                                <div className="mt-3 pt-3 border-t border-gray-300">
                                  <div className="flex justify-between font-bold text-gray-900">
                                    <span>Total Aggregate:</span>
                                    <span>
                                      {
                                        result.details.aggregate_calculation
                                          .total
                                      }{" "}
                                      points
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}

                            {result.details.aggregate_score &&
                              !result.details.aggregate_calculation && (
                                <div>
                                  <p className="font-semibold text-gray-900">
                                    Your Aggregate Score
                                  </p>
                                  <p className="text-2xl font-bold text-gray-800">
                                    {result.details.aggregate_score}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    Required: {result.details.cutoff} or better
                                  </p>
                                </div>
                              )}

                            {result.details.breakdown && (
                              <div>
                                <p className="font-semibold text-gray-900 mb-2">
                                  Subject Breakdown
                                </p>
                                <div className="space-y-2">
                                  {Object.entries(result.details.breakdown).map(
                                    ([subject, info]) => (
                                      <div
                                        key={subject}
                                        className="flex items-center justify-between text-sm"
                                      >
                                        <span className="capitalize">
                                          {subject.replace(/_/g, " ")}
                                        </span>
                                        <span
                                          className={`font-semibold ${
                                            info.meets_requirement
                                              ? "text-green-600"
                                              : "text-red-600"
                                          }`}
                                        >
                                          {info.grade}{" "}
                                          {info.meets_requirement ? "✓" : "✗"}
                                        </span>
                                      </div>
                                    )
                                  )}
                                </div>
                              </div>
                            )}

                            {result.recommendations &&
                              result.recommendations.length > 0 && (
                                <div>
                                  <p className="font-semibold text-gray-900 mb-2">
                                    <AlertCircle className="w-5 h-5 inline mr-2" />
                                    Recommendations
                                  </p>
                                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                    {result.recommendations.map((rec, idx) => (
                                      <li key={idx}>{rec}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                          </div>
                        )}

                        {result.is_eligible && (
                          <div className="mt-6">
                            <a
                              href="https://apps.knust.edu.gh/admissions/apply"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                            >
                              Proceed to KNUST Portal
                              <ExternalLink className="w-5 h-5" />
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* Admission Guides Tab */}
            {activeTab === "guides" && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Step-by-Step Admission Guides
                </h2>
                {guidelines.length === 0 ? (
                  <p className="text-gray-600">Loading guides...</p>
                ) : (
                  guidelines
                    .sort((a, b) => a.order - b.order)
                    .map((guide, idx) => (
                      <motion.div
                        key={guide.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-gradient-to-r from-white to-gray-50 border-2 border-gray-200 hover:border-red-300 rounded-xl p-6 hover:shadow-xl transition-all duration-300"
                      >
                        <div className="flex items-start gap-4">
                          <span className="w-12 h-12 bg-gradient-to-br from-red-600 to-red-700 text-white rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-lg">
                            {guide.order}
                          </span>
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                              {guide.title}
                              <BookOpen className="w-5 h-5 text-red-600" />
                            </h3>
                            <div className="bg-white rounded-lg p-4 mb-4 border border-gray-100 shadow-sm">
                              <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line leading-relaxed">
                                {guide.content}
                              </div>
                            </div>
                            {guide.portal_url && (
                              <motion.a
                                href={guide.portal_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer"
                              >
                                <ExternalLink className="w-5 h-5" />
                                Visit KNUST Portal
                              </motion.a>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))
                )}
              </div>
            )}

            {/* FAQs Tab */}
            {activeTab === "faqs" && (
              <div className="space-y-4">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Frequently Asked Questions
                </h2>
                {faqs.length === 0 ? (
                  <p className="text-gray-600">Loading FAQs...</p>
                ) : (
                  faqs
                    .sort((a, b) => a.order - b.order)
                    .map((faq, idx) => (
                      <motion.div
                        key={faq.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        className="bg-white border border-gray-200 rounded-lg p-6"
                      >
                        <h3 className="font-semibold text-gray-900 mb-2 flex items-start gap-2">
                          <HelpCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                          {faq.question}
                        </h3>
                        <p className="text-gray-700 ml-7">{faq.answer}</p>
                      </motion.div>
                    ))
                )}
              </div>
            )}

            {/* Important Dates Tab */}
            {activeTab === "dates" && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Important Dates
                </h2>
                {dates.upcoming?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Upcoming Events
                    </h3>
                    <div className="space-y-4">
                      {dates.upcoming.map((date, idx) => (
                        <motion.div
                          key={date.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="bg-blue-50 border-l-4 border-blue-600 rounded-lg p-4"
                        >
                          <div className="flex items-start gap-4">
                            <Calendar className="w-6 h-6 text-blue-600 flex-shrink-0" />
                            <div>
                              <h4 className="font-semibold text-blue-900">
                                {date.title}
                              </h4>
                              <p className="text-sm text-blue-800 mt-1">
                                {date.description}
                              </p>
                              <p className="text-sm font-medium text-blue-900 mt-2">
                                {new Date(date.event_date).toLocaleDateString(
                                  "en-US",
                                  {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                  }
                                )}
                              </p>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {dates.past?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Past Events
                    </h3>
                    <div className="space-y-4 opacity-60">
                      {dates.past.map((date) => (
                        <div
                          key={date.id}
                          className="bg-gray-50 border-l-4 border-gray-400 rounded-lg p-4"
                        >
                          <div className="flex items-start gap-4">
                            <Calendar className="w-6 h-6 text-gray-600 flex-shrink-0" />
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {date.title}
                              </h4>
                              <p className="text-sm text-gray-700 mt-1">
                                {date.description}
                              </p>
                              <p className="text-sm font-medium text-gray-900 mt-2">
                                {new Date(date.event_date).toLocaleDateString(
                                  "en-US",
                                  {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                  }
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* WhatsApp Helpdesk Tab */}
            {activeTab === "helpdesk" && (
              <div className="max-w-2xl mx-auto">
                <div className="text-center mb-8">
                  <MessageCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    WhatsApp Helpdesk
                  </h2>
                  <p className="text-gray-600">
                    Enter your Application ID to get access to our WhatsApp
                    support group
                  </p>
                </div>

                <form onSubmit={getWhatsAppLink} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Application ID
                    </label>
                    <input
                      type="text"
                      value={applicationId}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, "");
                        setApplicationId(value);
                      }}
                      placeholder="Enter your Application ID"
                      required
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                    <p className="text-sm text-gray-500 mt-2">
                      Enter your Application ID as provided by KNUST
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={helpdeskLoading}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {helpdeskLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Verifying...</span>
                      </>
                    ) : (
                      <>
                        <MessageCircle className="w-5 h-5" />
                        <span>Get WhatsApp Link</span>
                      </>
                    )}
                  </button>
                </form>

                {/* Result Display */}
                {helpdeskResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6"
                  >
                    {helpdeskResult.success ? (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <div className="flex items-start gap-3 mb-4">
                          <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                          <div className="flex-1">
                            <h3 className="font-semibold text-green-900 text-lg">
                              Welcome, {helpdeskResult.student_name}!
                            </h3>
                            <p className="text-sm text-green-700 mt-1">
                              Program: {helpdeskResult.program_display || helpdeskResult.programme}
                            </p>
                          </div>
                        </div>

                        <div className="bg-white border border-green-200 rounded-lg p-4 mb-4">
                          <p className="text-gray-700 mb-3">
                            {helpdeskResult.message}
                          </p>

                          {/* Group Description */}
                          {helpdeskResult.group_description && (
                            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4 rounded">
                              <p className="text-sm text-blue-900 font-medium mb-1">
                                About this group:
                              </p>
                              <p className="text-sm text-blue-800">
                                {helpdeskResult.group_description}
                              </p>
                            </div>
                          )}

                          <button
                            onClick={() => {
                              const link = helpdeskResult.whatsapp_group_link;
                              // Try to open in new window first
                              const newWindow = window.open(link, '_blank', 'noopener,noreferrer');
                              
                              // If popup was blocked or failed, try direct navigation
                              if (!newWindow) {
                                window.location.href = link;
                              }
                            }}
                            className="w-full inline-flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                          >
                            <MessageCircle className="w-5 h-5" />
                            <span>Join WhatsApp Group</span>
                            <ExternalLink className="w-4 h-4" />
                          </button>
                          
                          <p className="text-xs text-gray-500 mt-3">
                            💡 Click the button above to join directly. If it doesn&apos;t work, try using a different browser or refresh the page.
                          </p>
                        </div>

                        <div className="text-sm text-green-700">
                          <p className="font-medium mb-1">Important Notes:</p>
                          <ul className="list-disc list-inside space-y-1 text-green-600">
                            <li>Be respectful in the group chat</li>
                            <li>Ask questions related to admissions only</li>
                            <li>Response time: 24-48 hours</li>
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                        <div className="flex items-start gap-3">
                          <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                          <div>
                            <h3 className="font-semibold text-red-900 text-lg">
                              Application ID Not Found
                            </h3>
                            <p className="text-red-700 mt-2">
                              {helpdeskResult.message}
                            </p>
                            <div className="mt-4 text-sm text-red-600">
                              <p className="font-medium mb-1">Please ensure:</p>
                              <ul className="list-disc list-inside space-y-1">
                                <li>You entered the correct Application ID</li>
                                <li>Your Application ID is active</li>
                                <li>Contact support if the problem persists</li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer Links */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg shadow-lg p-6 mt-8"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Links
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                label: "Apply Now",
                url: "https://apps.knust.edu.gh/admissions/apply",
              },
              {
                label: "Register Account",
                url: "https://apps.knust.edu.gh/admissions/apply/Account/Register",
              },
              {
                label: "Check Status",
                url: "https://apps.knust.edu.gh/admissions/check/Home/Undergraduates",
              },
              {
                label: "Sign In",
                url: "https://apps.knust.edu.gh/admissions/apply/Account/SignIn",
              },
            ].map((link) => (
              <a
                key={link.label}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg transition-colors group"
              >
                <span className="font-medium text-gray-700 group-hover:text-red-600">
                  {link.label}
                </span>
                <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-red-600" />
              </a>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AdmissionPage;
