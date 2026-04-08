"""
API routes - form generation, health checks, and core functionality.
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
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': current_app.config.get('APP_VERSION', '2.0'),
        'app': current_app.config.get('APP_NAME', 'ITC Form Generator'),
    })


@api_bp.route('/generate', methods=['POST'])
def generate():
    """Generate ITC forms from uploaded SOO document and optional points list."""
    try:
        # Validate required file
        if 'soo_file' not in request.files:
            return jsonify(error='No SOO file uploaded'), 400

        soo_file = request.files['soo_file']
        if not soo_file.filename:
            return jsonify(error='No file selected'), 400

        # Validate file extension
        allowed = current_app.config.get('UPLOAD_EXTENSIONS', {'.md', '.txt', '.pdf'})
        soo_ext = os.path.splitext(soo_file.filename)[1].lower()
        if soo_ext not in allowed:
            return jsonify(error=f'Unsupported file type: {soo_ext}'), 400

        # Parse form data
        project_number = request.form.get('project_number', '').strip()
        building_area = request.form.get('building_area', '').strip()
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'

        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        output_dir = os.path.join(current_app.config.get('OUTPUT_DIR', '/tmp/itc_forms'), session_id)
        os.makedirs(output_dir, exist_ok=True)

        services = current_app.services

        # Read SOO document
        soo_content = ''
        if soo_ext == '.pdf':
            try:
                from itc_form_generator.pdf_parser import PDFParser
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    soo_file.save(tmp.name)
                    pdf_parser = PDFParser()
                    soo_content = pdf_parser.extract_text_from_file(tmp.name)
                    os.unlink(tmp.name)
            except ImportError:
                return jsonify(error='PDF parsing not available (pymupdf not installed)'), 500
        else:
            soo_content = soo_file.read().decode('utf-8', errors='replace')

        if not soo_content.strip():
            return jsonify(error='SOO document is empty or could not be read'), 400

        # Parse points list if provided
        points_list = None
        points_file = request.files.get('points_file')
        if points_file and points_file.filename:
            try:
                pts_ext = os.path.splitext(points_file.filename)[1].lower()
                if pts_ext in ('.csv', '.tsv'):
                    pts_content = points_file.read().decode('utf-8', errors='replace')
                    points_list = services['points_parser'].parse(pts_content, points_file.filename)
                elif pts_ext in ('.xlsx', '.xls'):
                    with tempfile.NamedTemporaryFile(suffix=pts_ext, delete=False) as tmp:
                        points_file.save(tmp.name)
                        points_list = services['points_parser'].parse(tmp.name, points_file.filename)
                        os.unlink(tmp.name)
            except Exception as e:
                logger.warning(f"Points list parsing failed: {e}")

        # Parse SOO document
        parser = services['parser']
        soo_data = parser.parse(soo_content)

        # Generate forms using FormGenerator
        FormGeneratorClass = services['form_generator_class']
        generator = FormGeneratorClass(soo_data, points_list=points_list)
        inspection_forms = generator.generate_all_forms()

        # Render each form to HTML and save
        exported_files = []
        try:
            from itc_form_generator.renderer import HTMLRenderer
            renderer = HTMLRenderer()
        except ImportError:
            renderer = None

        for form in inspection_forms:
            try:
                if renderer:
                    html_content = renderer.render(form)
                    # Build safe filename from form attributes
                    system_name = getattr(form, 'system', '') or 'form'
                    form_title = getattr(form, 'title', '') or 'output'
                    filename = f"{system_name}_{form_title}.html"
                    filename = secure_filename(filename)
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    exported_files.append({
                        'filename': filename,
                        'system_type': system_name,
                        'name': form_title,
                        'sections': len(getattr(form, 'sections', [])),
                    })
            except Exception as e:
                logger.warning(f"Form rendering failed: {e}")

        # Export to ACC Excel workbook
        if inspection_forms:
            try:
                exporter = services.get('exporter')
                if exporter:
                    excel_filename = secure_filename(f"{project_number or 'itc'}_acc_checklist.xlsx")
                    excel_path = os.path.join(output_dir, excel_filename)
                    excel_bytes = exporter.export_to_acc_excel(
                        inspection_forms,
                        project_number=project_number,
                    )
                    if excel_bytes:
                        with open(excel_path, 'wb') as ef:
                            ef.write(excel_bytes)
                        exported_files.append({
                            'filename': excel_filename,
                            'system_type': 'ACC',
                            'name': 'ACC Checklist (Excel)',
                            'format': 'excel',
                        })
            except Exception as e:
                logger.warning(f"ACC Excel export failed: {e}")

        elapsed = round(time.time() - start_time, 2)

        # Get points summary safely
        points_summary = None
        if points_list:
            points_summary = getattr(points_list, 'summary', None)
            if points_summary is None:
                points_summary = {'total_points': len(getattr(points_list, 'points', []))}

        # Store session data
        if not hasattr(current_app, 'sessions'):
            current_app.sessions = {}

        current_app.sessions[session_id] = {
            'forms': inspection_forms,
            'files': exported_files,
            'output_dir': output_dir,
            'project_number': project_number,
            'building_area': building_area,
            'points_summary': points_summary,
            'elapsed_time': elapsed,
            'created_at': time.time(),
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'forms_generated': len(inspection_forms),
            'files': exported_files,
            'elapsed_seconds': elapsed,
            'points_summary': points_summary,
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
        output_dir = os.path.join(current_app.config.get('OUTPUT_DIR', '/tmp/itc_forms'), session_id)
        os.makedirs(output_dir, exist_ok=True)
        start_time = time.time()

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

        from itc_form_generator.renderer import HTMLRenderer
        renderer = HTMLRenderer()
        html_content = renderer.render(form_data)

        filename = f"{template_type}_{variant}_{area}.html"
        filename = secure_filename(filename)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        elapsed = round(time.time() - start_time, 2)

        if not hasattr(current_app, 'sessions'):
            current_app.sessions = {}

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

    except ImportError as e:
        return jsonify(error=f'Template module not available: {e}'), 500
    except Exception as e:
        logger.error(f"Template generation failed: {e}", exc_info=True)
        return jsonify(error=str(e)), 500


@api_bp.route('/upload-example', methods=['POST'])
def upload_example():
    """Upload example forms for learning."""
    try:
        if 'example_file' not in request.files:
            return jsonify(error='No file provided'), 400

        file = request.files['example_file']
        if not file or not file.filename:
            return jsonify(error='No file selected'), 400

        from itc_form_generator.example_form_parser import get_example_store
        store = get_example_store()
        content = file.read().decode('utf-8', errors='replace')
        result = store.learn_from_example(content, file.filename)

        return jsonify(success=True, message=f'Learned from {file.filename}', details=result)
    except ImportError:
        return jsonify(error='Example form parser not available'), 500
    except Exception as e:
        return jsonify(error=str(e)), 500


@api_bp.route('/generate-integrated', methods=['POST'])
def generate_integrated():
    """Generate forms using integrated template system."""
    try:
        services = current_app.services
        soo_file = request.files.get('soo_file')
        if not soo_file:
            return jsonify(error='No SOO file provided'), 400

        soo_content = soo_file.read().decode('utf-8', errors='replace')
        template_type = request.form.get('template_type', 'auto')
        project_number = request.form.get('project_number', '')
        building_area = request.form.get('building_area', '')

        parser = services['parser']
        soo_data = parser.parse(soo_content)

        from itc_form_generator.template_integration import generate_integrated_form
        result = generate_integrated_form(
            soo_data=soo_data,
            template_type=template_type,
            project_number=project_number,
            building_area=building_area,
        )

        return jsonify(success=True, forms=result)
    except ImportError:
        return jsonify(error='Template integration module not available'), 500
    except Exception as e:
        return jsonify(error=str(e)), 500


@api_bp.route('/examples/stats', methods=['GET'])
def examples_stats():
    """Get example learning statistics."""
    try:
        from itc_form_generator.example_form_parser import get_example_store
        store = get_example_store()
        stats = store.get_stats() if hasattr(store, 'get_stats') else {'total': 0, 'types': {}}
        return jsonify(stats)
    except ImportError:
        return jsonify(total=0, types={})
    except Exception as e:
        return jsonify(total=0, types={}, error=str(e))
