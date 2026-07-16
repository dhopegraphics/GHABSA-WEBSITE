import React, { useEffect } from "react";
import { InternshipCard } from "./InternshipCard";
import { motion } from "framer-motion";
import { fadeIn, underlineAnimation } from "../../utils/framerVariants";
import { useInternships } from "../../Context/InternshipsContext";
import { InternshipCardSkeleton } from "./InternshipCardSkeleton";
import { getData } from "../../utils/apiHandler";
import { FiArrowUpRight } from "react-icons/fi";
import { Link } from "react-router-dom";
import { Briefcase, Calendar, X } from "lucide-react";

export function InternshipsSection() {
  const { internships, setInternships } = useInternships();

  const fetchInternships = async () => {
    const { response, error } = await getData("/academics/internships/");
    if (error) {
      console.error("Error fetching internships:", error);
    }
    if (response) {
      // Backend already filters active internships
      setInternships(response);
    }
  };

  useEffect(() => {
    fetchInternships();
  }, []);

  const hasInternships = internships && internships.length > 0;

  return (
    <section id="internships" className="py-16 px-4 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <motion.h1
          variants={fadeIn("up", 0.5, 0)}
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0 }}
          className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
        >
          Open{" "}
          <span className="relative text-blue-600">
            Internships
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
        <p className="text-gray-600 text-center mb-12">
          Explore exciting internship opportunities from leading companies in
          the tech industry
        </p>

        {!internships ? (
          // Loading state
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {Array.from({ length: 4 }).map((_, index) => (
              <InternshipCardSkeleton key={index} />
            ))}
          </div>
        ) : hasInternships ? (
          // Has internships
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {internships.slice(0, 4).map((internship) => (
                <InternshipCard
                  key={internship.internship_id}
                  internship={internship}
                />
              ))}
            </div>

            {internships.length > 4 && (
              <div className="mt-12 text-center justify-center md:justify-start">
                <Link
                  to={"/internships"}
                  className="border-2 border-blue-700 text-blue-700 px-6 py-3 font-medium rounded hover:bg-blue-700 hover:text-white transition"
                >
                  See More <FiArrowUpRight className="inline" />
                </Link>
              </div>
            )}
          </>
        ) : (
          // No active internships
          <div className="text-center py-16">
            <div className="mb-6">
              <Briefcase className="w-20 h-20 mx-auto text-gray-300" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              No Active Internships
            </h3>
            <p className="text-gray-600 max-w-md mx-auto mb-6">
              There are currently no internship opportunities with open
              applications. Check back soon for new opportunities!
            </p>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>
                All posted internships have passed their application deadline
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
