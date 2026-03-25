"""
IWM (Industrial Water Manager) Form Generator

This module generates ITC forms for IWM equipment by parsing SOO documents
and applying the IWM-specific templates to produce BIM360 ACC compatible output.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import (
    InspectionForm, FormSection, CheckItem, FormType,
    CheckItemType, Priority
)
from .base_templates import (
    ChecklistSection, ChecklistItem, ResponseType,
    create_standard_header_sections,
    create_sensor_test_section,
    create_tolerance_test_section,
    create_no_sensors_test_section,
    create_communication_failure_section,
    create_power_failure_section,
    create_completion_section,
)


@dataclass
class IWMSensor:
    """A sensor extracted from the IWM SOO."""
    name: str
    tag: str
    sensor_type: str = ""  # temperature, pressure, flow, etc.
    count: int = 2  # number of redundant sensors
    unit: str = ""


@dataclass
class IWMEquipment:
    """Equipment controlled by the IWM."""
    name: str
    tag: str
    equipment_type: str = ""
    count: int = 1


@dataclass
class IWMSystem:
    """Parsed IWM system information from SOO."""
    name: str = "Industrial Water Manager"
    tag: str = "IWM"
    description: str = ""
    sensors: list[IWMSensor] = field(default_factory=list)
    equipment: list[IWMEquipment] = field(default_factory=list)
    setpoints: list[dict] = field(default_factory=list)
    failure_modes: list[dict] = field(default_factory=list)
    alert_delays: list[dict] = field(default_factory=list)


def parse_iwm_soo(content: str) -> IWMSystem:
    """
    Parse an IWM Sequence of Operations document.

    Args:
        content: The text content of the SOO document

    Returns:
        IWMSystem object with extracted information
    """
    system = IWMSystem()

    # Extract system name from document title
    title_match = re.search(
        r'CONTROL SEQUENCES? FOR\s+(.+?)(?:\n|V\d+|\()',
        content, re.IGNORECASE
    )
    if title_match:
        system.name = title_match.group(1).strip()

    # Extract sensors
    system.sensors = _extract_iwm_sensors(content)

    # Extract equipment (mCUPs, pumps, etc.)
    system.equipment = _extract_iwm_equipment(content)

    # Extract setpoints
    system.setpoints = _extract_iwm_setpoints(content)

    # Extract failure modes
    system.failure_modes = _extract_iwm_failure_modes(content)

    return system


def _extract_iwm_sensors(content: str) -> list[IWMSensor]:
    """Extract sensor definitions from the IWM SOO."""
    sensors = []

    # Common IWM sensor patterns
    sensor_patterns = [
        # Outside Air Temperature sensors
        (r'Outside Air\s+(?:Drybulb\s+)?Temperature', 'IWM.OA.TEMP', 'temperature', 2),
        (r'Outside Air\s+(?:Relative\s+)?Humidity', 'IWM.OA.RH', 'humidity', 2),
        # Facility Water sensors
        (r'Facility Water\s+(?:Differential\s+)?Pressure', 'DH.FW.DP', 'pressure', 2),
        (r'Facility Water\s+Flow', 'IWM.FW.FLOW', 'flow', 1),
        # Sidestream Filter sensors
        (r'Sidestream Filter Flow', 'IWM.SS.FLOW', 'flow', 1),
        # Make Up Water sensors
        (r'Make Up Water\s+(?:Flow)?', 'IWM.MUW.FLOW', 'flow', 1),
        (r'Building\s+(?:Entry\s+)?Water\s+Meter', 'IWM.BW.FLOW', 'flow', 1),
        # Pressure sensors
        (r'Site Water Pressure', 'IWM.SW.PRESS', 'pressure', 1),
        (r'Facility Water Loop Charge', 'IWM.FW.CHARGE', 'pressure', 1),
    ]

    for name_pattern, tag, sensor_type, count in sensor_patterns:
        if re.search(name_pattern, content, re.IGNORECASE):
            # Try to find actual tag in the document
            tag_match = re.search(rf'\[({tag}[^\]]*)\]', content)
            actual_tag = tag_match.group(1) if tag_match else tag

            sensors.append(IWMSensor(
                name=re.search(name_pattern, content, re.IGNORECASE).group(0).strip(),
                tag=actual_tag,
                sensor_type=sensor_type,
                count=count
            ))

    # Look for DH (Data Hall) DP sensors
    dh_dp_matches = re.findall(r'\[(DH[AB]\.FW\.DP\d+)[^\]]*\]', content)
    for match in dh_dp_matches:
        base_tag = match.rstrip('AB')  # Remove A/B suffix to get base
        if not any(s.tag == base_tag for s in sensors):
            sensors.append(IWMSensor(
                name=f"Facility Water DP - {match[:3]}",
                tag=base_tag,
                sensor_type="pressure",
                count=2
            ))

    return sensors


def _extract_iwm_equipment(content: str) -> list[IWMEquipment]:
    """Extract equipment definitions from the IWM SOO."""
    equipment = []

    # mCUP (modular Cooling Unit Package)
    mcup_match = re.search(r'(\d+)\s*mCUPs?', content, re.IGNORECASE)
    if mcup_match or 'mCUP' in content:
        count = int(mcup_match.group(1)) if mcup_match else 8
        equipment.append(IWMEquipment(
            name="Modular Cooling Unit Package",
            tag="mCUP",
            equipment_type="cooling_unit",
            count=count
        ))

    # Filtration Pumps
    if 'filtration' in content.lower() and 'pump' in content.lower():
        pump_match = re.search(r'(\d+)\s*(?:VFD\s+)?(?:driven\s+)?pumps?', content, re.IGNORECASE)
        count = int(pump_match.group(1)) if pump_match else 2
        equipment.append(IWMEquipment(
            name="IWM Filtration Pump",
            tag="IWM.FP",
            equipment_type="pump",
            count=count
        ))

    return equipment


def _extract_iwm_setpoints(content: str) -> list[dict]:
    """Extract setpoints from the IWM SOO."""
    setpoints = []

    # Flow setpoints
    flow_match = re.search(r'flow rate of\s+(\d+)\s*GPM', content, re.IGNORECASE)
    if flow_match:
        setpoints.append({
            'name': 'Sidestream Filter Flow Rate',
            'value': f"{flow_match.group(1)} GPM",
            'adjustable': True
        })

    # Communication timeout
    comm_match = re.search(r'(\d+)\s+seconds?\s*(?:\(adj\))?\s*(?:has passed|without communication)', content, re.IGNORECASE)
    if comm_match:
        setpoints.append({
            'name': 'Communication Heartbeat Timeout',
            'value': f"{comm_match.group(1)} seconds",
            'adjustable': True
        })

    # Tolerance setpoints
    tolerance_match = re.search(r'(\d+)\s*psi\s+(?:difference|tolerance)', content, re.IGNORECASE)
    if tolerance_match:
        setpoints.append({
            'name': 'DP Sensor Out of Tolerance',
            'value': f"{tolerance_match.group(1)} psi",
            'adjustable': True
        })

    return setpoints


def _extract_iwm_failure_modes(content: str) -> list[dict]:
    """Extract failure modes from the IWM SOO."""
    failure_modes = []

    # Communication failure
    if 'communication failure' in content.lower() or 'loss of communication' in content.lower():
        failure_modes.append({
            'name': 'Communication Failure',
            'response': 'Continue in last known state, generate alert'
        })

    # Power failure
    if 'power failure' in content.lower() or 'loss of power' in content.lower():
        failure_modes.append({
            'name': 'Power Failure',
            'response': 'Monitor ATS signals, maintain run commands'
        })

    # Controller failure
    if 'controller fail' in content.lower():
        failure_modes.append({
            'name': 'IWM Controller Failure',
            'response': 'Redundant controller takes over'
        })

    # mCUP failure
    if 'mcup fail' in content.lower() or 'mcup fault' in content.lower():
        failure_modes.append({
            'name': 'mCUP Failure',
            'response': 'Stage on next available mCUP'
        })

    # Sensor failure
    if 'sensor fail' in content.lower() or 'sensor fault' in content.lower():
        failure_modes.append({
            'name': 'Sensor Failure',
            'response': 'Indicate input as bad, exclude from calculations'
        })

    return failure_modes


def generate_iwm_fpt_form(system: IWMSystem, project_number: str = "") -> InspectionForm:
    """
    Generate an IWM Functional Performance Test form from parsed SOO data.

    Args:
        system: Parsed IWMSystem object
        project_number: Project number for form naming

    Returns:
        InspectionForm with IWM FPT content
    """
    form_name = f"L3L4_{system.tag} Manager_FunctionalPerformanceTest"

    # Start with standard header sections
    sections, num = create_standard_header_sections(form_name)

    # Add sensor test sections for each sensor type
    for sensor in system.sensors:
        # Create sensor selection and individual tests
        sensor_section, num = create_sensor_test_section(
            sensor.name, sensor.tag, num, sensor.count
        )
        sections.append(sensor_section)

        # Add tolerance test if applicable (for paired sensors)
        if sensor.count >= 2:
            tolerance_section, num = create_tolerance_test_section(
                sensor.name, f"{sensor.tag}#", num
            )
            sections.append(tolerance_section)

            # Add no sensors available test
            sensor_tags = [f"{sensor.tag}A", f"{sensor.tag}B"]
            no_sensors_section, num = create_no_sensors_test_section(
                sensor.name, sensor_tags, num
            )
            sections.append(no_sensors_section)

    # Add communication failure test
    comm_section, num = create_communication_failure_section(
        "IWM and mCUP PLC", "mCUP", num
    )
    sections.append(comm_section)

    # Add power failure test
    power_section, num = create_power_failure_section(
        "IWM System", "IWM", num
    )
    sections.append(power_section)

    # Add completion section
    completion_section, num = create_completion_section(num)
    sections.append(completion_section)

    # Convert template sections to InspectionForm
    form = InspectionForm(
        form_type=FormType.FPT,
        system=system.name,
        system_tag=system.tag,
        title=f"L3L4 {system.name} Functional Performance Test"
    )

    # Convert ChecklistSections to FormSections
    for template_section in sections:
        section = FormSection(
            title=template_section.name,
            description=f"Section for {template_section.name}"
        )

        for item in template_section.items:
            check_type = _response_type_to_check_type(item.response_type)

            check_item = CheckItem(
                id=f"IWM-{item.display_number:03d}",
                description=item.item_text,
                check_type=check_type,
                priority=Priority.MEDIUM,
                acceptance_criteria=_get_acceptance_criteria(item),
                expected_value=item.default_answer if item.default_answer else ""
            )
            section.check_items.append(check_item)

        if section.check_items:
            form.sections.append(section)

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


def generate_iwm_forms_from_soo(soo_content: str, project_number: str = "") -> list[InspectionForm]:
    """
    Generate all IWM forms from SOO content.

    This is the main entry point for IWM form generation.

    Args:
        soo_content: Text content of the SOO document
        project_number: Optional project number

    Returns:
        List of InspectionForm objects
    """
    # Parse the SOO
    system = parse_iwm_soo(soo_content)

    # Generate FPT form
    fpt_form = generate_iwm_fpt_form(system, project_number)

    return [fpt_form]
