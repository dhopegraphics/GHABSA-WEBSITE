import { useEffect } from "react";
import { ResourceCard } from "./ResourceCard";
import { Book, Code2, Database, Brain } from "lucide-react";
import { fadeIn, underlineAnimation } from "../../utils/framerVariants";
import { motion } from "framer-motion";
import { useCourses } from "../../Context/CoursesContext";
import { getData } from "../../utils/apiHandler";

let yearResources = [
  {
    year: 1,
    courses: null,
    icon: Book,
    description:
      "Foundation courses covering programming basics, mathematics, and computer architecture.",
    topics: [
      "Programming Fundamentals",
      "Calculus",
      "Digital Logic",
      "Linear Algebra",
    ],
  },
  {
    year: 2,
    courses: null,
    icon: Database,
    description:
      "Core programming concepts, databases, and software development principles.",
    topics: ["Data Structures", "OOP", "Algorithms", "Web Development"],
  },
  {
    year: 3,
    courses: null,
    icon: Code2,
    description:
      "Advanced computing concepts, and specialized programming domains.",
    topics: [
      "Database Systems",
      "Operating Systems",
      "Networks",
      "Software Engineering",
    ],
  },
  {
    year: 4,
    courses: null,
    icon: Brain,
    description:
      "Specialized electives, advanced topics, and final year project.",
    topics: ["AI/ML", "Cloud Computing", "Project", "Cybersecurity"],
  },
];

export function ResourcesSection() {
  const { courses, setCourses } = useCourses();

  const fetchCourses = async () => {
    const { response, error } = await getData("/academics/courses/");
    if (error) {
      console.error("Error fetching Courses:", error);
    }
    if (response) {
      setCourses(response);
      courseSegregation(response);
    }
  };

  const courseSegregation = (fetchedCourses) => {
    yearResources = yearResources.map((resource) => ({
      ...resource,
      courses: [],
    }));

    fetchedCourses.forEach((course) => {
      // Backend now returns year as 1, 2, 3, 4 directly
      const yearIndex = parseInt(course?.year) - 1;
      if (yearIndex >= 0 && yearIndex < yearResources.length) {
        yearResources[yearIndex].courses.push(course);
      }
    });
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  return (
    <section id="resources" className="py-16 px-4 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
        >
          Academic{" "}
          <span className="relative text-blue-600">
            Resources
            <motion.div
              variants={underlineAnimation(0.7)}
              initial="offscreen"
              whileInView="onscreen"
              exit="reverse"
              className="absolute left-0 bottom-0 h-1 bg-blue-600"
              style={{ width: "0%", height: "3px" }}
            />
          </span>
        </motion.h1>
        <p className="text-center text-gray-600 mb-12">
          Comprehensive course materials and resources organized by year to
          support your academic journey in computer science.
        </p>

        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {yearResources.map((resource) => (
            <li key={resource.year} className="flex">
              <ResourceCard key={resource.year} {...resource} />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
