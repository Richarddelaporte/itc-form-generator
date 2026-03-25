"""
Main page routes — serves the upload page and results.
"""

import os
from flask import Blueprint, render_template, current_app, send_from_directory

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Serve the main upload page."""
    pdf_supported = False
    excel_supported = False
    try:
        from itc_form_generator.pdf_parser import check_pdf_support
        pdf_status = check_pdf_support()
        pdf_supported = pdf_status.get('available', False)
    except Exception:
        pass
    try:
        from itc_form_generator.exporter import check_excel_support
        excel_supported = check_excel_support()
    except Exception:
        pass

    return render_template('index.html',
                         app_version=current_app.config['APP_VERSION'],
                         pdf_supported=pdf_supported,
                         excel_supported=excel_supported)


@main_bp.route('/results/<session_id>')
def results(session_id):
    """Serve the results page for a generation session."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return render_template('error.html', message="Session not found or expired."), 404

    return render_template('results.html',
                         session=session_data,
                         session_id=session_id)


@main_bp.route('/preview/<session_id>/<filename>')
def preview(session_id, filename):
    """Preview a generated form as HTML."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return "Session not found", 404

    output_dir = session_data.get('output_dir', '')
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

