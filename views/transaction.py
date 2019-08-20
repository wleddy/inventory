from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from inventory.models import Item, Category, Uom, Transaction, Warehouse
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import getDatetimeFromString, local_datetime_now
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('transaction',__name__, template_folder='templates/inventory', static_folder='static/inventory', url_prefix='/trx')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Inventory Transaction'


@mod.route('/',methods=["GET",])
@table_access_required(Transaction)
def display():
    setExits()
    
    recs = Transaction(g.db).select()
   
    #Get categories to display
    items = Item(g.db)
    item = {}
    #import pdb;pdb.set_trace()
    
    if recs:
        for rec in recs:
            fnd = items.get(rec.item_id)
            if fnd:
                item[rec.item_id] = fnd.name

    return render_template('trx_list.html',recs=recs,item=item)
    
    
@mod.route('/edit_from_list',methods=["GET", "POST",])
@mod.route('/edit_from_list/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/<int:item_id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def edit_from_list(id=None,item_id=None):
    """Handle creation of transaction from the Item record form"""
    setExits()
    #import pdb;pdb.set_trace()
    
    item_id=cleanRecordID(item_id)
    item_rec = None
    rec = None
    warehouses = Warehouse(g.db).select()
    trx_types = get_site_config().get('trx_types',['Add','Remove',])
    transaction = Transaction(g.db)
    trx_id = cleanRecordID(id)
    if trx_id > 0:
        rec = transaction.get(trx_id)
        
    if rec:
        item_id = rec.item_id
    else:
        rec = transaction.new()
        rec.created = local_datetime_now()
        if 'last_trx' in session:
            transaction.update(rec,session['last_trx'])
    
    # Handle Response?
    if request.form:
        #import pdb;pdb.set_trace()
        error_list=[]
        transaction.update(rec,request.form)
        if save_record(rec,error_list):
            return "success" # the success function looks for this...
        else:
            pass
            
    
    if item_id > 0:
        item_rec = Item(g.db).get(item_id)
    
    if not item_rec:
        flash("This is not a valid item id")
        return "failure: This is not a valid item id."
    else:
        rec.item_id=item_id
        
            
    return render_template('trx_edit_from_list.html',rec=rec,current_item=item_rec,warehouses=warehouses,trx_types=trx_types)
    
#@mod.route('/add_from_list/',methods=["GET", "POST",])
#@mod.route('/add_from_list/<int:item_id>/',methods=["GET", "POST",])
#@table_access_required(Transaction)
#def add_from_list(item_id=None):
#    import pdb;pdb.set_trace()
#    
#    return edit_from_list(0,item_id)
        
    
@mod.route('/delete_from_list/',methods=["GET", "POST",])
@mod.route('/delete_from_list/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def delete_from_list(id=None):
    setExits()
    if handle_delete(id):
        return "success"

    return 'failure: Could not delete that {}'.format(g.title)
    
@mod.route('/edit',methods=["GET", "POST",])
@mod.route('/edit/',methods=["GET", "POST",])
@mod.route('/edit/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def edit(id=None):
    setExits()
    #import pdb;pdb.set_trace()
    
    transaction = Transaction(g.db)
    
    if request.form:
        id = request.form.get('id',None)
    id = cleanRecordID(id)
    items = Item(g.db).select()
    current_item = None
    
    if id < 0:
        flash("Invalid Record ID")
        return redirect(g.listURL)
    
    if id >= 0 and not request.form:
        if id == 0:
            rec = transaction.new()
            rec.created = local_datetime_now()
            if 'last_trx' in session:
                transaction.update(rec,session['last_trx'])
        else:
            rec = transaction.get(id)
            
        if not rec:
            flash('Record not Found')
            return redirect(g.listURL)
        else:
            #Get the item if there is one
            if rec.item_id != 0:
                current_item = Item(g.db).get(rec.item_id)
                
            
    elif request.form:
        current_item = Item(g.db).get(cleanRecordID(request.form.get('item_id',"0")))
        if id == 0:
            rec = transaction.new()
        else:
            rec = transaction.get(id)
            if not rec:
                flash('Record not found when trying to save')
                return redirect(g.listURL)
                
        transaction.update(rec,request.form)
        error_list = []
        if save_record(rec,error_list):
            return redirect(g.listURL)
        else:
            for err in error_list:
                flash(err)
        return redirect(g.listURL)
                    
    return render_template('trx_edit.html',rec=rec,current_item=current_item,items=items)


@mod.route('/get_trx_list/',methods=["GET", ])
@mod.route('/get_trx_list/<int:item_id>/',methods=["GET", ])
def get_list_for_item(item_id=None):
    """Render an html snippet of the transaciton list for the item"""
    item_id = cleanRecordID(item_id)
    trxs = None
    if item_id and item_id > 0:
        where = 'item_id = {}'.format(item_id)
        order_by = 'trx.created desc, trx.warehouse_id'
        
        sql = """SELECT 
            trx.*, 
            warehouse.name as warehouse_name, 
            category.name as category_name
            
        FROM trx 
        JOIN item on item.id = trx.item_id 
        JOIN category on category.id = item.cat_id
        JOIN warehouse on warehouse.id = trx.warehouse_id
        WHERE {where}
        ORDER BY {order_by}
        """.format(where=where,order_by=order_by)
        
        
        trxs = Transaction(g.db).query(sql)
        
    return render_template('trx_embed_list.html',trxs=trxs,item_id=item_id)
    
    
@mod.route('/delete',methods=["GET", "POST",])
@mod.route('/delete/',methods=["GET", "POST",])
@mod.route('/delete/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def delete(id=None):
    setExits()
    if handle_delete(id):
        flash("{} Deleted".format(g.title))
        
    return redirect(g.listURL)
    
    
def handle_delete(id=None):
    if id == None:
        id = request.form.get('id',request.args.get('id',-1))
    
    id = cleanRecordID(id)
    if id <=0:
        #flash("That is not a valid record ID")
        return False
        
    rec = Transaction(g.db).get(id)
    if not rec:
        #flash("Record not found")
        return False
    else:
        Transaction(g.db).delete(rec.id)
        g.db.commit()
        return True
    
    
def save_record(rec,err_list=[]):
    """Attempt to validate and save a record"""
    if validate_form(rec):
        Transaction(g.db).save(rec)
        try:
            g.db.commit()
            #Save the date and comment to session
            session['last_trx'] = {"created":rec.created,"note":rec.note}
            return True
            
        except Exception as e:
            err_list.append(printException('Error attempting to save Transaction record',str(e)))
            
    g.db.rollback()
    return False
    
    
def validate_form(rec):
    valid_form = True
    datestring = request.form.get('created','').strip()
    if datestring == '':
        valid_form = False
        flash('Date may not be empty')
    else:
        createdDate = getDatetimeFromString(datestring)
        if createdDate is None:
            flash('Date is not in a known format ("mm/dd/yy")')
            valid_form = False
        elif createdDate > local_datetime_now():
            flash("The date may not be in the future")
            valid_form = False
    
    if valid_form:
        rec.created = createdDate
        
    
    # Value must be a number
    try:
        rec.value = float(request.form.get('value',0))
    except ValueError as e:
        flash('Could not convert Value {} to a number'.format(request.form.get('value',"")))
        valid_form = False

    # Must be attached to an item
    itemID = cleanRecordID(request.form.get('item_id',0))
    if not itemID or itemID < 0:
        flash("You must select an item to use with this transaction")
        valid_form = False
        
    #Try to coerse qty to a number
    rec.qty = request.form.get('qty','').strip()
    if rec.qty =='':
        flash('Quantity is required')
        valid_form = False
        
    if not Warehouse(g.db).get(request.form.get('warehouse_id',-1)):
        flash("You must select a warehouse")
        valid_form = False

    try:
        rec.qty = float(rec.qty)
        if rec.qty == 0:
            flash('Quantity may not be 0')
            valid_form = False
            
        #truncate qty if int
        if rec.qty - int(rec.qty) == 0:
            rec.qty = int(rec.qty)
                       
    except ValueError as e:
        flash('Could not convert Qty {} to a number'.format(rec.qty))
        valid_form = False
    
    return valid_form