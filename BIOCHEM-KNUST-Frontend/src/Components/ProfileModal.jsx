import {
  X,
  Mail,
  Phone,
  MapPin,
  Clock,
  Award,
  Briefcase,
  Code,
  Linkedin,
  Twitter,
  Facebook,
  Instagram,
  Github,
  Youtube,
  MessageCircle,
  Send,
  Music,
  Globe,
} from "lucide-react";
import PropTypes from "prop-types";
import { getOptimizedImageUrl, IMAGE_PRESETS } from "../utils/imageUtils";

// Social media icon mapping
const getSocialIcon = (platform) => {
  const platformLower = platform.toLowerCase();
  switch (platformLower) {
    case "linkedin":
      return Linkedin;
    case "twitter":
      return Twitter;
    case "facebook":
      return Facebook;
    case "instagram":
      return Instagram;
    case "github":
      return Github;
    case "youtube":
      return Youtube;
    case "whatsapp":
      return MessageCircle;
    case "telegram":
      return Send;
    case "snapchat":
    case "tiktok":
      return Music;
    default:
      return Globe;
  }
};

// Social media color mapping
const getSocialColor = (platform) => {
  const platformLower = platform.toLowerCase();
  switch (platformLower) {
    case "linkedin":
      return "from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800";
    case "twitter":
      return "from-sky-400 to-sky-600 hover:from-sky-500 hover:to-sky-700";
    case "facebook":
      return "from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800";
    case "instagram":
      return "from-pink-500 via-purple-500 to-orange-500 hover:from-pink-600 hover:via-purple-600 hover:to-orange-600";
    case "github":
      return "from-gray-700 to-gray-900 hover:from-gray-800 hover:to-black";
    case "youtube":
      return "from-red-600 to-red-700 hover:from-red-700 hover:to-red-800";
    case "whatsapp":
      return "from-green-500 to-green-600 hover:from-green-600 hover:to-green-700";
    case "telegram":
      return "from-blue-400 to-blue-600 hover:from-blue-500 hover:to-blue-700";
    case "snapchat":
      return "from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600";
    case "tiktok":
      return "from-black to-gray-800 hover:from-gray-900 hover:to-black";
    case "pinterest":
      return "from-red-500 to-red-700 hover:from-red-600 hover:to-red-800";
    case "reddit":
      return "from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700";
    case "discord":
      return "from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700";
    case "twitch":
      return "from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800";
    case "medium":
      return "from-gray-800 to-black hover:from-gray-900 hover:to-black";
    case "slack":
      return "from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600";
    default:
      return "from-gray-600 to-gray-800 hover:from-gray-700 hover:to-gray-900";
  }
};

export default function ProfileModal({ person, type, onClose }) {
  if (!person) return null;

  const name =
    type === "executive" ? person.executive_name : person.appointee_name;
  const position = type === "executive" ? person.position?.name : person.role;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-slideUp">
        {/* Header Section with Image */}
        <div className="relative h-64 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-10 h-10 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center text-white transition-all duration-300"
          >
            <X className="w-6 h-6" />
          </button>
          <div className="absolute -bottom-20 left-1/2 -translate-x-1/2">
            <div className="relative">
              <img
                src={getOptimizedImageUrl(
                  person.image || "/images/default-profile.png",
                  IMAGE_PRESETS.profileLarge
                )}
                alt={name}
                className="w-40 h-40 rounded-full border-8 border-white object-cover shadow-xl"
                loading="lazy"
              />
            </div>
          </div>
        </div>

        {/* Content Section */}
        <div className="pt-24 px-8 pb-8">
          {/* Name and Position */}
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">{name}</h2>
            <p className="text-xl text-blue-600 font-semibold">
              {type === "executive"
                ? position
                : position === "head"
                ? "Committee Head"
                : position === "deputy_head"
                ? "Deputy Head"
                : "Member"}
            </p>
            {type === "appointee" && person.committee_name && (
              <p className="text-gray-600 mt-1">{person.committee_name}</p>
            )}
          </div>

          {/* Biography Section */}
          {person.bio && (
            <div className="mb-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <Briefcase className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-bold text-gray-900">About</h3>
              </div>
              <p className="text-gray-700 leading-relaxed">{person.bio}</p>
            </div>
          )}

          {/* Portfolio/Responsibilities */}
          {type === "appointee" && person.portfolio && (
            <div className="mb-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <Briefcase className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  Portfolio & Responsibilities
                </h3>
              </div>
              <p className="text-gray-700 leading-relaxed">
                {person.portfolio}
              </p>
            </div>
          )}

          {/* Skills Section */}
          {person.skills && person.skills.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Code className="w-5 h-5 text-indigo-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  Skills & Expertise
                </h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {person.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-full text-sm font-medium shadow-md hover:shadow-lg transition-all duration-300"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Achievements Section */}
          {person.achievements && person.achievements.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Award className="w-5 h-5 text-amber-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  Achievements & Awards
                </h3>
              </div>
              <div className="space-y-2">
                {person.achievements.map((achievement, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-xl hover:shadow-md transition-all duration-300"
                  >
                    <Award className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                    <p className="text-gray-700">{achievement}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contact Information */}
          {type === "appointee" && person.contact_details && (
            <div className="mb-6 bg-gray-50 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Contact Information
              </h3>
              <div className="space-y-3">
                {person.contact_details.email && (
                  <a
                    href={`mailto:${person.contact_details.email}`}
                    className="flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors duration-300"
                  >
                    <Mail className="w-5 h-5" />
                    <span>{person.contact_details.email}</span>
                  </a>
                )}
                {person.contact_details.phone && (
                  <a
                    href={`tel:${person.contact_details.phone}`}
                    className="flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors duration-300"
                  >
                    <Phone className="w-5 h-5" />
                    <span>{person.contact_details.phone}</span>
                  </a>
                )}
                {person.contact_details.office_location && (
                  <div className="flex items-center gap-3 text-gray-700">
                    <MapPin className="w-5 h-5" />
                    <span>{person.contact_details.office_location}</span>
                  </div>
                )}
                {person.contact_details.office_hours && (
                  <div className="flex items-center gap-3 text-gray-700">
                    <Clock className="w-5 h-5" />
                    <span>{person.contact_details.office_hours}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Executive Phone */}
          {type === "executive" && person.phone && (
            <div className="mb-6 bg-gray-50 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Contact Information
              </h3>
              <a
                href={`tel:${person.phone}`}
                className="flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors duration-300"
              >
                <Phone className="w-5 h-5" />
                <span>{person.phone}</span>
              </a>
            </div>
          )}

          {/* Social Media Links */}
          {person.social_media_links &&
            person.social_media_links.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  Connect With Me
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {person.social_media_links.map((link) => {
                    const SocialIcon = getSocialIcon(link.platform);
                    const colorClass = getSocialColor(link.platform);
                    return (
                      <a
                        key={link.id}
                        href={link.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r ${colorClass} text-white rounded-xl font-medium shadow-md hover:shadow-xl hover:scale-105 transition-all duration-300 group`}
                      >
                        <SocialIcon className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
                        <span className="capitalize text-sm">
                          {link.platform}
                        </span>
                      </a>
                    );
                  })}
                </div>
              </div>
            )}

          {/* Empty State */}
          {!person.bio &&
            !person.portfolio &&
            (!person.skills || person.skills.length === 0) &&
            (!person.achievements || person.achievements.length === 0) && (
              <div className="text-center py-12">
                <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <Briefcase className="w-10 h-10 text-gray-400" />
                </div>
                <p className="text-gray-500 text-lg">
                  No portfolio information available yet.
                </p>
                <p className="text-gray-400 text-sm mt-2">
                  Check back later for updates!
                </p>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}

ProfileModal.propTypes = {
  person: PropTypes.object,
  type: PropTypes.oneOf(["executive", "appointee"]).isRequired,
  onClose: PropTypes.func.isRequired,
};
