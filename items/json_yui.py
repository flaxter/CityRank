from gviz_api import *
from items.models import Item

class DataTableYUI(DataTable):
#  def __init__(self, schema, data):
#	self.
  def ToJSonYUI(self, columns_order=None, order_by=(), include_index = False):
    """Writes a JSON string that can be used in a JS DataTable constructor.

    This method writes a JSON string that can be passed directly into a Yahoo!
    UI DataTable constructor. Use this output if you are
    hosting the visualization HTML on your site, and want to code the data
    table in Python. Pass this string into the

!    google.visualization.DataTable constructor, e.g,:
!      ... on my page that hosts my visualization ...
!      google.setOnLoadCallback(drawTable);
!      function drawTable() {
!        var data = new google.visualization.DataTable(_my_JSon_string, 0.5);
!        myTable.draw(data);
!      }

    Args:
      columns_order: Optional. Specifies the order of columns in the
                     output table. Specify a list of all column IDs in the order
                     in which you want the table created.
                     Note that you must list all column IDs in this parameter,
                     if you use it.
      order_by: Optional. Specifies the name of the column(s) to sort by.
                Passed as is to _PreparedData().

    Returns:
      A JSon constructor string to generate a JS DataTable with the data
      stored in the DataTable object.
      Example result (the result is without the newlines):
!       {cols: [{id:'a',label:'a',type:'number'},
!               {id:'b',label:'b',type:'string'},
!              {id:'c',label:'c',type:'number'}],
!        rows: [{c:[{v:1},{v:'z'},{v:2}]}, c:{[{v:3,f:'3$'},{v:'w'},{v:null}]}]}

    Raises:
      DataTableException: The data does not match the type.
    """
    if columns_order is None:
      columns_order = [col["id"] for col in self._DataTable__columns]
    col_dict = dict([(col["id"], col) for col in self._DataTable__columns])

    # Creating the columns jsons
#    cols_jsons = ["{id:'%(id)s',label:'%(label)s',type:'%(type)s'}" %
#                  col_dict[col_id] for col_id in columns_order]
    cols_defns = ["{key:'%(id)s',label:'%(label)s',sortable:true, maxAutoWidth:100, formatter:\"%(type)sFormatter\"}" %
                  col_dict[col_id] for col_id in columns_order]

    # for yahoo, make it much simpler
    cols_jsons = ["'%(id)s'" %
                  col_dict[col_id] for col_id in columns_order]

    # Creating the rows jsons
    rows_jsons = []
    index = 1


    for row in self._PreparedData(order_by):
      cells_jsons = []
      for col in columns_order:
        # We omit the {v:null} for a None value of the not last column
        value = row.get(col, None)
	if include_index and col == 'index':
            cells_jsons.append(u"index: %d" % index)
            index += 1
	elif value is None and col != columns_order[-1]:
            cells_jsons.append(u"%s: '<span class=\"empty\">-</span>'" % col) # TO BE FIXED
        else:
	  if type(value) == Item:
	          value = self.SingleValueToJS(unicode(value.name), col_dict[col]["type"])
	  else:
	          value = self.SingleValueToJS(value, col_dict[col]["type"])

          if isinstance(value, tuple):
		    # We have a formatted value as well
            #cells_jsons.append("{v:%s,f:%s}" % value) # TO BE FIXED
            cells_jsons.append(u"%s: %s" % (col, value[0]))
          else:
            cells_jsons.append(u"%s: %s" % (col, value))

#      if include_index:
#        cells_jsons.append(u"index: %d" % index)
#        index += 1

      rows_jsons.append(u"{%s}" % u",".join(cells_jsons))

    # We now join the columns jsons and the rows jsons
    json = u"{'fields': [%s], 'columns': [%s], 'Result': [%s]}" % (u",".join(cols_jsons), u",".join(cols_defns), u",".join(rows_jsons))
    return json
