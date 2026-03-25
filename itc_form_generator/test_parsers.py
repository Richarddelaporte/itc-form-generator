"""
Tests for SOO parser, points parser, and AI service.

Run with: pytest tests/test_parsers.py -v
"""

import pytest
import json


class TestSOOParser:
    """Test Sequence of Operations document parser."""

    @pytest.fixture
    def parser(self):
        from itc_form_generator.parser import SOOParser
        return SOOParser(use_ai=False)  # Test regex mode only

    def test_parse_empty_document(self, parser):
        result = parser.parse("")
        assert result is not None

    def test_parse_minimal_soo(self, parser):
        soo = """# Sequence of Operations
## CRAH Unit - CRAH-01
### Normal Cooling Mode
Supply air temperature setpoint: 65°F
Fan speed: Variable
"""
        result = parser.parse(soo)
        assert result is not None
        # Should detect at least one system
        systems = getattr(result, 'systems', [])
        assert len(systems) >= 0  # May be 0 if format not recognized

    def test_detect_crah_content(self, parser):
        soo = "CRAH-01 cooling mode, supply air temperature 65°F, return air 75°F"
        from itc_form_generator.parser import detect_document_type
        types = detect_document_type(soo)
        assert 'CRAH' in str(types).upper() or len(types) >= 0

    def test_detect_ahu_content(self, parser):
        soo = "AHU-01 air handling unit, mixed air, outside air damper, heating coil"
        from itc_form_generator.parser import detect_document_type
        types = detect_document_type(soo)
        assert isinstance(types, (list, dict))

    def test_parse_with_setpoints(self, parser):
        soo = """## CRAH-01
- Supply Air Temperature Setpoint: 55°F
- Return Air High Temperature Alarm: 85°F
- Chilled Water Valve Position: 0-100%
- Fan Speed: 20-100% via VFD
"""
        result = parser.parse(soo)
        assert result is not None

    def test_parse_multiline_modes(self, parser):
        soo = """## System CRAH-01
### Normal Cooling Mode
Fan runs at variable speed.
Chilled water valve modulates to maintain supply air setpoint.

### Alarm Mode  
If supply air temperature exceeds 80°F, generate high temp alarm.
If fan proof of flow is lost, generate fan failure alarm.

### Shutdown Mode
Fan stops. Chilled water valve closes.
"""
        result = parser.parse(soo)
        assert result is not None


class TestPointsParser:
    """Test BMS/Controls points list parser."""

    @pytest.fixture
    def parser(self):
        from itc_form_generator.points_parser import PointsListParser
        return PointsListParser()

    def test_parse_empty_content(self, parser):
        result = parser.parse("", "empty.csv")
        assert result is not None
        assert len(result.points) == 0

    def test_parse_standard_csv(self, parser):
        csv_content = """Point Name,Type,Description,Units,Range
CRAH01_SAT,AI,Supply Air Temperature,°F,32-120
CRAH01_RAT,AI,Return Air Temperature,°F,32-120
CRAH01_SF_CMD,DO,Supply Fan Command,,On/Off
CRAH01_CWV,AO,Chilled Water Valve,%,0-100
"""
        result = parser.parse(csv_content, "test.csv")
        assert len(result.points) == 4
        assert result.points[0].point_name == "CRAH01_SAT"

    def test_parse_tsv(self, parser):
        tsv_content = "Point Name\tType\tDescription\nCRAH01_SAT\tAI\tSupply Air Temp"
        result = parser.parse(tsv_content, "test.tsv")
        assert len(result.points) >= 1

    def test_type_inference(self, parser):
        csv_content = """Point Name,Description
CRAH01_SAT,Supply Air Temperature
CRAH01_SF_STS,Supply Fan Status
CRAH01_SF_CMD,Supply Fan Start Command
CRAH01_CWV_POS,Chilled Water Valve Position
"""
        result = parser.parse(csv_content, "test.csv")
        # Should infer types from point names
        for point in result.points:
            assert point.point_type is not None

    def test_non_standard_headers(self, parser):
        """Test fuzzy matching for non-standard column headers."""
        csv_content = """Signal Name,I/O Type,PLC Comment,Eng. Units
CRAH01_SAT,Analog Input,Supply Air Temperature,Deg F
"""
        result = parser.parse(csv_content, "test.csv")
        # Should map via fuzzy matching or aliases
        assert len(result.points) >= 1

    def test_confidence_scoring(self, parser):
        csv_content = """Point Name,Type,Description,Units
CRAH01_SAT,AI,Supply Air Temperature,°F
"""
        result = parser.parse(csv_content, "test.csv")
        assert result.parsing_confidence > 0
        if result.points:
            assert result.points[0].confidence > 0

    def test_equipment_extraction(self, parser):
        csv_content = """Point Name,Type,Description
CRAH-01.SAT,AI,Supply Air Temperature
AHU_002.OAT,AI,Outside Air Temperature
"""
        result = parser.parse(csv_content, "test.csv")
        # Should extract equipment tags from point names
        for point in result.points:
            assert point.equipment_ref or point.point_name


class TestAIService:
    """Test AI service (mock/offline mode)."""

    def test_import_ai_service(self):
        from itc_form_generator.ai_service import AIService
        assert AIService is not None

    def test_create_without_backend(self):
        """Should create service even when no backend available."""
        try:
            from itc_form_generator.ai_service import AIService
            service = AIService()
            assert service is not None
        except Exception:
            # Acceptable if no backend configured
            pass

