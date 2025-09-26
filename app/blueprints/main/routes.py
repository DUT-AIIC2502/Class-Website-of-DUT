from flask import Blueprint, redirect, request

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def main():
    # return "hello"
    return redirect('/info_management', code=302, Response=None)
