from flask import Blueprint

new_bp = Blueprint('new', __name__,
                   url_prefix='/new',
                   template_folder='templates')


@new_bp.route('/', methods=['GET', 'POST'])
def new_function():
    pass
