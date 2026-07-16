import  { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { fadeIn, underlineAnimation } from "../utils/framerVariants";
import { LiaLaptopCodeSolid } from "react-icons/lia";
import { FaBinoculars } from "react-icons/fa";

import { BsGlobe2 } from "react-icons/bs";

export const Feature = () => {
  return (
    <div className="z-10 pt-7">
      <motion.h1
        variants={fadeIn("up", 0.5, 0)}
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0 }}
        className="text-4xl md:text-5xl mb-10 font-bold text-gray-900 text-center"
      >
        <span className="relative text-blue-600">
          About
          <motion.div
            variants={underlineAnimation(0.7)}
            initial="offscreen"
            whileInView="onscreen"
            exit="reverse"
            className="absolute left-0 bottom-0 h-1 bg-blue-600"
            style={{ width: "0%", height: "3px" }}
          />
        </span>{" "}
        Us
      </motion.h1>
      <TextParallaxContent
        index={1}
        imgUrl="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=2671&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        subheading="Community"
        heading="Empowering Computer Scientists"
      >
        <Content
          heading="<Who We Are />"
          icon={<BsGlobe2 />}
          description="The Computer Science Society is a hub for innovation and collaboration, bringing together students and professionals passionate about technology. Our mission is to inspire growth, learning, and real-world impact through projects, events, and community engagement."
        />
      </TextParallaxContent>
      <TextParallaxContent
        index={2}
        imgUrl="https://images.unsplash.com/photo-1530893609608-32a9af3aa95c?q=80&w=2564&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        subheading="Innovation"
        heading="Shaping the Future of Technology"
      >
        <Content
          heading="<Our Vision />"
          icon={<FaBinoculars />}
          description="We strive to be at the forefront of technological advancements, fostering an environment that encourages curiosity, creativity, and collaboration. From artificial intelligence to ethical hacking, we aim to shape the future of computer science."
        />
      </TextParallaxContent>
      <TextParallaxContent
        index={3}
        imgUrl="https://images.unsplash.com/photo-1504610926078-a1611febcad3?q=80&w=2416&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        subheading="Excellence"
        heading="Learn, Build, Grow"
      >
        <Content
          heading="<What We Do />"
          icon={<LiaLaptopCodeSolid />}
          description="Our activities include coding bootcamps, hackathons, seminars by industry leaders, and hands-on workshops. We empower members to build projects, gain expertise, and make a meaningful impact in the tech world."
        />
      </TextParallaxContent>
    </div>
  );
};

const TextParallaxContent = ({
  imgUrl,
  subheading,
  heading,
  children,
  index,
}) => {
  const IMG_PADDING = 12;
  return (
    <motion.div
      style={{ paddingLeft: IMG_PADDING, paddingRight: IMG_PADDING }}
      className={`flex flex-col gap-x-8 ${
        index % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
      }`}
    >
      <motion.div className="relative md:h-[100vh] md:w-1/2 h-[50vh]">
        <StickyImage imgUrl={imgUrl} />
        <OverlayCopy heading={heading} subheading={subheading} />
      </motion.div>
      {children}
    </motion.div>
  );
};

const StickyImage = ({ imgUrl }) => {
  const IMG_PADDING = 12;
  const targetRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ["end end", "end start"],
  });

  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.8]);
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0]);

  return (
    <motion.div
      style={{
        backgroundImage: `url(${imgUrl})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        height: `calc(100% - ${IMG_PADDING * 2}px - 70px)`,
        top: 70,
        scale,
      }}
      ref={targetRef}
      className="sticky z-0 overflow-hidden md:h-[calc(100% - 24px - 70px)] h-[calc(50% - 24px - 70px)] rounded-3xl"
    >
      <motion.div
        className="absolute inset-0 bg-neutral-950/70 rounded-3xl"
        style={{ opacity }}
      />
    </motion.div>
  );
};

const OverlayCopy = ({ subheading, heading }) => {
  const targetRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ["start end", "end start"],
  });

  const y = useTransform(scrollYProgress, [0, 1], [100, -200]);
  const opacity = useTransform(scrollYProgress, [0.25, 0.5, 0.75], [0, 1, 0]);

  return (
    <motion.div
      style={{
        y,
        opacity,
      }}
      ref={targetRef}
      className="absolute left-0 top-[50px] md:top-[200px] flex h-[50vh] w-full flex-col items-center justify-center text-white"
    >
      <p className="mb-2 text-center text-xl md:mb-4 md:text-3xl">
        {subheading}
      </p>
      <p className="text-center text-3xl font-bold md:text-7xl">{heading}</p>
    </motion.div>
  );
};

const Content = ({ heading, description, icon }) => (
  <div className="md:w-1/2 relative flex items-center flex-col justify-center px-4 overflow-hidden">
    <div className="absolute -top-32 -right-32 opacity-20 md:text-[400px] text-[300px] text-blue-700">
      {icon}
    </div>
    <div className="flex flex-row gap-4 text-3xl text-blue-700 z-10 items-center w-full">
      {icon}
      <h2 className="col-span-1 text-2xl text-start font-bold text-black md:col-span-4">
        {heading}
      </h2>
    </div>
    <p className="mb-8 z-10 text-xl text-neutral-600">{description}</p>
  </div>
);
