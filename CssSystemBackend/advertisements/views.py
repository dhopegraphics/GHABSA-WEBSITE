from rest_framework.generics import ListAPIView
from advertisements.repository import AdsRepository
from advertisements.serializers import AdsSerializer

# Create your views here.


class GetAdsListView(ListAPIView):
    repo = AdsRepository
    queryset = repo.get_all_ads()
    serializer_class = AdsSerializer
