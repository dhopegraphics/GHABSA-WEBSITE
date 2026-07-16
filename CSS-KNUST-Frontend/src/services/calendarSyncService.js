/**
 * Calendar Sync Service
 * Handles calendar subscription and download functionality
 */

import { BACKEND_HOST } from "../utils/config";

// Calendar types available
export const CALENDAR_TYPES = {
  classes: { name: "Class Timetable", icon: "📚", color: "blue" },
  exams: { name: "Exam Schedule", icon: "📝", color: "red" },
  events: { name: "My Events", icon: "🎉", color: "purple" },
  full: { name: "Full Academic Calendar", icon: "📅", color: "indigo" },
};

/**
 * Fetch calendar subscription URLs from the backend
 */
export const getCalendarSubscriptionUrls = async (axiosInstance, accessToken) => {
  try {
    const response = await axiosInstance.get(
      `${BACKEND_HOST}/calendar/subscription-urls/`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Failed to fetch calendar URLs:", error);
    throw error;
  }
};

/**
 * Download calendar as .ics file
 */
export const downloadCalendar = async (axiosInstance, accessToken, calendarType) => {
  try {
    const response = await axiosInstance.get(
      `${BACKEND_HOST}/calendar/download/${calendarType}/`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
        responseType: "blob",
      }
    );

    // Create download link
    const blob = new Blob([response.data], { type: "text/calendar" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${calendarType}_calendar.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    return true;
  } catch (error) {
    console.error("Failed to download calendar:", error);
    throw error;
  }
};

/**
 * Download public events calendar (no auth required)
 */
export const downloadPublicEventsCalendar = async () => {
  try {
    const response = await fetch(
      `${BACKEND_HOST}/calendar/public/events/?download=true`
    );
    
    if (!response.ok) throw new Error("Failed to download");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "css_knust_events.ics";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    return true;
  } catch (error) {
    console.error("Failed to download public events calendar:", error);
    throw error;
  }
};

/**
 * Download single event as .ics file
 */
export const downloadSingleEvent = async (eventId) => {
  try {
    const response = await fetch(
      `${BACKEND_HOST}/calendar/event/${eventId}/`
    );
    
    if (!response.ok) throw new Error("Failed to download event");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `event_${eventId}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    return true;
  } catch (error) {
    console.error("Failed to download event:", error);
    throw error;
  }
};

/**
 * Open webcal URL (for iOS/macOS native subscription)
 * Note: This only works with publicly accessible URLs, not localhost
 */
export const openWebcalUrl = (webcalUrl) => {
  // Check if we're on localhost - webcal won't work
  if (webcalUrl.includes('localhost') || webcalUrl.includes('127.0.0.1')) {
    return { success: false, reason: 'localhost' };
  }
  window.location.href = webcalUrl;
  return { success: true };
};

/**
 * Check if we're in local development
 */
export const isLocalDevelopment = () => {
  return window.location.hostname === 'localhost' || 
         window.location.hostname === '127.0.0.1';
};

/**
 * Copy subscription URL to clipboard
 */
export const copySubscriptionUrl = async (url) => {
  try {
    await navigator.clipboard.writeText(url);
    return true;
  } catch (error) {
    console.error("Failed to copy URL:", error);
    throw error;
  }
};

/**
 * Detect user's platform for appropriate instructions
 */
export const detectPlatform = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (/iphone|ipad|ipod/.test(userAgent)) {
    return "ios";
  } else if (/macintosh|mac os x/.test(userAgent)) {
    return "macos";
  } else if (/android/.test(userAgent)) {
    return "android";
  } else if (/windows/.test(userAgent)) {
    return "windows";
  }
  return "other";
};

/**
 * Get platform-specific instructions
 */
export const getPlatformInstructions = (platform, isLocal = false) => {
  // For local development, always show download instructions
  if (isLocal) {
    return {
      title: "Local Development Mode",
      steps: [
        "Download the .ics file using the button below",
        "Double-click the downloaded file to open in Calendar",
        "Click 'Add' or 'Import' to add the events",
        "Note: Live subscription requires a public server URL",
      ],
      useWebcal: false,
      isLocal: true,
    };
  }

  const instructions = {
    ios: {
      title: "Add to iPhone/iPad",
      steps: [
        "Tap the subscription button below",
        "iOS will prompt you to subscribe to the calendar",
        "Tap 'Subscribe' to confirm",
        "Your calendar will sync automatically",
      ],
      useWebcal: true,
    },
    macos: {
      title: "Add to Mac Calendar",
      steps: [
        "Click the subscription button below",
        "Calendar app will open with the subscription",
        "Click 'Subscribe' to confirm",
        "Events will sync automatically",
      ],
      useWebcal: true,
    },
    android: {
      title: "Add to Google Calendar",
      steps: [
        "Download the .ics file",
        "Open Google Calendar on your phone",
        "Go to Settings → Import",
        "Select the downloaded .ics file",
      ],
      useWebcal: false,
    },
    windows: {
      title: "Add to Outlook/Windows",
      steps: [
        "Download the .ics file",
        "Open the file with Outlook or Calendar app",
        "Confirm to add all events",
        "For live sync, use 'Subscribe from web' option",
      ],
      useWebcal: false,
    },
    other: {
      title: "Add to Calendar",
      steps: [
        "Download the .ics file below",
        "Open your calendar application",
        "Import the downloaded file",
      ],
      useWebcal: false,
    },
  };
  
  return instructions[platform] || instructions.other;
};
