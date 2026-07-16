from django.contrib import admin
from events.models import (
    Event, EventRSVP, EventRegistration, TeamMember,
    SyncMemoAlbum, SyncMemoPhoto, SyncMemoComment, SyncMemoLike,
    EventPaymentPackage, EventPaymentTransaction, EventPaymentRefund
)
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q, Sum, Case, When, Value, IntegerField
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixins for models with file fields
EventMediaAdminMixin = make_media_admin_mixin(['event_image_1', 'event_image_2'])
SyncMemoAlbumMediaAdminMixin = make_media_admin_mixin(['cover_photo'])
SyncMemoPhotoMediaAdminMixin = make_media_admin_mixin(['photo'])

# Register your models here.


@admin.register(Event)
class EventAdmin(EventMediaAdminMixin, admin.ModelAdmin):
    list_filter = ["organised_by", "event_date", "event_type", "location_type", "featured", "requires_payment"]
    search_fields = ["event_name", "description", "organised_by", "venue"]
    date_hierarchy = "event_date"
    # Set default ordering to event_date ascending (nearest first)
    ordering = ['event_date']
    
    list_display = [
        "event_name", 
        "_event_img", 
        "organised_by",
        "event_type",
        "location_type",
        "event_date",
        "event_end_date",
        "_event_status",
        "_payment_info",
        "_attendee_count",
        "_has_gallery",
        "featured",
    ]
    
    def get_changelist_instance(self, request):
        """
        Custom ordering: Upcoming events first (nearest date first), 
        then past events, then events with no date at bottom.
        Applied AFTER changelist is created to ensure it takes effect.
        """
        cl = super().get_changelist_instance(request)
        
        # Only apply custom ordering if user hasn't clicked a column header to sort
        if not request.GET.get('o'):
            now = timezone.now()
            
            # Sort priority:
            # 0 = upcoming events (event_date >= now)
            # 1 = past events (event_date < now) 
            # 2 = no date (event_date is NULL)
            cl.queryset = cl.queryset.annotate(
                _sort_priority=Case(
                    When(event_date__isnull=True, then=Value(2)),  # No date at bottom
                    When(event_date__gte=now, then=Value(0)),      # Upcoming first
                    default=Value(1),                              # Past events
                    output_field=IntegerField(),
                )
            ).order_by('_sort_priority', 'event_date')
        
        return cl
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("event_name", "description", "organised_by", "emoji", "featured")
        }),
        ("Event Type & Category", {
            "fields": ("event_type",),
            "description": "Categorize your event for mobile app filtering"
        }),
        ("Dates", {
            "fields": ("event_date", "event_end_date"),
            "description": "Set event_end_date for multi-day events. Leave blank for single-day events."
        }),
        ("Location", {
            "fields": ("location_type", "venue", "building", "virtual_link"),
            "description": "Physical location or virtual meeting link"
        }),
        ("Media", {
            "fields": (
                ("event_image_1", "event_image_1_url"),
                ("event_image_2", "event_image_2_url"),
                "media_link"
            ),
            "description": "Upload images OR provide Google Drive/Dropbox links via URL fields. Add gallery link for event photos/videos"
        }),
        ("Registration Settings", {
            "fields": (
                "registration_link",
                "requires_registration",
                "max_attendees",
                "registration_deadline",
                "allows_team_registration",
                "min_team_size",
                "max_team_size",
            ),
            "description": "External registration link OR internal registration settings (not both)"
        }),
        ("💳 Payment Settings", {
            "fields": (
                "requires_payment",
                "payment_description",
                "early_bird_deadline",
                "payment_deadline",
                "allow_partial_payment",
                "minimum_deposit_percentage",
            ),
            "description": "Enable if this event requires payment. Create packages in 'Event Payment Packages' after saving.",
            "classes": ("collapse",),
        }),
        ("RSVP & Features", {
            "fields": ("allows_rsvp", "sync_memo_enabled"),
        }),
    )
    
    actions = ["mark_as_past_event", "mark_as_upcoming_event", "add_end_date_today", "enable_sync_memo", "enable_payment"]

    def _event_img(self, obj):
        if obj.event_image_1:
            return format_html(
                '<a href={}><img src="{}" width="50" height="50" style="border-radius: 4px;" /></a>',
                obj.event_image_1.url,
                obj.event_image_1.url,
            )
        return "-"
    _event_img.short_description = "Image"

    def _event_status(self, obj):
        """Display event status with colored badge"""
        now = timezone.now()
        
        if not obj.event_date:
            return format_html('<span style="color: gray;">❓ Unknown</span>')
        
        # Determine status
        if obj.event_end_date:
            if now < obj.event_date:
                status = "upcoming"
                color = "blue"
                icon = "📅"
            elif obj.event_date <= now <= obj.event_end_date:
                status = "ongoing"
                color = "green"
                icon = "🟢"
            else:
                status = "past"
                color = "gray"
                icon = "✓"
        else:
            event_day_start = obj.event_date.replace(hour=0, minute=0, second=0, microsecond=0)
            event_day_end = obj.event_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if now < event_day_start:
                status = "upcoming"
                color = "blue"
                icon = "📅"
            elif event_day_start <= now <= event_day_end:
                status = "ongoing"
                color = "green"
                icon = "🟢"
            else:
                status = "past"
                color = "gray"
                icon = "✓"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            status.capitalize()
        )
    _event_status.short_description = "Status"
    
    def _attendee_count(self, obj):
        """Display attendee count"""
        count = obj.attendee_count
        max_count = obj.max_attendees
        
        if max_count:
            percentage = (count / max_count) * 100
            if percentage >= 90:
                color = "red"
            elif percentage >= 70:
                color = "orange"
            else:
                color = "green"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{}</span>',
                color, count, max_count
            )
        return format_html('<span>{}</span>', count)
    _attendee_count.short_description = "Attendees"
    
    def _payment_info(self, obj):
        """Display payment status"""
        if not obj.requires_payment:
            return format_html('<span style="color: gray;">Free</span>')
        
        packages = obj.payment_packages.filter(is_active=True)
        if not packages.exists():
            return format_html('<span style="color: orange;">💳 No Packages</span>')
        
        lowest_price = obj.lowest_package_price
        total_revenue = obj.total_revenue
        paid_count = obj.paid_registrations_count
        
        return format_html(
            '<span style="color: green; font-weight: bold;">💳 GHS {} • {} paid (GHS {})</span>',
            lowest_price, paid_count, total_revenue
        )
    _payment_info.short_description = "Payment"

    def _has_gallery(self, obj):
        """Show if event has a gallery link"""
        if obj.media_link:
            return format_html(
                '<a href="{}" target="_blank" style="color: purple;">🖼️ Gallery</a>',
                obj.media_link
            )
        return "-"
    _has_gallery.short_description = "Gallery"

    # Bulk Actions
    def mark_as_past_event(self, request, queryset):
        """Mark selected events as past by setting end_date to yesterday"""
        yesterday = timezone.now() - timezone.timedelta(days=1)
        updated = queryset.update(event_end_date=yesterday)
        self.message_user(request, f"{updated} event(s) marked as past.")
    mark_as_past_event.short_description = "✓ Mark selected events as PAST"

    def mark_as_upcoming_event(self, request, queryset):
        """Mark selected events as upcoming by setting date to future"""
        next_week = timezone.now() + timezone.timedelta(days=7)
        updated = queryset.update(event_date=next_week, event_end_date=None)
        self.message_user(request, f"{updated} event(s) marked as upcoming (1 week from now).")
    mark_as_upcoming_event.short_description = "📅 Mark selected events as UPCOMING"

    def add_end_date_today(self, request, queryset):
        """Set end_date to today for selected events (makes them past if event_date is also past)"""
        today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        updated = queryset.update(event_end_date=today_end)
        self.message_user(request, f"{updated} event(s) end date set to today.")
    add_end_date_today.short_description = "⏰ Set end date to TODAY"
    
    def enable_sync_memo(self, request, queryset):
        """Enable Sync Memo (photo gallery) for selected events"""
        updated = queryset.update(sync_memo_enabled=True)
        self.message_user(request, f"Sync Memo enabled for {updated} event(s).")
    enable_sync_memo.short_description = "📸 Enable Sync Memo (Photo Gallery)"
    
    def enable_payment(self, request, queryset):
        """Enable payment requirement for selected events"""
        updated = queryset.update(requires_payment=True, requires_registration=True)
        self.message_user(request, f"Payment enabled for {updated} event(s). Don't forget to create payment packages!")
    enable_payment.short_description = "💳 Enable Payment Requirement"


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ["event", "user", "status", "reminder", "created_at"]
    list_filter = ["status", "reminder", "event"]
    search_fields = ["event__event_name", "user__username", "user__personal_email", "user__student_email"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    
    fieldsets = (
        ("RSVP Information", {
            "fields": ("event", "user", "status")
        }),
        ("Preferences", {
            "fields": ("reminder", "notes")
        }),
    )
    
    readonly_fields = ["created_at", "updated_at"]


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1
    fields = ["full_name", "email", "phone", "student_id", "year_group", "program", "role"]


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "registration_number", "full_name", "event", "status", "payment_status",
        "_payment_progress", "email", "team_name",
        "is_team_leader", "checked_in", "created_at"
    ]
    list_filter = ["status", "payment_status", "checked_in", "is_team_leader", "event"]
    search_fields = [
        "full_name", "email", "student_id", "team_name",
        "event__event_name", "user__username", "registration_number"
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    inlines = [TeamMemberInline]
    
    fieldsets = (
        ("Registration Information", {
            "fields": ("registration_number", "event", "user", "status")
        }),
        ("💳 Payment Information", {
            "fields": (
                "payment_package", "payment_status",
                ("amount_due", "amount_paid"),
                "payment_completed_at",
            ),
            "description": "Payment details for paid events"
        }),
        ("Personal Details", {
            "fields": (
                "full_name", "email", "phone", "student_id",
                "year_group", "program"
            )
        }),
        ("Team Information", {
            "fields": ("is_team_leader", "team_name")
        }),
        ("Additional Information", {
            "fields": ("dietary_restrictions", "special_requirements", "notes", "admin_notes")
        }),
        ("Check-in", {
            "fields": ("checked_in", "checked_in_at")
        }),
    )
    
    readonly_fields = ["registration_number", "created_at", "updated_at", "payment_completed_at"]
    
    actions = ["mark_as_confirmed", "mark_as_checked_in", "mark_payment_as_paid", "send_payment_reminder"]
    
    def _payment_progress(self, obj):
        """Display payment progress"""
        if obj.payment_status == 'not_required':
            return format_html('<span style="color: gray;">N/A</span>')
        
        if obj.amount_due == 0:
            return format_html('<span style="color: gray;">-</span>')
        
        percentage = obj.payment_percentage
        paid = obj.amount_paid
        due = obj.amount_due
        
        if percentage >= 100:
            color = "green"
            icon = "✓"
        elif percentage > 0:
            color = "orange"
            icon = "⏳"
        else:
            color = "red"
            icon = "⚠"
        
        return format_html(
            '<span style="color: {};">{} GHS {}/{} ({}%)</span>',
            color, icon, paid, due, percentage
        )
    _payment_progress.short_description = "Payment Progress"
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} registration(s) confirmed.")
    mark_as_confirmed.short_description = "✓ Confirm selected registrations"
    
    def mark_as_checked_in(self, request, queryset):
        updated = queryset.update(checked_in=True, checked_in_at=timezone.now())
        self.message_user(request, f"{updated} attendee(s) checked in.")
    mark_as_checked_in.short_description = "✓ Check in selected attendees"
    
    def mark_payment_as_paid(self, request, queryset):
        """Mark selected registrations as fully paid (manual payment)"""
        for registration in queryset:
            registration.amount_paid = registration.amount_due
            registration.payment_status = 'paid'
            registration.payment_completed_at = timezone.now()
            if registration.status == 'pending_payment':
                registration.status = 'confirmed'
            registration.save()
        self.message_user(request, f"{queryset.count()} registration(s) marked as paid.")
    mark_payment_as_paid.short_description = "💳 Mark as Fully Paid (Manual)"
    
    def send_payment_reminder(self, request, queryset):
        """Send payment reminder to selected registrations with pending payment"""
        pending = queryset.filter(payment_status__in=['pending', 'partial'])
        count = pending.count()
        # TODO: Implement actual email sending
        self.message_user(request, f"Payment reminder queued for {count} registration(s).")
    send_payment_reminder.short_description = "📧 Send Payment Reminder"


@admin.register(SyncMemoAlbum)
class SyncMemoAlbumAdmin(SyncMemoAlbumMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        "title", "event", "status", "_photo_count",
        "_contributor_count", "allow_uploads", "created_at"
    ]
    list_filter = ["status", "allow_uploads", "allow_comments", "require_approval"]
    search_fields = ["title", "event__event_name"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    
    fieldsets = (
        ("Album Information", {
            "fields": ("event", "title", "description", "status", ("cover_photo", "cover_photo_url")),
            "description": "Upload cover photo OR provide Google Drive/Dropbox link"
        }),
        ("Settings", {
            "fields": ("allow_uploads", "allow_comments", "require_approval")
        }),
    )
    
    readonly_fields = ["created_at", "updated_at"]
    
    def _photo_count(self, obj):
        return obj.photo_count
    _photo_count.short_description = "Photos"
    
    def _contributor_count(self, obj):
        return obj.contributor_count
    _contributor_count.short_description = "Contributors"


@admin.register(SyncMemoPhoto)
class SyncMemoPhotoAdmin(SyncMemoPhotoMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        "_thumbnail", "album", "uploaded_by", "_like_count",
        "_comment_count", "is_approved", "created_at"
    ]
    list_filter = ["is_approved", "share_to_feed", "album__event"]
    search_fields = ["caption", "uploaded_by__username", "album__title"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    
    fieldsets = (
        ("Photo Information", {
            "fields": ("album", "uploaded_by", ("photo", "photo_url"), "caption"),
            "description": "Upload photo OR provide Google Drive/Dropbox link"
        }),
        ("Moderation", {
            "fields": ("is_approved", "approved_by", "approved_at")
        }),
        ("Sharing", {
            "fields": ("share_to_feed",)
        }),
    )
    
    readonly_fields = ["created_at", "updated_at", "approved_at"]
    
    actions = ["approve_photos", "unapprove_photos"]
    
    def _thumbnail(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 4px; object-fit: cover;" />',
                obj.photo.url
            )
        return "-"
    _thumbnail.short_description = "Photo"
    
    def _like_count(self, obj):
        return obj.like_count
    _like_count.short_description = "Likes"
    
    def _comment_count(self, obj):
        return obj.comment_count
    _comment_count.short_description = "Comments"
    
    def approve_photos(self, request, queryset):
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} photo(s) approved.")
    approve_photos.short_description = "✓ Approve selected photos"
    
    def unapprove_photos(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_by=None, approved_at=None)
        self.message_user(request, f"{updated} photo(s) unapproved.")
    unapprove_photos.short_description = "✗ Unapprove selected photos"


@admin.register(SyncMemoComment)
class SyncMemoCommentAdmin(admin.ModelAdmin):
    list_display = ["photo", "user", "_comment_preview", "_like_count", "created_at"]
    list_filter = ["photo__album__event"]
    search_fields = ["comment", "user__username", "photo__caption"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    
    def _comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    _comment_preview.short_description = "Comment"
    
    def _like_count(self, obj):
        return obj.like_count
    _like_count.short_description = "Likes"


# ========== EVENT PAYMENT ADMIN CLASSES ==========

@admin.register(EventPaymentPackage)
class EventPaymentPackageAdmin(admin.ModelAdmin):
    list_display = [
        "name", "event", "package_type", "_pricing", "_availability",
        "_slots_info", "is_featured", "display_order", "is_active"
    ]
    list_filter = ["package_type", "is_active", "is_featured", "event"]
    search_fields = ["name", "event__event_name", "description"]
    ordering = ["event", "display_order", "price"]
    list_editable = ["display_order", "is_active", "is_featured"]
    
    fieldsets = (
        ("Package Information", {
            "fields": ("event", "name", "package_type", "description")
        }),
        ("💰 Pricing", {
            "fields": (
                ("price", "early_bird_price"),
            ),
            "description": "Set regular price. Early bird price uses event's early_bird_deadline."
        }),
        ("📊 Capacity", {
            "fields": ("max_slots",),
            "description": "Leave empty for unlimited slots"
        }),
        ("🎁 Benefits", {
            "fields": ("benefits",),
            "description": "List of perks included in this package (JSON array)"
        }),
        ("📅 Availability", {
            "fields": (
                "is_active",
                ("available_from", "available_until"),
            )
        }),
        ("🎨 Display", {
            "fields": (
                "display_order", "is_featured", "badge_text"
            )
        }),
    )
    
    def _pricing(self, obj):
        """Display pricing info"""
        if obj.early_bird_price and obj.event.is_early_bird_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">GHS {} <del style="color: gray;">GHS {}</del></span>',
                obj.early_bird_price, obj.price
            )
        return format_html('<span style="font-weight: bold;">GHS {}</span>', obj.price)
    _pricing.short_description = "Price"
    
    def _availability(self, obj):
        """Display availability status"""
        if not obj.is_active:
            return format_html('<span style="color: gray;">🚫 Inactive</span>')
        if obj.is_sold_out:
            return format_html('<span style="color: red;">🔴 Sold Out</span>')
        if not obj.is_available:
            return format_html('<span style="color: orange;">⏳ Not Available</span>')
        return format_html('<span style="color: green;">✓ Available</span>')
    _availability.short_description = "Status"
    
    def _slots_info(self, obj):
        """Display slots information"""
        if not obj.max_slots:
            return format_html('<span style="color: gray;">Unlimited</span>')
        available = obj.slots_available
        total = obj.max_slots
        taken = obj.slots_taken
        
        if available == 0:
            color = "red"
        elif available < total * 0.2:
            color = "orange"
        else:
            color = "green"
        
        return format_html(
            '<span style="color: {};">{}/{} ({} left)</span>',
            color, taken, total, available
        )
    _slots_info.short_description = "Slots"


@admin.register(EventPaymentTransaction)
class EventPaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "event", "_user_info", "transaction_type",
        "_amount_display", "payment_method", "payment_gateway",
        "status", "initiated_at"
    ]
    list_filter = ["status", "transaction_type", "payment_method", "payment_gateway", "event"]
    search_fields = [
        "reference", "gateway_reference", "customer_email", "customer_phone",
        "customer_name", "user__username", "event__event_name",
        "registration__registration_number"
    ]
    date_hierarchy = "initiated_at"
    ordering = ["-initiated_at"]
    readonly_fields = [
        "reference", "initiated_at", "completed_at", "updated_at",
        "gateway_response", "verified", "verified_at"
    ]
    
    fieldsets = (
        ("Transaction Information", {
            "fields": (
                "reference", "transaction_type", "status", "status_message"
            )
        }),
        ("🔗 Relations", {
            "fields": ("event", "registration", "user", "package")
        }),
        ("💰 Amount", {
            "fields": (
                ("amount", "currency"),
                ("gateway_fee", "net_amount"),
            )
        }),
        ("💳 Payment Details", {
            "fields": (
                ("payment_method", "payment_gateway"),
                "authorization_url", "access_code"
            )
        }),
        ("👤 Customer Info", {
            "fields": ("customer_name", "customer_email", "customer_phone")
        }),
        ("🔌 Gateway Response", {
            "fields": ("gateway_reference", "gateway_response"),
            "classes": ("collapse",)
        }),
        ("↩️ Refund Info", {
            "fields": ("refund_amount", "refund_reason", "refunded_at", "refunded_by"),
            "classes": ("collapse",)
        }),
        ("📊 Metadata", {
            "fields": ("ip_address", "metadata"),
            "classes": ("collapse",)
        }),
        ("⏰ Timestamps", {
            "fields": (
                "initiated_at", "completed_at", "expires_at", "updated_at",
                "verified", "verified_at"
            )
        }),
    )
    
    actions = ["mark_as_success", "mark_as_failed", "verify_transactions"]
    
    def _user_info(self, obj):
        """Display user info"""
        if obj.customer_name:
            return format_html(
                '<span title="{}">{}</span>',
                obj.customer_email, obj.customer_name
            )
        return obj.customer_email or obj.user.username if obj.user else "-"
    _user_info.short_description = "Customer"
    
    def _amount_display(self, obj):
        """Display amount with status color"""
        if obj.status == 'success':
            color = "green"
            icon = "✓"
        elif obj.status in ['pending', 'processing']:
            color = "orange"
            icon = "⏳"
        else:
            color = "red"
            icon = "✗"
        
        return format_html(
            '<span style="color: {};">{} {} {}</span>',
            color, icon, obj.currency, obj.amount
        )
    _amount_display.short_description = "Amount"
    
    def mark_as_success(self, request, queryset):
        """Mark transactions as successful (manual verification)"""
        for txn in queryset.filter(status='pending'):
            txn.status = 'success'
            txn.completed_at = timezone.now()
            txn.save()
        self.message_user(request, f"{queryset.count()} transaction(s) marked as successful.")
    mark_as_success.short_description = "✓ Mark as Successful"
    
    def mark_as_failed(self, request, queryset):
        """Mark transactions as failed"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, f"{updated} transaction(s) marked as failed.")
    mark_as_failed.short_description = "✗ Mark as Failed"
    
    def verify_transactions(self, request, queryset):
        """Verify transactions with payment gateway"""
        # TODO: Implement actual gateway verification
        count = queryset.filter(status='pending').count()
        self.message_user(request, f"Verification queued for {count} transaction(s).")
    verify_transactions.short_description = "🔍 Verify with Gateway"


@admin.register(EventPaymentRefund)
class EventPaymentRefundAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "_original_transaction", "_registration",
        "amount", "reason", "status", "created_at"
    ]
    list_filter = ["status", "reason", "original_transaction__event"]
    search_fields = [
        "reference", "gateway_reference", "reason_details",
        "original_transaction__reference", "registration__registration_number"
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    readonly_fields = ["reference", "created_at", "processed_at", "completed_at", "approved_at"]
    
    fieldsets = (
        ("Refund Information", {
            "fields": ("reference", "original_transaction", "registration", "amount")
        }),
        ("Reason", {
            "fields": ("reason", "reason_details")
        }),
        ("Status", {
            "fields": ("status", "status_message")
        }),
        ("Gateway Response", {
            "fields": ("gateway_reference", "gateway_response"),
            "classes": ("collapse",)
        }),
        ("Admin Tracking", {
            "fields": ("initiated_by", "approved_by", "approved_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "processed_at", "completed_at")
        }),
    )
    
    actions = ["approve_refunds", "process_refunds", "reject_refunds"]
    
    def _original_transaction(self, obj):
        return format_html(
            '<a href="/admin/events/eventpaymenttransaction/{}/change/">{}</a>',
            obj.original_transaction.id, obj.original_transaction.reference
        )
    _original_transaction.short_description = "Original Txn"
    
    def _registration(self, obj):
        return format_html(
            '<a href="/admin/events/eventregistration/{}/change/">{}</a>',
            obj.registration.id, obj.registration.registration_number
        )
    _registration.short_description = "Registration"
    
    def approve_refunds(self, request, queryset):
        """Approve pending refunds"""
        updated = queryset.filter(status='pending').update(
            status='processing',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} refund(s) approved for processing.")
    approve_refunds.short_description = "✓ Approve Refunds"
    
    def process_refunds(self, request, queryset):
        """Process approved refunds"""
        # TODO: Implement actual refund processing with gateway
        count = queryset.filter(status='processing').count()
        self.message_user(request, f"Processing queued for {count} refund(s).")
    process_refunds.short_description = "💳 Process Refunds"
    
    def reject_refunds(self, request, queryset):
        """Reject pending refunds"""
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"{updated} refund(s) rejected.")
    reject_refunds.short_description = "✗ Reject Refunds"
