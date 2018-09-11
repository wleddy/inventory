from flask import g
from users.utils import cleanRecordID

"""
Some utility functions
"""
from datetime import datetime

def str_to_short_date(date_str):
    formats = [
    '%m/%d/%y',
    '%m/%d/%Y',
    '%m-%d-%y',
    '%m-%d-%Y',
    '%y-%m-%d',
    '%Y-%m-%d',
    ]
    
    space_at = date_str.find(" ")
    if space_at > 0:
        date_str = date_str[:space_at]
    
    a_date = None
    for fmt in formats:
        try:
            a_date = datetime.strptime(date_str,fmt)
            break
        except ValueError as e:
            pass
        except Exception as e:
            print(str(e))
            
    return a_date
    
    
# some custom filters for templates
def date_string(value, format='%-m/%-d/%y'):
    if type(value) is datetime:
        return value.strftime(format)
    if type(value) is str:
        return str_to_short_date(value).strftime(format)
    
    return value
    
    
def two_digit_string(the_string):
    #import pdb;pdb.set_trace()
    try:
        the_string = float(the_string)
        the_string = (str(the_string) + "00")
        pos = the_string.find(".")
        if pos > 0:
            the_string = the_string[:pos+3]
    except ValueError as e:
        pass
        
    return the_string
    
def category_name(id=None):
    """Return the name of the category or None"""
    from inventory.models import Category
    rec = Category(g.db).select_one(where='id = {}'.format(cleanRecordID(id)))
    if rec:
        return rec.name
        
    return None
        
def stock_on_hand(id=None):
    """Return the stock count for the item.id else 0"""
    from inventory.models import Item
    rec = Item(g.db).get(cleanRecordID(id))
    if rec:
        soh = Item(g.db).stock_on_hand(cleanRecordID(id))
        if soh > 0:
            if soh >= rec.min_stock:
                return soh
            else:
                return "low stock({}) {}".format(rec.min_stock,soh)
                
        return "- out of stock -"

def register_jinja_filters(app):
    # register the filters
    app.jinja_env.filters['date_string'] = date_string
    app.jinja_env.filters['money'] = two_digit_string
    app.jinja_env.filters['category_name'] = category_name
    app.jinja_env.filters['stock_on_hand'] = stock_on_hand