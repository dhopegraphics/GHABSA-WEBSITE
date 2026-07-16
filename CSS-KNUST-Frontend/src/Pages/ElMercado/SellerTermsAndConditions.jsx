import { motion } from "framer-motion";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { Helmet } from "react-helmet-async";
import { 
  FileText, 
  Scale, 
  ShieldCheck, 
  AlertCircle,
  CheckCircle2,
  XCircle
} from "lucide-react";

export function SellerTermsAndConditions() {
  const sections = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: "1. Agreement to Terms",
      content: [
        "By registering as a seller on El Mercado, you agree to be bound by these Terms and Conditions.",
        "These terms constitute a legally binding agreement between you and CSS KNUST El Mercado.",
        "You must be at least 18 years old and have the legal capacity to enter into contracts to become a seller.",
        "If you are registering as a business, you represent that you have the authority to bind that business to these terms."
      ]
    },
    {
      icon: <ShieldCheck className="w-6 h-6" />,
      title: "2. Seller Account",
      content: [
        "You must provide accurate, current, and complete information during registration.",
        "You are responsible for maintaining the confidentiality of your account credentials.",
        "You agree to notify us immediately of any unauthorized use of your account.",
        "El Mercado reserves the right to suspend or terminate accounts that violate these terms.",
        "One person or business may only operate one seller account unless explicitly authorized."
      ]
    },
    {
      icon: <CheckCircle2 className="w-6 h-6" />,
      title: "3. Seller Obligations",
      content: [
        "You must comply with all applicable laws and regulations in your jurisdiction.",
        "Products and services must be accurately described, including condition, specifications, and limitations.",
        "You must honor all sales and maintain reasonable response times to customer inquiries.",
        "Shipping and delivery timelines must be clearly stated and adhered to.",
        "You are responsible for customer service, returns, and refunds according to El Mercado policies.",
        "You must maintain adequate inventory or clearly indicate when items are out of stock."
      ]
    },
    {
      icon: <XCircle className="w-6 h-6" />,
      title: "4. Prohibited Activities",
      content: [
        "Selling counterfeit, illegal, or prohibited items as defined by Ghana law.",
        "Engaging in fraudulent activities, including misrepresenting products or services.",
        "Manipulating reviews, ratings, or search rankings through artificial means.",
        "Harassing, threatening, or abusing buyers or other sellers.",
        "Attempting to circumvent El Mercado's payment system or fees.",
        "Infringing on intellectual property rights of others.",
        "Selling weapons, drugs, or other items prohibited by El Mercado policy."
      ]
    },
    {
      icon: <Scale className="w-6 h-6" />,
      title: "5. Pricing and Payments",
      content: [
        "You are responsible for setting your own prices for products and services.",
        "All prices must be listed in Ghana Cedis (GHS) unless otherwise specified.",
        "Platform commission fees will be deducted from each sale as outlined in the Commission Policy.",
        "Payments will be processed according to the payout schedule and minimum thresholds.",
        "You are responsible for all applicable taxes on your sales.",
        "El Mercado reserves the right to hold payments in cases of disputes or suspected fraud."
      ]
    },
    {
      icon: <AlertCircle className="w-6 h-6" />,
      title: "6. Intellectual Property",
      content: [
        "You retain ownership of the content you post, but grant El Mercado a license to use it.",
        "You warrant that you have the right to sell all items listed and use all content posted.",
        "El Mercado's trademarks, logos, and branding remain the property of CSS KNUST.",
        "You may not use El Mercado's intellectual property without express written permission."
      ]
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: "7. Listing Policies",
      content: [
        "All listings must include clear, accurate photos of the actual item being sold.",
        "Product descriptions must not be misleading or contain false information.",
        "Listings must be placed in the appropriate category.",
        "El Mercado reserves the right to remove, edit, or reclassify listings at its discretion.",
        "Duplicate listings for the same item are not permitted.",
        "Listings must comply with El Mercado's content and image guidelines."
      ]
    },
    {
      icon: <ShieldCheck className="w-6 h-6" />,
      title: "8. Customer Data and Privacy",
      content: [
        "You must comply with all applicable data protection and privacy laws.",
        "Customer personal information must be used only for order fulfillment.",
        "You may not share, sell, or misuse customer data obtained through El Mercado.",
        "You must maintain appropriate security measures to protect customer information."
      ]
    },
    {
      icon: <Scale className="w-6 h-6" />,
      title: "9. Disputes and Resolution",
      content: [
        "You agree to work in good faith to resolve disputes with buyers.",
        "El Mercado may mediate disputes at its discretion.",
        "El Mercado's decision in dispute resolution is final and binding.",
        "You may be required to issue refunds or accept returns according to El Mercado policy.",
        "Persistent disputes or poor seller performance may result in account suspension."
      ]
    },
    {
      icon: <AlertCircle className="w-6 h-6" />,
      title: "10. Liability and Indemnification",
      content: [
        "You are solely responsible for your products, services, and business operations.",
        "El Mercado is not liable for any losses arising from your use of the platform.",
        "You agree to indemnify El Mercado against claims arising from your activities as a seller.",
        "El Mercado's total liability to you shall not exceed the fees paid in the last 12 months."
      ]
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: "11. Account Suspension and Termination",
      content: [
        "El Mercado may suspend or terminate your account for violation of these terms.",
        "You may close your account at any time, subject to outstanding obligations.",
        "Upon termination, you must fulfill all pending orders and resolve outstanding issues.",
        "El Mercado may withhold payments if there are unresolved disputes or policy violations.",
        "Terminated sellers may not create new accounts without explicit permission."
      ]
    },
    {
      icon: <CheckCircle2 className="w-6 h-6" />,
      title: "12. Changes to Terms",
      content: [
        "El Mercado reserves the right to modify these terms at any time.",
        "Material changes will be communicated to sellers via email or platform notification.",
        "Continued use of the platform after changes constitutes acceptance of new terms.",
        "You are responsible for regularly reviewing these terms."
      ]
    }
  ];

  return (
    <>
      <Helmet>
        <title>Seller Terms &amp; Conditions | El Mercado - CSS KNUST</title>
        <meta name="description" content="Read the seller terms and conditions for El Mercado, the official CSS KNUST marketplace platform." />
      </Helmet>

      <div className="min-h-screen flex flex-col bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <Navbar />

        <main className="flex-grow pt-24 pb-16 px-4">
          <div className="max-w-5xl mx-auto">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl mb-6">
                <FileText className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Seller Terms &amp; Conditions
              </h1>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Please read these terms carefully before becoming a seller on El Mercado
              </p>
              <div className="mt-6 text-sm text-gray-500">
                Last Updated: January 15, 2026
              </div>
            </motion.div>

            {/* Introduction */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl shadow-xl p-8 mb-8"
            >
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Introduction</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Welcome to El Mercado, the official marketplace platform of the Computer Science Students&apos; 
                Society (CSS) at Kwame Nkrumah University of Science and Technology (KNUST). These Seller 
                Terms and Conditions govern your use of El Mercado as a seller and establish the rights and 
                responsibilities between you and the platform.
              </p>
              <p className="text-gray-700 leading-relaxed">
                El Mercado is designed to facilitate both Business-to-Consumer (B2C) and Peer-to-Peer (P2P) 
                commerce within the KNUST community and beyond. By registering as a seller, you become part 
                of a trusted marketplace ecosystem and agree to uphold the standards outlined in these terms.
              </p>
            </motion.div>

            {/* Terms Sections */}
            <div className="space-y-6">
              {sections.map((section, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + index * 0.05 }}
                  className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow"
                >
                  <div className="flex items-start gap-4 mb-6">
                    <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-purple-100 to-blue-100 rounded-xl flex items-center justify-center text-purple-600">
                      {section.icon}
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mt-2">
                      {section.title}
                    </h2>
                  </div>
                  <ul className="space-y-3">
                    {section.content.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-gray-700">
                        <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{item}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </div>

            {/* Contact Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl shadow-xl p-8 mt-12 text-white"
            >
              <h2 className="text-2xl font-bold mb-4">Questions or Concerns?</h2>
              <p className="text-purple-100 mb-6">
                If you have any questions about these Seller Terms and Conditions, please contact us:
              </p>
              <div className="space-y-2 text-purple-100">
                <p><strong className="text-white">Email:</strong> info@thecssknust.com</p>
                <p><strong className="text-white">Support Portal:</strong> Available through your seller dashboard</p>
                <p><strong className="text-white">Office:</strong> CSS KNUST Office, Department of Computer Science</p>
              </div>
            </motion.div>

            {/* Acceptance Notice */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
              className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6 mt-8"
            >
              <div className="flex items-start gap-4">
                <AlertCircle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-orange-900 mb-2">
                    Acknowledgment and Acceptance
                  </h3>
                  <p className="text-orange-800 leading-relaxed">
                    By submitting a seller application or continuing to use El Mercado as a seller, you 
                    acknowledge that you have read, understood, and agree to be bound by these Seller Terms 
                    and Conditions, as well as our Commission Policy and Privacy Policy.
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="flex flex-col sm:flex-row gap-4 justify-center mt-12"
            >
              <a
                href="/el-mercado/become-a-seller"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-bold hover:from-purple-700 hover:to-blue-700 transition-all hover:shadow-xl transform hover:-translate-y-1"
              >
                Apply to Become a Seller
              </a>
              <a
                href="/el_mercado/commission-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white border-2 border-purple-600 text-purple-600 rounded-xl font-bold hover:bg-purple-50 transition-all"
              >
                View Commission Policy
              </a>
            </motion.div>
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default SellerTermsAndConditions;
