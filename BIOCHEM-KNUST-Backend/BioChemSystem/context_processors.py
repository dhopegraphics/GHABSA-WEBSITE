"""
Context processors for BioChemSystem project.
Makes certain variables available to all templates.
"""
from django.conf import settings


def google_maps_api_key(request):
    """
    Add Google Maps API key to template context.
    This makes GOOGLE_MAPS_API_KEY available in all templates.
    """
    return {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
    }


def brand_context(request):
    """
    Add brand values to the context of templates rendered via Django's
    normal RequestContext (e.g. admin views). Templates rendered via
    render_to_string() outside a request (emails, SMS, background jobs)
    must use BioChemSystem.config.brand.get_brand_context() directly instead.
    """
    from BioChemSystem.config.brand import get_brand_context
    return get_brand_context()
