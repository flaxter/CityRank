from urank.items.models import *
from django.contrib import admin
from django.db import connection
from items.models import *

admin.site.register(Country)
admin.site.register(TLD)
admin.site.register(DataScheme)
admin.site.register(DataSource)
admin.site.register(Category)
admin.site.register(UserRanking)
admin.site.register(Weighting)
admin.site.register(WikiEntry)
admin.site.register(DataSourceColor)

class ItemLinkAdmin(admin.ModelAdmin):
	def country(obj):
		return obj.item.tld.country_set.all()[0]
	country.short_description = 'Country'
	search_fields = ['item__name']
	list_filter = ['source']
	list_display = ['item', 'url', country]

class ItemAdmin(admin.ModelAdmin):
	def country(obj):
		countries = Country.objects.filter(tld = obj.tld)	
		countries = map(lambda x: x.name, countries)
		return reduce(lambda x, y: x + ', ' + y, countries)
	country.short_description = 'Country'
	search_fields = ['name']
#	list_filter = ['name']
#	list_filter = ['item__tld__']
	list_display = ['name', country, 'tld']

class DataAdmin(admin.ModelAdmin):
	search_fields = ['item__name']
	list_filter = ['source', 'scheme']
	list_display = ['item', 'value', 'source']

admin.site.register(Item, ItemAdmin)
admin.site.register(ItemLink, ItemLinkAdmin)
admin.site.register(Data, DataAdmin)
