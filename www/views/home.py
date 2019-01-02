from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from users.admin import login_required, table_access_required
from takeabeltof.utils import render_markdown_for, printException, handle_request_error
from takeabeltof.date_utils import datetime_as_string
import os


mod = Blueprint('www',__name__, template_folder='../templates', url_prefix='')


def setExits():
    g.homeURL = url_for('.home')
    g.aboutURL = url_for('.about')
    g.contactURL = url_for('.contact')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()
    g.suppress_page_header = True
    rendered_html = render_markdown_for('index.md',mod)

    return render_template('markdown.html',rendered_html=rendered_html,)


@mod.route('/about', methods=['GET',])
@mod.route('/about/', methods=['GET',])
def about():
    setExits()
    g.title = "About"
    
    rendered_html = render_markdown_for('about.md',mod)
            
    return render_template('markdown.html',rendered_html=rendered_html)


@mod.route('/contact', methods=['POST', 'GET',])
@mod.route('/contact/', methods=['POST', 'GET',])
def contact():
    setExits()
    g.title = 'Contact Us'
    from app import app
    from takeabeltof.mailer import send_message
    rendered_html = render_markdown_for('contact.md',mod)
    
    show_form = True
    context = {}
    success = True
    passed_quiz = False
    mes = "No errors yet..."
    if request.form:
        #import pdb;pdb.set_trace()
        quiz_answer = request.form.get('quiz_answer',"A")
        if quiz_answer.upper() == "C":
            passed_quiz = True
        else:
            flash("You did not answer the quiz correctly.")
        if request.form['email'] and request.form['comment'] and passed_quiz:
            context.update({'date':datetime_as_string()})
            for key, value in request.form.items():
                context.update({key:value})
                
            # get best contact email
            to = []
            # See if the contact info is in Prefs
            try:
                from users.views.pref import get_contact_email
                contact_to = get_contact_email()
                if contact_to:
                    to.append(contact_to)
            except Exception as e:
                printException("Need to update home.contact to find contacts in prefs.","error",e)
                
            try:
                admin_to = None
                if not to:
                    to = [(app.config['CONTACT_NAME'],app.config['CONTACT_EMAIL_ADDR'],),]
                if app.config['CC_ADMIN_ON_CONTACT']:
                    admin_to = (app.config['MAIL_DEFAULT_SENDER'],app.config['MAIL_DEFAULT_ADDR'],)
                    
                if admin_to:
                    to.append(admin_to,)
                
            except KeyError as e:
                mes = "Could not get email addresses."
                mes = printException(mes,"error",e)
                if to:
                    #we have at least a to address, so continue
                    pass
                else:
                    success = False
                    
            if success:
                # Ok so far... Try to send
                success, mes = send_message(
                                    to,
                                    subject = "Contact from {}".format(app.config['SITE_NAME']),
                                    html_template = "home/email/contact_email.html",
                                    context = context,
                                    reply_to = request.form['email'],
                                )
        
            show_form = False
        else:
            context = request.form
            flash('You left some stuff out.')
            
    if success:
        return render_template('contact.html',rendered_html=rendered_html, show_form=show_form, context=context,passed_quiz=passed_quiz)
            
    handle_request_error(mes,request,500)
    flash(mes)
    return render_template('500.html'), 500
    
@mod.route('/docs', methods=['GET',])
@mod.route('/docs/', methods=['GET',])
@mod.route('/docs/<path:filename>', methods=['GET',])
def docs(filename=None):
    setExits()
    g.title = "Docs"
    from app import get_app_config
    app_config = get_app_config()
    
    #import pdb;pdb.set_trace()
    
    file_exists = False
    if not filename:
        filename = "README.md"
    else:
        filename = filename.strip('/')
        
    # first try to get it as a (possibly) valid path
    temp_path = os.path.join(os.path.dirname(os.path.abspath(__name__)),filename)
    if not os.path.isfile(temp_path):
        # try the default doc dir
        temp_path = os.path.join(os.path.dirname(os.path.abspath(__name__)),'docs',filename)
        
    if not os.path.isfile(temp_path) and 'DOC_DIRECTORY_LIST' in app_config:
        for path in app_config['DOC_DIRECTORY_LIST']:
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__name__)),path.strip('/'),filename)
            if os.path.isfile(temp_path):
                break
            
    filename = temp_path
    file_exists = os.path.isfile(filename)
            
    if file_exists:
        rendered_html = render_markdown_for(filename,mod)
        return render_template('markdown.html',rendered_html=rendered_html)
    else:
        #file not found
        abort(404)
    
@mod.route('/robots.txt', methods=['GET',])
def robots():
    resp = Response("""User-agent: *
Disallow: /""" )
    resp.headers['content-type'] = 'text/plain'
    return resp

