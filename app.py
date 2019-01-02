from flask import Flask, render_template, g, session, url_for, request, redirect, flash, abort
from flask_mail import Mail
from takeabeltof.database import Database
from takeabeltof.utils import send_static_file
from takeabeltof.jinja_filters import register_jinja_filters
from users.models import User,Role,Pref
from users.admin import Admin
import os    

# Create app
# setting static_folder to None allows me to handle loading myself
app = Flask(__name__, instance_relative_config=True,
        static_folder=None)
app.config.from_pyfile('site_settings.py', silent=True)


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)

register_jinja_filters(app)
from inventory.utils import register_inv_filters
register_inv_filters(app)


mail = Mail(app)

def init_db(db=None):
    # to support old code
    initalize_all_tables(db)

def initalize_all_tables(db=None):
    """Place code here as needed to initialze all the tables for this site"""
    if not db:
        db = get_db()
        
    from users.models import init_db as users_init_db 
    users_init_db(db)
    from inventory.models import init_tables as inv_init_db
    inv_init_db(db)
    

def update_config_for_host():
    # update settings for the requested host
    #import pdb;pdb.set_trace()
    
    # if there is no request this function will error out
    # check to see if the property we need is available
    request_in_flight = True
    try:
        request.url
    except:
        request_in_flight = False
        
    if request_in_flight and "SUB_DOMAIN_SETTINGS" in app.config and len(app.config["SUB_DOMAIN_SETTINGS"]) > 0:
        try:
            server = None
            for value in app.config['SUB_DOMAIN_SETTINGS']:
                if value.get('host_name') == request.host:
                    server = value
                    break

            if not server:
                #did not find a server to match, use default
                raise ValueError
            
            for key, value in server.items():
                app.config[key.upper()] = value
            
            # refresh mail since settings changed
            mail = Mail(app)
            
        except:
            # Will use the default settings
            if app.config['DEBUG']:
                #raise ValueError("SUB_DOMAIN_SETTINGS could not be determined")
                flash("Using Default SUB_DOMAIN_SETTINGS")
    
        
def get_app_config():
    """Returns a copy of the current app.config.
    This makes it possible for other modules to get access to the config
    with the values as updated for the current host.
    Import this method rather than importing app
    """
    #import pdb;pdb.set_trace()
    update_config_for_host()
    return app.config

    
def get_db(filespec=None):
    """Return a connection to the database.
    If the db path does not exist, create it and initialize the db"""
    
    if not filespec:
        filespec = app.config['DATABASE_PATH']
        
    initialize = False
    if 'db' not in g:
        # test the path, if not found, create it
        root_path = os.path.dirname(os.path.abspath(__name__))
        if not os.path.isfile(os.path.join(root_path,filespec)):
            initialize = True
            # split it into directories and create them if needed
            path_list = filespec.split("/")
            current_path = root_path
            for d in range(len(path_list)-1):
                current_path = os.path.join(current_path,path_list[d])
                if not os.path.isdir(current_path):
                    os.mkdir(current_path, mode=0o744)
                    
        
    g.db = Database(filespec).connect()
    if initialize:
        initalize_all_tables(g.db)
            
    return g.db


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))

    #ensure that nothing is served from the instance directory
    if 'instance' in request.url:
        abort(404)
    
    update_config_for_host()
    
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
        
        from inventory.models import Item,Category,Uom,Transaction
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

@app.route('/static/<path:filename>')
def static(filename):
    """This takes full responsibility for loading static content"""
        
    local_path = None
    if "LOCAL_STATIC_FOLDER" in app.config:
        local_path = app.config['LOCAL_STATIC_FOLDER']

    return send_static_file(filename,local_path=local_path)

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
        # create the default database if needed
        initalize_all_tables()
        
    #app.run(host='localhost', port=8000)
    app.run()
    
