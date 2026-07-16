from rest_framework.throttling import UserRateThrottle


class ContactUsThrottle(UserRateThrottle):
    scope = "contact_us"
