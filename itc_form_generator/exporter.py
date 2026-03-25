"""Export ITC forms to CSV and Excel formats.

Supports ACC (Autodesk Construction Cloud) checklist import format
for BIM360/ACC field inspection workflows.
"""

import csv
import io
from typing import Optional

from .models import InspectionForm, FormSection, CheckItem, FormType, CheckItemType, Priority


def escape_excel_formula(value: str) -> str:
    """Escape strings that Excel might interpret as formulas.

    Excel treats strings starting with =, -, +, @ as formulas.
    Prefix with a single quote to force text interpretation.
    """
    if not value:
        return value
    if isinstance(value, str) and value and value[0] in ('=', '-', '+', '@'):
        return "'" + value
    return value


# ACC column headers (A–V, 22 columns)
ACC_HEADERS = [
    '###',                  # A
    'Template Name',        # B
    'Template Type',        # C
    'Item Text',            # D
    'Item Description',     # E
    'Response Type',        # F
    'Response Required',    # G
    'List Answers',         # H
    'Non Conforming Answers',  # I
    'Issue Title',          # J
    'Issue Description',    # K
    'Issue Type',           # L
    'Issue Subtype',        # M
    'Issue Assignee',       # N
    'Issue Assignee Type',  # O
    'Issue Owner',          # P
    'Issue Root Cause Category',  # Q
    'Issue Root Cause',     # R
    'Issue Auto Create',    # S
    'index',                # T
    'number',               # U
    'required by',          # V
]

ACC_INSTRUCTIONS = [
    '###',
    'Required\n\nUnique template name',
    'Required\n\nQuality, Safety, Punch List, or Commissioning',
    'Required\n\nText for the checklist item',
    'Optional\n\nDetailed description / acceptance criteria',
    'Required\n\nResponse type for this item',
    'Optional\n\nTRUE or FALSE',
    'Optional\n\nCustom list answers',
    'Optional\n\nAnswers triggering non-conformance',
    'Optional\n\nAuto-created issue title',
    'Optional\n\nAuto-created issue description',
    'Optional\n\nIssue type category',
    'Optional\n\nIssue subtype',
    'Optional\n\nDefault issue assignee',
    'Optional\n\nAssignee type (user/company)',
    'Optional\n\nIssue owner',
    'Optional\n\nRoot cause category',
    'Optional\n\nRoot cause detail',
    'Optional\n\nTRUE to auto-create issues',
    'Optional\n\nRow index',
    'Optional\n\nItem number',
    'Optional\n\nRequired-by date',
]

ACC_COLUMN_WIDTHS = [
    6, 50, 18, 80, 50, 20, 16, 20, 22,
    30, 30, 14, 14, 20, 18, 20, 22, 18,
    16, 8, 8, 14,
]

# FormType → ACC Level code
FORM_TYPE_LEVEL = {
    FormType.PFI: 'L2',
    FormType.FPT: 'L3',
    FormType.IST: 'L4',
    FormType.CXC: 'L2',
    FormType.ITC: 'L3',
}

# FormType → ACC activity label
FORM_TYPE_ACTIVITY = {
    FormType.PFI: 'SetInPlace',
    FormType.FPT: 'FunctionalTest',
    FormType.IST: 'Integration',
    FormType.CXC: 'Commissioning',
    FormType.ITC: 'ITC',
}

# FormType → ACC Template Type
FORM_TYPE_TEMPLATE_TYPE = {
    FormType.PFI: 'Quality',
    FormType.FPT: 'Commissioning',
    FormType.IST: 'Commissioning',
    FormType.CXC: 'Commissioning',
    FormType.ITC: 'Commissioning',
}


class FormExporter:
    """Export inspection forms to various formats."""

    # ── CSV (unchanged) ──────────────────────────────────────────────

    def export_to_csv(self, form: InspectionForm) -> str:
        """Export a single form to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Form Type', 'System', 'System Tag', 'Section', 'Item ID',
            'Description', 'Check Type', 'Priority', 'Acceptance Criteria',
            'Expected Value', 'Actual Value', 'Pass/Fail', 'Comments',
        ])

        for section in form.sections:
            for item in section.check_items:
                writer.writerow([
                    form.form_type.value, form.system, form.system_tag,
                    section.title, item.id, item.description,
                    item.check_type.value, item.priority.value,
                    item.acceptance_criteria, item.expected_value,
                    item.actual_value, item.pass_fail, item.comments,
                ])

        return output.getvalue()

    def export_all_to_csv(self, forms: list[InspectionForm]) -> str:
        """Export all forms to a single CSV file."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Form Type', 'System', 'System Tag', 'Section', 'Item ID',
            'Description', 'Check Type', 'Priority', 'Acceptance Criteria',
            'Expected Value', 'Actual Value', 'Pass/Fail', 'Comments',
        ])

        for form in forms:
            for section in form.sections:
                for item in section.check_items:
                    writer.writerow([
                        form.form_type.value, form.system, form.system_tag,
                        section.title, item.id, item.description,
                        item.check_type.value, item.priority.value,
                        item.acceptance_criteria, item.expected_value,
                        item.actual_value, item.pass_fail, item.comments,
                    ])

        return output.getvalue()

    # ── ACC helpers ──────────────────────────────────────────────────

    def _get_response_type(self, check_type: CheckItemType) -> str:
        """Map CheckItemType to ACC-valid response type.

        Values must match the Lookups sheet exactly (slash-delimited).
        """
        mapping = {
            CheckItemType.VISUAL: "Yes/No/N/A",
            CheckItemType.MEASUREMENT: "Text",
            CheckItemType.FUNCTIONAL: "Pass/Fail/N/A",
            CheckItemType.DOCUMENTATION: "Text",
            CheckItemType.VERIFICATION: "Yes/No/N/A",
        }
        return mapping.get(check_type, "Yes/No/N/A")

    def _get_non_conforming(self, response_type: str) -> str:
        """Return the non-conforming answer string for a given response type."""
        if response_type == "Yes/No/N/A":
            return "No"
        if response_type == "Pass/Fail/N/A":
            return "Fail"
        return ""

    def _get_template_name(
        self,
        form: InspectionForm,
        project_number: str = "",
    ) -> str:
        """Build an ACC-convention template name.

        Format: {spec}_{level}_{equipment}_{activity}
        """
        spec = project_number or form.project or "000000"
        level = FORM_TYPE_LEVEL.get(form.form_type, "L2")
        equipment = (
            form.system_tag
            or form.system.replace(" ", "")[:20]
            or "Equipment"
        )
        activity = FORM_TYPE_ACTIVITY.get(form.form_type, "Inspection")
        return f"{spec}_{level}_{equipment}_{activity}"

    def _get_template_type(self, form: InspectionForm) -> str:
        """Map FormType to ACC Template Type."""
        return FORM_TYPE_TEMPLATE_TYPE.get(form.form_type, "Commissioning")

    # ── ACC Excel export ─────────────────────────────────────────────

    def export_to_acc_excel(
        self,
        forms: list[InspectionForm],
        project_number: str = "",
    ) -> Optional[bytes]:
        """Export forms to ACC (Autodesk Construction Cloud) Excel format.

        Creates a workbook matching the ACC checklist import template with:
        - 22-column structure (A–V)
        - Row 1: Column headers
        - Row 2: Column descriptions/instructions
        - Row 3: Reminder row
        - Row 4+: Data rows (sections + check items)
        - Lookups sheet with valid enumeration values

        Args:
            forms: List of inspection forms to export.
            project_number: Project number for template naming.

        Returns:
            Excel file content as bytes, or None if openpyxl not available.
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            return None

        wb = Workbook()
        wb.remove(wb.active)

        # Styles
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        instruction_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        section_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'),
        )
        wrap_alignment = Alignment(wrap_text=True, vertical='top')
        num_cols = len(ACC_HEADERS)

        def _write_header_rows(ws):
            """Write the standard 3-row header block to a worksheet."""
            # Row 1: Column headers
            for col, hdr in enumerate(ACC_HEADERS, 1):
                cell = ws.cell(row=1, column=col, value=hdr)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = wrap_alignment

            # Row 2: Descriptions / instructions
            for col, instr in enumerate(ACC_INSTRUCTIONS, 1):
                cell = ws.cell(row=2, column=col, value=instr)
                cell.fill = instruction_fill
                cell.alignment = wrap_alignment
                cell.border = thin_border

            # Row 3: Reminder
            ws.cell(row=3, column=1, value='###')
            ws.cell(row=3, column=2, value="REMINDER: Don't delete or rename columns")

        def _write_section_row(ws, row, template_name, template_type, section_title, section_description=""):
            """Write a section header row (Response Type = Section)."""
            ws.cell(row=row, column=2, value=template_name)       # B: Template Name
            ws.cell(row=row, column=3, value=template_type)       # C: Template Type
            ws.cell(row=row, column=4, value=escape_excel_formula(section_title))  # D: Item Text
            if section_description:
                ws.cell(row=row, column=5, value=escape_excel_formula(section_description))  # E: Item Description
            ws.cell(row=row, column=6, value='Section')           # F: Response Type
            for c in range(1, num_cols + 1):
                ws.cell(row=row, column=c).fill = section_fill
                ws.cell(row=row, column=c).border = thin_border

        def _write_item_row(ws, row, template_name, template_type, item: CheckItem, idx: int):
            """Write a single check-item data row."""
            response_type = self._get_response_type(item.check_type)
            non_conforming = self._get_non_conforming(response_type)
            is_required = item.priority in (Priority.CRITICAL, Priority.HIGH)

            # Build item description from acceptance criteria + method + priority
            desc_parts = []
            if item.acceptance_criteria:
                desc_parts.append(item.acceptance_criteria)
            if item.method:
                desc_parts.append(f"Method: {item.method}")
            if item.expected_value:
                desc_parts.append(f"Expected: {item.expected_value}")
            if item.priority.value != "Medium":
                desc_parts.append(f"Priority: {item.priority.value}")
            item_description = " | ".join(desc_parts)

            ws.cell(row=row, column=2, value=template_name)          # B: Template Name
            ws.cell(row=row, column=3, value=template_type)          # C: Template Type
            ws.cell(row=row, column=4, value=escape_excel_formula(item.description))  # D: Item Text
            ws.cell(row=row, column=5, value=escape_excel_formula(item_description))  # E: Item Description
            ws.cell(row=row, column=6, value=response_type)          # F: Response Type
            ws.cell(row=row, column=7, value='TRUE' if is_required else 'FALSE')  # G: Response Required
            if non_conforming:
                ws.cell(row=row, column=9, value=non_conforming)     # I: Non Conforming Answers
            ws.cell(row=row, column=12, value=template_type)         # L: Issue Type
            ws.cell(row=row, column=13, value='Inspection')          # M: Issue Subtype
            if non_conforming:
                ws.cell(row=row, column=19, value='TRUE')            # S: Issue Auto Create
            ws.cell(row=row, column=20, value=idx)                   # T: index

            for c in range(1, num_cols + 1):
                ws.cell(row=row, column=c).border = thin_border
                ws.cell(row=row, column=c).alignment = wrap_alignment

        def _apply_column_widths(ws):
            for col, w in enumerate(ACC_COLUMN_WIDTHS, 1):
                ws.column_dimensions[get_column_letter(col)].width = w

        # ── Per-form worksheets ──────────────────────────────────────
        for form in forms:
            sheet_name = f"{form.form_type.name}_{form.system_tag}"[:31]
            ws = wb.create_sheet(title=sheet_name)

            template_name = self._get_template_name(form, project_number)
            template_type = self._get_template_type(form)

            _write_header_rows(ws)

            row = 4
            idx = 1
            for section in form.sections:
                _write_section_row(ws, row, template_name, template_type, section.title, section.description)
                row += 1
                idx += 1

                for item in section.check_items:
                    _write_item_row(ws, row, template_name, template_type, item, idx)
                    row += 1
                    idx += 1

            _apply_column_widths(ws)
            ws.freeze_panes = 'A4'

        # ── Combined FULL sheet ──────────────────────────────────────
        ws_full = wb.create_sheet(title="FULL", index=0)
        _write_header_rows(ws_full)

        row = 4
        idx = 1
        for form in forms:
            template_name = self._get_template_name(form, project_number)
            template_type = self._get_template_type(form)

            for section in form.sections:
                _write_section_row(ws_full, row, template_name, template_type, section.title, section.description)
                row += 1
                idx += 1

                for item in section.check_items:
                    _write_item_row(ws_full, row, template_name, template_type, item, idx)
                    row += 1
                    idx += 1

        _apply_column_widths(ws_full)
        ws_full.freeze_panes = 'A4'

        # ── Lookups sheet ────────────────────────────────────────────
        ws_lookup = wb.create_sheet(title="Lookups")
        ws_lookup.cell(row=1, column=1, value="Version")
        ws_lookup.cell(row=1, column=2, value=1)

        ws_lookup.cell(row=3, column=1, value="Template Types")
        for i, tt in enumerate(["Quality", "Safety", "Punch List", "Commissioning"], start=4):
            ws_lookup.cell(row=i, column=1, value=tt)

        ws_lookup.cell(row=9, column=1, value="Response Types")
        response_types = [
            "Section",
            "Yes/No/N/A",
            "Plus/Minus/N/A",
            "True/False/N/A",
            "Pass/Fail/N/A",
            "Text",
            "Date",
        ]
        for i, rt in enumerate(response_types, start=10):
            ws_lookup.cell(row=i, column=1, value=rt)

        ws_lookup.column_dimensions['A'].width = 22
        ws_lookup.column_dimensions['B'].width = 10

        # ── Save ─────────────────────────────────────────────────────
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    # ── Public convenience wrappers ──────────────────────────────────

    def export_to_excel(
        self,
        forms: list[InspectionForm],
        project_number: str = "",
    ) -> Optional[bytes]:
        """Export forms to Excel (ACC format).

        Drop-in replacement for the previous Procore method.

        Args:
            forms: List of inspection forms to export.
            project_number: Project number for ACC template naming.

        Returns:
            Excel file content as bytes, or None if openpyxl not available.
        """
        return self.export_to_acc_excel(forms, project_number=project_number)

    # Backward-compat alias
    export_to_procore_excel = export_to_acc_excel

    # ── Summary CSV (unchanged) ──────────────────────────────────────

    def export_summary_csv(self, forms: list[InspectionForm]) -> str:
        """Export a summary of all forms to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Form Type', 'System', 'System Tag', 'Total Items',
            'Critical Items', 'High Priority Items',
            'Medium Priority Items', 'Low Priority Items',
        ])

        for form in forms:
            critical = sum(1 for s in form.sections for i in s.check_items if i.priority.name == 'CRITICAL')
            high = sum(1 for s in form.sections for i in s.check_items if i.priority.name == 'HIGH')
            medium = sum(1 for s in form.sections for i in s.check_items if i.priority.name == 'MEDIUM')
            low = sum(1 for s in form.sections for i in s.check_items if i.priority.name == 'LOW')

            writer.writerow([
                form.form_type.value, form.system, form.system_tag,
                form.total_items, critical, high, medium, low,
            ])

        return output.getvalue()


def check_excel_support() -> bool:
    """Check if Excel export is available."""
    try:
        import openpyxl
        return True
    except ImportError:
        return False
