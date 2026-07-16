"""
Currency conversion and exchange rate views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from payments.models import Currency
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_currencies(request):
    """
    Get all active currencies with their exchange rates
    
    Returns:
    {
        "currencies": [
            {
                "code": "GHS",
                "name": "Ghana Cedis",
                "symbol": "₵",
                "exchange_rate": "1.000000",
                "is_base": true
            },
            ...
        ],
        "base_currency": "GHS"
    }
    """
    try:
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        base_currency = Currency.objects.filter(is_base_currency=True).first()
        
        currency_data = []
        for currency in currencies:
            currency_data.append({
                'code': currency.code,
                'name': currency.name,
                'symbol': currency.symbol,
                'exchange_rate': str(currency.exchange_rate),
                'is_base': currency.is_base_currency,
            })
        
        return Response({
            'currencies': currency_data,
            'base_currency': base_currency.code if base_currency else 'GHS'
        })
    
    except Exception as e:
        logger.exception(f"Error fetching currencies: {str(e)}")
        return Response({
            'error': 'Failed to fetch currencies'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def convert_currency(request):
    """
    Convert amount between currencies
    
    Request:
    {
        "amount": "100.00",
        "from_currency": "GHS",
        "to_currency": "USD"
    }
    
    Response:
    {
        "original_amount": "100.00",
        "converted_amount": "8.33",
        "from_currency": "GHS",
        "to_currency": "USD",
        "exchange_rate": "0.083333"
    }
    """
    try:
        amount = Decimal(request.data.get('amount', '0'))
        from_currency_code = request.data.get('from_currency', 'GHS')
        to_currency_code = request.data.get('to_currency', 'USD')
        
        # Get currencies
        try:
            from_currency = Currency.objects.get(code=from_currency_code, is_active=True)
            to_currency = Currency.objects.get(code=to_currency_code, is_active=True)
        except Currency.DoesNotExist as e:
            return Response({
                'error': f'Currency not found: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert to base currency (GHS) first, then to target currency
        # amount_in_base = amount / from_currency_rate
        # converted_amount = amount_in_base * to_currency_rate
        
        if from_currency.is_base_currency:
            # From base to target
            converted_amount = amount * to_currency.exchange_rate
            exchange_rate = to_currency.exchange_rate
        elif to_currency.is_base_currency:
            # From source to base
            converted_amount = amount / from_currency.exchange_rate
            exchange_rate = Decimal('1.0') / from_currency.exchange_rate
        else:
            # From source to base, then base to target
            amount_in_base = amount / from_currency.exchange_rate
            converted_amount = amount_in_base * to_currency.exchange_rate
            exchange_rate = to_currency.exchange_rate / from_currency.exchange_rate
        
        return Response({
            'original_amount': str(amount),
            'converted_amount': str(converted_amount.quantize(Decimal('0.01'))),
            'from_currency': from_currency_code,
            'to_currency': to_currency_code,
            'exchange_rate': str(exchange_rate),
            'from_currency_symbol': from_currency.symbol,
            'to_currency_symbol': to_currency.symbol,
        })
    
    except Exception as e:
        logger.exception(f"Error converting currency: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
