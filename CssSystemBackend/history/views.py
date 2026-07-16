from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SocietyHistory
from .serializers import SocietyHistorySerializer, SocietyHistoryListSerializer


class SocietyHistoryListView(ListAPIView):
    """
    Get all published society history records
    Returns lighter serialization for list view performance
    """
    queryset = SocietyHistory.objects.filter(
        is_published=True
    ).prefetch_related('leaders', 'milestones').order_by('-start_date', 'order')
    serializer_class = SocietyHistoryListSerializer


class SocietyHistoryDetailView(RetrieveAPIView):
    """
    Get detailed information about a specific history record
    Includes all leaders and milestones
    """
    queryset = SocietyHistory.objects.filter(
        is_published=True
    ).prefetch_related('leaders', 'milestones')
    serializer_class = SocietyHistorySerializer
    lookup_field = 'history_id'


class SocietyHistoryByCategoryView(APIView):
    """
    Get history records filtered by category
    Categories: founding, administration, milestone, achievement, event, lecture
    """
    def get(self, request, category):
        valid_categories = ['founding', 'administration', 'milestone', 'achievement', 'event', 'lecture', 'other']
        
        if category not in valid_categories:
            return Response(
                {"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        histories = SocietyHistory.objects.filter(
            category=category,
            is_published=True
        ).prefetch_related('leaders', 'milestones').order_by('-start_date', 'order')
        
        serializer = SocietyHistoryListSerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SocietyHistoryByYearView(APIView):
    """
    Get history records filtered by session year
    Example: /history/year/2023/2024/
    """
    def get(self, request, year):
        histories = SocietyHistory.objects.filter(
            session_year=year,
            is_published=True
        ).prefetch_related('leaders', 'milestones').order_by('order')
        
        serializer = SocietyHistoryListSerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoryCategoriesView(APIView):
    """
    Get all available categories with their counts
    """
    def get(self, request):
        categories = SocietyHistory.objects.filter(
            is_published=True
        ).values_list('category', flat=True).distinct()
        
        category_data = []
        for cat in categories:
            count = SocietyHistory.objects.filter(category=cat, is_published=True).count()
            display_name = dict(SocietyHistory._meta.get_field('category').choices).get(cat, cat)
            category_data.append({
                'value': cat,
                'label': display_name,
                'count': count
            })
        
        return Response(category_data, status=status.HTTP_200_OK)


class HistoryYearsView(APIView):
    """
    Get all available session years
    """
    def get(self, request):
        years = SocietyHistory.objects.filter(
            is_published=True
        ).values_list('session_year', flat=True).distinct().order_by('-session_year')
        
        # Filter out None values
        years = [year for year in years if year]
        
        return Response({"years": years}, status=status.HTTP_200_OK)

