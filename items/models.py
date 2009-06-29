from django.db import models
from django.contrib.auth.models import User

# Uniquely identifies country/state/item states
# will soon be deprecated
class TLD(models.Model):
	def __unicode__(self):
		return self.tld
	tld = models.CharField(max_length=5)

# Countries can have multiple names--they are stored here and associated with 
# a TLD, which is unique
# will soon be deprecated
class Country(models.Model):
	def __unicode__(self):
		return self.name
	name = models.CharField(max_length=255)
	tld = models.ForeignKey(TLD)
	class Meta:
		ordering = ["name"]

class Item(models.Model):
	def __unicode__(self):
		return self.name
	def get_absolute_url(self):
		return "/items/" + self.name
	def full(self):
		country = self.tld.country_set.all()[0] 
		if self.name == country.name:
			return self.name
		else:
			return u"%s, %s" % (self.name, country.name)

	name = models.CharField(max_length=255)
	tld = models.ForeignKey(TLD, blank=True, null=True)
	lat = models.FloatField()
	long = models.FloatField()
	class Meta:
		ordering = ["name"]

class Category(models.Model):
	def __unicode__(self):
		return self.name
	name = models.CharField(max_length=255)

class DataSource(models.Model):
	def __unicode__(self):
		return "%s - %s" % (self.shortname, self.name)
	name = models.CharField(max_length=255)
	shortname = models.CharField(max_length=63)
	source = models.CharField(max_length=255) # should be renamed
	description = models.TextField()
	category = models.ForeignKey(Category)
	creator = models.ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	active = models.BooleanField()

	class Meta:
		ordering = ["name"]

class DataSourceColor(models.Model):
	def __unicode__(self):
		return "%s is %s" % (self.datasource, self.color)
	def color_as_array(self):
		return [int('0x' + self.color[0] + self.color[1], 16), int('0x' + self.color[2] + self.color[3], 16), int('0x' + self.color[4] + self.color[5], 16), 0xff] # is this as efficient as it could be?
	datasource = models.ForeignKey(DataSource, blank=True, null=True)
	color = models.CharField(max_length=6) # in hex-form, like ff0000 for red

class DataScheme(models.Model): 
	def __unicode__(self):
		return "%s - %s" % (self.source.name, self.description)
	def get_absolute_url(self):
		if self.type == 's':
			return "/stats/%d" % self.source.id
		else:
			return "/indicators/%d" % self.source.id
	source = models.ForeignKey(DataSource)
	TYPES = (('r', 'rank'), ('w', 'weighted rank'), ('s', 'statistic'))
	type = models.CharField(max_length=1, choices=TYPES)
	description = models.CharField(max_length=255)
	decimals = models.IntegerField(null=True, blank=True) # number of decimals places to round to for display purposes
	sort_ascending = models.BooleanField() # True => ascending, False => descending

	class Meta:
		ordering = ["type"]
	

class Data(models.Model):
	def __unicode__(self):
		if self.scheme.type == 'r':
			return "%s ranks %d on %s" % (self.item.name, self.value, self.source.name)
		elif self.scheme.type == 'w':
			return "%s scores %f on %s" % (self.item.name, self.value, self.source.name)
		else:
			return "%s is %f in %s" % (self.item.name, self.value, self.source.name)
	source = models.ForeignKey(DataSource)	
	item = models.ForeignKey(Item)
	scheme = models.ForeignKey(DataScheme)
	value = models.FloatField()
	class Meta:
		ordering = ['value']

class ItemLink(models.Model):
	def __unicode__(self):
		return self.url

	item = models.ForeignKey(Item)
	url = models.URLField()
	source = models.CharField(max_length=32)
	embed = models.BooleanField()

	class Meta:
		ordering = ['source', 'item']

# used by UserRanking, a collection of Weightings submitted by a user
class Weighting(models.Model):
	def __unicode__(self):
		return self.source.shortname + u' = ' + unicode(self.weight)

	source = models.ForeignKey(DataSource)	
	weight = models.FloatField()

class UserRanking(models.Model):
	def __unicode__(self):
		return self.name

	name = models.CharField(max_length=255)
	description = models.TextField()
	weights = models.ManyToManyField(Weighting) 
	creator = models.ForeignKey(User) 
	created = models.DateTimeField(auto_now_add=True)
	json = models.TextField()

class WikiEntry(models.Model):
	def __unicode__(self):
		return self.item.name

	html = models.TextField()
	url = models.URLField()
	item = models.ForeignKey(Item)
