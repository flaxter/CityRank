from items.models import *
from django import forms
from django.contrib.auth.decorators import login_required
import utils
from utils import render_response
import csv
from django.db.models import Q
import django.core.mail as mail #import send_mail, EmailMessage

@login_required
def data_submit(request, indicator=True):
	categories = Category.objects.all()
	data_type_list = [('0', u'Indicator (with ordinal ranks: 1st, 2nd, 3rd...)'), ('1', 'Statistics')]

	class DataSubmitForm(forms.Form): 
		name = forms.CharField(max_length=100, required=True)
		shortname = forms.CharField(max_length=100, required=True)
		source = forms.CharField(max_length=100, required=True)
		category = forms.ModelChoiceField(queryset=categories)
		type = forms.ChoiceField(choices=data_type_list)
		description = forms.CharField(widget=forms.widgets.Textarea())
		#text_delimiter = forms.CharField(max_length=1, initial=",")
		#quote_char = forms.CharField(max_length=1, initial='"')
		file = forms.FileField(required = True, label="File (must be less than 4mb)")

	if request.method == 'POST':
		form = DataSubmitForm(request.POST, request.FILES)
		if form.is_valid():
			return data_submit_handle(request, form)
	else:
		form = DataSubmitForm()

	return render_response(request, 'items/data_submit.html', {'form': form })

def data_submit_final(request):
	assert request.method == 'POST'
	assert 'new_stats' in request.session
	assert 'new_data_values' in request.session

	values = request.session['new_data_values']
	ranks = request.session['new_data_ranks']
	newStat = request.session['new_stats']
	items = [None] * len(values)

	for key, value in request.POST.items():
		if key[0] == 'c': # a item
			id = int(key.lstrip("item"))
			value = int(value)
			if value > -1: 
				items[id] = value
			else:
				items[id] = None

	source = DataSource(name=newStat['name'], shortname=newStat['shortname'], source=newStat['source'], description=newStat['description'], category=newStat['category'], creator=request.user, active=False)
	source.save()

	if newStat['indicator']:
		schemeW = DataScheme(source=source, type='w', description=newStat['data_label'])
		schemeR = DataScheme(source=source, type='r', description='Rank')
		schemeW.save()
		schemeR.save()

		for value, rank, item in zip(values, ranks, items):
			if item:
				matchedItem = Item.objects.get(id=item)
				
				datum = Data(source=source,scheme=schemeW, item=matchedItem, value=value)
				datum.save()

				datum = Data(source=source,scheme=schemeR, item=matchedItem, value=rank)
				datum.save()
	else:
		scheme = DataScheme(source=source, type='s', description=newStat['data_label'])
		scheme.save()

		for value, item in zip(values, items):
			if item:
				matchedItem = Item.objects.get(id=item)
				
				datum = Data(source=source,scheme=scheme, item=matchedItem, value=value)
				datum.save()
			
	return render_response(request, 'items/data_submit_final.html')

def data_submit_handle(request, form):
	request.session['new_stats'] = {}

	for key in form.cleaned_data:
		if not key == 'file':
			request.session['new_stats'][key] = form.cleaned_data[key]

	if form.cleaned_data['type'] == u'0': # an indicator is being submitted
		request.session['new_stats']['indicator'] = indicator = True
	else:
		request.session['new_stats']['indicator'] = indicator = False

	message = ''
	for key in form.cleaned_data:
		if not key == 'file':
			message += str(key) + ": " + str(request.session['new_stats'][key]) + '\n'
	name = request.user.username
	subject = '[CityRank.ch] Data submitted by ' + request.user.username
        from_email = '%s <%s>' % (name, request.user.email)
	
	if request.FILES['file'].size < 1024 * 1024 * 4:	
		fp = request.FILES['file'].read()
	
		em = mail.EmailMessage(subject=subject,from_email=from_email, body=message,to=['itemrankch@gmail.com'], attachments=[('attachment.txt', fp,'text/plain')])
		em.send()
	
		return render_response(request, 'items/data_submit_final.html')
	else:
		return render_response(request, 'items/data_submit_final.html', {'error': True})

#	request.session['new_stats'] = {'name': form.cleaned_data['name'],
#		'shortname': form.cleaned_data['shortname'],
#		'source': form.cleaned_data['source'],
#		'category': form.cleaned_data['category'],
#		'description': form.cleaned_data['description']}

#		name = forms.CharField(max_length=100, required=True)
#		shortname = forms.CharField(max_length=100, required=True)
#		source = forms.CharField(max_length=100, required=True)
#		category = forms.ModelChoiceField(queryset=categories)
#		type = forms.ChoiceField(choices=data_type_list)
#		description = forms.CharField(widget=forms.widgets.Textarea())
#		text_delimiter = forms.CharField(max_length=2, initial=",")
#		quote_char = forms.CharField(max_length=2, initial='"')
#		file = forms.FileField(required = True)

	

	file_r = request.FILES['file']
	d = request.session['new_stats']['text_delimiter'].encode('latin-1')
	q = request.session['new_stats']['quote_char'].encode('latin-1')

	parser = csv.reader(file_r, delimiter=d, quotechar=q)
	headers = parser.next()
	identified = [False] * len(headers)
	
	item_names = ["items", "item", "name"]
	country_names = ["countries", "country"]
	rank_names = ["rank", "index", "indicator"]
	
	item_col = country_col = rank_col = None
	
	i = 0
	headers_lower = [col.lower() for col in headers]

	for col in headers_lower:
		if col in item_names:
			item_col = i
			identified[i] = True
		elif col in country_names:
			country_col = i
			identified[i] = True
		elif col in rank_names:
			rank_col = i
			identified[i] = True
		i += 1
	
	# use the first unidentified column and the second if needed
	if indicator:
		if not rank_col:
			rank_col = identified.index(False)
			values_col = identified.index(False, rank_col + 1)
		else:
			values_col = identified.index(False, rank_col + 1)
	else:
		values_col = identified.index(False)
	request.session['new_stats']['data_label'] = headers[values_col]

	data = []
	numCities = 0

	allCities = [('-2', u'--- select item ---'), ('-1', '--- add a new item ---')] + ([(unicode(item.id), item.name) for item in Item.objects.all()])

	itemSelect = forms.Form()
	hiddenValues = forms.Form()
	
	if indicator: 
		hiddenRankValues = forms.Form()

	values = []
	ranks = []
	matches = []
	q = 0

	for row in parser:
		row = [col.decode('iso-8859-1') for col in row]
		item = row[item_col]
		qset = Q(name__icontains=item)

		possibilities = Item.objects.filter(qset)
#		if possibilities.count() != 1:
#			if country_col:
#				country = row[country_col]
#				countries = Country.objects.filter(name__icontains=country)
				
		if country_col:
			displayName = item + u", " + row[country_col]
		else:
			displayName = item

		hiddenValues.fields['value' + unicode(numCities)] = forms.CharField(initial=row[values_col], widget=forms.widgets.HiddenInput())
		if indicator:
			hiddenRankValues.fields['rank' + unicode(numCities)] = forms.CharField(initial=row[rank_col], widget=forms.widgets.HiddenInput())

		values.append(float(row[values_col]))
		if indicator:
			ranks.append(float(row[rank_col]))
		matches.append(False)

		row_dict = {'displayName': displayName, 'value': row[values_col]}
		if indicator:
			row_dict['rank'] = row[rank_col]
			row_dict['hiddenRank'] = hiddenRankValues.fields['rank' + unicode(numCities)] 
		
		if possibilities.count() == 0: # no matches
			itemSelect.fields[u'item' + unicode(numCities)] = forms.ChoiceField(choices=allCities, label=displayName, initial=allCities[0][0])
		elif possibilities.count() == 1: # a match!
			row_dict['item'] = possibilities[0]
			itemSelect.fields[u'item' + unicode(numCities)] = forms.ChoiceField(choices=allCities, label=displayName, initial=possibilities[0].id)
		#	print "possible", possibilities[0].id
			matches[numCities] = True
		else: # multiple matches!
			row_dict['choices'] = possibilities
			itemSelect.fields[u'item' + unicode(numCities)] = forms.ChoiceField(choices=allCities, label=displayName, initial=possibilities[0].id) 

		data.append(row_dict)

		numCities += 1

	request.session['new_data_values'] = values
	request.session['new_data_ranks'] = ranks
	print "vals", values
	print "ranks", ranks

	if indicator: 
		return render_response(request, 'items/data_submit_handle.html', 
			{'form': itemSelect, 'data': data, 'table': zip(data, itemSelect, matches, hiddenValues), 'indicator': True, 'column_label': request.session['new_stats']['data_label'] })
	else:
		return render_response(request, 'items/data_submit_handle.html', 
			{'form': itemSelect, 'data': data, 'table': zip(data, itemSelect, matches, hiddenValues), 'indicator': False, 'column_label': request.session['new_stats']['data_label'] })
