from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from users.utils import printException, cleanRecordID
from datetime import datetime
from inventory.models import Item, Category, Uom, Transaction
from inventory.utils import str_to_short_date

mod = Blueprint('transaction',__name__, template_folder='../templates', url_prefix='/trx')


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
    
    
@mod.route('/add',methods=["GET", "POST",])
@mod.route('/add/',methods=["GET", "POST",])
@mod.route('/add/<int:item_id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def add(item_id=None):
    item_id=cleanRecordID(item_id)
    item = None
    if item_id:
        item = Item(g.db).get(item_id)
    
    if not item:
        return "This is not a valid item id"
    
    g.inv_item_id = item_id
    
    return edit(0)
    
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
            rec.created = datetime.now()
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
        if id == 0:
            rec = transaction.new()
        else:
            rec = transaction.get(id)
            if not rec:
                flash('Record not found when trying to save')
                return redirect(g.listURL)
                
        transaction.update(rec,request.form)
        if validate_form(rec):
            transaction.save(rec)
            try:
                g.db.commit()
                #Save the date and comment to session
                session['last_trx'] = {"created":rec.created,"note":rec.note}
                return redirect(g.listURL)
                
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save Transaction record',str(e)))
                return redirect(g.listURL)
        else:
            current_item = Item(g.db).get(cleanRecordID(request.form.get('item_id',"0")))
        #    rec = transaction.new()
        #    transaction.update(rec,request.form)
                    
    return render_template('trx_edit.html',rec=rec,current_item=current_item,items=items)


    
@mod.route('/delete',methods=["GET", "POST",])
@mod.route('/delete/',methods=["GET", "POST",])
@mod.route('/delete/<int:id>/',methods=["GET", "POST",])
@table_access_required(Transaction)
def delete(id=None):
    setExits()
    if id == None:
        id = request.form.get('id',request.args.get('id',-1))
    
    id = cleanRecordID(id)
    if id <=0:
        flash("That is not a valid record ID")
        return redirect(g.listURL)
        
    rec = Transaction(g.db).get(id)
    if not rec:
        flash("Record not found")
    else:
        Transaction(g.db).delete(rec.id)
        g.db.commit()
        flash("Record Deleted")
        
    return redirect(g.listURL)
    
    
def validate_form(rec):
    valid_form = True
    datestring = request.form.get('created','').strip()
    if datestring == '':
        valid_form = False
        flash('Date may not be empty')
        
    if str_to_short_date(datestring) is None:
        flash('Date is not in a known format ("mm/dd/yy")')
        valid_form = False
    
    #Try to coerse qty to a number
    try:
        rec.qty = float(request.form.get('qty',0))
        if rec.qty - int(rec.qty) == 0:
            rec.qty = int(rec.qty)
    except ValueError as e:
        flash('Could not convert Qty {} to a number'.format(request.form.get('qty',"")))
        valid_form = False
    
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
        
    return valid_form