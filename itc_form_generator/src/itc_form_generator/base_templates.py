"""
Base Templates for ITC Form Generation

This module provides common sections and patterns used across all equipment types
in BIM360 ACC format. All equipment-specific templates should inherit from these.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ResponseType(Enum):
    """Response types matching BIM360 ACC format."""
    GROUP_HEADER = "Group Header"
    PASS_FAIL_NA = "Pass, Fail, N/A"
    YES_NO_NA = "Yes, No, N/A"
    TEXT = "Text"
    DATE = "Date"
    NUMBER = "Number"


@dataclass
class ChecklistItem:
    """A single checklist item in the form."""
    display_number: int
    item_text: str
    response_type: ResponseType
    dropdown_answers: str = ""
    default_answer: str = ""
    nonconformance_answers: str = ""
    revision: str = ""


@dataclass
class ChecklistSection:
    """A section (group) of checklist items."""
    name: str
    items: list[ChecklistItem] = field(default_factory=list)


def create_standard_header_sections(form_name: str) -> tuple[list[ChecklistSection], int]:
    """
    Create all standard header sections common to all FPT forms.

    Returns:
        Tuple of (list of ChecklistSections, next_display_number)
    """
    sections = []
    num = 1

    # Document Header
    header = ChecklistSection(name=form_name)
    header.items = [
        ChecklistItem(num, form_name, ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Equipment Designation", ResponseType.TEXT),
        ChecklistItem(num + 2, "Commence Date", ResponseType.DATE),
        ChecklistItem(num + 3, "Commissioning Authority (Name)", ResponseType.TEXT),
    ]
    sections.append(header)
    num += 4

    # General Section
    general = ChecklistSection(name="General")
    general.items = [
        ChecklistItem(num, "General", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1,
            "While Performing This Procedure:\n**Items that do not apply shall be noted with N/A response.\n**Any issues or failures must be documented with Non-Conformance.",
            ResponseType.YES_NO_NA),
        ChecklistItem(num + 2,
            "TEST EXECUTION / COMPLETION REQUIREMENTS:\nThe actual testing procedure shall be completed in accordance with the approved SOO.",
            ResponseType.YES_NO_NA),
    ]
    sections.append(general)
    num += 3

    # Commissioning Support
    support = ChecklistSection(name="I. Commissioning Support")
    support.items = [
        ChecklistItem(num, "I. Commissioning Support", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "All necessary personnel are available to exercise the equipment", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 2, "Document the full names of all participating parties:", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 3, "Electrical Contractor", ResponseType.TEXT),
        ChecklistItem(num + 4, "Mechanical Contractor", ResponseType.TEXT),
        ChecklistItem(num + 5, "Equipment Vendor", ResponseType.TEXT),
        ChecklistItem(num + 6, "CSI Representative", ResponseType.TEXT),
        ChecklistItem(num + 7, "DSI Representative", ResponseType.TEXT),
        ChecklistItem(num + 8, "Client Representative", ResponseType.TEXT),
    ]
    sections.append(support)
    num += 9

    # Procedure Modifications
    mods = ChecklistSection(name="II. Procedure Modifications")
    mods.items = [
        ChecklistItem(num, "II. Procedure Modifications", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Modification to or any additional testing not specifically indicated in the approved procedure require pre-approval documentation.", ResponseType.YES_NO_NA),
    ]
    sections.append(mods)
    num += 2

    # Prerequisites
    prereqs = ChecklistSection(name="III. Prerequisites")
    prereqs.items = [
        ChecklistItem(num, "III. Prerequisites", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "All Level 1 Factory witness testing and documentation is complete", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 2, "All Level 2 Site arrival inspections, construction checklists complete", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 3, "All Level 3 Start-up procedures (Mech/Elec) completed", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 4, "This FPT procedure has been made available for review (record date):", ResponseType.TEXT),
        ChecklistItem(num + 5, "The EPMS and/or BMS system is ready and functioning properly", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 6, "Load Bank Plan requirements have been met (if applicable)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 7, "ACCBuild Equipment Information has been completed", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 8, "Test, Adjust, Balance (TAB) testing is complete", ResponseType.PASS_FAIL_NA),
    ]
    sections.append(prereqs)
    num += 9

    # Documentation
    docs = ChecklistSection(name="IV. Documentation")
    docs.items = [
        ChecklistItem(num, "IV. Documentation\n**Confirm Availability & Note Revision Prior to testing", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Sequence of Operation (record rev)", ResponseType.TEXT),
        ChecklistItem(num + 2, "BMS Points List (EOR rev)", ResponseType.TEXT),
        ChecklistItem(num + 3, "Client Global Settings (record rev)", ResponseType.TEXT),
        ChecklistItem(num + 4, "Test & Balance (TAB) report", ResponseType.PASS_FAIL_NA),
    ]
    sections.append(docs)
    num += 5

    # Safety
    safety = ChecklistSection(name="V. Safety & Equipment Requirements")
    safety.items = [
        ChecklistItem(num, "V. Safety & Equipment requirements", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Lock Out Tag Out (LOTO) Plan has been reviewed and is available", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 2, "All parties have been notified, equipped with the necessary PPE", ResponseType.PASS_FAIL_NA),
    ]
    sections.append(safety)
    num += 3

    # Firmware
    firmware = ChecklistSection(name="VI. Equipment Settings & Firmware")
    firmware.items = [
        ChecklistItem(num, "VI. Equipment Settings & Firmware (As Found)", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "OPC Server Type (DA or UA)", ResponseType.TEXT),
        ChecklistItem(num + 2, "OPC Server Version", ResponseType.TEXT),
        ChecklistItem(num + 3, "OPCUA Driver Version", ResponseType.TEXT),
        ChecklistItem(num + 4, "BMS/EPMS version number", ResponseType.TEXT),
        ChecklistItem(num + 5, "Graphics file name", ResponseType.TEXT),
        ChecklistItem(num + 6, "Graphics version number", ResponseType.TEXT),
        ChecklistItem(num + 7, "PLC Firmware Version", ResponseType.TEXT),
        ChecklistItem(num + 8, "PLC Development Version number", ResponseType.TEXT),
        ChecklistItem(num + 9, "PLC Code ZEF file name", ResponseType.TEXT),
        ChecklistItem(num + 10, "PLC Code ZEF version number", ResponseType.TEXT),
        ChecklistItem(num + 11, "PLC Code STA file name", ResponseType.TEXT),
        ChecklistItem(num + 12, "PLC Code STA version number", ResponseType.TEXT),
        ChecklistItem(num + 13, "Confirm STA and ZEF version numbers are identical", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 14, "Record the Modicon M580 PAC Redundant HSBY Processor Module Firmware Version", ResponseType.TEXT),
        ChecklistItem(num + 15, "Record the Modicon M580 ePAC 3-Port Ethernet Communication Module Firmware Version", ResponseType.TEXT),
        ChecklistItem(num + 16, "Record the Modicon M580 EIO Drop Adapter Firmware Version", ResponseType.TEXT),
        ChecklistItem(num + 17, "All Modicon Firmware versions match APPROVED PLC Platform Package", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 18, "Control Expert DFB Library Date", ResponseType.TEXT),
        ChecklistItem(num + 19, "TAB values have been uploaded to applicable parameters", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 20, "VFD/VSD as-Found Settings match the Client Approved Settings", ResponseType.PASS_FAIL_NA),
    ]
    sections.append(firmware)
    num += 21

    return sections, num


def create_sensor_test_section(sensor_name: str, sensor_tag: str, start_num: int,
                                sensor_count: int = 2) -> tuple[ChecklistSection, int]:
    """
    Create a complete sensor test section with selection, OOS, and fault tests.

    Args:
        sensor_name: Human-readable name (e.g., "Outside Air Temperature")
        sensor_tag: BMS point tag base (e.g., "IWM.OA.TEMP")
        start_num: Starting display number
        sensor_count: Number of individual sensors to test (default 2)

    Returns:
        Tuple of (ChecklistSection, next_display_number)
    """
    section = ChecklistSection(name=f"{sensor_name} Test")
    num = start_num
    items = []

    # Main sensor group header
    items.append(ChecklistItem(num, f"{sensor_tag} - {sensor_name}", ResponseType.GROUP_HEADER))
    num += 1

    # Initial setup and selection tests
    items.append(ChecklistItem(num, f"Ensure the {sensor_name} is selected as primary", ResponseType.YES_NO_NA))
    num += 1
    items.append(ChecklistItem(num, "Open the associated sensor(s) popup", ResponseType.YES_NO_NA))
    num += 1
    items.append(ChecklistItem(num, "Record the current values of all sensors and the current min/max/avg values", ResponseType.TEXT))
    num += 1

    # Selection tests
    for selection in ["average", "maximum", "minimum"]:
        items.append(ChecklistItem(num, f"Set selection to {selection}", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, f"Verify the signal matches the {selection} value", ResponseType.PASS_FAIL_NA))
        num += 1

    # Individual sensor tests
    for i in range(1, sensor_count + 1):
        sensor_id = f"{sensor_tag}{i}"
        items.append(ChecklistItem(num, f"[{sensor_id}] Test", ResponseType.GROUP_HEADER))
        num += 1

        # Minimum selection test
        items.append(ChecklistItem(num, "Minimum Selection", ResponseType.GROUP_HEADER))
        num += 1
        items.append(ChecklistItem(num, f"Set [{sensor_id}.Fb] value below all other sensors within tolerance", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify the average value matches the calculated average", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify the maximum value matches the current maximum", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Set selection to minimum", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, f"Verify signal and minimum value is the [{sensor_id}.Fb] value", ResponseType.PASS_FAIL_NA))
        num += 1

        # OOS test
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] out of service (OOS)", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min do not include the OOS sensor", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"[{sensor_tag}.Sel.vSig] remains the controlling signal", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] back in service", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min are the previous values", ResponseType.PASS_FAIL_NA))
        num += 1

        # Channel fault test
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] in channel fault", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min do not include the faulted sensor", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify popups properly indicate the alert (text and highlighting)", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"[{sensor_tag}.Sel.vSig] remains the controlling signal", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] out of channel fault and acknowledge alert", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min are the previous values", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify signal matches current selection", ResponseType.PASS_FAIL_NA))
        num += 1

        # Maximum selection test
        items.append(ChecklistItem(num, "Maximum Selection", ResponseType.GROUP_HEADER))
        num += 1
        items.append(ChecklistItem(num, f"Set [{sensor_id}.Fb] value above all other sensors within tolerance", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify the average value matches calculated average", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify minimum value is the current minimum", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Set selection to maximum", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, f"Verify signal and maximum value is the [{sensor_id}.Fb] value", ResponseType.PASS_FAIL_NA))
        num += 1

        # Repeat OOS and channel fault for maximum
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] out of service (OOS)", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min do not include the OOS sensor", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] back in service", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min are the previous values", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] in channel fault", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min do not include the faulted sensor", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify popups properly indicate the alert", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, f"Place [{sensor_id}.Fb] out of channel fault and acknowledge alert", ResponseType.YES_NO_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify avg/max/min are the previous values", ResponseType.PASS_FAIL_NA))
        num += 1
        items.append(ChecklistItem(num, "Verify signal matches current selection", ResponseType.PASS_FAIL_NA))
        num += 1

    section.items = items
    return section, num


def create_tolerance_test_section(sensor_name: str, sensor_tag: str, start_num: int) -> tuple[ChecklistSection, int]:
    """Create tolerance alert test section."""
    section = ChecklistSection(name=f"{sensor_name} Tolerance Alert Test")
    num = start_num
    items = [
        ChecklistItem(num, "Tolerance Alert Test", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Set the Tolerance Alert Delay to 10 seconds", ResponseType.YES_NO_NA),
        ChecklistItem(num + 2, f"Set [{sensor_tag}.Fb] out of tolerance with other sensors", ResponseType.YES_NO_NA),
        ChecklistItem(num + 3, "Verify out of tolerance alert displays after 10 seconds", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 4, "Verify neither sensor is removed from avg/max/min values", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 5, "Set tolerance alert setpoint above difference between sensors", ResponseType.YES_NO_NA),
        ChecklistItem(num + 6, "Verify out of tolerance alert becomes inactive, unacknowledged", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 7, "Set tolerance alert setpoint back to original value", ResponseType.YES_NO_NA),
        ChecklistItem(num + 8, "Verify out of tolerance alert becomes active", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 9, f"Set [{sensor_tag}.Fb] just within tolerance alert setpoint", ResponseType.YES_NO_NA),
        ChecklistItem(num + 10, "Verify out of tolerance alert becomes inactive", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 11, "Acknowledge the alert", ResponseType.YES_NO_NA),
        ChecklistItem(num + 12, "Set Tolerance Alert Delay back to design value", ResponseType.YES_NO_NA),
        ChecklistItem(num + 13, f"Set [{sensor_tag}.Fb] back to normal/auto", ResponseType.YES_NO_NA),
    ]
    section.items = items
    return section, num + 14


def create_no_sensors_test_section(sensor_name: str, sensor_tags: list[str], start_num: int) -> tuple[ChecklistSection, int]:
    """Create 'No Sensors Available' test section."""
    section = ChecklistSection(name=f"{sensor_name} No Sensors Available Test")
    num = start_num
    items = [
        ChecklistItem(num, "No Sensors available test", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, f"Place [{sensor_tags[0]}.Fb] in channel fault", ResponseType.YES_NO_NA),
        ChecklistItem(num + 2, 'Verify "No Sensors Available" is "False"', ResponseType.PASS_FAIL_NA),
    ]
    num += 3

    if len(sensor_tags) > 1:
        items.extend([
            ChecklistItem(num, f"Place [{sensor_tags[1]}.Fb] in channel fault", ResponseType.YES_NO_NA),
            ChecklistItem(num + 1, 'Verify "No Sensors Available" indicates "True"', ResponseType.PASS_FAIL_NA),
            ChecklistItem(num + 2, "Verify popups properly indicate the alert", ResponseType.PASS_FAIL_NA),
        ])
        num += 3

    items.extend([
        ChecklistItem(num, f"Place [{sensor_tags[0]}.Fb] back in normal operation and acknowledge", ResponseType.YES_NO_NA),
        ChecklistItem(num + 1, 'Verify "No Sensors Available" is "False"', ResponseType.PASS_FAIL_NA),
    ])
    num += 2

    if len(sensor_tags) > 1:
        items.extend([
            ChecklistItem(num, f"Place [{sensor_tags[1]}.Fb] back in normal operation and acknowledge", ResponseType.YES_NO_NA),
            ChecklistItem(num + 1, 'Verify "No Sensors Available" is "False"', ResponseType.PASS_FAIL_NA),
        ])
        num += 2

    items.extend([
        ChecklistItem(num, "Set selection to average", ResponseType.YES_NO_NA),
        ChecklistItem(num + 1, "Verify signal matches calculated average value", ResponseType.PASS_FAIL_NA),
    ])
    num += 2

    section.items = items
    return section, num


def create_communication_failure_section(equipment_name: str, equipment_tag: str, start_num: int) -> tuple[ChecklistSection, int]:
    """Create communication failure test section."""
    section = ChecklistSection(name=f"Communication Failure - {equipment_name}")
    num = start_num
    items = [
        ChecklistItem(num, f"Communication Failure Between {equipment_name}", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, f"Simulate loss of communication to {equipment_tag}", ResponseType.YES_NO_NA),
        ChecklistItem(num + 2, "Verify communication alert is generated after configured delay", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 3, "Verify SCADA shows dithered points (orange question mark)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 4, "Verify equipment continues to operate in last known state", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 5, f"Restore communication to {equipment_tag}", ResponseType.YES_NO_NA),
        ChecklistItem(num + 6, "Verify communication alert clears", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 7, "Verify all points return to normal display", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 8, "Verify equipment returns to normal operation", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section, num + 9


def create_power_failure_section(equipment_name: str, equipment_tag: str, start_num: int) -> tuple[ChecklistSection, int]:
    """Create power failure test section."""
    section = ChecklistSection(name=f"Power Failure - {equipment_name}")
    num = start_num
    items = [
        ChecklistItem(num, f"Power Failure Test - {equipment_name}", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "Verify ATS Source 1 Available is indicated", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 2, "Simulate loss of ATS Source 1 Available signal", ResponseType.YES_NO_NA),
        ChecklistItem(num + 3, "Verify alarm is generated for loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 4, "Brief Interruption Test (< 3 seconds)", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 5, "Simulate brief utility power loss", ResponseType.YES_NO_NA),
        ChecklistItem(num + 6, f"Verify {equipment_tag} attempts restart upon power restoration", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 7, "Generator Backup Test", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 8, "Simulate utility loss causing ATS Source 2 Connected", ResponseType.YES_NO_NA),
        ChecklistItem(num + 9, "Verify alert indicating utility power lost and on generator backup", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 10, "Simulate complete power loss", ResponseType.YES_NO_NA),
        ChecklistItem(num + 11, f"Verify {equipment_tag} maintains run commands for configured period", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 12, "Restore power within 45 seconds", ResponseType.YES_NO_NA),
        ChecklistItem(num + 13, f"Verify {equipment_tag} returns to normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 14, "Verify all alerts clear", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section, num + 15


def create_completion_section(start_num: int) -> tuple[ChecklistSection, int]:
    """Create test completion section."""
    section = ChecklistSection(name="Test Completion")
    num = start_num
    items = [
        ChecklistItem(num, "Test Completion", ResponseType.GROUP_HEADER),
        ChecklistItem(num + 1, "All sections have been completed satisfactorily", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 2, "All alerts and alarms have been cleared", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 3, "All manual overrides have been released", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 4, "All setpoints returned to design values", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 5, "System is operating normally", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 6, "All non-conformances have been documented", ResponseType.PASS_FAIL_NA),
        ChecklistItem(num + 7, "Commissioning Authority Signature", ResponseType.TEXT),
        ChecklistItem(num + 8, "Completion Date", ResponseType.DATE),
        ChecklistItem(num + 9, "Comments/Notes", ResponseType.TEXT),
    ]
    section.items = items
    return section, num + 10
