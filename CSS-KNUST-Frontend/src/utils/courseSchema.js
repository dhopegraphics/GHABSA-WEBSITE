export const SEMESTERS = [
  { value: "all", label: "All semesters" },
  { value: "1", label: "First semester" },
  { value: "2", label: "Second semester" },
];

export const normalizeCourse = (course) => ({
  ...course,
  year: Number(course?.year),
  semester:
    course?.semester === "both"
      ? "both"
      : String(course?.semester ?? "").replace(/semester\s*/i, "").trim(),
});

export const normalizeCourses = (payload) => {
  const courses = Array.isArray(payload) ? payload : payload?.results || [];
  return courses.map(normalizeCourse);
};

export const courseMatchesSemester = (course, semester) =>
  semester === "all" ||
  normalizeCourse(course).semester === semester ||
  normalizeCourse(course).semester === "both";

