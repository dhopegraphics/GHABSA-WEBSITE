"""
Single source of truth for BIO-CHEM branding across the backend.
Edit this file only for future rebrands.
"""
from decouple import config

BRAND_NAME = "BIO-CHEM"
BRAND_SHORT_LABEL_PROSE = "Biochem Society"
BRAND_FULL_NAME = "Biochemistry Society, KNUST"
BRAND_SITE_LABEL = "BIO-CHEM KNUST"  # replaces literal "CSS KNUST" in subjects/templates

FRONTEND_URL = config("FRONTEND_URL", default="https://biochemknust.com")
BACKEND_URL = config("BACKEND_URL", default="https://api.biochemknust.com")

EMAIL_INFO = config("BRAND_EMAIL_INFO", default="info@biochemknust.com")
EMAIL_ADMIN = config("BRAND_EMAIL_ADMIN", default="admin@biochemknust.com")
EMAIL_SUPPORT = config("BRAND_EMAIL_SUPPORT", default="support@biochemknust.com")
EMAIL_SELLER_SUPPORT = config("BRAND_EMAIL_SELLER_SUPPORT", default="seller-support@biochemknust.com")

UID_DOMAIN = config("BRAND_UID_DOMAIN", default="biochemknust.edu.gh")

LOGO_STATIC_PATH = "logos/logo.png"  # was logos/css.png

# Keep pointing at the EXISTING working Cloudinary asset until real BIO-CHEM
# artwork is re-uploaded under a biochem-knust/ folder — don't let the rename
# break live transactional email images.
EMAIL_HEADER_IMAGE_URL = config(
    "BRAND_EMAIL_HEADER_URL",
    default="https://res.cloudinary.com/dxmlwrxja/image/upload/v1766236154/css-knust/email-header.png",
)
EMAIL_FOOTER_IMAGE_URL = config(
    "BRAND_EMAIL_FOOTER_URL",
    default="https://res.cloudinary.com/dxmlwrxja/image/upload/v1766236155/css-knust/email-footer.png",
)

DEFAULT_EMAIL_SUBJECT = f"{BRAND_SITE_LABEL} Notification"
EMAIL_FOOTER_TEXT = f"This is an automated notification from {BRAND_SITE_LABEL}."
EMAIL_SIGNOFF = f"{BRAND_NAME} Team"

ICAL_PRODID = f"-//{BRAND_SITE_LABEL}//Calendar Sync//EN"

JAZZMIN_SITE_TITLE = f"{BRAND_NAME} Department Administration"
JAZZMIN_SITE_HEADER = f"{BRAND_NAME} Department Executives"
JAZZMIN_SITE_BRAND = f"{BRAND_NAME} Department"
JAZZMIN_COPYRIGHT = f"{BRAND_NAME} Department Execs"


def get_brand_context():
    """
    Merge into render_to_string() context dicts. Most branded templates render
    outside RequestContext (signal handlers, background threads, management
    commands), so a context processor alone can't reach them.
    """
    return {
        "brand_name": BRAND_NAME,
        "brand_full_name": BRAND_FULL_NAME,
        "brand_site_label": BRAND_SITE_LABEL,
        "frontend_url": FRONTEND_URL,
        "backend_url": BACKEND_URL,
        "email_header_url": EMAIL_HEADER_IMAGE_URL,
        "email_footer_url": EMAIL_FOOTER_IMAGE_URL,
        "email_footer_text": EMAIL_FOOTER_TEXT,
        "support_email": EMAIL_SUPPORT,
    }
