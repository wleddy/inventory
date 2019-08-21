# create reports of Items

from inventory.models import Item, Category, Transaction, Warehouse
from flask import Response,g
from shotglass2.shotglass import get_app_config
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.takeabeltof.jinja_filters import iso_date_string
from shotglass2.takeabeltof.utils import cleanRecordID
from datetime import timedelta
import csv
from io import StringIO
from collections import OrderedDict

def stock_on_hand_report(start_date=None,end_date=None,warehouse=-1):
    """Create a CSV report of the current state of Item"""
    out = ''
    
    #import pdb;pdb.set_trace()
    items = Item(g.db)
    warehouse_id = cleanRecordID(warehouse)
    where = '1'
    warehouse_name = "All"
    if warehouse_id > 0:
        where = " trx.warehouse_id = {}".format(warehouse_id)
        warehouse_name = Warehouse(g.db).get(warehouse).name
        
        sql = """SELECT 
                item.*, 
                wares.name as warehouse,
                cats.name as category
            
                from item
                left join trx on trx.item_id = item.id
                join warehouse as wares on wares.id = trx.warehouse_id
                join category as cats on cats.id = item.cat_id
            
                Where {where}
                order by lower(category), item.name
        """.format(where=where)
        
        
    else:
        warehouse_id = None
        
        sql = """SELECT 
                item.*, 
                "{warehouse_name}" as warehouse,
                cats.name as category
                from item
                join category as cats on cats.id = item.cat_id
            
                order by lower(category), item.name
        """.format(warehouse_name=warehouse_name)
    recs = items.query(sql)
    
    # Default to reporting only for this year
    if start_date is None:
        start_date = local_datetime_now().replace(month=1,day=1)
    if end_date is None:
        end_date = local_datetime_now().replace(year=local_datetime_now().year,month=12,day=31)
        
    if recs:
        fields_to_ignore = ['id','cat_id','description',]
        fields = recs[0]._fields # a tuple
        fieldnames = [s for s in fields if s not in fields_to_ignore ]
        extras = []
        extras.append('prev soh')
        extras.append('added')
        extras.append('used')
        extras.append('lifo cost')
        extras.append('on hand')
        fieldnames.extend(extras)
    
        output = StringIO()
        with output as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            app_config = get_app_config()
            row = {fieldnames[0]: "{} Stock Report from {} thru {}".format(app_config["SITE_NAME"],iso_date_string(start_date),iso_date_string(end_date)) }
            writer.writerow(row)
            writer.writeheader()
            
            #import pdb;pdb.set_trace()
            for rec in recs:
                extras_value_list = [items.stock_on_hand(rec.id,start_date - timedelta(days=1),warehouse_id=warehouse_id),
                    items.additions(rec.id,start_date,end_date,warehouse_id=warehouse_id),
                    items.subtractions(rec.id,start_date,end_date,warehouse_id=warehouse_id),
                    items.lifo_cost(rec.id,warehouse_id=warehouse_id),
                    items.stock_on_hand(rec.id,end_date,warehouse_id=warehouse_id),]

                temp_row = rec._asdict()
                # temp_row is an orderedDict and elements can't be removed
                row = OrderedDict()
                for key, value in temp_row.items():
                    if key not in fields_to_ignore:
                        row[key] = value
                    
                for x in range(len(extras_value_list)):
                    row[extras[x]] = extras_value_list[x]
                        
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
    