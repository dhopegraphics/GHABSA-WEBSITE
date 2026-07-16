import { Building2, Upload, CheckCircle2, Check, AlertCircle } from "lucide-react";
import { BUSINESS_TYPES } from "../constants";

export function BusinessInfoStep({
  formData,
  fileNames,
  categories,
  onInputChange,
  onFileChange,
  onCategoryToggle,
}) {
  const isBusiness = formData.seller_type === "BUSINESS";

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        {isBusiness ? "Business Information" : "Seller Profile"}
      </h2>
      <p className="text-gray-600 mb-8">
        {isBusiness ? "Provide details about your business." : "Tell us what you plan to sell."}
      </p>

      <div className="space-y-6">
        {isBusiness && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Name *
              </label>
              <div className="relative">
                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.business_name}
                  onChange={(e) => onInputChange("business_name", e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="Your business name"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Registration Number
                </label>
                <input
                  type="text"
                  value={formData.business_registration_number}
                  onChange={(e) => onInputChange("business_registration_number", e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g., BN-123456"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Type
                </label>
                <select
                  value={formData.business_type}
                  onChange={(e) => onInputChange("business_type", e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                >
                  <option value="">Select Type</option>
                  {BUSINESS_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Registration Document *
              </label>
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
                  fileNames.business_document
                    ? "border-green-400 bg-green-50"
                    : "border-gray-300 hover:border-blue-400"
                }`}
              >
                <input
                  type="file"
                  id="business_document"
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={(e) => onFileChange("business_document", e)}
                  className="hidden"
                />
                <label htmlFor="business_document" className="cursor-pointer">
                  {fileNames.business_document ? (
                    <div className="flex items-center justify-center gap-3">
                      <CheckCircle2 className="w-8 h-8 text-green-600" />
                      <div className="text-left">
                        <p className="font-medium text-green-700">{fileNames.business_document}</p>
                        <p className="text-sm text-green-600">Click to change file</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600">Upload business registration certificate</p>
                    </>
                  )}
                </label>
              </div>
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What do you plan to sell? *
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => onInputChange("description", e.target.value)}
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
            placeholder="Describe the products or services you plan to offer on El Mercado..."
          />
        </div>

        {categories.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Categories of Interest *
            </label>
            <p className="text-sm text-gray-500 mb-4">
              Select the categories that best describe what you plan to sell
            </p>

            <div className="space-y-4">
              {categories
                .filter((cat) => !cat.parent)
                .map((parentCategory) => (
                  <div key={parentCategory.id} className="border border-gray-200 rounded-xl p-4">
                    <button
                      type="button"
                      onClick={() => onCategoryToggle(parentCategory.id)}
                      className={`flex items-center gap-3 w-full text-left mb-3 p-2 rounded-lg transition-all ${
                        formData.categories_of_interest.includes(parentCategory.id)
                          ? "bg-blue-100 ring-2 ring-blue-500"
                          : "hover:bg-gray-50"
                      }`}
                    >
                      <span className="text-2xl">{parentCategory.icon}</span>
                      <div className="flex-1">
                        <span className="font-semibold text-gray-900">{parentCategory.name}</span>
                        {parentCategory.description && (
                          <p className="text-xs text-gray-500">{parentCategory.description}</p>
                        )}
                      </div>
                      {formData.categories_of_interest.includes(parentCategory.id) && (
                        <Check className="w-5 h-5 text-blue-600" />
                      )}
                    </button>

                    {parentCategory.children && parentCategory.children.length > 0 && (
                      <div className="flex flex-wrap gap-2 pl-2">
                        {parentCategory.children.map((subCategory) => {
                          const isSelected = formData.categories_of_interest.includes(
                            subCategory.id
                          );
                          return (
                            <button
                              key={subCategory.id}
                              type="button"
                              onClick={() => onCategoryToggle(subCategory.id)}
                              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm transition-all ${
                                isSelected
                                  ? "bg-purple-600 text-white"
                                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                              }`}
                            >
                              {subCategory.icon && <span className="text-sm">{subCategory.icon}</span>}
                              {subCategory.name}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))}
            </div>

            {formData.categories_of_interest.length > 0 && (
              <p className="mt-4 text-sm text-blue-600 font-medium">
                {formData.categories_of_interest.length} categor
                {formData.categories_of_interest.length === 1 ? "y" : "ies"} selected
              </p>
            )}
          </div>
        )}

        {categories.length === 0 && (
          <div className="bg-yellow-50 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-yellow-800 font-medium">Categories loading...</p>
              <p className="text-yellow-700 text-sm">
                Categories will be available shortly. You can proceed without selecting any.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BusinessInfoStep;
