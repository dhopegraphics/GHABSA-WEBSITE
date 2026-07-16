// Single source of truth for all BIO-CHEM branding. Edit this file only.

export const BRAND = {
  shortName: "BIO-CHEM", // logo/proper-noun contexts
  shortLabel: "Biochem Society", // prose contexts, e.g. copyright line
  siteLabel: "BIO-CHEM KNUST", // <title>, email subjects
  fullName: "Biochemistry Society, KNUST",
  tagline:
    "Empowering students to explore, learn, and innovate in the world of biochemistry.",
};

export const DOMAIN = {
  root: "https://biochemknust.com",
};

export const EMAILS = {
  info: "info@biochemknust.com",
  admin: "admin@biochemknust.com",
  support: "support@biochemknust.com",
  sellerSupport: "seller-support@biochemknust.com",
};

export const SOCIAL = {
  twitter: "https://x.com/thebiochemknust",
  linkedin: "https://linkedin.com/in/thebiochemknust",
  instagram: "https://instagram.com/thebiochemknust",
  telegram: "https://t.me/thebiochemknust",
};

export const SEO_DEFAULTS = {
  siteName: BRAND.siteLabel,
  defaultTitle: `${BRAND.shortName} - KNUST`,
  defaultDescription: `${BRAND.fullName} — official student society site.`,
  ogImage: `${DOMAIN.root}/og-default.jpg`,
};

// Helper so per-page SEO/Helmet blocks don't hand-assemble title/og/twitter
// tags independently.
export function buildPageSEO({ title, description, path, image }) {
  const url = `${DOMAIN.root}${path}`;
  return {
    title: `${title} | ${BRAND.siteLabel}`,
    description,
    url,
    canonical: url,
    ogImage: image || SEO_DEFAULTS.ogImage,
  };
}

export const FINGERPRINT_SEED = "BIOCHEM-KNUST-Voting"; // was 'CSS-KNUST-Voting'

export default BRAND;
