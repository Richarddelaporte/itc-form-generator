"""
Feedback routes — user feedback and learning system.
"""

import json
import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/submit', methods=['POST'])
def submit_feedback():
    """Submit feedback for a generated form."""
    try:
        data = request.get_json()
        if not data:
            return jsonify(error="No data provided"), 400

        store = current_app.services['feedback_store']
        from itc_form_generator.feedback_store import create_feedback_entry

        entry = create_feedback_entry(
            system_type=data.get('system_type', ''),
            feedback_type=data.get('feedback_type', 'general'),
            feedback_text=data.get('feedback_text', ''),
            section_name=data.get('section_name', ''),
            check_item=data.get('check_item', ''),
            rating=data.get('rating', 0),
        )
        store.add_feedback(entry)

        return jsonify(success=True, message="Feedback recorded. Thank you!")

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return jsonify(error=str(e)), 500


@feedback_bp.route('/stats', methods=['GET'])
def feedback_stats():
    """Get feedback statistics."""
    try:
        store = current_app.services['feedback_store']
        stats = store.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify(error=str(e)), 500


@feedback_bp.route('/context', methods=['GET'])
def feedback_context():
    """Get feedback context for a system type."""
    system_type = request.args.get('system_type', '')
    try:
        store = current_app.services['feedback_store']
        context = store.get_context(system_type)
        return jsonify(context)
    except Exception as e:
        return jsonify(error=str(e)), 500

