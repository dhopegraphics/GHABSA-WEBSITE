import React, { useState } from "react";
import {
  Book,
  FileText,
  Video,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Eye,
  Link as LinkIcon,
  Maximize2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ResourcesModal } from "./ResourcesModal";

export function CourseResourceCard({ course, isCurrentSemester, isPeek }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getCourseResources = () => {
    const resources = [];
    if (course.past_questions?.length > 0) {
      resources.push({
        type: "Past Questions",
        icon: FileText,
        count: course.past_questions.length,
      });
    }
    if (course.slides?.length > 0) {
      resources.push({
        type: "Slides",
        icon: Book,
        count: course.slides.length,
      });
    }
    if (course.online_tutorial_tips?.length > 0) {
      resources.push({
        type: "Tutorials",
        icon: Video,
        count: course.online_tutorial_tips.length,
      });
    }
    return resources;
  };

  const resources = getCourseResources();
  const hasResources = resources.length > 0;

  // Handle file viewing with DocumentViewer in new tab
  const handleViewFile = (file, title, type) => {
    const fileUrl = file.file || file.file_url;
    if (!fileUrl) {
      console.error("No file URL available");
      return;
    }

    // Extract file extension
    const extension = fileUrl.split(".").pop()?.toLowerCase().split("?")[0];

    // Open in new tab
    const viewerUrl = `/document-viewer?fileUrl=${encodeURIComponent(
      fileUrl
    )}&fileName=${encodeURIComponent(title)}&fileType=${extension}`;
    window.open(viewerUrl, "_blank");
  };

  // Handle file download
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        relative rounded-lg border-2 transition-all duration-300 overflow-hidden
        ${
          isCurrentSemester && !isPeek
            ? "border-blue-500 bg-blue-50 shadow-lg shadow-blue-100"
            : "border-gray-200 bg-white hover:border-blue-300 hover:shadow-md"
        }
        ${isPeek ? "opacity-75 hover:opacity-100" : ""}
      `}
    >
      {/* Current Semester Badge */}
      {isCurrentSemester && !isPeek && (
        <div className="absolute top-0 right-0">
          <div className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
            Current
          </div>
        </div>
      )}

      <div className="p-4">
        {/* Course Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4
              className={`font-bold text-sm mb-1 ${
                isCurrentSemester && !isPeek ? "text-blue-900" : "text-gray-900"
              }`}
            >
              {course.course_code}
            </h4>
            <p
              className={`text-xs line-clamp-2 ${
                isCurrentSemester && !isPeek ? "text-blue-700" : "text-gray-600"
              }`}
            >
              {course.course_name}
            </p>
          </div>
        </div>

        {/* Credit Hours */}
        <div
          className={`text-xs mb-3 flex items-center gap-1 ${
            isCurrentSemester && !isPeek ? "text-blue-600" : "text-gray-500"
          }`}
        >
          <Book className="w-3 h-3" />
          <span>{course.credit_hours} Credits</span>
        </div>

        {/* Resources Summary */}
        {hasResources ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {resources.map((resource) => (
                <div
                  key={`${course.id}-${resource.type}`}
                  className={`
                    flex items-center gap-1 px-2 py-1 rounded text-xs
                    ${
                      isCurrentSemester && !isPeek
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-700"
                    }
                  `}
                >
                  <resource.icon className="w-3 h-3" />
                  <span>{resource.count}</span>
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className={`
                  flex-1 flex items-center justify-center gap-1 py-2 rounded text-xs font-medium transition-colors
                  ${
                    isCurrentSemester && !isPeek
                      ? "bg-blue-500 text-white hover:bg-blue-600"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }
                `}
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="w-3 h-3" />
                    Hide
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3" />
                    Quick View
                  </>
                )}
              </button>

              <button
                onClick={() => setIsModalOpen(true)}
                className={`
                  flex-1 flex items-center justify-center gap-1 py-2 rounded text-xs font-medium transition-colors
                  ${
                    isCurrentSemester && !isPeek
                      ? "bg-indigo-500 text-white hover:bg-indigo-600"
                      : "bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                  }
                `}
              >
                <Maximize2 className="w-3 h-3" />
                View All
              </button>
            </div>

            {/* Expanded Resources */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="pt-3 border-t space-y-3">
                    {/* Past Questions */}
                    {course.past_questions?.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          Past Questions ({course.past_questions.length})
                        </h5>
                        <div className="space-y-1.5">
                          {course.past_questions.map((pq, idx) => (
                            <div
                              key={pq.id || `pq-${idx}`}
                              className="flex items-center justify-between gap-2 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                            >
                              <span className="text-xs text-gray-700 truncate flex-1">
                                {pq.title || `Past Question ${idx + 1}`}
                              </span>
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() =>
                                    handleViewFile(
                                      pq,
                                      pq.title ||
                                        `${
                                          course.course_code
                                        } - Past Question ${idx + 1}`,
                                      "past_question"
                                    )
                                  }
                                  className="p-1.5 hover:bg-blue-100 rounded text-blue-600 transition-colors"
                                  title="View"
                                >
                                  <Eye className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() =>
                                    handleDownload(
                                      pq.file || pq.file_url,
                                      pq.title ||
                                        `${course.course_code}_PQ_${idx + 1}`
                                    )
                                  }
                                  className="p-1.5 hover:bg-green-100 rounded text-green-600 transition-colors"
                                  title="Download"
                                >
                                  <Download className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Slides */}
                    {course.slides?.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                          <Book className="w-3 h-3" />
                          Slides ({course.slides.length})
                        </h5>
                        <div className="space-y-1.5">
                          {course.slides.map((slide, idx) => (
                            <div
                              key={slide.id || `slide-${idx}`}
                              className="flex items-center justify-between gap-2 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                            >
                              <span className="text-xs text-gray-700 truncate flex-1">
                                {slide.title || `Slide ${idx + 1}`}
                              </span>
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() =>
                                    handleViewFile(
                                      slide,
                                      slide.title ||
                                        `${course.course_code} - Slide ${
                                          idx + 1
                                        }`,
                                      "slide"
                                    )
                                  }
                                  className="p-1.5 hover:bg-blue-100 rounded text-blue-600 transition-colors"
                                  title="View"
                                >
                                  <Eye className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() =>
                                    handleDownload(
                                      slide.file || slide.file_url,
                                      slide.title ||
                                        `${course.course_code}_Slide_${idx + 1}`
                                    )
                                  }
                                  className="p-1.5 hover:bg-green-100 rounded text-green-600 transition-colors"
                                  title="Download"
                                >
                                  <Download className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Online Tutorial Tips */}
                    {course.online_tutorial_tips?.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                          <LinkIcon className="w-3 h-3" />
                          Online Resources ({course.online_tutorial_tips.length}
                          )
                        </h5>
                        <div className="space-y-1.5">
                          {course.online_tutorial_tips.map((tutorial, idx) => (
                            <div
                              key={tutorial.id || `tutorial-${idx}`}
                              className="flex items-center justify-between gap-2 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                            >
                              <span className="text-xs text-gray-700 truncate flex-1">
                                {tutorial.title || `Tutorial ${idx + 1}`}
                              </span>
                              <div className="flex items-center gap-1">
                                <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                                  {tutorial.type_of_resource || "Link"}
                                </span>
                                <a
                                  href={tutorial.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-1.5 hover:bg-blue-100 rounded text-blue-600 transition-colors"
                                  title="Open Link"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ) : (
          <div className="text-xs text-gray-400 text-center py-2">
            No resources available yet
          </div>
        )}
      </div>

      {/* Resources Modal */}
      <ResourcesModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        course={course}
      />
    </motion.div>
  );
}
