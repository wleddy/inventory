"""
A 'one-time' method to import the canvasapps data for Bike Doc
"""
import sys
sys.path.append('') ##get import to look in the working dir.

import csv
from datetime import datetime
import os.path
from users.database import Database
from inventory.models import Category, Item, Uom, Transaction

def import_data(filespec):
    db = Database('instance/database.sqlite').connect()
    category = Category(db)
    uom = Uom(db)
    item = Item(db)
    trx = Transaction(db)
        
    with open(filespec, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print('Name: {}, Category: {}'.format(row['item_name'], row['category_name']))
            #import pdb;pdb.set_trace()
            #create a Category if not exists
            cats = category.select_one(where='name = "{}"'.format(row['category_name']))
            if not cats:
                cats = category.new()
                cats.name = row["category_name"]
                category.save(cats)
            cat_id = cats.id
            #create UOM if not exists
            uom_name = row['uom'].strip()
            if uom_name == '':
                uom_name = "Ea."
                
            uoms = uom.select_one(where='name = "{}"'.format(uom_name))
            if not uoms:
                uoms = uom.new()
                uoms.name = uom_name
                uom.save(uoms)
           
            items = item.select_one(where = 'name = "{}"'.format(row['item_name'],))
            if not items:
                items = item.new()
                items.name = row['item_name']
                items.uom = uom_name
                items.cat_id = cat_id
                item.save(items)
                
            # Create a transaction record
            trxs = trx.new()
            trx.update(trxs,row)
            trxs.created = datetime.strptime(row['created'],'%Y-%m-%d')
            trxs.item_id = items.id
            trx.save(trxs)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(str(e))
            
            
if __name__ == '__main__':
    go_on = True
    while go_on:
        filespec = input('File to import: ').strip()
        if os.path.isfile(filespec):
            go_on = False
            import_data(filespec) 
        else:
            print('File does not exist')
