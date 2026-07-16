import {
  X,
  Book,
  FileText,
  Eye,
  Download,
  ExternalLink,
  Link as LinkIcon,
  GraduationCap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function ResourcesModal({ isOpen, onClose, course }) {
  if (!isOpen || !course) return null;

  const handleViewFile = (fileUrl, fileName) => {
    if (!fileUrl) {
      console.error("No file URL available");
      return;
    }

    // Extract file extension - handle Google Drive/Docs URLs
    let extension = "";

    // Check if it's a Google Drive/Docs URL
    if (fileUrl.includes("docs.google.com/presentation")) {
      extension = "pptx";
    } else if (fileUrl.includes("docs.google.com/document")) {
      extension = "docx";
    } else if (fileUrl.includes("docs.google.com/spreadsheets")) {
      extension = "xlsx";
    } else if (fileUrl.includes("drive.google.com")) {
      // Try to get extension from filename
      extension = fileName.split(".").pop()?.toLowerCase() || "pdf";
    } else {
      // Regular file URL
      extension = fileUrl.split(".").pop()?.toLowerCase().split("?")[0];
    }

    // Open in new tab with document viewer
    const viewerUrl = `/document-viewer?fileUrl=${encodeURIComponent(
      fileUrl
    )}&fileName=${encodeURIComponent(fileName)}&fileType=${extension}`;
    window.open(viewerUrl, "_blank");
  };

  const handleDownload = (fileUrl, fileName) => {
    if (!fileUrl) return;

    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = fileName;
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const hasPastQuestions = course.past_questions?.length > 0;
  const hasSlides = course.slides?.length > 0;
  const hasTutorials = course.online_tutorial_tips?.length > 0;
  const hasResources = hasPastQuestions || hasSlides || hasTutorials;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            style={{ zIndex: 9999998 }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 md:inset-8 lg:inset-16 bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden"
            style={{ zIndex: 9999999 }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <GraduationCap className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{course.course_code}</h2>
                  <p className="text-sm text-blue-100">{course.course_name}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Course Info Bar */}
            <div className="bg-gray-50 px-6 py-3 border-b flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <Book className="w-4 h-4" />
                  {course.credit_hours} Credits
                </span>
                {course.lecturer_name && (
                  <span className="flex items-center gap-1">
                    <GraduationCap className="w-4 h-4" />
                    {course.lecturer_name}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                  Year {course.year}
                </span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">
                  Semester {course.semester}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {hasResources ? (
                <div className="space-y-6 max-w-5xl mx-auto">
                  {/* Past Questions Section */}
                  {hasPastQuestions && (
                    <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden">
                      <div className="bg-gradient-to-r from-red-50 to-orange-50 px-4 py-3 border-b border-red-200">
                        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                          <FileText className="w-5 h-5 text-red-600" />
                          Past Questions ({course.past_questions.length})
                        </h3>
                      </div>
                      <div className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {course.past_questions.map((pq, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
                            >
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className="p-2 bg-red-100 rounded-lg">
                                  <FileText className="w-5 h-5 text-red-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-gray-900 truncate">
                                    {pq.title || `Past Question ${idx + 1}`}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    PDF Document
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() =>
                                    handleViewFile(
                                      pq.file || pq.file_url,
                                      pq.title ||
                                        `${
                                          course.course_code
                                        } - Past Question ${idx + 1}`
                                    )
                                  }
                                  className="p-2 hover:bg-blue-100 rounded-lg text-blue-600 transition-colors"
                                  title="View in new tab"
                                >
                                  <Eye className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() =>
                                    handleDownload(
                                      pq.file || pq.file_url,
                                      pq.title ||
                                        `${course.course_code}_PQ_${idx + 1}`
                                    )
                                  }
                                  className="p-2 hover:bg-green-100 rounded-lg text-green-600 transition-colors"
                                  title="Download"
                                >
                                  <Download className="w-5 h-5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Slides Section */}
                  {hasSlides && (
                    <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden">
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-blue-200">
                        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                          <Book className="w-5 h-5 text-blue-600" />
                          Lecture Slides ({course.slides.length})
                        </h3>
                      </div>
                      <div className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {course.slides.map((slide, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
                            >
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                  <Book className="w-5 h-5 text-blue-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-gray-900 truncate">
                                    {slide.title || `Slide ${idx + 1}`}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    Presentation
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() =>
                                    handleViewFile(
                                      slide.file || slide.file_url,
                                      slide.title ||
                                        `${course.course_code} - Slide ${
                                          idx + 1
                                        }`
                                    )
                                  }
                                  className="p-2 hover:bg-blue-100 rounded-lg text-blue-600 transition-colors"
                                  title="View in new tab"
                                >
                                  <Eye className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() =>
                                    handleDownload(
                                      slide.file || slide.file_url,
                                      slide.title ||
                                        `${course.course_code}_Slide_${idx + 1}`
                                    )
                                  }
                                  className="p-2 hover:bg-green-100 rounded-lg text-green-600 transition-colors"
                                  title="Download"
                                >
                                  <Download className="w-5 h-5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tutorials Section */}
                  {hasTutorials && (
                    <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden">
                      <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3 border-b border-purple-200">
                        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                          <LinkIcon className="w-5 h-5 text-purple-600" />
                          Online Resources ({course.online_tutorial_tips.length}
                          )
                        </h3>
                      </div>
                      <div className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {course.online_tutorial_tips.map((tutorial, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
                            >
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className="p-2 bg-purple-100 rounded-lg">
                                  <LinkIcon className="w-5 h-5 text-purple-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-gray-900 truncate">
                                    {tutorial.title || `Tutorial ${idx + 1}`}
                                  </p>
                                  <p className="text-xs text-gray-500 capitalize">
                                    {tutorial.type_of_resource || "Link"}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <span className="text-xs px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">
                                  {tutorial.type_of_resource || "link"}
                                </span>
                                <a
                                  href={tutorial.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-2 hover:bg-blue-100 rounded-lg text-blue-600 transition-colors"
                                  title="Open in new tab"
                                >
                                  <ExternalLink className="w-5 h-5" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <Book className="w-20 h-20 mb-4 opacity-30" />
                  <p className="text-lg font-medium">
                    No resources available yet
                  </p>
                  <p className="text-sm mt-2">
                    Resources will appear here once they are uploaded
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t flex items-center justify-between">
              <p className="text-sm text-gray-600">
                {hasPastQuestions &&
                  `${course.past_questions.length} Past Questions`}
                {hasPastQuestions && hasSlides && " • "}
                {hasSlides && `${course.slides.length} Slides`}
                {(hasPastQuestions || hasSlides) && hasTutorials && " • "}
                {hasTutorials &&
                  `${course.online_tutorial_tips.length} Tutorials`}
              </p>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors font-medium"
              >
                Close
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
