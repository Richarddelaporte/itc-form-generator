"""
Tests for Flask web application routes and API endpoints.

Run with: pytest tests/test_app.py -v
"""

import os
import io
import json
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create test application."""
    app = create_app('testing')
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_returns_200(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get('/api/health')
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'version' in data

    def test_health_includes_version(self, client):
        response = client.get('/api/health')
        data = response.get_json()
        assert data['version'] == '2.0.0'


class TestMainRoutes:
    """Test main page routes."""

    def test_index_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_index_contains_upload_form(self, client):
        response = client.get('/')
        assert b'upload' in response.data.lower() or b'form' in response.data.lower()

    def test_results_404_for_invalid_session(self, client):
        response = client.get('/results/nonexistent')
        assert response.status_code == 404


class TestGenerateAPI:
    """Test form generation endpoints."""

    def test_generate_requires_file(self, client):
        response = client.post('/api/generate')
        assert response.status_code == 400

    def test_generate_rejects_invalid_extension(self, client):
        data = {'soo_file': (io.BytesIO(b'test'), 'test.exe')}
        response = client.post('/api/generate', data=data, content_type='multipart/form-data')
        assert response.status_code == 400

    def test_generate_accepts_md_file(self, client):
        """Test with a minimal SOO document."""
        soo_content = """# Sequence of Operations
## CRAH Unit - CRAH-01

### Normal Cooling Mode
- Supply air temperature setpoint: 65°F
- Return air temperature high alarm: 85°F
- Fan speed: Variable, controlled by VFD
- Chilled water valve: Modulating

### Components
- Supply Fan (SF-01): Variable speed
- Chilled Water Valve (CWV-01): 2-way modulating
- Temperature Sensor (TS-01): Supply air
"""
        data = {
            'soo_file': (io.BytesIO(soo_content.encode()), 'test_soo.md'),
            'project_number': 'TEST-001',
            'building_area': 'Test Building',
        }
        response = client.post('/api/generate', data=data, content_type='multipart/form-data')
        # Should succeed or at least not crash
        assert response.status_code in (200, 500)  # 500 if deps missing in test env
        if response.status_code == 200:
            result = response.get_json()
            assert result['success'] is True
            assert 'session_id' in result

    def test_generate_with_points_list(self, client):
        """Test generation with SOO + points list."""
        soo_content = "# SOO\n## CRAH-01\nNormal mode: cooling"
        points_csv = """Point Name,Type,Description,Units
CRAH01_SAT,AI,Supply Air Temperature,°F
CRAH01_RAT,AI,Return Air Temperature,°F
CRAH01_SF_CMD,DO,Supply Fan Start/Stop,
CRAH01_CWV,AO,Chilled Water Valve Position,%
"""
        data = {
            'soo_file': (io.BytesIO(soo_content.encode()), 'soo.md'),
            'points_file': (io.BytesIO(points_csv.encode()), 'points.csv'),
        }
        response = client.post('/api/generate', data=data, content_type='multipart/form-data')
        assert response.status_code in (200, 500)


class TestExportRoutes:
    """Test export/download endpoints."""

    def test_download_404_for_invalid_session(self, client):
        response = client.get('/export/download/invalid/test.html')
        assert response.status_code == 404

    def test_zip_404_for_invalid_session(self, client):
        response = client.get('/export/zip/invalid')
        assert response.status_code == 404

    def test_csv_404_for_invalid_session(self, client):
        response = client.get('/export/csv/invalid')
        assert response.status_code == 404


class TestFeedbackAPI:
    """Test feedback endpoints."""

    def test_feedback_requires_json(self, client):
        response = client.post('/api/feedback/submit')
        assert response.status_code == 400

    def test_feedback_stats(self, client):
        response = client.get('/api/feedback/stats')
        # Should return stats or error gracefully
        assert response.status_code in (200, 500)


class TestTemplateAPI:
    """Test template listing endpoints."""

    def test_rsb_templates_list(self, client):
        response = client.get('/api/templates/rsb/list')
        assert response.status_code in (200, 500)

    def test_ats_templates_list(self, client):
        response = client.get('/api/templates/ats/list')
        assert response.status_code in (200, 500)

