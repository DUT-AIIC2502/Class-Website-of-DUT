from flask import Blueprint, request, render_template, redirect, url_for, session, g

new_bp = Blueprint('new', __name__,
                   url_prefix='/new',
                   template_folder='templates')


@new_bp.route('/', methods=['GET', 'POST'])
def new_function():
    pass
