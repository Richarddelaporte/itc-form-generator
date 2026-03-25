"""HTML renderer for ITC forms."""

from typing import Optional
from .models import InspectionForm, FormType, Priority


class HTMLRenderer:
    """Renders inspection forms to HTML."""

    CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.4; color: #333; }
    .form-container { max-width: 1000px; margin: 0 auto; padding: 20px; }

    .form-header {
        border: 2px solid #333;
        padding: 15px;
        margin-bottom: 20px;
        background: #f5f5f5;
    }
    .form-header h1 { font-size: 18pt; margin-bottom: 10px; }
    .form-header .meta { display: flex; flex-wrap: wrap; gap: 20px; }
    .form-header .meta-item { flex: 1; min-width: 200px; }
    .form-header .meta-item label { font-weight: bold; display: block; }

    .signature-block {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #999;
    }
    .signature-block .sig-item label { font-weight: bold; display: block; font-size: 9pt; }
    .signature-block .sig-line {
        border-bottom: 1px solid #333;
        height: 25px;
        margin-top: 5px;
    }

    .section { margin-bottom: 25px; page-break-inside: avoid; }
    .section h2 {
        font-size: 14pt;
        background: #333;
        color: white;
        padding: 8px 12px;
        margin-bottom: 0;
    }
    .section-desc {
        font-style: italic;
        padding: 8px 12px;
        background: #eee;
        border: 1px solid #333;
        border-top: none;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 10pt;
    }
    th, td {
        border: 1px solid #333;
        padding: 6px 8px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background: #e0e0e0;
        font-weight: bold;
        white-space: nowrap;
    }

    .col-id { width: 70px; }
    .col-desc { width: auto; }
    .col-criteria { width: 150px; }
    .col-expected { width: 100px; }
    .col-actual { width: 100px; }
    .col-pf { width: 60px; text-align: center; }
    .col-comments { width: 150px; }

    .priority-critical { border-left: 4px solid #c00; }
    .priority-high { border-left: 4px solid #f80; }
    .priority-medium { border-left: 4px solid #fc0; }
    .priority-low { border-left: 4px solid #0a0; }

    .type-badge {
        display: inline-block;
        font-size: 8pt;
        padding: 2px 6px;
        border-radius: 3px;
        background: #666;
        color: white;
        margin-left: 5px;
    }

    .form-footer {
        margin-top: 30px;
        padding-top: 20px;
        border-top: 2px solid #333;
    }
    .form-footer h3 { margin-bottom: 10px; }
    .notes-area {
        border: 1px solid #333;
        min-height: 100px;
        padding: 10px;
    }

    .summary-stats {
        display: flex;
        gap: 20px;
        margin-top: 20px;
        padding: 10px;
        background: #f5f5f5;
        border: 1px solid #333;
    }
    .stat { text-align: center; }
    .stat-value { font-size: 24pt; font-weight: bold; }
    .stat-label { font-size: 9pt; color: #666; }

    @media print {
        .form-container { padding: 0; }
        .section { page-break-inside: avoid; }
        .no-print { display: none; }
        body { font-size: 10pt; }
        th, td { padding: 4px 6px; }
    }
    """

    def render_form(self, form: InspectionForm) -> str:
        """Render a single form to HTML."""
        sections_html = '\n'.join(
            self._render_section(section) for section in form.sections
        )

        total_items = form.total_items

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{form.title}</title>
    <style>{self.CSS}</style>
</head>
<body>
    <div class="form-container">
        {self._render_header(form)}
        {sections_html}
        {self._render_footer(form, total_items)}
    </div>
</body>
</html>"""

    def _render_header(self, form: InspectionForm) -> str:
        """Render form header."""
        form_type_label = form.form_type.value

        return f"""
        <div class="form-header">
            <h1>{form_type_label}</h1>
            <h2 style="margin-bottom: 15px;">{form.system} ({form.system_tag})</h2>
            <div class="meta">
                <div class="meta-item">
                    <label>Project:</label>
                    <span>{form.project or '________________'}</span>
                </div>
                <div class="meta-item">
                    <label>Form Version:</label>
                    <span>{form.version}</span>
                </div>
                <div class="meta-item">
                    <label>Date:</label>
                    <span>________________</span>
                </div>
                <div class="meta-item">
                    <label>Location:</label>
                    <span>________________</span>
                </div>
            </div>
            <div class="signature-block">
                <div class="sig-item">
                    <label>Performed By:</label>
                    <div class="sig-line"></div>
                </div>
                <div class="sig-item">
                    <label>Company:</label>
                    <div class="sig-line"></div>
                </div>
                <div class="sig-item">
                    <label>Witnessed By:</label>
                    <div class="sig-line"></div>
                </div>
            </div>
        </div>"""

    def _render_section(self, section) -> str:
        """Render a form section."""
        rows = '\n'.join(
            self._render_check_item(item) for item in section.check_items
        )

        desc_html = ""
        if section.description:
            desc_html = f'<div class="section-desc">{section.description}</div>'

        return f"""
        <div class="section">
            <h2>{section.title}</h2>
            {desc_html}
            <table>
                <thead>
                    <tr>
                        <th class="col-id">ID</th>
                        <th class="col-desc">Description</th>
                        <th class="col-criteria">Acceptance Criteria</th>
                        <th class="col-expected">Expected</th>
                        <th class="col-actual">Actual</th>
                        <th class="col-pf">P/F</th>
                        <th class="col-comments">Comments</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>"""

    def _render_check_item(self, item) -> str:
        """Render a single check item row."""
        priority_class = f"priority-{item.priority.name.lower()}"
        type_badge = f'<span class="type-badge">{item.check_type.value}</span>'

        return f"""
                    <tr class="{priority_class}">
                        <td class="col-id">{item.id}</td>
                        <td class="col-desc">{item.description}{type_badge}</td>
                        <td class="col-criteria">{item.acceptance_criteria}</td>
                        <td class="col-expected">{item.expected_value}</td>
                        <td class="col-actual"></td>
                        <td class="col-pf"></td>
                        <td class="col-comments"></td>
                    </tr>"""

    def _render_footer(self, form: InspectionForm, total_items: int) -> str:
        """Render form footer."""
        return f"""
        <div class="form-footer">
            <div class="summary-stats">
                <div class="stat">
                    <div class="stat-value">{total_items}</div>
                    <div class="stat-label">Total Items</div>
                </div>
                <div class="stat">
                    <div class="stat-value">____</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat">
                    <div class="stat-value">____</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat">
                    <div class="stat-value">____</div>
                    <div class="stat-label">N/A</div>
                </div>
            </div>

            <h3 style="margin-top: 20px;">General Notes / Deficiencies:</h3>
            <div class="notes-area"></div>

            <div class="signature-block" style="margin-top: 30px;">
                <div class="sig-item">
                    <label>Inspector Signature:</label>
                    <div class="sig-line"></div>
                </div>
                <div class="sig-item">
                    <label>Date:</label>
                    <div class="sig-line"></div>
                </div>
                <div class="sig-item">
                    <label>Witness Signature:</label>
                    <div class="sig-line"></div>
                </div>
            </div>
        </div>"""

    def render_index(
        self,
        forms: list[InspectionForm],
        project_name: str = "ITC Forms"
    ) -> str:
        """Render index page linking to all forms."""
        forms_by_system: dict[str, list[InspectionForm]] = {}
        for form in forms:
            key = f"{form.system} ({form.system_tag})"
            if key not in forms_by_system:
                forms_by_system[key] = []
            forms_by_system[key].append(form)

        systems_html = ""
        for system, system_forms in forms_by_system.items():
            links = '\n'.join(
                f'<li><a href="{self._form_filename(f)}">{f.form_type.value}</a> '
                f'({f.total_items} items)</li>'
                for f in system_forms
            )
            systems_html += f"""
            <div class="system-card">
                <h2>{system}</h2>
                <ul>{links}</ul>
            </div>"""

        total_items = sum(f.total_items for f in forms)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - ITC Forms Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f0f0f0; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ margin-bottom: 10px; }}
        .subtitle {{ color: #666; margin-bottom: 30px; }}
        .system-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .system-card h2 {{ margin-bottom: 15px; color: #333; }}
        .system-card ul {{ list-style: none; }}
        .system-card li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .system-card li:last-child {{ border-bottom: none; }}
        .system-card a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: bold;
        }}
        .system-card a:hover {{ text-decoration: underline; }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-box .value {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        .stat-box .label {{ color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project_name}</h1>
        <p class="subtitle">Inspection, Testing & Commissioning Forms</p>

        <div class="stats">
            <div class="stat-box">
                <div class="value">{len(forms_by_system)}</div>
                <div class="label">Systems</div>
            </div>
            <div class="stat-box">
                <div class="value">{len(forms)}</div>
                <div class="label">Forms</div>
            </div>
            <div class="stat-box">
                <div class="value">{total_items}</div>
                <div class="label">Check Items</div>
            </div>
        </div>

        {systems_html}
    </div>
</body>
</html>"""

    def _form_filename(self, form: InspectionForm) -> str:
        """Generate filename for a form."""
        safe_system = form.system_tag or form.system.replace(' ', '_')
        return f"{safe_system}_{form.form_type.name}.html"

