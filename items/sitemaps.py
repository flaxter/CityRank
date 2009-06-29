from django.contrib.sitemaps import Sitemap
from items.models import Item, DataSource, DataScheme


class ItemSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Item.objects.filter()

#    def lastmod(self, obj):
#        return obj.pub_date

class IndicatorSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return DataScheme.objects.filter(source__active=True)

#    def lastmod(self, obj):
#        return obj.pub_date

sitemaps = {'items': ItemSitemap, 'indicators': IndicatorSitemap}
