from flask import Blueprint, render_template

psychology_page = Blueprint('psychology_page', __name__)

@psychology_page.route('/psicologia')
def Psychology():
    return render_template('/pages/psychology/PsychologyPage.html')