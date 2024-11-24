from flask import Blueprint, render_template

selfesteem_page = Blueprint('selfesteem_page', __name__)

@selfesteem_page.route('/selfesteem')
def Selfesteem():
    return render_template('/pages/selfesteem/SelfesteemPage.html')