import { useState } from "react";
import { Star, MapPin, Clock, Package, Shield, Award, TrendingUp, MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { ContactSellerModal } from "./ContactSellerModal";

export function SellerInfoSection({ seller, listing = null, onSignInClick }) {
  const [showContactModal, setShowContactModal] = useState(false);

  if (!seller) return null;

  return (
    <div className="space-y-8">
      {/* Seller Header */}
      <div className="flex items-start gap-6">
        <div className="w-24 h-24 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg overflow-hidden">
          {seller.logo_url ? (
            <img src={seller.logo_url} alt={seller.business_name} className="w-full h-full object-cover" />
          ) : (
            seller.business_name?.charAt(0) || "S"
          )}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-gray-900">{seller.business_name}</h2>
            {seller.is_verified && (
              <span className="bg-blue-100 text-blue-700 text-sm px-3 py-1 rounded-full flex items-center gap-1">
                <Shield className="w-4 h-4" />
                Verified Seller
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">{seller.seller_type_display || "Seller"}</p>
          
          {/* Quick Stats */}
          <div className="flex items-center gap-6 flex-wrap">
            {seller.average_rating > 0 && (
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                <span className="font-semibold text-gray-900">{seller.average_rating?.toFixed(1)}</span>
                <span className="text-sm text-gray-500">({seller.total_reviews} reviews)</span>
              </div>
            )}
            {seller.total_products > 0 && (
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-gray-400" />
                <span className="text-gray-700">{seller.total_products} products</span>
              </div>
            )}
            {seller.total_sales > 0 && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span className="text-gray-700">{seller.total_sales} sales</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Seller Description */}
      {seller.description && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">About This Seller</h3>
          <p className="text-gray-700 leading-relaxed">{seller.description}</p>
        </div>
      )}

      {/* Business Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Location */}
        {seller.business_location && (
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Location</h4>
                <p className="text-sm text-gray-600">{seller.business_location}</p>
              </div>
            </div>
          </div>
        )}

        {/* Member Since */}
        {seller.created_at && (
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Member Since</h4>
                <p className="text-sm text-gray-600">
                  {new Date(seller.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long'
                  })}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Seller Policies */}
      <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-blue-600" />
          Seller Policies
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-1">Return Policy</h4>
            <p className="text-sm text-gray-600">
              {seller.return_policy || "Returns accepted within 7 days of delivery"}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-1">Shipping</h4>
            <p className="text-sm text-gray-600">
              {seller.shipping_policy || "Items ship within 2-3 business days"}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-1">Response Time</h4>
            <p className="text-sm text-gray-600">
              Usually responds within 24 hours
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-1">Accepted Payments</h4>
            <p className="text-sm text-gray-600">
              Mobile Money, Credit/Debit Cards
            </p>
          </div>
        </div>
      </div>

      {/* Rating Breakdown */}
      {seller.average_rating > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Seller Ratings</h3>
          <div className="space-y-3">
            {[
              { label: 'Communication', value: seller.communication_rating || seller.average_rating },
              { label: 'Shipping Speed', value: seller.shipping_rating || seller.average_rating },
              { label: 'Product Quality', value: seller.quality_rating || seller.average_rating },
              { label: 'As Described', value: seller.accuracy_rating || seller.average_rating },
            ].map((item, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-700 w-32">{item.label}</span>
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-600 transition-all"
                    style={{ width: `${(item.value / 5) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8">{item.value.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => setShowContactModal(true)}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors shadow-lg hover:shadow-xl"
        >
          <MessageCircle className="w-5 h-5" />
          Contact Seller
        </button>
        <Link
          to={`/el-mercado/store/${seller.slug}`}
          className="flex-1 text-center py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
        >
          Visit Store
        </Link>
      </div>

      {/* Contact Seller Modal */}
      <ContactSellerModal
        isOpen={showContactModal}
        onClose={() => setShowContactModal(false)}
        seller={seller}
        listing={listing}
        onSignInClick={onSignInClick}
      />
    </div>
  );
}

export default SellerInfoSection;
