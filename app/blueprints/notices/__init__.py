# app/blueprints/notices/__init__.py

from flask import Blueprint

notices_bp = Blueprint('notices', __name__,
                       url_prefix='/notices',
                       template_folder='templates')

from . import notices, new_notices, private_message