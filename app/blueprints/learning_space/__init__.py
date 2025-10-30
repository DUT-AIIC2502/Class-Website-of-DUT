from flask import Blueprint

learning_space_bp = Blueprint('learning_space', __name__,
                   url_prefix='/learning_space',
                   template_folder='templates')

from . import home, study_notes