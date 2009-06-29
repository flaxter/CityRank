from django.shortcuts import render_to_response
from django import forms
from django.db.models import Q
from items.models import *
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
import utils
from utils import render_response, send_error_message
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
import csv
import gviz_api
from aggregator import aggregation_as_json, CitiesPerPage, DefaultSources, DefaultWeights, check_session_version
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
import pickle
from json_yui import DataTableYUI
from pngcanvas import PNGCanvas
import registration.signals 
from django.contrib.auth import login

#@login_required
#def user_activated(sender, **kwargs):
#	print "login", kwargs['user']
#	login(HttpRequest(), kwargs['user'])

#registration.signals.user_activated.connect(user_activated)

class ItemForm(forms.Form): 
	item = forms.CharField(max_length=100, required=False)
	country = forms.CharField(max_length=100, required=False)

def css_test(request):
	cookies = False
	if 'foobarval' in request.session:
		cookies = True
	val = request.session.get('foobarval', -1)
	request.session['foobarval'] = val + 1
	return render_response(request, 'css_test.html', {'cookies': cookies, 'val': val, 'foo': 23189.321839 })


def add_item(request):
	return render_response(request, 'items/add_item.html')

def add_item_handle(request):
	item_form = ItemForm(request.POST)
	if form.is_valid():
		print form.cleaned_data
	return render_response(request, 'base.html')

def index(request):
	check_session_version(request)
	sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)
	source_weights = request.session.get('source_weights', DefaultWeights)

	from django.conf import settings

        weightings = UserRanking.objects.all().order_by('-created')

        latest = weightings[0:15]

	return render_response(request, 'index.html', {'latest': latest })

def item_redirect(request, object_id=None):
	if object_id: 
		try:
			item = Item.objects.get(id=object_id)
			return HttpResponsePermanentRedirect('/items/' + item.name)
		except Item.DoesNotExist: 
			form = ItemForm()
			return render_response(request, 'items/item_search.html', {'form': form, 'title': u'Cities'})
	else: 
		form = ItemForm()
		return render_response(request, 'items/item_search.html', {'form': form, 'title': u'Cities'})


def item_detail_render(request, item, ajax):
	rankings = DataSource.objects.filter(Q(data__item=item) & Q(data__scheme__type='r') & Q(active=True))
	stats = DataSource.objects.filter(Q(data__item=item) & Q(data__scheme__type='s') & Q(active=True))

	try:
		ranked = [[ranking, int(Data.objects.get(item=item,source=ranking,scheme__type='r').value)] for ranking in rankings]
	except Data.MultipleObjectsReturned: # should never happen, but data might be imported wrong
		ranked = [[ranking, int(Data.objects.filter(item=item,source=ranking,scheme__type='r')[0].value)] for ranking in rankings]
		utils.send_error_message(request, Data.MultipleObjectsReturned)

	ranked.sort(lambda x, y: x[1] - y[1])

	try: 
		stats = [[stat, Data.objects.get(item=item,source=stat,scheme__type='s')] for stat in stats]
	except Data.MultipleObjectsReturned: # should never happen, unless stats have a problem (i.e. duplicate entries)
		stats = [[stat, Data.objects.filter(item=item,source=stat,scheme__type='s')[0]] for stat in stats]
		utils.send_error_message(request, Data.MultipleObjectsReturned)

	n = len(ranked)

	try:
		wiki_entry = WikiEntry.objects.get(item=item)
	except WikiEntry.DoesNotExist:
		wiki_entry = None

	if ajax:
		return render_response(request, 'items/item_detail_content.html', {'item': item, 'title': u'Cities', 'rankings': ranked, 'stats': stats  }) 

	highlight_item = page_containing_item = item_row = None
	if 'current_ranking' in request.session:
		try:
			rank = request.session['current_ranking'].index(item)
			page_containing_item = rank / CitiesPerPage
			item_row = rank - page_containing_item * CitiesPerPage
			highlight_item = True
		except ValueError:
			print "item", item, "not in", request.session['current_ranking']
	
	params = {'item': item, 'rankings': ranked, 'highlight_item': highlight_item, 'page': page_containing_item, 'row': item_row, 'wiki_entry': wiki_entry, 'stats': stats } 
	if(n > 5):
		params['strengths'] = ranked[:3]
		params['weaknesses'] = ranked[-3:]
		strengths = ranked[:3]
		weaknesses = ranked[-3:]
		
	return render_response(request, 'items/item_detail.html', params)

def item_detail(request, name='', object_id = None, ajax = False):
	if ajax:
		item = Item.objects.get(id=object_id)
		return item_detail_render(request, item, ajax)

	if request.method == 'POST':
		form = ItemForm(request.POST)
		if form.is_valid():
			item = form.cleaned_data['item']
			country = form.cleaned_data['country']

			items = countries = []	
			if item or country:
				qset = (Q(name__icontains=item) | Q(country__name__icontains=country))
				items = Item.objects.filter(qset)
			if country:
				qset = (Q(name__icontains=country))
				countries = Country.objects.filter(qset)
			return render_response(request, 'items.html', {'form': form, 'items': items, 'countries': countries, 'title': u'Cities'})
		else:
			return render_response(request, 'items/item_search.html', {'form': form, 'title': u'Cities'})
	elif name:
		items = Item.objects.filter(name__icontains=name)
		
		if items.count() == 1: 
			return item_detail_render(request, items[0], ajax)
		else:
			return HttpResponseRedirect("/items/")
	else:
		form = ItemForm()
		return render_response(request, 'items/item_search.html', {'form': form, 'title': u'Cities'})

def datasource_submit(request):
	class DataSourceSubmitForm(forms.Form): 
		name = forms.CharField(max_length=100, required=True)
		shortname = forms.CharField(max_length=100, required=True)
		source = forms.CharField(max_length=100, required=True)
		description = forms.CharField(widget=forms.widgets.Textarea())
		file = forms.FileField(required=True)

	form = DataSourceSubmitForm()

	return render_response(request, 'items/ranking_submit.html', {'form': form }) 

def datasource_csv(request, object_id):
	datasource = DataSource.objects.get(id=object_id)

	# first, sort all data by item, then for each item, retain original sort
	# order by data scheme
	itemdata = Data.objects.filter(source=datasource).order_by('item').order_by()
	schemes = DataScheme.objects.filter(source=datasource)
	n = itemdata.filter(scheme=schemes[0]).count()

#	return render_response(request, 'items/ranking_detail.html', {'datasource': datasource, 'titles': schemes, 'itemdata': itemdata, 'num_of_rows': n, 'title': datasource.name})

	response = HttpResponse(mimetype='text/csv')
	response['Content-Disposition'] = 'attachment; filename=' + datasource.name + '.csv'
	writer = csv.writer(response)
	
	writer.writerow(schemes)
	for row in itemdata:
		data = [r.value for r in row]
		writer.writerow(data)
	return response

# this should be in aggregate.py
# OLD!!!
def datasource_aggregate(request, id, include):
	# check it's a valid ID before cluttering the session
	source = DataSource.objects.get(id=id, datascheme__type='r', active=True)
	# this will raise DataSource.DoesNotExist on invalid ids--need to fail more gracefully?

	if source:
		sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)
		source_weights = request.session.get('source_weights', DefaultWeights)
		if include:
			sources_to_aggregate.add(source)
			source_weights[source] = 10 # default weight value
		else:
			sources_to_aggregate.remove(source)
			del source_weights[source]
		# need to catch KeyError	

		request.session['recent_submission'] = False 
		request.session['sources_to_aggregate'] = sources_to_aggregate
		request.session['source_weights'] = source_weights
		request.session['current_aggregation_json'] = None

	return datasource_list(request)

def datasource_list(request):
	check_session_version(request)
        sources = DataSource.objects.filter(datascheme__type='r', active=True).order_by('id')
	sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)

	for source in sources:
		source.aggregate = source in sources_to_aggregate

	return render_response(request, 'items/ranking_list.html', {'sources': sources, 'ranking_id': request.session.get('ranking_id', 100) + 1})

def item_list(request):
	items = Item.objects.all()

	class ItemsForm(forms.Form): 
		item = forms.ModelChoiceField(queryset=items)

	if request.method == 'POST':
		form = ItemsForm(request.POST)
		if form.is_valid():
			item = form.cleaned_data['item']
			#country = form.cleaned_data['country']
			return HttpResponseRedirect("/items/" + item.name)
	else:
		form = ItemsForm()

	countries = [c.tld.country_set.all()[0] for c in items]
	counts = [utils.sources_for_item(c).count() for c in items]

	json_map = utils.items_to_json(items, counts)

	return render_response(request, 'items/item_list.html', {'items': zip(items, countries),  'json_map': json_map, 'form': form })

def datasource_detail(request, id):
	datasource = DataSource.objects.get(id=id, active=True)
	schemes = DataScheme.objects.filter(source=datasource)
	
	datasource.aggregate = datasource in request.session.get('sources_to_aggregate', DefaultSources)

	itemdata = [Data.objects.filter(source=datasource, scheme=scheme).order_by('item') for scheme in schemes]

	schema = [('Item', 'string')]
	order = ['Item']

	i = 0
	for scheme in schemes:
		schema.append((scheme.type + str(i), 'number', scheme.description))
		order.append(scheme.type + str(i))
		i += 1

	def get_values(v):
		return [x.value for x in v]

	items = [v.item for v in itemdata[0]]
	ranks = [int(v.value) for v in itemdata[0]]
	values = [v.value for v in itemdata[1]]
	rankMax = [min(v,26) for v in ranks]

	formatted_names = ["<a href=\"/items/%s\">%s</a>" % (v.item.name, v.item.name) for v in itemdata[0]]
	names = [v.item.name for v in itemdata[0]]
	#print names
	itemdata = [get_values(v) for v in itemdata]	

	graph = zip(names, values)
	graph.sort(lambda x, y: int(y[1] - x[1]))

	table = DataTableYUI(schema, zip(formatted_names, *itemdata))
	graph_table = gviz_api.DataTable(schema, graph[:25])

	json_table = table.ToJSonYUI(columns_order=order, order_by=order[1])
	json_graph_table = graph_table.ToJSon(columns_order=order, order_by=order[1])
	json_map = utils.items_to_json(items, ranks, True)

	return render_response(request, 'items/ranking_detail.html', {'datasource': datasource, 'titles': schemes, 'json_table': json_table, 'json_graph_table': json_graph_table, 'json_map': json_map, 'title': datasource.name, 'item_data': zip(items, ranks, rankMax, values), 'ranking_id': request.session.get('ranking_id', 100) + 1})

@login_required
def profile(request):
	if request.session.get('anonymous_submit', False):
		request.session['anonymous_submit'] = False
		return HttpResponseRedirect("/ranking/submit/")
	else:
		print "request.user", request.user, request.user.username
		return HttpResponseRedirect("/accounts/profile/" + request.user.username)

def profile_view(request, username):
	viewed_user = User.objects.get(username=username)
	weightings = UserRanking.objects.filter(creator=viewed_user).order_by('-created')
	return render_response(request, 'items/profile.html', {'viewed_user': viewed_user, 'weightings': weightings})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreationForm()
    return render_response(request, "registration/register.html", {
        'form': form,
    })

@login_required
def bugs(request):
	class ContactForm(forms.Form):
		name = forms.CharField(initial=request.user.username, label="Name (optional)", required=False)
		email = forms.EmailField(label="E-mail (optional)", required=False)
		url = forms.URLField(initial=request.META.get('HTTP_REFERER'), required=False)
		message = forms.CharField(widget=forms.widgets.Textarea())
	
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			message = request.POST.get('message', '')
			name = request.POST.get('name', '')
			url = request.POST.get('url', '')
			subject = '[Django] Bug report for ' + url + ' user id = ' + str(request.user.id)
			message += '\n\n======== DEBUG INFORMATION ==========\n\nurl: ' + url + '\n\n\n### BEGIN pickle.dumps(request.session[sources_to_aggregate] ###\n' + pickle.dumps(request.session['sources_to_aggregate'], 0) + '\n\n\n### BEGIN pickle.dumps(request.session[weightings] ###\n' + pickle.dumps(request.session['source_weights'])
			from_email = request.POST.get('email', '')
			send_mail(subject, message, '%s <%s>' % (name, from_email), ['itemrankch@gmail.com'])
			return render_response(request, 'bugs_thanks.html', {'form': form, 'url': url})
		else:
			return render_response(request, 'bugs.html', {'form': form})
	else:
		form = ContactForm() 
		return render_response(request, 'bugs.html', {'form': form})


def colors_css(request):
	data = DataSourceColor.objects.all()
	return render_response(request, 'colors.css', {'data': data})
