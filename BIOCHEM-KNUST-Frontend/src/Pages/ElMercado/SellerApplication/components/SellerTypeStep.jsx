import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { SELLER_TYPES } from "../constants";

export function SellerTypeStep({ formData, onInputChange }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Seller Type</h2>
      <p className="text-gray-600 mb-8">
        Select the type that best describes how you&apos;ll be selling on El Mercado.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {SELLER_TYPES.map((type) => {
          const Icon = type.icon;
          const isSelected = formData.seller_type === type.value;

          return (
            <motion.div
              key={type.value}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onInputChange("seller_type", type.value)}
              className={`cursor-pointer rounded-2xl border-2 p-6 transition-all ${
                isSelected
                  ? "border-purple-500 bg-purple-50 ring-4 ring-purple-100"
                  : "border-gray-200 hover:border-purple-300"
              }`}
            >
              <div
                className={`w-14 h-14 rounded-xl flex items-center justify-center mb-4 ${
                  isSelected ? "bg-purple-600 text-white" : "bg-gray-100 text-gray-600"
                }`}
              >
                <Icon className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{type.label}</h3>
              <p className="text-gray-600 text-sm mb-4">{type.description}</p>
              <ul className="space-y-2">
                {type.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                    <Check className="w-4 h-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

export default SellerTypeStep;
