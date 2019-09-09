from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from inventory.models import Item, Transaction, Warehouse, Transfer, TransferItem
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import getDatetimeFromString, local_datetime_now
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('transfer',__name__, template_folder='templates/inventory', static_folder='static/inventory', url_prefix='/transfer')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Inventory Transfer'


@mod.route('/',methods=["GET",])
@table_access_required(Transfer)
def display():
    setExits()
    
    recs = Transfer(g.db).select()
   
    #Get categories to display
    items = Item(g.db)
    item = {}
    #import pdb;pdb.set_trace()
    
    if recs:
        for rec in recs:
            fnd = items.get(rec.item_id)
            if fnd:
                item[rec.item_id] = fnd.name

    return render_template('transfer_list.html',recs=recs,item=item)
    
    
@mod.route('/edit_from_list',methods=["GET", "POST",])
@mod.route('/edit_from_list/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/<int:item_id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
def edit_from_list(id=None,item_id=None):
    """Handle creation of transfer from the Item record form"""
    setExits()
    #import pdb;pdb.set_trace()
    
    item_id=cleanRecordID(item_id)
    item_rec = None
    rec = None
    warehouses = Warehouse(g.db).select()
    transfer = Transfer(g.db)
    tran_id = cleanRecordID(id)
    if tran_id > 0:
        rec = transfer.get(tran_id)
        
    if rec:
        item_id = rec.item_id
    else:
        rec = transfer.new()
        rec.created = local_datetime_now()
        if 'last_tran' in session:
            transfer.update(rec,session['last_tran'])
    
    # Handle Response?
    if request.form:
        #import pdb;pdb.set_trace()
        error_list=[]
        transfer.update(rec,request.form)
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
        
            
    return render_template('transaction_edit_from_list.html',rec=rec,current_item=item_rec,warehouses=warehouses,)
    
#@mod.route('/add_from_list/',methods=["GET", "POST",])
#@mod.route('/add_from_list/<int:item_id>/',methods=["GET", "POST",])
#@table_access_required(Transfer)
#def add_from_list(item_id=None):
#    import pdb;pdb.set_trace()
#    
#    return edit_from_list(0,item_id)
        
    
@mod.route('/delete_from_list/',methods=["GET", "POST",])
@mod.route('/delete_from_list/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
def delete_from_list(id=None):
    setExits()
    if handle_delete(id):
        return "success"

    return 'failure: Could not delete that {}'.format(g.title)
    
@mod.route('/edit',methods=["GET", "POST",])
@mod.route('/edit/',methods=["GET", "POST",])
@mod.route('/edit/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
def edit(id=None):
    setExits()
    #import pdb;pdb.set_trace()
    
    transfer = Transfer(g.db)
    
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
            rec = transfer.new()
            rec.created = local_datetime_now()
            if 'last_trans' in session:
                transfer.update(rec,session['last_trans'])
        else:
            rec = transfer.get(id)
            
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
            rec = transfer.new()
        else:
            rec = transfer.get(id)
            if not rec:
                flash('Record not found when trying to save')
                return redirect(g.listURL)
                
        transfer.update(rec,request.form)
        error_list = []
        if save_record(rec,error_list):
            return redirect(g.listURL)
        else:
            for err in error_list:
                flash(err)
        return redirect(g.listURL)
                    
    return render_template('transfer_edit.html',rec=rec,current_item=current_item,items=items)


@mod.route('/get_transfer_list/',methods=["GET", ])
@mod.route('/get_transfer_list/<int:item_id>/',methods=["GET", ])
def get_list_for_item(item_id=None):
    """Render an html snippet of the transaciton list for the item"""
    item_id = cleanRecordID(item_id)
    trans = None
    if item_id and item_id > 0:
        # where = 'item_id = {}'.format(item_id)
        # order_by = 'trx.created desc, trx.warehouse_id'
        #
        # sql = """SELECT
        #     transfer.*,
        #
        # FROM transfer
        # JOIN item on item.id = transfer.item_id
        # JOIN category on category.id = item.cat_id
        # WHERE {where}
        # ORDER BY {order_by}
        # """.format(where=where,order_by=order_by)
        #
        # trxs = Transfer(g.db).query(sql)
        
        trans=Transfer.select(where='item_id = {}'.format(item_id))
        
    return render_template('transfer_embed_list.html',trans=trans,item_id=item_id)
    
    
@mod.route('/delete',methods=["GET", "POST",])
@mod.route('/delete/',methods=["GET", "POST",])
@mod.route('/delete/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
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
        
    rec = Transfer(g.db).get(id)
    if not rec:
        #flash("Record not found")
        return False
    else:
        Transfer(g.db).delete(rec.id)
        g.db.commit()
        return True
    
    
def save_record(rec,err_list=[]):
    """Attempt to validate and save a record"""
    if validate_form(rec):
        Transfer(g.db).save(rec)
        try:
            g.db.commit()
            #Save the date and comment to session
            session['last_trans'] = {"created":rec.created,"note":rec.note}
            return True
            
        except Exception as e:
            err_list.append(printException('Error attempting to save Transfer record',str(e)))
            
    g.db.rollback()
    return False
    
    
def validate_form(rec):
    valid_form = True
        
    
    # Must be attached to an item
    itemID = cleanRecordID(request.form.get('item_id',0))
    if not itemID or itemID < 0:
        flash("You must select an item to use with this transfer")
        valid_form = False
        
        
    if not Warehouse(g.db).get(request.form.get('warehouse_out_id',-1)):
        flash("You must select a transfer out warehouse")
        valid_form = False

    if not Warehouse(g.db).get(request.form.get('warehouse_in_id',-1)):
        flash("You must select a transfer in warehouse")
        valid_form = False

    #Try to coerse qty to a number
    transfer_qty = request.form.get('transfer_qty','').strip()
    if transfer_qty =='':
        flash('Quantity is required')
        valid_form = False
    else:
        try:
            transfer_qty = float(transfer_qty)
            if transfer_qty <= 0:
                flash('Quantity must be greater than 0')
                valid_form = False
            
            #truncate qty if int
            elif transfer_qty - int(transfer_qty) == 0:
                transfer_qty = int(transfer_qty)
                
        except ValueError as e:
            flash('Quantity must be a number')
            valid_form = False
    
    return valid_form