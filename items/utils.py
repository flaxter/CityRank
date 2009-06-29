from django.template import RequestContext
from django.shortcuts import render_to_response
from items.models import *
from django.db.models import Q
from scipy import *
import gviz_api
from items.models import DataSource
from time import time
import cPickle
from django.core.mail import send_mail

CITYRANK_DATA_VERSION = 0.013
pickle_folder = "items/pickled/"

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

# given a list of items, convert it to a JSON repsosne for gviz_api
def items_to_json(items, values, format_for_gmap=False):
	if format_for_gmap:
		schema = [('Lat', 'number'), ('Lon', 'number'), 
			('Name', 'string')]
		order = ['Lat', 'Lon', 'Name']
		itemdata = [[c.lat, c.long, c.name] for c, v in zip(items, values)]
	else:
		schema = [('latitude', 'number'), ('longitude', 'number'), 
			('value', 'number'), ('HOVER', 'string')]
		order = ['latitude', 'longitude', 'value', 'HOVER']
		itemdata = [[c.lat, c.long, v, c.name] for c, v in zip(items, values)]

	table = gviz_api.DataTable(schema, itemdata)
	return table.ToJSon(columns_order=order, order_by=order[0])

def items_to_json_for_map(items, values):
	schema = [('latitude', 'number'), ('longitude', 'number'), 
		('value', 'number'), ('HOVER', 'string')]
	order = ['latitude', 'longitude', 'value', 'HOVER']

	def get_data(c, v):
		return [c.lat, c.long, v, c.name]

	itemdata = [get_data(c, v) for c, v in zip(items, values)]
	table = gviz_api.DataTable(schema, itemdata)
	return table.ToJSon(columns_order=order, order_by=order[0])

def sources_for_item(item):
	return DataSource.objects.filter(Q(data__item=item) & Q(data__scheme__type='r'))

# given data from the Data model, with one data source per row and one item 
# per column, sorted by rank, normalize the data so that the top item (1st 
# place) has the value in the variable first and the middle item 
# (shortest column / 2) has the value in the variable mid 
# if middle = -1, calculate it, otherwise use it

def normalize(data, middle):
	first = 100
	mid = 50

	r0 = data[0]
	r1 = data[middle]
	m = mid / (r0 - r1)
	b = first - m * r0
	return [m * x + b for x in data]

def calculate_normalization(data):
        lengths = [len(row) for row in data]
	middle = min(lengths) / 2

	slopes = [None] * len(data)
	intercepts = [None] * len(data)
	first = 100
	mid = 50

        for alpha in range(0,len(data)):
                # find m and b for f(x) = mx + b
                # for points (data[alpha][0], first) and (data[alpha][0], mid)

                r0 = data[alpha][0].value
                r1 = data[alpha][middle].value
                m = mid / (r0 - r1)
                b = first - m * r0

		slopes[alpha] = m
		intercepts[alpha] = b

		# WHY IS THIS HERE?! data doesn't get returned!
                for j in range(lengths[alpha]):
                       data[alpha][j].scaled_value = m  * data[alpha][j].value + b
	return slopes, intercepts, middle

def load_cached_data(filename):
	f = file(pickle_folder + "table_" + filename + ".txt", "r")
	table = cPickle.load(f)
	f.close()
	f = file(pickle_folder + "rows_" + filename + ".txt", "r")
	rows = cPickle.load(f)
	f.close()
	f = file(pickle_folder + "items_" + filename + ".txt", "r")
	items = cPickle.load(f)
	f.close()
	f = file(pickle_folder + "display_" + filename + ".txt", "r")
	display = cPickle.load(f)
	f.close()
	f = file(pickle_folder + "middle_" + filename + ".txt", "r")
	middle = cPickle.load(f)
	f.close()
	
	print "successfully LOAD_CACHED_DATA"

	return table, rows, items, display, middle

def save_cached_data(filename, table, rows, items, display, middle):
	print "saving cached data to", filename

	f = file(pickle_folder + "table_" + filename + ".txt", "w")
	cPickle.dump(table, f)
	f.close()
	f = file(pickle_folder + "rows_" + filename + ".txt", "w")
	cPickle.dump(rows, f)
	f.close()
	f = file(pickle_folder + "items_" + filename + ".txt", "w")
	cPickle.dump(items, f)
	f.close()
	f = file(pickle_folder + "display_" + filename + ".txt", "w")
	cPickle.dump(display, f)
	f.close()
	f = file(pickle_folder + "middle_" + filename + ".txt", "w")
	cPickle.dump(middle, f)
	f.close()

def fetch_data(sources, table=True):
	data = []
	ranks = []
	items = set()
	item_count = {}

	filename = "-".join([str(source.id) for source in sources])
	
#	if(len(sources) > 1): # just for now, don't load these from memory
	try:
		return load_cached_data(filename)
	except IOError:
		pass

	i = 0
	maxn = 0

        start = time()

	for source in sources:
		scheme = DataScheme.objects.filter(source=source, type='w')
		scheme2 = DataScheme.objects.filter(source=source, type='r')

		if scheme.count() > 0 and scheme2.count() > 0:
			d = Data.objects.filter(scheme=scheme[0]).order_by('-value')
			r = Data.objects.filter(scheme=scheme2[0]).order_by('value')
			if d:
				data.append(d) 
				ranks.append(r)

				for datum in d:
					items.add(datum.item)
					item_count[datum.item] = item_count.get(datum.item, 0) + 1
					
			#	data_len = d.count() #len(data[i])
			#	if data_len > maxn:
			#		maxn = data_len
				i += 1
		else:
			assert False

        totTime = time() - start
	print "loop1 end", totTime

        start = time()
	print "loop2 start"

	data_len = len(data)

	if data_len > 1: # if we're aggregating (i.e. data_len > 1) then we should remove items that only appear once
		for item in item_count:
			if item_count[item] == 1:
				items.remove(item)
				for i in range(data_len):
					data[i] = data[i].exclude(item=item)
					ranks[i] = ranks[i].exclude(item=item)

        totTime = time() - start
	print "loop2 end", totTime

	print "loop3 start"
        start = time()
	q = [len(d) for d in data]
	maxn = max(q)
        totTime = time() - start
	print "loop3 end", totTime

        totTime = time() - start
	print "calculate_normalization start"
	slopes, intercepts, middle = calculate_normalization(data)
        totTime = time() - start
	print "calc_normal end", totTime
	if table:
		cols = data_len
		items = list(items)
		rows = len(items)

		items.sort(key=lambda x: x.name)

		table = [[None] * cols for i in range(rows)]
		table2 = [[None] * cols for i in range(rows)]

		#	table2[i] = data.filter(item__in=items[i])

		print "rescale start"
        	totTime = time() - start
		for i in range(rows):
			for j in range(cols):
				try:
					table[i][j] = data[j].get(item__id=items[i].id)
					table[i][j].scaled_value = slopes[j] * table[i][j].value + intercepts[j]
                       			table[i][j].rank = ranks[j].get(item__id=items[i].id).value
				except Data.DoesNotExist:
					table[i][j] = None
		totTime = time() - start
		print "rescale end", totTime

		if(i == 1):
			display = zip(*data)
		else:
			display = map(None, *data)

		save_cached_data(filename, table, rows, items, display, middle)

		return table, rows, items, display, middle
	else:
		return data

def process(data, items, rankings, weights, numpairs):
	num_comparisons = [0] * numpairs
	A = [[0.0] * rankings for i in range(numpairs)]
	p0 = [0.0] * items # starting guess for solver
	num_items = [0] * items
	
	for alpha in range(rankings): 
		# need to include item 0, because we start with item 1 below
		if data[0][alpha]:
			p0[0] += weights[alpha] * data[0][alpha].scaled_value * 0.1
			num_items[0] += 1

		p = 0
		for i in range(1,items):
			if data[i][alpha]:
				p0[i] += weights[alpha] * data[i][alpha].scaled_value * 0.1
				num_items[i] += 1
			for j in range(i):
				# p = i * items + j FALSEFALSEFALSEFALSE!!! blkjdfsaljkdfa!
				if data[j][alpha] and data[i][alpha]:
					A[p][alpha] = weights[alpha] * (data[j][alpha].scaled_value - data[i][alpha].scaled_value) * 0.1
					num_comparisons[p] += 1
				else:
					A[p][alpha] = 0
				p += 1

	# return p0 (starting estimate), Ybar (see pg. 8 of paper), num_comparisons
	return [val / num for (val, num) in zip(p0, num_items)], \
		[sum(row) / num for (row, num) in zip(A, num_comparisons)], num_comparisons


def rank_suffix(n):
	if 10 < (n%100) and (n%100) < 14:
		return "th";

	suffixes = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]

	return suffixes[int(n) % 10]

def send_error_message(request, exception):
	subject = '[Django] Error ' + str(exception)
	message = 'On ' + request.path + ' ' + request.method + ' there was an error\n'
	send_mail(subject, message, 'itemrankch@gmail.com', ['itemrankch@gmail.com'])
