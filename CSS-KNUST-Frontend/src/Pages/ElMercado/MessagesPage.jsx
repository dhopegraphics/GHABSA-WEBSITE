import { useEffect, useState, useCallback, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  MessageCircle,
  Search,
  Store,
  Package,
  ChevronRight,
  Inbox,
  AlertCircle,
  LogIn,
  Heart,
  ArrowLeft,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { UserContext } from "../../Context/UserContext";

// Format relative time
const formatRelativeTime = (date) => {
  if (!date) return "";
  
  const now = new Date();
  const messageDate = new Date(date);
  
  // Check if date is valid
  if (isNaN(messageDate.getTime())) return "";
  
  const diffMs = now - messageDate;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return messageDate.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });
};

// Conversation Card Component
function ConversationCard({ conversation, onClick }) {
  const otherParty = conversation.other_party;
  const hasUnread = conversation.unread_count > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={`bg-white rounded-xl shadow-sm border cursor-pointer transition-all hover:shadow-md ${
        hasUnread ? "border-blue-200 bg-blue-50/30" : "border-gray-100"
      }`}
    >
      <div className="p-4 flex items-start gap-4">
        {/* Avatar */}
        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-xl font-bold shadow flex-shrink-0 overflow-hidden">
          {otherParty?.logo_url ? (
            <img 
              src={otherParty.logo_url} 
              alt={otherParty.name} 
              className="w-full h-full object-cover"
            />
          ) : (
            otherParty?.name?.charAt(0) || "?"
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              {otherParty?.type === "seller" ? (
                <Store className="w-4 h-4 text-gray-400" />
              ) : (
                <MessageCircle className="w-4 h-4 text-gray-400" />
              )}
              <span className={`font-semibold truncate ${hasUnread ? "text-gray-900" : "text-gray-700"}`}>
                {otherParty?.name || "Unknown"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {conversation.last_message_at && (
                <span className="text-xs text-gray-500">
                  {formatRelativeTime(conversation.last_message_at)}
                </span>
              )}
              {hasUnread && (
                <span className="bg-blue-600 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {conversation.unread_count}
                </span>
              )}
            </div>
          </div>
          
          {/* Listing context */}
          {conversation.listing_title && (
            <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5">
              <Package className="w-3.5 h-3.5" />
              <span className="truncate">{conversation.listing_title}</span>
            </div>
          )}
          
          {/* Last message preview */}
          <p className={`text-sm truncate ${hasUnread ? "text-gray-900 font-medium" : "text-gray-500"}`}>
            {conversation.last_message_preview || "No messages yet"}
          </p>
        </div>
        
        {/* Arrow */}
        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
      </div>
    </motion.div>
  );
}

// Empty State
function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center"
    >
      <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Inbox className="w-10 h-10 text-blue-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        No Messages Yet
      </h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">
        Start a conversation by contacting a seller about their products or services.
      </p>
      <Link
        to="/el-mercado/browse"
        className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        Browse Products
      </Link>
    </motion.div>
  );
}

// Loading Skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 bg-gray-200 rounded-xl animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
              <div className="h-3 bg-gray-200 rounded w-1/4 animate-pulse" />
              <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Not Authenticated State
function NotAuthenticatedState({ onSignIn }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center"
    >
      <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <LogIn className="w-10 h-10 text-blue-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        Sign In Required
      </h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">
        Please sign in to view your messages and conversations with sellers.
      </p>
      <button
        onClick={onSignIn}
        className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        Sign In
      </button>
    </motion.div>
  );
}

// Main Messages Page
export function MessagesPage() {
  const { fetchConversations } = useElMercado();
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  const isAuthenticated = !!user;

  useEffect(() => {
    scrollToTop();
  }, []);

  const loadConversations = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const result = await fetchConversations();
    
    if (result.success) {
      setConversations(result.data);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  }, [isAuthenticated, fetchConversations]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Filter conversations by search
  const filteredConversations = conversations.filter((conv) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      conv.other_party?.name?.toLowerCase().includes(query) ||
      conv.listing_title?.toLowerCase().includes(query) ||
      conv.last_message_preview?.toLowerCase().includes(query)
    );
  });

  const handleConversationClick = (conversationId) => {
    navigate(`/el-mercado/messages/${conversationId}`);
  };

  return (
    <>
      <Helmet>
        <title>Messages | El Mercado - CSS KNUST</title>
        <meta name="description" content="View and manage your conversations with sellers on El Mercado." />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          {/* Navigation Bar */}
          <div className="bg-white border-b border-gray-100">
            <div className="max-w-4xl mx-auto px-4 py-3">
              <div className="flex items-center justify-between">
                <Link
                  to="/el-mercado/browse"
                  className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Back to Browse
                </Link>
                
                <Link
                  to="/el-mercado/favorites"
                  className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-colors"
                >
                  <Heart className="w-4 h-4" />
                  <span className="hidden sm:inline">Favorites</span>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Header */}
          <section className="bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 text-white py-8 px-4">
            <div className="max-w-4xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3 mb-4"
              >
                <MessageCircle className="w-8 h-8" />
                <h1 className="text-2xl md:text-3xl font-bold">Messages</h1>
              </motion.div>
              <p className="text-blue-100">
                Your conversations with sellers and buyers
              </p>
            </div>
          </section>

          <div className="max-w-4xl mx-auto px-4 py-8">
            {!isAuthenticated ? (
              <NotAuthenticatedState onSignIn={() => navigate("/login")} />
            ) : loading ? (
              <LoadingSkeleton />
            ) : error ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Messages</h3>
                <p className="text-gray-500 mb-4">{error}</p>
                <button
                  onClick={loadConversations}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            ) : conversations.length === 0 ? (
              <EmptyState />
            ) : (
              <>
                {/* Search Bar */}
                <div className="mb-6">
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search conversations..."
                      className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Conversations List */}
                <div className="space-y-3">
                  <AnimatePresence>
                    {filteredConversations.length > 0 ? (
                      filteredConversations.map((conversation) => (
                        <ConversationCard
                          key={conversation.id}
                          conversation={conversation}
                          onClick={() => handleConversationClick(conversation.id)}
                        />
                      ))
                    ) : (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-12 text-gray-500"
                      >
                        No conversations found matching &ldquo;{searchQuery}&rdquo;
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            )}
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default MessagesPage;
