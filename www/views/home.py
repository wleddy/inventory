from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from datetime import datetime
import mistune # for Markdown rendering
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

    rendered_html = render_markdown_for(mod,'index.md')

    return render_template('markdown.html',rendered_html=rendered_html,)


@mod.route('/about', methods=['GET',])
@mod.route('/about/', methods=['GET',])
def about():
    setExits()
    g.title = "About"
    
    rendered_html = render_markdown_for(mod,'about.md')
            
    return render_template('markdown.html',rendered_html=rendered_html)


@mod.route('/contact', methods=['POST', 'GET',])
@mod.route('/contact/', methods=['POST', 'GET',])
def contact():
    setExits()
    g.name = 'Contact Us'
    from app import app
    from users.mailer import send_message
    rendered_html = render_markdown_for(mod,'contact.md')
    show_form = True
    context = {}
    if request.form:
        if request.form['name'] and request.form['email'] and request.form['comment']:
            context['name'] = request.form['name']
            context['email'] = request.form['email']
            context['comment'] = request.form['comment']
            context['date'] = datetime.now().isoformat(sep=" ")
            print(context)
            send_message(
                None,
                subject = "Comment from {}".format(app.config['SITE_NAME']),
                html_template = "home/email/contact_email.html",
                context = context,
                reply_to = request.form['email'],
            )
        
            show_form = False
        else:
            context = request.form
            flash('You left some stuff out.')
            
    
    return render_template('contact.html',rendered_html=rendered_html, show_form=show_form, context=context)
    
    
@mod.route('/robots.txt', methods=['GET',])
def robots():
    resp = Response("""User-agent: *
Disallow: /""" )
    resp.headers['content-type'] = 'text/plain'
    return resp


def render_markdown_for(mod,file_name):
    """Try to find the file to render and then do so"""
    rendered_html = ''
    # use similar search approach as flask templeting, root first, then local
    # try to find the root templates directory
    markdown_path = os.path.dirname(os.path.abspath(__name__)) + '/templates/{}'.format(file_name)
    if not os.path.isfile(markdown_path):
        # look in the templates directory of the calling blueprint
        markdown_path = os.path.dirname(os.path.abspath(__file__)) + '/{}/{}'.format(mod.template_folder,file_name)
    if os.path.isfile(markdown_path):
        f = open(markdown_path)
        rendered_html = f.read()
        f.close()
        rendered_html = mistune.markdown(rendered_html)

    return rendered_html
    