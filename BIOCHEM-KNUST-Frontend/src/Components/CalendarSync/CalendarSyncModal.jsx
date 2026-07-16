import React, { useState, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Download,
  X,
  Copy,
  Check,
  ExternalLink,
  Smartphone,
  Monitor,
  Loader,
  BookOpen,
  FileText,
  PartyPopper,
  CalendarDays,
} from "lucide-react";
import { UserContext } from "../../Context/UserContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import {
  getCalendarSubscriptionUrls,
  downloadCalendar,
  downloadPublicEventsCalendar,
  openWebcalUrl,
  copySubscriptionUrl,
  detectPlatform,
  getPlatformInstructions,
  isLocalDevelopment,
  CALENDAR_TYPES,
} from "../../services/calendarSyncService";

const CalendarTypeCard = ({
  type,
  typeInfo,
  urls,
  platform,
  isLocal,
  onDownload,
  onSubscribe,
  onCopy,
  loading,
  copied,
}) => {
  const instructions = getPlatformInstructions(platform, isLocal);
  const iconMap = {
    classes: BookOpen,
    exams: FileText,
    events: PartyPopper,
    full: CalendarDays,
  };
  const Icon = iconMap[type] || Calendar;

  const colorClasses = {
    blue: "from-blue-500 to-blue-600 border-blue-200 bg-blue-50",
    red: "from-red-500 to-red-600 border-red-200 bg-red-50",
    purple: "from-purple-500 to-purple-600 border-purple-200 bg-purple-50",
    indigo: "from-indigo-500 to-indigo-600 border-indigo-200 bg-indigo-50",
  };

  // Don't show subscribe button if local development
  const showSubscribe = instructions.useWebcal && urls?.webcal_url && !isLocal;

  return (
    <div
      className={`border-2 ${
        colorClasses[typeInfo.color].split(" ")[2]
      } rounded-xl p-4 ${colorClasses[typeInfo.color].split(" ")[3]}`}
    >
      <div className="flex items-center gap-3 mb-3">
        <div
          className={`p-2 rounded-lg bg-gradient-to-br ${
            colorClasses[typeInfo.color].split(" ")[0]
          } ${colorClasses[typeInfo.color].split(" ")[1]} text-white`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{typeInfo.name}</h4>
          <p className="text-xs text-gray-500">
            {type === "classes" && "Weekly class schedule with reminders"}
            {type === "exams" && "Exam dates with multiple reminders"}
            {type === "events" && "All upcoming BIO-CHEM KNUST events"}
            {type === "full" && "Everything in one calendar"}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {showSubscribe ? (
          <button
            onClick={() => onSubscribe(urls.webcal_url)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-gradient-to-r ${
              colorClasses[typeInfo.color].split(" ")[0]
            } ${
              colorClasses[typeInfo.color].split(" ")[1]
            } text-white font-medium text-sm hover:opacity-90 transition`}
          >
            <ExternalLink className="w-4 h-4" />
            Subscribe
          </button>
        ) : null}

        <button
          onClick={() => onDownload(type)}
          disabled={loading === type}
          className={`${showSubscribe ? 'flex-1' : 'flex-1'} flex items-center justify-center gap-2 py-2 px-3 rounded-lg ${
            !showSubscribe 
              ? `bg-gradient-to-r ${colorClasses[typeInfo.color].split(" ")[0]} ${colorClasses[typeInfo.color].split(" ")[1]} text-white` 
              : 'bg-white border-2 border-gray-200 text-gray-700'
          } font-medium text-sm hover:opacity-90 transition disabled:opacity-50`}
        >
          {loading === type ? (
            <Loader className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          Download .ics
        </button>

        {urls?.http_url && (
          <button
            onClick={() => onCopy(urls.http_url, type)}
            className="p-2 rounded-lg bg-white border-2 border-gray-200 text-gray-600 hover:bg-gray-50 transition"
            title="Copy subscription URL"
          >
            {copied === type ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export function CalendarSyncModal({
  isOpen,
  onClose,
  calendarTypes = ["classes", "exams", "events", "full"],
  title = "Sync to Phone Calendar",
}) {
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();

  const [urls, setUrls] = useState(null);
  const [loadingUrls, setLoadingUrls] = useState(false);
  const [loading, setLoading] = useState(null);
  const [copied, setCopied] = useState(null);
  const [error, setError] = useState(null);

  const platform = detectPlatform();
  const isLocal = isLocalDevelopment();
  const instructions = getPlatformInstructions(platform, isLocal);

  // Fetch subscription URLs when modal opens
  React.useEffect(() => {
    if (isOpen && user?.access && !urls) {
      fetchUrls();
    }
  }, [isOpen, user?.access]);

  const fetchUrls = async () => {
    setLoadingUrls(true);
    setError(null);
    try {
      const response = await getCalendarSubscriptionUrls(
        axiosInstance,
        user.access
      );
      if (response.success) {
        setUrls(response.data);
      }
    } catch (err) {
      setError("Failed to load calendar URLs. Please try again.");
    } finally {
      setLoadingUrls(false);
    }
  };

  const handleDownload = async (type) => {
    setLoading(type);
    setError(null);
    try {
      await downloadCalendar(axiosInstance, user.access, type);
    } catch (err) {
      setError("Failed to download calendar. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  const handleSubscribe = (webcalUrl) => {
    openWebcalUrl(webcalUrl);
  };

  const handleCopy = async (url, type) => {
    try {
      await copySubscriptionUrl(url);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      setError("Failed to copy URL");
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-t-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Calendar className="w-8 h-8" />
                <div>
                  <h2 className="text-xl font-bold">{title}</h2>
                  <p className="text-blue-100 text-sm">
                    Add schedules to your phone
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Local Development Warning */}
            {isLocal && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <span className="text-lg">⚠️</span>
                  <div>
                    <p className="font-medium text-amber-800">Local Development Mode</p>
                    <p className="text-sm text-amber-700">
                      Live calendar subscription requires a public server URL. 
                      Use the <strong>Download .ics</strong> option instead, or copy the URL for later use in production.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Platform Detection */}
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              {platform === "ios" || platform === "macos" ? (
                <Smartphone className="w-5 h-5 text-gray-600" />
              ) : (
                <Monitor className="w-5 h-5 text-gray-600" />
              )}
              <div className="flex-1">
                <p className="font-medium text-gray-900">
                  {instructions.title}
                </p>
                <p className="text-xs text-gray-500">
                  Detected: {platform.toUpperCase()}
                </p>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Loading State */}
            {loadingUrls ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader className="w-10 h-10 text-blue-600 animate-spin mb-3" />
                <p className="text-gray-600">Loading calendar options...</p>
              </div>
            ) : (
              <>
                {/* Calendar Type Cards */}
                <div className="space-y-3">
                  {calendarTypes.map((type) => (
                    <CalendarTypeCard
                      key={type}
                      type={type}
                      typeInfo={CALENDAR_TYPES[type]}
                      urls={urls?.[type]}
                      platform={platform}
                      isLocal={isLocal}
                      onDownload={handleDownload}
                      onSubscribe={handleSubscribe}
                      onCopy={handleCopy}
                      loading={loading}
                      copied={copied}
                    />
                  ))}
                </div>

                {/* Instructions */}
                <div className="border-t pt-4">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <span className="text-lg">📖</span>
                    How to add to your calendar
                  </h4>
                  <ol className="space-y-2">
                    {instructions.steps.map((step, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-2 text-sm text-gray-600"
                      >
                        <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Tips */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-800">
                    <strong>💡 Tip:</strong>{" "}
                    {isLocal
                      ? "Download the .ics file and double-click to add to your calendar app."
                      : instructions.useWebcal
                      ? "Use 'Subscribe' for automatic updates when schedules change."
                      : "For automatic updates, copy the subscription URL and add it to Google Calendar via 'Other calendars' → 'From URL'."}
                  </p>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Compact button for inline use
export function CalendarSyncButton({
  calendarTypes = ["full"],
  variant = "default",
  className = "",
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const variants = {
    default:
      "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white",
    outline:
      "bg-white border-2 border-blue-600 text-blue-600 hover:bg-blue-50",
    ghost: "text-blue-600 hover:bg-blue-50",
  };

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${variants[variant]} ${className}`}
      >
        <Calendar className="w-5 h-5" />
        <span>Sync to Calendar</span>
      </button>

      <CalendarSyncModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        calendarTypes={calendarTypes}
      />
    </>
  );
}

// Public events sync (no auth required)
export function PublicEventsCalendarButton({ className = "" }) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      await downloadPublicEventsCalendar();
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-purple-600 hover:bg-purple-700 text-white transition disabled:opacity-50 ${className}`}
    >
      {loading ? (
        <Loader className="w-5 h-5 animate-spin" />
      ) : (
        <Calendar className="w-5 h-5" />
      )}
      <span>Download Events Calendar</span>
    </button>
  );
}

export default CalendarSyncModal;
