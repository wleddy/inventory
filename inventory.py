from flask import g, url_for, abort
from shotglass2.takeabeltof.utils import printException
from inventory.utils import register_inv_filters
from inventory.models import init_tables, Item,Category,Uom,Transaction
from inventory.views import item, category, uom, transaction

def register_jinja_filters(app):
    register_inv_filters(app)

def initalize_tables(db):
    init_tables(db)
    
def register_admin():
    
    try:
        g.admin.register(Item,None,display_name='Inv Admin',header_row=True,minimum_rank_required=500)
        g.admin.register(Item,url_for('item.display'),minimum_rank_required=1)
        g.admin.register(Category,url_for('category.display'),display_name='Categories',minimum_rank_required=500)
        g.admin.register(Uom,url_for('uom.display'),display_name='UOM',minimum_rank_required=500)
        g.admin.register(Transaction,url_for('transaction.display'),display_name='Transactions',minimum_rank_required=500)
    except AttributeError as e:
        flash(printException('Unable to register Inventory Access',err=e))
        abort(500)
        

def register_blueprints(app):
    #import pdb;pdb.set_trace()
    
    app.register_blueprint(item.mod)
    app.register_blueprint(category.mod)
    app.register_blueprint(uom.mod)
    app.register_blueprint(transaction.mod)
