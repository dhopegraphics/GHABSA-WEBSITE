
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
        <title>Home | BIO-CHEM KNUST</title>
        <meta
          name="description"
          content="Welcome to the official platform of the Biochemistry Society, KNUST. Get updates on events, blogs, and more."
        />
        <meta
          name="keywords"
          content="BIO-CHEM KNUST, Computer Science KNUST, biochem knust, knust, biochemknust"
        />
        <meta name="robots" content="index, nofollow" />
        <meta property="og:title" content="BIO-CHEM KNUST - Home" />
        <meta
          property="og:description"
          content="Discover the tech heartbeat of KNUST!"
        />
        <meta
          property="og:image"
          content="https://biochemknust.com/images/logo.png"
        />
        <meta property="og:url" content="https://biochemknust.com/" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollegeOrUniversity",
            name: "Biochemistry Society, KNUST",
            url: "https://biochemknust.com",
            logo: "https://biochemknust.com/images/logo.png",
            description:
              "The official Biochemistry Society, KNUST. Empowering students through tech, innovation, and community.",
            sameAs: [
              "https://x.com/thebiochemknust",
              "https://t.me/thebiochemknust",
              "https://linkedin.com/in/thebiochemknust",
              "https://instagram.com/thebiochemknust",
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
