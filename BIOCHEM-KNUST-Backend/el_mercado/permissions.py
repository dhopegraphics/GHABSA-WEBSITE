"""
El Mercado Custom Permissions
=============================
Custom permission classes for the marketplace API.
"""

from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """
    Permission class that only allows sellers to access the view.
    """
    message = "You must be a registered seller to perform this action."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return hasattr(request.user, 'seller_profile') and \
               request.user.seller_profile.status == 'ACTIVE'


class IsSellerOwner(permissions.BasePermission):
    """
    Permission class that ensures the user owns the seller resource.
    """
    message = "You can only access your own seller resources."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'seller_profile'):
            return False
        
        # Check if the object is a Seller instance
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if the object belongs to the seller (e.g., Listing, Order)
        if hasattr(obj, 'seller'):
            return obj.seller == request.user.seller_profile
        
        return False


class IsBuyer(permissions.BasePermission):
    """
    Permission class that identifies the user as a buyer.
    Any authenticated user can be a buyer.
    """
    message = "You must be logged in to perform this action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsOrderParticipant(permissions.BasePermission):
    """
    Permission class that checks if the user is a participant in the order.
    Either as a buyer or as the seller.
    """
    message = "You must be a participant in this order."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is the buyer
        if obj.buyer == request.user:
            return True
        
        # Check if user is the seller
        if hasattr(request.user, 'seller_profile'):
            return obj.seller == request.user.seller_profile
        
        return False


class IsConversationParticipant(permissions.BasePermission):
    """
    Permission class that checks if the user is a participant in the conversation.
    """
    message = "You must be a participant in this conversation."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is the buyer
        if obj.buyer == request.user:
            return True
        
        # Check if user is the seller
        if hasattr(request.user, 'seller_profile'):
            return obj.seller == request.user.seller_profile
        
        return False


class IsReviewAuthor(permissions.BasePermission):
    """
    Permission class that checks if the user is the author of the review.
    """
    message = "You can only modify your own reviews."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        return obj.reviewer == request.user


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows sellers to modify, but anyone to read.
    """
    
    def has_permission(self, request, view):
        # Allow read-only methods for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Require seller for write operations
        if not request.user.is_authenticated:
            return False
        
        return hasattr(request.user, 'seller_profile') and \
               request.user.seller_profile.status == 'ACTIVE'


class IsApplicationOwner(permissions.BasePermission):
    """
    Permission class for seller applications.
    Users can only view/modify their own applications.
    """
    message = "You can only access your own applications."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff can access all applications
        if request.user.is_staff:
            return True
        
        return obj.user == request.user


class CanInitiateDispute(permissions.BasePermission):
    """
    Permission class that checks if the user can initiate a dispute.
    Only the buyer of an order can initiate a dispute.
    """
    message = "Only the buyer can initiate a dispute for this order."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For disputes, obj is the order
        return obj.buyer == request.user


class IsDisputeParticipant(permissions.BasePermission):
    """
    Permission class that checks if the user is involved in the dispute.
    """
    message = "You must be involved in this dispute."
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Check if user initiated the dispute
        if obj.initiated_by == request.user:
            return True
        
        # Check if user is the seller of the order
        if hasattr(request.user, 'seller_profile'):
            return obj.order.seller == request.user.seller_profile
        
        return False
