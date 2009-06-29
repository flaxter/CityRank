from django.conf.urls.defaults import *
from urank.views import *
from django.contrib import admin
from items.models import *
from items.views import *
from items.aggregator import aggregator_submit, gallery_detail, gallery_list, weighting, make_ranking_icon, explain
from items.stats import *
from items.data_submit import *
from items.item import search, add_item_submit
from django.contrib.auth.views import login, logout
from items.sitemaps import sitemaps
from settings import MEDIA_ROOT

admin.autodiscover()

items = {
	'queryset': Item.objects.all(),
}
#data_sources_and_data = {
#	'queryset': DataSource.objects.all(),
#	'extra_context': {'data': Data.objects.all()},
#}
data_sources = {
	'queryset': Item.objects.all(),
}

urlpatterns = patterns('',
	url(r'^indicators/$', datasource_list),
	url(r'^indicators/(?P<id>\d+)$', datasource_detail),
#	url(r'^indicators/(?P<object_id>\d+).csv$', datasource_csv, 'indicators'),
	url(r'^stats/$', stats_list),
	url(r'^stats/(?P<id>\d+)$', stats_detail),

	url(r'^data/submit/$', data_submit, {'indicator': True}),
	url(r'^data/submit/final/$', data_submit_final),

	url(r'google24ca1a3e76cf7e80.html', index),

	url(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),

	url(r'^items/$', item_list),
	url(r'^bugs/$', bugs),
	url(r'^bugs/submit/$', bugs),
	url(r'^accounts/logout/$', logout, {'next_page': '/'}), 
	url(r'^accounts/', include('registration.urls')),
	url(r'^accounts/login/$',  login), 
	url(r'^accounts/profile/$', profile),
	url(r'^accounts/profile/(?P<username>.+)/$', profile_view),
#	url(r'^add_item/$', add_item),
#	url(r'^add_item/submit/$', add_item_submit),
#	url(r'^css_test/$', css_test),
	url(r'^items/(?P<object_id>\d+)/$$', item_redirect),
	url(r'^items/(?P<name>.+)/$', item_detail),
	url(r'^itemsX/(?P<object_id>\d+)/$', item_detail, {'ajax': True}),
#	url(r'^search/?.+$', search),
	url(r'^$', index),
	url(r'^(?P<id>\d+)$', gallery_detail),
	url(r'^ranking\d+.png$', make_ranking_icon),
	url(r'^ranking_s\d+.png$', make_ranking_icon, {'icon': True}),
	url(r'^ranking/$', weighting),
	url(r'^explain/$', explain),
	url(r'^ranking/submit/$', aggregator_submit),
	url(r'^ranking/submit/final/$', aggregator_submit),
	url(r'^ranking/json/$', weighting, {'json': True}),
	url(r'^ranking/json/debug/$', weighting, {'json': True, 'debugging': True}),
	url(r'^gallery/(?P<id>\d+)/$', gallery_detail),
	url(r'^gallery/$', gallery_list),
#	url(r'^items/$', items),
	url(r'^about/$', 'django.views.generic.simple.direct_to_template', {'template': 'about.html'}),
	url(r'^learn/$', 'django.views.generic.simple.direct_to_template', {'template': 'more.html'}),
	url(r'.*academic paper$', 'django.views.generic.simple.direct_to_template', {'template': 'more.html'}),
        url(r'^contact/', include('contact_form.urls')),
#	url(r'^contact/$', 'django.views.generic.simple.direct_to_template', {'template': 'contact.html'}),
#	url(r'^media/ranking_icon(?P<path>.*)$', 'django.views.generic.simple.redirect_to', {'url': LOCAL_MEDIA_URL + 'ranking_icon%(path)s'}),
	#url(r'^media/css/screen/colors.css$', colors_css),
	url(r'^media/css/patches/iepngfix.htc$', 'django.views.generic.simple.direct_to_template', {'template': 'iepngfix.htc'}),
	url(r'^media/images/blank.gif$', 'django.views.static.serve', {'document_root': '/var/www/', 'path': 'media/images/blank.gif'}),
	#url(r'^media/(?P<path>.*)$', 'django.views.generic.simple.redirect_to', {'url': MEDIA_URL + '%(path)s'}),
	url(r'^media/(?P<path>.+)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}), #, 'path':  '%(path)s'}),

#	url(r'^admin/', include('django.contrib.admin.urls')),
    # Example:
    # (r'^urank/', include('urank.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
   (r'^admin/(.*)', admin.site.root),
#    url(r'^admin/', include('django.contrib.admin.urls')),
)

