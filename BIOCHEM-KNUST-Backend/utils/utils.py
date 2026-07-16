from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from random import sample
from string import ascii_uppercase, ascii_lowercase, digits
import httpx
import logging
import threading

from BioChemSystem.config.brand import get_brand_context

logger = logging.getLogger('sms')
email_logger = logging.getLogger('email')


# =====================
# MESSAGE PERSONALIZATION
# =====================

# Available placeholders for message personalization
MESSAGE_PLACEHOLDERS = {
    '{name}': 'First name',
    '{first_name}': 'First name',
    '{middle_name}': 'Middle name',
    '{last_name}': 'Last name',
    '{full_name}': 'Full name',
    '{phone}': 'Phone number',
    '{student_id}': 'Student ID',
    '{index_number}': 'Index number',
    '{personal_email}': 'Personal email',
    '{student_email}': 'Student email',
    '{program}': 'Program (CS/IT)',
    '{program_full}': 'Full program name',
    '{group}': 'Group (G1/G2)',
    '{group_full}': 'Full group name',
    '{year}': 'Year (1-4)',
    '{semester}': 'Current semester (1/2)',
    '{graduation_year}': 'Graduation year',
    '{gender}': 'Gender (M/F/O)',
    '{gender_full}': 'Full gender name',
}


def personalize_message(message, user):
    """
    Replace all placeholders in a message with user's actual data.
    
    Args:
        message: The message template containing placeholders like {name}, {student_id}, etc.
        user: CustomUser instance
    
    Returns:
        str: Personalized message with all placeholders replaced
    
    Available placeholders:
        {name}, {first_name} - First name
        {middle_name} - Middle name
        {last_name} - Last name  
        {full_name} - Full name (first + middle + last)
        {phone} - Phone number
        {student_id} - Student ID
        {index_number} - Index number
        {personal_email} - Personal email
        {student_email} - Student email
        {program} - Program code (CS/IT)
        {program_full} - Full program name
        {group} - Group code (G1/G2)
        {group_full} - Full group name
        {year} - Year (1-4)
        {semester} - Current semester (1/2)
        {graduation_year} - Graduation year
        {gender} - Gender code (M/F/O)
        {gender_full} - Full gender name
    """
    if not message or not user:
        return message
    
    # Check if message contains any placeholders to avoid unnecessary processing
    if '{' not in message:
        return message
    
    # Build full name
    full_name_parts = [user.first_name, user.middle_name, user.last_name]
    full_name = " ".join(part for part in full_name_parts if part).strip()
    
    # Get academic status safely
    try:
        academic_status = user.get_academic_status()
        year = str(academic_status.get('year', ''))
        semester = str(academic_status.get('semester', ''))
    except Exception:
        year = ''
        semester = ''
    
    # Define replacements with fallbacks
    replacements = {
        '{name}': user.first_name or 'there',
        '{first_name}': user.first_name or 'there',
        '{middle_name}': user.middle_name or '',
        '{last_name}': user.last_name or '',
        '{full_name}': full_name or 'there',
        '{phone}': str(user.phone) if user.phone else '',
        '{student_id}': user.student_id or 'N/A',
        '{index_number}': user.index_number or 'N/A',
        '{personal_email}': user.personal_email or 'N/A',
        '{student_email}': user.student_email or 'N/A',
        '{program}': user.program or 'N/A',
        '{program_full}': user.get_program_display_name() if hasattr(user, 'get_program_display_name') else (user.program or 'N/A'),
        '{group}': user.group or 'N/A',
        '{group_full}': user.get_group_display_name() if hasattr(user, 'get_group_display_name') else (user.group or 'N/A'),
        '{year}': year or 'N/A',
        '{semester}': semester or 'N/A',
        '{graduation_year}': str(user.graduation_year) if user.graduation_year else 'N/A',
        '{gender}': user.gender or 'N/A',
        '{gender_full}': user.get_gender_display_name() if hasattr(user, 'get_gender_display_name') else (user.gender or 'N/A'),
    }
    
    # Apply all replacements
    personalized = message
    for placeholder, value in replacements.items():
        if placeholder in personalized:
            personalized = personalized.replace(placeholder, str(value))
    
    return personalized


def message_has_placeholders(message):
    """
    Check if a message contains any personalization placeholders.
    
    Args:
        message: The message to check
    
    Returns:
        bool: True if message contains placeholders, False otherwise
    """
    if not message or '{' not in message:
        return False
    
    return any(placeholder in message for placeholder in MESSAGE_PLACEHOLDERS.keys())


def get_placeholder_help_text():
    """
    Get formatted help text showing all available placeholders.
    
    Returns:
        str: HTML formatted help text for admin interfaces
    """
    lines = ["<strong>Available Placeholders:</strong><br>"]
    for placeholder, description in MESSAGE_PLACEHOLDERS.items():
        lines.append(f"<code>{placeholder}</code> - {description}<br>")
    return "".join(lines)


def is_mobile(request):
    # check if user is trying to access the admin from mobile
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

    mobile_keywords = [
        "iphone",
        "android",
        "mobile",
        "blackberry",
        "windows phone",
    ]

    if any(keyword in user_agent for keyword in mobile_keywords):
        return True
    else:
        return False


def generate_code(max=4, reset_password=False):
    codes = digits
    code = sample(population=codes, k=max)
    return "".join(code)


def normalize_phone(number: str):
    """Normalize phone number to format 0XXXXXXXXX for MNotify SMS API
    
    Handles various input formats:
    - +233597959032 -> 0597959032
    - 233597959032 -> 0597959032  
    - 0597959032 -> 0597959032 (unchanged)
    """
    if not number:
        return number
        
    # Remove spaces and common separators
    valid_phone = number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Handle +233 format (13 characters: +233597959032)
    if valid_phone.startswith("+233") and len(valid_phone) == 13:
        return "0" + valid_phone[4:]  # Remove +233 and add 0
    
    # Handle 233 format without + (12 characters: 233597959032)
    elif valid_phone.startswith("233") and len(valid_phone) == 12:
        return "0" + valid_phone[3:]  # Remove 233 and add 0
    
    # Handle already normalized format (10 characters: 0597959032)
    elif valid_phone.startswith("0") and len(valid_phone) == 10:
        return valid_phone  # Already in correct format
    
    # Handle 9-digit local format (597959032)
    elif len(valid_phone) == 9 and valid_phone.isdigit():
        return "0" + valid_phone
    
    # Return as-is if format is unrecognized (with warning log)
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unrecognized phone number format: {number} (length: {len(valid_phone)})")
        return number


def send_sms_message(phone, template, context, is_otp=False, max_retries=3):
    """Send SMS via mnotify with automatic retry and return success status.
    Returns tuple: (success: bool, message: str)
    
    Args:
        phone: Recipient phone number
        template: Template file path
        context: Template context variables
        is_otp: If True, uses OTP type for better delivery (costs 0.035 extra per campaign)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Retry Strategy:
        - Immediate retry with exponential backoff (1s, 2s)
        - Stops immediately on success (no duplicate SMS)
        - Completes within 3-4 seconds for user experience
        - No background tasks (prevents stale OTP codes)
    """
    import time
    
    msg = render_to_string(template, context).strip()
    endpoint = f"https://api.mnotify.com/api/sms/quick?key={settings.SMS_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": [phone],
        "sender": settings.SENDER_ID,
        "message": msg,
    }
    
    # Add OTP type for verification codes (improves delivery)
    if is_otp:
        data["sms_type"] = "otp"

    last_error_msg = None
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            # Increased timeout for African network latency (Ghana SMS providers)
            with httpx.Client(timeout=30.0) as client:  # 30 seconds for reliability
                response = client.post(url=endpoint, headers=headers, json=data)
                response.raise_for_status()
                
                # Check mnotify response
                result = response.json()
                # Check for success indicators from Mnotify API
                if result.get("status") == "success" or result.get("code") in ["2000", 2000]:
                    campaign_id = result.get("summary", {}).get("_id", "unknown")
                    retry_info = f" (attempt {attempt + 1}/{max_retries})" if attempt > 0 else ""
                    logger.info(
                        f"SMS sent successfully{retry_info} to {phone} (Campaign: {campaign_id})", 
                        extra={'template': template, 'campaign_id': campaign_id, 'attempt': attempt + 1}
                    )
                    return (True, result.get("message", "SMS sent successfully"))
                else:
                    error_msg = result.get("message", result.get("summary", "SMS service unavailable"))
                    error_code = result.get("code", "unknown")
                    last_error_msg = error_msg
                    logger.warning(
                        f"SMS failed for {phone} (attempt {attempt + 1}/{max_retries}): {error_msg} (Code: {error_code})", 
                        extra={'template': template, 'error_code': error_code, 'full_response': result, 'attempt': attempt + 1}
                    )
                    
        except httpx.TimeoutException:
            last_error_msg = "SMS service timeout - please try again in a moment"
            logger.warning(
                f"SMS timeout for {phone} (attempt {attempt + 1}/{max_retries})", 
                extra={'template': template, 'error_type': 'timeout', 'attempt': attempt + 1}
            )
            
        except httpx.HTTPStatusError as e:
            last_error_msg = f"SMS service error (HTTP {e.response.status_code})"
            logger.warning(
                f"SMS HTTP error {e.response.status_code} for {phone} (attempt {attempt + 1}/{max_retries})", 
                extra={'template': template, 'status_code': e.response.status_code, 'error_type': 'http_status', 'attempt': attempt + 1}
            )
            
        except httpx.HTTPError as e:
            last_error_msg = f"SMS service error: {str(e)}"
            logger.warning(
                f"SMS HTTP error for {phone} (attempt {attempt + 1}/{max_retries}): {e}", 
                extra={'template': template, 'error_type': 'http_error', 'attempt': attempt + 1}
            )
            
        except Exception as e:
            last_error_msg = f"Failed to send SMS: {str(e)}"
            logger.warning(
                f"SMS exception for {phone} (attempt {attempt + 1}/{max_retries}): {e}", 
                exc_info=True, 
                extra={'template': template, 'error_type': 'exception', 'attempt': attempt + 1}
            )
        
        # Exponential backoff before retry (don't sleep after last attempt)
        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt  # 1s, 2s, 4s exponential backoff
            logger.info(f"Retrying SMS to {phone} in {sleep_time}s...")
            time.sleep(sleep_time)
    
    # All retries failed
    logger.error(
        f"SMS failed for {phone} after {max_retries} attempts. Last error: {last_error_msg}", 
        extra={'template': template, 'total_attempts': max_retries}
    )
    return (False, last_error_msg or "Failed to send SMS after multiple attempts")


def send_sms_async(phone, template, context, is_otp=False, callback=None):
    """
    Send SMS asynchronously in a background thread.
    Returns immediately so the user doesn't have to wait.
    
    Args:
        phone: Recipient phone number
        template: Template file path
        context: Template context variables
        is_otp: If True, uses OTP type for better delivery
        callback: Optional function to call with (success, message) after sending
    
    Returns:
        True (always - actual result comes via callback or logging)
    """
    def _send_in_background():
        try:
            success, message = send_sms_message_fast(phone, template, context, is_otp)
            if callback:
                try:
                    callback(success, message)
                except Exception as e:
                    logger.error(f"SMS callback error: {e}")
        except Exception as e:
            logger.error(f"Background SMS error for {phone}: {e}")
            if callback:
                try:
                    callback(False, str(e))
                except:
                    pass
    
    thread = threading.Thread(target=_send_in_background, daemon=True)
    thread.start()
    return True


def send_sms_message_fast(phone, template, context, is_otp=False):
    """
    Fast SMS sending without retries - for time-critical operations like registration.
    Single attempt with short timeout. Use send_sms_message for reliable delivery.
    
    Returns tuple: (success: bool, message: str)
    """
    msg = render_to_string(template, context).strip()
    endpoint = f"https://api.mnotify.com/api/sms/quick?key={settings.SMS_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": [phone],
        "sender": settings.SENDER_ID,
        "message": msg,
    }
    
    if is_otp:
        data["sms_type"] = "otp"

    try:
        # Short timeout for fast response - user experience priority
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url=endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success" or result.get("code") in ["2000", 2000]:
                campaign_id = result.get("summary", {}).get("_id", "unknown")
                logger.info(f"Fast SMS sent to {phone} (Campaign: {campaign_id})")
                return (True, "SMS sent successfully")
            else:
                error_msg = result.get("message", "SMS service unavailable")
                logger.warning(f"Fast SMS failed for {phone}: {error_msg}")
                return (False, error_msg)
                
    except httpx.TimeoutException:
        logger.warning(f"Fast SMS timeout for {phone}")
        return (False, "SMS service timeout")
    except Exception as e:
        logger.warning(f"Fast SMS error for {phone}: {e}")
        return (False, str(e))


def notify_user(phone, message, is_priority=False, max_retries=3):
    """Send SMS via MNotify with automatic retry and proper error handling.
    Returns tuple: (success: bool, message: str, campaign_id: str or None)
    
    Args:
        phone: Recipient phone number (should be in format 0XXXXXXXXX)
        message: SMS message content
        is_priority: If True, uses OTP type for faster delivery (costs 0.035 extra per SMS)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Retry Strategy:
        - Immediate retry with exponential backoff (1s, 2s)
        - Stops immediately on success (no duplicate SMS)
        - Completes within 3-4 seconds for user experience
        - No background tasks (prevents stale messages)
    """
    import time
    
    # Convert phone to string if it's a PhoneNumber object
    phone_str = str(phone) if phone else ""
    if not phone_str:
        return (False, "No phone number provided", None)
    
    # Normalize phone number to format MNotify expects (0XXXXXXXXX)
    normalized_phone = normalize_phone(phone_str)
    
    endpoint = f"https://api.mnotify.com/api/sms/quick?key={settings.SMS_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": [normalized_phone],
        "sender": settings.SENDER_ID,
        "message": message.strip(),
        "is_schedule": False,
        "schedule_date": "",
    }
    
    # Add OTP type for priority delivery (faster but costs 0.035 extra)
    if is_priority:
        data["sms_type"] = "otp"

    last_error_msg = None
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30.0) as client:  # 30 second timeout
                response = client.post(url=endpoint, headers=headers, json=data)
                response.raise_for_status()
                
                # Parse MNotify response
                result = response.json()
                
                # Check for success - MNotify returns status="success" and code="2000"
                if result.get("status") == "success" and str(result.get("code")) == "2000":
                    campaign_id = result.get("summary", {}).get("_id")
                    success_msg = result.get("message", "SMS sent successfully")
                    retry_info = f" (attempt {attempt + 1}/{max_retries})" if attempt > 0 else ""
                    logger.info(
                        f"Notification SMS sent{retry_info} to {normalized_phone} (Campaign: {campaign_id})",
                        extra={'campaign_id': campaign_id, 'attempt': attempt + 1, 'original_phone': phone_str}
                    )
                    return (True, success_msg, campaign_id)
                else:
                    # MNotify returned an error
                    error_msg = result.get("message", "Unknown error from SMS service")
                    last_error_msg = f"SMS failed: {error_msg}"
                    logger.warning(
                        f"Notification SMS failed for {normalized_phone} (attempt {attempt + 1}/{max_retries}): {error_msg}",
                        extra={'attempt': attempt + 1, 'response': result, 'original_phone': phone_str}
                    )
                    
        except httpx.TimeoutException:
            last_error_msg = "SMS service timeout - request took too long"
            logger.warning(
                f"Notification SMS timeout for {normalized_phone} (attempt {attempt + 1}/{max_retries})",
                extra={'attempt': attempt + 1, 'error_type': 'timeout'}
            )
            
        except httpx.HTTPStatusError as e:
            last_error_msg = f"SMS service error (HTTP {e.response.status_code})"
            logger.warning(
                f"Notification SMS HTTP error for {normalized_phone} (attempt {attempt + 1}/{max_retries}): HTTP {e.response.status_code}",
                extra={'attempt': attempt + 1, 'status_code': e.response.status_code}
            )
            
        except httpx.RequestError as e:
            last_error_msg = f"Network error: {str(e)}"
            logger.warning(
                f"Notification SMS network error for {normalized_phone} (attempt {attempt + 1}/{max_retries}): {e}",
                extra={'attempt': attempt + 1, 'error_type': 'network'}
            )
            
        except ValueError as e:
            last_error_msg = f"Invalid response from SMS service: {str(e)}"
            logger.warning(
                f"Notification SMS invalid response for {normalized_phone} (attempt {attempt + 1}/{max_retries}): {e}",
                extra={'attempt': attempt + 1, 'error_type': 'invalid_response'}
            )
            
        except Exception as e:
            last_error_msg = f"Unexpected error: {str(e)}"
            logger.warning(
                f"Notification SMS exception for {normalized_phone} (attempt {attempt + 1}/{max_retries}): {e}",
                exc_info=True,
                extra={'attempt': attempt + 1, 'error_type': 'exception'}
            )
        
        # Exponential backoff before retry (don't sleep after last attempt)
        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt  # 1s, 2s, 4s exponential backoff
            logger.info(f"Retrying notification SMS to {normalized_phone} in {sleep_time}s...")
            time.sleep(sleep_time)
    
    # All retries failed
    logger.error(
        f"Notification SMS failed for {normalized_phone} after {max_retries} attempts. Last error: {last_error_msg}",
        extra={'total_attempts': max_retries}
    )
    return (False, last_error_msg or "Failed to send SMS after multiple attempts", None)


def send_examination_schedule_message(students_phones, schedule_date, context):
    # end_point = "https://api.mnotify.com/api/sms/quick"
    # msg = render_to_string("exam_schedule_message.txt", context)
    # api_key = settings.SMS_API_KEY_V2
    # data = {
    #     "recipient[]": students_phones,
    #     "sender": settings.SENDER_ID,
    #     "message": msg,
    #     "is_schedule": True,
    #     "schedule_date": schedule_date,
    # }
    # url = end_point + "?key=" + api_key
    # response = requests.post(url, data)
    # data = response.json()
    # print(data)
    pass


# =====================
# EMAIL UTILITIES
# =====================

# Email rate limiting to prevent hitting provider limits
# PrivateEmail (Namecheap) allows 500 emails/hour on Starter plan
_email_send_times = []
EMAIL_RATE_LIMIT_PER_HOUR = 300  # Max emails per hour (more conservative)
EMAIL_RATE_LIMIT_PER_DAY = 2000  # Max emails per day
EMAIL_DELAY_BETWEEN_SENDS = 1.0  # Seconds between emails (increased to prevent connection issues)
EMAIL_BATCH_SIZE = 10  # Number of emails per connection (reduced for stability)


def _check_email_rate_limit():
    """
    Check if we're within email rate limits.
    Returns: (allowed: bool, wait_seconds: float, message: str)
    """
    import time
    from datetime import datetime, timedelta
    
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    
    # Clean up old entries
    global _email_send_times
    _email_send_times = [t for t in _email_send_times if t > one_day_ago]
    
    # Count emails in last hour and day
    emails_last_hour = sum(1 for t in _email_send_times if t > one_hour_ago)
    emails_last_day = len(_email_send_times)
    
    if emails_last_day >= EMAIL_RATE_LIMIT_PER_DAY:
        oldest_today = min(t for t in _email_send_times)
        wait_until = oldest_today + timedelta(days=1)
        wait_seconds = (wait_until - now).total_seconds()
        return (False, wait_seconds, f"Daily limit reached ({EMAIL_RATE_LIMIT_PER_DAY}/day). Reset in {wait_seconds/3600:.1f} hours.")
    
    if emails_last_hour >= EMAIL_RATE_LIMIT_PER_HOUR:
        oldest_hour = min(t for t in _email_send_times if t > one_hour_ago)
        wait_until = oldest_hour + timedelta(hours=1)
        wait_seconds = (wait_until - now).total_seconds()
        return (False, wait_seconds, f"Hourly limit reached ({EMAIL_RATE_LIMIT_PER_HOUR}/hour). Reset in {wait_seconds/60:.1f} minutes.")
    
    return (True, 0, "OK")


def _record_email_sent():
    """Record that an email was sent for rate limiting."""
    from datetime import datetime
    _email_send_times.append(datetime.now())


def get_email_rate_status():
    """
    Get current email rate limit status.
    Useful for admin dashboard to show remaining capacity.
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    
    # Clean and count
    recent = [t for t in _email_send_times if t > one_day_ago]
    emails_last_hour = sum(1 for t in recent if t > one_hour_ago)
    emails_last_day = len(recent)
    
    return {
        'emails_sent_last_hour': emails_last_hour,
        'emails_sent_last_day': emails_last_day,
        'remaining_this_hour': max(0, EMAIL_RATE_LIMIT_PER_HOUR - emails_last_hour),
        'remaining_today': max(0, EMAIL_RATE_LIMIT_PER_DAY - emails_last_day),
        'hourly_limit': EMAIL_RATE_LIMIT_PER_HOUR,
        'daily_limit': EMAIL_RATE_LIMIT_PER_DAY,
    }


def send_email_notification(
    recipient_email,
    subject,
    template_name=None,
    context=None,
    plain_text_message=None,
    html_message=None,
    from_email=None,
    max_retries=2
):
    """
    Send email notification with HTML and plain text support.
    Returns tuple: (success: bool, message: str)
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject line
        template_name: HTML template file path (optional)
        context: Template context variables (optional)
        plain_text_message: Plain text message (used if no template)
        html_message: Pre-rendered HTML message (used if no template)
        from_email: Sender email (defaults to EMAIL_HOST_USER)
        max_retries: Maximum retry attempts (default: 2)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import time
    
    if not recipient_email:
        return (False, "No recipient email provided")
    
    # Check rate limit before sending
    allowed, wait_seconds, rate_msg = _check_email_rate_limit()
    if not allowed:
        email_logger.warning(f"Email rate limit hit: {rate_msg}")
        return (False, f"Rate limit: {rate_msg}")
    
    # Validate email configuration
    if not getattr(settings, 'EMAIL_HOST', None):
        email_logger.warning("EMAIL_HOST not configured")
        return (False, "Email not configured: EMAIL_HOST missing")
    
    if not getattr(settings, 'EMAIL_HOST_USER', None):
        email_logger.warning("EMAIL_HOST_USER not configured")
        return (False, "Email not configured: EMAIL_HOST_USER missing")
    
    from_email = from_email or settings.EMAIL_HOST_USER
    
    # Build email content
    if template_name and context:
        try:
            full_context = {**get_brand_context(), **context}
            html_content = render_to_string(template_name, full_context)
            text_content = strip_tags(html_content)
        except Exception as e:
            email_logger.error(f"Failed to render email template {template_name}: {e}")
            return (False, f"Template error: {str(e)}")
    elif html_message:
        html_content = html_message
        text_content = strip_tags(html_message)
    elif plain_text_message:
        text_content = plain_text_message
        html_content = None
    else:
        return (False, "No message content provided")
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Create email with HTML and plain text alternatives
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            email.send(fail_silently=False)
            
            # Record successful send for rate limiting
            _record_email_sent()
            
            # Add delay between emails to prevent spam detection
            time.sleep(EMAIL_DELAY_BETWEEN_SENDS)
            
            retry_info = f" (attempt {attempt + 1}/{max_retries})" if attempt > 0 else ""
            email_logger.info(f"Email sent successfully{retry_info} to {recipient_email}")
            return (True, "Email sent successfully")
            
        except Exception as e:
            last_error = str(e)
            email_logger.warning(
                f"Email failed to {recipient_email} (attempt {attempt + 1}/{max_retries}): {e}"
            )
            
            # Exponential backoff before retry
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    email_logger.error(f"Email failed to {recipient_email} after {max_retries} attempts: {last_error}")
    return (False, last_error or "Failed to send email")


def send_email_async(recipient_email, subject, template_name=None, context=None, 
                     plain_text_message=None, html_message=None, callback=None):
    """
    Send email asynchronously in a background thread.
    Returns immediately so the user doesn't have to wait.
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject line
        template_name: HTML template file path (optional)
        context: Template context variables (optional)
        plain_text_message: Plain text message (optional)
        html_message: Pre-rendered HTML message (optional)
        callback: Optional function to call with (success, message) after sending
    
    Returns:
        True (always - actual result comes via callback or logging)
    """
    def _send_in_background():
        try:
            success, message = send_email_notification(
                recipient_email, subject, template_name, context,
                plain_text_message, html_message
            )
            if callback:
                try:
                    callback(success, message)
                except Exception as e:
                    email_logger.error(f"Email callback error: {e}")
        except Exception as e:
            email_logger.error(f"Background email error for {recipient_email}: {e}")
            if callback:
                try:
                    callback(False, str(e))
                except:
                    pass
    
    thread = threading.Thread(target=_send_in_background, daemon=True)
    thread.start()
    return True


def notify_user_email(email, message, subject=None, html_template=None, context=None):
    """
    Send email notification to a user - wrapper for NotifyUser model.
    Returns tuple: (success: bool, message: str)

    Args:
        email: Recipient email address
        message: Plain text message content
        subject: Email subject (default: settings.DEFAULT_EMAIL_SUBJECT)
        html_template: Optional HTML template path
        context: Template context for HTML template

    Returns:
        tuple: (success: bool, message: str)
    """
    subject = subject or settings.DEFAULT_EMAIL_SUBJECT

    if html_template and context:
        return send_email_notification(
            recipient_email=email,
            subject=subject,
            template_name=html_template,
            context=context
        )
    else:
        # Branded email template with header and footer images
        EMAIL_HEADER_URL = settings.EMAIL_HEADER_IMAGE_URL
        EMAIL_FOOTER_URL = settings.EMAIL_FOOTER_IMAGE_URL
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background: #f4f4f7;
                }}
                .email-wrapper {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                }}
                .header-image {{
                    margin-top: 50px;
                    width: 300px;
                    display: block;
                    margin: 20px auto;
                }}
                .content-container {{
                    padding: 30px 40px;
                }}
                .greeting {{
                    font-size: 16px;
                    color: #1e3a5f;
                    margin-bottom: 20px;
                }}
                .message-content {{
                    font-size: 15px;
                    line-height: 1.7;
                    color: #333333;
                    white-space: pre-line;
                    margin-bottom: 25px;
                }}
                .cta-button {{
                    display: inline-block;
                    background: #2563eb;
                    color: #ffffff !important;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 15px 0;
                }}
                .cta-button:hover {{
                    background: #1d4ed8;
                }}
                .divider {{
                    border: none;
                    border-top: 1px solid #e5e7eb;
                    margin: 25px 0;
                }}
                .footer-text {{
                    font-size: 12px;
                    color: #6b7280;
                    text-align: center;
                    padding: 0 40px 20px;
                }}
                .footer-image {{
                    width: 100%;
                    display: block;
                }}
                .social-links {{
                    text-align: center;
                    padding: 15px 0;
                }}
                .social-links a {{
                    color: #2563eb;
                    text-decoration: none;
                    margin: 0 10px;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <!-- Header Image -->
                <img src="{EMAIL_HEADER_URL}" alt="{settings.BRAND_SITE_LABEL}" class="header-image">

                <!-- Main Content -->
                <div class="content-container">
                    <div class="message-content">{message}</div>

                    <hr class="divider">

                    <div class="footer-text">
                        <p>{settings.EMAIL_FOOTER_TEXT}</p>
                        <p>If you have any questions, please contact us at <a href="mailto:{settings.EMAIL_INFO}" style="color: #2563eb;">{settings.EMAIL_INFO}</a></p>
                    </div>
                </div>

                <!-- Footer Image -->
                <img src="{EMAIL_FOOTER_URL}" alt="{settings.BRAND_SITE_LABEL} Footer" class="footer-image">
            </div>
        </body>
        </html>
        """
        return send_email_notification(
            recipient_email=email,
            subject=subject,
            plain_text_message=message,
            html_message=html_content
        )


# =====================
# BATCH EMAIL SYSTEM
# =====================

def get_branded_email_html(message):
    """
    Generate branded HTML email content with the current brand header/footer.
    """
    EMAIL_HEADER_URL = settings.EMAIL_HEADER_IMAGE_URL
    EMAIL_FOOTER_URL = settings.EMAIL_FOOTER_IMAGE_URL
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #333;
                margin: 0;
                padding: 0;
                background: #f4f4f7;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
            }}
            .header-image {{
                margin-top: 50px;
                width: 300px;
                display: block;
                margin: 20px auto;
            }}
            .content-container {{
                padding: 30px 40px;
            }}
            .message-content {{
                font-size: 15px;
                line-height: 1.7;
                color: #333333;
                white-space: pre-line;
                margin-bottom: 25px;
            }}
            .divider {{
                border: none;
                border-top: 1px solid #e5e7eb;
                margin: 25px 0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b7280;
                text-align: center;
                padding: 0 40px 20px;
            }}
            .footer-image {{
                width: 100%;
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <img src="{EMAIL_HEADER_URL}" alt="{settings.BRAND_SITE_LABEL}" class="header-image">
            <div class="content-container">
                <div class="message-content">{message}</div>
                <hr class="divider">
                <div class="footer-text">
                    <p>{settings.EMAIL_FOOTER_TEXT}</p>
                    <p>If you have any questions, please contact us at <a href="mailto:{settings.EMAIL_INFO}" style="color: #2563eb;">{settings.EMAIL_INFO}</a></p>
                </div>
            </div>
            <img src="{EMAIL_FOOTER_URL}" alt="{settings.BRAND_SITE_LABEL} Footer" class="footer-image">
        </div>
    </body>
    </html>
    """


def send_branded_email(subject, message, recipient_email, recipient_name=None, max_retries=2):
    """
    Send a branded email with the current brand's header and footer.
    
    Args:
        subject: Email subject line
        message: Message content (can include HTML)
        recipient_email: Recipient's email address
        recipient_name: Optional recipient name for personalization
        max_retries: Maximum retry attempts (default: 2)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import time
    
    if not recipient_email:
        return (False, "No recipient email provided")
    
    # Check rate limit
    allowed, wait_seconds, rate_msg = _check_email_rate_limit()
    if not allowed:
        email_logger.warning(f"Email rate limit hit: {rate_msg}")
        return (False, f"Rate limit: {rate_msg}")
    
    # Validate email configuration
    if not getattr(settings, 'EMAIL_HOST', None) or not getattr(settings, 'EMAIL_HOST_USER', None):
        email_logger.warning("Email not configured properly")
        return (False, "Email service not configured")
    
    from_email = settings.EMAIL_HOST_USER
    
    # Generate branded HTML
    html_content = get_branded_email_html(message)
    text_content = strip_tags(html_content)
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            # Record successful send
            _record_email_sent()
            
            # Add delay to prevent spam detection
            time.sleep(EMAIL_DELAY_BETWEEN_SENDS)
            
            email_logger.info(f"Branded email sent to {recipient_email}: {subject}")
            return (True, "Email sent successfully")
            
        except Exception as e:
            last_error = str(e)
            email_logger.warning(f"Email attempt {attempt + 1} failed to {recipient_email}: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    email_logger.error(f"Branded email failed to {recipient_email} after {max_retries} attempts: {last_error}")
    return (False, last_error or "Failed to send email")


def process_email_batch(batch_id, pause_check_callback=None):
    """
    Process a batch email send with connection reuse and proper tracking.
    
    Args:
        batch_id: ID of the EmailBatch to process
        pause_check_callback: Optional callable that returns True if batch should pause
    
    Returns:
        dict: Summary of the batch processing
    """
    import time
    from django.utils import timezone
    from django.core.mail import get_connection
    from core.models import EmailBatch, EmailBatchRecipient
    
    try:
        batch = EmailBatch.objects.get(id=batch_id)
    except EmailBatch.DoesNotExist:
        email_logger.error(f"Batch {batch_id} not found")
        return {"success": False, "error": "Batch not found"}
    
    # Update status to in_progress
    batch.status = "in_progress"
    if not batch.started_at:
        batch.started_at = timezone.now()
    batch.save(update_fields=["status", "started_at"])
    
    # Get pending recipients
    pending_recipients = batch.recipients.filter(status="pending").order_by("id")
    total_pending = pending_recipients.count()
    
    if total_pending == 0:
        batch.status = "completed"
        batch.completed_at = timezone.now()
        batch.save(update_fields=["status", "completed_at"])
        return {"success": True, "message": "No pending recipients", "processed": 0}
    
    email_logger.info(f"Starting batch {batch_id}: {total_pending} pending emails")
    
    # Check if message contains any personalization placeholders
    has_personalization = message_has_placeholders(batch.message)
    
    # If no personalization needed, prepare HTML content once for efficiency
    if not has_personalization:
        html_content = get_branded_email_html(batch.message)
        text_content = strip_tags(html_content)
    
    from_email = settings.EMAIL_HOST_USER
    
    processed = 0
    success_count = 0
    fail_count = 0
    batch_emails_in_connection = 0
    connection = None
    
    try:
        # Use select_related to fetch user data for personalization
        recipients_queryset = pending_recipients.select_related('user') if has_personalization else pending_recipients
        
        for recipient in recipients_queryset.iterator():
            # Check if we should pause
            if pause_check_callback and pause_check_callback():
                email_logger.info(f"Batch {batch_id} paused by callback")
                batch.status = "paused"
                batch.last_processed_at = timezone.now()
                batch.save(update_fields=["status", "last_processed_at"])
                break
            
            # Refresh batch status from DB (in case it was paused externally)
            batch.refresh_from_db()
            if batch.status == "paused":
                email_logger.info(f"Batch {batch_id} paused externally")
                break
            
            # Check rate limit
            allowed, wait_seconds, rate_msg = _check_email_rate_limit()
            if not allowed:
                email_logger.warning(f"Rate limit hit during batch {batch_id}: {rate_msg}")
                batch.status = "paused"
                batch.last_error = f"Rate limit: {rate_msg}"
                batch.last_processed_at = timezone.now()
                batch.save(update_fields=["status", "last_error", "last_processed_at"])
                break
            
            # Open new connection if needed (every EMAIL_BATCH_SIZE emails)
            if connection is None or batch_emails_in_connection >= EMAIL_BATCH_SIZE:
                if connection:
                    try:
                        connection.close()
                    except:
                        pass
                    # Longer pause between connection batches to avoid rate limiting
                    time.sleep(3.0)
                
                # Retry connection up to 3 times with exponential backoff
                connection_attempts = 0
                max_connection_attempts = 3
                connection = None
                
                while connection_attempts < max_connection_attempts:
                    try:
                        connection = get_connection()
                        connection.open()
                        batch_emails_in_connection = 0
                        email_logger.debug(f"Opened new SMTP connection for batch {batch_id} (attempt {connection_attempts + 1})")
                        break
                    except Exception as e:
                        connection_attempts += 1
                        wait_time = 5 * connection_attempts  # 5, 10, 15 seconds
                        email_logger.warning(f"SMTP connection attempt {connection_attempts} failed: {e}. Waiting {wait_time}s...")
                        
                        if connection_attempts < max_connection_attempts:
                            time.sleep(wait_time)
                        else:
                            email_logger.error(f"Failed to open SMTP connection after {max_connection_attempts} attempts")
                            # Mark remaining recipients as failed due to connection issue
                            recipient.status = "failed"
                            recipient.error_message = f"Connection error after {max_connection_attempts} attempts: {str(e)}"
                            recipient.retry_count += 1
                            recipient.save()
                            fail_count += 1
                            processed += 1
                            
                            # Pause batch if we can't connect
                            batch.status = "paused"
                            batch.last_error = f"SMTP connection failed: {str(e)}"
                            batch.save(update_fields=["status", "last_error"])
                            
                            # Close any partial connection
                            if connection:
                                try:
                                    connection.close()
                                except:
                                    pass
                            connection = None
                            break
                
                if connection is None:
                    # If we still don't have a connection after all retries, exit the loop
                    break
            
            # Personalize content if needed
            if has_personalization:
                # Use centralized personalization function for all placeholders
                personalized_message = personalize_message(batch.message, recipient.user)
                
                # Generate personalized HTML
                html_content = get_branded_email_html(personalized_message)
                text_content = strip_tags(html_content)
            
            # Send email with retry logic
            max_send_attempts = 2
            send_success = False
            
            for send_attempt in range(max_send_attempts):
                try:
                    email = EmailMultiAlternatives(
                        subject=batch.subject,
                        body=text_content,
                        from_email=from_email,
                        to=[recipient.email],
                        connection=connection
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send(fail_silently=False)
                    
                    # Success - record it
                    _record_email_sent()
                    recipient.status = "sent"
                    recipient.sent_at = timezone.now()
                    recipient.error_message = None
                    recipient.save()
                    
                    success_count += 1
                    batch_emails_in_connection += 1
                    send_success = True
                    
                    email_logger.debug(f"Email sent to {recipient.email} (batch {batch_id})")
                    
                    # Delay between emails
                    time.sleep(EMAIL_DELAY_BETWEEN_SENDS)
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # If connection error, try to reopen connection
                    if "connection" in error_msg.lower() or "closed" in error_msg.lower() or "unexpectedly" in error_msg.lower():
                        email_logger.warning(f"Connection error on attempt {send_attempt + 1}: {error_msg}")
                        try:
                            if connection:
                                connection.close()
                        except:
                            pass
                        
                        # Wait and try to reopen connection
                        time.sleep(5)
                        try:
                            connection = get_connection()
                            connection.open()
                            batch_emails_in_connection = 0
                            email_logger.info("Reopened SMTP connection after error")
                            continue  # Retry sending
                        except Exception as conn_err:
                            email_logger.error(f"Failed to reopen connection: {conn_err}")
                            connection = None
                    
                    # If not a connection error or final attempt, record failure
                    if send_attempt == max_send_attempts - 1 or "connection" not in error_msg.lower():
                        email_logger.warning(f"Failed to send to {recipient.email}: {error_msg}")
                        recipient.status = "failed"
                        recipient.error_message = error_msg
                        recipient.retry_count += 1
                        recipient.save()
                        fail_count += 1
                        break
            
            processed += 1
            
            # Update batch progress periodically (every 10 emails)
            if processed % 10 == 0:
                batch.sent_count = batch.recipients.filter(status="sent").count()
                batch.failed_count = batch.recipients.filter(status="failed").count()
                batch.last_processed_at = timezone.now()
                batch.save(update_fields=["sent_count", "failed_count", "last_processed_at"])
                email_logger.info(
                    f"Batch {batch_id} progress: {batch.sent_count}/{batch.total_recipients} sent, "
                    f"{batch.failed_count} failed"
                )
        
    finally:
        # Close connection
        if connection:
            try:
                connection.close()
            except:
                pass
    
    # Final update
    batch.sent_count = batch.recipients.filter(status="sent").count()
    batch.failed_count = batch.recipients.filter(status="failed").count()
    batch.skipped_count = batch.recipients.filter(status="skipped").count()
    batch.last_processed_at = timezone.now()
    
    # Check if complete
    pending_remaining = batch.recipients.filter(status="pending").count()
    if pending_remaining == 0:
        batch.status = "completed"
        batch.completed_at = timezone.now()
    elif batch.status == "in_progress":
        # Still in progress but loop ended - check why
        if batch.failed_count > batch.total_recipients * 0.5:
            batch.status = "failed"
            batch.last_error = "Too many failures (>50%)"
    
    batch.save()
    
    email_logger.info(
        f"Batch {batch_id} processing complete: {success_count} sent, {fail_count} failed, "
        f"{pending_remaining} pending. Status: {batch.status}"
    )
    
    return {
        "success": True,
        "batch_id": batch_id,
        "processed": processed,
        "sent": success_count,
        "failed": fail_count,
        "pending": pending_remaining,
        "status": batch.status
    }


def process_email_batch_async(batch_id):
    """
    Process batch email in background thread.
    """
    def _run():
        try:
            result = process_email_batch(batch_id)
            email_logger.info(f"Async batch {batch_id} completed: {result}")
        except Exception as e:
            email_logger.error(f"Async batch {batch_id} error: {e}", exc_info=True)
            # Update batch status to failed
            try:
                from core.models import EmailBatch
                batch = EmailBatch.objects.get(id=batch_id)
                batch.status = "failed"
                batch.last_error = str(e)
                batch.save(update_fields=["status", "last_error"])
            except:
                pass
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True


def create_email_batch(
    title,
    subject,
    message,
    recipients_queryset,
    created_by=None,
    filter_description="",
    channel="email",
    start_immediately=False
):
    """
    Create a new email batch from a queryset of users.
    
    Args:
        title: Internal name for the batch
        subject: Email subject line
        message: Email message content
        recipients_queryset: QuerySet of CustomUser objects
        created_by: User who created the batch (optional)
        filter_description: Description of filter used
        channel: Notification channel
        start_immediately: Whether to start processing immediately
    
    Returns:
        EmailBatch instance
    """
    from core.models import EmailBatch, EmailBatchRecipient
    
    # Create the batch
    batch = EmailBatch.objects.create(
        title=title,
        subject=subject,
        message=message,
        channel=channel,
        filter_description=filter_description,
        created_by=created_by,
        status="pending"
    )
    
    # Create recipient entries (only for users with personal email)
    recipients_created = 0
    for user in recipients_queryset:
        if user.personal_email:
            EmailBatchRecipient.objects.create(
                batch=batch,
                user=user,
                email=user.personal_email,
                status="pending"
            )
            recipients_created += 1
    
    # Update total count
    batch.total_recipients = recipients_created
    batch.save(update_fields=["total_recipients"])
    
    email_logger.info(
        f"Created email batch '{title}' with {recipients_created} recipients"
    )
    
    # Start processing if requested
    if start_immediately and recipients_created > 0:
        process_email_batch_async(batch.id)
    
    return batch


def get_batch_status(batch_id):
    """
    Get current status of an email batch.
    """
    from core.models import EmailBatch
    
    try:
        batch = EmailBatch.objects.get(id=batch_id)
        return {
            "id": batch.id,
            "title": batch.title,
            "status": batch.status,
            "total": batch.total_recipients,
            "sent": batch.sent_count,
            "failed": batch.failed_count,
            "skipped": batch.skipped_count,
            "pending": batch.pending_count,
            "progress": batch.progress_percentage,
            "can_resume": batch.can_resume,
            "can_pause": batch.can_pause,
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "last_error": batch.last_error,
        }
    except EmailBatch.DoesNotExist:
        return {"error": "Batch not found"}


def pause_email_batch(batch_id):
    """
    Pause an in-progress email batch.
    """
    from core.models import EmailBatch
    
    try:
        batch = EmailBatch.objects.get(id=batch_id)
        if batch.status == "in_progress":
            batch.status = "paused"
            batch.save(update_fields=["status"])
            return {"success": True, "message": "Batch paused"}
        return {"success": False, "message": f"Cannot pause batch with status: {batch.status}"}
    except EmailBatch.DoesNotExist:
        return {"success": False, "message": "Batch not found"}


def resume_email_batch(batch_id, async_mode=True):
    """
    Resume a paused or failed email batch.
    """
    from core.models import EmailBatch
    
    try:
        batch = EmailBatch.objects.get(id=batch_id)
        if not batch.can_resume:
            return {"success": False, "message": f"Cannot resume batch with status: {batch.status}"}
        
        if async_mode:
            process_email_batch_async(batch_id)
            return {"success": True, "message": "Batch resuming in background"}
        else:
            return process_email_batch(batch_id)
    except EmailBatch.DoesNotExist:
        return {"success": False, "message": "Batch not found"}


def cancel_email_batch(batch_id):
    """
    Cancel an email batch and mark all pending recipients as skipped.
    """
    from core.models import EmailBatch
    
    try:
        batch = EmailBatch.objects.get(id=batch_id)
        if batch.status in ["completed", "cancelled"]:
            return {"success": False, "message": f"Cannot cancel batch with status: {batch.status}"}
        
        # Mark pending recipients as skipped
        batch.recipients.filter(status="pending").update(status="skipped")
        
        # Update batch
        batch.status = "cancelled"
        batch.update_counts()
        batch.save(update_fields=["status"])
        
        return {"success": True, "message": "Batch cancelled"}
    except EmailBatch.DoesNotExist:
        return {"success": False, "message": "Batch not found"}

