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
    <article className="group relative overflow-hidden rounded-[28px] bg-[#0b2347] shadow-[0_16px_45px_rgba(6,20,43,0.14)]">
      <div className="relative h-[390px] w-full overflow-hidden lg:h-[410px]">
        <img
          src={imageUrl}
          alt={name}
          className="h-full w-full object-cover object-top transition-transform duration-700 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#06142b] via-[#06142b]/10 to-transparent" />

        <div className="absolute bottom-0 left-0 right-0 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-300">{role}</p>
          <h4 className="mt-2 text-2xl font-semibold tracking-tight text-white">{name}</h4>
        </div>

        {/* Left Social Icons */}
        <div className="absolute left-4 top-4 flex gap-2">
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
                aria-label={`${name} on ${item?.platform}`}
                className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-slate-950/30 text-white backdrop-blur-md transition-colors duration-300 ${color}`}
              >
                <Icon className="h-4 w-4" />
              </a>
            );
          })}
        </div>

        {/* Right Social Icons */}
        <div className="absolute right-4 top-4 flex gap-2">
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
                aria-label={`${name} on ${item?.platform}`}
                className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-slate-950/30 text-white backdrop-blur-md transition-colors duration-300 ${color}`}
              >
                <Icon className="h-4 w-4" />
              </a>
            );
          })}
        </div>
      </div>
    </article>
  );
}
