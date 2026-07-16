"""
Paystack Payment Gateway Implementation
"""
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from .gateway_base import (
    BasePaymentGateway,
    PaymentInitializationError,
    PaymentVerificationError,
    RefundError,
    WebhookVerificationError,
)


class PaystackGateway(BasePaymentGateway):
    """
    Paystack payment gateway implementation
    
    Supports:
    - Payment initialization
    - Payment verification
    - Refunds
    - Webhook handling
    """
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self, gateway_model):
        super().__init__(gateway_model)
        
        # Get API keys from config or settings
        self.secret_key = self.config.get('secret_key') or settings.PAYSTACK_SECRET_KEY
        self.public_key = self.config.get('public_key') or settings.PAYSTACK_PUBLIC_KEY
        
        # Set base URL based on test mode
        if self.is_test_mode:
            self.base_url = self.BASE_URL  # Paystack uses same URL for test/live
        else:
            self.base_url = self.BASE_URL
        
        # Request headers
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Paystack API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
        
        Returns:
            Dict: Response data
        
        Raises:
            PaymentGatewayException: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise PaymentInitializationError(f"Paystack API request failed: {str(e)}")
    
    def initialize_payment(
        self,
        amount: Decimal,
        email: str,
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        currency: str = 'GHS',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize payment with Paystack
        
        Paystack API: https://paystack.com/docs/api/transaction/#initialize
        """
        # Format amount (convert to pesewas for GHS)
        amount_in_pesewas = self.format_amount(amount)
        
        # Prepare request data
        data = {
            'email': email,
            'amount': amount_in_pesewas,
            'currency': currency,
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {},
        }
        
        # Add optional parameters
        if 'channels' in kwargs:
            data['channels'] = kwargs['channels']
        
        if 'split_code' in kwargs:
            data['split_code'] = kwargs['split_code']
        
        if 'subaccount' in kwargs:
            data['subaccount'] = kwargs['subaccount']
        
        if 'transaction_charge' in kwargs:
            data['transaction_charge'] = self.format_amount(kwargs['transaction_charge'])
        
        if 'bearer' in kwargs:
            data['bearer'] = kwargs['bearer']
        
        try:
            response = self._make_request('POST', '/transaction/initialize', data)
            
            if not response.get('status'):
                raise PaymentInitializationError(
                    response.get('message', 'Payment initialization failed')
                )
            
            response_data = response.get('data', {})
            
            return {
                'authorization_url': response_data.get('authorization_url'),
                'access_code': response_data.get('access_code'),
                'reference': response_data.get('reference'),
                'gateway_reference': response_data.get('reference'),
            }
        
        except Exception as e:
            raise PaymentInitializationError(f"Paystack initialization failed: {str(e)}")
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify payment with Paystack
        
        Paystack API: https://paystack.com/docs/api/transaction/#verify
        
        Paystack accepts either:
        - Transaction reference (e.g., TXN-XXX or their generated reference)
        - Transaction ID (numeric, shown as "Receipt Number" in dashboard)
        """
        try:
            response = self._make_request('GET', f'/transaction/verify/{reference}')
            
            if not response.get('status'):
                raise PaymentVerificationError(
                    response.get('message', 'Payment verification failed')
                )
            
            data = response.get('data', {})
            
            # Map Paystack status to our status
            paystack_status = data.get('status', '').lower()
            if paystack_status == 'success':
                status = 'success'
            elif paystack_status == 'failed':
                status = 'failed'
            elif paystack_status == 'abandoned':
                status = 'cancelled'
            else:
                status = 'pending'
            
            # Extract customer details
            customer = data.get('customer', {})
            
            # Parse amount
            amount = self.parse_amount(data.get('amount', 0))
            
            return {
                'status': status,
                'amount': amount,
                'currency': data.get('currency', 'GHS'),
                'paid_at': data.get('paid_at'),
                'gateway_reference': data.get('reference'),
                'transaction_id': str(data.get('id', '')),  # Paystack's internal transaction ID
                'customer': {
                    'email': customer.get('email'),
                    'name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    'phone': customer.get('phone'),
                    'customer_code': customer.get('customer_code'),
                },
                'channel': data.get('channel'),
                'metadata': data.get('metadata', {}),
                'gateway_response': data,
                'ip_address': data.get('ip_address'),
                'fees': self.parse_amount(data.get('fees', 0)),
                'authorization': data.get('authorization', {}),
            }
        
        except Exception as e:
            raise PaymentVerificationError(f"Paystack verification failed: {str(e)}")
    
    def process_refund(
        self,
        transaction_reference: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process refund with Paystack
        
        Paystack API: https://paystack.com/docs/api/refund/#create
        """
        # Prepare request data
        data = {
            'transaction': transaction_reference,
        }
        
        # Add amount for partial refund
        if amount is not None:
            data['amount'] = self.format_amount(amount)
        
        # Add reason
        if reason:
            data['customer_note'] = reason
        
        # Add merchant note
        if 'merchant_note' in kwargs:
            data['merchant_note'] = kwargs['merchant_note']
        
        try:
            response = self._make_request('POST', '/refund', data)
            
            if not response.get('status'):
                raise RefundError(
                    response.get('message', 'Refund processing failed')
                )
            
            refund_data = response.get('data', {})
            
            # Map Paystack refund status
            paystack_status = refund_data.get('status', '').lower()
            if paystack_status in ['processed', 'success']:
                status = 'success'
            elif paystack_status == 'failed':
                status = 'failed'
            else:
                status = 'pending'
            
            return {
                'status': status,
                'refund_reference': str(refund_data.get('id')),
                'amount': self.parse_amount(refund_data.get('amount', 0)),
                'currency': refund_data.get('currency', 'GHS'),
                'gateway_response': refund_data,
                'transaction_reference': refund_data.get('transaction_reference'),
            }
        
        except Exception as e:
            raise RefundError(f"Paystack refund failed: {str(e)}")
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify Paystack webhook signature
        
        Paystack sends webhooks with x-paystack-signature header
        """
        try:
            # Compute hash
            computed_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(computed_signature, signature)
        
        except Exception as e:
            raise WebhookVerificationError(f"Webhook verification failed: {str(e)}")
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Paystack webhook event
        
        Paystack webhook events: https://paystack.com/docs/api/webhook/
        """
        event_type = payload.get('event')
        data = payload.get('data', {})
        
        # Extract common fields
        reference = data.get('reference')
        status_map = {
            'charge.success': 'success',
            'charge.failed': 'failed',
            'refund.processed': 'success',
            'refund.failed': 'failed',
        }
        
        return {
            'event_type': event_type,
            'reference': reference,
            'status': status_map.get(event_type, 'pending'),
            'data': data,
            'amount': self.parse_amount(data.get('amount', 0)) if data.get('amount') else None,
            'currency': data.get('currency'),
            'customer_email': data.get('customer', {}).get('email'),
        }
    
    def get_transaction_status(self, reference: str) -> str:
        """
        Get current transaction status from Paystack
        """
        try:
            verification_result = self.verify_payment(reference)
            return verification_result.get('status', 'pending')
        except Exception:
            return 'failed'
    
    def get_banks(self, country: str = 'ghana') -> list:
        """
        Get list of supported banks (for bank transfers)
        
        Paystack API: https://paystack.com/docs/api/miscellaneous/#bank
        """
        try:
            response = self._make_request('GET', '/bank', {'country': country})
            
            if not response.get('status'):
                return []
            
            return response.get('data', [])
        
        except Exception:
            return []
    
    def resolve_account_number(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """
        Resolve bank account details
        
        Paystack API: https://paystack.com/docs/api/verification/#resolve-account
        """
        try:
            data = {
                'account_number': account_number,
                'bank_code': bank_code,
            }
            
            response = self._make_request('GET', '/bank/resolve', data)
            
            if not response.get('status'):
                return {}
            
            return response.get('data', {})
        
        except Exception:
            return {}
    
    # =========================================================================
    # TRANSFER METHODS (for seller payouts)
    # =========================================================================
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get Paystack account balance
        
        Paystack API: https://paystack.com/docs/api/miscellaneous/#check-balance
        
        Returns:
            Dict with balance info for each currency
        """
        try:
            response = self._make_request('GET', '/balance')
            
            if not response.get('status'):
                return {'success': False, 'message': response.get('message', 'Failed to fetch balance')}
            
            balances = response.get('data', [])
            
            # Parse balances - amounts are in pesewas/kobo
            result = {'success': True, 'balances': {}}
            for balance_data in balances:
                currency = balance_data.get('currency', 'GHS')
                result['balances'][currency] = {
                    'balance': self.parse_amount(balance_data.get('balance', 0)),
                    'currency': currency,
                }
            
            return result
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_mobile_money_providers(self, currency: str = 'GHS') -> list:
        """
        Get list of supported mobile money providers
        
        Paystack API: https://paystack.com/docs/api/miscellaneous/#bank
        """
        try:
            response = self._make_request('GET', '/bank', {
                'currency': currency,
                'type': 'mobile_money'
            })
            
            if not response.get('status'):
                return []
            
            return response.get('data', [])
        
        except Exception:
            return []
    
    def create_transfer_recipient(
        self,
        recipient_type: str,
        name: str,
        account_number: str,
        bank_code: str,
        currency: str = 'GHS',
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a transfer recipient (beneficiary)
        
        Paystack API: https://paystack.com/docs/api/transfer-recipient/#create
        
        Args:
            recipient_type: 'ghipss' for Ghana banks, 'mobile_money' for MoMo
            name: Recipient's name
            account_number: Bank account or mobile number
            bank_code: Bank code or telco code (MTN, VOD, ATL for Ghana MoMo)
            currency: Currency (default GHS)
            metadata: Optional metadata
        
        Returns:
            Dict with recipient_code on success
        """
        try:
            data = {
                'type': recipient_type,
                'name': name,
                'account_number': account_number,
                'bank_code': bank_code,
                'currency': currency,
            }
            
            if metadata:
                data['metadata'] = metadata
            
            response = self._make_request('POST', '/transferrecipient', data)
            
            if not response.get('status'):
                return {
                    'success': False,
                    'message': response.get('message', 'Failed to create recipient')
                }
            
            recipient_data = response.get('data', {})
            
            return {
                'success': True,
                'recipient_code': recipient_data.get('recipient_code'),
                'recipient_id': recipient_data.get('id'),
                'name': recipient_data.get('name'),
                'type': recipient_data.get('type'),
                'details': recipient_data.get('details', {}),
            }
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def initiate_transfer(
        self,
        amount: Decimal,
        recipient_code: str,
        reference: str,
        reason: Optional[str] = None,
        currency: str = 'GHS'
    ) -> Dict[str, Any]:
        """
        Initiate a single transfer
        
        Paystack API: https://paystack.com/docs/api/transfer/#initiate
        
        Args:
            amount: Amount to transfer
            recipient_code: Recipient code from create_transfer_recipient
            reference: Unique transfer reference (max 50 chars, alphanumeric + _ -)
            reason: Optional reason for transfer
            currency: Currency (default GHS)
        
        Returns:
            Dict with transfer details on success
        """
        try:
            # Amount in smallest denomination (pesewas)
            amount_in_pesewas = self.format_amount(amount)
            
            data = {
                'source': 'balance',
                'amount': amount_in_pesewas,
                'recipient': recipient_code,
                'reference': reference,
                'currency': currency,
            }
            
            if reason:
                data['reason'] = reason
            
            response = self._make_request('POST', '/transfer', data)
            
            if not response.get('status'):
                return {
                    'success': False,
                    'message': response.get('message', 'Transfer initiation failed')
                }
            
            transfer_data = response.get('data', {})
            
            return {
                'success': True,
                'transfer_code': transfer_data.get('transfer_code'),
                'reference': transfer_data.get('reference'),
                'status': transfer_data.get('status'),  # 'pending', 'success', 'failed', etc.
                'amount': self.parse_amount(transfer_data.get('amount', 0)),
                'currency': transfer_data.get('currency'),
                'message': response.get('message', 'Transfer initiated'),
            }
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def verify_transfer(self, reference: str) -> Dict[str, Any]:
        """
        Verify transfer status
        
        Paystack API: https://paystack.com/docs/api/transfer/#verify
        
        Args:
            reference: Transfer reference
        
        Returns:
            Dict with transfer status
        """
        try:
            response = self._make_request('GET', f'/transfer/verify/{reference}')
            
            if not response.get('status'):
                return {
                    'success': False,
                    'message': response.get('message', 'Transfer verification failed')
                }
            
            data = response.get('data', {})
            
            return {
                'success': True,
                'status': data.get('status'),  # 'pending', 'success', 'failed', 'reversed'
                'transfer_code': data.get('transfer_code'),
                'reference': data.get('reference'),
                'amount': self.parse_amount(data.get('amount', 0)),
                'currency': data.get('currency'),
                'recipient': data.get('recipient', {}),
            }
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def can_process_transfer(self, amount: Decimal, currency: str = 'GHS') -> Dict[str, Any]:
        """
        Check if we have sufficient balance to process a transfer
        
        Args:
            amount: Amount to transfer
            currency: Currency
        
        Returns:
            Dict with 'can_transfer' boolean and balance info
        """
        balance_result = self.get_balance()
        
        if not balance_result.get('success'):
            return {
                'can_transfer': False,
                'reason': 'Failed to check balance',
                'message': balance_result.get('message')
            }
        
        balances = balance_result.get('balances', {})
        currency_balance = balances.get(currency, {})
        available = currency_balance.get('balance', Decimal('0.00'))
        
        # Paystack charges ~GHS 5 per transfer (varies)
        # We'll add a buffer for fees
        transfer_fee = Decimal('10.00')  # Conservative estimate
        required = amount + transfer_fee
        
        if available >= required:
            return {
                'can_transfer': True,
                'available_balance': available,
                'required_amount': required,
                'transfer_fee_estimate': transfer_fee
            }
        else:
            return {
                'can_transfer': False,
                'available_balance': available,
                'required_amount': required,
                'shortfall': required - available,
                'reason': 'Insufficient balance in Paystack account'
            }
