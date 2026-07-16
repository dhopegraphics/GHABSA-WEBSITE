import { useEffect } from "react";
import { TeamCard } from "./TeamCard";
import { motion } from "framer-motion";
import {
  fadeIn,
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
    const { response, error } = await getData("/executives/");
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
    <section className="bg-white px-5 py-20 sm:px-8 sm:py-28 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 lg:flex lg:items-end lg:justify-between">
          <div>
          <motion.h1
            variants={fadeIn("up", 0.5, 0)}
            initial="offscreen"
            whileInView="onscreen"
            viewport={{ once: true, amount: 0 }}
            className="max-w-3xl text-4xl font-semibold leading-tight tracking-[-0.04em] text-slate-950 sm:text-5xl"
          >
            Meet the people{" "}
            <span className="relative text-blue-600">
              moving us forward.
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
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
            The dedicated individuals behind our Biochemistry Society, KNUST,
            working together to create opportunities and foster innovation.
          </p></div>
          <Link to="/executives" className="mt-7 inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:border-blue-600 hover:text-blue-700 lg:mt-0">Meet the full team <FiArrowUpRight /></Link>
        </div>

        <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
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
        <div className="hidden">
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
