# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class Allcities(models.Model):
    def __unicode__(self):
	return self.name
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=765, blank=True)
    country = models.CharField(max_length=12, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'allcities'

class Data10(models.Model):
    def __unicode__(self):
	return u'%s %d %d %f' % (self.cityname, self.cityid, self.rank, self.value)
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data10'

class Data11(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data11'

class Data12(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data12'

class Data13(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    dimension1 = models.FloatField(null=True, blank=True)
    dimension2 = models.FloatField(null=True, blank=True)
    dimension3 = models.FloatField(null=True, blank=True)
    dimension4 = models.FloatField(null=True, blank=True)
    dimension5 = models.FloatField(null=True, blank=True)
    dimension6 = models.FloatField(null=True, blank=True)
    dimension7 = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data13'

class Data14(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data14'

class Data15(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data15'

class Data16(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data16'

class Data17(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data17'

class Data18(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data18'

class Data19(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data19'

class Data20(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data20'

class Data21(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data21'

class Data9(models.Model):
    id = models.IntegerField(primary_key=True)
    cityname = models.CharField(max_length=765, blank=True)
    cityid = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'data9'

class Gawc(models.Model):
    name = models.TextField(blank=True)
    country = models.TextField(blank=True)
    worldcityness = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'gawc'

class Indices(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    source = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    class Meta:
        db_table = u'indices'

class Population(models.Model):
    name = models.TextField(blank=True)
    country = models.TextField()
    countrycode = models.TextField()
    lowercasename = models.TextField(blank=True)
    population = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'population'

class LegacyCityMap(models.Model):
	old = models.ForeignKey(Allcities)
	new = models.ForeignKey('cities.City')

