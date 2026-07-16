from news.models import News


class NewsRepository:
    model = News.objects

    @classmethod
    def get_all(cls):
        """
        Get all blogs ordered by creation date (most recent first)
        """
        return cls.model.all().order_by('-created_at')

    @classmethod
    # get news or blog
    def get_news_blog(cls, news_id):
        try:
            return cls.model.get(news_id=news_id)
        except News.DoesNotExist:
            return None
