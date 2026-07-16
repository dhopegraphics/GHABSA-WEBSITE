"""
Donation Admin Dashboard Views
Standalone admin interface for managing donation withdrawals
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from decimal import Decimal
import json

from .models import Donation, DonationWallet, DonationWithdrawal
from .services import DonationService


@staff_member_required
def withdrawal_dashboard(request):
    """
    Main withdrawal dashboard - standalone admin interface
    Shows all withdrawals with actions based on status
    """
    wallet = DonationWallet.get_wallet()
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    method_filter = request.GET.get('method', 'all')
    search = request.GET.get('search', '')
    
    # Base queryset
    withdrawals = DonationWithdrawal.objects.select_related(
        'initiated_by', 'approved_by'
    ).order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    if method_filter != 'all':
        withdrawals = withdrawals.filter(transfer_method=method_filter)
    
    if search:
        withdrawals = withdrawals.filter(
            Q(reference__icontains=search) |
            Q(recipient_name__icontains=search) |
            Q(recipient_account__icontains=search) |
            Q(purpose__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(withdrawals, 20)
    page = request.GET.get('page', 1)
    withdrawals_page = paginator.get_page(page)
    
    # Stats
    stats = {
        'pending': DonationWithdrawal.objects.filter(status='pending').count(),
        'approved': DonationWithdrawal.objects.filter(status='approved').count(),
        'processing': DonationWithdrawal.objects.filter(status='processing').count(),
        'completed': DonationWithdrawal.objects.filter(status='completed').count(),
        'failed': DonationWithdrawal.objects.filter(status='failed').count(),
        'rejected': DonationWithdrawal.objects.filter(status='rejected').count(),
        'pending_amount': DonationWithdrawal.objects.filter(
            status__in=['pending', 'approved']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
    }
    
    # Recent donations (last 5)
    recent_donations = Donation.objects.filter(
        status='completed'
    ).order_by('-created_at')[:5]
    
    context = {
        'wallet': wallet,
        'withdrawals': withdrawals_page,
        'stats': stats,
        'recent_donations': recent_donations,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'search': search,
        'bank_choices': DonationWithdrawal.BANK_CHOICES,
    }
    
    return render(request, 'donations/admin/dashboard.html', context)


@staff_member_required
@require_POST
def create_withdrawal(request):
    """Create a new withdrawal request"""
    try:
        data = json.loads(request.body)
        
        amount = Decimal(str(data.get('amount', 0)))
        recipient_name = data.get('recipient_name', '').strip()
        recipient_account = data.get('recipient_account', '').strip()
        recipient_bank_code = data.get('recipient_bank_code', '')
        purpose = data.get('purpose', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'other')
        transfer_method = data.get('transfer_method', 'gateway')
        
        # Validation
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be greater than 0'})
        
        if not recipient_name:
            return JsonResponse({'success': False, 'error': 'Recipient name is required'})
        
        if not recipient_account:
            return JsonResponse({'success': False, 'error': 'Recipient account is required'})
        
        if not purpose:
            return JsonResponse({'success': False, 'error': 'Purpose is required'})
        
        # Check wallet balance
        wallet = DonationWallet.get_wallet()
        if amount > wallet.balance:
            return JsonResponse({
                'success': False, 
                'error': f'Insufficient balance. Available: GH₵{wallet.balance:,.2f}'
            })
        
        # Get bank display name
        bank_display = dict(DonationWithdrawal.BANK_CHOICES).get(
            recipient_bank_code, recipient_bank_code
        )
        
        # Create withdrawal
        withdrawal = DonationWithdrawal.objects.create(
            amount=amount,
            recipient_name=recipient_name,
            recipient_account=recipient_account,
            recipient_bank=bank_display,
            recipient_bank_code=recipient_bank_code,
            purpose=purpose,
            description=description,
            category=category,
            transfer_method=transfer_method,
            status='pending',
            initiated_by=request.user,
            balance_before=wallet.balance,
            balance_after=wallet.balance - amount,
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Withdrawal request created: {withdrawal.reference}',
            'reference': withdrawal.reference,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def approve_withdrawal(request, withdrawal_id):
    """Approve a pending withdrawal - system tracks who and when"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status != 'pending':
            return JsonResponse({
                'success': False,
                'error': f'Cannot approve: status is {withdrawal.get_status_display()}'
            })
        
        # System automatically sets approval
        withdrawal.status = 'approved'
        withdrawal.approved_by = request.user
        withdrawal.approved_at = timezone.now()
        withdrawal.status_message = f'Approved by {request.user.get_full_name() or request.user.username}'
        withdrawal.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Withdrawal {withdrawal.reference} approved',
            'approved_by': request.user.get_full_name() or request.user.username,
            'approved_at': withdrawal.approved_at.strftime('%Y-%m-%d %H:%M'),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def reject_withdrawal(request, withdrawal_id):
    """Reject a pending withdrawal"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status not in ['pending', 'approved']:
            return JsonResponse({
                'success': False,
                'error': f'Cannot reject: status is {withdrawal.get_status_display()}'
            })
        
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'Rejected by admin')
        
        withdrawal.status = 'rejected'
        withdrawal.status_message = f'Rejected by {request.user.get_full_name() or request.user.username}: {reason}'
        withdrawal.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Withdrawal {withdrawal.reference} rejected',
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def process_gateway_transfer(request, withdrawal_id):
    """Process a withdrawal via Paystack gateway transfer"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status not in ['pending', 'approved']:
            return JsonResponse({
                'success': False,
                'error': f'Cannot process: status is {withdrawal.get_status_display()}'
            })
        
        if not withdrawal.recipient_account:
            return JsonResponse({
                'success': False,
                'error': 'Recipient account number is required'
            })
        
        if not withdrawal.recipient_bank_code:
            return JsonResponse({
                'success': False,
                'error': 'Bank/provider code is required for gateway transfer'
            })
        
        # Auto-approve if still pending
        if withdrawal.status == 'pending':
            withdrawal.status = 'approved'
            withdrawal.approved_by = request.user
            withdrawal.approved_at = timezone.now()
            withdrawal.save()
        
        # Process the transfer
        result = DonationService.initiate_gateway_transfer(
            withdrawal=withdrawal,
            performed_by=request.user
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result.get('message', 'Transfer initiated successfully'),
                'transfer_code': result.get('transfer_code'),
                'status': withdrawal.status,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Transfer failed'),
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def verify_transfer(request, withdrawal_id):
    """Verify the status of a gateway transfer"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.transfer_method != 'gateway':
            return JsonResponse({
                'success': False,
                'error': 'This is not a gateway transfer'
            })
        
        if not withdrawal.gateway_transfer_code:
            return JsonResponse({
                'success': False,
                'error': 'No transfer code found'
            })
        
        # Pass the transfer_code string, not the withdrawal object
        result = DonationService.verify_transfer(withdrawal.gateway_transfer_code)
        
        if result['success']:
            # Update withdrawal based on Paystack status
            transfer_status = result.get('transfer_status', '').lower()
            
            if transfer_status == 'success':
                # Complete the transfer
                complete_result = DonationService.complete_gateway_transfer(
                    withdrawal=withdrawal,
                    transfer_status='success',
                    gateway_data=result.get('details')
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Transfer completed successfully!',
                    'status': 'completed',
                    'gateway_status': transfer_status,
                })
            elif transfer_status in ['failed', 'reversed']:
                DonationService.complete_gateway_transfer(
                    withdrawal=withdrawal,
                    transfer_status='failed',
                    gateway_data=result.get('details')
                )
                return JsonResponse({
                    'success': False,
                    'message': f'Transfer {transfer_status}',
                    'status': 'failed',
                    'gateway_status': transfer_status,
                })
            else:
                # Still pending/processing
                withdrawal.status_message = f'Paystack status: {transfer_status}'
                withdrawal.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Transfer is {transfer_status}. Please wait for Paystack to process.',
                    'status': withdrawal.status,
                    'gateway_status': transfer_status,
                })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Verification failed'),
                'status': withdrawal.status,
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def mark_manual_complete(request, withdrawal_id):
    """Mark a manual transfer as completed (with receipt upload)"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status not in ['pending', 'approved']:
            return JsonResponse({
                'success': False,
                'error': f'Cannot complete: status is {withdrawal.get_status_display()}'
            })
        
        # Handle file upload
        receipt_file = request.FILES.get('receipt')
        if not receipt_file and withdrawal.transfer_method == 'manual':
            return JsonResponse({
                'success': False,
                'error': 'Receipt image is required for manual transfers'
            })
        
        # Auto-approve if still pending
        if withdrawal.status == 'pending':
            withdrawal.approved_by = request.user
            withdrawal.approved_at = timezone.now()
        
        # Save receipt if provided
        if receipt_file:
            withdrawal.receipt_image = receipt_file
        
        # Complete the withdrawal
        result = DonationService.complete_withdrawal(
            withdrawal=withdrawal,
            performed_by=request.user,
            receipt_url=withdrawal.receipt_image.url if withdrawal.receipt_image else None
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'Withdrawal {withdrawal.reference} marked as completed',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to complete'),
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def bulk_process(request):
    """Process multiple withdrawals at once"""
    try:
        data = json.loads(request.body)
        withdrawal_ids = data.get('withdrawal_ids', [])
        action = data.get('action', 'process')  # 'approve', 'process', 'reject'
        
        results = []
        
        for wid in withdrawal_ids:
            try:
                withdrawal = DonationWithdrawal.objects.get(pk=wid)
                
                if action == 'approve':
                    if withdrawal.status == 'pending':
                        withdrawal.status = 'approved'
                        withdrawal.approved_by = request.user
                        withdrawal.approved_at = timezone.now()
                        withdrawal.save()
                        results.append({'id': wid, 'success': True, 'message': 'Approved'})
                    else:
                        results.append({'id': wid, 'success': False, 'message': f'Cannot approve: {withdrawal.status}'})
                
                elif action == 'process':
                    if withdrawal.status in ['pending', 'approved']:
                        # Auto-approve first
                        if withdrawal.status == 'pending':
                            withdrawal.status = 'approved'
                            withdrawal.approved_by = request.user
                            withdrawal.approved_at = timezone.now()
                            withdrawal.save()
                        
                        if withdrawal.recipient_bank_code and withdrawal.recipient_account:
                            result = DonationService.initiate_gateway_transfer(
                                withdrawal=withdrawal,
                                performed_by=request.user
                            )
                            results.append({
                                'id': wid,
                                'success': result['success'],
                                'message': result.get('message') or result.get('error')
                            })
                        else:
                            results.append({
                                'id': wid,
                                'success': False,
                                'message': 'Missing bank code or account'
                            })
                    else:
                        results.append({'id': wid, 'success': False, 'message': f'Cannot process: {withdrawal.status}'})
                
                elif action == 'reject':
                    if withdrawal.status in ['pending', 'approved']:
                        withdrawal.status = 'rejected'
                        withdrawal.status_message = f'Bulk rejected by {request.user.get_full_name()}'
                        withdrawal.save()
                        results.append({'id': wid, 'success': True, 'message': 'Rejected'})
                    else:
                        results.append({'id': wid, 'success': False, 'message': f'Cannot reject: {withdrawal.status}'})
                        
            except DonationWithdrawal.DoesNotExist:
                results.append({'id': wid, 'success': False, 'message': 'Not found'})
            except Exception as e:
                results.append({'id': wid, 'success': False, 'message': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        
        return JsonResponse({
            'success': True,
            'message': f'{success_count}/{len(results)} processed successfully',
            'results': results,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def withdrawal_detail(request, withdrawal_id):
    """Get withdrawal details as JSON"""
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        data = {
            'id': str(withdrawal.id),
            'reference': withdrawal.reference,
            'amount': float(withdrawal.amount),
            'status': withdrawal.status,
            'status_display': withdrawal.get_status_display(),
            'transfer_method': withdrawal.transfer_method,
            'recipient_name': withdrawal.recipient_name,
            'recipient_account': withdrawal.recipient_account,
            'recipient_bank': withdrawal.recipient_bank,
            'recipient_bank_code': withdrawal.recipient_bank_code,
            'purpose': withdrawal.purpose,
            'description': withdrawal.description,
            'category': withdrawal.category,
            'initiated_by': withdrawal.initiated_by.get_full_name() if withdrawal.initiated_by else None,
            'approved_by': withdrawal.approved_by.get_full_name() if withdrawal.approved_by else None,
            'approved_at': withdrawal.approved_at.strftime('%Y-%m-%d %H:%M') if withdrawal.approved_at else None,
            'completed_at': withdrawal.completed_at.strftime('%Y-%m-%d %H:%M') if withdrawal.completed_at else None,
            'created_at': withdrawal.created_at.strftime('%Y-%m-%d %H:%M'),
            'gateway_transfer_code': withdrawal.gateway_transfer_code,
            'gateway_fee': float(withdrawal.gateway_fee),
            'status_message': withdrawal.status_message,
            'receipt_url': withdrawal.receipt_image.url if withdrawal.receipt_image else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def update_withdrawal(request, withdrawal_id):
    """Update withdrawal details (only if pending)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status not in ['pending']:
            return JsonResponse({
                'success': False,
                'error': 'Can only edit pending withdrawals'
            })
        
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'recipient_name' in data:
            withdrawal.recipient_name = data['recipient_name']
        if 'recipient_account' in data:
            withdrawal.recipient_account = data['recipient_account']
        if 'recipient_bank_code' in data:
            withdrawal.recipient_bank_code = data['recipient_bank_code']
            withdrawal.recipient_bank = dict(DonationWithdrawal.BANK_CHOICES).get(
                data['recipient_bank_code'], data['recipient_bank_code']
            )
        if 'purpose' in data:
            withdrawal.purpose = data['purpose']
        if 'description' in data:
            withdrawal.description = data['description']
        if 'category' in data:
            withdrawal.category = data['category']
        if 'transfer_method' in data:
            withdrawal.transfer_method = data['transfer_method']
        
        withdrawal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Withdrawal updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def finalize_transfer_otp(request, withdrawal_id):
    """
    Finalize a transfer that requires OTP verification.
    This is called when Paystack requires OTP to complete the transfer.
    """
    try:
        withdrawal = get_object_or_404(DonationWithdrawal, pk=withdrawal_id)
        
        if withdrawal.status != 'processing':
            return JsonResponse({
                'success': False,
                'error': f'Cannot finalize: status is {withdrawal.get_status_display()}'
            })
        
        if not withdrawal.gateway_transfer_code:
            return JsonResponse({
                'success': False,
                'error': 'No transfer code found'
            })
        
        data = json.loads(request.body) if request.body else {}
        otp = data.get('otp', '').strip()
        
        if not otp:
            return JsonResponse({
                'success': False,
                'error': 'OTP is required'
            })
        
        # Finalize with OTP
        result = DonationService.finalize_transfer_with_otp(
            withdrawal=withdrawal,
            otp=otp
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_POST
def sync_pending_transfers(request):
    """
    Check all pending/processing gateway transfers and update their status.
    This syncs with Paystack API to get the latest transfer status.
    """
    from django.db.models import Q
    
    try:
        # Find all processing gateway transfers with transfer codes
        pending_withdrawals = DonationWithdrawal.objects.filter(
            Q(status='processing') | Q(status='approved'),
            transfer_method='gateway',
            gateway_transfer_code__isnull=False,
        ).exclude(
            gateway_transfer_code=''
        )
        
        results = {
            'total': pending_withdrawals.count(),
            'completed': 0,
            'failed': 0,
            'still_pending': 0,
            'errors': 0,
            'details': []
        }
        
        for withdrawal in pending_withdrawals:
            try:
                result = DonationService.verify_transfer(withdrawal.gateway_transfer_code)
                
                if result['success']:
                    transfer_status = result.get('transfer_status', '').lower()
                    
                    if transfer_status == 'success':
                        DonationService.complete_gateway_transfer(
                            withdrawal=withdrawal,
                            transfer_status='success',
                            gateway_data=result.get('details')
                        )
                        results['completed'] += 1
                        results['details'].append({
                            'reference': withdrawal.reference,
                            'status': 'completed',
                            'message': 'Transfer completed successfully'
                        })
                        
                    elif transfer_status in ['failed', 'reversed']:
                        DonationService.complete_gateway_transfer(
                            withdrawal=withdrawal,
                            transfer_status='failed',
                            gateway_data=result.get('details')
                        )
                        results['failed'] += 1
                        results['details'].append({
                            'reference': withdrawal.reference,
                            'status': transfer_status,
                            'message': f'Transfer {transfer_status}'
                        })
                    else:
                        results['still_pending'] += 1
                        results['details'].append({
                            'reference': withdrawal.reference,
                            'status': transfer_status,
                            'message': f'Still {transfer_status}'
                        })
                else:
                    results['errors'] += 1
                    results['details'].append({
                        'reference': withdrawal.reference,
                        'status': 'error',
                        'message': result.get('error', 'Verification failed')
                    })
                    
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'reference': withdrawal.reference,
                    'status': 'error',
                    'message': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'message': f"Sync complete: {results['completed']} completed, {results['failed']} failed, {results['still_pending']} pending, {results['errors']} errors",
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
