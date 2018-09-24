from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from users.utils import printException, cleanRecordID
from datetime import datetime
from inventory.models import Item, Category, Uom, Transaction

mod = Blueprint('uom',__name__, template_folder='../templates', url_prefix='/uom')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Unit of Measure'

@mod.route('/',methods=["GET",])
@table_access_required(Uom)
def display():
    setExits()
    
    recs = Uom(g.db).select()

    return render_template('uom_list.html',recs=recs,)
    
    
@mod.route('/edit',methods=["GET", "POST",])
@mod.route('/edit/',methods=["GET", "POST",])
@mod.route('/edit/<int:id>/',methods=["GET", "POST",])
@table_access_required(Uom)
def edit(id=None):
    setExits()
    
    uom = Uom(g.db)
    
    if request.form:
        id = request.form.get('id',None)
    id = cleanRecordID(id)
    
    if id >= 0 and not request.form:
        if id == 0:
            rec = uom.new()
        else:
            rec = uom.get(id)
            
        if rec:
            return render_template('uom_edit.html',rec=rec)
        else:
            flash('Record not Found')
            
            
    if request.form:
        if not validate_form():
            return render_template('uom_edit.html', rec=request.form)
            
        if id == 0:
            rec = uom.new()
        else:
            rec = uom.get(id)
        if rec:
            uom.update(rec,request.form)
            uom.save(rec)
            try:
                g.db.commit()
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save Uom record',str(e)))
                return redirect(g.listURL)
        else:
            flash('Record not Found')
        
        
    return redirect(g.listURL)
    
    
@mod.route('/delete',methods=["GET", "POST",])
@mod.route('/delete/',methods=["GET", "POST",])
@mod.route('/delete/<int:id>/',methods=["GET", "POST",])
@table_access_required(Uom)
def delete(id=None):
    setExits()
    if id == None:
        id = request.form.get('id',request.args.get('id',-1))
    
    id = cleanRecordID(id)
    if id <=0:
        flash("That is not a valid record ID")
        return redirect(g.listURL)
        
    rec = Uom(g.db).get(id)
    if not rec:
        flash("Record not found")
    else:
        Uom(g.db).delete(rec.id)
        g.db.commit()
        flash("Record Deleted")
        
    return redirect(g.listURL)
    
    
def validate_form():
    valid_form = True
    if request.form['name'].strip() == '':
        valid_form = False
        flash('The name may not be empty')
        
    return valid_form