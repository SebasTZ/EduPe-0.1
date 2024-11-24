from flask import Blueprint, render_template

test_page = Blueprint('test_page', __name__)

@test_page.route('/test')
def Test():
    return render_template('/pages/test/TestPage.html')