import { 
  Store, 
  User, 
  MapPin, 
  FileText, 
  CheckCircle2, 
  Briefcase,
  Edit3 
} from "lucide-react";
import { SELLER_TYPES, ID_DOCUMENT_TYPES } from "../constants";

export function ReviewStep({ formData, fileNames, categories, isEditMode }) {
  // Helper to find category by ID
  const findCategory = (catId) => {
    for (const parent of categories) {
      if (parent.id === catId) return parent;
      if (parent.children) {
        const child = parent.children.find((c) => c.id === catId);
        if (child) return child;
      }
    }
    return null;
  };

  const isBusiness = formData.seller_type === "BUSINESS";

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        {isEditMode ? "Review Your Changes" : "Review Your Application"}
      </h2>
      <p className="text-gray-600 mb-4">
        {isEditMode
          ? "Review the changes before updating your application."
          : "Please review your information before submitting."}
      </p>

      {/* Edit mode notice */}
      {isEditMode && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6 flex items-start gap-3">
          <Edit3 className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-orange-800 font-medium">Updating Existing Application</p>
            <p className="text-orange-700">
              Only fields you&apos;ve changed will be updated. Documents that weren&apos;t
              re-uploaded will remain unchanged.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Seller Type */}
        <div className="bg-gray-50 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <Store className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Seller Type</h3>
          </div>
          <p className="text-gray-700">
            {SELLER_TYPES.find((t) => t.value === formData.seller_type)?.label}
          </p>
        </div>

        {/* Personal Info */}
        <div className="bg-gray-50 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <User className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Personal Information</h3>
          </div>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Name</p>
              <p className="text-gray-900 font-medium">{formData.applicant_name}</p>
            </div>
            <div>
              <p className="text-gray-500">Email</p>
              <p className="text-gray-900 font-medium">{formData.applicant_email}</p>
            </div>
            <div>
              <p className="text-gray-500">Phone</p>
              <p className="text-gray-900 font-medium">{formData.applicant_phone}</p>
            </div>
          </div>
        </div>

        {/* Address */}
        <div className="bg-gray-50 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <MapPin className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Address</h3>
          </div>
          <p className="text-gray-700">
            {formData.address_line_1}
            {formData.address_line_2 && `, ${formData.address_line_2}`}
            <br />
            {formData.city}, {formData.region}, {formData.country}
          </p>
        </div>

        {/* Documents */}
        <div className="bg-gray-50 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <FileText className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Documents</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span className="text-gray-700">
                {ID_DOCUMENT_TYPES.find((t) => t.value === formData.id_document_type)?.label}:{" "}
                {fileNames.id_document}
              </span>
            </div>
            {fileNames.proof_of_address && (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-gray-700">
                  Proof of Address: {fileNames.proof_of_address}
                </span>
              </div>
            )}
            {fileNames.business_document && (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-gray-700">
                  Business Document: {fileNames.business_document}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Business/Seller Info */}
        <div className="bg-gray-50 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <Briefcase className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">
              {isBusiness ? "Business Details" : "Seller Profile"}
            </h3>
          </div>
          {isBusiness && (
            <div className="grid md:grid-cols-2 gap-4 text-sm mb-4">
              <div>
                <p className="text-gray-500">Business Name</p>
                <p className="text-gray-900 font-medium">{formData.business_name}</p>
              </div>
              {formData.business_type && (
                <div>
                  <p className="text-gray-500">Business Type</p>
                  <p className="text-gray-900 font-medium">{formData.business_type}</p>
                </div>
              )}
            </div>
          )}
          <div>
            <p className="text-gray-500 text-sm mb-2">Description</p>
            <p className="text-gray-700 text-sm">{formData.description}</p>
          </div>

          {/* Selected Categories */}
          {formData.categories_of_interest.length > 0 && (
            <div className="mt-4">
              <p className="text-gray-500 text-sm mb-2">Categories of Interest</p>
              <div className="flex flex-wrap gap-2">
                {formData.categories_of_interest.map((catId) => {
                  const category = findCategory(catId);
                  return category ? (
                    <span
                      key={catId}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full"
                    >
                      {category.icon && <span>{category.icon}</span>}
                      {category.name}
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          )}
        </div>

        {/* Terms */}
        <div className="bg-purple-50 rounded-xl p-5">
          <p className="text-sm text-purple-800">
            By submitting this application, you agree to El Mercado&apos;s{" "}
            <a 
              href="/el_mercado/seller-terms" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold underline hover:text-purple-900 transition-colors"
            >
              Seller Terms &amp; Conditions
            </a>{" "}
            and{" "}
            <a 
              href="/el_mercado/commission-policy" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold underline hover:text-purple-900 transition-colors"
            >
              Commission Policy
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

export default ReviewStep;
