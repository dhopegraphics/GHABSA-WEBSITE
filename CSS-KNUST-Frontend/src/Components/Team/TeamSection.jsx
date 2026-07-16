import React, { useEffect } from "react";
import { TeamCard } from "./TeamCard";
import { motion } from "framer-motion";
import {
  container,
  fadeIn,
  item,
  underlineAnimation,
} from "../../utils/framerVariants";
import { Link } from "react-router-dom";
import { FiArrowUpRight } from "react-icons/fi";
import { useTeam } from "../../Context/TeamContext";
import { getData } from "../../utils/apiHandler";
import { TeamCardSkeleton } from "./TeamCardSkeleton";

export function TeamSection() {
  const { team, setTeam } = useTeam();

  const fetchTeam = async () => {
    const { response, error, loading } = await getData("/executives/");
    if (error) {
      console.error("Error fetching Team:", error);
    }
    if (response) {
      setTeam(response?.filter((i) => i?.is_active == true));
    }
  };

  useEffect(() => {
    fetchTeam();
  }, []);

  return (
    <section className="py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <motion.h1
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
          >
            Our{" "}
            <span className="relative text-blue-600">
              Executives
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
          <p className="text-gray-600 max-w-2xl mx-auto">
            The dedicated individuals behind our Biochemistry Society, KNUST,
            working together to create opportunities and foster innovation.
          </p>
        </div>

        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {team?.length == 0
            ? Array.from({ length: 4 }).map((_, index) => (
                <TeamCardSkeleton key={index} />
              ))
            : team.map(
                (member, index) =>
                  index < 4 && (
                    <TeamCard
                      key={member?.executive_id}
                      imageUrl={member?.image}
                      name={member?.executive_name}
                      role={member?.position?.name}
                      socialLinks={member?.social_media_links}
                    />
                  )
              )}
        </ul>
        <div className="mt-12  text-center justify-center md:justify-start">
          <Link
            to={"/executives"}
            className="border-2 border-blue-700 text-blue-700 px-6 py-3 font-medium rounded hover:bg-blue-700 hover:text-white transition"
          >
            See More <FiArrowUpRight className="inline" />
          </Link>
        </div>
      </div>
    </section>
  );
}
