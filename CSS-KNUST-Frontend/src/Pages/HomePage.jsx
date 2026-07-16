
import Navbar from "../Components/Navbar";
import Hero from "../Components/Hero/Hero";

import { Feature } from "../Components/Feature";

import { EventsTimeline } from "../Components/Events/EventsTimeline";
import { BlogSection } from "../Components/Blog/BlogSection";
import { TeamSection } from "../Components/Team/TeamSection";
import { Footer } from "../Components/Footer/Footer";
import { ResourcesSection } from "../Components/Resources/ResourcesSection";


import { InternshipsSection } from "../Components/Internships/InternshipsSection";
import { Helmet } from "react-helmet-async";

function HomePage() {





  return (
    <>
      <Helmet>
        <title>Home | CSS KNUST</title>
        <meta
          name="description"
          content="Welcome to the official platform of the Computer Science Society of KNUST. Get updates on events, blogs, and more."
        />
        <meta
          name="keywords"
          content="CSS KNUST, Computer Science KNUST, css knust, knust, thecssknust"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="CSS KNUST - Home" />
        <meta
          property="og:description"
          content="Discover the tech heartbeat of KNUST!"
        />
        <meta
          property="og:image"
          content="https://thecssknust.com/images/css.png"
        />
        <meta property="og:url" content="https://thecssknust.com/" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollegeOrUniversity",
            name: "Computer Science Society, KNUST",
            url: "https://thecssknust.com",
            logo: "https://thecssknust.com/images/css.png",
            description:
              "The official Computer Science Society of KNUST. Empowering students through tech, innovation, and community.",
            sameAs: [
              "https://x.com/thecssknust",
              "https://t.me/thecssknust",
              "https://linkedin.com/in/thecssknust-original",
              "https://instagram.com/thecssknust",
            ],
            address: {
              "@type": "PostalAddress",
              addressLocality: "Kumasi",
              addressRegion: "Ashanti Region",
              addressCountry: "GH",
            },
          })}
        </script>
      </Helmet>

      <div className="relative">
        <Navbar />

        {/* <DotBackground> */}
        <Hero  />

        <Feature />
        <EventsTimeline />
        <ResourcesSection />
        <InternshipsSection />
        <BlogSection />
        <TeamSection />
        <Footer />
        {/* </DotBackground> */}
       
      </div>
    </>
  );
}

export default HomePage;
