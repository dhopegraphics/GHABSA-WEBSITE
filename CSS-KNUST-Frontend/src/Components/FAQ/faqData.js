import {
    GraduationCap,
    BookOpen,
    Briefcase,
    ShoppingBag,
    Users,
    Shield
  } from 'lucide-react';
  
  export const faqData = [
    {
      category: "Academic Resources",
      icon: GraduationCap,
      questions: [
        {
          question: "How can I access course materials?",
          answer: "Course materials are available in the Resources section, organized by year and course. Simply navigate to your year, select the course, and you'll find lecture slides, past questions, and additional study materials."
        },
        {
          question: "Are past examination questions available?",
          answer: "Yes, past examination questions are available for most courses. You can find them in the course resources section, typically under the 'Past Questions' tab."
        },
        {
          question: "How often are resources updated?",
          answer: "Resources are updated regularly throughout the semester. New materials are typically added within 24 hours of being provided by professors."
        }
      ]
    },
    {
      category: "Study Materials",
      icon: BookOpen,
      questions: [
        {
          question: "Can I download study materials for offline use?",
          answer: "Yes, most study materials can be downloaded for offline use. Look for the download icon next to each resource."
        },
        {
          question: "How do I save resources for later?",
          answer: "Click the bookmark icon on any resource to save it to your 'Saved Resources' section for quick access later."
        },
        {
          question: "Are there recommended online tutorials?",
          answer: "Yes, each course has a curated list of online tutorials and additional resources that complement the course material."
        }
      ]
    },
    {
      category: "Internships",
      icon: Briefcase,
      questions: [
        {
          question: "How do I apply for internships?",
          answer: "Each internship listing includes an 'Apply' button that will direct you to the company's application page. Make sure to note application deadlines and requirements."
        },
        {
          question: "Are internship opportunities updated regularly?",
          answer: "Yes, new internship opportunities are posted as soon as they become available. Check back regularly or enable notifications to stay updated."
        },
        {
          question: "What should I prepare for internship applications?",
          answer: "Typically, you'll need an updated resume, cover letter, and your academic transcripts. Some positions may also require a portfolio of projects."
        }
      ]
    },
    {
      category: "Merchandise",
      icon: ShoppingBag,
      questions: [
        {
          question: "How can I purchase CS Society merchandise?",
          answer: "Browse our merchandise section, add items to your cart, and proceed to checkout. We accept various payment methods including credit cards and digital payments."
        },
        {
          question: "What's the return policy?",
          answer: "Unworn merchandise can be returned within 30 days of purchase. Items must be in original condition with tags attached."
        },
        {
          question: "Do you ship internationally?",
          answer: "Currently, we only ship within the country. International shipping options are being considered for the future."
        }
      ]
    },
    {
      category: "Community",
      icon: Users,
      questions: [
        {
          question: "How can I join the CS Society?",
          answer: "Membership is open to all computer science students. Register through the 'Join Now' button on the homepage and follow the registration process."
        },
        {
          question: "Are there regular meetups or events?",
          answer: "Yes, we organize regular workshops, hackathons, and social events. Check the Events section for upcoming activities."
        },
        {
          question: "How can I contribute to the community?",
          answer: "You can contribute by sharing resources, participating in events, or joining our volunteer team. Contact us for more information."
        }
      ]
    },
    {
      category: "Account & Privacy",
      icon: Shield,
      questions: [
        {
          question: "How is my data protected?",
          answer: "We use industry-standard encryption and security measures to protect your data. Review our Privacy Policy for detailed information."
        },
        {
          question: "Can I change my account settings?",
          answer: "Yes, you can modify your account settings, including notification preferences and privacy options, in the Settings section."
        },
        {
          question: "How do I reset my password?",
          answer: "Use the 'Forgot Password' link on the login page. You'll receive instructions to reset your password via your registered email."
        }
      ]
    }
  ];