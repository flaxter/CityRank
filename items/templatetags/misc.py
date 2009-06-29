from django import template
import items.utils 

register = template.Library()

@register.simple_tag
def crumb():
  return "<span>&raquo;</span>";

@register.filter
def rank_suffix(n):
	return u"%d%s" % (n, items.utils.rank_suffix(n))

@register.filter
def addnewlineslashes(str):
  print "Here:", str
  return str.replace("\n", "\\n")

addnewlineslashes.needs_autoescape = False

@register.filter
def js_bool(value):
  return "true" if value else "false"

@register.filter
def number_format(number, decimals=0, alldigits=False, dec_point='.', thousands_sep=','):
    if decimals == None:
      alldigits = True
    if not alldigits:
	    try:
		number = round(float(number), decimals)
	    except ValueError:
		return number

    neg = number < 0
    integer, fractional = str(abs(number)).split('.')
    m = len(integer) % 3
    if m:
        parts = [integer[:m]]
    else:
        parts = []
    
    parts.extend([integer[m+t:m+t+3] for t in xrange(0, len(integer[m:]), 3)])
    
    if decimals:
        return '%s%s%s%s' % (
            neg and '-' or '', 
            thousands_sep.join(parts), 
            dec_point, 
            fractional.ljust(decimals, '0')[:decimals]
        )
    elif alldigits:
        return '%s%s%s%s' % (
            neg and '-' or '', 
            thousands_sep.join(parts), 
            dec_point, 
            fractional #.ljust(decimals, '0')[:decimals]
        )
    else:
        return '%s%s' % (neg and '-' or '', thousands_sep.join(parts))


