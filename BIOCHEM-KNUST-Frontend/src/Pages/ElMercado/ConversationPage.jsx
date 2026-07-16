import { useEffect, useState, useCallback, useContext, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowLeft,
  Send,
  Package,
  Paperclip,
  Loader2,
  AlertCircle,
  Check,
  CheckCheck,
  X,
  MoreVertical,
  Clock,
  MessageCircle,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { scrollToTop } from "../../utils/scrollToTop";
import { useElMercado } from "../../Context/ElMercadoContext";
import { UserContext } from "../../Context/UserContext";
import { useAuthModals } from "../../Context/AuthModalsContext";

// Format message time
const formatMessageTime = (date) => {
  if (!date) return "";
  
  const messageDate = new Date(date);
  
  // Check if date is valid
  if (isNaN(messageDate.getTime())) return "";
  
  const now = new Date();
  const isToday = messageDate.toDateString() === now.toDateString();
  
  if (isToday) {
    return messageDate.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  
  return messageDate.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Message Bubble Component
function MessageBubble({ message, isOwn }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isOwn ? "justify-end" : "justify-start"} mb-3`}
    >
      <div
        className={`max-w-[75%] sm:max-w-[65%] px-4 py-2.5 rounded-2xl ${
          isOwn
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-100 text-gray-900 rounded-bl-md"
        }`}
      >
        {/* System message styling */}
        {message.sender_type === "SYSTEM" && (
          <div className="text-center text-sm text-gray-500 italic py-1">
            {message.content}
          </div>
        )}
        
        {/* Regular message */}
        {message.sender_type !== "SYSTEM" && (
          <>
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
            
            {/* Attachment */}
            {message.attachment && (
              <a
                href={message.attachment}
                target="_blank"
                rel="noopener noreferrer"
                className={`flex items-center gap-2 mt-2 text-sm ${
                  isOwn ? "text-blue-100 hover:text-white" : "text-blue-600 hover:text-blue-700"
                }`}
              >
                <Paperclip className="w-4 h-4" />
                {message.attachment_name || "Attachment"}
              </a>
            )}
            
            {/* Timestamp and status */}
            <div className={`flex items-center gap-1.5 mt-1 text-xs ${
              isOwn ? "text-blue-200 justify-end" : "text-gray-400"
            }`}>
              <span>{formatMessageTime(message.created_at)}</span>
              {isOwn && (
                message.is_read ? (
                  <CheckCheck className="w-3.5 h-3.5" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )
              )}
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}

// Message Input Component
function MessageInput({ onSend, disabled }) {
  const [message, setMessage] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if ((!message.trim() && !attachment) || sending) return;
    
    setSending(true);
    await onSend(message.trim(), attachment);
    setMessage("");
    setAttachment(null);
    setSending(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Limit file size to 10MB
      if (file.size > 10 * 1024 * 1024) {
        alert("File size must be less than 10MB");
        return;
      }
      setAttachment(file);
    }
  };

  const removeAttachment = () => {
    setAttachment(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      {/* Attachment preview */}
      {attachment && (
        <div className="mb-3 flex items-center gap-2 p-2 bg-gray-100 rounded-lg">
          <Paperclip className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-700 truncate flex-1">{attachment.name}</span>
          <button
            onClick={removeAttachment}
            className="p-1 hover:bg-gray-200 rounded-full transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        {/* Attachment button */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept="image/*,.pdf,.doc,.docx"
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || sending}
          className="p-3 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors disabled:opacity-50"
        >
          <Paperclip className="w-5 h-5" />
        </button>
        
        {/* Message input */}
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Type a message..."
            rows={1}
            disabled={disabled || sending}
            className="w-full px-4 py-3 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-50"
            style={{ maxHeight: "120px" }}
          />
        </div>
        
        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || sending || (!message.trim() && !attachment)}
          className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
        >
          {sending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>
    </div>
  );
}

// Conversation Header
function ConversationHeader({ conversation, onBack }) {
  const otherParty = conversation.seller || conversation.other_party;
  const isSeller = conversation.other_party?.type === "seller";

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-[60px] z-10">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        
        <Link 
          to={isSeller ? `/el-mercado/store/${otherParty?.slug}` : "#"}
          className="flex items-center gap-3 flex-1 min-w-0"
        >
          {/* Avatar */}
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold shadow overflow-hidden flex-shrink-0">
            {otherParty?.logo_url ? (
              <img 
                src={otherParty.logo_url} 
                alt={otherParty?.display_name || otherParty?.name} 
                className="w-full h-full object-cover"
              />
            ) : (
              (otherParty?.display_name || otherParty?.name)?.charAt(0) || "?"
            )}
          </div>
          
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 truncate">
                {otherParty?.display_name || otherParty?.business_name || otherParty?.name}
              </span>
              {otherParty?.is_verified && (
                <span className="text-blue-500 text-xs">✓</span>
              )}
            </div>
            {conversation.listing && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Package className="w-3.5 h-3.5" />
                <span className="truncate">{conversation.listing.title}</span>
              </div>
            )}
          </div>
        </Link>
        
        {/* Actions */}
        <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <MoreVertical className="w-5 h-5 text-gray-600" />
        </button>
      </div>
    </div>
  );
}

// Main Conversation Page
export function ConversationPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { fetchConversation, fetchMessages, sendMessage } = useElMercado();
  const { user } = useContext(UserContext);
  const { openLoginModal } = useAuthModals();
  
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const isAuthenticated = !!user;

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load conversation and messages
  const loadConversation = useCallback(async () => {
    if (!conversationId || !isAuthenticated) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    // Fetch conversation details
    const convResult = await fetchConversation(conversationId);
    if (!convResult.success) {
      setError(convResult.error);
      setLoading(false);
      return;
    }
    setConversation(convResult.data);
    
    // Fetch messages
    const msgResult = await fetchMessages(conversationId);
    if (msgResult.success) {
      setMessages(msgResult.data);
    }
    
    setLoading(false);
  }, [conversationId, isAuthenticated, fetchConversation, fetchMessages]);

  useEffect(() => {
    scrollToTop();
    loadConversation();
  }, [loadConversation]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending a message
  const handleSendMessage = async (content, attachment) => {
    const result = await sendMessage(conversationId, content, attachment);
    
    if (result.success) {
      setMessages((prev) => [...prev, result.data]);
    } else {
      alert(result.error || "Failed to send message");
    }
  };

  // Determine if message is from current user
  const isOwnMessage = (message) => {
    if (!user) return false;
    
    // Check if user is the seller
    if (conversation?.seller?.user?.id === user.id) {
      return message.sender_type === "SELLER";
    }
    
    // Otherwise user is the buyer
    return message.sender_type === "BUYER";
  };

  if (!isAuthenticated) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20 flex items-center justify-center">
          <div className="text-center p-8">
            <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Sign In Required</h2>
            <p className="text-gray-500 mb-4">Please sign in to view your messages.</p>
            <button
              onClick={openLoginModal}
              className="inline-block px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
        <Footer />
      </>
    );
  }

  if (error || !conversation) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 pt-20 flex items-center justify-center">
          <div className="text-center p-8">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Conversation Not Found</h2>
            <p className="text-gray-500 mb-4">{error || "This conversation doesn't exist or you don't have access."}</p>
            <Link
              to="/el-mercado/messages"
              className="inline-block px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Back to Messages
            </Link>
          </div>
        </div>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>
          Chat with {conversation.seller?.display_name || conversation.other_party?.name} | El Mercado
        </title>
      </Helmet>

      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />

        <div className="mt-20"/>

        {/* Conversation Header */}
        <ConversationHeader
          conversation={conversation}
          onBack={() => navigate("/el-mercado/messages")}
        />

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto pt-4 pb-4 px-4" style={{ marginTop: "60px" }}>
          <div className="max-w-3xl mx-auto">
            {/* Conversation start indicator */}
            {conversation.created_at && (
              <div className="text-center mb-6">
                <span className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  Conversation started {(() => {
                    const date = new Date(conversation.created_at);
                    return isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "long",
                      year: "numeric"
                    });
                  })()}
                </span>
              </div>
            )}
            
            {/* Listing context */}
            {conversation.listing && (
              <Link
                to={`/el-mercado/products/${conversation.listing.slug}`}
                className="block mb-6 p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                    {conversation.listing.main_image_url ? (
                      <img
                        src={conversation.listing.main_image_url}
                        alt={conversation.listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-6 h-6 text-gray-400" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">Regarding:</p>
                    <h4 className="font-semibold text-gray-900 truncate">
                      {conversation.listing.title}
                    </h4>
                    <p className="text-sm text-blue-600 font-medium">
                      GH₵ {parseFloat(conversation.listing.price).toFixed(2)}
                    </p>
                  </div>
                </div>
              </Link>
            )}
            
            {/* Messages */}
            <AnimatePresence>
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id || `msg-${index}`}
                  message={message}
                  isOwn={isOwnMessage(message)}
                />
              ))}
            </AnimatePresence>
            
            {/* Empty messages */}
            {messages.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No messages yet. Start the conversation!</p>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Message Input */}
        <div className="sticky bottom-0">
          <div className="max-w-3xl mx-auto">
            <MessageInput onSend={handleSendMessage} disabled={loading} />
          </div>
        </div>
      </div>
    </>
  );
}

export default ConversationPage;
