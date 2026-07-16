import { useState, useEffect } from "react";
import { X, Bell, CheckCircle, Smartphone } from "lucide-react";
import PropTypes from "prop-types";

const NotificationPermissionPrompt = ({
  onPermissionGranted,
  onPermissionDenied,
  onClose,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isRequestingPermission, setIsRequestingPermission] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Detect iOS
    const iOS =
      /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(iOS);

    // iOS doesn't support web push notifications
    if (iOS) {
      // Show iOS message after delay
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 2000);
      return () => clearTimeout(timer);
    }

    // Check if browser supports notifications
    if (!("Notification" in window)) {
      console.warn("This browser does not support notifications");
      return;
    }

    // Check if permission is already granted or denied
    if (Notification.permission === "granted") {
      onPermissionGranted?.();
      return;
    }

    if (Notification.permission === "denied") {
      return; // Don't show prompt if user already denied
    }

    // Show the prompt after a short delay (user experience)
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 2000);

    return () => clearTimeout(timer);
  }, [onPermissionGranted]);

  const handleAllowNotifications = async () => {
    setIsRequestingPermission(true);

    try {
      const permission = await Notification.requestPermission();

      if (permission === "granted") {
        console.log("Notification permission granted");
        onPermissionGranted?.();
        setIsVisible(false);
        onClose?.();
      } else {
        console.log("Notification permission denied");
        onPermissionDenied?.();
        setIsVisible(false);
        onClose?.();
      }
    } catch (error) {
      console.error("Error requesting notification permission:", error);
      onPermissionDenied?.();
    } finally {
      setIsRequestingPermission(false);
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
    onClose?.();
    // Store dismissal in localStorage to avoid showing again immediately
    localStorage.setItem(
      "notification-prompt-dismissed",
      Date.now().toString()
    );
  };

  if (!isVisible) return null;

  // iOS-specific message
  if (isIOS) {
    return (
      <div className="fixed top-4 right-4 z-50 max-w-md animate-slide-in-right">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-white">
              <Smartphone className="w-5 h-5" />
              <h3 className="font-semibold">Get Notifications</h3>
            </div>
            <button
              onClick={handleDismiss}
              className="text-white hover:bg-white/20 rounded-full p-1 transition-colors"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              📱 <strong>iOS users:</strong> Safari on iPhone doesn't support
              web notifications.
            </p>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                To receive push notifications on your iPhone:
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span>
                    Download the <strong>BIO-CHEM KNUST SMART app</strong> from the
                    App Store - but <strong>NOT AVAILABLE YET!</strong>
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span>
                    Get instant notifications for classes, exams, and
                    announcements
                  </span>
                </li>
              </ul>
            </div>

            <a
              href="https://apps.apple.com/app/biochem-knust"
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium text-center transition-colors"
            >
              Download iOS App
            </a>

            <button
              onClick={handleDismiss}
              className="w-full mt-2 px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Continue with Web
            </button>

            <p className="text-xs text-gray-500 dark:text-gray-500 mt-3 text-center">
              This is an Apple limitation, not a bug 😊
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md animate-slide-in-right">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Bell className="w-5 h-5" />
            <h3 className="font-semibold">Stay Updated</h3>
          </div>
          <button
            onClick={handleDismiss}
            className="text-white hover:bg-white/20 rounded-full p-1 transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Enable notifications to receive instant updates about:
          </p>

          <ul className="space-y-2 mb-4">
            <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Upcoming classes and exams</span>
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Important announcements and events</span>
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Assignment deadlines and reminders</span>
            </li>
          </ul>

          <div className="flex gap-2">
            <button
              onClick={handleAllowNotifications}
              disabled={isRequestingPermission}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRequestingPermission ? "Requesting..." : "Allow Notifications"}
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Not Now
            </button>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-500 mt-3 text-center">
            You can change this anytime in your browser settings
          </p>
        </div>
      </div>
    </div>
  );
};

NotificationPermissionPrompt.propTypes = {
  onPermissionGranted: PropTypes.func,
  onPermissionDenied: PropTypes.func,
  onClose: PropTypes.func,
};

export default NotificationPermissionPrompt;
