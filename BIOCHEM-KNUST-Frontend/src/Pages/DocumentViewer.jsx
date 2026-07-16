import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Download,
  ExternalLink,
  X,
  FileText,
  Loader,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  Maximize,
} from "lucide-react";

export default function DocumentViewer() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [zoom, setZoom] = useState(100);
  const [iframeError, setIframeError] = useState(false);

  // Get file info from location state or URL params
  const urlParams = new URLSearchParams(location.search);
  const fileUrl = location.state?.fileUrl || urlParams.get("fileUrl") || "";
  const fileName =
    location.state?.fileName || urlParams.get("fileName") || "Document";
  const fileType = location.state?.fileType || urlParams.get("fileType") || "";

  // Convert Google Drive links to embeddable format
  const convertGoogleDriveUrl = (url) => {
    if (!url) return url;

    // Google Docs presentation link - use embed (most reliable)
    if (url.includes("docs.google.com/presentation")) {
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      if (match) {
        return `https://docs.google.com/presentation/d/${match[1]}/embed?start=false&loop=false&delayms=3000`;
      }
    }

    // Google Drive file link - try preview first, fallback to viewer
    if (url.includes("drive.google.com/file/d/")) {
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      if (match) {
        // For public files, preview works best
        return `https://drive.google.com/file/d/${match[1]}/preview`;
      }
    }

    // Google Docs document link - use pub for published docs, preview otherwise
    if (url.includes("docs.google.com/document")) {
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      if (match) {
        // Try embedded preview (requires "Anyone with link can view")
        return `https://docs.google.com/document/d/${match[1]}/preview?embedded=true`;
      }
    }

    // Google Sheets link - use htmlview for better compatibility
    if (url.includes("docs.google.com/spreadsheets")) {
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      if (match) {
        // htmlview works better than preview for sheets
        return `https://docs.google.com/spreadsheets/d/${match[1]}/htmlview?embedded=true`;
      }
    }

    return url;
  };

  // Determine file type from URL if not provided
  const getFileType = (url) => {
    if (!url) return "unknown";

    // Check for Google Drive/Docs URLs
    if (url.includes("docs.google.com/presentation")) return "pptx";
    if (url.includes("docs.google.com/document")) return "docx";
    if (url.includes("docs.google.com/spreadsheets")) return "xlsx";
    if (url.includes("drive.google.com/file")) {
      // Try to extract file extension from the original filename
      const fileName = urlParams.get("fileName") || "";
      if (fileName) {
        const ext = fileName.split(".").pop()?.toLowerCase();
        if (ext) return ext;
      }
      // Default to PDF for drive links
      return "pdf";
    }

    const extension = url.split(".").pop()?.toLowerCase().split("?")[0];
    return extension || "unknown";
  };

  const detectedFileType = fileType || getFileType(fileUrl);
  const convertedFileUrl = convertGoogleDriveUrl(fileUrl);

  // File type categories
  const isPDF = detectedFileType === "pdf";
  const isExcel = ["xlsx", "xls", "csv"].includes(detectedFileType);
  const isWord = ["doc", "docx"].includes(detectedFileType);
  const isPowerPoint = ["ppt", "pptx"].includes(detectedFileType);
  const isImage = ["jpg", "jpeg", "png", "gif", "bmp", "webp"].includes(
    detectedFileType
  );
  const isText = ["txt", "text"].includes(detectedFileType);

  // Office Online Viewer URL
  const getOfficeViewerUrl = (url) => {
    return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(
      url
    )}`;
  };

  // Cloudinary transformation for PDF optimization
  const getOptimizedPdfUrl = (url) => {
    if (url.includes("cloudinary.com")) {
      // Add transformations for better viewing
      return url.replace("/upload/", "/upload/f_auto,q_auto/");
    }
    return url;
  };

  useEffect(() => {
    if (fileUrl) {
      setLoading(false);
    } else {
      setError("No file URL provided");
      setLoading(false);
    }
  }, [fileUrl]);

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = fileName;
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenInNewTab = () => {
    window.open(fileUrl, "_blank");
  };

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 25, 50));
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  const renderViewer = () => {
    // Google Drive/Docs Viewer (highest priority)
    if (
      convertedFileUrl.includes("google.com") &&
      convertedFileUrl !== fileUrl
    ) {
      if (iframeError) {
        // Show helpful error message with fallback options
        return (
          <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-8">
            <AlertCircle className="w-16 h-16 text-orange-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">
              Unable to Preview Document
            </h3>
            <p className="text-gray-600 text-center mb-6 max-w-md">
              This Google Drive document may have restricted sharing settings or
              embedding disabled.
            </p>
            <div className="space-y-3">
              <button
                onClick={handleOpenInNewTab}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <ExternalLink className="w-5 h-5" />
                Open in Google Docs
              </button>
              <p className="text-sm text-gray-500 text-center">
                To enable embedding, the document owner needs to:
                <br />
                1. Set sharing to &quot;Anyone with the link can view&quot;
                <br />
                2. Ensure embedding is allowed in sharing settings
              </p>
            </div>
          </div>
        );
      }

      return (
        <iframe
          src={convertedFileUrl}
          title={fileName}
          className="w-full h-full border-0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          onLoad={() => {
            setLoading(false);
            // Check if iframe loaded successfully
            setTimeout(() => {
              const iframe = document.querySelector("iframe");
              if (iframe) {
                try {
                  // If we can't access contentWindow, it might be blocked
                  if (!iframe.contentWindow) {
                    setIframeError(true);
                  }
                } catch (e) {
                  // Cross-origin error is expected, but iframe should still load
                  console.log("Iframe loaded (cross-origin)");
                }
              }
            }, 2000);
          }}
          onError={() => {
            setLoading(false);
            setIframeError(true);
          }}
        />
      );
    }

    // PDF Viewer
    if (isPDF) {
      return (
        <iframe
          src={`${getOptimizedPdfUrl(
            convertedFileUrl
          )}#view=FitH&toolbar=1&navpanes=1`}
          title={fileName}
          className="w-full h-full border-0"
          style={{
            transform: `scale(${zoom / 100})`,
            transformOrigin: "top center",
          }}
        />
      );
    }

    // Excel Viewer
    if (isExcel) {
      return (
        <iframe
          src={getOfficeViewerUrl(fileUrl)}
          title={fileName}
          className="w-full h-full border-0"
          onLoad={() => setLoading(false)}
          onError={() => {
            // Fallback to Google Viewer
            setError("Using alternative viewer...");
          }}
        />
      );
    }

    // Word Document Viewer
    if (isWord) {
      return (
        <iframe
          src={getOfficeViewerUrl(fileUrl)}
          title={fileName}
          className="w-full h-full border-0"
          onLoad={() => setLoading(false)}
        />
      );
    }

    // PowerPoint Viewer
    if (isPowerPoint) {
      return (
        <iframe
          src={getOfficeViewerUrl(fileUrl)}
          title={fileName}
          className="w-full h-full border-0"
          onLoad={() => setLoading(false)}
        />
      );
    }

    // Image Viewer
    if (isImage) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-100">
          <img
            src={fileUrl}
            alt={fileName}
            className="max-w-full max-h-full object-contain"
            style={{ transform: `scale(${zoom / 100})` }}
          />
        </div>
      );
    }

    // Text File Viewer
    if (isText) {
      return (
        <iframe
          src={fileUrl}
          title={fileName}
          className="w-full h-full border-0 bg-white p-4"
          style={{
            transform: `scale(${zoom / 100})`,
            transformOrigin: "top center",
          }}
        />
      );
    }

    // Fallback: Google Docs Viewer for unsupported types
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
        <AlertCircle className="w-16 h-16 text-yellow-500" />
        <p className="text-lg font-medium text-gray-700">
          Preview not available for this file type
        </p>
        <p className="text-sm text-gray-500">File type: .{detectedFileType}</p>
        <div className="flex gap-3 mt-4">
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <Download className="w-4 h-4" />
            Download File
          </button>
          <button
            onClick={handleOpenInNewTab}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
          >
            <ExternalLink className="w-4 h-4" />
            Open in New Tab
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-white flex items-center justify-center z-50">
        <div className="flex flex-col items-center gap-4">
          <Loader className="w-12 h-12 text-blue-600 animate-spin" />
          <p className="text-lg text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error && !fileUrl) {
    return (
      <div className="fixed inset-0 bg-white flex items-center justify-center z-50">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <AlertCircle className="w-16 h-16 text-red-500" />
          <p className="text-lg font-medium text-gray-900">
            Unable to load document
          </p>
          <p className="text-sm text-gray-600">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-800 text-white px-4 py-3 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-700 rounded-lg transition"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
          <FileText className="w-5 h-5 text-blue-400" />
          <div>
            <h1 className="font-semibold text-sm md:text-base truncate max-w-xs md:max-w-md">
              {fileName}
            </h1>
            <p className="text-xs text-gray-400 uppercase">
              .{detectedFileType}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom Controls (for PDF and Images) */}
          {(isPDF || isImage) && (
            <div className="hidden md:flex items-center gap-2 mr-2">
              <button
                onClick={handleZoomOut}
                className="p-2 hover:bg-gray-700 rounded-lg transition"
                title="Zoom Out"
                disabled={zoom <= 50}
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-sm px-2">{zoom}%</span>
              <button
                onClick={handleZoomIn}
                className="p-2 hover:bg-gray-700 rounded-lg transition"
                title="Zoom In"
                disabled={zoom >= 200}
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="hidden md:block p-2 hover:bg-gray-700 rounded-lg transition"
            title="Toggle Fullscreen"
          >
            <Maximize className="w-4 h-4" />
          </button>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm"
            title="Download"
          >
            <Download className="w-4 h-4" />
            <span className="hidden md:inline">Download</span>
          </button>

          {/* Open in New Tab */}
          <button
            onClick={handleOpenInNewTab}
            className="p-2 hover:bg-gray-700 rounded-lg transition"
            title="Open in New Tab"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Viewer Content */}
      <div className="flex-1 overflow-hidden bg-gray-100">{renderViewer()}</div>

      {/* Loading Overlay for iframes */}
      {(isExcel || isWord || isPowerPoint) && loading && (
        <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader className="w-12 h-12 text-blue-600 animate-spin" />
            <p className="text-lg text-gray-600">Loading preview...</p>
          </div>
        </div>
      )}
    </div>
  );
}
