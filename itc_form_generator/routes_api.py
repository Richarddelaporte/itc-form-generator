"""
API routes — form generation, health checks, and core functionality.
"""

import io
import os
import time
import uuid
import json
import tempfile
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Nest/load balancers."""
    return jsonify({
        'status': 'healthy',
        'version': current_app.config['APP_VERSION'],
        'app': current_app.config['APP_NAME'],
    })


@api_bp.route('/generate', methods=['POST'])
def generate():
    """Generate ITC forms from uploaded SOO document and optional points list.

    Accepts multipart form data with:
    - soo_file: SOO document (required, .md/.txt/.pdf)
    - points_file: Points list (optional, .csv/.xlsx)
    - project_number: Project identifier
    - building_area: Building/area name
    - use_ai: Enable AI-enhanced parsing (default: true)
    """
    try:
        # Validate required file
        if 'soo_file' not in request.files:
            return jsonify(error='No SOO file uploaded'), 400

        soo_file = request.files['soo_file']
        if not soo_file.filename:
            return jsonify(error='No file selected'), 400

        # Validate file extension
        allowed = current_app.config['UPLOAD_EXTENSIONS']
        soo_ext = os.path.splitext(soo_file.filename)[1].lower()
        if soo_ext not in allowed:
            return jsonify(error=f'Unsupported file type: {soo_ext}'), 400

        # Parse form data
        project_number = request.form.get('project_number', '').strip()
        building_area = request.form.get('building_area', '').strip()
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'

        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        output_dir = os.path.join(current_app.config['OUTPUT_DIR'], session_id)
        os.makedirs(output_dir, exist_ok=True)

        services = current_app.services

        # Read SOO document
        soo_content = ''
        if soo_ext == '.pdf':
            from itc_form_generator.pdf_parser import PDFParser
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                soo_file.save(tmp.name)
                pdf_parser = PDFParser()
                soo_content = pdf_parser.parse(tmp.name)
                os.unlink(tmp.name)
        else:
            soo_content = soo_file.read().decode('utf-8', errors='replace')

        if not soo_content.strip():
            return jsonify(error='SOO document is empty or could not be read'), 400

        # Parse points list if provided
        points_list = None
        points_file = request.files.get('points_file')
        if points_file and points_file.filename:
            pts_ext = os.path.splitext(points_file.filename)[1].lower()
            if pts_ext in ('.csv', '.tsv'):
                pts_content = points_file.read().decode('utf-8', errors='replace')
                points_list = services['points_parser'].parse(pts_content, points_file.filename)
            elif pts_ext in ('.xlsx', '.xls'):
                with tempfile.NamedTemporaryFile(suffix=pts_ext, delete=False) as tmp:
                    points_file.save(tmp.name)
                    points_list = services['points_parser'].parse(tmp.name, points_file.filename)
                    os.unlink(tmp.name)

        # Parse SOO document
        parser = services['parser']
        soo_data = parser.parse(soo_content)

        # Detect document/equipment types
        from itc_form_generator.parser import detect_document_type
        detected_types = detect_document_type(soo_content)

        # Check for MUA-specific content
        from itc_form_generator.mua_parser import MUASOOParser
        mua_parser = MUASOOParser()
        is_mua = 'mua' in soo_content.lower() or 'make-up air' in soo_content.lower() or 'make up air' in soo_content.lower()

        # Generate forms
        forms = []
        generator = services['form_generator']

        if is_mua:
            from itc_form_generator.mua_form_generator import generate_mua_form
            mua_forms = generate_mua_form(soo_content, project_number, building_area)
            forms.extend(mua_forms)
        else:
            generated = generator.generate(
                soo_data=soo_data,
                project_number=project_number,
                building_area=building_area,
                points_list=points_list,
                detected_types=detected_types,
            )
            forms.extend(generated)

        # Export forms
        exporter = services['exporter']
        exported_files = []
        for form in forms:
            # Render to HTML
            from itc_form_generator.renderer import HTMLRenderer
            renderer = HTMLRenderer()
            html_content = renderer.render(form)

            filename = f"{form.get('system_type', 'form')}_{form.get('name', 'output')}.html"
            filename = secure_filename(filename)
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            exported_files.append({
                'filename': filename,
                'system_type': form.get('system_type', 'Unknown'),
                'name': form.get('name', ''),
                'sections': len(form.get('sections', [])),
            })

            # Also export to Excel if supported
            try:
                excel_filename = filename.replace('.html', '.xlsx')
                excel_path = os.path.join(output_dir, excel_filename)
                exporter.export_to_excel(form, excel_path)
                exported_files.append({
                    'filename': excel_filename,
                    'system_type': form.get('system_type', 'Unknown'),
                    'name': form.get('name', '') + ' (Excel)',
                    'format': 'excel',
                })
            except Exception as e:
                logger.warning(f"Excel export failed: {e}")

        elapsed = round(time.time() - start_time, 2)

        # Store session data
        current_app.sessions[session_id] = {
            'forms': forms,
            'files': exported_files,
            'output_dir': output_dir,
            'project_number': project_number,
            'building_area': building_area,
            'detected_types': detected_types,
            'points_summary': points_list.summary if points_list else None,
            'elapsed_time': elapsed,
            'created_at': time.time(),
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'forms_generated': len(forms),
            'files': exported_files,
            'elapsed_seconds': elapsed,
            'detected_types': detected_types,
            'points_summary': points_list.summary if points_list else None,
            'results_url': f'/results/{session_id}',
        })

    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        return jsonify(error=f'Generation failed: {str(e)}'), 500


@api_bp.route('/generate/template', methods=['POST'])
def generate_from_template():
    """Generate forms from pre-built templates (RSB, ATS, etc.)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify(error='No data provided'), 400

        template_type = data.get('template_type', '').upper()
        project_number = data.get('project_number', '')
        building_area = data.get('building_area', '')
        variant = data.get('variant', '')
        area = data.get('area', '')
        level = data.get('level', 'L1')

        session_id = str(uuid.uuid4())[:8]
        output_dir = os.path.join(current_app.config['OUTPUT_DIR'], session_id)
        os.makedirs(output_dir, exist_ok=True)

        start_time = time.time()

        # Import template generators
        if template_type == 'RSB':
            from itc_form_generator.rsb_templates import generate_rsb_form
            form_data = generate_rsb_form(
                variant=variant, area=area, level=level,
                project_number=project_number, building_area=building_area
            )
        elif template_type == 'ATS':
            from itc_form_generator.ats_templates import generate_ats_form
            form_data = generate_ats_form(
                variant=variant, area=area, level=level,
                project_number=project_number, building_area=building_area
            )
        else:
            return jsonify(error=f'Unknown template type: {template_type}'), 400

        # Render and save
        from itc_form_generator.renderer import HTMLRenderer
        renderer = HTMLRenderer()
        html_content = renderer.render(form_data)

        filename = f"{template_type}_{variant}_{area}.html"
        filename = secure_filename(filename)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        elapsed = round(time.time() - start_time, 2)

        current_app.sessions[session_id] = {
            'forms': [form_data],
            'files': [{'filename': filename, 'system_type': template_type, 'name': f'{template_type} {variant}'}],
            'output_dir': output_dir,
            'project_number': project_number,
            'building_area': building_area,
            'elapsed_time': elapsed,
            'created_at': time.time(),
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'html': html_content,
            'results_url': f'/results/{session_id}',
        })

    except Exception as e:
        logger.error(f"Template generation failed: {e}", exc_info=True)
        return jsonify(error=str(e)), 500
