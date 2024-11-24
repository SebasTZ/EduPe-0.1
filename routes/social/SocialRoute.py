from flask import Blueprint, render_template

social_page = Blueprint('social_page', __name__)

@social_page.route('/social')
def Social():
    return render_template('/pages/social/SocialPage.html')