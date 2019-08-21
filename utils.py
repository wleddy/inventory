from flask import g
from shotglass2.takeabeltof.utils import cleanRecordID
from inventory.models import Item, Category

"""
Some utility functions
"""
    
def category_name(id=None):
    """Return the name of the category or None"""
    from inventory.models import Category
    rec = Category(g.db).select_one(where='id = {}'.format(cleanRecordID(id)))
    if rec:
        return rec.name
        
    return None
        
def stock_on_hand(id=None):
    """Return the stock count for the item.id else something else"""
    rec = Item(g.db).get(cleanRecordID(id))
    if rec:
        soh = Item(g.db).stock_on_hand(cleanRecordID(id))
        if soh > 0:
            if soh >= rec.min_stock:
                return soh
            else:
                return "{} Min ({})".format(soh,rec.min_stock)
                
        return "- out of stock -"
        
        
def lifo_cost(id=None):
    """Return the LIFO cost as a string for item """
    cost = Item(g.db).lifo_cost(cleanRecordID(id))
    return str(cost)

def register_inv_filters(app):
    # register the filters
    app.jinja_env.filters['category_name'] = category_name
    app.jinja_env.filters['stock_on_hand'] = stock_on_hand
    app.jinja_env.filters['lifo_cost'] = lifo_cost
    
    