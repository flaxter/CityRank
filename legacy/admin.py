from mysite.legacy.models import *
from django.contrib import admin

#admin.site.register(Allcities)
admin.site.register(Data10)
admin.site.register(Data11)

class CitiesAdmin(admin.ModelAdmin):
	search_fields = ['name']
	list_filter = ['country']

admin.site.register(Allcities, CitiesAdmin)
