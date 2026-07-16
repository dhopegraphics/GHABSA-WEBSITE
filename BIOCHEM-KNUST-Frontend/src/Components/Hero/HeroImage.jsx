import React from 'react';
import cs from '../../assets/cs3r.png'
import { motion } from 'framer-motion';
import { fadeIn } from '../../utils/framerVariants';

export function HeroImage() {
  return (
    <div className="relative">
      <motion.figure
                        variants={fadeIn("down", 0.7, 0)}
                        initial="offscreen"
                        whileInView="onscreen"
                        viewport={{ once: true, amount: 0 }} className="relative  rounded-full mx-auto bg-gradient-to-t from-blue-700 to-transparent aspect-square  overflow-hidden shadow-xl ">
        <img 
          src={cs}
          alt="Biochem Society Members" 
          className="h-full w-full object-cover"
        />
      </motion.figure>
    </div>
  );
}