from django.shortcuts import render_to_response
from django import forms
from items.models import *
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from utils import render_response
import gviz_api
import utils
from aggregator import aggregation_as_json, CitiesPerPage, DefaultSources
from json_yui import DataTableYUI

def stats_list(request):
	sources = DataSource.objects.filter(datascheme__type='s')

	return render_response(request, 'items/stats_list.html', {'sources': sources})

def stats_detail(request, id):
	datasource = DataSource.objects.get(id=id)
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
	values = [v.value for v in itemdata[0]]
	decimals = schemes[0].decimals

	formatted_names = ["<a href=\"/items/%s\">%s</a>" % (v.item.name, v.item.name) for v in itemdata[0]]
	names = [v.item.name for v in itemdata[0]]

	itemdata = [get_values(v) for v in itemdata]	

	graph = zip(names, values)
	graph.sort(key=lambda x: x[1], reverse=(not schemes[0].sort_ascending))
		#graph.sort(lambda x, y: y[1] - x[1])
	order_string = "asc" if schemes[0].sort_ascending else "desc"

	table = DataTableYUI(schema, zip(formatted_names, *itemdata))

	graph_table = gviz_api.DataTable(schema, graph[:25])

	json_graph_table = graph_table.ToJSon(columns_order=order, order_by=(order[1], order_string))
	json_table = table.ToJSonYUI(columns_order=order, order_by=(order[1], order_string))
	json_map = utils.items_to_json(items, values, True)

	return render_response(request, 'items/stats_detail.html', {'datasource': datasource, 'titles': schemes, 'json_table': json_table, 'json_map': json_map, 'title': datasource.name, 'item_data': zip(items, values), 'json_graph_table': json_graph_table, 'decimals': decimals })

