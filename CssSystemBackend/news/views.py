from news.serializers import NewsSerializer
from rest_framework.generics import ListAPIView
from news.repository import NewsRepository
# Create your views here.


class GetAllNewsViews(ListAPIView):
    repo  = NewsRepository
    queryset = repo.get_all()
    serializer_class = NewsSerializer



