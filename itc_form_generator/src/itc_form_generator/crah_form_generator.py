"""
CRAH (Computer Room Air Handler) Form Generator

This module generates ITC forms for CRAH equipment by parsing SOO documents
and applying the CRAH-specific templates to produce BIM360 ACC compatible output.
"""

import re
from typing import Optional
from dataclasses import dataclass, field

from .models import (
    InspectionForm, FormSection, CheckItem, FormType,
    CheckItemType, Priority
)
from .crah_templates import (
    CRAHTemplate, ChecklistSection, ChecklistItem, ResponseType,
    create_l3l4_crah_fpt_template
)


@dataclass
class CRAHSetpoint:
    """A setpoint extracted from the SOO."""
    name: str
    value: str
    delay: str = "N/A"
    unit: str = ""


@dataclass
class CRAHAlert:
    """An alert extracted from the SOO."""
    name: str
    description: str
    priority: int = 2
    delay: str = ""


@dataclass
class CRAHFailureMode:
    """A failure mode extracted from the SOO."""
    component: str
    condition: str
    action: str


@dataclass
class CRAHSystem:
    """Parsed CRAH system information from SOO."""
    name: str = "Computer Room Air Handler"
    tag: str = "CRAH"
    description: str = ""
    setpoints: list[CRAHSetpoint] = field(default_factory=list)
    alerts: list[CRAHAlert] = field(default_factory=list)
    failure_modes: list[CRAHFailureMode] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    control_sequences: list[str] = field(default_factory=list)


def parse_crah_soo(content: str) -> CRAHSystem:
    """
    Parse a CRAH Sequence of Operations document.

    Args:
        content: The text content of the SOO document

    Returns:
        CRAHSystem object with extracted information
    """
    system = CRAHSystem()

    # Extract system name from document title
    title_match = re.search(
        r'CONTROL SEQUENCES? FOR\s+(.+?)(?:\n|V\d+|\()',
        content, re.IGNORECASE
    )
    if title_match:
        system.name = title_match.group(1).strip()

    # Extract setpoints from tables or lists
    system.setpoints = _extract_setpoints(content)

    # Extract alerts
    system.alerts = _extract_alerts(content)

    # Extract failure modes
    system.failure_modes = _extract_failure_modes(content)

    # Extract equipment lists
    system.equipment = _extract_equipment(content)

    # Extract instruments
    system.instruments = _extract_instruments(content)

    # Extract control sequences
    system.control_sequences = _extract_control_sequences(content)

    return system


def _extract_setpoints(content: str) -> list[CRAHSetpoint]:
    """Extract setpoints from the SOO content."""
    setpoints = []

    # Pattern for setpoint tables: "Parameter | Set Point | Time delay"
    # Example: "Eco Mode Room Temp Setpoint | 77 °F | N/A"
    table_pattern = re.compile(
        r'([A-Za-z][A-Za-z\s]+(?:Setpoint|Temperature|Temp|Alert))\s*'
        r'(\d+\.?\d*)\s*°?([FC]|°F|°C)?\s*'
        r'(?:(\d+\s*(?:sec|min|seconds|minutes))|N/?A)?',
        re.IGNORECASE
    )

    for match in table_pattern.finditer(content):
        name = match.group(1).strip()
        value = match.group(2)
        unit = match.group(3) or "°F"
        delay = match.group(4) or "N/A"

        # Normalize unit
        if unit.upper() in ('F', '°F'):
            unit = "°F"
        elif unit.upper() in ('C', '°C'):
            unit = "°C"

        setpoints.append(CRAHSetpoint(
            name=name,
            value=f"{value}{unit}",
            delay=delay
        ))

    # Also look for specific known CRAH setpoints
    known_setpoints = [
        (r'Eco Mode Room Temp(?:erature)? Setpoint[:\s]+(\d+)\s*°?F',
         "Eco Mode Room Temp Setpoint"),
        (r'Supply Air Temp(?:erature)? Setpoint[:\s]+(\d+)\s*°?F',
         "Supply Air Temp Setpoint"),
        (r'Room Temp(?:erature)? Setpoint on UPS[^:]*[:\s]+(\d+)\s*°?F',
         "Room Temp Setpoint on UPS Power (Battery Mode)"),
        (r'Supply Air High Temperature Alert[^:]*[:\s]+(?:Setpoint\s*\+\s*)?(\d+)\s*°?F',
         "Supply Air High Temperature Alert Setpoint"),
        (r'Room High Temperature Alert[^:]*[:\s]+(?:Setpoint\s*\+\s*)?(\d+)\s*°?F',
         "Room High Temperature Alert Setpoint"),
    ]

    for pattern, name in known_setpoints:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Check if we already have this setpoint
            existing = [sp for sp in setpoints if name.lower() in sp.name.lower()]
            if not existing:
                value = match.group(1)
                # Look for associated delay
                delay_match = re.search(
                    rf'{name}[^.]*?(\d+\s*(?:sec|min))',
                    content, re.IGNORECASE
                )
                delay = delay_match.group(1) if delay_match else "N/A"

                setpoints.append(CRAHSetpoint(
                    name=name,
                    value=f"{value}°F",
                    delay=delay
                ))

    # Deduplicate
    seen = set()
    unique_setpoints = []
    for sp in setpoints:
        key = sp.name.lower()
        if key not in seen:
            seen.add(key)
            unique_setpoints.append(sp)

    return unique_setpoints


def _extract_alerts(content: str) -> list[CRAHAlert]:
    """Extract alert definitions from the SOO content."""
    alerts = []

    # Look for Alerts section
    alert_section = re.search(
        r'(?:Alerts|ALERTS)[:\s]*\n(.*?)(?:\n\d+\.\d+|\nPART|\nEND OF|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    if alert_section:
        alert_text = alert_section.group(1)

        # Pattern for numbered alert items
        alert_items = re.findall(
            r'\d+\.\s*([A-Za-z][^\n]+)',
            alert_text
        )

        for item in alert_items:
            alerts.append(CRAHAlert(
                name=item.strip(),
                description=item.strip()
            ))

    # Also look for specific alert patterns throughout document
    alert_patterns = [
        r'(CRAH General Fault)',
        r'(Loss of Communication)',
        r'(Loss of Communication Between Units)',
        r'(Leak Detected)',
        r'(Exhaust Fan Run Status)',
        r'(High Temperature Alert)',
        r'(Low Temperature Alert)',
        r'(Sensor Failure)',
        r'(Valve Signal Status Mismatch)',
        r'(CRAH Fail to Run)',
    ]

    for pattern in alert_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            name = re.search(pattern, content, re.IGNORECASE).group(1)
            if not any(a.name.lower() == name.lower() for a in alerts):
                alerts.append(CRAHAlert(name=name, description=name))

    return alerts


def _extract_failure_modes(content: str) -> list[CRAHFailureMode]:
    """Extract failure modes from the SOO content."""
    failure_modes = []

    # Look for Failure Modes section
    fm_section = re.search(
        r'(?:Failure Modes?|FAILURE MODES?)[:\s]*\n(.*?)(?:\n\d+\.\d+|\nPART|\nEND OF|Alerts|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    if fm_section:
        fm_text = fm_section.group(1)

        # Pattern for component + failure mode
        # e.g., "Loss of Power to a single CRAH unit: the associated CRAH..."
        fm_items = re.findall(
            r'([A-Za-z][^:]+):\s*([^\n]+(?:\n(?![A-Z\d])[^\n]+)*)',
            fm_text
        )

        for condition, action in fm_items:
            failure_modes.append(CRAHFailureMode(
                component="CRAH",
                condition=condition.strip(),
                action=action.strip()
            ))

    # Look for specific known failure modes
    known_failures = [
        ("CRAH Units", "Loss of Power", "associated CRAH compensates, alert generated"),
        ("CRAH Units", "Loss of communication", "units operate independently, alert generated"),
        ("Control Valve", "Loss of Power", "valve fails open (FO)"),
        ("Control Valve", "Loss of Position Command", "valve fails open (FO)"),
        ("Fan Array", "Supply Air Temperature Sensor Lost", "CRAH disabled, alert generated"),
        ("Fan Array", "Room Temperature Sensor Lost", "uses other CRAH sensor, continues operating"),
    ]

    for component, condition, action in known_failures:
        pattern = rf'{condition}'
        if re.search(pattern, content, re.IGNORECASE):
            if not any(fm.condition.lower() == condition.lower() for fm in failure_modes):
                failure_modes.append(CRAHFailureMode(
                    component=component,
                    condition=condition,
                    action=action
                ))

    return failure_modes


def _extract_equipment(content: str) -> list[str]:
    """Extract major equipment from SOO."""
    equipment = []

    # Look for Major Equipment section
    equip_section = re.search(
        r'Major Equipment[:\s]*\n(.*?)(?:Major Instruments|Supervisory|\d+\.\d+)',
        content, re.DOTALL | re.IGNORECASE
    )

    if equip_section:
        # Extract lettered/numbered items
        items = re.findall(
            r'[a-z]\.\s*([^\n(]+)',
            equip_section.group(1), re.IGNORECASE
        )
        equipment.extend([item.strip() for item in items])

    # Default CRAH equipment if none found
    if not equipment:
        equipment = [
            "Hydronic Cooling Coils (2)",
            "Facility Water Return Control Valve (1)",
            "Unitary Controller",
            "Fan Array (6 Fans)"
        ]

    return equipment


def _extract_instruments(content: str) -> list[str]:
    """Extract major instruments from SOO."""
    instruments = []

    # Look for Major Instruments section
    instr_section = re.search(
        r'Major Instruments[:\s]*\n(.*?)(?:Supervisory|Communications|\d+\.\d+)',
        content, re.DOTALL | re.IGNORECASE
    )

    if instr_section:
        items = re.findall(
            r'[a-z]\.\s*([^\n(]+)',
            instr_section.group(1), re.IGNORECASE
        )
        instruments.extend([item.strip() for item in items])

    # Default CRAH instruments if none found
    if not instruments:
        instruments = [
            "Facility Water Return Control Valve Actuator (1)",
            "Room Temperature Sensor (1)",
            "Supply Air Temperature (SAT) Sensor (1)",
            "Integral Drip Pan Leak Detection Sensor (1)"
        ]

    return instruments


def _extract_control_sequences(content: str) -> list[str]:
    """Extract key control sequence descriptions."""
    sequences = []

    # Look for operation descriptions
    operation_patterns = [
        r'modulate[s]?\s+the\s+([^\n.]+)',
        r'shall\s+operate\s+([^\n.]+)',
        r'shall\s+modulate\s+([^\n.]+)',
        r'is\s+controlled\s+by\s+([^\n.]+)',
    ]

    for pattern in operation_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        sequences.extend(matches)

    return sequences[:10]  # Limit to 10 key sequences


def generate_crah_fpt_form(system: CRAHSystem, project_number: str = "") -> InspectionForm:
    """
    Generate a CRAH Functional Performance Test form from parsed SOO data.

    Args:
        system: Parsed CRAHSystem object
        project_number: Project number for form naming

    Returns:
        InspectionForm with CRAH FPT content
    """
    # Convert setpoints to dict format for template
    setpoint_dicts = [
        {"name": sp.name, "value": sp.value, "delay": sp.delay}
        for sp in system.setpoints
    ]

    # Get the CRAH template
    template = create_l3l4_crah_fpt_template(setpoint_dicts if setpoint_dicts else None)

    # Convert template to InspectionForm
    form = InspectionForm(
        form_type=FormType.FPT,
        system=system.name,
        system_tag=system.tag,
        title=f"L3L4 {system.name} Functional Performance Test"
    )

    # Convert template sections to form sections
    for template_section in template.sections:
        section = FormSection(
            title=template_section.name,
            description=f"Section for {template_section.name}"
        )

        for item in template_section.items:
            # Map response type to check item type
            check_type = _response_type_to_check_type(item.response_type)

            check_item = CheckItem(
                id=f"CRAH-{item.display_number:03d}",
                description=item.item_text,
                check_type=check_type,
                priority=Priority.MEDIUM,
                acceptance_criteria=_get_acceptance_criteria(item),
                expected_value=item.default_answer if item.default_answer else ""
            )
            section.check_items.append(check_item)

        if section.check_items:  # Only add non-empty sections
            form.sections.append(section)

    # Add system-specific sections based on SOO data
    _add_soo_specific_sections(form, system)

    return form


def _response_type_to_check_type(response_type: ResponseType) -> CheckItemType:
    """Map template ResponseType to CheckItemType."""
    mapping = {
        ResponseType.GROUP_HEADER: CheckItemType.DOCUMENTATION,
        ResponseType.PASS_FAIL_NA: CheckItemType.VERIFICATION,
        ResponseType.YES_NO_NA: CheckItemType.FUNCTIONAL,
        ResponseType.TEXT: CheckItemType.DOCUMENTATION,
        ResponseType.DATE: CheckItemType.DOCUMENTATION,
        ResponseType.NUMBER: CheckItemType.MEASUREMENT,
    }
    return mapping.get(response_type, CheckItemType.VERIFICATION)


def _get_acceptance_criteria(item: ChecklistItem) -> str:
    """Generate acceptance criteria based on response type."""
    if item.response_type == ResponseType.PASS_FAIL_NA:
        return "Pass required for acceptance"
    elif item.response_type == ResponseType.YES_NO_NA:
        return "Complete action as specified"
    elif item.response_type == ResponseType.TEXT:
        return "Record value"
    elif item.response_type == ResponseType.DATE:
        return "Enter date"
    return ""


def _add_soo_specific_sections(form: InspectionForm, system: CRAHSystem):
    """Add sections specific to the SOO content."""

    # Add equipment verification section if we have equipment list
    if system.equipment:
        section = FormSection(
            title="Equipment Verification",
            description="Verify major equipment per SOO"
        )
        for i, equip in enumerate(system.equipment, 1):
            section.check_items.append(CheckItem(
                id=f"CRAH-EQ-{i:02d}",
                description=f"Verify {equip} is installed and operational",
                check_type=CheckItemType.VISUAL,
                priority=Priority.HIGH
            ))
        form.sections.append(section)

    # Add instrument verification section
    if system.instruments:
        section = FormSection(
            title="Instrument Verification",
            description="Verify major instruments per SOO"
        )
        for i, instr in enumerate(system.instruments, 1):
            section.check_items.append(CheckItem(
                id=f"CRAH-IN-{i:02d}",
                description=f"Verify {instr} is installed and calibrated",
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH
            ))
        form.sections.append(section)

    # Add alert testing section based on extracted alerts
    if system.alerts:
        section = FormSection(
            title="Alert Testing",
            description="Test all alerts defined in SOO"
        )
        for i, alert in enumerate(system.alerts, 1):
            section.check_items.append(CheckItem(
                id=f"CRAH-AL-{i:02d}",
                description=f"Test alert: {alert.name}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH
            ))
            section.check_items.append(CheckItem(
                id=f"CRAH-AL-{i:02d}a",
                description=f"Alert is initiated at BMS graphic(s)",
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH
            ))
            section.check_items.append(CheckItem(
                id=f"CRAH-AL-{i:02d}b",
                description=f"Alert clears when condition is resolved",
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH
            ))
        form.sections.append(section)

    # Add failure mode testing based on extracted failure modes
    if system.failure_modes:
        section = FormSection(
            title="Failure Mode Testing",
            description="Test failure modes defined in SOO"
        )
        for i, fm in enumerate(system.failure_modes, 1):
            section.check_items.append(CheckItem(
                id=f"CRAH-FM-{i:02d}",
                description=f"Simulate {fm.condition} on {fm.component}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH
            ))
            section.check_items.append(CheckItem(
                id=f"CRAH-FM-{i:02d}a",
                description=f"Verify response: {fm.action}",
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH
            ))
        form.sections.append(section)


def generate_crah_forms_from_soo(soo_content: str, project_number: str = "") -> list[InspectionForm]:
    """
    Generate all CRAH forms from SOO content.

    This is the main entry point for CRAH form generation.

    Args:
        soo_content: Text content of the SOO document
        project_number: Optional project number

    Returns:
        List of InspectionForm objects
    """
    # Parse the SOO
    system = parse_crah_soo(soo_content)

    # Generate FPT form
    fpt_form = generate_crah_fpt_form(system, project_number)

    return [fpt_form]
