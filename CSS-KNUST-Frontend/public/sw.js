/**
 * Service Worker for Push Notifications
 * Handles incoming push notifications and user interactions
 */

// Listen for push events
self.addEventListener("push", function (event) {
  console.log("🔔🔔🔔 PUSH EVENT RECEIVED! 🔔🔔🔔");
  console.log("Event object:", event);
  console.log("Event.data:", event.data);

  // Try to read the data in different ways
  if (event.data) {
    console.log("Raw data text:", event.data.text());
    try {
      console.log("Data as JSON:", event.data.json());
    } catch (e) {
      console.error("Cannot parse as JSON:", e);
    }
  }

  if (!event.data) {
    console.warn("⚠️ Push event has no data");
    // Show a notification anyway so user knows something was received
    event.waitUntil(
      self.registration.showNotification("CSS KNUST - No Data", {
        body: "Received push but no data attached",
        icon: "/logo.png",
        tag: "no-data",
        requireInteraction: true,
      })
    );
    return;
  }

  try {
    const data = event.data.json();
    console.log("📦 Successfully parsed push data:", data);
    console.log("Title:", data.title);
    console.log("Body:", data.body);

    const title = data.title || "CSS KNUST (no title)";
    const options = {
      body: data.body || "You have a new notification (no body)",
      icon: data.icon || "/logo.png",
      badge: data.badge || "/badge-icon.png",
      tag: data.tag || "default",
      data: data.data || {},
      requireInteraction: true, // Make it stay until clicked
      vibrate: [200, 100, 200],
      actions: data.actions || [],
    };

    console.log("🔔 About to show notification with:", { title, options });

    // Show the notification
    const showPromise = self.registration.showNotification(title, options);

    showPromise
      .then(() => {
        console.log("✅✅✅ Notification shown successfully! ✅✅✅");
      })
      .catch((error) => {
        console.error("❌❌❌ Failed to show notification:", error);
      });

    event.waitUntil(showPromise);
  } catch (error) {
    console.error("❌ Error parsing push notification:", error);
    console.error("Error stack:", error.stack);

    // Show a default notification if parsing fails
    event.waitUntil(
      self.registration.showNotification("CSS KNUST - Parse Error", {
        body: "Received notification but couldn't parse data: " + error.message,
        icon: "/logo.png",
        requireInteraction: true,
      })
    );
  }
});

// Handle notification click
self.addEventListener("notificationclick", function (event) {
  console.log("Notification clicked:", event);

  event.notification.close();

  // Get the notification data
  const notificationData = event.notification.data || {};

  // Determine the URL to open
  let urlToOpen = "/";

  if (notificationData.url) {
    urlToOpen = notificationData.url;
  } else if (notificationData.screen) {
    // Map screen names to URLs
    const screenMap = {
      Dashboard: "/",
      Courses: "/courses",
      Timetable: "/timetable",
      Exams: "/exams",
      Notifications: "/notifications",
      Profile: "/profile",
    };
    urlToOpen = screenMap[notificationData.screen] || "/";
  }

  // Open or focus the app window
  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then(function (clientList) {
        // Check if there's already a window open
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (
            client.url === self.location.origin + urlToOpen &&
            "focus" in client
          ) {
            return client.focus();
          }
        }

        // If no window is open, open a new one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Handle notification close
self.addEventListener("notificationclose", function (event) {
  console.log("Notification closed:", event);

  // You can track notification dismissals here
  const notificationData = event.notification.data || {};

  // Optional: Send analytics or track the dismissal
  if (notificationData.trackClose) {
    // Send tracking data to your server
    fetch("/api/v1/notifications/track-close/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        notification_id: notificationData.id,
        closed_at: new Date().toISOString(),
      }),
    }).catch((err) => console.error("Error tracking notification close:", err));
  }
});

// Service worker activation
self.addEventListener("activate", function (event) {
  console.log("Service Worker activated");
  event.waitUntil(clients.claim());
});

// Service worker installation
self.addEventListener("install", function (event) {
  console.log("Service Worker installed");
  self.skipWaiting();
});

// Handle background sync (optional - for offline notification queue)
self.addEventListener("sync", function (event) {
  if (event.tag === "sync-notifications") {
    event.waitUntil(syncNotifications());
  }
});

async function syncNotifications() {
  // Implement sync logic here if needed
  console.log("Syncing notifications...");
}
