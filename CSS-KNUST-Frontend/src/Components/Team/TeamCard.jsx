import {
  Github,
  Linkedin,
  Twitter,
  Facebook,
  Instagram,
  Youtube,
} from "lucide-react";
import {
  FaTiktok,
  FaPinterest,
  FaReddit,
  FaWhatsapp,
  FaTelegram,
} from "react-icons/fa";

export function TeamCard({ name, role, imageUrl, socialLinks }) {
  // Helper function to get the appropriate icon and color for each platform
  const getSocialIcon = (platform) => {
    const platformLower = platform?.toLowerCase();

    const iconMap = {
      github: { Icon: Github, color: "hover:text-gray-900" },
      linkedin: { Icon: Linkedin, color: "hover:text-blue-600" },
      twitter: { Icon: Twitter, color: "hover:text-blue-400" },
      facebook: { Icon: Facebook, color: "hover:text-blue-700" },
      instagram: { Icon: Instagram, color: "hover:text-pink-500" },
      youtube: { Icon: Youtube, color: "hover:text-red-600" },
      tiktok: { Icon: FaTiktok, color: "hover:text-black" },
      pinterest: { Icon: FaPinterest, color: "hover:text-red-700" },
      reddit: { Icon: FaReddit, color: "hover:text-orange-600" },
      whatsapp: { Icon: FaWhatsapp, color: "hover:text-green-500" },
      telegram: { Icon: FaTelegram, color: "hover:text-blue-500" },
    };

    return iconMap[platformLower] || null;
  };

  // Split social links into left and right groups
  const validLinks =
    socialLinks?.filter((item) => getSocialIcon(item?.platform)) || [];
  const midPoint = Math.ceil(validLinks.length / 2);
  const leftLinks = validLinks.slice(0, midPoint);
  const rightLinks = validLinks.slice(midPoint);

  return (
    <div className="relative group">
      <div className="w-full h-96 lg:h-80 relative overflow-hidden">
        <img
          src={imageUrl}
          alt={name}
          className="w-full h-full object-cover object-top transform scale-105 transition-transform duration-500"
        />
        <div className="absolute w-full scale-x-0 h-full bg-[#282cadb4] top-0 left-0 group-hover:scale-x-100 transition-all duration-500 origin-left"></div>

        <div className="opacity-50 group-hover:opacity-100 transition-all duration-500 group-hover:-translate-y-6 absolute bottom-0 left-[8%]">
          <p className="text-white text-[14px]">{role}</p>
          <h4 className="text-white text-[24px]">{name}</h4>
        </div>

        {/* Left Social Icons */}
        <div className="absolute left-[6%] top-0 translate-y-[-125px] group-hover:delay-200 grid gap-2 transition-all duration-700 group-hover:translate-y-4">
          {leftLinks.map((item, index) => {
            const iconData = getSocialIcon(item?.platform);

            if (!iconData) return null;

            const { Icon, color } = iconData;

            return (
              <a
                key={`left-${item?.platform}-${index}`}
                href={item?.link}
                target="_blank"
                rel="noopener noreferrer"
                className={`text-white transition-colors duration-300 ${color}`}
              >
                <Icon className="w-6 h-6" />
              </a>
            );
          })}
        </div>

        {/* Right Social Icons */}
        <div className="absolute right-[6%] top-0 translate-y-[-125px] group-hover:delay-200 grid gap-2 transition-all duration-700 group-hover:translate-y-4">
          {rightLinks.map((item, index) => {
            const iconData = getSocialIcon(item?.platform);

            if (!iconData) return null;

            const { Icon, color } = iconData;

            return (
              <a
                key={`right-${item?.platform}-${index}`}
                href={item?.link}
                target="_blank"
                rel="noopener noreferrer"
                className={`text-white transition-colors duration-300 ${color}`}
              >
                <Icon className="w-6 h-6" />
              </a>
            );
          })}
        </div>
      </div>
    </div>
  );
}
