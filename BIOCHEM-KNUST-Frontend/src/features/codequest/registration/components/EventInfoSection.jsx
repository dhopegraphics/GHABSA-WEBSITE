import { motion } from "framer-motion";

const EventInfoSection = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          {/* Section Header */}
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              About Code Quest
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              An immersive mobile app development challenge where creativity
              meets code
            </p>
          </motion.div>

          {/* Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <InfoCard
              icon="🎯"
              title="Objective"
              description="Build innovative mobile applications that solve real-world problems using modern technologies"
              delay={0.1}
            />
            <InfoCard
              icon="👥"
              title="Team Work"
              description="Work in groups of 6-8 members with elected Project Managers and expert consultants"
              delay={0.2}
            />
            <InfoCard
              icon="📱"
              title="Technologies"
              description="React Native, Flutter, or native Android/iOS development with backend integration"
              delay={0.3}
            />
            <InfoCard
              icon="📅"
              title="Timeline"
              description="8-week intensive development period from project selection to final presentation"
              delay={0.4}
            />
            <InfoCard
              icon="🏆"
              title="Evaluation"
              description="Projects evaluated by facilitators on UI/UX, functionality, innovation, and code quality"
              delay={0.5}
            />
            <InfoCard
              icon="🎓"
              title="Mentorship"
              description="Year 3/4 student consultants provide guidance throughout the development process"
              delay={0.6}
            />
          </div>

          {/* Important Dates */}
          <motion.div
            className="mt-16 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.7 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Important Dates
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <DateCard
                title="Registration Opens"
                date="15 Jan 2025"
                icon="📝"
              />
              <DateCard
                title="Registration Closes"
                date="25 Jan 2025"
                icon="🚫"
              />
              <DateCard
                title="Development Period"
                date="1 Feb - 30 Mar"
                icon="💻"
              />
              <DateCard title="Presentation Day" date="5 Apr 2025" icon="🎤" />
            </div>
          </motion.div>

          {/* Call to Action */}
          <motion.div
            id="registration"
            className="mt-16 text-center"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Ready to Build Something Amazing?
            </h3>
            <p className="text-gray-600 mb-6">
              Choose your role below and start your Code Quest journey
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

// Info Card Component
const InfoCard = ({ icon, title, description, delay }) => {
  return (
    <motion.div
      className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-shadow border border-gray-100"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -5 }}
    >
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{description}</p>
    </motion.div>
  );
};

// Date Card Component
const DateCard = ({ title, date, icon }) => {
  return (
    <div className="text-center">
      <div className="text-4xl mb-2">{icon}</div>
      <h4 className="font-bold text-gray-900 mb-1">{title}</h4>
      <p className="text-blue-600 font-semibold">{date}</p>
    </div>
  );
};

export default EventInfoSection;
