from flask import Blueprint, render_template

wellbeing_page = Blueprint('wellbeing_page', __name__)

@wellbeing_page.route('/wellbeing')
def Wellbeing():
    return render_template('/pages/wellbeing/WellbeingPage.html')