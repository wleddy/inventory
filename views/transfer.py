from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from inventory.models import Item, Transaction, Warehouse, Transfer
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import getDatetimeFromString, local_datetime_now
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('transfer',__name__, template_folder='templates/inventory', static_folder='static/inventory', url_prefix='/transfer')


def setExits():
    g.listURL = url_for('.display')
    #g.editURL = url_for('.edit')
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
    
    
### In reality this is only used to add new transfers since editing opens a whole can of worms.
### Just delete bad transfer records and recreate them

@mod.route('/edit_from_list',methods=["GET", "POST",])
@mod.route('/edit_from_list/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/',methods=["GET", "POST",])
@mod.route('/edit_from_list/<int:id>/<int:item_id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
def edit_from_list(id=None,item_id=None):
    """Handle creation of transfer from the Item record form
       It's not practical to edit existing transfers, so delete the offending
       transfer record then recreate it instead.
    """
    setExits()
    #import pdb;pdb.set_trace()

    rec = None
    item_rec = None
    tran_id = cleanRecordID(id)
    item_id=cleanRecordID(item_id)
    transfer = Transfer(g.db)
    if tran_id > 0:
        sql = get_transfer_select(where="transfer.id = {}".format(tran_id))
        rec = transfer.query(sql)

    if rec:
        rec = rec[0]
        item_id = rec.item_id
        # warehouse_in_id = rec.warehouse_in_id
        # warehouse_out_id = rec.warehouse_out_id

    else:
        rec = transfer.new()
        rec.transfer_date = local_datetime_now()
        if 'last_transfer' in session:
            transfer.update(rec,session['last_transfer'])

    if item_id > 0:
        item_rec = Item(g.db).get(item_id)

    if item_rec:
        rec.item_id=item_id
    else:
        flash("This is not a valid item id")
        return "failure: This is not a valid item id."

    warehouses = get_warehouse_dropdown(item_id)
    warehouse_in_id = cleanRecordID(request.form.get('warehouse_in_id',rec._asdict().get('warehouse_in_id',0)))
    warehouse_out_id = cleanRecordID(request.form.get('warehouse_out_id',rec._asdict().get('warehouse_out_id',0)))

    # Handle Response?
    if request.form:
        #import pdb;pdb.set_trace()

        if save_record(rec):
            return "success" # the success function looks for this...
        else:
            pass

    return render_template('transfer_edit_from_list.html',
            rec=rec,
            warehouses=warehouses,
            item=item_rec,
            warehouse_in_id=warehouse_in_id,
            warehouse_out_id=warehouse_out_id,
            )

    
@mod.route('/delete_from_list/',methods=["GET", "POST",])
@mod.route('/delete_from_list/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transfer)
def delete_from_list(id=None):
    #import pdb;pdb.set_trace()
    from inventory.views.item import refresh_trx_lists
    setExits()
    # get the item id first
    rec = Transfer(g.db).get(id)
    if rec and handle_delete(id):
        return refresh_trx_lists(rec.item_id)

    return 'failure: Could not delete that {}'.format(g.title)
    
    
###
# On further review, it is too problematic to actually edit existing transfers. Just
# delete them and recreate as needed.
###
# @mod.route('/edit',methods=["GET", "POST",])
# @mod.route('/edit/',methods=["GET", "POST",])
# @mod.route('/edit/<int:id>/',methods=["GET", "POST",])
# @table_access_required(Transfer)
# def edit(id=None):
#     setExits()
#     #import pdb;pdb.set_trace()
#
#     transfer = Transfer(g.db)
#
#     if request.form:
#         id = request.form.get('id',None)
#     id = cleanRecordID(id)
#     items = Item(g.db).select()
#     current_item = None
#
#     if id < 0:
#         flash("Invalid Record ID")
#         return redirect(g.listURL)
#
#     if id >= 0 and not request.form:
#         if id == 0:
#             rec = transfer.new()
#             rec.transfer_date = local_datetime_now()
#
#         else:
#             rec = transfer.get(id)
#
#         if not rec:
#             flash('Record not Found')
#             return redirect(g.listURL)
#         else:
#             #Get the item if there is one
#             if rec.item_id != 0:
#                 current_item = Item(g.db).get(rec.item_id)
#
#
#     elif request.form:
#         if id == 0:
#             rec = transfer.new()
#             #rec.transfer_date = local_datetime_now()
#         else:
#             rec = transfer.get(id)
#             if not rec:
#                 flash('Record not found when trying to save')
#                 return redirect(g.listURL)
#
#         transfer.update(rec,request.form)
#         if save_record(rec):
#             return redirect(g.listURL)
#         else:
#             for err in error_list:
#                 flash(err)
#         return redirect(g.listURL)
#
#     return render_template('transfer_edit.html',rec=rec,current_item=current_item,items=items)


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
        Transaction(g.db).delete(rec.out_trx_id)
        Transaction(g.db).delete(rec.in_trx_id)
        Transfer(g.db).delete(rec.id)
        g.db.commit()
        return True
    
    
def save_record(rec):
    """Attempt to validate and save a record"""
    
    #import pdb;pdb.set_trace()
    
    transfer = Transfer(g.db)
    trx_table = Transaction(g.db)
    
        
    transfer.update(rec,request.form)
    if validate_form(rec):
        if rec.id:
            ## delete the current transfer record.
            trx_table.delete(cleanRecordID(rec.out_trx_id))
            trx_table.delete(cleanRecordID(rec.in_trx_id))
            ## related transfer record is deleted by cascade
            transfer.delete(cleanRecordID(rec.id))
            g.db.commit() # trigger the casscade delete of transactions
            rec = transfer.new()
            transfer.update(rec,request.form)
        
        transfer.save(rec)
        #Create trx recods for this transfer...
        #create the Outgoing trx record
        trx_rec = trx_table.new()
            
        trx_rec.item_id = rec.item_id
        trx_rec.qty = abs(rec.qty) * -1
        trx_rec.created = rec.transfer_date
        trx_rec.warehouse_id = request.form["warehouse_out_id"]
        trx_rec.value = 0
        trx_rec.trx_type = "Transfer Out"
        trx_table.save(trx_rec)
        rec.out_trx_id = trx_rec.id
        
        trx_rec2 = trx_table.new()
            
        trx_table.update(trx_rec2,trx_rec._asdict())
        trx_rec2.qty = abs(rec.qty)
        trx_rec2.value = Item(g.db).lifo_cost(trx_rec.item_id,end_date=rec.transfer_date)
        trx_rec2.warehouse_id = request.form["warehouse_in_id"]
        trx_rec2.trx_type = "Transfer In"
        trx_table.save(trx_rec2)
        rec.in_trx_id = trx_rec2.id
        
        transfer.save(rec)
        #Save some data to session
        session['last_transfer'] = {"transfer_date":rec.transfer_date,}
        
        try:
            g.db.commit()
            #Save the date and comment to session
            return True
            
        except Exception as e:
            flash(printException('Error attempting to save Transfer record',str(e)))
            
    g.db.rollback()
    return False
    
    
def validate_form(rec):
    valid_form = True
        
    #Try to coerse qty to a number
    if request.form['qty'].strip() =='':
        flash('Quantity is required')
        valid_form = False
    else:
        try:
            rec.qty = float(rec.qty)
            if rec.qty <= 0:
                flash('Quantity must be greater than 0')
                valid_form = False
            
            #truncate qty if int
            elif rec.qty - int(rec.qty) == 0:
                rec.qty = int(rec.qty)
            
        except ValueError as e:
            flash('Quantity must be a number')
            valid_form = False
    
    # Must be attached to an item
    itemID = cleanRecordID(request.form.get('item_id',0))
    if itemID <= 0:
        flash("You must select an item to use with this transfer")
        valid_form = False
        #Must not be more than stock on hand
    elif rec.qty and type(rec.qty) != str:
        QOH =  Item(g.db).stock_on_hand(itemID,warehouse_id=request.form.get("warehouse_out_id"))
        if rec.qty > QOH:
            flash("You may not transfer more than the quantity on hand ({})".format(QOH))
            valid_form = False
    
    if not Warehouse(g.db).get(cleanRecordID(request.form.get('warehouse_out_id'))):
        flash("You must select a transfer out warehouse")
        valid_form = False

    if not Warehouse(g.db).get(cleanRecordID(request.form.get('warehouse_in_id'))):
        flash("You must select a transfer in warehouse")
        valid_form = False

            
    # test for valid date
    test_date = getDatetimeFromString(rec.transfer_date)
    if not test_date:
        flash("There must be transfer date")
        valid_form = False
    else:
        rec.transfer_date = test_date
        
        if test_date > local_datetime_now():
            flash("Transfer date may not be in the future")
            valid_form = False
        
    return valid_form
    
    
def get_transfer_select(where):
    """Return the sql to create a selection for a transfer record"""
    
    sql = """SELECT
                transfer.*,
                warehouse_out.name as warehouse_out_name,
                warehouse_out.id as warehouse_out_id,
                warehouse_in.name as warehouse_in_name,
                warehouse_in.id as warehouse_in_id,
                item.name as item_name
            
            FROM transfer
            LEFT JOIN trx as trx_out on trx_out.id = transfer.out_trx_id
            LEFT JOIN trx as trx_in on trx_in.id = transfer.in_trx_id
            LEFT JOIN warehouse as warehouse_out on warehouse_out.id = trx_out.warehouse_id
            LEFT JOIN warehouse as warehouse_in on warehouse_in.id = trx_in.warehouse_id
            JOIN item on item.id = transfer.item_id
            WHERE {where}
            ORDER BY transfer.transfer_date DESC, transfer.id DESC
            """.format(where=where)
            
    return sql
    
    
def get_warehouse_dropdown(item_id=0):
    """Return a list of dicts to be used in the transfer drop downs for warehouses"""
    
    out = []
    recs = Warehouse(g.db).select()
    if recs:
        for rec in recs:
            out.append(rec._asdict())
            qoh = 0
            if item_id:
                qoh = Item(g.db).stock_on_hand(item_id,warehouse_id=rec.id)
                
            out[len(out)-1].update({'qoh':qoh})
            
    return out
        
        
def get_transfer_list_for_item(item_id=None):
    """Render an html snippet of the transaciton list for the item"""

    item_id = cleanRecordID(item_id)
    recs = None
    where = "1"
    if item_id and item_id > 0:
        where = 'transfer.item_id = {}'.format(item_id)

        sql = get_transfer_select(where)
        
        #print(sql)
        recs = Transfer(g.db).query(sql)
            
    return render_template('transfer_embed_list.html',recs=recs,item_id=item_id)

    
        