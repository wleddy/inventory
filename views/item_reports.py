# create reports of Items

from inventory.models import Item, Category, Transaction, Warehouse
from flask import Response,g
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.takeabeltof.jinja_filters import iso_date_string, excel_date_and_time_string, local_date_string
from shotglass2.takeabeltof.utils import cleanRecordID
from datetime import timedelta

from shotglass2.takeabeltof.views import TableView
    

def stock_on_hand_report(start_date=None,end_date=None,warehouse=-1):
    view = TableView(Item,g.db)

    view.export_fields = [
            {'name':'name',},
            {'name':'uom',},
            {'name':'category',},
            {'name':'warehouse',},
            {'name':'lifo_cost',},
            {'name':'prev_soh',},
            {'name':'added',},
            {'name':'xfer_out',},
            {'name':'used',},
            {'name':'soh','label':'On Hand'},
        ]
    
    # import pdb;pdb.set_trace()
    view.path = ['export',]
    warehouse_name = 'All Warehouse'
    where = '1'
    warehouse_id = cleanRecordID(warehouse)
    if warehouse_id > 0:
        where = " trx.warehouse_id = {}".format(warehouse_id)
        rec = Warehouse(g.db).get(warehouse_id)
        warehouse_name = rec.name if rec else "Warehouse Unknown"
            
    # Default to reporting only for this year
    if start_date is None:
        start_date = local_datetime_now().replace(month=1,day=1)
    if end_date is None:
        end_date = local_datetime_now().replace(year=local_datetime_now().year,month=12,day=31)
        
    view.export_title = "{} Stock Report for period {} thru {} generated on {}".format(
        warehouse_name.title(),
        local_date_string(start_date),
        local_date_string(end_date),
        excel_date_and_time_string(local_datetime_now()),
    )
    view.export_file_name = "{} stock report {}.csv".format(
        warehouse_name,
        str(local_datetime_now())[:19],
    ).replace(' ','_').lower()
        
                
    view.sql = """SELECT 
                item.*, 
                cats.name as category,
                '{warehouse_name}' as warehouse,
                COALESCE (
                    (select trx.value from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') <= date('{end_date}','localtime') 
                        and trx.value > 0 and {where} order by trx.created desc limit 1
                    )
                ,0) as lifo_cost,
                COALESCE (
                    (select sum(trx.qty) from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') < date('{start_date}','localtime') 
                        and {where}
                    )
                ,0) as prev_soh,
                COALESCE (
                    (select sum(trx.qty) from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') >= date('{start_date}','localtime') 
                        and date(trx.created, 'localtime') <= date('{end_date}','localtime') 
                        and {where} and lower(trx.trx_type) = 'transfer out'
                    )
                ,0) as xfer_out,
                COALESCE (
                    (select sum(trx.qty) from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') >= date('{start_date}','localtime') 
                        and date(trx.created, 'localtime') <= date('{end_date}','localtime') 
                        and {where} and trx.qty > 0
                    )
                ,0) as added,
                COALESCE (
                    (select sum(trx.qty) from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') >= date('{start_date}','localtime') 
                        and date(trx.created, 'localtime') <= date('{end_date}','localtime') 
                        and {where} and lower(trx.trx_type) = 'remove'
                    )
                ,0) as used,
                COALESCE (
                    (select sum(trx.qty) from trx 
                        where trx.item_id = item.id  
                        and date(trx.created, 'localtime') <= date('{end_date}','localtime') 
                        and {where}
                    )
                ,0) as soh
            
                from item
                left join trx on trx.item_id = item.id
                left join warehouse as wares on wares.id = trx.warehouse_id
                left join category as cats on cats.id = item.cat_id
            
                where {where} 
                group by item.id
                order by lower(category), lower(item.name)
        """.format(
            where=where,
            start_date=iso_date_string(start_date),
            end_date=iso_date_string(end_date),
            warehouse_name=warehouse_name,
            )

    return view.dispatch_request()
    
    
def send_as_file(out,name='report',ext='csv'):
    #send the report
    resp = Response(out)
    resp.headers['content-type'] = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename="{}.{}"'.format(name,ext)
    resp.headers['Content-Type'] = 'application/{}'.format(ext)
    return resp
    