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
      "Core foundations in chemistry, biology and the principles of biochemistry.",
    topics: [
      "General Chemistry",
      "Cell Biology",
      "Organic Chemistry",
      "Mathematics",
    ],
  },
  {
    year: 2,
    courses: null,
    icon: Database,
    description:
      "Build a deeper understanding of biomolecules, metabolism and laboratory methods.",
    topics: ["Biomolecules", "Metabolism", "Microbiology", "Lab Methods"],
  },
  {
    year: 3,
    courses: null,
    icon: Code2,
    description:
      "Explore advanced molecular systems and applied biochemical techniques.",
    topics: [
      "Molecular Biology",
      "Enzymology",
      "Immunology",
      "Biotechnology",
    ],
  },
  {
    year: 4,
    courses: null,
    icon: Brain,
    description:
      "Specialised study, research practice and the final-year project experience.",
    topics: ["Research", "Bioinformatics", "Project", "Seminars"],
  },
];

export function ResourcesSection() {
  const { setCourses } = useCourses();

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
    <section id="resources" className="bg-[#f4f7fb] px-5 py-20 sm:px-8 sm:py-28 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="max-w-3xl text-4xl font-semibold leading-tight tracking-[-0.04em] text-slate-950 sm:text-5xl"
        >
          Study with more{" "}
          <span className="relative text-blue-600">
            direction.
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
        <p className="mb-12 mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
          Comprehensive course materials and resources organized by year to
          support your academic journey in biochemistry.
        </p>

        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
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
