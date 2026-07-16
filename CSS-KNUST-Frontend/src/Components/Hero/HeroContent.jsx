import React, { useContext } from "react";
import { Code2, Users, Globe, Heart } from "lucide-react";
import { FeatureCard } from "./FeatureCard";
import { motion } from "framer-motion";
import {
  container,
  fadeIn,
  item,
  underlineAnimation,
} from "../../utils/framerVariants.js";
import { FiArrowUpRight } from "react-icons/fi";
import { Link, useNavigate } from "react-router-dom";
import { UserContext } from "../../Context/UserContext.jsx";

export function HeroContent({ onSignupClick }) {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  return (
    <motion.div
      variants={fadeIn("up", 0.7, 0.5)}
      initial="offscreen"
      whileInView="onscreen"
      viewport={{ once: true, amount: 0 }}
      className="space-y-8 flex items-center flex-col justify-center text-center md:text-left "
    >
      <h1 className="text-4xl md:text-5xl font-bold text-gray-100">
        Empowering Future{" "}
        <span className="relative text-blue-600">
          Tech Leaders
          <motion.div
            variants={underlineAnimation(0.7)}
            initial="offscreen"
            whileInView="onscreen"
            exit="reverse"
            className="absolute left-0 bottom-0 h-1 bg-blue-700"
            style={{ width: "0%", height: "3px" }}
          />
        </span>
      </h1>

      <p className="text-md md:text-lg text-white max-w-2xl text-center font-light">
        Join our vibrant community of aspiring developers, innovators, and tech
        enthusiasts. We're dedicated to fostering growth, collaboration, and
        excellence in computer science.
      </p>

      <div className="mt-6 animate-fade-in-up flex gap-4 flex-row justify-center md:justify-start flex-wrap">
        {user ? (
          <button
            onClick={() => navigate("/dashboard/home")}
            className="border-2 border-blue-700 hover:border-blue-800 bg-blue-700 hover:bg-blue-800 text-white px-4 md:px-6 py-3 font-medium rounded transition"
          >
            Go to Dashboard
          </button>
        ) : (
          <button
            onClick={onSignupClick}
            className="border-2 border-blue-700 hover:border-blue-800 bg-blue-700 hover:bg-blue-800 text-white px-4 md:px-6 py-3 font-medium rounded transition"
          >
            Join the Society
          </button>
        )}
        <Link
          to={"/admission?tab=helpdesk"}
          className="border-2 border-red-600 bg-red-600 text-white px-6 py-3 font-medium rounded hover:bg-red-700 hover:border-red-700 transition"
        >
          Freshers Help Desk <FiArrowUpRight className="inline" />
        </Link>
        <Link
          to={"/faq"}
          className="border-2 border-blue-600 text-blue-600 px-6 py-3 font-medium rounded hover:bg-blue-700 hover:border-blue-700 hover:text-white transition"
        >
          Learn More <FiArrowUpRight className="inline" />
        </Link>
        <Link
          to="/donate"
          className="border-2 border-pink-500 bg-gradient-to-r from-pink-500 to-red-500 text-white px-6 py-3 font-medium rounded hover:from-pink-600 hover:to-red-600 transition flex items-center gap-2"
        >
          <Heart className="w-4 h-4" /> Donate
        </Link>
      </div>

      <motion.ul
        variants={container}
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0.5 }}
        className="grid grid-cols-3 gap-10 md:gap-14 pt-8"
      >
        <motion.li variants={item}>
          <FeatureCard
            icon={Code2}
            title="Workshops"
            description="Weekly coding sessions"
          />
        </motion.li>
        <motion.li variants={item}>
          <FeatureCard
            icon={Users}
            title="Network"
            description="500+ active members"
          />
        </motion.li>
        <motion.li variants={item}>
          <FeatureCard
            icon={Globe}
            title="Events"
            description="Global hackathons"
          />
        </motion.li>
      </motion.ul>
    </motion.div>
  );
}
