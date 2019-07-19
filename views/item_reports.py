# create reports of Items

from inventory.models import Item, Category, Transaction
from flask import Response,g
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.takeabeltof.jinja_filters import iso_date_string
from datetime import timedelta
import csv
from io import StringIO
from collections import OrderedDict

def stock_on_hand_report(start_date=None,end_date=None):
    """Create a CSV report of the current state of Item"""
    out = ''
    
    #import pdb;pdb.set_trace()
    items = Item(g.db)
    recs = items.select()
    # Default to reporting only for this year
    if start_date is None:
        start_date = local_datetime_now().replace(month=1,day=1)
    if end_date is None:
        end_date = local_datetime_now().replace(year=local_datetime_now().year,month=12,day=31)
        
    if recs:
        fields_to_ignore = ['id','cat_id','description']
        fields = recs[0]._fields # a tuple
        fieldnames = [s for s in fields if s not in fields_to_ignore ]
        extras = []
        extras.append('category')
        extras.append('prev soh')
        extras.append('added')
        extras.append('used')
        extras.append('lifo cost')
        extras.append('on hand')
        fieldnames.extend(extras)
    
        output = StringIO()
        with output as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            from shotglass2.shotglass import get_app_config
            app_config = get_app_config()
            row = {fieldnames[0]: "{} Stock Report from {} thru {}".format(app_config["SITE_NAME"],iso_date_string(start_date),iso_date_string(end_date)) }
            writer.writerow(row)
            writer.writeheader()
            
            for rec in recs:
                temp_row = rec._asdict()
                # temp_row is an orderedDict and elements can't be removed
                row = OrderedDict()
                for key, value in temp_row.items():
                    if key not in fields_to_ignore:
                        row[key] = value
                    
                row[extras[0]] = Category(g.db).category_name(rec.cat_id)
                row[extras[1]] = items.stock_on_hand(rec.id,start_date - timedelta(days=1))
                row[extras[2]] = items.additions(rec.id,start_date,end_date)
                row[extras[3]] = items.subtractions(rec.id,start_date,end_date)
                row[extras[4]] = items.lifo_cost(rec.id) # get the most recent cost
                row[extras[5]] = items.stock_on_hand(rec.id,end_date)
                writer.writerow(row)
                    
            out = output.getvalue()

            
    name = 'stock_report_{}'.format(local_datetime_now().strftime('%Y%m%d_%H%M'))
    return send_as_file(out,name=name,ext='csv')
    
def send_as_file(out,name='report',ext='csv'):
    #send the report
    resp = Response(out)
    resp.headers['content-type'] = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename="{}.{}"'.format(name,ext)
    resp.headers['Content-Type'] = 'application/{}'.format(ext)
    return resp
    