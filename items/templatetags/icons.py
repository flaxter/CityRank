from django import template

register = template.Library()

#@register.tag(name="exclude_ajax")
#def do_exclude_ajax(parser, token):
#	try:
#		tag_name, format_string = token.split_contents()
#	except ValueError:
#		msg = '%r tag requires a single argument' % token.contents[0]
#		raise template.TemplateSyntaxError(msg)
#	return 

@register.simple_tag
def include(id, color_class=True):
	# files should not be hardcoded! FIX this
	return "<a href=\"javascript:toggle_ranking(%d)\" class=\"indicator_color%d\"><img border=0 width=20 height=20 src=\"http://media.cityrank.ch/add.png\" alt=\"Include this ranking in your ranking\" id=\"toggle%d\" /></a>"  % (id, id, id)
include.needs_autoescape = False

@register.simple_tag
def exclude(id, color_class=True):
	# files should not be hardcoded! FIX this
	return "<a href=\"javascript:toggle_ranking(%d)\" class=\"indicator_color%d\"><img border=0 width=20 height=20 src=\"http://media.cityrank.ch/remove.png\" alt=\"Remove this ranking from your ranking\" id=\"toggle%d\" /></a>"  % (id, id, id)
exclude.needs_autoescape = False


# AHHHHHH, WHAT HAPPENED TO DRY?!

@register.simple_tag
def include2(id):
	return "<a href=\"javascript:toggle_ranking(%d)\"><img border=0 width=20 height=20 src=\"/media/add.png\" alt=\"Include this ranking in your ranking\" id=\"toggle%d\" /></a>"  % (id, id)

@register.simple_tag
def exclude2(id):
	return "<a href=\"javascript:toggle_ranking(%d)\"><img border=0 width=20 height=20 src=\"/media/remove.png\" alt=\"Remove this ranking from your ranking\" id=\"toggle%d\" /></a>"  % (id, id)

