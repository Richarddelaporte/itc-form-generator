"""
Integration tests for ACC (Autodesk Construction Cloud) Excel export.

Verifies the full export pipeline produces a valid ACC checklist template
matching the reference file (213113_L2_JockeyPump_SetInPlace.xlsx).

Run with:  pytest itc_form_generator/test_acc_export.py -v
"""

import io
import pytest
from openpyxl import load_workbook

from itc_form_generator.models import (
    InspectionForm, FormSection, CheckItem,
    FormType, CheckItemType, Priority,
)
from itc_form_generator.exporter import (
    FormExporter, ACC_HEADERS, escape_excel_formula,
)


# ── Fixtures ────────────────────────────────────────────────────────

DATA_START_ROW = 6  # Rows 1-5 are header block, data starts at 6


@pytest.fixture
def exporter():
    return FormExporter()


@pytest.fixture
def pfi_form():
    """A Pre-Functional Inspection form with two sections and mixed check types."""
    return InspectionForm(
        form_type=FormType.PFI,
        title="Jockey Pump Pre-Functional Inspection",
        system="Jockey Pump",
        system_tag="JockeyPump",
        project="213113",
        sections=[
            FormSection(
                title="Documentation Verification",
                description="Verify documentation is complete.",
                check_items=[
                    CheckItem(
                        id="DV-001",
                        description="Confirm submittal data is present in BIM",
                        check_type=CheckItemType.VISUAL,
                        priority=Priority.CRITICAL,
                        acceptance_criteria="Pump bolted per manufacturer specs",
                    ),
                    CheckItem(
                        id="DV-002",
                        description="Record suction pressure gauge reading",
                        check_type=CheckItemType.MEASUREMENT,
                        priority=Priority.HIGH,
                    ),
                ],
            ),
            FormSection(
                title="Pump Installation",
                check_items=[
                    CheckItem(
                        id="PI-001",
                        description="Verify motor rotation direction",
                        check_type=CheckItemType.FUNCTIONAL,
                        priority=Priority.CRITICAL,
                    ),
                    CheckItem(
                        id="PI-002",
                        description="Confirm nameplate data matches submittals",
                        check_type=CheckItemType.DOCUMENTATION,
                        priority=Priority.MEDIUM,
                    ),
                    CheckItem(
                        id="PI-003",
                        description="Verify ground fault protection is installed",
                        check_type=CheckItemType.VERIFICATION,
                        priority=Priority.LOW,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def fpt_form():
    """A Functional Performance Test form."""
    return InspectionForm(
        form_type=FormType.FPT,
        title="CRAH Functional Performance Test",
        system="CRAH Unit",
        system_tag="CRAH-01",
        project="",
        sections=[
            FormSection(
                title="Cooling Mode Test",
                check_items=[
                    CheckItem(
                        id="CM-001",
                        description="Verify supply air temperature control",
                        check_type=CheckItemType.FUNCTIONAL,
                        priority=Priority.HIGH,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def pfi_workbook(exporter, pfi_form):
    """Export pfi_form and return a loaded openpyxl Workbook."""
    excel_bytes = exporter.export_to_acc_excel([pfi_form], project_number="213113")
    assert excel_bytes is not None
    return load_workbook(io.BytesIO(excel_bytes))


@pytest.fixture
def multi_workbook(exporter, pfi_form, fpt_form):
    """Export two forms and return a loaded openpyxl Workbook."""
    excel_bytes = exporter.export_to_acc_excel(
        [pfi_form, fpt_form], project_number="213113"
    )
    assert excel_bytes is not None
    return load_workbook(io.BytesIO(excel_bytes))


# ── Helpers ─────────────────────────────────────────────────────────


def _row_values(ws, row_num, max_col=22):
    return [ws.cell(row=row_num, column=c).value for c in range(1, max_col + 1)]


def _col_values(ws, col_num, start_row=DATA_START_ROW):
    vals = []
    for r in range(start_row, ws.max_row + 1):
        v = ws.cell(row=r, column=col_num).value
        if v is not None:
            vals.append(v)
    return vals


# ═══════════════════════════════════════════════════════════════════
#  Tests
# ═══════════════════════════════════════════════════════════════════


class TestWorkbookStructure:
    def test_single_form_produces_three_sheets(self, pfi_workbook):
        names = pfi_workbook.sheetnames
        assert "FULL" in names
        assert "Lookups" in names
        assert len(names) == 3

    def test_multi_form_produces_correct_sheets(self, multi_workbook):
        names = multi_workbook.sheetnames
        assert "FULL" in names
        assert "Lookups" in names
        assert len(names) == 4

    def test_full_sheet_is_first(self, pfi_workbook):
        assert pfi_workbook.sheetnames[0] == "FULL"

    def test_lookups_sheet_is_last(self, pfi_workbook):
        assert pfi_workbook.sheetnames[-1] == "Lookups"


class TestHeaderBlock:
    """Verify the 5-row header block matches the ACC reference template."""

    def test_row1_has_22_acc_headers(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        headers = _row_values(ws, 1)
        assert headers == ACC_HEADERS

    def test_row2_has_required_optional_labels(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        row2 = _row_values(ws, 2)
        assert row2[1] == "Required"   # B: Template Name
        assert row2[2] == "Required"   # C: Template Type
        assert row2[3] == "Required"   # D: Item Text

    def test_row3_has_descriptions(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert "Name of the template" in str(ws.cell(row=3, column=2).value)
        assert "Type of the template" in str(ws.cell(row=3, column=3).value)

    def test_row4_has_paste_instructions(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert "Must be filled in" in str(ws.cell(row=4, column=2).value)

    def test_row5_is_reminder(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        reminder_text = str(ws.cell(row=5, column=9).value)
        assert "REMINDER" in reminder_text
        assert "Don't delete" in reminder_text

    def test_row5_has_red_fill(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        fill = ws.cell(row=5, column=9).fill
        assert fill.start_color.rgb in ("00FF0000", "FFFF0000")

    def test_freeze_panes_at_row6(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert ws.freeze_panes == "A6"


class TestGeneralSection:
    """Verify the GENERAL section appears at the top of each form's data."""

    def test_general_section_present(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert ws.cell(row=DATA_START_ROW, column=4).value == "GENERAL"
        assert ws.cell(row=DATA_START_ROW, column=6).value == "Section"

    def test_date_field(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert ws.cell(row=DATA_START_ROW + 1, column=4).value == "Date"
        assert ws.cell(row=DATA_START_ROW + 1, column=6).value == "Date"

    def test_qaqc_authority_field(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        assert ws.cell(row=DATA_START_ROW + 2, column=4).value == "QA/QC Authority Name"
        assert ws.cell(row=DATA_START_ROW + 2, column=6).value == "Text"

    def test_attendees_field(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        text = ws.cell(row=DATA_START_ROW + 3, column=4).value
        assert "Inspection Attendees" in text
        assert ws.cell(row=DATA_START_ROW + 3, column=6).value == "Text"

    def test_general_template_name_populated(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, DATA_START_ROW + 4):
            assert ws.cell(row=r, column=2).value is not None
            assert "213113" in ws.cell(row=r, column=2).value


class TestResponseTypeMapping:
    """Verify check-type → response-type mapping uses comma format."""

    def test_visual_maps_to_yes_no_na(self, exporter):
        assert exporter._get_response_type(CheckItemType.VISUAL) == "Yes, No NA"

    def test_measurement_maps_to_text(self, exporter):
        assert exporter._get_response_type(CheckItemType.MEASUREMENT) == "Text"

    def test_functional_maps_to_pass_fail_na(self, exporter):
        assert exporter._get_response_type(CheckItemType.FUNCTIONAL) == "Pass, Fail, N/A"

    def test_documentation_maps_to_text(self, exporter):
        assert exporter._get_response_type(CheckItemType.DOCUMENTATION) == "Text"

    def test_verification_maps_to_yes_no_na(self, exporter):
        assert exporter._get_response_type(CheckItemType.VERIFICATION) == "Yes, No NA"


class TestNonConformingAnswers:
    def test_yes_no_na_non_conforming_is_no(self, exporter):
        assert exporter._get_non_conforming("Yes, No NA") == "No"

    def test_pass_fail_na_non_conforming_is_fail(self, exporter):
        assert exporter._get_non_conforming("Pass, Fail, N/A") == "Fail"

    def test_text_has_no_non_conforming(self, exporter):
        assert exporter._get_non_conforming("Text") == ""

    def test_non_conforming_column_in_workbook(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            resp = ws.cell(row=r, column=6).value
            nc = ws.cell(row=r, column=9).value
            if resp == "Yes, No NA":
                assert nc == "No", f"Row {r}: Yes, No NA should have NC='No'"
            elif resp == "Pass, Fail, N/A":
                assert nc == "Fail", f"Row {r}: Pass, Fail, N/A should have NC='Fail'"
            elif resp in ("Text", "Section", "Date"):
                assert nc is None, f"Row {r}: {resp} should have no NC value"


class TestResponseRequired:
    """In ACC reference, Response Required = TRUE for all check items."""

    def test_all_items_required_true(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            resp = ws.cell(row=r, column=6).value
            req = ws.cell(row=r, column=7).value
            if resp and resp not in ("Section", "Date", "Text"):
                assert req == "TRUE", f"Row {r}: item should have Required=TRUE"


class TestIssueAutoCreate:
    """Issue Auto Create = TRUE for all check items in reference."""

    def test_auto_create_true_for_all_items(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            resp = ws.cell(row=r, column=6).value
            auto = ws.cell(row=r, column=19).value
            if resp and resp not in ("Section", "Date", "Text"):
                assert auto == "TRUE", f"Row {r}: should have AutoCreate=TRUE"


class TestTemplateNaming:
    def test_pfi_template_name(self, exporter, pfi_form):
        name = exporter._get_template_name(pfi_form, project_number="213113")
        assert name == "213113_L2_JockeyPump_SetInPlace"

    def test_fpt_template_name(self, exporter, fpt_form):
        name = exporter._get_template_name(fpt_form, project_number="999999")
        assert name == "999999_L3_CRAH-01_FunctionalTest"

    def test_fallback_to_default_project(self, exporter):
        form = InspectionForm(
            form_type=FormType.IST, title="T", system="Sys",
            system_tag="TAG", project="", sections=[],
        )
        name = exporter._get_template_name(form, project_number="")
        assert name.startswith("000000_")

    def test_template_name_on_every_data_row(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            val = ws.cell(row=r, column=2).value
            assert val is not None, f"Row {r}: Template Name must not be empty"
            assert "_L2_" in val


class TestTemplateType:
    def test_pfi_is_quality(self, exporter):
        form = InspectionForm(form_type=FormType.PFI, title="T", system="S", sections=[])
        assert exporter._get_template_type(form) == "Quality"

    def test_fpt_is_commissioning(self, exporter):
        form = InspectionForm(form_type=FormType.FPT, title="T", system="S", sections=[])
        assert exporter._get_template_type(form) == "Commissioning"

    def test_template_type_on_every_data_row(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        valid_types = {"Quality", "Safety", "Punch List", "Commissioning"}
        for r in range(DATA_START_ROW, ws.max_row + 1):
            val = ws.cell(row=r, column=3).value
            assert val in valid_types, f"Row {r}: unexpected template type '{val}'"


class TestIssueTypeSubtype:
    """Issue Type and Issue Subtype should both match template_type."""

    def test_issue_type_matches_template_type(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            resp = ws.cell(row=r, column=6).value
            if resp and resp not in ("Section", "Date", "Text"):
                assert ws.cell(row=r, column=12).value == "Quality"

    def test_issue_subtype_matches_template_type(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(DATA_START_ROW, ws.max_row + 1):
            resp = ws.cell(row=r, column=6).value
            if resp and resp not in ("Section", "Date", "Text"):
                assert ws.cell(row=r, column=13).value == "Quality"


class TestSectionRows:
    def test_section_rows_have_response_type_section(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        section_rows = [
            r for r in range(DATA_START_ROW, ws.max_row + 1)
            if ws.cell(row=r, column=6).value == "Section"
        ]
        # GENERAL + Documentation Verification + Pump Installation = 3
        assert len(section_rows) == 3

    def test_section_title_in_item_text(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        section_titles = []
        for r in range(DATA_START_ROW, ws.max_row + 1):
            if ws.cell(row=r, column=6).value == "Section":
                section_titles.append(ws.cell(row=r, column=4).value)
        assert "GENERAL" in section_titles
        assert "Documentation Verification" in section_titles
        assert "Pump Installation" in section_titles


class TestLookupsSheet:
    def test_lookups_version(self, pfi_workbook):
        ws = pfi_workbook["Lookups"]
        assert ws.cell(row=1, column=1).value == "Version"
        assert ws.cell(row=1, column=2).value == 1

    def test_lookups_template_types(self, pfi_workbook):
        ws = pfi_workbook["Lookups"]
        assert ws.cell(row=3, column=1).value == "Template Types"
        types = [ws.cell(row=r, column=1).value for r in range(4, 8)]
        assert types == ["Quality", "Safety", "Punch List", "Commissioning"]

    def test_lookups_response_types(self, pfi_workbook):
        ws = pfi_workbook["Lookups"]
        assert ws.cell(row=9, column=1).value == "Response Types"
        rtypes = [ws.cell(row=r, column=1).value for r in range(10, 17)]
        assert rtypes == [
            "Section", "Yes, No, N/A", "Plus, Minus, N/A",
            "True, False, N/A", "Pass, Fail, N/A", "Text", "Date",
        ]


class TestMultiFormExport:
    def test_full_sheet_has_both_template_names(self, multi_workbook):
        ws = multi_workbook["FULL"]
        template_names = set(_col_values(ws, 2, start_row=DATA_START_ROW))
        assert len(template_names) == 2
        assert any("SetInPlace" in n for n in template_names)
        assert any("FunctionalTest" in n for n in template_names)

    def test_per_form_sheets_have_data(self, multi_workbook):
        sheets = [s for s in multi_workbook.sheetnames if s not in ("FULL", "Lookups")]
        assert len(sheets) == 2
        for sheet_name in sheets:
            ws = multi_workbook[sheet_name]
            rows = [r for r in range(DATA_START_ROW, ws.max_row + 1) if ws.cell(row=r, column=2).value]
            assert len(rows) > 0


class TestBackwardCompatibility:
    def test_export_to_procore_excel_alias(self, exporter, pfi_form):
        result = exporter.export_to_procore_excel([pfi_form], project_number="123")
        assert result is not None and isinstance(result, bytes)

    def test_export_to_excel_wrapper(self, exporter, pfi_form):
        result = exporter.export_to_excel([pfi_form], project_number="123")
        assert result is not None and isinstance(result, bytes)

    def test_all_three_methods_produce_identical_output(self, exporter, pfi_form):
        a = exporter.export_to_acc_excel([pfi_form], project_number="X")
        b = exporter.export_to_procore_excel([pfi_form], project_number="X")
        c = exporter.export_to_excel([pfi_form], project_number="X")
        assert a == b == c


class TestEdgeCases:
    def test_empty_forms_list(self, exporter):
        result = exporter.export_to_acc_excel([], project_number="123")
        assert result is not None
        wb = load_workbook(io.BytesIO(result))
        assert "FULL" in wb.sheetnames
        assert "Lookups" in wb.sheetnames

    def test_form_with_no_sections(self, exporter):
        form = InspectionForm(
            form_type=FormType.CXC, title="Empty", system="Sys",
            system_tag="SYS-01", sections=[],
        )
        result = exporter.export_to_acc_excel([form], project_number="456")
        assert result is not None

    def test_formula_injection_escaped(self, exporter):
        form = InspectionForm(
            form_type=FormType.PFI, title="T", system="S", system_tag="S-01",
            sections=[FormSection(title="Safe Section", check_items=[
                CheckItem(id="1", description="+cmd('calc')", check_type=CheckItemType.VISUAL),
            ])],
        )
        result = exporter.export_to_acc_excel([form])
        wb = load_workbook(io.BytesIO(result))
        ws = wb["FULL"]
        # Find the item row (after GENERAL section + section header)
        for r in range(DATA_START_ROW, ws.max_row + 1):
            val = ws.cell(row=r, column=4).value
            if val and "+cmd" in val:
                assert val.startswith("'"), "Formula should be escaped"
                break

    def test_escape_excel_formula_function(self):
        assert escape_excel_formula("=SUM(A1)") == "'=SUM(A1)"
        assert escape_excel_formula("-1+1") == "'-1+1"
        assert escape_excel_formula("Normal text") == "Normal text"
        assert escape_excel_formula("") == ""

    def test_all_form_types_produce_valid_output(self, exporter):
        for ft in FormType:
            form = InspectionForm(
                form_type=ft, title=f"{ft.name} Test", system="TestSys",
                system_tag="TS-01",
                sections=[FormSection(title="Section", check_items=[
                    CheckItem(id="1", description="Item", check_type=CheckItemType.VISUAL),
                ])],
            )
            result = exporter.export_to_acc_excel([form])
            assert result is not None, f"FormType {ft.name} should export"


class TestColumnCount:
    def test_headers_list_has_22_entries(self):
        assert len(ACC_HEADERS) == 22

    def test_row1_has_22_columns(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        row1 = _row_values(ws, 1, max_col=22)
        assert len(row1) == 22
        assert row1[0] == "###"
        assert row1[21] == "required by"

    def test_no_data_beyond_column_v(self, pfi_workbook):
        ws = pfi_workbook["FULL"]
        for r in range(1, ws.max_row + 1):
            assert ws.cell(row=r, column=23).value is None, f"Row {r} has data beyond column V"
