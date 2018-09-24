# create reports of Items

from inventory.models import Item, Category, Transaction
from flask import Response,g
from datetime import datetime
import csv
from io import StringIO
from collections import OrderedDict

def stock_on_hand_report():
    """Create a CSV report of the current state of Item"""
    out = ''
    
    #import pdb;pdb.set_trace()
    items = Item(g.db)
    recs = items.select()
    if recs:
        fields_to_ignore = ['id','cat_id','description']
        fields = recs[0]._fields # a tuple
        fieldnames = [s for s in fields if s not in fields_to_ignore ]
        extras = []
        extras.append('category')
        extras.append('added')
        extras.append('used')
        extras.append('on hand')
        fieldnames.extend(extras)
    
        output = StringIO()
        with output as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for rec in recs:
                temp_row = rec._asdict()
                # temp_row is an orderedDict and elements can't be removed
                row = OrderedDict()
                for key, value in temp_row.items():
                    if key not in fields_to_ignore:
                        row[key] = value
                    
                row[extras[0]] = items.category(rec.cat_id)
                row[extras[1]] = items.additions(rec.id)
                row[extras[2]] = items.subtractions(rec.id)
                row[extras[3]] = items.stock_on_hand(rec.id)
                writer.writerow(row)
                    
            out = output.getvalue()

            
    name = 'stock_report_{}'.format(datetime.now().strftime('%Y%m%d_%H%M'))
    return send_as_file(out,name=name,ext='csv')
    
def send_as_file(out,name='report',ext='csv'):
    #send the report
    resp = Response(out)
    resp.headers['content-type'] = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename="{}.{}"'.format(name,ext)
    resp.headers['Content-Type'] = 'application/{}'.format(ext)
    return resp
    