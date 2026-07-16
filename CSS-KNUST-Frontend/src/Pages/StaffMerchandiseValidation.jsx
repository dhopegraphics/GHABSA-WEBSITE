import { useState, useContext, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { UserContext } from "../Context/UserContext";
import { BACKEND_HOST } from "../utils/config";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  Snackbar,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Fade,
  Zoom,
  Backdrop,
  Avatar,
  Badge,
  Stack,
  alpha,
  useTheme,
} from "@mui/material";
import {
  Search,
  CheckCircle,
  XCircle,
  Package,
  AlertTriangle,
  Trash2,
  Plus,
  User,
  Phone,
  Mail,
  DollarSign,
  Calendar,
  ShoppingBag,
  Clock,
  Layers,
  Zap,
  Shield,
  QrCode,
  Sparkles,
  TrendingUp,
  PackageCheck,
  ScanLine,
  Barcode,
  ChevronRight,
  RefreshCw,
  Copy,
  Check,
  X,
  AlertCircle,
  Info,
  Palette,
  Ruler,
  Hash,
  ArrowRight,
  CircleDot,
  Loader2,
  MoreHorizontal,
  Eye,
  Ban,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Custom styled components for glassmorphism effect
const glassStyle = {
  background: "rgba(255, 255, 255, 0.85)",
  backdropFilter: "blur(20px)",
  WebkitBackdropFilter: "blur(20px)",
  border: "1px solid rgba(255, 255, 255, 0.3)",
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.08)",
};

const gradientBg = {
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
};

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 12,
    },
  },
};

const pulseVariants = {
  pulse: {
    scale: [1, 1.02, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};

const shimmerVariants = {
  animate: {
    backgroundPosition: ["200% 0", "-200% 0"],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: "linear",
    },
  },
};

export function StaffMerchandiseValidation() {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const theme = useTheme();
  
  // Single validation state
  const [singleCode, setSingleCode] = useState("");
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleResult, setSingleResult] = useState(null);
  const [singleError, setSingleError] = useState("");
  
  // Bulk validation state
  const [bulkCodes, setBulkCodes] = useState([]);
  const [bulkInput, setBulkInput] = useState("");
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResults, setBulkResults] = useState(null);
  const [bulkError, setBulkError] = useState("");
  
  // Mode toggle
  const [mode, setMode] = useState("single"); // 'single' or 'bulk'
  
  // Snackbar for notifications
  const [snackbar, setSnackbar] = useState({ open: false, message: "", severity: "success" });
  
  // Variant collection dialog
  const [variantDialog, setVariantDialog] = useState({ open: false, variant: null, index: 0 });
  const [variantForm, setVariantForm] = useState({ quantity: 1, substituted: false, substitution_notes: "" });
  
  // Unavailable dialog
  const [unavailableDialog, setUnavailableDialog] = useState({ open: false, variant: null, index: 0 });
  const [unavailableReason, setUnavailableReason] = useState("");
  
  // Copied state for code copy
  const [codeCopied, setCodeCopied] = useState(false);
  
  // Ref for auto-focus
  const inputRef = useRef(null);
  
  // Check if user is staff
  useEffect(() => {
    if (!user) {
      navigate("/");
      return;
    }
    
    if (!user.user?.is_staff) {
      navigate("/dashboard/home");
      return;
    }
  }, [user, navigate]);
  
  // Auto-focus input on mode change
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [mode]);
  
  // Helper to make authenticated requests
  const authFetch = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${user?.access}`,
        ...options.headers,
      },
    });
    return response;
  };
  
  // ==========================
  // SINGLE CODE OPERATIONS
  // ==========================
  
  const handleSingleLookup = async () => {
    if (!singleCode.trim()) {
      setSingleError("Please enter a validation code");
      return;
    }
    
    const code = singleCode.trim().toUpperCase();
    if (code.length !== 6) {
      setSingleError("Validation code must be exactly 6 characters");
      return;
    }
    
    setSingleLoading(true);
    setSingleError("");
    setSingleResult(null);
    
    try {
      const response = await authFetch(`${BACKEND_HOST}/products/staff/validation/lookup/`, {
        method: "POST",
        body: JSON.stringify({ validation_code: code }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setSingleError(data.error || "Lookup failed");
        return;
      }
      
      setSingleResult(data);
    } catch (_err) {
      setSingleError("Network error. Please try again.");
    } finally {
      setSingleLoading(false);
    }
  };
  
  const handleSingleCollect = async (variantCollections = null) => {
    if (!singleResult?.validation_code) return;
    
    setSingleLoading(true);
    
    try {
      const response = await authFetch(`${BACKEND_HOST}/products/staff/validation/collect/`, {
        method: "POST",
        body: JSON.stringify({
          validation_code: singleResult.validation_code,
          variant_collections: variantCollections,
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setSnackbar({ open: true, message: data.error || "Collection failed", severity: "error" });
        return;
      }
      
      // Refresh the result
      setSingleResult(data);
      setSnackbar({
        open: true,
        message: data.fully_collected ? "✅ All items collected!" : "Items collected successfully",
        severity: "success",
      });
    } catch (_err) {
      setSnackbar({ open: true, message: "Network error", severity: "error" });
    } finally {
      setSingleLoading(false);
      setVariantDialog({ open: false, variant: null, index: 0 });
    }
  };
  
  const handleMarkUnavailable = async () => {
    if (!singleResult?.validation_code) return;
    
    setSingleLoading(true);
    
    try {
      const response = await authFetch(`${BACKEND_HOST}/products/staff/validation/mark_unavailable/`, {
        method: "POST",
        body: JSON.stringify({
          validation_code: singleResult.validation_code,
          variant_index: unavailableDialog.index,
          reason: unavailableReason,
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setSnackbar({ open: true, message: data.error || "Failed to mark unavailable", severity: "error" });
        return;
      }
      
      // Refresh the single result
      handleSingleLookup();
      setSnackbar({ open: true, message: "Variant marked as unavailable", severity: "warning" });
    } catch (_err) {
      setSnackbar({ open: true, message: "Network error", severity: "error" });
    } finally {
      setSingleLoading(false);
      setUnavailableDialog({ open: false, variant: null, index: 0 });
      setUnavailableReason("");
    }
  };
  
  // ==========================
  // BULK CODE OPERATIONS
  // ==========================
  
  const addBulkCode = () => {
    const code = bulkInput.trim().toUpperCase();
    if (!code) return;
    
    if (code.length !== 6) {
      setBulkError("Each code must be exactly 6 characters");
      return;
    }
    
    if (bulkCodes.includes(code)) {
      setBulkError("This code is already in the list");
      return;
    }
    
    if (bulkCodes.length >= 50) {
      setBulkError("Maximum 50 codes per batch");
      return;
    }
    
    setBulkCodes([...bulkCodes, code]);
    setBulkInput("");
    setBulkError("");
    inputRef.current?.focus();
  };
  
  const removeBulkCode = (code) => {
    setBulkCodes(bulkCodes.filter((c) => c !== code));
  };
  
  const clearBulkCodes = () => {
    setBulkCodes([]);
    setBulkResults(null);
    setBulkError("");
  };
  
  const handleBulkLookup = async () => {
    if (bulkCodes.length === 0) {
      setBulkError("Add at least one validation code");
      return;
    }
    
    setBulkLoading(true);
    setBulkError("");
    setBulkResults(null);
    
    try {
      const response = await authFetch(`${BACKEND_HOST}/products/staff/validation/bulk_lookup/`, {
        method: "POST",
        body: JSON.stringify({ validation_codes: bulkCodes }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setBulkError(data.error || "Bulk lookup failed");
        return;
      }
      
      setBulkResults(data);
    } catch (_err) {
      setBulkError("Network error. Please try again.");
    } finally {
      setBulkLoading(false);
    }
  };
  
  const handleBulkCollect = async () => {
    if (bulkCodes.length === 0) {
      setBulkError("Add at least one validation code");
      return;
    }
    
    setBulkLoading(true);
    setBulkError("");
    
    try {
      const response = await authFetch(`${BACKEND_HOST}/products/staff/validation/bulk_collect/`, {
        method: "POST",
        body: JSON.stringify({ validation_codes: bulkCodes }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setBulkError(data.error || "Bulk collection failed");
        return;
      }
      
      setBulkResults(data);
      setSnackbar({
        open: true,
        message: `Processed ${data.total_processed} codes: ${data.success_count} successful, ${data.error_count} failed`,
        severity: data.error_count > 0 ? "warning" : "success",
      });
    } catch (_err) {
      setBulkError("Network error. Please try again.");
    } finally {
      setBulkLoading(false);
    }
  };
  
  // Handle Enter key
  const handleKeyPress = (e, action) => {
    if (e.key === "Enter") {
      e.preventDefault();
      action();
    }
  };
  
  // Render collection status badge
  const renderStatusBadge = (status) => {
    const statusConfig = {
      pending: { 
        color: "info", 
        icon: <Clock size={14} />, 
        label: "Pending",
        gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        bg: "rgba(102, 126, 234, 0.1)",
      },
      partial: { 
        color: "warning", 
        icon: <AlertTriangle size={14} />, 
        label: "Partial",
        gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        bg: "rgba(245, 87, 108, 0.1)",
      },
      collected: { 
        color: "success", 
        icon: <CheckCircle size={14} />, 
        label: "Collected",
        gradient: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        bg: "rgba(56, 239, 125, 0.1)",
      },
      unavailable: { 
        color: "default", 
        icon: <XCircle size={14} />, 
        label: "Unavailable",
        gradient: "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)",
        bg: "rgba(189, 195, 199, 0.1)",
      },
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
        <Chip
          size="small"
          icon={config.icon}
          label={config.label}
          sx={{ 
            fontWeight: 700,
            fontSize: "0.75rem",
            letterSpacing: "0.5px",
            background: config.gradient,
            color: "white",
            border: "none",
            boxShadow: `0 4px 14px ${alpha(theme.palette.common.black, 0.15)}`,
            "& .MuiChip-icon": {
              color: "white",
            },
          }}
        />
      </motion.div>
    );
  };

  // Copy code to clipboard
  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCodeCopied(true);
    setTimeout(() => setCodeCopied(false), 2000);
  };
  
  // Don't render if not staff
  if (!user?.user?.is_staff) {
    return null;
  }
  
  return (
    <Box 
      sx={{ 
        minHeight: "100vh",
        background: "linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 50%, #f5f7fa 100%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Animated background decorations */}
      <Box
        sx={{
          position: "absolute",
          top: -100,
          right: -100,
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: "linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%)",
          filter: "blur(60px)",
          animation: "float 8s ease-in-out infinite",
          "@keyframes float": {
            "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
            "50%": { transform: "translateY(-30px) rotate(10deg)" },
          },
        }}
      />
      <Box
        sx={{
          position: "absolute",
          bottom: -150,
          left: -150,
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "linear-gradient(135deg, rgba(240, 147, 251, 0.12) 0%, rgba(245, 87, 108, 0.08) 100%)",
          filter: "blur(80px)",
          animation: "float2 10s ease-in-out infinite",
          "@keyframes float2": {
            "0%, 100%": { transform: "translateX(0)" },
            "50%": { transform: "translateX(30px)" },
          },
        }}
      />

      <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1400, mx: "auto", position: "relative", zIndex: 1 }}>
        {/* Modern Header with Glass Effect */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, md: 4 },
              mb: 4,
              background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
              color: "white",
              borderRadius: 4,
              position: "relative",
              overflow: "hidden",
              border: "1px solid rgba(255, 255, 255, 0.1)",
            }}
          >
            {/* Header background pattern */}
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                background: `
                  radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.3) 0%, transparent 50%),
                  radial-gradient(circle at 80% 50%, rgba(240, 147, 251, 0.2) 0%, transparent 50%)
                `,
                opacity: 0.8,
              }}
            />
            
            {/* Animated sparkles */}
            <Box sx={{ position: "absolute", top: 20, right: 30, opacity: 0.6 }}>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles size={24} />
              </motion.div>
            </Box>
            
            <Box sx={{ position: "relative", zIndex: 1 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
                <motion.div
                  whileHover={{ rotate: 15, scale: 1.1 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: "linear-gradient(135deg, rgba(102, 126, 234, 0.5) 0%, rgba(118, 75, 162, 0.5) 100%)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Shield size={28} />
                  </Box>
                </motion.div>
                <Box>
                  <Typography 
                    variant="h4" 
                    fontWeight={800}
                    sx={{ 
                      background: "linear-gradient(135deg, #fff 0%, #e0e0e0 100%)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                      letterSpacing: "-0.5px",
                    }}
                  >
                    Merchandise Validation
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      opacity: 0.7,
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      mt: 0.5,
                    }}
                  >
                    <ScanLine size={14} /> Staff Portal • Secure Access
                  </Typography>
                </Box>
              </Box>
              
              <Typography 
                variant="body1" 
                sx={{ 
                  opacity: 0.85, 
                  maxWidth: 600,
                  lineHeight: 1.7,
                }}
              >
                Validate purchase codes and manage merchandise collection. Scan or enter codes to verify orders and mark items as collected.
              </Typography>
              
              {/* Quick stats */}
              <Box sx={{ display: "flex", gap: 3, mt: 3, flexWrap: "wrap" }}>
                {[
                  { icon: <QrCode size={18} />, label: "Single Scan", desc: "One at a time" },
                  { icon: <Layers size={18} />, label: "Bulk Process", desc: "Multiple codes" },
                  { icon: <PackageCheck size={18} />, label: "Track Status", desc: "Real-time updates" },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + i * 0.1 }}
                  >
                    <Box 
                      sx={{ 
                        display: "flex", 
                        alignItems: "center", 
                        gap: 1.5,
                        px: 2,
                        py: 1,
                        borderRadius: 2,
                        background: "rgba(255, 255, 255, 0.1)",
                        backdropFilter: "blur(10px)",
                      }}
                    >
                      {item.icon}
                      <Box>
                        <Typography variant="body2" fontWeight={600}>{item.label}</Typography>
                        <Typography variant="caption" sx={{ opacity: 0.7 }}>{item.desc}</Typography>
                      </Box>
                    </Box>
                  </motion.div>
                ))}
              </Box>
            </Box>
          </Paper>
        </motion.div>
      
        {/* Modern Mode Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <Box 
            sx={{ 
              display: "flex", 
              gap: 2, 
              mb: 4,
              p: 1,
              borderRadius: 3,
              ...glassStyle,
            }}
          >
            <motion.div style={{ flex: 1 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                fullWidth
                variant={mode === "single" ? "contained" : "text"}
                onClick={() => setMode("single")}
                sx={{ 
                  py: 2,
                  borderRadius: 2,
                  fontWeight: 700,
                  fontSize: "0.95rem",
                  letterSpacing: "0.3px",
                  background: mode === "single" 
                    ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" 
                    : "transparent",
                  color: mode === "single" ? "white" : "text.primary",
                  boxShadow: mode === "single" 
                    ? "0 8px 30px rgba(102, 126, 234, 0.4)" 
                    : "none",
                  "&:hover": {
                    background: mode === "single" 
                      ? "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)"
                      : "rgba(102, 126, 234, 0.08)",
                  },
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <QrCode size={20} />
                  Single Lookup
                </Box>
              </Button>
            </motion.div>
            
            <motion.div style={{ flex: 1 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                fullWidth
                variant={mode === "bulk" ? "contained" : "text"}
                onClick={() => setMode("bulk")}
                sx={{ 
                  py: 2,
                  borderRadius: 2,
                  fontWeight: 700,
                  fontSize: "0.95rem",
                  letterSpacing: "0.3px",
                  background: mode === "bulk" 
                    ? "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)" 
                    : "transparent",
                  color: mode === "bulk" ? "white" : "text.primary",
                  boxShadow: mode === "bulk" 
                    ? "0 8px 30px rgba(240, 147, 251, 0.4)" 
                    : "none",
                  "&:hover": {
                    background: mode === "bulk" 
                      ? "linear-gradient(135deg, #e085ec 0%, #e64d60 100%)"
                      : "rgba(240, 147, 251, 0.08)",
                  },
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <Layers size={20} />
                  Bulk Validation
                </Box>
              </Button>
            </motion.div>
          </Box>
        </motion.div>
      
      {/* ======================== */}
      {/* SINGLE MODE */}
      {/* ======================== */}
      {mode === "single" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Modern Search Box */}
          <Paper 
            elevation={0} 
            sx={{ 
              p: { xs: 3, md: 4 }, 
              mb: 4, 
              borderRadius: 4,
              ...glassStyle,
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Decorative element */}
            <Box
              sx={{
                position: "absolute",
                top: 0,
                right: 0,
                width: 200,
                height: 200,
                background: "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, transparent 100%)",
                borderRadius: "0 0 0 100%",
              }}
            />
            
            <Box sx={{ position: "relative", zIndex: 1 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    display: "flex",
                    color: "white",
                  }}
                >
                  <Barcode size={24} />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={700} color="text.primary">
                    Enter Validation Code
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Type the 6-character code from the customer&apos;s receipt
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: "flex", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
                <TextField
                  inputRef={inputRef}
                  fullWidth
                  value={singleCode}
                  onChange={(e) => setSingleCode(e.target.value.toUpperCase())}
                  onKeyPress={(e) => handleKeyPress(e, handleSingleLookup)}
                  placeholder="ABC123"
                  inputProps={{
                    maxLength: 6,
                    style: { 
                      textTransform: "uppercase", 
                      letterSpacing: "8px", 
                      fontWeight: 800, 
                      fontSize: "1.5rem",
                      textAlign: "center",
                      fontFamily: "monospace",
                    },
                  }}
                  disabled={singleLoading}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      borderRadius: 3,
                      background: "rgba(255, 255, 255, 0.8)",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        background: "white",
                        boxShadow: "0 4px 20px rgba(102, 126, 234, 0.15)",
                      },
                      "&.Mui-focused": {
                        background: "white",
                        boxShadow: "0 4px 20px rgba(102, 126, 234, 0.25)",
                      },
                    },
                  }}
                />
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    variant="contained"
                    onClick={handleSingleLookup}
                    disabled={singleLoading || !singleCode.trim()}
                    sx={{ 
                      minWidth: { xs: "100%", sm: 160 },
                      height: 56,
                      borderRadius: 3,
                      fontWeight: 700,
                      fontSize: "1rem",
                      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      boxShadow: "0 8px 30px rgba(102, 126, 234, 0.4)",
                      "&:hover": {
                        background: "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
                      },
                      "&:disabled": {
                        background: "linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%)",
                      },
                    }}
                  >
                    {singleLoading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Loader2 size={24} />
                      </motion.div>
                    ) : (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Search size={20} />
                        Search
                      </Box>
                    )}
                  </Button>
                </motion.div>
              </Box>
              
              {singleError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Alert 
                    severity="error" 
                    sx={{ 
                      mt: 3,
                      borderRadius: 2,
                      background: "rgba(244, 67, 54, 0.1)",
                      border: "1px solid rgba(244, 67, 54, 0.2)",
                    }}
                    icon={<AlertCircle size={20} />}
                  >
                    {singleError}
                  </Alert>
                </motion.div>
              )}
            </Box>
          </Paper>
          
          {/* Single Result Display */}
          <AnimatePresence mode="wait">
            {singleResult && (
              <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.98 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    borderRadius: 4,
                    overflow: "hidden",
                    ...glassStyle,
                  }}
                >
                  {/* Result Header with gradient */}
                  <Box
                    sx={{
                      p: { xs: 3, md: 4 },
                      background: singleResult.collection_summary?.overall_status === "collected"
                        ? "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
                        : singleResult.collection_summary?.overall_status === "partial"
                        ? "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
                        : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      color: "white",
                      position: "relative",
                    }}
                  >
                    {/* Background pattern */}
                    <Box
                      sx={{
                        position: "absolute",
                        inset: 0,
                        opacity: 0.1,
                        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                      }}
                    />
                    
                    <Box sx={{ position: "relative", zIndex: 1 }}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 2 }}>
                        <Box>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
                            <Package size={28} />
                            <Typography variant="h5" fontWeight={800}>
                              {singleResult.product_name}
                            </Typography>
                          </Box>
                          
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            <Typography
                              variant="h4"
                              sx={{ 
                                fontFamily: "monospace", 
                                letterSpacing: 6, 
                                fontWeight: 800,
                                background: "rgba(255, 255, 255, 0.2)",
                                px: 2,
                                py: 0.5,
                                borderRadius: 2,
                              }}
                            >
                              {singleResult.validation_code}
                            </Typography>
                            <Tooltip title={codeCopied ? "Copied!" : "Copy code"}>
                              <IconButton 
                                size="small" 
                                onClick={() => handleCopyCode(singleResult.validation_code)}
                                sx={{ color: "white", opacity: 0.8, "&:hover": { opacity: 1 } }}
                              >
                                {codeCopied ? <Check size={18} /> : <Copy size={18} />}
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                        
                        {renderStatusBadge(singleResult.collection_summary?.overall_status)}
                      </Box>
                    </Box>
                  </Box>
                  
                  {/* Content Section */}
                  <Box sx={{ p: { xs: 3, md: 4 } }}>
                    {/* Collection Stats Cards */}
                    <Grid container spacing={2} sx={{ mb: 4 }}>
                      {[
                        { 
                          value: singleResult.collection_summary?.total_ordered || 0, 
                          label: "Total Ordered",
                          gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                          icon: <ShoppingBag size={20} />,
                        },
                        { 
                          value: singleResult.collection_summary?.total_collected || 0, 
                          label: "Collected",
                          gradient: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                          icon: <CheckCircle size={20} />,
                        },
                        { 
                          value: singleResult.collection_summary?.total_pending || 0, 
                          label: "Pending",
                          gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                          icon: <Clock size={20} />,
                        },
                      ].map((stat, idx) => (
                        <Grid item xs={4} key={idx}>
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                          >
                            <Paper
                              elevation={0}
                              sx={{
                                p: 2.5,
                                textAlign: "center",
                                borderRadius: 3,
                                background: stat.gradient,
                                color: "white",
                                position: "relative",
                                overflow: "hidden",
                              }}
                            >
                              <Box
                                sx={{
                                  position: "absolute",
                                  top: 10,
                                  right: 10,
                                  opacity: 0.3,
                                }}
                              >
                                {stat.icon}
                              </Box>
                              <Typography variant="h3" fontWeight={800}>
                                {stat.value}
                              </Typography>
                              <Typography variant="body2" sx={{ opacity: 0.9, fontWeight: 500 }}>
                                {stat.label}
                              </Typography>
                            </Paper>
                          </motion.div>
                        </Grid>
                      ))}
                    </Grid>
                    
                    {/* Progress bar */}
                    {singleResult.collection_summary?.total_ordered > 0 && (
                      <Box sx={{ mb: 4 }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1.5 }}>
                          <Typography variant="body2" fontWeight={700} color="text.secondary">
                            Collection Progress
                          </Typography>
                          <Typography variant="body2" fontWeight={700}>
                            {singleResult.collection_summary?.total_collected}/{singleResult.collection_summary?.total_ordered}
                            <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                              ({Math.round(
                                (singleResult.collection_summary?.total_collected / singleResult.collection_summary?.total_ordered) * 100
                              )}%)
                            </Typography>
                          </Typography>
                        </Box>
                        <Box sx={{ position: "relative", height: 12, borderRadius: 6, overflow: "hidden", bgcolor: "grey.100" }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ 
                              width: `${(singleResult.collection_summary?.total_collected / singleResult.collection_summary?.total_ordered) * 100}%` 
                            }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            style={{
                              height: "100%",
                              background: "linear-gradient(90deg, #11998e 0%, #38ef7d 100%)",
                              borderRadius: 6,
                            }}
                          />
                        </Box>
                      </Box>
                    )}
                    
                    {/* Customer Info Grid - Modern Cards */}
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}>
                      <User size={20} /> Customer Information
                    </Typography>
                    
                    <Grid container spacing={2} sx={{ mb: 4 }}>
                      {[
                        { icon: <User size={18} />, label: "Customer", value: singleResult.customer_name || "N/A", color: "#667eea" },
                        { icon: <Phone size={18} />, label: "Phone", value: singleResult.customer_phone || "N/A", color: "#11998e" },
                        { icon: <Mail size={18} />, label: "Email", value: singleResult.customer_email || "N/A", color: "#f5576c", truncate: true },
                        { icon: <DollarSign size={18} />, label: "Amount Paid", value: `GH₵ ${singleResult.amount_paid}`, color: "#38ef7d", highlight: true },
                        { icon: <ShoppingBag size={18} />, label: "Quantity", value: singleResult.quantity, color: "#764ba2" },
                        { icon: <Calendar size={18} />, label: "Academic Year", value: singleResult.academic_year || "N/A", color: "#f093fb" },
                      ].map((item, idx) => (
                        <Grid item xs={12} sm={6} md={4} key={idx}>
                          <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 + idx * 0.05 }}
                          >
                            <Paper
                              elevation={0}
                              sx={{
                                p: 2,
                                borderRadius: 2,
                                background: "rgba(255, 255, 255, 0.6)",
                                border: "1px solid rgba(0, 0, 0, 0.05)",
                                display: "flex",
                                alignItems: "center",
                                gap: 2,
                                transition: "all 0.2s ease",
                                "&:hover": {
                                  background: "white",
                                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
                                },
                              }}
                            >
                              <Box
                                sx={{
                                  p: 1,
                                  borderRadius: 1.5,
                                  background: `${item.color}15`,
                                  color: item.color,
                                  display: "flex",
                                }}
                              >
                                {item.icon}
                              </Box>
                              <Box sx={{ overflow: "hidden" }}>
                                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                                  {item.label}
                                </Typography>
                                <Typography 
                                  fontWeight={item.highlight ? 800 : 600} 
                                  color={item.highlight ? "success.main" : "text.primary"}
                                  sx={{ 
                                    ...(item.truncate && { 
                                      overflow: "hidden", 
                                      textOverflow: "ellipsis", 
                                      whiteSpace: "nowrap",
                                      maxWidth: 200,
                                    })
                                  }}
                                >
                                  {item.value}
                                </Typography>
                              </Box>
                            </Paper>
                          </motion.div>
                        </Grid>
                      ))}
                    </Grid>
                    
                    {/* Quick Actions */}
                    {singleResult.collection_summary?.overall_status !== "collected" && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                      >
                        <Paper
                          elevation={0}
                          sx={{
                            p: 3,
                            mb: 3,
                            borderRadius: 3,
                            background: "linear-gradient(135deg, rgba(17, 153, 142, 0.1) 0%, rgba(56, 239, 125, 0.1) 100%)",
                            border: "1px solid rgba(56, 239, 125, 0.3)",
                          }}
                        >
                          <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                            <Button
                              variant="contained"
                              size="large"
                              fullWidth
                              onClick={() => handleSingleCollect(null)}
                              disabled={singleLoading}
                              sx={{
                                py: 2,
                                borderRadius: 2,
                                fontWeight: 700,
                                fontSize: "1.1rem",
                                background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                                boxShadow: "0 8px 30px rgba(56, 239, 125, 0.4)",
                                "&:hover": {
                                  background: "linear-gradient(135deg, #0f8a7f 0%, #2ed06e 100%)",
                                },
                              }}
                            >
                              {singleLoading ? (
                                <motion.div
                                  animate={{ rotate: 360 }}
                                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                >
                                  <Loader2 size={24} />
                                </motion.div>
                              ) : (
                                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                                  <CheckCircle size={24} />
                                  Mark All Remaining as Collected
                                </Box>
                              )}
                            </Button>
                          </motion.div>
                        </Paper>
                      </motion.div>
                    )}
                    
                    {singleResult.collection_summary?.overall_status === "collected" && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                      >
                        <Alert 
                          severity="success" 
                          sx={{ 
                            mb: 3,
                            borderRadius: 3,
                            background: "linear-gradient(135deg, rgba(17, 153, 142, 0.15) 0%, rgba(56, 239, 125, 0.15) 100%)",
                            border: "1px solid rgba(56, 239, 125, 0.3)",
                            "& .MuiAlert-icon": {
                              color: "#11998e",
                            },
                          }}
                          icon={<CheckCircle size={24} />}
                        >
                          <Typography fontWeight={700} sx={{ mb: 0.5 }}>
                            All items have been collected!
                          </Typography>
                          {singleResult.merchandise_taken_at && (
                            <Typography variant="body2" color="text.secondary">
                              Collected on {new Date(singleResult.merchandise_taken_at).toLocaleString()} by{" "}
                              <strong>{singleResult.taken_by || "Admin"}</strong>
                            </Typography>
                          )}
                        </Alert>
                      </motion.div>
                    )}
                    
                    {/* Variants Section */}
                    <Divider sx={{ my: 4 }} />
                    
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
                      <Package size={22} />
                      Item Variants
                      <Chip 
                        label={singleResult.formatted_collection_details?.length || 0}
                        size="small"
                        sx={{ 
                          ml: 1,
                          fontWeight: 700,
                          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                          color: "white",
                        }}
                      />
                    </Typography>
                    
                    <Stack spacing={2}>
                      {singleResult.formatted_collection_details?.map((variant, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                        >
                          <Card
                            elevation={0}
                            sx={{
                              borderRadius: 3,
                              overflow: "hidden",
                              border: "1px solid rgba(0, 0, 0, 0.05)",
                              background: "rgba(255, 255, 255, 0.7)",
                              transition: "all 0.3s ease",
                              "&:hover": {
                                background: "white",
                                boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
                                transform: "translateY(-2px)",
                              },
                            }}
                          >
                            {/* Variant status indicator bar */}
                            <Box
                              sx={{
                                height: 4,
                                background: variant.status === "collected"
                                  ? "linear-gradient(90deg, #11998e 0%, #38ef7d 100%)"
                                  : variant.status === "partial"
                                  ? "linear-gradient(90deg, #f093fb 0%, #f5576c 100%)"
                                  : variant.status === "unavailable"
                                  ? "linear-gradient(90deg, #bdc3c7 0%, #2c3e50 100%)"
                                  : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                              }}
                            />
                            
                            <CardContent sx={{ p: 3 }}>
                              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap", gap: 2 }}>
                                <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap" }}>
                                  {/* Variant number badge */}
                                  <Avatar
                                    sx={{
                                      width: 36,
                                      height: 36,
                                      fontSize: "0.9rem",
                                      fontWeight: 800,
                                      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                    }}
                                  >
                                    {idx + 1}
                                  </Avatar>
                                  
                                  {variant.color_name && (
                                    <Chip
                                      size="small"
                                      icon={
                                        <Box
                                          sx={{
                                            width: 18,
                                            height: 18,
                                            borderRadius: "50%",
                                            bgcolor: variant.color_hex || "#888",
                                            border: "2px solid rgba(0,0,0,0.1)",
                                            boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                                          }}
                                        />
                                      }
                                      label={variant.color_name}
                                      sx={{ 
                                        fontWeight: 600,
                                        background: "rgba(0, 0, 0, 0.05)",
                                        border: "none",
                                      }}
                                    />
                                  )}
                                  
                                  {variant.size_name && (
                                    <Chip
                                      size="small"
                                      icon={<Ruler size={14} />}
                                      label={`${variant.size_code} - ${variant.size_name}`}
                                      sx={{ 
                                        fontWeight: 600,
                                        background: "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)",
                                        border: "none",
                                        color: "#667eea",
                                      }}
                                    />
                                  )}
                                  
                                  <Chip
                                    size="small"
                                    variant="outlined"
                                    icon={<Package size={14} />}
                                    label={`${variant.collected_quantity || 0}/${variant.ordered_quantity || 1} collected`}
                                    sx={{ fontWeight: 600 }}
                                  />
                                </Box>
                                
                                {renderStatusBadge(variant.status)}
                              </Box>
                              
                              {/* Collection info for collected items */}
                              {(variant.status === "collected" || variant.status === "partial") && variant.collected_at && (
                                <Paper
                                  elevation={0}
                                  sx={{
                                    p: 2,
                                    mb: 2,
                                    borderRadius: 2,
                                    background: "linear-gradient(135deg, rgba(17, 153, 142, 0.08) 0%, rgba(56, 239, 125, 0.08) 100%)",
                                    border: "1px solid rgba(56, 239, 125, 0.2)",
                                  }}
                                >
                                  <Grid container spacing={2}>
                                    <Grid item xs={12} sm={4}>
                                      <Typography variant="caption" color="text.secondary">Collected</Typography>
                                      <Typography fontWeight={600}>{variant.collected_quantity} of {variant.ordered_quantity}</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                      <Typography variant="caption" color="text.secondary">When</Typography>
                                      <Typography fontWeight={600}>{new Date(variant.collected_at).toLocaleString()}</Typography>
                                    </Grid>
                                    {variant.collected_by && (
                                      <Grid item xs={12} sm={4}>
                                        <Typography variant="caption" color="text.secondary">By</Typography>
                                        <Typography fontWeight={600}>{variant.collected_by}</Typography>
                                      </Grid>
                                    )}
                                  </Grid>
                                </Paper>
                              )}
                              
                              {/* Substitution note */}
                              {(variant.substituted || variant.substitution_notes) && (
                                <Alert 
                                  severity="warning" 
                                  variant="outlined" 
                                  sx={{ 
                                    mb: 2,
                                    borderRadius: 2,
                                    background: "rgba(255, 152, 0, 0.05)",
                                  }}
                                  icon={<AlertTriangle size={18} />}
                                >
                                  {variant.substituted && <strong>Substitution Made: </strong>}
                                  {variant.substitution_notes || "No notes"}
                                </Alert>
                              )}
                              
                              {/* Actions for pending/partial items */}
                              {variant.status !== "collected" && variant.status !== "unavailable" && (
                                <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
                                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                                    <Button
                                      variant="contained"
                                      size="small"
                                      onClick={() => {
                                        setVariantForm({
                                          quantity: variant.ordered_quantity - (variant.collected_quantity || 0),
                                          substituted: false,
                                          substitution_notes: "",
                                        });
                                        setVariantDialog({ open: true, variant, index: idx });
                                      }}
                                      sx={{
                                        borderRadius: 2,
                                        fontWeight: 600,
                                        background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                                        boxShadow: "0 4px 14px rgba(56, 239, 125, 0.3)",
                                        "&:hover": {
                                          background: "linear-gradient(135deg, #0f8a7f 0%, #2ed06e 100%)",
                                        },
                                      }}
                                    >
                                      <CheckCircle size={16} style={{ marginRight: 6 }} />
                                      Collect
                                    </Button>
                                  </motion.div>
                                  
                                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                                    <Button
                                      variant="outlined"
                                      color="inherit"
                                      size="small"
                                      onClick={() => setUnavailableDialog({ open: true, variant, index: idx })}
                                      sx={{
                                        borderRadius: 2,
                                        fontWeight: 600,
                                        borderColor: "grey.300",
                                        "&:hover": {
                                          borderColor: "grey.400",
                                          background: "rgba(0, 0, 0, 0.02)",
                                        },
                                      }}
                                    >
                                      <Ban size={16} style={{ marginRight: 6 }} />
                                      Unavailable
                                    </Button>
                                  </motion.div>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </Stack>
                  </Box>
                </Paper>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
      
      {/* ======================== */}
      {/* BULK MODE */}
      {/* ======================== */}
      {mode === "bulk" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Modern Bulk Input */}
          <Paper 
            elevation={0} 
            sx={{ 
              p: { xs: 3, md: 4 }, 
              mb: 4, 
              borderRadius: 4,
              ...glassStyle,
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Decorative element */}
            <Box
              sx={{
                position: "absolute",
                top: 0,
                right: 0,
                width: 250,
                height: 250,
                background: "linear-gradient(135deg, rgba(240, 147, 251, 0.1) 0%, transparent 100%)",
                borderRadius: "0 0 0 100%",
              }}
            />
            
            <Box sx={{ position: "relative", zIndex: 1 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                    display: "flex",
                    color: "white",
                  }}
                >
                  <Layers size={24} />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={700} color="text.primary">
                    Bulk Validation
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Process multiple validation codes at once
                  </Typography>
                </Box>
              </Box>
              
              <Alert 
                severity="info" 
                sx={{ 
                  mt: 2, 
                  mb: 3, 
                  borderRadius: 2,
                  background: "rgba(102, 126, 234, 0.08)",
                  border: "1px solid rgba(102, 126, 234, 0.2)",
                }}
                icon={<Info size={20} />}
              >
                Enter codes one at a time and press Enter. Perfect for processing multiple customers in a queue.
                <strong> Max 50 codes per batch.</strong>
              </Alert>
              
              <Box sx={{ display: "flex", gap: 2, mb: 3, flexDirection: { xs: "column", sm: "row" } }}>
                <TextField
                  inputRef={inputRef}
                  fullWidth
                  value={bulkInput}
                  onChange={(e) => setBulkInput(e.target.value.toUpperCase())}
                  onKeyPress={(e) => handleKeyPress(e, addBulkCode)}
                  placeholder="ABC123"
                  inputProps={{
                    maxLength: 6,
                    style: { 
                      textTransform: "uppercase", 
                      letterSpacing: "6px", 
                      fontWeight: 700,
                      textAlign: "center",
                      fontFamily: "monospace",
                      fontSize: "1.2rem",
                    },
                  }}
                  disabled={bulkLoading}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      borderRadius: 3,
                      background: "rgba(255, 255, 255, 0.8)",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        background: "white",
                        boxShadow: "0 4px 20px rgba(240, 147, 251, 0.15)",
                      },
                      "&.Mui-focused": {
                        background: "white",
                        boxShadow: "0 4px 20px rgba(240, 147, 251, 0.25)",
                      },
                    },
                  }}
                />
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button 
                    variant="contained" 
                    onClick={addBulkCode} 
                    disabled={bulkLoading || !bulkInput.trim()}
                    sx={{
                      minWidth: 56,
                      height: 56,
                      borderRadius: 3,
                      background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                      boxShadow: "0 4px 14px rgba(240, 147, 251, 0.4)",
                      "&:hover": {
                        background: "linear-gradient(135deg, #e085ec 0%, #e64d60 100%)",
                      },
                    }}
                  >
                    <Plus size={24} />
                  </Button>
                </motion.div>
              </Box>
              
              {bulkError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Alert 
                    severity="error" 
                    sx={{ 
                      mb: 3,
                      borderRadius: 2,
                      background: "rgba(244, 67, 54, 0.1)",
                      border: "1px solid rgba(244, 67, 54, 0.2)",
                    }}
                    icon={<AlertCircle size={20} />}
                  >
                    {bulkError}
                  </Alert>
                </motion.div>
              )}
              
              {/* Code chips - Modern Style */}
              {bulkCodes.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  transition={{ duration: 0.3 }}
                >
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      mb: 3,
                      borderRadius: 3,
                      background: "rgba(255, 255, 255, 0.6)",
                      border: "1px solid rgba(0, 0, 0, 0.05)",
                    }}
                  >
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                        <Badge 
                          badgeContent={bulkCodes.length} 
                          color="primary"
                          sx={{
                            "& .MuiBadge-badge": {
                              background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                              fontWeight: 700,
                            },
                          }}
                        >
                          <Hash size={20} />
                        </Badge>
                        <Typography variant="subtitle1" fontWeight={700}>
                          Codes Added
                        </Typography>
                      </Box>
                      <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button 
                          size="small" 
                          color="error" 
                          onClick={clearBulkCodes}
                          sx={{
                            borderRadius: 2,
                            fontWeight: 600,
                          }}
                        >
                          <Trash2 size={16} style={{ marginRight: 4 }} />
                          Clear All
                        </Button>
                      </motion.div>
                    </Box>
                    
                    <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
                      <AnimatePresence>
                        {bulkCodes.map((code, idx) => (
                          <motion.div
                            key={code}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            transition={{ delay: idx * 0.03 }}
                          >
                            <Chip
                              label={code}
                              onDelete={() => removeBulkCode(code)}
                              deleteIcon={
                                <motion.div whileHover={{ scale: 1.2 }}>
                                  <X size={16} />
                                </motion.div>
                              }
                              sx={{ 
                                fontFamily: "monospace", 
                                fontWeight: 700, 
                                letterSpacing: 2,
                                fontSize: "0.9rem",
                                py: 2.5,
                                background: "white",
                                border: "1px solid rgba(0, 0, 0, 0.08)",
                                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                                "&:hover": {
                                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
                                },
                              }}
                            />
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </Box>
                  </Paper>
                </motion.div>
              )}
              
              {/* Action buttons - Modern Style */}
              <Box sx={{ display: "flex", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
                <motion.div style={{ flex: 1 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={handleBulkLookup}
                    disabled={bulkLoading || bulkCodes.length === 0}
                    sx={{
                      py: 2,
                      borderRadius: 3,
                      fontWeight: 700,
                      fontSize: "1rem",
                      borderWidth: 2,
                      borderColor: "#667eea",
                      color: "#667eea",
                      "&:hover": {
                        borderWidth: 2,
                        borderColor: "#5a6fd6",
                        background: "rgba(102, 126, 234, 0.05)",
                      },
                    }}
                  >
                    {bulkLoading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Loader2 size={22} />
                      </motion.div>
                    ) : (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Eye size={20} />
                        Preview All
                      </Box>
                    )}
                  </Button>
                </motion.div>
                
                <motion.div style={{ flex: 1 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleBulkCollect}
                    disabled={bulkLoading || bulkCodes.length === 0}
                    sx={{
                      py: 2,
                      borderRadius: 3,
                      fontWeight: 700,
                      fontSize: "1rem",
                      background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                      boxShadow: "0 8px 30px rgba(56, 239, 125, 0.4)",
                      "&:hover": {
                        background: "linear-gradient(135deg, #0f8a7f 0%, #2ed06e 100%)",
                      },
                    }}
                  >
                    {bulkLoading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Loader2 size={22} />
                      </motion.div>
                    ) : (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Zap size={20} />
                        Collect All
                      </Box>
                    )}
                  </Button>
                </motion.div>
              </Box>
            </Box>
          </Paper>
          
          {/* Bulk Results - Modern Style */}
          <AnimatePresence>
            {bulkResults && (
              <motion.div 
                initial={{ opacity: 0, y: 30, scale: 0.98 }} 
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.98 }}
                transition={{ duration: 0.4 }}
              >
                <Paper 
                  elevation={0} 
                  sx={{ 
                    borderRadius: 4,
                    overflow: "hidden",
                    ...glassStyle,
                  }}
                >
                  {/* Results Header */}
                  <Box
                    sx={{
                      p: { xs: 3, md: 4 },
                      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
                      color: "white",
                    }}
                  >
                    <Typography variant="h6" fontWeight={700} sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                      <TrendingUp size={22} />
                      Processing Results
                    </Typography>
                  </Box>
                  
                  <Box sx={{ p: { xs: 3, md: 4 } }}>
                    {/* Summary Stats */}
                    <Grid container spacing={2} sx={{ mb: 4 }}>
                      {[
                        { 
                          value: bulkResults.total_processed || bulkResults.total_codes, 
                          label: "Total",
                          gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                          icon: <Hash size={20} />,
                        },
                        { 
                          value: bulkResults.success_count || bulkResults.valid_count || 0, 
                          label: "Successful",
                          gradient: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                          icon: <CheckCircle size={20} />,
                        },
                        { 
                          value: bulkResults.error_count || (bulkResults.total_codes - bulkResults.valid_count) || 0, 
                          label: "Failed",
                          gradient: "linear-gradient(135deg, #f5576c 0%, #f093fb 100%)",
                          icon: <XCircle size={20} />,
                        },
                        ...(bulkResults.pending_count !== undefined ? [{
                          value: bulkResults.pending_count,
                          label: "Pending",
                          gradient: "linear-gradient(135deg, #f093fb 0%, #764ba2 100%)",
                          icon: <Clock size={20} />,
                        }] : []),
                      ].map((stat, idx) => (
                        <Grid item xs={6} sm={3} key={idx}>
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                          >
                            <Paper
                              elevation={0}
                              sx={{
                                p: 2.5,
                                textAlign: "center",
                                borderRadius: 3,
                                background: stat.gradient,
                                color: "white",
                                position: "relative",
                                overflow: "hidden",
                              }}
                            >
                              <Box
                                sx={{
                                  position: "absolute",
                                  top: 8,
                                  right: 8,
                                  opacity: 0.3,
                                }}
                              >
                                {stat.icon}
                              </Box>
                              <Typography variant="h3" fontWeight={800}>
                                {stat.value}
                              </Typography>
                              <Typography variant="body2" sx={{ opacity: 0.9, fontWeight: 500 }}>
                                {stat.label}
                              </Typography>
                            </Paper>
                          </motion.div>
                        </Grid>
                      ))}
                    </Grid>
                    
                    <Divider sx={{ my: 3 }} />
                    
                    {/* Individual results */}
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
                      <Package size={22} />
                      Individual Results
                    </Typography>
                    
                    <Stack spacing={1.5}>
                      {bulkResults.results?.map((result, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                        >
                          <Card
                            elevation={0}
                            sx={{
                              borderRadius: 2,
                              overflow: "hidden",
                              border: "1px solid rgba(0, 0, 0, 0.05)",
                              background: "rgba(255, 255, 255, 0.7)",
                              transition: "all 0.2s ease",
                              "&:hover": {
                                background: "white",
                                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.06)",
                              },
                            }}
                          >
                            {/* Status indicator bar */}
                            <Box
                              sx={{
                                height: 3,
                                background: result.success 
                                  ? "linear-gradient(90deg, #11998e 0%, #38ef7d 100%)"
                                  : "linear-gradient(90deg, #f5576c 0%, #f093fb 100%)",
                              }}
                            />
                            
                            <CardContent sx={{ py: 2, "&:last-child": { pb: 2 } }}>
                              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 1 }}>
                                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                                  <Box
                                    sx={{
                                      p: 1,
                                      borderRadius: 1.5,
                                      background: result.success 
                                        ? "rgba(56, 239, 125, 0.1)" 
                                        : "rgba(244, 67, 54, 0.1)",
                                      color: result.success ? "#11998e" : "#f44336",
                                      display: "flex",
                                    }}
                                  >
                                    {result.success ? <CheckCircle size={18} /> : <XCircle size={18} />}
                                  </Box>
                                  
                                  <Box>
                                    <Typography 
                                      fontWeight={800} 
                                      sx={{ 
                                        fontFamily: "monospace", 
                                        letterSpacing: 3,
                                        fontSize: "1.1rem",
                                      }}
                                    >
                                      {result.validation_code}
                                    </Typography>
                                    {result.success && (
                                      <Typography variant="body2" color="text.secondary">
                                        {result.customer_name} • {result.product_name}
                                      </Typography>
                                    )}
                                    {!result.success && (
                                      <Typography variant="body2" color="error.main" fontWeight={500}>
                                        {result.error}
                                      </Typography>
                                    )}
                                  </Box>
                                </Box>
                                
                                {result.success && result.collection_summary && (
                                  renderStatusBadge(result.collection_summary.overall_status)
                                )}
                              </Box>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </Stack>
                  </Box>
                </Paper>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
      
      {/* ======================== */}
      {/* DIALOGS - Modern Style */}
      {/* ======================== */}
      
      {/* Variant Collection Dialog */}
      <Dialog 
        open={variantDialog.open} 
        onClose={() => setVariantDialog({ open: false, variant: null, index: 0 })}
        PaperProps={{
          sx: {
            borderRadius: 4,
            maxWidth: 450,
            width: "100%",
            ...glassStyle,
          },
        }}
        TransitionComponent={Zoom}
      >
        <Box
          sx={{
            background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
            p: 3,
            color: "white",
          }}
        >
          <DialogTitle sx={{ p: 0, color: "white" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <PackageCheck size={24} />
              <Typography variant="h6" fontWeight={700}>
                Collect Variant #{variantDialog.index + 1}
              </Typography>
            </Box>
          </DialogTitle>
        </Box>
        
        <DialogContent sx={{ p: 3 }}>
          <Box sx={{ pt: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Confirm the collection details for this item variant.
            </Typography>
            
            <TextField
              fullWidth
              type="number"
              label="Quantity to Collect"
              value={variantForm.quantity}
              onChange={(e) => setVariantForm({ ...variantForm, quantity: parseInt(e.target.value) || 1 })}
              inputProps={{ min: 1, max: variantDialog.variant?.ordered_quantity || 1 }}
              sx={{ 
                mb: 3,
                "& .MuiOutlinedInput-root": {
                  borderRadius: 2,
                },
              }}
            />
            
            <Paper
              elevation={0}
              sx={{
                p: 2,
                borderRadius: 2,
                background: "rgba(255, 152, 0, 0.08)",
                border: "1px solid rgba(255, 152, 0, 0.2)",
                mb: 2,
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={variantForm.substituted}
                    onChange={(e) => setVariantForm({ ...variantForm, substituted: e.target.checked })}
                    sx={{
                      "&.Mui-checked": {
                        color: "#f5576c",
                      },
                    }}
                  />
                }
                label={
                  <Typography variant="body2" fontWeight={600}>
                    Item was substituted (different color/size)
                  </Typography>
                }
              />
            </Paper>
            
            <AnimatePresence>
              {variantForm.substituted && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <TextField
                    fullWidth
                    label="Substitution Notes"
                    value={variantForm.substitution_notes}
                    onChange={(e) => setVariantForm({ ...variantForm, substitution_notes: e.target.value })}
                    placeholder="e.g., Given red instead of blue"
                    multiline
                    rows={2}
                    sx={{ 
                      mt: 2,
                      "& .MuiOutlinedInput-root": {
                        borderRadius: 2,
                      },
                    }}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ p: 3, pt: 0, gap: 1 }}>
          <Button 
            onClick={() => setVariantDialog({ open: false, variant: null, index: 0 })}
            sx={{ 
              borderRadius: 2,
              fontWeight: 600,
              px: 3,
            }}
          >
            Cancel
          </Button>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              variant="contained"
              onClick={() =>
                handleSingleCollect([
                  {
                    variant_index: variantDialog.index,
                    quantity: variantForm.quantity,
                    substituted: variantForm.substituted,
                    substitution_notes: variantForm.substitution_notes,
                  },
                ])
              }
              sx={{
                borderRadius: 2,
                fontWeight: 700,
                px: 4,
                background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
                boxShadow: "0 4px 14px rgba(56, 239, 125, 0.3)",
                "&:hover": {
                  background: "linear-gradient(135deg, #0f8a7f 0%, #2ed06e 100%)",
                },
              }}
            >
              <CheckCircle size={18} style={{ marginRight: 6 }} />
              Confirm Collection
            </Button>
          </motion.div>
        </DialogActions>
      </Dialog>
      
      {/* Mark Unavailable Dialog */}
      <Dialog 
        open={unavailableDialog.open} 
        onClose={() => setUnavailableDialog({ open: false, variant: null, index: 0 })}
        PaperProps={{
          sx: {
            borderRadius: 4,
            maxWidth: 450,
            width: "100%",
            ...glassStyle,
          },
        }}
        TransitionComponent={Zoom}
      >
        <Box
          sx={{
            background: "linear-gradient(135deg, #f5576c 0%, #f093fb 100%)",
            p: 3,
            color: "white",
          }}
        >
          <DialogTitle sx={{ p: 0, color: "white" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <Ban size={24} />
              <Typography variant="h6" fontWeight={700}>
                Mark as Unavailable
              </Typography>
            </Box>
          </DialogTitle>
        </Box>
        
        <DialogContent sx={{ p: 3 }}>
          <Alert 
            severity="warning" 
            sx={{ 
              mb: 3, 
              borderRadius: 2,
              background: "rgba(255, 152, 0, 0.1)",
              border: "1px solid rgba(255, 152, 0, 0.2)",
            }}
            icon={<AlertTriangle size={20} />}
          >
            This will mark the item as unavailable. The customer will be notified.
          </Alert>
          
          <TextField
            fullWidth
            label="Reason (optional)"
            value={unavailableReason}
            onChange={(e) => setUnavailableReason(e.target.value)}
            placeholder="e.g., Out of stock, Wrong size, etc."
            multiline
            rows={3}
            sx={{ 
              "& .MuiOutlinedInput-root": {
                borderRadius: 2,
              },
            }}
          />
        </DialogContent>
        
        <DialogActions sx={{ p: 3, pt: 0, gap: 1 }}>
          <Button 
            onClick={() => setUnavailableDialog({ open: false, variant: null, index: 0 })}
            sx={{ 
              borderRadius: 2,
              fontWeight: 600,
              px: 3,
            }}
          >
            Cancel
          </Button>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button 
              variant="contained" 
              onClick={handleMarkUnavailable}
              sx={{
                borderRadius: 2,
                fontWeight: 700,
                px: 4,
                background: "linear-gradient(135deg, #f5576c 0%, #f093fb 100%)",
                boxShadow: "0 4px 14px rgba(245, 87, 108, 0.3)",
                "&:hover": {
                  background: "linear-gradient(135deg, #e64d60 0%, #e085ec 100%)",
                },
              }}
            >
              <Ban size={18} style={{ marginRight: 6 }} />
              Mark Unavailable
            </Button>
          </motion.div>
        </DialogActions>
      </Dialog>
      
      {/* Modern Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        TransitionComponent={Fade}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            variant="filled"
            sx={{ 
              width: "100%",
              borderRadius: 3,
              fontWeight: 600,
              boxShadow: "0 8px 30px rgba(0, 0, 0, 0.2)",
              ...(snackbar.severity === "success" && {
                background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
              }),
              ...(snackbar.severity === "error" && {
                background: "linear-gradient(135deg, #f5576c 0%, #f093fb 100%)",
              }),
              ...(snackbar.severity === "warning" && {
                background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
              }),
            }}
          >
            {snackbar.message}
          </Alert>
        </motion.div>
      </Snackbar>
      </Box>
    </Box>
  );
}

export default StaffMerchandiseValidation;
