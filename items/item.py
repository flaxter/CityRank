from django.shortcuts import render_to_response
from django import forms
from django.db.models import Q
from items.models import *
from items.views import item_detail_render
import utils
from utils import render_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
import csv
import gviz_api
from aggregator import aggregation_as_json, CitiesPerPage, DefaultSources, DefaultWeights

def search(request):
	lat = request.GET.get('lat', '')
	long = request.GET.get('long', '')
	item = request.GET.get('item', '')
	tld = request.GET.get('tld', '')
	
	items = countries = []
	matching_item = None
	if item:
		qset = Q(name__icontains=item)
		items = Item.objects.filter(qset)
		if items.count() > 0:
			matching_item = items[0]

	country = None
	if tld:
		qset = (Q(tld__icontains=tld))
		tlds = TLD.objects.filter(qset)
		if(tlds.count() > 0):
			countries =  Country.objects.filter(tld=tlds[0])
			if countries.count() > 0:
				country = countries[0]

	#print "found", items, "matching", item
	if matching_item:
		return item_detail_render(request, matching_item, True)
	else:
		return add_item_form(request, lat, long, item, country)

class ItemForm(forms.Form):
	item = forms.CharField(label="Item")
	country = forms.ModelChoiceField(queryset=Country.objects.all())

def add_item_form(request, lat, long, item, country):
	countries = Country.objects.all()

	item_form = ItemForm()
	if item:
		item_form.fields['item'] = forms.CharField(initial=item)
	if country:
		item_form.fields['country'] = forms.ModelChoiceField(queryset=countries, initial=country.id)

	return render_response(request, 'items/add_item_form.html', {'lat': lat, 'long': long, 'item': item, 'country': country, 'form': item_form})

def add_item_submit(request):
	lat = request.GET.get('lat', '')
	long = request.GET.get('long', '')
	name = request.GET.get('item', '')
	country_id = request.GET.get('country', '')

	country = Country.objects.get(id=country_id)

	item = Item(name=name, lat=lat, long=long, tld=country.tld)
	item.save()
	
	return render_response(request, 'items/add_item_submit.html')
