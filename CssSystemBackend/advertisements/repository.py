from advertisements.models import Advertisement


class AdsRepository:
    model = Advertisement.objects

    @classmethod
    def get_all_ads(cls):
        return cls.model.all()
