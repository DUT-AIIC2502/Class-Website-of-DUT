from flask import Blueprint, redirect, session

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def main():
    session["table_name"] = "student_info_AIIC2502"
    return redirect('/info_management', code=302, Response=None)
