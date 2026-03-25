"""
Export routes — file download, ZIP, CSV, Excel export.
"""

import io
import os
import csv
import zipfile
import logging
from flask import Blueprint, request, send_file, current_app, jsonify, send_from_directory

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)


@export_bp.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """Download a single generated file."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return jsonify(error="Session not found"), 404

    output_dir = session_data.get('output_dir', '')
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        return jsonify(error="File not found"), 404

    return send_from_directory(output_dir, filename, as_attachment=True)


@export_bp.route('/zip/<session_id>')
def download_zip(session_id):
    """Download all generated files as a ZIP archive."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return jsonify(error="Session not found"), 404

    output_dir = session_data.get('output_dir', '')
    project = session_data.get('project_number', 'itc_forms')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_info in session_data.get('files', []):
            filepath = os.path.join(output_dir, file_info['filename'])
            if os.path.exists(filepath):
                zf.write(filepath, file_info['filename'])

    zip_buffer.seek(0)
    zip_name = f"{project}_itc_forms.zip"
    return send_file(zip_buffer, mimetype='application/zip',
                     as_attachment=True, download_name=zip_name)


@export_bp.route('/csv/<session_id>')
def download_csv(session_id):
    """Export form check items as CSV."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return jsonify(error="Session not found"), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['System', 'Section', 'Check Item', 'Expected Value', 'Status'])

    for form in session_data.get('forms', []):
        system_name = form.get('name', 'Unknown')
        for section in form.get('sections', []):
            section_name = section.get('name', '')
            for item in section.get('items', []):
                writer.writerow([
                    system_name,
                    section_name,
                    item.get('description', ''),
                    item.get('expected_value', ''),
                    ''
                ])

    csv_bytes = output.getvalue().encode('utf-8')
    return send_file(
        io.BytesIO(csv_bytes),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{session_data.get('project_number', 'forms')}_checklist.csv"
    )


@export_bp.route('/excel/<session_id>')
def download_excel(session_id):
    """Export forms as Excel workbook."""
    session_data = current_app.sessions.get(session_id)
    if not session_data:
        return jsonify(error="Session not found"), 404

    try:
        exporter = current_app.services['exporter']
        project_number = session_data.get('project_number', '')

        # Use pre-converted InspectionForm objects if available
        inspection_forms = session_data.get('inspection_forms', [])
        if not inspection_forms:
            return jsonify(error="No exportable forms in session"), 400

        excel_bytes = exporter.export_to_acc_excel(inspection_forms, project_number=project_number)
        if not excel_bytes:
            return jsonify(error="Excel export not available (openpyxl missing)"), 500

        excel_buffer = io.BytesIO(excel_bytes)

        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{project_number or 'forms'}_itc_forms.xlsx"
        )
    except Exception as e:
        logger.error(f"ACC Excel export failed: {e}")
        return jsonify(error=f"Excel export failed: {str(e)}"), 500
