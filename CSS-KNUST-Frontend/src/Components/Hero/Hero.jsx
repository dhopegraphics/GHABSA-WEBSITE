

import { HeroContent } from "./HeroContent";
import CssHero from "../../assets/cssHero.png";

export default function Hero({ onSignupClick }) {
  return (
    <div
      className="min-h-screen mt-[70px] z-10 hero relative bg-cover  bg-center transition-all duration-1000 ease-in-out"
      style={{
        backgroundImage: `url(${CssHero})`,
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 to-black/95" />
      <div className="max-w-7xl mx-auto px-1 md:px-4  lg:px-8 py-24 relative z-10">
        <div className="flex items-center justify-center">
          <HeroContent onSignupClick={onSignupClick} />
        </div>
      </div>
    </div>
  );
}
