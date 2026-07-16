import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ParticipantRegistrationForm from "./components/ParticipantRegistrationForm";
import ConsultantRegistrationForm from "./components/ConsultantRegistrationForm";
import HeroSection from "./components/HeroSection";
import EventInfoSection from "./components/EventInfoSection";

const RegistrationPage = () => {
  const [activeTab, setActiveTab] = useState("participant");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <HeroSection />

      {/* Event Info */}
      <EventInfoSection />

      {/* Registration Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            {/* Tab Switcher */}
            <div className="flex gap-4 mb-8">
              <TabButton
                active={activeTab === "participant"}
                onClick={() => setActiveTab("participant")}
                icon="🎓"
                title="I'm a Participant"
                description="Year 2 or Deferred Student"
              />
              <TabButton
                active={activeTab === "consultant"}
                onClick={() => setActiveTab("consultant")}
                icon="👨‍🏫"
                title="I'm a Consultant"
                description="Year 3/4 Mentor"
              />
            </div>

            {/* Tab Content */}
            <motion.div
              className="bg-white rounded-2xl shadow-xl p-8 md:p-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <AnimatePresence mode="wait">
                {activeTab === "participant" ? (
                  <motion.div
                    key="participant"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ParticipantRegistrationForm />
                  </motion.div>
                ) : (
                  <motion.div
                    key="consultant"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ConsultantRegistrationForm />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Frequently Asked Questions
            </h2>
            <FAQAccordion />
          </div>
        </div>
      </section>
    </div>
  );
};

// Tab Button Component
const TabButton = ({ active, onClick, icon, title, description }) => {
  return (
    <button
      onClick={onClick}
      className={`
        flex-1 p-6 rounded-xl border-2 transition-all duration-300 text-left
        ${
          active
            ? "border-blue-600 bg-blue-50 shadow-lg scale-105"
            : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
        }
      `}
    >
      <div className="flex items-start gap-4">
        <span className="text-4xl">{icon}</span>
        <div>
          <h3
            className={`text-lg font-bold mb-1 ${
              active ? "text-blue-600" : "text-gray-900"
            }`}
          >
            {title}
          </h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </button>
  );
};

// FAQ Accordion Component
const FAQAccordion = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: "Who can participate in Code Quest?",
      answer:
        "All Year 2 students and deferred students (Year 3/4) who need to complete the Mobile App Development course can participate.",
    },
    {
      question: "How are groups formed?",
      answer:
        "Groups are formed automatically by the admin based on your registration details. Regular students and deferred students are grouped separately.",
    },
    {
      question: "What happens after I register?",
      answer:
        "You will receive an access key via email. Use this key to login to your participant portal where you can view your group, vote for PM, and track your progress.",
    },
    {
      question: "Can I be a consultant and participant?",
      answer:
        "No, you can only register as either a participant or a consultant, not both.",
    },
    {
      question: "What if I lose my access key?",
      answer:
        "Contact the admin team at admin@biochemknust.com to recover your access key.",
    },
  ];

  return (
    <div className="space-y-4">
      {faqs.map((faq, index) => (
        <div
          key={index}
          className="border border-gray-200 rounded-lg overflow-hidden"
        >
          <button
            onClick={() => setOpenIndex(openIndex === index ? null : index)}
            className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <span className="font-semibold text-gray-900">{faq.question}</span>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${
                openIndex === index ? "rotate-180" : ""
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          <AnimatePresence>
            {openIndex === index && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: "auto" }}
                exit={{ height: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="p-4 pt-0 text-gray-600">{faq.answer}</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
};

export default RegistrationPage;
