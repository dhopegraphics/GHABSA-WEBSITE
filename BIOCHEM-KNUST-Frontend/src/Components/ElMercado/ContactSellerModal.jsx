import { useState, useContext, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  X,
  Send,
  Loader2,
  MessageCircle,
  Store,
  Package,
  AlertCircle,
  LogIn,
  Sparkles,
} from "lucide-react";
import { useElMercado } from "../../Context/ElMercadoContext";
import { UserContext } from "../../Context/UserContext";

// Generate dynamic starter message based on listing
const generateStarterMessage = (listing, seller) => {
  if (!listing) {
    return `Hi ${seller?.display_name || seller?.business_name || 'there'}! I came across your store on El Mercado and I'm interested in learning more about your products. Could you help me with some information?`;
  }

  const sellerName = seller?.display_name || seller?.business_name || 'there';
  const productTitle = listing.title || 'this item';
  const price = listing.price ? `GHS ${parseFloat(listing.price).toFixed(2)}` : '';
  
  // Different message templates based on listing type
  const templates = [
    `Hi ${sellerName}! I'm interested in your "${productTitle}"${price ? ` listed at ${price}` : ''}. Is it still available? I'd love to know more about it.`,
    `Hello! I saw your listing for "${productTitle}" on El Mercado and I'm very interested. Could you tell me more about the condition and if you offer any delivery options?`,
    `Hi ${sellerName}! I'm reaching out about "${productTitle}". ${price ? `I noticed it's priced at ${price}. ` : ''}Is the price negotiable? Also, when would be the earliest I could get it?`,
  ];
  
  // Select template based on listing ID - handle both number and UUID string
  let templateIndex = 0;
  if (listing.id) {
    if (typeof listing.id === 'number') {
      templateIndex = listing.id % templates.length;
    } else if (typeof listing.id === 'string') {
      // Hash the string to get a consistent number
      let hash = 0;
      for (let i = 0; i < listing.id.length; i++) {
        hash = ((hash << 5) - hash) + listing.id.charCodeAt(i);
        hash = hash & hash; // Convert to 32bit integer
      }
      templateIndex = Math.abs(hash) % templates.length;
    }
  }
  
  return templates[templateIndex];
};

export function ContactSellerModal({ 
  isOpen, 
  onClose, 
  seller, 
  listing = null,
  onSignInClick 
}) {
  // Generate starter message
  const starterMessage = generateStarterMessage(listing, seller);
  
  const [message, setMessage] = useState(starterMessage);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const { startConversation } = useElMercado();
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  
  const isAuthenticated = !!user;
  
  // Update message when modal opens or listing changes
  useEffect(() => {
    if (isOpen) {
      const newMessage = generateStarterMessage(listing, seller);
      console.log("Setting starter message:", newMessage, "listing:", listing, "seller:", seller);
      setMessage(newMessage);
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, listing?.id, seller?.id]);
  
  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) {
      // Small delay to prevent flash during close animation
      const timer = setTimeout(() => {
        setMessage("");
        setError(null);
        setSuccess(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message?.trim()) {
      setError("Please enter a message");
      return;
    }
    
    setSending(true);
    setError(null);
    
    const result = await startConversation(
      seller.id,
      listing?.id || null,
      message.trim()
    );
    
    if (result.success) {
      setSuccess(true);
      setTimeout(() => {
        onClose();
        navigate(`/el-mercado/messages/${result.data.id}`);
      }, 1500);
    } else {
      setError(result.error);
    }
    
    setSending(false);
  };

  const handleSignIn = () => {
    onClose();
    if (onSignInClick) {
      onSignInClick();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 text-white">
                    <MessageCircle className="w-6 h-6" />
                    <h2 className="text-lg font-semibold">Contact Seller</h2>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-white/80 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              {/* Content */}
              <div className="p-6">
                {!isAuthenticated ? (
                  /* Not logged in state */
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <LogIn className="w-8 h-8 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Sign In Required
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Please sign in to contact {seller?.display_name || seller?.business_name}
                    </p>
                    <button
                      onClick={handleSignIn}
                      className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                    >
                      Sign In
                    </button>
                  </div>
                ) : success ? (
                  /* Success state */
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <MessageCircle className="w-8 h-8 text-green-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Message Sent!
                    </h3>
                    <p className="text-gray-600">
                      Redirecting to your conversation...
                    </p>
                  </div>
                ) : (
                  /* Contact form */
                  <>
                    {/* Seller Info */}
                    <div className="flex items-center gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
                      <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-xl font-bold shadow-lg">
                        {seller?.logo_url ? (
                          <img 
                            src={seller.logo_url} 
                            alt={seller.display_name} 
                            className="w-full h-full object-cover rounded-xl"
                          />
                        ) : (
                          seller?.display_name?.charAt(0) || seller?.business_name?.charAt(0) || "S"
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Store className="w-4 h-4 text-gray-400" />
                          <span className="font-semibold text-gray-900">
                            {seller?.display_name || seller?.business_name}
                          </span>
                          {seller?.is_verified && (
                            <span className="text-blue-500 text-xs">✓</span>
                          )}
                        </div>
                        {listing && (
                          <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
                            <Package className="w-4 h-4 text-gray-400" />
                            <span className="truncate">{listing.title}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Error */}
                    {error && (
                      <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{error}</span>
                      </div>
                    )}
                    
                    {/* Message Form */}
                    <form onSubmit={handleSubmit}>
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <label className="block text-sm font-medium text-gray-700">
                            Your Message
                          </label>
                          {listing && (
                            <button
                              type="button"
                              onClick={() => {
                                if (message === starterMessage) {
                                  setMessage("");
                                } else {
                                  setMessage(starterMessage);
                                }
                              }}
                              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
                            >
                              <Sparkles className="w-3.5 h-3.5" />
                              {message === starterMessage ? "Write my own" : "Use suggested"}
                            </button>
                          )}
                        </div>
                        
                        {/* Starter message indicator */}
                        {listing && message === starterMessage && (
                          <div className="mb-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-lg">
                            <p className="text-xs text-blue-700 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5" />
                              AI-suggested message based on the product. Feel free to edit!
                            </p>
                          </div>
                        )}
                        
                        <textarea
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          placeholder={`Hi! I'm interested in ${listing ? `"${listing.title}"` : 'your products'}...`}
                          rows={5}
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                          disabled={sending}
                        />
                      </div>
                      
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={onClose}
                          disabled={sending}
                          className="flex-1 px-4 py-3 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={sending || !message?.trim()}
                          className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          {sending ? (
                            <>
                              <Loader2 className="w-5 h-5 animate-spin" />
                              Sending...
                            </>
                          ) : (
                            <>
                              <Send className="w-5 h-5" />
                              Send Message
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                    
                    {/* Tip */}
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
                      <p className="text-xs text-gray-600 text-center">
                        <span className="font-medium text-gray-700">Powered by CSS El Mercado</span> — Your trusted campus marketplace
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default ContactSellerModal;
