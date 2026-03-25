"""
Template API routes — RSB, ATS, and other pre-built templates.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/rsb/list', methods=['GET'])
def rsb_templates():
    """List available RSB templates."""
    try:
        from itc_form_generator.rsb_templates import get_available_templates
        templates = get_available_templates()
        return jsonify(templates=templates)
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/rsb/variants', methods=['GET'])
def rsb_variants():
    """Get RSB template variants."""
    try:
        from itc_form_generator.rsb_templates import get_variants
        return jsonify(variants=get_variants())
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/rsb/areas', methods=['GET'])
def rsb_areas():
    """Get RSB area options."""
    try:
        from itc_form_generator.rsb_templates import get_areas
        return jsonify(areas=get_areas())
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/ats/list', methods=['GET'])
def ats_templates():
    """List available ATS templates."""
    try:
        from itc_form_generator.ats_templates import get_available_templates
        templates = get_available_templates()
        return jsonify(templates=templates)
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/ats/variants', methods=['GET'])
def ats_variants():
    """Get ATS variants."""
    try:
        from itc_form_generator.ats_templates import get_variants
        return jsonify(variants=get_variants())
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/ats/areas', methods=['GET'])
def ats_areas():
    """Get ATS area options."""
    try:
        from itc_form_generator.ats_templates import get_areas
        return jsonify(areas=get_areas())
    except Exception as e:
        return jsonify(error=str(e)), 500


@templates_bp.route('/ats/categories', methods=['GET'])
def ats_categories():
    """Get ATS categories."""
    try:
        from itc_form_generator.ats_templates import get_categories
        return jsonify(categories=get_categories())
    except Exception as e:
        return jsonify(error=str(e)), 500

