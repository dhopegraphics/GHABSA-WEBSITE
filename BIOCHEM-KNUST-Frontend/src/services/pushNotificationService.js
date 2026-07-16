/**
 * Web Push Notification Service
 * Handles browser push notification subscriptions
 */

const VAPID_PUBLIC_KEY_ENDPOINT = "/notifications/vapid-public-key/";
const REGISTER_DEVICE_ENDPOINT = "/notifications/devices/register/";

/**
 * Convert base64 string to Uint8Array (required for VAPID key)
 */
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Detect if user is on iOS (iPhone/iPad)
 * iOS does not support web push notifications
 */
export function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

/**
 * Check if browser supports push notifications
 */
export function isPushNotificationSupported() {
  // iOS Safari does not support web push notifications
  if (isIOS()) {
    return false;
  }

  return (
    "Notification" in window &&
    "serviceWorker" in navigator &&
    "PushManager" in window
  );
}

/**
 * Get current notification permission status
 */
export function getNotificationPermissionStatus() {
  if (!isPushNotificationSupported()) {
    return "unsupported";
  }
  return Notification.permission;
}

/**
 * Request notification permission from user
 */
export async function requestNotificationPermission() {
  if (!isPushNotificationSupported()) {
    throw new Error("Push notifications are not supported in this browser");
  }

  const permission = await Notification.requestPermission();
  return permission;
}

/**
 * Get VAPID public key from server
 */
async function getVapidPublicKey(axiosInstance) {
  try {
    const response = await axiosInstance.get(VAPID_PUBLIC_KEY_ENDPOINT);
    console.log("VAPID key response:", response.data);

    if (!response.data || !response.data.publicKey) {
      throw new Error("Invalid VAPID key response from server");
    }

    return response.data.publicKey;
  } catch (error) {
    console.error("Error fetching VAPID public key:", error);
    throw error;
  }
}

/**
 * Register service worker and subscribe to push notifications
 */
export async function subscribeToPushNotifications(axiosInstance) {
  if (!isPushNotificationSupported()) {
    throw new Error("Push notifications are not supported");
  }

  if (Notification.permission !== "granted") {
    throw new Error("Notification permission not granted");
  }

  try {
    // Register service worker
    const registration = await navigator.serviceWorker.register("/sw.js");
    console.log("Service Worker registered:", registration);

    // Wait for service worker to be ready
    await navigator.serviceWorker.ready;

    // Get VAPID public key from server
    const vapidPublicKey = await getVapidPublicKey(axiosInstance);
    console.log("VAPID public key received:", vapidPublicKey);

    if (!vapidPublicKey) {
      throw new Error("VAPID public key is empty or undefined");
    }

    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

    // Subscribe to push notifications
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey,
    });

    console.log("Push subscription created:", subscription);
    return subscription;
  } catch (error) {
    console.error("Error subscribing to push notifications:", error);
    throw error;
  }
}

/**
 * Register the push subscription with the backend
 */
export async function registerPushSubscription(subscription, axiosInstance) {
  try {
    const subscriptionData = {
      device_token: subscription.endpoint,
      platform: "web",
      device_name: getBrowserInfo(),
      web_subscription: subscription.toJSON(),
    };

    const response = await axiosInstance.post(
      REGISTER_DEVICE_ENDPOINT,
      subscriptionData
    );

    console.log("Push subscription registered with backend:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error registering push subscription:", error);
    throw error;
  }
}

/**
 * Get browser information for device name
 */
function getBrowserInfo() {
  const userAgent = navigator.userAgent;
  let browserName = "Unknown Browser";
  let osName = "Unknown OS";

  // Detect browser
  if (userAgent.includes("Firefox")) {
    browserName = "Firefox";
  } else if (userAgent.includes("Chrome")) {
    browserName = "Chrome";
  } else if (userAgent.includes("Safari")) {
    browserName = "Safari";
  } else if (userAgent.includes("Edge")) {
    browserName = "Edge";
  }

  // Detect OS
  if (userAgent.includes("Windows")) {
    osName = "Windows";
  } else if (userAgent.includes("Mac")) {
    osName = "macOS";
  } else if (userAgent.includes("Linux")) {
    osName = "Linux";
  } else if (userAgent.includes("Android")) {
    osName = "Android";
  } else if (userAgent.includes("iOS")) {
    osName = "iOS";
  }

  return `${browserName} on ${osName}`;
}

/**
 * Complete flow: Request permission, subscribe, and register
 */
export async function initializePushNotifications(axiosInstance) {
  try {
    // Check browser support
    if (!isPushNotificationSupported()) {
      throw new Error("Push notifications are not supported in this browser");
    }

    // Request permission
    const permission = await requestNotificationPermission();

    if (permission !== "granted") {
      throw new Error("Notification permission denied");
    }

    // Subscribe to push notifications
    const subscription = await subscribeToPushNotifications(axiosInstance);

    // Register with backend
    const registrationResult = await registerPushSubscription(
      subscription,
      axiosInstance
    );

    // Store subscription status
    localStorage.setItem("push-subscription-registered", "true");

    return {
      success: true,
      subscription,
      registration: registrationResult,
    };
  } catch (error) {
    console.error("Error initializing push notifications:", error);
    throw error;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPushNotifications() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      await subscription.unsubscribe();
      localStorage.removeItem("push-subscription-registered");
      console.log("Unsubscribed from push notifications");
      return true;
    }

    return false;
  } catch (error) {
    console.error("Error unsubscribing from push notifications:", error);
    throw error;
  }
}

/**
 * Check if user is already subscribed
 */
export async function isSubscribedToPush() {
  try {
    if (!isPushNotificationSupported()) {
      return false;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    return subscription !== null;
  } catch (error) {
    console.error("Error checking push subscription:", error);
    return false;
  }
}
