/**
 * Device Fingerprinting Utility
 * Generates a unique fingerprint based on browser and device characteristics
 * Used for preventing duplicate anonymous votes
 * 
 * IMPORTANT: Fingerprints must be DETERMINISTIC - same device should always
 * produce the same fingerprint for reliable duplicate detection.
 */

// Deterministic hash function - MUST NOT include random or timestamp values
// Uses crypto.subtle if available (HTTPS), falls back to djb2 hash for HTTP/mobile
const hashString = async (str) => {
  // Check if crypto.subtle is available (requires secure context - HTTPS)
  if (window.crypto && window.crypto.subtle) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(str);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (e) {
      console.warn('crypto.subtle failed, using fallback hash:', e);
    }
  }
  
  // Fallback: djb2 hash - DETERMINISTIC (no random/timestamp!)
  // Same input ALWAYS produces same output
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & 0xFFFFFFFF; // Keep as 32-bit integer
  }
  // Convert to hex and ensure consistent length
  const hexHash = Math.abs(hash).toString(16).padStart(8, '0');
  return `fp_${hexHash}`;
};

// Get canvas fingerprint
const getCanvasFingerprint = () => {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 200;
    canvas.height = 50;
    
    // Draw text with specific font
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('CSS-KNUST-Voting', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('CSS-KNUST-Voting', 4, 17);
    
    return canvas.toDataURL();
  } catch {
    return 'canvas-not-available';
  }
};

// Get WebGL fingerprint
const getWebGLFingerprint = () => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) return 'webgl-not-available';
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = debugInfo 
      ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) 
      : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo 
      ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) 
      : gl.getParameter(gl.RENDERER);
    
    return `${vendor}~${renderer}`;
  } catch {
    return 'webgl-error';
  }
};

// Collect browser characteristics
const collectBrowserData = () => {
  const data = {
    userAgent: navigator.userAgent,
    language: navigator.language,
    languages: navigator.languages?.join(',') || '',
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency || 0,
    deviceMemory: navigator.deviceMemory || 0,
    screenWidth: screen.width,
    screenHeight: screen.height,
    screenColorDepth: screen.colorDepth,
    screenPixelRatio: window.devicePixelRatio || 1,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
    touchSupport: 'ontouchstart' in window,
    cookiesEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack || 'unknown',
    plugins: Array.from(navigator.plugins || []).map(p => p.name).join(','),
  };
  
  return data;
};

// Get or create session ID with localStorage fallback for better persistence
// Priority: localStorage > sessionStorage > memory fallback
const STORAGE_KEY = 'css_voting_session_id';
let memorySessionId = null; // In-memory fallback

const getSessionId = () => {
  // Try to return existing memory session first (fastest)
  if (memorySessionId) {
    return memorySessionId;
  }
  
  // Try localStorage first (persists across browser sessions)
  try {
    let sessionId = localStorage.getItem(STORAGE_KEY);
    if (sessionId) {
      memorySessionId = sessionId;
      return sessionId;
    }
  } catch {
    // localStorage blocked (private mode, etc.)
  }
  
  // Try sessionStorage (persists within tab session)
  try {
    let sessionId = sessionStorage.getItem(STORAGE_KEY);
    if (sessionId) {
      memorySessionId = sessionId;
      return sessionId;
    }
  } catch {
    // sessionStorage blocked
  }
  
  // Generate new session ID
  const newSessionId = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 11)}`;
  
  // Try to persist in localStorage
  try {
    localStorage.setItem(STORAGE_KEY, newSessionId);
  } catch {
    // Try sessionStorage as fallback
    try {
      sessionStorage.setItem(STORAGE_KEY, newSessionId);
    } catch {
      console.warn('All storage blocked - session will be memory-only');
    }
  }
  
  memorySessionId = newSessionId;
  return newSessionId;
};

// Generate the complete device fingerprint
// Uses stable device characteristics for deterministic output
export const generateDeviceFingerprint = async () => {
  try {
    const browserData = collectBrowserData();
    const canvasFingerprint = getCanvasFingerprint();
    const webglFingerprint = getWebGLFingerprint();
    
    // Combine all data into a single string - MUST be deterministic
    const fingerprintData = JSON.stringify({
      ...browserData,
      canvas: canvasFingerprint.substring(0, 100), // Truncate for efficiency
      webgl: webglFingerprint,
    });
    
    // Hash the combined data
    const fingerprint = await hashString(fingerprintData);
    
    return fingerprint;
  } catch (error) {
    console.error('Error generating device fingerprint:', error);
    // Fallback to simpler but still DETERMINISTIC fingerprint
    const fallbackData = `${navigator.userAgent}|${screen.width}x${screen.height}|${new Date().getTimezoneOffset()}|${navigator.language}`;
    return await hashString(fallbackData);
  }
};

// Get session ID for additional tracking
export const getVotingSessionId = () => {
  return getSessionId();
};

// Combined function to get both fingerprint and session ID
// Includes timeout protection for slow devices
export const getVotingIdentifiers = async (timeoutMs = 5000) => {
  try {
    // Race between fingerprint generation and timeout
    const fingerprintPromise = generateDeviceFingerprint();
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Fingerprint generation timeout')), timeoutMs)
    );
    
    const deviceFingerprint = await Promise.race([fingerprintPromise, timeoutPromise]);
    const sessionId = getSessionId();
    
    return {
      device_fingerprint: deviceFingerprint,
      session_id: sessionId
    };
  } catch (error) {
    console.warn('getVotingIdentifiers error:', error.message);
    // Return session ID even if fingerprint fails
    return {
      device_fingerprint: '', // Empty fingerprint, backend will rely on other methods
      session_id: getSessionId()
    };
  }
};

export default {
  generateDeviceFingerprint,
  getVotingSessionId,
  getVotingIdentifiers
};
