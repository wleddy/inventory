from flask import Flask, render_template, g, session, url_for, request, redirect
from flask_mail import Mail

from takeabeltof.database import Database
from takeabeltof.utils import send_static_file
from takeabeltof.jinja_filters import register_jinja_filters
from users.models import User,Role,init_db, Pref
from users.admin import Admin

from inventory.models import init_tables, Item, Uom, Transaction, Category

# Create app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('site_settings.py', silent=True)


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)


# Create a mailer obj
mail = Mail(app)


def get_db(filespec=app.config['DATABASE_PATH']):
    if 'db' not in g:
        g.db = Database(filespec).connect()
    return g.db

from takeabeltof.jinja_filters import register_jinja_filters
register_jinja_filters(app)
from inventory.utils import register_inv_filters
register_inv_filters(app)
        
@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))
        
    get_db()
    
    # Is the user signed in?
    g.user = None
    if 'user' in session:
        g.user = session['user']
        
    if 'admin' not in g:
        g.admin = Admin(g.db)
        # Add items to the Admin menu
        # the order here determines the order of display in the menu
        
        # a header row must have the some permissions or higher than the items it heads
        g.admin.register(User,url_for('user.display'),display_name='User Admin',header_row=True,minimum_rank_required=500)
            
        g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
        g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=1000)
        g.admin.register(Pref,url_for('pref.display'),display_name='Prefs',minimum_rank_required=1000)
        
        g.admin.register(Item,None,display_name='Inv Admin',header_row=True,minimum_rank_required=500)
        g.admin.register(Item,url_for('item.display'),minimum_rank_required=1)
        g.admin.register(Category,url_for('category.display'),display_name='Categories',minimum_rank_required=500)
        g.admin.register(Uom,url_for('uom.display'),display_name='UOM',minimum_rank_required=500)
        g.admin.register(Transaction,url_for('transaction.display'),display_name='Transactions',minimum_rank_required=500)


@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()


@app.errorhandler(404)
def page_not_found(error):
    from takeabeltof.utils import handle_request_error
    handle_request_error(error,request,404)
    g.title = "Page Not Found"
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    from takeabeltof.utils import handle_request_error
    handle_request_error(error,request,500)
    g.title = "Server Error"
    return render_template('500.html'), 500

@app.route('/static_instance/<path:filename>')
def static_instance(filename):
    return send_static_file(filename)

from www.views import home
app.register_blueprint(home.mod)


from users.views import user, login, role, pref
app.register_blueprint(user.mod)
app.register_blueprint(login.mod)
app.register_blueprint(role.mod)
app.register_blueprint(pref.mod)

from inventory.views import item, category, uom, transaction
app.register_blueprint(item.mod)
app.register_blueprint(category.mod)
app.register_blueprint(uom.mod)
app.register_blueprint(transaction.mod)


if __name__ == '__main__':
    with app.app_context():
        init_db(get_db())
        init_tables(get_db())
        get_db().close()
        
    #app.run(host='172.20.10.2', port=5000)
    app.run()
    