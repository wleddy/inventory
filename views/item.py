from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from inventory.models import Item, Category, Uom, Transaction, Warehouse
from .item_reports import stock_on_hand_report
from inventory.views.transaction import get_list_for_item

mod = Blueprint('item',__name__, template_folder='templates/inventory', static_folder='static/inventory', url_prefix='/items')


def setExits():
    g.listURL = url_for('item.display')
    g.editURL = url_for('item.edit')
    g.deleteURL = url_for('item.delete')
    g.title = 'Inventory Item'
    g.stock_reportURL = url_for('item.stock_report')
    g.trxListFromItemURL = url_for('item.transaction_list_for_item')

@mod.route('/',methods=["GET",])
@table_access_required(Item)
def display():
    setExits()
    g.title = "{} List".format(g.title)
    recs = Item(g.db).select()
    
    return render_template('item_list.html',recs=recs)
    
    
@mod.route('/edit',methods=["GET", "POST",])
@mod.route('/edit/',methods=["GET", "POST",])
@mod.route('/edit/<int:id>/',methods=["GET", "POST",])
@table_access_required(Item)
def edit(id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)
    
    item = Item(g.db)
    transactionList = None
    #import pdb;pdb.set_trace()
    if request.form:
        id = request.form.get('id',None)
    
    id = cleanRecordID(id)
    
    if id < 0:
        flash("Invalid Record ID")
        return redirect(g.listURL)
    
    categories = Category(g.db).select()
    uoms = Uom(g.db).select()
    
    if id >= 0 and not request.form:
        if id == 0:
            rec = item.new() # allow creation of new properties
            item.save(rec) # need an id for transactions
            g.db.commit() # have to commit this to protect the ID we just got
            # This name changes behavure of the Cancel link in the edit form
            g.cancelURL = url_for('.cancel') + "{}/".format(rec.id)
            
        else:
            rec = item.get(id)
            
        if not rec:
            flash('Record not Found')
            return redirect(g.listURL)
            
    #import pdb;pdb.set_trace()
    on_hand = item.stock_on_hand(id)
                
    if request.form:
        rec = item.get(id)
        if rec:
            item.update(rec,request.form)
            if validate_form():
                item.save(rec)
                try:
                    g.db.commit()
                    return redirect(g.listURL)
                
                except Exception as e:
                    g.db.rollback()
                    flash(printException('Error attempting to save Item record',str(e)))
                    return redirect(g.listURL)
            else:
                pass # There are imput errors
                
        else:
            flash('Record not Found')
            return redirect(g.listURL)
            
    transactionList = get_list_for_item(rec.id)
    
    return render_template('item_edit.html',rec=rec,categories=categories,uoms=uoms,transactionList=transactionList,on_hand=on_hand)

@mod.route('/cancel',methods=["GET", "POST",])
@mod.route('/cancel/',methods=["GET", "POST",])
@mod.route('/cancel/<int:id>/',methods=["GET", "POST",])
@table_access_required(Item)
def cancel(id=None):
    """If user canceled a new record come here to delete the record stub"""
    setExits()
    
    if id:
        try:
            Item(g.db).delete(id)
            g.db.commit()
        except:
            flash("Could not delete temporary Item with id = {}".format(id))
        
        
    return redirect(g.listURL)
    

@mod.route('/get_stock_on_hand',methods=["GET",])
@mod.route('/get_stock_on_hand/',methods=["GET",])
@mod.route('/get_stock_on_hand/<int:item_id>',methods=["GET",])
@mod.route('/get_stock_on_hand/<int:item_id>/',methods=["GET",])
def get_stock_on_hand(item_id=0):  
    return str(Item(g.db).stock_on_hand(cleanRecordID(item_id)))
    
    
@mod.route('/transaction_list_for_item',methods=["GET",])
@mod.route('/transaction_list_for_item/<int:item_id>',methods=["GET",])
@table_access_required(Item)
def transaction_list_for_item(item_id=None):
    setExits()
    return get_list_for_item(item_id)
    
    
@mod.route('/delete',methods=["GET", "POST",])
@mod.route('/delete/',methods=["GET", "POST",])
@mod.route('/delete/<int:id>/',methods=["GET", "POST",])
@table_access_required(Item)
def delete(id=None):
    setExits()
    if id == None:
        id = request.form.get('id',request.args.get('id',-1))
    
    id = cleanRecordID(id)
    if id <=0:
        flash("That is not a valid record ID")
        return redirect(g.listURL)
        
    rec = Item(g.db).get(id)
    if not rec:
        flash("Record not found")
    else:
        Item(g.db).delete(rec.id)
        g.db.commit()
        flash("Record Deleted")
        
    return redirect(g.listURL)
    
@mod.route('/stock_report',methods=["GET","POST",])
@mod.route('/stock_report/',methods=["GET","POST",])
@login_required
def stock_report():
    """Ask user for report date range then create report on post"""
    setExits()
    g.title = "Inventory Stock Report"
    start_date = None
    end_date = None
    warehouses = Warehouse(g.db).select()
    if request.form:
        start_date = getDatetimeFromString(request.form.get("start_date",None))
        end_date = getDatetimeFromString(request.form.get("end_date",None))
        warehouse_id = request.form.get('warehouse_id','-1')
        if start_date and end_date and start_date < end_date:
            return stock_on_hand_report(start_date,end_date,warehouse_id)
        else:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            flash("Those don't look like valid dates... Try 'YYYY-MM-DD'")
    ## else send form page
    if not start_date:
        start_date = local_datetime_now().replace(month=1, day=1)
    if not end_date:
        end_date = local_datetime_now().replace(month=12, day=31)
    
    return render_template('reports/item_report_input.html',start_date=start_date,end_date=end_date,warehouses=warehouses)
    
def validate_form():
    valid_form = True
    if request.form['name'].strip() == '':
        valid_form = False
        flash('The name may not be empty')
    
    if request.form['cat_id'] == None or request.form['cat_id'] == "0":
        valid_form = False
        flash('You must select a category for this item')
        
    return valid_form
    
