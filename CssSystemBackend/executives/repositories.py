from executives.models import Executive


class ExecutiveRepo:
    model = Executive.objects

    @classmethod
    def get_all_active(cls):
        """Get all current/active executives"""
        # Order by position priority (lower = higher) then most recent office_from
        return cls.model.filter(is_active=True).select_related('position').order_by('position__priority', '-office_from')
    
    @classmethod
    def get_all_past(cls):
        """Get all past executives"""
        return cls.model.filter(is_active=False).select_related('position').order_by('position__priority', '-office_from')
    
    @classmethod
    def get_by_year(cls, year):
        """Get executives by office year (e.g., '2024/2025')"""
        return cls.model.filter(office_year=year).select_related('position').order_by('position__priority', '-office_from')
    
    @classmethod
    def get_available_years(cls):
        """Get all unique office years"""
        return cls.model.exclude(office_year__isnull=True).values_list('office_year', flat=True).distinct().order_by('-office_year')
