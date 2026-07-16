"""
Recent Updates Repository
Aggregates notifications from various models without creating new database tables
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from typing import List, Dict, Any, Optional
from uuid import uuid4


class RecentUpdatesRepository:
    """
    Repository for aggregating recent updates from various models
    No database storage - pulls data from existing models
    """
    
    @classmethod
    def get_recent_updates(
        cls,
        user,
        days: int = 7,
        limit: int = 50,
        types: Optional[List[str]] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get aggregated recent updates for a user
        
        Args:
            user: User instance
            days: Number of days to look back
            limit: Maximum number of updates to return
            types: Filter by update types (task, event, helpdesk, payment, security)
            priority: Filter by priority (low, medium, high, urgent)
            page: Page number for pagination
            page_size: Items per page
        
        Returns:
            Dict with updates and metadata
        """
        since_date = timezone.now() - timedelta(days=days)
        all_updates = []
        
        # Map specific types to categories for filtering
        # If types contains specific update types, extract their categories
        categories = set()
        if types:
            for t in types:
                if t.startswith('task_'):
                    categories.add('task')
                elif t.startswith('event_'):
                    categories.add('event')
                elif t.startswith('helpdesk_'):
                    categories.add('helpdesk')
                elif t.startswith('payment_'):
                    categories.add('payment')
                elif t.startswith('merchandise_'):
                    categories.add('merchandise')
                elif t.startswith('security_'):
                    categories.add('security')
                # Also support generic category names
                elif t in ['task', 'event', 'helpdesk', 'payment', 'merchandise', 'security']:
                    categories.add(t)
        
        # Collect updates from different sources
        if not types or 'task' in categories:
            task_updates = cls._get_task_updates(user, since_date, limit)
            all_updates.extend(task_updates)
        
        if not types or 'event' in categories:
            event_updates = cls._get_event_updates(user, since_date, limit)
            all_updates.extend(event_updates)
        
        if not types or 'helpdesk' in categories:
            helpdesk_updates = cls._get_helpdesk_updates(user, since_date, limit)
            all_updates.extend(helpdesk_updates)
        
        if not types or 'payment' in categories:
            payment_updates = cls._get_payment_updates(user, since_date, limit)
            all_updates.extend(payment_updates)
        
        if not types or 'merchandise' in categories:
            merchandise_updates = cls._get_merchandise_collection_updates(user, since_date, limit)
            all_updates.extend(merchandise_updates)
        
        if not types or 'security' in categories:
            security_updates = cls._get_security_updates(user, since_date, limit)
            all_updates.extend(security_updates)
        
        # Sort by created_at descending
        all_updates.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Filter by specific types if provided (after fetching by category)
        if types:
            specific_types = [t for t in types if '_' in t]  # Only specific types like 'task_created'
            if specific_types:
                all_updates = [u for u in all_updates if u['type'] in specific_types]
        
        # Filter by priority if specified
        if priority:
            all_updates = [u for u in all_updates if u.get('priority') == priority]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_updates = all_updates[start_idx:end_idx]
        has_more = end_idx < len(all_updates)
        
        # Calculate stats
        stats = cls._calculate_stats(all_updates, since_date)
        
        # Build next/previous URLs (will be None for now, or can be constructed)
        next_url = None
        previous_url = None
        if has_more:
            next_url = f"?page={page + 1}&page_size={page_size}"
        if page > 1:
            previous_url = f"?page={page - 1}&page_size={page_size}"
        
        return {
            'count': len(all_updates),  # Total count of all updates (before pagination)
            'next': next_url,
            'previous': previous_url,
            'results': paginated_updates,  # Changed from 'updates' to 'results' for DRF compatibility
            'stats': stats,  # Extra field for statistics
        }
    
    @classmethod
    def _get_task_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get task-related updates"""
        from planner.models import Task
        
        updates = []
        
        # Recent tasks
        recent_tasks = Task.objects.filter(
            user=user,
            created_at__gte=since_date,
            is_deleted=False
        ).order_by('-created_at')[:limit]
        
        for task in recent_tasks:
            # Build informative description
            due_info = ""
            if task.due_date:
                days_until = (task.due_date - timezone.now().date()).days
                if days_until < 0:
                    due_info = f" (Overdue by {abs(days_until)} day{'s' if abs(days_until) != 1 else ''})"
                elif days_until == 0:
                    due_info = " (Due today!)"
                elif days_until == 1:
                    due_info = " (Due tomorrow)"
                else:
                    due_info = f" (Due in {days_until} days)"
            
            description = f"📚 {task.course_code}{due_info} • Priority: {task.priority.title()}"
            if task.description:
                desc_preview = task.description[:60] + "..." if len(task.description) > 60 else task.description
                description += f" • {desc_preview}"
            
            updates.append({
                'id': f"task-{task.id}",
                'type': 'task_created',
                'category': 'Tasks',
                'title': f"📝 New: {task.title}",
                'description': description,
                'priority': task.priority,
                'created_at': task.created_at,
                'time_ago': '',  # Will be calculated by serializer
                'related_object_id': str(task.id),
                'metadata': {
                    'course_code': task.course_code,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'status': task.status,
                },
            })
        
        # Completed tasks
        completed_tasks = Task.objects.filter(
            user=user,
            completed=True,
            completed_at__gte=since_date,
            is_deleted=False
        ).order_by('-completed_at')[:limit]
        
        for task in completed_tasks:
            completion_info = f"📚 {task.course_code}"
            if task.completed_at:
                time_taken = (task.completed_at - task.created_at).days
                if time_taken == 0:
                    completion_info += " • Completed same day!"
                else:
                    completion_info += f" • Took {time_taken} day{'s' if time_taken != 1 else ''}"
            
            updates.append({
                'id': f"task-completed-{task.id}",
                'type': 'task_completed',
                'category': 'Tasks',
                'title': f"✅ Completed: {task.title}",
                'description': completion_info + " • Well done!",
                'priority': 'low',
                'created_at': task.completed_at,
                'time_ago': '',
                'related_object_id': str(task.id),
                'metadata': {
                    'course_code': task.course_code,
                },
            })
        
        # Upcoming due tasks (urgent)
        upcoming_due = Task.objects.filter(
            user=user,
            completed=False,
            due_date__lte=timezone.now().date() + timedelta(days=2),
            due_date__gte=timezone.now().date(),
            is_deleted=False
        ).order_by('due_date')[:10]
        
        for task in upcoming_due:
            days_until_due = (task.due_date - timezone.now().date()).days
            
            # Create urgency-based description
            if days_until_due == 0:
                urgency = "⚠️ DUE TODAY!"
                description = f"📚 {task.course_code} • Complete this task ASAP"
            elif days_until_due == 1:
                urgency = "⏰ Due Tomorrow"
                description = f"📚 {task.course_code} • Don't forget about this!"
            else:
                urgency = f"⏰ Due in {days_until_due} days"
                description = f"📚 {task.course_code} • Plan ahead to complete on time"
            
            # Add task details if available
            if task.description:
                desc_preview = task.description[:50] + "..." if len(task.description) > 50 else task.description
                description += f" • {desc_preview}"
            
            updates.append({
                'id': f"task-due-{task.id}",
                'type': 'task_due_soon',
                'category': 'Tasks',
                'title': f"{urgency}: {task.title}",
                'description': description,
                'priority': 'urgent' if days_until_due == 0 else 'high',
                'created_at': task.updated_at or task.created_at,
                'time_ago': '',
                'related_object_id': str(task.id),
                'metadata': {
                    'course_code': task.course_code,
                    'due_date': task.due_date.isoformat(),
                    'days_until_due': days_until_due,
                },
            })
        
        return updates
    
    @classmethod
    def _get_event_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get event-related updates"""
        from events.models import Event
        
        updates = []
        
        # New events (created recently)
        new_events = Event.objects.filter(
            created_at__gte=since_date
        ).order_by('-created_at')[:limit]
        
        for event in new_events:
            # Check if event is upcoming
            is_upcoming = event.event_date and event.event_date > timezone.now()
            
            # Build detailed event description
            date_str = event.event_date.strftime('%B %d, %Y at %I:%M %p') if event.event_date else 'Date TBA'
            venue_str = f"📍 {event.venue}" if event.venue else "📍 Venue TBA"
            event_type_emoji = "🎤" if event.event_type == "Seminar" else "🎉" if event.event_type == "Social" else "📚"
            
            # Add registration info if available
            registration_info = ""
            if hasattr(event, 'registration_required') and event.registration_required:
                registration_info = " • 🎫 Registration required"
            elif hasattr(event, 'is_free') and event.is_free:
                registration_info = " • 🆓 Free entry"
            
            title = f"{event_type_emoji} New: {event.event_name}"
            description = f"{event.event_type or 'Event'} • 📅 {date_str} • {venue_str}{registration_info}"
            
            # Featured events get star emoji
            if event.featured:
                title = f"⭐ {title}"
            
            updates.append({
                'id': f"event-{event.event_id}",
                'type': 'event_created',
                'category': 'Events',
                'title': title,
                'description': description,
                'priority': 'high' if event.featured else 'medium',
                'related_object_id': str(event.event_id),  # Include event UUID for routing
                'metadata': {
                    'event_id': str(event.event_id),
                    'event_type': event.event_type,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'venue': event.venue,
                    'featured': event.featured,
                },
                'created_at': event.created_at,
                'time_ago': '',  # Will be calculated later
            })
        
        # Upcoming events (next 3 days)
        upcoming_events = Event.objects.filter(
            event_date__gte=timezone.now(),
            event_date__lte=timezone.now() + timedelta(days=3)
        ).order_by('event_date')[:10]
        
        for event in upcoming_events:
            # Calculate days until event using calendar dates (not datetime difference)
            if event.event_date:
                event_day = event.event_date.date()
                today = timezone.now().date()
                days_until = (event_day - today).days
                hours_until = int((event.event_date - timezone.now()).total_seconds() / 3600)
            else:
                days_until = 0
                hours_until = 0
            
            # Create urgency-based messaging
            if days_until == 0:
                if hours_until <= 1:
                    urgency_msg = "🔥 Starting NOW!"
                    time_msg = "Event is happening right now"
                elif hours_until <= 3:
                    urgency_msg = f"⏰ Starting in {hours_until} hour{'s' if hours_until != 1 else ''}!"
                    time_msg = "Get ready!"
                else:
                    urgency_msg = "🔔 TODAY!"
                    time_msg = f"Starts at {event.event_date.strftime('%I:%M %p')}"
            elif days_until == 1:
                urgency_msg = "📅 Tomorrow"
                time_msg = f"at {event.event_date.strftime('%I:%M %p')}"
            elif days_until == 2:
                urgency_msg = "📆 In 2 days"
                time_msg = f"{event.event_date.strftime('%A at %I:%M %p')}"
            else:
                urgency_msg = f"📅 In {days_until} days"
                time_msg = event.event_date.strftime('%A, %B %d at %I:%M %p')
            
            venue_str = f"📍 {event.venue}" if event.venue else "📍 Venue TBA"
            title = f"{urgency_msg} {event.event_name}"
            description = f"{time_msg} • {venue_str}"
            
            # Add event type info
            if event.event_type:
                description += f" • {event.event_type}"
            
            updates.append({
                'id': f"event-upcoming-{event.event_id}",
                'type': 'event_upcoming',
                'category': 'Events',
                'title': title,
                'description': description,
                'priority': 'urgent' if days_until == 0 else 'high',
                'related_object_id': str(event.event_id),  # Include event UUID for routing
                'metadata': {
                    'event_id': str(event.event_id),
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'days_until': days_until,
                    'hours_until': hours_until,
                    'venue': event.venue,
                },
                'created_at': event.last_updated or event.created_at,
                'time_ago': '',  # Will be calculated later
            })
        
        return updates
    
    @classmethod
    def _get_helpdesk_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get helpdesk ticket updates"""
        from helpdesk.models import HelpDeskRequest, HelpDeskResponse
        
        updates = []
        
        # User's requests with recent updates
        user_requests = HelpDeskRequest.objects.filter(
            author=user,
            updated_at__gte=since_date
        ).prefetch_related('responses').order_by('-updated_at')[:limit]
        
        for request in user_requests:
            # Get recent responses from others (not the user themselves)
            recent_responses_qs = request.responses.filter(
                created_at__gte=since_date
            ).exclude(author=user).select_related('author').order_by('-created_at')
            
            recent_responses_count = recent_responses_qs.count()
            has_new_response = recent_responses_count > 0
            
            # Get the most recent response for detailed info
            latest_response = recent_responses_qs.first() if has_new_response else None
            
            # Build detailed description
            if request.status == 'resolved':
                title = f"✅ Resolved: {request.title[:40]}"
                if latest_response:
                    responder_name = f"{latest_response.author.first_name} {latest_response.author.last_name}"
                    # Get preview of response (first 80 chars)
                    response_preview = latest_response.content[:80] + "..." if len(latest_response.content) > 80 else latest_response.content
                    description = f"{responder_name} marked this resolved: \"{response_preview}\""
                    priority_level = 'medium'
                else:
                    description = "Your help request has been resolved"
                    priority_level = 'medium'
            elif request.status == 'active':
                if has_new_response:
                    # Show who responded and preview
                    responder_name = f"{latest_response.author.first_name} {latest_response.author.last_name}"
                    response_preview = latest_response.content[:100] + "..." if len(latest_response.content) > 100 else latest_response.content
                    
                    if recent_responses_count == 1:
                        title = f"💬 {responder_name} responded"
                        description = f"On '{request.title[:40]}': \"{response_preview}\""
                    else:
                        title = f"💬 {recent_responses_count} new responses"
                        description = f"{responder_name} (latest): \"{response_preview}\""
                    priority_level = 'high'
                else:
                    title = f"📋 Active: {request.title[:45]}"
                    description = f"Your help request is awaiting responses. {request.response_count} total response(s)."
                    priority_level = 'medium'
            else:
                title = f"📋 {request.title[:45]}"
                description = f"Status: {request.status.title()}"
                priority_level = 'low'
            
            update_type = 'helpdesk_response_added' if has_new_response else 'helpdesk_status_changed'
            
            # Add responder info to metadata
            responder_info = None
            if latest_response:
                responder_info = {
                    'name': f"{latest_response.author.first_name} {latest_response.author.last_name}",
                    'response_preview': latest_response.content[:150],
                }
            
            updates.append({
                'id': f"helpdesk-{request.tracking_id}",
                'type': update_type,
                'category': 'HelpDesk',
                'title': title,
                'description': description,
                'priority': priority_level,
                'related_object_id': str(request.id),  # Include UUID for routing
                'metadata': {
                    'request_id': str(request.id),  # UUID for API calls
                    'tracking_id': request.tracking_id,
                    'title': request.title,
                    'status': request.status,
                    'priority': request.priority,
                    'response_count': recent_responses_count,
                    'total_responses': request.response_count,
                    'responder': responder_info,
                },
                'created_at': request.updated_at,
                'time_ago': '',  # Will be calculated later
            })
        
        return updates
    
    @classmethod
    def _get_payment_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get payment/purchase updates"""
        from payments.models import Transaction
        from products.models import Product, ProductPayment
        from django.contrib.contenttypes.models import ContentType
        
        updates = []
        
        # Get product purchases
        product_content_type = ContentType.objects.get_for_model(Product)
        
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type='payment',
            content_type=product_content_type,
            initiated_at__gte=since_date
        ).select_related('content_type').prefetch_related('product_payments').order_by('-initiated_at')[:limit]
        
        for txn in transactions:
            # Access content_object directly (GenericForeignKey)
            product = txn.content_object
            product_name = product.product_name if product and hasattr(product, 'product_name') else 'Product'
            
            # Get product size/variation info if available
            product_details = ""
            if product and hasattr(product, 'size') and product.size:
                product_details = f" (Size: {product.size})"
            elif product and hasattr(product, 'variation') and product.variation:
                product_details = f" ({product.variation})"
            
            # Get merchandise collection info from ProductPayment (not Transaction)
            product_payment = txn.product_payments.first()  # Get associated ProductPayment
            merchandise_collected = product_payment.merchandise_taken if product_payment else False
            validation_code = product_payment.transaction_validation_code if product_payment else None
            
            if txn.status == 'success':
                update_type = 'payment_uncollected' if not merchandise_collected else 'payment_success'
                
                if not merchandise_collected:
                    # Payment success but not collected - URGENT
                    title = f"🎁 Ready for pickup: {product_name}{product_details}"
                    description = f"💳 Paid GH₵{txn.amount} • 🔑 Collection Code: {validation_code or 'Pending'} • Visit merchandise desk to collect"
                    priority_level = 'high'
                else:
                    # Payment success and collected
                    title = f"✅ Purchase complete: {product_name}{product_details}"
                    description = f"💳 GH₵{txn.amount} • Successfully collected. Thank you for your purchase!"
                    priority_level = 'medium'
                    
            elif txn.status == 'failed':
                update_type = 'payment_failed'
                title = f"❌ Payment failed: {product_name}{product_details}"
                description = f"💳 GH₵{txn.amount} transaction failed • Reason: {txn.status_message or 'Payment could not be processed'} • Please try again or contact support"
                priority_level = 'high'
                
            elif txn.status == 'pending':
                update_type = 'payment_uncollected'
                title = f"⏳ Payment pending: {product_name}{product_details}"
                description = f"💳 GH₵{txn.amount} • Awaiting payment confirmation • Check back shortly"
                priority_level = 'medium'
            else:
                continue
            
            updates.append({
                'id': f"payment-{txn.id}",
                'type': update_type,
                'category': 'Payments',
                'title': title,
                'description': description,
                'priority': priority_level,
                'related_object_id': txn.id,
                'metadata': {
                    'transaction_id': str(txn.id),
                    'product_name': product_name,
                    'amount': str(txn.amount),
                    'status': txn.status,
                    'validation_code': validation_code,
                    'collected': merchandise_collected,
                },
                'created_at': txn.initiated_at,
                'time_ago': '',  # Will be calculated later
            })
        
        return updates
    
    @classmethod
    def _get_merchandise_collection_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get merchandise collection updates from ProductPayment"""
        from products.models import ProductPayment
        
        updates = []
        
        # Get collected merchandise (find by phone number since ProductPayment doesn't have user FK)
        if not user.phone:
            return updates
        
        phone_str = str(user.phone)
        
        # Get ProductPayments where collection happened recently
        collected_payments = ProductPayment.objects.filter(
            phone=phone_str,
            merchandise_taken=True,
            merchandise_taken_at__gte=since_date,
            payment_successful=True
        ).select_related('product').order_by('-merchandise_taken_at')[:limit]
        
        for payment in collected_payments:
            product = payment.product
            product_name = product.product_name if product else 'Product'
            
            # Get collection summary
            summary = payment.get_collection_summary() if hasattr(payment, 'get_collection_summary') else {}
            total_collected = summary.get('total_collected', payment.quantity)
            total_ordered = summary.get('total_ordered', payment.quantity)
            overall_status = summary.get('overall_status', 'collected')
            
            # Build variant details for description
            variant_info = ""
            if payment.collection_details:
                collected_variants = [v for v in payment.collection_details if v.get('status') == 'collected']
                if collected_variants:
                    # Get color/size names
                    variant_names = []
                    for v in collected_variants[:2]:  # Show max 2
                        color_id = v.get('color_id')
                        size_id = v.get('size_id')
                        parts = []
                        if color_id:
                            try:
                                from products.models import ProductColor
                                color = ProductColor.objects.get(id=color_id)
                                parts.append(color.name)
                            except:
                                pass
                        if size_id:
                            try:
                                from products.models import ProductSize
                                size = ProductSize.objects.get(id=size_id)
                                parts.append(size.name)
                            except:
                                pass
                        if parts:
                            variant_names.append(" / ".join(parts))
                    if variant_names:
                        variant_info = f" ({', '.join(variant_names)})"
            
            # Determine update type and message
            if overall_status == 'collected':
                update_type = 'merchandise_collected'
                title = f"✅ Collected: {product_name}{variant_info}"
                description = f"All {total_ordered} item(s) collected • Code: {payment.transaction_validation_code}"
                priority_level = 'low'
            elif overall_status == 'partial':
                update_type = 'merchandise_partial_collected'
                title = f"📦 Partially Collected: {product_name}"
                description = f"{total_collected} of {total_ordered} items collected • Come back for the rest"
                priority_level = 'medium'
            else:
                continue  # Skip pending items
            
            # Include who verified
            taken_by_info = ""
            if payment.taken_by:
                taken_by_info = f" • Verified by {payment.taken_by}"
            
            updates.append({
                'id': f"collection-{payment.payment_id}",
                'type': update_type,
                'category': 'Collections',
                'title': title,
                'description': f"{description}{taken_by_info}",
                'priority': priority_level,
                'related_object_id': str(payment.payment_id),
                'metadata': {
                    'payment_id': str(payment.payment_id),
                    'product_id': str(product.product_id) if product else None,
                    'product_name': product_name,
                    'validation_code': payment.transaction_validation_code,
                    'total_collected': total_collected,
                    'total_ordered': total_ordered,
                    'collection_status': overall_status,
                    'taken_by': payment.taken_by,
                    'amount': str(payment.amount) if payment.amount else None,
                },
                'created_at': payment.merchandise_taken_at,
                'time_ago': '',  # Will be calculated later
            })
        
        return updates
    
    @classmethod
    def _get_security_updates(cls, user, since_date, limit) -> List[Dict]:
        """Get security-related updates (password changes, profile updates)"""
        # TODO: Implement security updates tracking
        # For now, return empty list since we need proper audit logging
        return []
        """Get security-related updates"""
        updates = []
        
        # Check if password was changed recently
        # Note: We can track this via user's updated_at if password_changed_at doesn't exist
        if hasattr(user, 'password_changed_at') and user.password_changed_at:
            if user.password_changed_at >= since_date:
                updates.append({
                    'id': f"security-password-{user.id}",
                    'type': 'security',
                    'category': 'password_change',
                    'title': "Password changed",
                    'message': "Your password was successfully changed",
                    'icon': 'shield-checkmark',
                    'emoji': '🔒',
                    'color': '#10B981',
                    'priority': 'medium',
                    'action_url': None,
                    'action_label': None,
                    'is_actionable': False,
                    'metadata': {
                        'type': 'password_change',
                    },
                    'created_at': user.password_changed_at,
                    'is_read': False,
                })
        
        # Check for profile updates
        if user.updated_at >= since_date:
            updates.append({
                'id': f"security-profile-{user.id}",
                'type': 'security',
                'category': 'profile_update',
                'title': "Profile updated",
                'message': "Your profile information was updated",
                'icon': 'person',
                'emoji': '👤',
                'color': '#3B82F6',
                'priority': 'low',
                'action_url': '/profile',
                'action_label': 'View Profile',
                'is_actionable': False,
                'metadata': {
                    'type': 'profile_update',
                },
                'created_at': user.updated_at,
                'is_read': False,
            })
        
        return updates
    
    @classmethod
    def _calculate_stats(cls, updates: List[Dict], since_date) -> Dict[str, Any]:
        """Calculate statistics for updates"""
        total = len(updates)
        unread = sum(1 for u in updates if not u.get('is_read', False))
        
        # Count by type
        by_type = {}
        for update in updates:
            update_type = update.get('type', 'unknown')
            by_type[update_type] = by_type.get(update_type, 0) + 1
        
        # Count by priority
        by_priority = {}
        for update in updates:
            priority = update.get('priority', 'medium')
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Count today and this week
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        today_count = sum(
            1 for u in updates 
            if u.get('created_at') and u['created_at'].date() == today
        )
        
        this_week_count = sum(
            1 for u in updates 
            if u.get('created_at') and u['created_at'].date() >= week_ago
        )
        
        urgent_count = sum(
            1 for u in updates 
            if u.get('priority') == 'urgent' and u.get('is_actionable', False)
        )
        
        return {
            'total': total,
            'unread': unread,
            'by_type': by_type,
            'by_priority': by_priority,
            'today_count': today_count,
            'this_week_count': this_week_count,
            'urgent_count': urgent_count,
        }
    
    @classmethod
    def get_users_needing_notifications(cls, notification_type: str) -> List:
        """
        Get list of users who need push notifications for a specific type
        Used by management command for scheduled push notifications
        
        Args:
            notification_type: Type of notification to check
                - 'task_due': Tasks due soon
                - 'event_upcoming': Events starting soon
                - 'helpdesk_response': New ticket responses
                - 'payment_reminder': Uncollected purchases
        
        Returns:
            List of (user, notification_data) tuples
        """
        from accounts.models import CustomUser
        from django.utils import timezone
        
        users_to_notify = []
        
        if notification_type == 'task_due':
            # Users with tasks due in next 24 hours
            from planner.models import Task
            
            tomorrow = timezone.now() + timedelta(days=1)
            tasks = Task.objects.filter(
                completed=False,
                due_date__lte=tomorrow.date(),
                due_date__gte=timezone.now().date(),
                is_deleted=False
            ).select_related('user')
            
            user_tasks = {}
            for task in tasks:
                if task.user not in user_tasks:
                    user_tasks[task.user] = []
                user_tasks[task.user].append(task)
            
            for user, user_task_list in user_tasks.items():
                # Get most urgent task for preview
                most_urgent = min(user_task_list, key=lambda t: t.due_date)
                days_until = (most_urgent.due_date - timezone.now().date()).days
                
                # Create detailed notification message
                if len(user_task_list) == 1:
                    task = user_task_list[0]
                    urgency = "⚠️ DUE TODAY!" if days_until == 0 else "⏰ Due Tomorrow"
                    title = f"{urgency} {task.title[:40]}"
                    body = f"📚 {task.course_code} • {task.description[:50] if task.description else 'Complete ASAP'}"
                else:
                    title = f"⚠️ {len(user_task_list)} tasks due soon"
                    urgency = f"{sum(1 for t in user_task_list if (t.due_date - timezone.now().date()).days == 0)} today" if any((t.due_date - timezone.now().date()).days == 0 for t in user_task_list) else "within 24 hours"
                    body = f"{urgency} • Most urgent: {most_urgent.title[:40]}"
                
                users_to_notify.append((user, {
                    'title': title,
                    'body': body,
                    'data': {
                        'type': 'task_due_soon',
                        'category': 'Tasks',
                        'count': len(user_task_list),
                        'task_ids': [str(t.id) for t in user_task_list],
                        'most_urgent_course': most_urgent.course_code,
                    }
                }))
        
        elif notification_type == 'event_upcoming':
            # Events starting in next 24 hours
            from events.models import Event
            
            tomorrow = timezone.now() + timedelta(days=1)
            events = Event.objects.filter(
                event_date__gte=timezone.now(),
                event_date__lte=tomorrow
            )
            
            # Notify all active users about upcoming events
            active_users = CustomUser.objects.filter(is_active=True)
            
            for event in events:
                days_until = (event.event_date - timezone.now()).days if event.event_date else 0
                hours_until = int((event.event_date - timezone.now()).total_seconds() / 3600) if event.event_date else 0
                
                # Create urgency-based messaging
                if days_until == 0:
                    if hours_until <= 1:
                        urgency = "🔥 STARTING NOW"
                        time_detail = "happening right now"
                    elif hours_until <= 3:
                        urgency = f"⏰ In {hours_until}h"
                        time_detail = f"starting in {hours_until} hour{'s' if hours_until != 1 else ''}"
                    else:
                        urgency = "🔔 TODAY"
                        time_detail = f"at {event.event_date.strftime('%I:%M %p')}"
                else:
                    urgency = "📅 Tomorrow"
                    time_detail = f"at {event.event_date.strftime('%I:%M %p')}"
                
                venue_info = f"📍 {event.venue}" if event.venue else "📍 Venue TBA"
                
                for user in active_users:
                    users_to_notify.append((user, {
                        'title': f"{urgency}: {event.event_name}",
                        'body': f"{event.event_type or 'Event'} {time_detail} • {venue_info}",
                        'data': {
                            'type': 'event_upcoming',
                            'category': 'Events',
                            'event_id': str(event.event_id),
                            'hours_until': hours_until,
                        }
                    }))
        
        elif notification_type == 'payment_reminder':
            # Uncollected purchases older than 3 days
            from payments.models import Transaction
            from products.models import Product
            from django.contrib.contenttypes.models import ContentType
            
            three_days_ago = timezone.now() - timedelta(days=3)
            product_content_type = ContentType.objects.get_for_model(Product)
            
            uncollected = Transaction.objects.filter(
                status='success',
                transaction_type='payment',
                content_type=product_content_type,
                merchandise_collected=False,
                initiated_at__lte=three_days_ago  # Use initiated_at instead of completed_at
            ).select_related('user')
            
            for txn in uncollected:
                product = txn.content_object
                product_name = product.product_name if product and hasattr(product, 'product_name') else 'item'
                
                # Calculate days waiting
                days_waiting = (timezone.now() - txn.initiated_at).days
                urgency = "🚨" if days_waiting > 7 else "⏰"
                
                users_to_notify.append((txn.user, {
                    'title': f"{urgency} Collect your {product_name}",
                    'body': f"💳 GH₵{txn.amount} • 🔑 Code: {txn.merchandise_validation_code or 'N/A'} • Waiting {days_waiting} days",
                    'data': {
                        'type': 'payment_uncollected',
                        'category': 'Payments',
                        'transaction_id': str(txn.id),
                        'validation_code': txn.merchandise_validation_code,
                        'days_waiting': days_waiting,
                    }
                }))
        
        return users_to_notify
