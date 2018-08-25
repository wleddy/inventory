from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from users.utils import printException, cleanRecordID
from datetime import datetime
from inventory.models import Item, Category, Uom, Transaction

mod = Blueprint('item',__name__, template_folder='../templates', url_prefix='/items')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Inventory Item'

@mod.route('/',methods=["GET",])
@table_access_required(Item)
def display():
    setExits()
    
    recs = Item(g.db).select()
    
    #Get categories to display
    categories = Category(g.db)
    cats = {}
    if recs:
        for rec in recs:
            cat = categories.get(rec.cat_id)
            cats[rec.id] = cat.name
        

    return render_template('item_list.html',recs=recs,cats=cats)
    
    
@mod.route('/edit',methods=["GET", "POST",])
@mod.route('/edit/',methods=["GET", "POST",])
@mod.route('/edit/<int:id>/',methods=["GET", "POST",])
@table_access_required(Item)
def edit(id=None):
    setExits()
    
    item = Item(g.db)
    
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
            rec = item.new()
        else:
            rec = item.get(id)
            
        if not rec:
            flash('Record not Found')
            return redirect(g.listURL)
            
    if request.form:
        if not validate_form():
            rec = request.form
            
        if id == 0:
            rec = item.new()
        else:
            rec = item.get(id)
        if rec:
            item.update(rec,request.form)
            item.save(rec)
            try:
                g.db.commit()
                return redirect(g.listURL)
                    
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save Item record',str(e)))
                return redirect(g.listURL)
        else:
            flash('Record not Found')
            return redirect(g.listURL)
        
    return render_template('item_edit.html',rec=rec,categories=categories,uoms=uoms)


    
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
    
    
def validate_form():
    valid_form = True
    if request.form['name'].strip() == '':
        valid_form = False
        flash('The name may not be empty')
    
    return valid_form