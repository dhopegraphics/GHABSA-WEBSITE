from utils.utils import notify_user, notify_user_email, personalize_message, message_has_placeholders
from django.db import models
from accounts.models import CustomUser
from phonenumber_field.modelfields import PhoneNumberField
import logging

logger = logging.getLogger(__name__)

# Create your models here.
action = [("send", "send"), ("draft", "draft"), ("sent", "sent")]

NOTIFICATION_CHANNEL_CHOICES = [
    ("sms", "SMS"),
    ("push", "Push Notification"),
    ("email", "Email"),
    ("both", "SMS & Push Notification"),
    ("sms_email", "SMS & Email"),
    ("push_email", "Push & Email"),
    ("all", "SMS, Push & Email"),
]


class NotifyUser(models.Model):
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Notification title (used for push notifications and email subject)"
    )
    message = models.TextField(
        help_text="Message for the user. Available placeholders: {name}, {full_name}, {phone}, {student_id}, "
                  "{index_number}, {personal_email}, {student_email}, {program}, {program_full}, {group}, "
                  "{year}, {semester}, {graduation_year}, {gender}"
    )
    channel = models.CharField(
        max_length=15,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        default="sms",
        help_text="Choose how to send the notification"
    )
    push_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data for push notification (e.g., screen to navigate to)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(choices=action, default="draft", max_length=255)
    sent = models.BooleanField(default=False, editable=False)
    sms_sent = models.BooleanField(default=False, editable=False)
    push_sent = models.BooleanField(default=False, editable=False)
    email_sent = models.BooleanField(default=False, editable=False)
    sms_campaign_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        help_text="MNotify campaign ID for tracking"
    )
    sms_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="SMS error message if sending failed"
    )
    push_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="Push notification error message if sending failed"
    )
    email_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="Email error message if sending failed"
    )
    retry_count = models.IntegerField(
        default=0,
        editable=False,
        help_text="Number of send attempts"
    )
    is_priority = models.BooleanField(
        default=False,
        help_text="Use priority delivery (OTP type - faster but costs 0.035 extra per SMS)"
    )
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.action.lower() == "send" and self.action.lower() != "sent":
            self.retry_count += 1
            
            # Personalize message if it contains placeholders (at send time for admin-created notifications)
            # Note: Bulk notifications are already personalized before saving
            actual_message = self.message
            if message_has_placeholders(self.message):
                actual_message = personalize_message(self.message, self.recipient)
            
            # Determine which channels to use
            send_sms = self.channel in ["sms", "both", "sms_email", "all"]
            send_push = self.channel in ["push", "both", "push_email", "all"]
            send_email = self.channel in ["email", "sms_email", "push_email", "all"]
            
            # Send SMS if required
            if send_sms:
                try:
                    success, message, campaign_id = notify_user(
                        str(self.recipient.phone), 
                        actual_message,
                        is_priority=self.is_priority
                    )
                    
                    if success:
                        self.sms_sent = True
                        self.sms_campaign_id = campaign_id
                        self.sms_error = None  # Clear any previous errors
                        priority_flag = "PRIORITY" if self.is_priority else ""
                        logger.info(f"SMS sent successfully {priority_flag} to {self.recipient.phone} (Campaign: {campaign_id})")
                    else:
                        self.sms_sent = False
                        self.sms_error = message
                        logger.error(f"SMS failed for {self.recipient.phone}: {message}")
                        
                except Exception as e:
                    self.sms_sent = False
                    self.sms_error = f"Exception: {str(e)}"
                    logger.error(f"SMS exception for {self.recipient.phone}: {str(e)}", exc_info=True)
            
            # Send Push Notification if required
            if send_push:
                try:
                    from notifications.services import PushNotificationService
                    
                    result = PushNotificationService.send_to_user(
                        user=self.recipient,
                        title=self.title or "Notification",
                        body=actual_message,
                        data=self.push_data,
                    )
                    
                    if result.get('success'):
                        self.push_sent = True
                        self.push_error = None  # Clear any previous errors
                        logger.info(f"Push notification sent to {self.recipient.username}")
                    else:
                        self.push_sent = False
                        self.push_error = result.get('message', 'Unknown error')
                        logger.error(f"Push notification failed for {self.recipient.username}: {result.get('message')}")
                        
                except Exception as e:
                    self.push_sent = False
                    self.push_error = f"Exception: {str(e)}"
                    logger.error(f"Push notification exception for {self.recipient.username}: {str(e)}", exc_info=True)
            
            # Send Email if required
            if send_email:
                try:
                    # Only send to personal email
                    # Note: Student emails (@st.knust.edu.gh) reject external emails due to Microsoft 365 policies
                    recipient_email = self.recipient.personal_email
                    
                    if recipient_email:
                        success, message = notify_user_email(
                            email=recipient_email,
                            message=actual_message,
                            subject=self.title
                        )
                        
                        if success:
                            self.email_sent = True
                            self.email_error = None
                            logger.info(f"Email sent to {recipient_email}")
                        else:
                            self.email_sent = False
                            self.email_error = f"{recipient_email}: {message}"
                            logger.error(f"Email failed for {recipient_email}: {message}")
                    else:
                        self.email_sent = False
                        self.email_error = "No personal email available for recipient"
                        logger.warning(f"No personal email for {self.recipient.username}")
                        
                except Exception as e:
                    self.email_sent = False
                    self.email_error = f"Exception: {str(e)}"
                    logger.error(f"Email exception for {self.recipient.username}: {str(e)}", exc_info=True)
            
            # Update status
            self.action = "sent"
            self.sent = self.sms_sent or self.push_sent or self.email_sent  # Mark as sent if at least one succeeded
            
            # Log final status
            if not self.sent:
                logger.error(f"WARNING: Notification #{self.pk} failed completely. SMS: {self.sms_error}, Push: {self.push_error}, Email: {self.email_error}")
        
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "notify_user"
        verbose_name = "Notify User"
        verbose_name_plural = "Notify User"


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    phone = PhoneNumberField(null=True)
    message = models.TextField()
    created_at = models.DateTimeField(verbose_name="Sent on", auto_now_add=True)

    class Meta:
        verbose_name = "Reported Issue"
        verbose_name_plural = "Reported Issues"


# =====================
# BATCH EMAIL SYSTEM
# =====================

BATCH_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("paused", "Paused"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("failed", "Failed"),
]

RECIPIENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("sent", "Sent"),
    ("failed", "Failed"),
    ("skipped", "Skipped"),
]


class EmailBatch(models.Model):
    """
    Tracks batch email sends with progress and resume capability.
    """
    title = models.CharField(
        max_length=200,
        help_text="Internal name for this batch (e.g., 'Welcome Emails - Jan 2025')"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Email subject line"
    )
    message = models.TextField(
        help_text="Email message content. Available placeholders: {name}, {full_name}, {phone}, {student_id}, "
                  "{index_number}, {personal_email}, {student_email}, {program}, {program_full}, {group}, "
                  "{year}, {semester}, {graduation_year}, {gender}"
    )
    channel = models.CharField(
        max_length=15,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        default="email",
        help_text="Notification channel (only email-related channels are processed)"
    )
    filter_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Description of filter used to select recipients"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=BATCH_STATUS_CHOICES,
        default="pending"
    )
    
    # Counts
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_email_batches'
    )
    
    # Error tracking
    last_error = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = "email_batch"
        verbose_name = "Email Batch"
        verbose_name_plural = "Email Batches"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.title} ({self.status}) - {self.sent_count}/{self.total_recipients}"
    
    @property
    def progress_percentage(self):
        if self.total_recipients == 0:
            return 0
        return round((self.sent_count + self.failed_count + self.skipped_count) / self.total_recipients * 100, 1)
    
    @property
    def pending_count(self):
        return self.total_recipients - self.sent_count - self.failed_count - self.skipped_count
    
    @property
    def can_resume(self):
        return self.status in ["paused", "failed"] and self.pending_count > 0
    
    @property
    def can_pause(self):
        return self.status == "in_progress"
    
    def update_counts(self):
        """Update counts from recipient records."""
        from django.db.models import Count
        stats = self.recipients.values('status').annotate(count=Count('id'))
        
        for stat in stats:
            if stat['status'] == 'sent':
                self.sent_count = stat['count']
            elif stat['status'] == 'failed':
                self.failed_count = stat['count']
            elif stat['status'] == 'skipped':
                self.skipped_count = stat['count']
        
        self.save(update_fields=['sent_count', 'failed_count', 'skipped_count'])


class EmailBatchRecipient(models.Model):
    """
    Tracks individual recipients within a batch email send.
    """
    batch = models.ForeignKey(
        EmailBatch,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_batch_entries'
    )
    email = models.EmailField(
        help_text="Email address used for this send"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=RECIPIENT_STATUS_CHOICES,
        default="pending"
    )
    
    # Timing
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = "email_batch_recipient"
        verbose_name = "Batch Email Recipient"
        verbose_name_plural = "Batch Email Recipients"
        ordering = ["id"]
        unique_together = [["batch", "user", "email"]]  # Prevent duplicate entries
    
    def __str__(self):
        return f"{self.email} - {self.status}"
