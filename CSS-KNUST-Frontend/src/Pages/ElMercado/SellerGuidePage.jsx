import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Store,
  Package,
  ShoppingCart,
  Wallet,
  MessageSquare,
  Star,
  TrendingUp,
  Shield,
  ChevronRight,
  ChevronDown,
  Search,
  Home,
  HelpCircle,
  FileText,
  BookOpen,
  Play,
  ExternalLink,
  Mail,
  Percent,
} from "lucide-react";
import Navbar from "../../Components/Navbar";
import { Footer } from "../../Components/Footer/Footer";
import { API_BASE_URL } from "../../utils/config";

// Guide sections data
const GUIDE_SECTIONS = [
  {
    id: "getting-started",
    title: "Getting Started",
    icon: Play,
    color: "purple",
    description: "Everything you need to know to begin selling",
    subsections: [
      {
        id: "dashboard-overview",
        title: "Dashboard Overview",
        content: `
          <h4>Accessing Your Dashboard</h4>
          <p>Once your seller application is approved, you can access your dashboard at:</p>
          <div class="code-block">
            <code>${API_BASE_URL}/seller-dashboard/</code>
          </div>
          
          <h4>Dashboard Sections</h4>
          <ul>
            <li><strong>Home:</strong> Quick overview of your store's performance, recent orders, and notifications</li>
            <li><strong>Listings:</strong> Manage all your products, digital items, and services</li>
            <li><strong>Orders:</strong> Track and fulfill customer orders</li>
            <li><strong>Reviews:</strong> Monitor customer feedback and respond to reviews</li>
            <li><strong>Wallet:</strong> View earnings, pending balances, and transaction history</li>
            <li><strong>Payouts:</strong> Request withdrawals and manage payout accounts</li>
            <li><strong>Messages:</strong> Communicate with buyers</li>
            <li><strong>Profile:</strong> Update your store branding and settings</li>
          </ul>
          
          <div class="tip-box">
            <strong>💡 Pro Tip:</strong> Bookmark your seller dashboard for quick access. You'll spend most of your time here!
          </div>
        `,
      },
      {
        id: "profile-setup",
        title: "Setting Up Your Profile",
        content: `
          <h4>Complete Your Seller Profile</h4>
          <p>A complete profile builds trust with buyers. Make sure to:</p>
          
          <ol>
            <li><strong>Upload a Logo:</strong> Use a clear, professional logo (recommended: 400x400px)</li>
            <li><strong>Add a Banner:</strong> Showcase your brand with a banner image (recommended: 1200x300px)</li>
            <li><strong>Write a Description:</strong> Tell customers about your store, what you sell, and why they should buy from you</li>
            <li><strong>Update Contact Info:</strong> Ensure your email and phone are correct for order notifications</li>
          </ol>
          
          <h4>Store Settings</h4>
          <ul>
            <li><strong>Auto-Accept Orders:</strong> When enabled, orders are automatically accepted when payment is confirmed</li>
            <li><strong>Vacation Mode:</strong> Temporarily disable your store when you're unavailable. Buyers will see your vacation message.</li>
          </ul>
          
          <div class="warning-box">
            <strong>⚠️ Important:</strong> Keep your contact information up-to-date. This is how we'll notify you about orders!
          </div>
        `,
      },
      {
        id: "seller-types",
        title: "Understanding Seller Types",
        content: `
          <h4>Individual Seller (P2P)</h4>
          <p>Perfect for students and individuals who want to:</p>
          <ul>
            <li>Sell personal items (used or new)</li>
            <li>Offer freelance services</li>
            <li>Sell digital products like notes, templates, or artwork</li>
          </ul>
          
          <h4>Business Seller (B2C)</h4>
          <p>Ideal for registered businesses that want to:</p>
          <ul>
            <li>Sell branded merchandise</li>
            <li>Operate a full e-commerce store</li>
            <li>Reach the KNUST community market</li>
          </ul>
          
          <h4>Verification Levels</h4>
          <table class="info-table">
            <tr><th>Level</th><th>Requirements</th><th>Benefits</th></tr>
            <tr>
              <td>Level 1</td>
              <td>Basic verification (ID)</td>
              <td>Can list up to 20 products</td>
            </tr>
            <tr>
              <td>Level 2</td>
              <td>Address verification</td>
              <td>Up to 50 products, priority support</td>
            </tr>
            <tr>
              <td>Level 3+</td>
              <td>Business documents + track record</td>
              <td>Unlimited products, featured placement</td>
            </tr>
          </table>
        `,
      },
    ],
  },
  {
    id: "listings",
    title: "Managing Listings",
    icon: Package,
    color: "blue",
    description: "Create and manage your products, services, and digital items",
    subsections: [
      {
        id: "create-listing",
        title: "Creating a New Listing",
        content: `
          <h4>Step-by-Step Guide</h4>
          <ol>
            <li>Go to <strong>Listings</strong> → <strong>Add Listing</strong></li>
            <li>Choose the listing type:
              <ul>
                <li><strong>Physical Product:</strong> Items that require shipping</li>
                <li><strong>Digital Product:</strong> Downloadable files, templates, notes</li>
                <li><strong>Service:</strong> Tutoring, design work, repairs, etc.</li>
              </ul>
            </li>
            <li>Fill in the basic information:
              <ul>
                <li>Title (clear and descriptive)</li>
                <li>Description (detailed, highlight benefits)</li>
                <li>Category (select the most relevant)</li>
              </ul>
            </li>
            <li>Set pricing and inventory</li>
            <li>Upload high-quality images</li>
            <li>Set condition (New, Like New, Good, Fair, Used)</li>
            <li>Click <strong>Save as Draft</strong> or <strong>Submit for Review</strong></li>
          </ol>
          
          <div class="tip-box">
            <strong>💡 Pro Tip:</strong> Use all available image slots. Listings with multiple images sell 3x faster!
          </div>
        `,
      },
      {
        id: "listing-images",
        title: "Product Images Best Practices",
        content: `
          <h4>Image Requirements</h4>
          <ul>
            <li><strong>Main Image:</strong> Required for all listings</li>
            <li><strong>Gallery Images:</strong> Up to 8 additional images</li>
            <li><strong>Minimum Size:</strong> 800x800 pixels</li>
            <li><strong>Format:</strong> JPG, PNG, or WebP</li>
            <li><strong>Max File Size:</strong> 5MB per image</li>
          </ul>
          
          <h4>Tips for Great Photos</h4>
          <ol>
            <li><strong>Good Lighting:</strong> Natural light works best</li>
            <li><strong>Clean Background:</strong> White or neutral backgrounds</li>
            <li><strong>Multiple Angles:</strong> Show front, back, sides, and details</li>
            <li><strong>Show Scale:</strong> Include items for size reference</li>
            <li><strong>Show Defects:</strong> For used items, photograph any wear honestly</li>
          </ol>
          
          <div class="warning-box">
            <strong>⚠️ Don't:</strong> Use stock photos, watermarked images, or photos from other sellers
          </div>
        `,
      },
      {
        id: "listing-pricing",
        title: "Pricing Your Products",
        content: `
          <h4>Setting the Right Price</h4>
          <ul>
            <li>Research similar products on El Mercado</li>
            <li>Consider your costs (item cost + commission + shipping)</li>
            <li>Factor in platform commission (typically 10%)</li>
            <li>Use <strong>Compare at Price</strong> to show discounts</li>
          </ul>
          
          <h4>Price Calculation Example</h4>
          <div class="code-block">
            <code>
Item Cost: GHS 80<br/>
Desired Profit: GHS 20<br/>
Platform Commission (10%): GHS 11<br/>
─────────────────────<br/>
Listing Price: GHS 111
            </code>
          </div>
          
          <h4>Showing Discounts</h4>
          <p>To display a discount badge on your listing:</p>
          <ol>
            <li>Set your selling price in the <strong>Price</strong> field</li>
            <li>Enter the original/higher price in <strong>Compare at Price</strong></li>
            <li>The discount percentage will be calculated automatically</li>
          </ol>
        `,
      },
      {
        id: "listing-inventory",
        title: "Inventory Management",
        content: `
          <h4>Stock Tracking</h4>
          <ul>
            <li><strong>Track Inventory:</strong> Enable to automatically update stock when orders are placed</li>
            <li><strong>Stock Quantity:</strong> Set your current available quantity</li>
            <li><strong>Low Stock Threshold:</strong> Get notified when stock falls below this number</li>
            <li><strong>Allow Backorder:</strong> Accept orders even when out of stock</li>
          </ul>
          
          <h4>Listing Statuses</h4>
          <table class="info-table">
            <tr><th>Status</th><th>Meaning</th></tr>
            <tr><td>Draft</td><td>Not visible to buyers, still being edited</td></tr>
            <tr><td>Pending Review</td><td>Submitted and waiting for approval</td></tr>
            <tr><td>Active</td><td>Live and visible to buyers</td></tr>
            <tr><td>Sold Out</td><td>Stock is zero (auto-set if tracking enabled)</td></tr>
            <tr><td>Inactive</td><td>Manually hidden from buyers</td></tr>
            <tr><td>Rejected</td><td>Did not meet guidelines (see reason)</td></tr>
          </table>
        `,
      },
      {
        id: "listing-variants",
        title: "Product Variants",
        content: `
          <h4>What are Variants?</h4>
          <p>Variants let you sell the same product in different options (size, color, etc.) under one listing.</p>
          
          <h4>Adding Variants</h4>
          <ol>
            <li>Create your main listing first</li>
            <li>Scroll to the <strong>Variants</strong> section</li>
            <li>Click <strong>Add Variant</strong></li>
            <li>Enter variant details:
              <ul>
                <li><strong>Name:</strong> e.g., "Red / Large"</li>
                <li><strong>SKU:</strong> Your internal code (optional)</li>
                <li><strong>Price:</strong> Override the main price if different</li>
                <li><strong>Stock:</strong> Stock for this specific variant</li>
              </ul>
            </li>
          </ol>
          
          <h4>Example: T-Shirt with Sizes</h4>
          <div class="code-block">
            <code>
Main Listing: CSS KNUST T-Shirt - GHS 80<br/>
├── Variant: Small - GHS 80 (Stock: 10)<br/>
├── Variant: Medium - GHS 80 (Stock: 15)<br/>
├── Variant: Large - GHS 85 (Stock: 12)<br/>
└── Variant: XL - GHS 90 (Stock: 8)
            </code>
          </div>
        `,
      },
    ],
  },
  {
    id: "orders",
    title: "Order Management",
    icon: ShoppingCart,
    color: "green",
    description: "Process, fulfill, and track customer orders",
    subsections: [
      {
        id: "order-workflow",
        title: "Order Workflow",
        content: `
          <h4>Order Lifecycle</h4>
          <div class="workflow-steps">
            <div class="step">
              <span class="step-num">1</span>
              <strong>Pending</strong>
              <p>Order created, awaiting payment</p>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <strong>Paid</strong>
              <p>Payment confirmed</p>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <strong>Processing</strong>
              <p>Preparing the order</p>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <strong>Shipped</strong>
              <p>Order dispatched (for physical items)</p>
            </div>
            <div class="step">
              <span class="step-num">5</span>
              <strong>Delivered</strong>
              <p>Buyer confirms receipt</p>
            </div>
            <div class="step">
              <span class="step-num">6</span>
              <strong>Completed</strong>
              <p>Funds released to your wallet</p>
            </div>
          </div>
          
          <div class="tip-box">
            <strong>💡 Note:</strong> For digital products, orders move to "Delivered" automatically after download.
          </div>
        `,
      },
      {
        id: "processing-orders",
        title: "Processing Orders",
        content: `
          <h4>When You Receive an Order</h4>
          <ol>
            <li>You'll receive a notification (email + dashboard)</li>
            <li>Review the order details:
              <ul>
                <li>Items ordered and quantities</li>
                <li>Shipping address (for physical items)</li>
                <li>Buyer notes (if any)</li>
              </ul>
            </li>
            <li>If <strong>Auto-Accept</strong> is disabled, accept or decline the order</li>
            <li>Prepare the item(s) for shipping</li>
            <li>Mark as <strong>Processing</strong> while you prepare</li>
          </ol>
          
          <h4>Order Actions</h4>
          <ul>
            <li><strong>Accept:</strong> Confirm you can fulfill the order</li>
            <li><strong>Process:</strong> Indicate you're preparing the order</li>
            <li><strong>Ship:</strong> Mark as shipped and add tracking info</li>
            <li><strong>Add Notes:</strong> Internal notes only you can see</li>
          </ul>
        `,
      },
      {
        id: "shipping-orders",
        title: "Shipping & Tracking",
        content: `
          <h4>Adding Shipping Information</h4>
          <ol>
            <li>Once your item is shipped, go to the order</li>
            <li>Click <strong>Mark as Shipped</strong></li>
            <li>Enter tracking details:
              <ul>
                <li><strong>Tracking Number:</strong> From your courier</li>
                <li><strong>Tracking URL:</strong> Link to track the package</li>
              </ul>
            </li>
            <li>The buyer will be notified with tracking info</li>
          </ol>
          
          <h4>Delivery Options in KNUST</h4>
          <ul>
            <li><strong>Campus Delivery:</strong> Arrange to meet on campus</li>
            <li><strong>Hall Delivery:</strong> Deliver to buyer's hall of residence</li>
            <li><strong>Pickup Point:</strong> Set a convenient pickup location</li>
            <li><strong>Courier Services:</strong> Use services like Bolt, Glovo</li>
          </ul>
          
          <div class="warning-box">
            <strong>⚠️ Important:</strong> Always get proof of delivery (signature, photo, or written confirmation)
          </div>
        `,
      },
      {
        id: "order-issues",
        title: "Handling Order Issues",
        content: `
          <h4>Common Issues & Solutions</h4>
          
          <table class="info-table">
            <tr><th>Issue</th><th>Solution</th></tr>
            <tr>
              <td>Out of stock after order</td>
              <td>Contact buyer immediately, offer alternatives or cancel</td>
            </tr>
            <tr>
              <td>Wrong item shipped</td>
              <td>Arrange return/exchange at your cost</td>
            </tr>
            <tr>
              <td>Buyer not responding</td>
              <td>Use the messaging system, wait 48 hours, then contact support</td>
            </tr>
            <tr>
              <td>Item damaged in transit</td>
              <td>Document with photos, work with buyer on resolution</td>
            </tr>
          </table>
          
          <h4>Cancellations & Refunds</h4>
          <ul>
            <li>Orders can be cancelled before shipping</li>
            <li>Refunds are processed through the platform</li>
            <li>Commission is refunded for cancelled orders</li>
            <li>Frequent cancellations may affect your seller rating</li>
          </ul>
        `,
      },
    ],
  },
  {
    id: "finances",
    title: "Finances & Payouts",
    icon: Wallet,
    color: "amber",
    description: "Understand earnings, commissions, and withdrawals",
    subsections: [
      {
        id: "understanding-earnings",
        title: "Understanding Your Earnings",
        content: `
          <h4>How Earnings Work</h4>
          <ol>
            <li><strong>Order Placed:</strong> Buyer pays the full amount</li>
            <li><strong>Pending Balance:</strong> Your earnings (minus commission) go to pending</li>
            <li><strong>Order Completed:</strong> Once delivered & confirmed, funds move to available balance</li>
            <li><strong>Withdrawal:</strong> Request payout to your bank/mobile money</li>
          </ol>
          
          <h4>Your Wallet Balances</h4>
          <table class="info-table">
            <tr><th>Balance Type</th><th>Description</th></tr>
            <tr>
              <td>Pending Balance</td>
              <td>Earnings from orders not yet completed (held in escrow)</td>
            </tr>
            <tr>
              <td>Available Balance</td>
              <td>Funds you can withdraw</td>
            </tr>
            <tr>
              <td>Total Earned</td>
              <td>Lifetime earnings (all-time)</td>
            </tr>
            <tr>
              <td>Total Withdrawn</td>
              <td>Amount you've withdrawn to date</td>
            </tr>
          </table>
        `,
      },
      {
        id: "commission-structure",
        title: "Commission Structure",
        content: `
          <h4>Platform Commission</h4>
          <p>El Mercado charges a commission on each successful sale to maintain the platform.</p>
          
          <table class="info-table">
            <tr><th>Category</th><th>Commission Rate</th></tr>
            <tr><td>Physical Products</td><td>10%</td></tr>
            <tr><td>Digital Products</td><td>8%</td></tr>
            <tr><td>Services</td><td>12%</td></tr>
            <tr><td>Electronics</td><td>8%</td></tr>
            <tr><td>Fashion</td><td>15%</td></tr>
          </table>
          
          <h4>Calculation Example</h4>
          <div class="code-block">
            <code>
Sale Price: GHS 100<br/>
Commission Rate: 10%<br/>
Platform Commission: GHS 10<br/>
─────────────────────<br/>
Your Earnings: GHS 90
            </code>
          </div>
          
          <p>For detailed information, see our <a href="/el_mercado/commission-policy" target="_blank">Commission Policy</a>.</p>
        `,
      },
      {
        id: "requesting-payouts",
        title: "Requesting Payouts",
        content: `
          <h4>Payout Requirements</h4>
          <ul>
            <li>Minimum withdrawal: <strong>GHS 50</strong></li>
            <li>Must have verified payout account</li>
            <li>Funds must be in Available Balance (not Pending)</li>
          </ul>
          
          <h4>How to Request a Payout</h4>
          <ol>
            <li>Go to <strong>Wallet</strong> → <strong>Request Payout</strong></li>
            <li>Enter the amount to withdraw</li>
            <li>Select your payout method</li>
            <li>Review and confirm</li>
            <li>Payout will be processed within 1-3 business days</li>
          </ol>
          
          <h4>Payout Methods</h4>
          <ul>
            <li><strong>Mobile Money:</strong> MTN MoMo, Vodafone Cash, AirtelTigo Money</li>
            <li><strong>Bank Transfer:</strong> All major Ghanaian banks</li>
          </ul>
          
          <div class="tip-box">
            <strong>💡 Auto-Payout:</strong> Enable automatic payouts when your balance reaches a threshold (e.g., GHS 500)
          </div>
        `,
      },
      {
        id: "payout-accounts",
        title: "Managing Payout Accounts",
        content: `
          <h4>Adding a Payout Account</h4>
          <ol>
            <li>Go to <strong>Payout Accounts</strong></li>
            <li>Click <strong>Add Account</strong></li>
            <li>Choose account type:
              <ul>
                <li><strong>Bank Account:</strong> Bank name, account number, account name</li>
                <li><strong>Mobile Money:</strong> Provider, phone number, registered name</li>
              </ul>
            </li>
            <li>Save and verify the account</li>
          </ol>
          
          <h4>Verification Process</h4>
          <p>For security, we verify payout accounts before use:</p>
          <ul>
            <li>Bank accounts: Small deposit verification</li>
            <li>Mobile Money: OTP verification to your number</li>
          </ul>
          
          <h4>Default Account</h4>
          <p>Set a default payout account for automatic payouts. You can have multiple accounts but only one default.</p>
          
          <div class="warning-box">
            <strong>⚠️ Security:</strong> Never share your payout account details with anyone claiming to be from El Mercado support.
          </div>
        `,
      },
    ],
  },
  {
    id: "reviews",
    title: "Reviews & Ratings",
    icon: Star,
    color: "yellow",
    description: "Build your reputation through customer feedback",
    subsections: [
      {
        id: "importance-of-reviews",
        title: "Why Reviews Matter",
        content: `
          <h4>Impact on Your Business</h4>
          <ul>
            <li><strong>Trust:</strong> Buyers rely on reviews to make decisions</li>
            <li><strong>Visibility:</strong> Higher-rated sellers appear higher in search</li>
            <li><strong>Conversion:</strong> Products with reviews sell 270% more</li>
            <li><strong>Verification:</strong> Consistent good reviews unlock verified badge</li>
          </ul>
          
          <h4>Rating Scale</h4>
          <div class="rating-guide">
            <div class="rating-item">
              <span class="stars">★★★★★</span>
              <span>Excellent - Keep it up!</span>
            </div>
            <div class="rating-item">
              <span class="stars">★★★★☆</span>
              <span>Good - Room for improvement</span>
            </div>
            <div class="rating-item">
              <span class="stars">★★★☆☆</span>
              <span>Average - Needs attention</span>
            </div>
            <div class="rating-item">
              <span class="stars">★★☆☆☆</span>
              <span>Below Average - Take action</span>
            </div>
            <div class="rating-item">
              <span class="stars">★☆☆☆☆</span>
              <span>Poor - Risk of suspension</span>
            </div>
          </div>
        `,
      },
      {
        id: "responding-to-reviews",
        title: "Responding to Reviews",
        content: `
          <h4>Responding to Positive Reviews</h4>
          <ul>
            <li>Thank the customer sincerely</li>
            <li>Personalize your response (use their name)</li>
            <li>Invite them to shop again</li>
          </ul>
          
          <h4>Handling Negative Reviews</h4>
          <ol>
            <li><strong>Don't Panic:</strong> Take time to understand the issue</li>
            <li><strong>Respond Professionally:</strong> Never be defensive or rude</li>
            <li><strong>Acknowledge:</strong> Thank them for the feedback</li>
            <li><strong>Apologize:</strong> If there was an issue on your end</li>
            <li><strong>Offer Solution:</strong> Propose how to make it right</li>
            <li><strong>Take it Offline:</strong> Offer to discuss privately</li>
          </ol>
          
          <h4>Example Response to Negative Review</h4>
          <div class="code-block" style="background: #f8f9fa;">
            <code style="white-space: pre-wrap;">
"Hi [Name], thank you for your feedback. I'm sorry your experience wasn't what you expected. I'd love to make this right - please message me directly so we can resolve this. Your satisfaction is my priority!"
            </code>
          </div>
        `,
      },
      {
        id: "getting-more-reviews",
        title: "Getting More Reviews",
        content: `
          <h4>Encourage Reviews</h4>
          <ul>
            <li>Deliver exceptional service - reviews follow naturally</li>
            <li>Include a thank-you note asking for a review</li>
            <li>Follow up after delivery (via messaging)</li>
            <li>Make the review process easy</li>
          </ul>
          
          <h4>What NOT to Do</h4>
          <ul class="dont-list">
            <li>❌ Offer incentives for positive reviews</li>
            <li>❌ Ask family/friends to leave fake reviews</li>
            <li>❌ Pressure buyers for 5-star reviews</li>
            <li>❌ Retaliate against negative reviewers</li>
          </ul>
          
          <div class="warning-box">
            <strong>⚠️ Policy:</strong> Fake or incentivized reviews violate our terms and can result in account suspension.
          </div>
        `,
      },
    ],
  },
  {
    id: "messaging",
    title: "Communication",
    icon: MessageSquare,
    color: "indigo",
    description: "Best practices for buyer communication",
    subsections: [
      {
        id: "messaging-basics",
        title: "Messaging Buyers",
        content: `
          <h4>The Messaging System</h4>
          <p>El Mercado provides a built-in messaging system for all buyer-seller communication.</p>
          
          <h4>When to Message</h4>
          <ul>
            <li>Clarifying order details</li>
            <li>Coordinating delivery/pickup</li>
            <li>Responding to product questions</li>
            <li>Resolving issues professionally</li>
            <li>Following up after delivery</li>
          </ul>
          
          <h4>Message Indicators</h4>
          <ul>
            <li><strong>Unread Count:</strong> Shows in your dashboard sidebar</li>
            <li><strong>Read Receipts:</strong> Know when buyer sees your message</li>
            <li><strong>Notifications:</strong> Email alerts for new messages</li>
          </ul>
        `,
      },
      {
        id: "communication-tips",
        title: "Communication Best Practices",
        content: `
          <h4>Do's</h4>
          <ul>
            <li>✅ Respond within 24 hours (sooner is better)</li>
            <li>✅ Be polite and professional</li>
            <li>✅ Provide clear, helpful answers</li>
            <li>✅ Use proper grammar and spelling</li>
            <li>✅ Set expectations clearly</li>
          </ul>
          
          <h4>Don'ts</h4>
          <ul>
            <li>❌ Share personal contact info</li>
            <li>❌ Conduct transactions outside the platform</li>
            <li>❌ Use offensive or inappropriate language</li>
            <li>❌ Ignore messages (affects seller score)</li>
            <li>❌ Make promises you can't keep</li>
          </ul>
          
          <h4>Response Templates</h4>
          <p>Save time with these common responses:</p>
          <div class="code-block" style="background: #f8f9fa; font-size: 13px;">
            <code>
<strong>Order Confirmation:</strong>
"Hi! Thanks for your order. I'm preparing it now and will ship within [X] days. I'll send you the tracking info once shipped!"

<strong>Shipping Update:</strong>
"Your order has been shipped! Track it here: [link]. Expected delivery: [date]. Let me know if you have any questions!"

<strong>Delivery Confirmation:</strong>
"Hi! Just checking if you received your order okay. Please confirm delivery when you can. Thank you for shopping with us!"
            </code>
          </div>
        `,
      },
    ],
  },
  {
    id: "best-practices",
    title: "Seller Best Practices",
    icon: TrendingUp,
    color: "emerald",
    description: "Tips to maximize your sales and success",
    subsections: [
      {
        id: "optimization-tips",
        title: "Listing Optimization",
        content: `
          <h4>Title Optimization</h4>
          <ul>
            <li>Include key product details (brand, size, color)</li>
            <li>Use searchable keywords</li>
            <li>Keep it under 80 characters</li>
            <li>Avoid ALL CAPS or excessive punctuation</li>
          </ul>
          
          <h4>Example Titles</h4>
          <div class="code-block">
            <code>
❌ Bad: "LAPTOP FOR SALE CHEAP!!!!"
✅ Good: "HP Pavilion 15 Laptop - Intel i5, 8GB RAM, 256GB SSD"

❌ Bad: "Nice shirt"
✅ Good: "CSS KNUST Official Polo Shirt - Navy Blue - Large"
            </code>
          </div>
          
          <h4>Description Tips</h4>
          <ul>
            <li>Start with the most important info</li>
            <li>Include specifications and dimensions</li>
            <li>Mention included accessories</li>
            <li>Be honest about condition (for used items)</li>
            <li>Add keywords naturally</li>
          </ul>
        `,
      },
      {
        id: "pricing-strategy",
        title: "Pricing Strategies",
        content: `
          <h4>Competitive Pricing</h4>
          <ul>
            <li>Research what similar items sell for</li>
            <li>Consider your costs and desired profit</li>
            <li>Factor in platform commission</li>
            <li>Price fairly - buyers compare!</li>
          </ul>
          
          <h4>Pricing Tactics</h4>
          <ul>
            <li><strong>Psychological Pricing:</strong> GHS 99 instead of GHS 100</li>
            <li><strong>Bundle Pricing:</strong> Offer discounts on multiple items</li>
            <li><strong>Discount Strategy:</strong> Use Compare at Price for sales</li>
            <li><strong>Competitive Matching:</strong> Match or beat competitors</li>
          </ul>
          
          <h4>When to Adjust Prices</h4>
          <ul>
            <li>Item not selling after 2 weeks</li>
            <li>Similar items are priced lower</li>
            <li>Seasonal demand changes</li>
            <li>Running a promotional campaign</li>
          </ul>
        `,
      },
      {
        id: "customer-service",
        title: "Customer Service Excellence",
        content: `
          <h4>The KNUST Community Advantage</h4>
          <p>You're selling to fellow students and community members. Build relationships, not just transactions!</p>
          
          <h4>Service Standards</h4>
          <ul>
            <li><strong>Response Time:</strong> Under 4 hours during business hours</li>
            <li><strong>Shipping Time:</strong> Ship within 48 hours of order</li>
            <li><strong>Accuracy:</strong> Send exactly what was ordered</li>
            <li><strong>Packaging:</strong> Protect items properly</li>
            <li><strong>Follow-up:</strong> Check in after delivery</li>
          </ul>
          
          <h4>Going Above & Beyond</h4>
          <ul>
            <li>Include a handwritten thank-you note</li>
            <li>Package items nicely</li>
            <li>Offer flexible pickup/delivery options</li>
            <li>Be understanding with issues</li>
            <li>Turn problems into opportunities</li>
          </ul>
        `,
      },
      {
        id: "growth-tips",
        title: "Growing Your Business",
        content: `
          <h4>Build Your Reputation</h4>
          <ol>
            <li>Start with a few quality listings</li>
            <li>Focus on excellent service</li>
            <li>Collect positive reviews</li>
            <li>Gradually expand your inventory</li>
            <li>Become a go-to seller in your niche</li>
          </ol>
          
          <h4>Marketing Your Store</h4>
          <ul>
            <li>Share listings on WhatsApp status</li>
            <li>Post in relevant KNUST groups (with permission)</li>
            <li>Word of mouth from satisfied customers</li>
            <li>Offer referral incentives</li>
          </ul>
          
          <h4>Track Your Performance</h4>
          <ul>
            <li>Monitor your dashboard statistics</li>
            <li>Track which items sell best</li>
            <li>Note seasonal trends</li>
            <li>Learn from reviews and feedback</li>
          </ul>
        `,
      },
    ],
  },
  {
    id: "policies",
    title: "Policies & Guidelines",
    icon: Shield,
    color: "red",
    description: "Rules and requirements for selling on El Mercado",
    subsections: [
      {
        id: "prohibited-items",
        title: "Prohibited Items",
        content: `
          <h4>Items Not Allowed</h4>
          <ul class="dont-list">
            <li>❌ Weapons and ammunition</li>
            <li>❌ Drugs and controlled substances</li>
            <li>❌ Counterfeit/fake branded products</li>
            <li>❌ Stolen goods</li>
            <li>❌ Adult content</li>
            <li>❌ Hazardous materials</li>
            <li>❌ Exam papers or academic cheating services</li>
            <li>❌ Items promoting hate or violence</li>
            <li>❌ Personal data or accounts</li>
            <li>❌ Medical prescriptions</li>
          </ul>
          
          <h4>Restricted Items</h4>
          <p>These require approval or have special requirements:</p>
          <ul>
            <li>Electronics (must be in working condition)</li>
            <li>Food items (proper handling required)</li>
            <li>Supplements (proper labeling required)</li>
          </ul>
          
          <div class="warning-box">
            <strong>⚠️ Violation:</strong> Listing prohibited items will result in immediate account suspension and potential legal action.
          </div>
        `,
      },
      {
        id: "seller-requirements",
        title: "Seller Requirements",
        content: `
          <h4>Maintain Good Standing</h4>
          <ul>
            <li><strong>Order Fulfillment Rate:</strong> Ship 95%+ of orders</li>
            <li><strong>Cancellation Rate:</strong> Keep under 5%</li>
            <li><strong>Response Time:</strong> Reply to messages within 24 hours</li>
            <li><strong>Review Rating:</strong> Maintain 3.5+ stars average</li>
          </ul>
          
          <h4>Account Health Indicators</h4>
          <table class="info-table">
            <tr><th>Status</th><th>Requirements</th><th>Impact</th></tr>
            <tr>
              <td style="color: green;">Excellent</td>
              <td>4.5+ rating, &lt;2% cancellation</td>
              <td>Featured placement, priority support</td>
            </tr>
            <tr>
              <td style="color: blue;">Good</td>
              <td>4.0+ rating, &lt;5% cancellation</td>
              <td>Normal visibility</td>
            </tr>
            <tr>
              <td style="color: orange;">At Risk</td>
              <td>3.5+ rating, &lt;10% cancellation</td>
              <td>Warning, reduced visibility</td>
            </tr>
            <tr>
              <td style="color: red;">Suspended</td>
              <td>&lt;3.5 rating, >10% cancellation</td>
              <td>Account suspended pending review</td>
            </tr>
          </table>
        `,
      },
      {
        id: "important-links",
        title: "Important Documents",
        content: `
          <h4>Required Reading</h4>
          <ul>
            <li>
              <a href="/el_mercado/seller-terms" target="_blank">
                📜 Terms & Conditions for Sellers
              </a>
              <p>Your agreement with El Mercado</p>
            </li>
            <li>
              <a href="/el_mercado/commission-policy" target="_blank">
                💰 Commission Policy
              </a>
              <p>Detailed breakdown of fees and commissions</p>
            </li>
          </ul>
          
          <h4>Support Resources</h4>
          <ul>
            <li><strong>Email:</strong> seller-support@cssknust.com</li>
            <li><strong>Response Time:</strong> Within 24-48 hours</li>
            <li><strong>Office Hours:</strong> Mon-Fri, 9 AM - 5 PM</li>
          </ul>
          
          <div class="tip-box">
            <strong>💡 Tip:</strong> Most common questions are answered in this guide. Check here first before contacting support!
          </div>
        `,
      },
    ],
  },
];

// FAQ data
const FAQ_DATA = [
  {
    question: "How long does it take to get approved as a seller?",
    answer: "Seller applications are typically reviewed within 2-5 business days. You'll receive an email notification once your application is processed. Make sure to submit all required documents to avoid delays.",
  },
  {
    question: "When will I receive my payment after a sale?",
    answer: "Funds move from pending to available balance once the order is marked as delivered and confirmed by the buyer (or after 7 days if buyer doesn't confirm). You can then request a payout, which takes 1-3 business days to process.",
  },
  {
    question: "Can I sell used items?",
    answer: "Yes! El Mercado supports P2P selling. Just make sure to accurately describe the condition (New, Like New, Good, Fair, or Used) and include photos showing any wear or defects.",
  },
  {
    question: "What happens if a buyer wants a refund?",
    answer: "Refund requests are handled through the platform. If approved, the amount is deducted from your pending or available balance. Commission is refunded for cancelled orders. Always try to resolve issues directly with the buyer first.",
  },
  {
    question: "How do I become a verified seller?",
    answer: "Verified status is earned by maintaining excellent service: 4.5+ star rating, low cancellation rate, fast response times, and consistent positive reviews. The verification badge is awarded automatically when you meet the criteria.",
  },
  {
    question: "Can I offer services instead of physical products?",
    answer: "Absolutely! Select 'Service' as your listing type. This is perfect for tutoring, design work, repairs, delivery services, and more. Service listings don't require inventory tracking.",
  },
  {
    question: "What if I need to take a break from selling?",
    answer: "Enable Vacation Mode in your profile settings. Your listings will be hidden, and buyers will see your vacation message. Remember to disable it when you're ready to resume!",
  },
  {
    question: "How are disputes resolved?",
    answer: "If you can't resolve an issue with a buyer directly, either party can open a dispute. Our team will review the case, including all messages and evidence, and make a fair decision within 5 business days.",
  },
];

// Color utilities
const getColorClasses = (color) => {
  const colors = {
    purple: { bg: "bg-purple-100", text: "text-purple-600", border: "border-purple-200", accent: "bg-purple-600" },
    blue: { bg: "bg-blue-100", text: "text-blue-600", border: "border-blue-200", accent: "bg-blue-600" },
    green: { bg: "bg-green-100", text: "text-green-600", border: "border-green-200", accent: "bg-green-600" },
    amber: { bg: "bg-amber-100", text: "text-amber-600", border: "border-amber-200", accent: "bg-amber-600" },
    yellow: { bg: "bg-yellow-100", text: "text-yellow-600", border: "border-yellow-200", accent: "bg-yellow-600" },
    indigo: { bg: "bg-indigo-100", text: "text-indigo-600", border: "border-indigo-200", accent: "bg-indigo-600" },
    emerald: { bg: "bg-emerald-100", text: "text-emerald-600", border: "border-emerald-200", accent: "bg-emerald-600" },
    red: { bg: "bg-red-100", text: "text-red-600", border: "border-red-200", accent: "bg-red-600" },
  };
  return colors[color] || colors.purple;
};

// Section Navigation Component
function SectionNav({ sections, activeSection, onSectionChange }) {
  return (
    <nav className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sticky top-24">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-purple-600" />
        Guide Contents
      </h3>
      <ul className="space-y-1">
        {sections.map((section) => {
          const colors = getColorClasses(section.color);
          const isActive = activeSection === section.id;
          return (
            <li key={section.id}>
              <button
                onClick={() => onSectionChange(section.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all flex items-center gap-2 text-sm ${
                  isActive
                    ? `${colors.bg} ${colors.text} font-medium`
                    : "hover:bg-gray-50 text-gray-600"
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.title}
              </button>
            </li>
          );
        })}
      </ul>
      
      {/* Quick Links */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-3">Quick Links</h4>
        <div className="space-y-2">
          <a
            href={`${API_BASE_URL}/seller-dashboard/`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
          >
            <ExternalLink className="w-4 h-4" />
            Seller Dashboard
          </a>
          <Link
            to="/el_mercado/seller-terms"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
          >
            <FileText className="w-4 h-4" />
            Terms & Conditions
          </Link>
          <Link
            to="/el_mercado/commission-policy"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
          >
            <Percent className="w-4 h-4" />
            Commission Policy
          </Link>
        </div>
      </div>
    </nav>
  );
}

// Section Content Component
function SectionContent({ section, expandedSubsection, onSubsectionToggle }) {
  const colors = getColorClasses(section.color);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      {/* Section Header */}
      <div className={`${colors.bg} rounded-xl p-6 border ${colors.border}`}>
        <div className="flex items-center gap-4">
          <div className={`${colors.accent} w-14 h-14 rounded-xl flex items-center justify-center`}>
            <section.icon className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{section.title}</h2>
            <p className="text-gray-600">{section.description}</p>
          </div>
        </div>
      </div>
      
      {/* Subsections */}
      <div className="space-y-4">
        {section.subsections.map((subsection) => {
          const isExpanded = expandedSubsection === subsection.id;
          return (
            <div
              key={subsection.id}
              className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
            >
              <button
                onClick={() => onSubsectionToggle(subsection.id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <h3 className="text-lg font-semibold text-gray-900">{subsection.title}</h3>
                <ChevronDown
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                />
              </button>
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div
                      className="px-6 pb-6 prose prose-sm max-w-none guide-content"
                      dangerouslySetInnerHTML={{ __html: subsection.content }}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

// FAQ Component
function FAQSection() {
  const [expandedFaq, setExpandedFaq] = useState(null);
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <HelpCircle className="w-6 h-6 text-purple-600" />
        Frequently Asked Questions
      </h3>
      <div className="space-y-3">
        {FAQ_DATA.map((faq, index) => {
          const isExpanded = expandedFaq === index;
          return (
            <div
              key={index}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpandedFaq(isExpanded ? null : index)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
              >
                <span className="font-medium text-gray-900">{faq.question}</span>
                <ChevronDown
                  className={`w-5 h-5 text-gray-400 flex-shrink-0 ml-2 transition-transform ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                />
              </button>
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <p className="px-4 pb-4 text-gray-600 text-sm">{faq.answer}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Main Seller Guide Page
export function SellerGuidePage() {
  const [activeSection, setActiveSection] = useState("getting-started");
  const [expandedSubsection, setExpandedSubsection] = useState("dashboard-overview");
  const [searchQuery, setSearchQuery] = useState("");
  
  const currentSection = useMemo(() => {
    return GUIDE_SECTIONS.find((s) => s.id === activeSection);
  }, [activeSection]);
  
  // Search functionality
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    
    const query = searchQuery.toLowerCase();
    const results = [];
    
    GUIDE_SECTIONS.forEach((section) => {
      section.subsections.forEach((subsection) => {
        if (
          subsection.title.toLowerCase().includes(query) ||
          subsection.content.toLowerCase().includes(query)
        ) {
          results.push({
            sectionId: section.id,
            sectionTitle: section.title,
            subsectionId: subsection.id,
            subsectionTitle: subsection.title,
          });
        }
      });
    });
    
    return results;
  }, [searchQuery]);
  
  const handleSectionChange = (sectionId) => {
    setActiveSection(sectionId);
    const section = GUIDE_SECTIONS.find((s) => s.id === sectionId);
    if (section && section.subsections.length > 0) {
      setExpandedSubsection(section.subsections[0].id);
    }
    setSearchQuery("");
  };
  
  const handleSubsectionToggle = (subsectionId) => {
    setExpandedSubsection(expandedSubsection === subsectionId ? null : subsectionId);
  };
  
  const handleSearchResultClick = (result) => {
    setActiveSection(result.sectionId);
    setExpandedSubsection(result.subsectionId);
    setSearchQuery("");
  };

  return (
    <>
      <Helmet>
        <title>Seller Guide | El Mercado - CSS KNUST</title>
        <meta
          name="description"
          content="Complete guide to selling on El Mercado. Learn how to manage your dashboard, create listings, handle orders, and grow your business."
        />
      </Helmet>

      {/* Custom styles for guide content */}
      <style>{`
        .guide-content h4 {
          font-size: 1rem;
          font-weight: 600;
          color: #1f2937;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
        }
        .guide-content h4:first-child {
          margin-top: 0;
        }
        .guide-content p {
          color: #4b5563;
          margin-bottom: 0.75rem;
        }
        .guide-content ul, .guide-content ol {
          margin-bottom: 1rem;
          padding-left: 1.5rem;
        }
        .guide-content li {
          color: #4b5563;
          margin-bottom: 0.5rem;
        }
        .guide-content strong {
          color: #1f2937;
        }
        .guide-content .code-block {
          background: #1f2937;
          border-radius: 0.5rem;
          padding: 1rem;
          margin: 1rem 0;
          overflow-x: auto;
        }
        .guide-content .code-block code {
          color: #e5e7eb;
          font-family: monospace;
          font-size: 0.875rem;
          white-space: pre-wrap;
        }
        .guide-content .tip-box {
          background: #ecfdf5;
          border: 1px solid #a7f3d0;
          border-radius: 0.5rem;
          padding: 1rem;
          margin: 1rem 0;
          color: #065f46;
        }
        .guide-content .warning-box {
          background: #fef3c7;
          border: 1px solid #fcd34d;
          border-radius: 0.5rem;
          padding: 1rem;
          margin: 1rem 0;
          color: #92400e;
        }
        .guide-content .info-table {
          width: 100%;
          border-collapse: collapse;
          margin: 1rem 0;
          font-size: 0.875rem;
        }
        .guide-content .info-table th,
        .guide-content .info-table td {
          border: 1px solid #e5e7eb;
          padding: 0.75rem;
          text-align: left;
        }
        .guide-content .info-table th {
          background: #f9fafb;
          font-weight: 600;
        }
        .guide-content .dont-list li {
          color: #dc2626;
        }
        .guide-content a {
          color: #7c3aed;
          text-decoration: underline;
        }
        .guide-content a:hover {
          color: #6d28d9;
        }
        .guide-content .workflow-steps {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 1rem;
          margin: 1rem 0;
        }
        .guide-content .workflow-steps .step {
          background: #f9fafb;
          border-radius: 0.5rem;
          padding: 1rem;
          text-align: center;
        }
        .guide-content .workflow-steps .step-num {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          background: #7c3aed;
          color: white;
          border-radius: 50%;
          font-size: 0.875rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
        }
        .guide-content .workflow-steps .step strong {
          display: block;
          margin-bottom: 0.25rem;
        }
        .guide-content .workflow-steps .step p {
          font-size: 0.75rem;
          margin: 0;
        }
        .guide-content .rating-guide {
          margin: 1rem 0;
        }
        .guide-content .rating-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.5rem 0;
        }
        .guide-content .rating-item .stars {
          color: #f59e0b;
          font-size: 1.25rem;
          min-width: 100px;
        }
      `}</style>

      <div className="min-h-screen bg-gray-50">
        <Navbar />

        <main className="pt-20 pb-16">
          {/* Hero Section */}
          <section className="bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-700 text-white py-12 px-4">
            <div className="max-w-7xl mx-auto">
              {/* Breadcrumb */}
              <div className="flex items-center gap-2 text-purple-200 text-sm mb-6">
                <Link to="/" className="hover:text-white">
                  <Home className="w-4 h-4" />
                </Link>
                <ChevronRight className="w-4 h-4" />
                <Link to="/el-mercado" className="hover:text-white">
                  El Mercado
                </Link>
                <ChevronRight className="w-4 h-4" />
                <span className="text-white">Seller Guide</span>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center max-w-3xl mx-auto"
              >
                <div className="flex items-center justify-center gap-3 mb-4">
                  <BookOpen className="w-10 h-10" />
                  <h1 className="text-3xl md:text-4xl font-bold">Seller Guide</h1>
                </div>
                <p className="text-lg text-purple-100 mb-8">
                  Everything you need to know to succeed as a seller on El Mercado. 
                  From setting up your store to growing your business.
                </p>
                
                {/* Search Bar */}
                <div className="relative max-w-xl mx-auto">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search the guide..."
                    className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-white placeholder-purple-200 focus:outline-none focus:ring-2 focus:ring-white/50"
                  />
                  
                  {/* Search Results Dropdown */}
                  {searchResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-50">
                      <div className="p-2">
                        {searchResults.slice(0, 6).map((result, index) => (
                          <button
                            key={index}
                            onClick={() => handleSearchResultClick(result)}
                            className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <p className="text-sm font-medium text-gray-900">
                              {result.subsectionTitle}
                            </p>
                            <p className="text-xs text-gray-500">
                              in {result.sectionTitle}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          </section>

          {/* Quick Stats */}
          <section className="max-w-7xl mx-auto px-4 -mt-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: Package, label: "Listing Types", value: "3", color: "blue" },
                { icon: Wallet, label: "Payout Methods", value: "2", color: "green" },
                { icon: Shield, label: "Verification Levels", value: "5", color: "purple" },
                { icon: Star, label: "Avg. Review Score", value: "4.5", color: "yellow" },
              ].map((stat, index) => {
                const colors = getColorClasses(stat.color);
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white rounded-xl shadow-lg p-4 flex items-center gap-3"
                  >
                    <div className={`${colors.bg} p-3 rounded-lg`}>
                      <stat.icon className={`w-6 h-6 ${colors.text}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                      <p className="text-sm text-gray-500">{stat.label}</p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </section>

          {/* Main Content */}
          <section className="max-w-7xl mx-auto px-4 py-12">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Sidebar Navigation */}
              <div className="lg:col-span-1">
                <SectionNav
                  sections={GUIDE_SECTIONS}
                  activeSection={activeSection}
                  onSectionChange={handleSectionChange}
                />
              </div>

              {/* Content Area */}
              <div className="lg:col-span-3 space-y-8">
                <AnimatePresence mode="wait">
                  {currentSection && (
                    <SectionContent
                      key={currentSection.id}
                      section={currentSection}
                      expandedSubsection={expandedSubsection}
                      onSubsectionToggle={handleSubsectionToggle}
                    />
                  )}
                </AnimatePresence>

                {/* FAQ Section */}
                <FAQSection />

                {/* Help CTA */}
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-8 text-white text-center">
                  <h3 className="text-2xl font-bold mb-2">Still Have Questions?</h3>
                  <p className="text-purple-100 mb-6">
                    Our support team is here to help you succeed as a seller.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link
                      to="/contact-us"
                      className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-colors"
                    >
                      <Mail className="w-5 h-5" />
                      Contact Support
                    </Link>
                    <a
                      href={`${API_BASE_URL}/seller-dashboard/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-purple-500 text-white rounded-lg font-semibold hover:bg-purple-400 transition-colors"
                    >
                      <Store className="w-5 h-5" />
                      Go to Dashboard
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>

        <Footer />
      </div>
    </>
  );
}

export default SellerGuidePage;
