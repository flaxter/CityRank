from models import *
from django import forms
import utils
from utils import render_response, CITYRANK_DATA_VERSION
from django.template.loader import render_to_string
import scipy.optimize
import leastsq
from time import time
import gviz_api
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponse, HttpResponseRedirect
import simplejson as jsona
from json_yui import DataTableYUI
from pngcanvas import PNGCanvas
import math

DefaultSources = []
DefaultWeights = {}
CitiesPerPage = 15

class DataSourceForm(forms.Form):
	def __init__(self, sources, *args, **kwargs):
		super(DataSourceForm, self).__init__(*args, **kwargs)

		i = 0
		for source in sources:
			n = source.data_set.count() / source.datascheme_set.count()
			label = "%s (%d)" % (source.description, n)
			self.fields['active' + str(source.id)] = \
				forms.BooleanField(label=label, required=False)
			self.fields['weight' + str(source.id)] = \
				forms.CharField(initial = u'1.0', required=False)
			i += 1

def current_aggregation_context(request):
	return {'current_aggregation_json': request.session.get('current_aggregation_json', None), 'current_aggregation_sources': request.session.get('sources_to_aggregate', DefaultSources)}


def explain(request):
	sources_to_aggregate = DataSource.objects.filter(id__in=[19,20,21,22])
	weights = {}
	for source in sources_to_aggregate:
		weights[source] = 10
	
        json_table, items, ranked, display, pairwise, after = aggregation_as_json(request, sources_to_aggregate, weights, include_all_sources=True, debugging=True)

	all_sources = DataSource.objects.filter(datascheme__type='r')
	for source in all_sources:
		source.aggregate = source in sources_to_aggregate

	ranking_id = request.session.get('ranking_id', 100) + 1
	request.session['ranking_id'] = ranking_id

	return render_response(request, 'items/explain.html', {'json_table': json_table, 'sources': sources_to_aggregate, 'items': items, 'pairwise': zip(items, pairwise), 'pairwise_after': zip(items, after), 'debugging': True, 'json_table': json_table, 'data':  map(None, ranked, display)  })
			

# current_item_rank is a (mutable) list [item, rank] 
# if it isn't None, rank is updated to the current item rank
def aggregation_as_json(request, selected_sources, source_weights, debugging = False, formfields = None, current_item_rank = None, include_all_sources = True, quick = True, compare1 = None, compare2 = None):
	if debugging:
		print "FOOBAR!!! aggregation_as_json!"
		print "selected_sources", selected_sources

	schema = [('Item', 'string'), ('Rank', 'number'), ('Latitude', 'number'), ('Longitude', 'number')]
	order = ['Item', 'Rank', 'Latitude', 'Longitude']

	if include_all_sources: 
		for source in selected_sources:
			name = 'rank' + str(source.id)
			schema.append((name, 'string'))
			order.append(name)

	schema.append(('index', 'number'))
	order.append('index')

	selected_sources_count = len(selected_sources)
	print "selected_sources_count = ", selected_sources_count

	if selected_sources_count == 0:
		table = DataTableYUI(schema, None)
		json_table = table.ToJSonYUI(columns_order=order, order_by=(order[1], "desc"), include_index=True)
		return json_table, None

	print "starting utils.fetch_Data!!!!!!!!!!!!!!!!!!!!!!!!!"
	start = time()
	table, rows, items, display, middle = utils.fetch_data(selected_sources)
	totTime = time() - start
	print "utils.fetch_data TOTAL TIME:", totTime

	using_old_ranking = False

	numitems = len(items)
	if 'old_ranking_values' in request.session and len(request.session['old_ranking_values']) == numitems and 'old_ranking' in request.session and len(request.session['old_ranking']) == numitems:
		schema.insert(2, ('Previous', 'string'))
		order.insert(2, 'Previous')
		using_old_ranking = True
	
	# nothing to aggregate, just zero or one data source
		
	pairs = numitems * (numitems - 1) / 2
	weights = [source_weights[source] for source in selected_sources]

	start = time()
	print "starting utils.process!!!!!!!!!!!!!!!!!!!!!!!!!"
	p0, Ybar, num_comparisons = utils.process(table, rows, selected_sources_count, weights, pairs)
	totTime = time() - start
	print "utils.process TOTAL TIME:", totTime
	final_wt = [scipy.sqrt(n) for n in num_comparisons]

	if debugging:
		print "To be passed into the C++ code"
		print "p = ", p0
		print "Ybar = ", Ybar
		print "wt = ", final_wt
		print "numitems = ", numitems
		print "numpairs = ", len(num_comparisons)

	if using_old_ranking and False:
		p0 = request.session['old_ranking_values']

	def ij_to_index(i, j):
		return i * (i - 1) / 2 + j

	compare1 = 10
	compare2 = 5
	# compare items indexed compare1 and compare2
	if debugging and compare1 and compare2 and compare2 < compare1:
		index = ij_to_index(compare1, compare2)
		#print "Comparing", items[compare1], items[compare2], " - ", Ybar[index]

	before = zip(p0, items)
	before.sort(key=lambda x: x[0], reverse=True)	

	start = time()
	print "starting!"
	p1 = [0.0] * numitems
	leastsq.optimize(numitems, pairs, p0, Ybar, final_wt, p1)
		
	totTime = time() - start
	print "\n\n### TOTAL TIME2:", totTime

	if compare1 and compare2:
		pass #print "Re-comparing", items[compare1], items[compare2], " - ", p1[compare1] - p1[compare2]

	pairwise = after = None
	if debugging: 
		pairwise = [[None] * numitems for i in range(numitems)]
		after = [[None] * numitems for i in range(numitems)]

		n = 0
		for i in range(numitems):
			after[i][i] = pairwise[i][i] = [0, '']
		for i in range(1, numitems):
			for j in range(i):
				pref1 = pref2 = ''
				if(Ybar[n] < 0): # negative value indicates i is preferred to j, set class for the td element so it is colored accordingly
					pref1 = 'row'
					pref2 = 'column'
				elif Ybar[n] > 0:
					pref1 = 'column'
					pref2 = 'row'

				pairwise[i][j] = [Ybar[n], pref1]
				pairwise[j][i] = [-1 * Ybar[n], pref2]

				if(p1[j] - p1[i] < 0): 
					pref1 = 'row'
					pref2 = 'column'
				else:
					pref1 = 'column'
					pref2 = 'row'

				after[i][j] = [p1[j] - p1[i], pref1]
				after[j][i] = [p1[i] - p1[j], pref2]
				n += 1

	assert len(p1) == numitems

	min_value = min(p1)
	values_range = max(p1) - min_value
	scalar = 100.0 / values_range

	# since there's a fair amount of error in our optimization algorithm
	# round to the nearest decimal so as not to have fake rankings appear
	p1 = [round((x - min_value) * scalar, 1) for x in p1]
	if debugging:
		print "Check against C++: ", p1

#	p1 = [round(x, 1) for x in p1]

	ranked = zip(p1, items)
	ranked.sort(key=lambda x: x[0], reverse=True)	

	request.session['current_ranking'] = list(map(None, *ranked)[1])

	i = -1
	if current_item_rank: # find out item's rank
		i = items.index(current_item_rank[0])	
		current_item = items[i] # "<span class=\"current_item\">%s</span>" % items[i]
#		items[i] = current_item

	if current_item_rank: # find out item's rank
		current_item_rank[1] = ranked.index((p1[i], current_item))

	if include_all_sources:
		for i in range(len(table)): # INEFFICIENT!!!
			for j in range(len(table[i])):
				if table[i][j]:
					if True: #table[i][j].scaled_value > 0:
						table[i][j] = "<span class=\"table-rank\">%d</span><span class=\"table-suffix\">%s</span> <span class=\"table-score\">%.02f</span>" % (table[i][j].rank, utils.rank_suffix(table[i][j].rank), table[i][j].scaled_value)
					else:
						table[i][j] = "<span class=\"table-rank\">%d</span><span class=\"table-suffix\">%s</span> <span class=\"table-score\">%.01f</span>" % (table[i][j].rank, utils.rank_suffix(table[i][j].rank), table[i][j].scaled_value)
				else:
					table[i][j] = None #(1000, '')


		latitude = [item.lat for item in items]
		longitude = [item.long for item in items]

		if using_old_ranking:
			ranked3 = zip(request.session['old_ranking'], p1) # OMG a terrible hack!
			ranked3.sort(key=lambda x: x[1], reverse=False)
			old_ranking = [r[0] for r in ranked3]
			item_names = [item.name for item in items]

			ranked2 = zip(item_names, p1, old_ranking, latitude, longitude)
		else:
			ranked2 = zip(items, p1, latitude, longitude)

		ranked2 = [a + tuple(d) for a, d in zip(ranked2, table)]
	else:
		ranked2 = zip(items, p1)

	ranked2.sort(key=lambda x: x[1], reverse=False)	
	
	request.session['old_ranking_values'] = p1
	request.session['old_ranking'] = [r[0] for r in ranked2]

	table = DataTableYUI(schema, ranked2)
	json_table = table.ToJSonYUI(columns_order=order, order_by=(order[1], "desc"), include_index=True)

#	for r, b in zip(ranked[:15], before[:15]):
#		print b, r

	# map(None, a, b) is a confusing way of zip(a,b), but only if len(a) == len(b)
	# otherwise zip truncates one of the lists (http://docs.python.org/library/functions.html#zip)
	# whereas map puts None's in instead

	return json_table, items, ranked, display, pairwise, after

def aggregator_submit(request):
	if not request.user.is_authenticated():
		request.session['anonymous_submit'] = True
		return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)

	if request.session.get('recent_submission', False):
		request.user.message_set.create(message=u'You just shared this ranking. In order to share another ranking you will need to <a href="/ranking/">change the weighting</a> or <a href="/indicators/">add or remove</a> different rankings.')
		request.session['anonymous_submit'] = False
		# THIS ISN'T working, how come?
		return HttpResponseRedirect('/accounts/profile')


	class UserRankingForm(forms.ModelForm):
		name = forms.CharField(label="Title of Ranking")
		class Meta:
			model = UserRanking
			fields = ('name', 'description')

	sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)
	source_weights = request.session.get('source_weights', DefaultWeights)

	print "here", request.method
	if request.method == 'POST': 
		print "foo"
		form = UserRankingForm(request.POST)
		if form.is_valid():
			instance = form.save(commit=False)

			instance.creator = request.user
			instance.json = request.session['current_aggregation_json']
			instance.save()
			for weight in request.session['weights_to_submit']:
				weight.save()
				instance.weights.add(weight)
			instance.save()
			request.session['recent_submission'] = True

			make_ranking_icon(request, instance.id)
			ranking_id = request.session.get('ranking_id', 100) + 1
			request.session['ranking_id'] = ranking_id

			return render_response(request, 'items/aggregator_submit_final.html', {'sources': sources_to_aggregate, 'weights': source_weights, 'id': instance.id, 'ranking_id': ranking_id })
		else:
			weights = [Weighting(source=source, weight=source_weights.get(source, 10)) for source in sources_to_aggregate]
			request.session['weights_to_submit'] = weights
	else: 
		print "bar"
		form = UserRankingForm()

		weights = [Weighting(source=source, weight=source_weights.get(source, 10)) for source in sources_to_aggregate]
		request.session['weights_to_submit'] = weights

	return render_response(request, 'items/aggregator_submit.html', {'weighting': weights, 'form': form, 'ranking_id': request.session.get('ranking_id', 100) })

def gallery_detail(request, id):
	weighting = UserRanking.objects.get(id=id)	
	weightings = weighting.weights.all()
	items = Item.objects.all()

#        counts = [utils.sources_for_item(c).count() for c in items]
#        json_map = utils.items_to_json(items, counts)

	return render_response(request, 'items/gallery_detail.html', {'weighting': weighting, 'weightings': weightings, 'json_table': weighting.json}) #, 'json_map': json_map}) #, 'item_data': zip(items, ranks, rankMax, values)})

def gallery_list(request):
	weightings = UserRanking.objects.all().order_by('-created')

	latest = weightings[0:10]

	feature_group = Group.objects.get(name=u'Featured')
	featured = UserRanking.objects.filter(creator__groups=feature_group).order_by('-created')

	return render_response(request, 'items/gallery_list.html', {'latest': latest, 'featured': featured })


def weighting(request, json = False, debugging = False):
	check_session_version(request)

	weights = request.session.get('source_weights', DefaultWeights)
	sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)

	if json:
		changed = False
		weightGet = request.GET.get('weights', '')
		if weightGet:
			values = weightGet.split(',')
			i = 0
			
			for source_weight in values:
				parse = source_weight.split('_')
				if len(parse) == 2:
					source_id = parse[0]
					value = parse[1]
					try:
						value = float(value)
						if value >= 0 and value <= 10:
							try:
								source = DataSource.objects.get(id=source_id)
								try: 	
									if weights[source] != value:
										weights[source] = value
										changed = True
								except KeyError: pass
							except DataSource.DoesNotExist: pass
					except ValueError: pass

		includeGet = request.GET.get('include', '')
		if includeGet: 
			id = includeGet.split(',')[0]
			try:
				source = DataSource.objects.get(id=id, datascheme__type='r')
				sources_to_aggregate.append(source)
				weights[source] = 10 # default weight value
				changed = True
			except DoesNotExist: pass

		toggleGet = request.GET.get('toggle', '')
		if toggleGet: 
			id = toggleGet.split(',')[0]
			try:
				source = DataSource.objects.get(id=id, datascheme__type='r')
				if source in sources_to_aggregate:
					sources_to_aggregate.remove(source)
					del weights[source]
				else:
					sources_to_aggregate.append(source)
					sources_to_aggregate.sort(key=lambda source: source.id)
					weights[source] = 10 # default weight value
				changed = True
			except DataSource.DoesNotExist: pass

		request.session['source_weights'] = weights
		request.session['sources_to_aggregate'] = sources_to_aggregate

		remove_all = request.GET.get('remove_all', '')
		if remove_all:
			request.session['source_weights'] = DefaultWeights
			request.session['sources_to_aggregate'] = DefaultSources
			sources_to_aggregate = request.session['sources_to_aggregate']
			weights = request.session['source_weights']
			changed = True

		request.session.save() # so it's available for the icon

		if changed or not 'current_aggregation_json' in request.session:
			request.session['current_aggregation_json'] = None
			request.session['recent_submission'] = False
			json_table = aggregation_as_json(request, sources_to_aggregate, weights, include_all_sources=True)[0]
			request.session['current_aggregation_json'] = json_table
			ranking_id = request.session.get('ranking_id', 100) + 1
			request.session['ranking_id'] = ranking_id 

		if debugging:
			return HttpResponse("Fresh data? %s\n\n %s" % (changed, request.session['current_aggregation_json']))
		else:
			return HttpResponse("%s" % (request.session['current_aggregation_json']), mimetype='application/json')

	else:
		all_sources = DataSource.objects.filter(datascheme__type='r')
		for source in all_sources:
			source.aggregate = source in sources_to_aggregate

		ranking_id = request.session.get('ranking_id', 100) + 1
		request.session['ranking_id'] = ranking_id 

		return render_response(request, 'items/weighting.html', {'sources': sources_to_aggregate, 'source_weights': weights, 'all_sources': all_sources, 'ranking_id': ranking_id }) 

def make_ranking_icon(request, id = None, icon = False):

	if id or icon: # make the smaller version for display (the id) or for saving to the server
		width = 80
		height = 40
	else:	
		width = 200
		height = 200

	colors = ([0x25, 0x67, 0x79, 0xff], [0xaf, 0xf3, 0x9b, 0xff], [0xed, 0x1e, 0x79, 0xff], [0x29, 0xaa, 0xe2, 0xff], [0x4d, 0x42, 0x4c, 0xff])

        weights = request.session.get('source_weights', DefaultWeights)
        sources_to_aggregate = request.session.get('sources_to_aggregate', DefaultSources)

	c = PNGCanvas(width,height)
	num_colors = len(colors)

#	f = open("/var/www/media/handle.png", "rb")
#	handle = PNGCanvas(12,12)
#	handle.load(f)
	
	num_sources = len(sources_to_aggregate)
	if num_sources == 0:
		return HttpResponse(mimetype='image/png', content=c.dump())

	bar_width = width / num_sources
	half = bar_width / 2

	i = 0
	for source in sources_to_aggregate:
		c.color = DataSourceColor.objects.get(datasource=source).color_as_array() #colors[i % num_colors]
		bar_height = height - height * (weights[source] / 10.0)
		c.filledRectangle(bar_width * i, bar_height, bar_width * (i + 1) - 1, height)
			
#		handle.copyRect(0,0,11,11,10,10,c) #int(bar_height + 6), bar_width * i + half,c)

		i += 1


	if id:
		f = open("/var/www/media/ranking_icons/icon%d.png" % id, "wb")
		f.write(c.dump())
		f.close()
	else:
		return HttpResponse(mimetype='image/png', content=c.dump())

def set_default_sources(request):	
	request.session['source_weights'] = DefaultWeights
	request.session['sources_to_aggregate'] = DefaultSources
	return # the code below is if you want to start with two indicators
		# but user tests suggest this is confusing

	source1 = DataSource.objects.filter(datascheme__type='r',active=True)[0]
	source2 = DataSource.objects.filter(datascheme__type='r',active=True)[1]

	request.session['sources_to_aggregate'] = [source1, source2]
	
	weights = {}
	weights[source1] = 10
	weights[source2] = 10
	request.session['source_weights'] = weights

def check_session_version(request):
	if request.session.get('version', 0.0) < CITYRANK_DATA_VERSION: # clear the session, start over
		request.session.clear()
		request.session['version'] = CITYRANK_DATA_VERSION

		set_default_sources(request)

