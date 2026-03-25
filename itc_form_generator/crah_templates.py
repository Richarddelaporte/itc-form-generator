"""
CRAH (Computer Room Air Handler) Templates for ITC Form Generation

This module provides templates for CRAH equipment forms based on the
BIM360 ACC format used in production. Templates are derived from actual
forms like 238123_L3L4_CRAH Unit_FunctionalPerformanceTest.

The structure matches the ACC checklist format:
- Checklist Name
- Permissions
- Auto Create Issue
- Display Number
- Item Text
- Response Type (Group Header, Pass/Fail/N/A, Yes/No/N/A, Text, Date)
- Drop-down Answers
- Default Answer
- Answers that create Non-conformances
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


@dataclass
class CRAHTemplate:
    """Complete CRAH form template."""
    template_id: str
    display_name: str
    level: str  # L3, L4, L3L4
    equipment_type: str = "CRAH"
    variant: str = ""
    sections: list[ChecklistSection] = field(default_factory=list)


def create_crah_header_section() -> ChecklistSection:
    """Create the standard CRAH header/general info section."""
    section = ChecklistSection(name="I. Document Control and General Information")
    items = [
        ChecklistItem(1, "Form Checklist No", ResponseType.TEXT),
        ChecklistItem(2, "Document Revision", ResponseType.TEXT),
        ChecklistItem(3, "Form Checklist Type", ResponseType.TEXT),
        ChecklistItem(4, "Form Title", ResponseType.TEXT),
        ChecklistItem(5, "Contractor Name(s)", ResponseType.TEXT),
        ChecklistItem(6, "Area Name", ResponseType.TEXT),
        ChecklistItem(7, "Equipment Designation", ResponseType.TEXT),
        ChecklistItem(8, "Commence Date", ResponseType.DATE),
        ChecklistItem(9, "Commissioning Authority (Name)", ResponseType.TEXT),
    ]
    section.items = items
    return section


def create_crah_prerequisites_section() -> ChecklistSection:
    """Create prerequisites section for CRAH testing."""
    section = ChecklistSection(name="II. Pre-requisites / Prerequisites")
    items = [
        ChecklistItem(10, "Confirm all previous level checklists have been completed satisfactorily", ResponseType.YES_NO_NA),
        ChecklistItem(11, "All mechanical installations are complete per approved drawings", ResponseType.PASS_FAIL_NA),
        ChecklistItem(12, "All electrical connections are complete and tested", ResponseType.PASS_FAIL_NA),
        ChecklistItem(13, "All control wiring is complete and verified", ResponseType.PASS_FAIL_NA),
        ChecklistItem(14, "System has been flushed and cleaned per project requirements", ResponseType.PASS_FAIL_NA),
        ChecklistItem(15, "TAB (Test and Balance) has been completed", ResponseType.PASS_FAIL_NA),
        ChecklistItem(16, "Confirm Applicable SOO Document Number and Revision", ResponseType.TEXT),
        ChecklistItem(17, "Confirm Applicable Points List Document Number and Revision", ResponseType.TEXT),
    ]
    section.items = items
    return section


def create_crah_software_versions_section() -> ChecklistSection:
    """Create software/firmware versions section."""
    section = ChecklistSection(name="III. Software and Firmware Versions")
    items = [
        ChecklistItem(18, "OPC Server Type (DA or UA)", ResponseType.TEXT),
        ChecklistItem(19, "OPC Server Version", ResponseType.TEXT),
        ChecklistItem(20, "OPCUA Driver Version", ResponseType.TEXT),
        ChecklistItem(21, "BMS/EPMS version number", ResponseType.TEXT),
        ChecklistItem(22, "Graphics file name", ResponseType.TEXT),
        ChecklistItem(23, "Graphics version number", ResponseType.TEXT),
        ChecklistItem(24, "PLC Firmware Version", ResponseType.TEXT),
        ChecklistItem(25, "PLC Development Version number", ResponseType.TEXT),
        ChecklistItem(26, "PLC Code ZEF file name", ResponseType.TEXT),
        ChecklistItem(27, "PLC Code ZEF version number", ResponseType.TEXT),
        ChecklistItem(28, "PLC Code STA file name", ResponseType.TEXT),
        ChecklistItem(29, "PLC Code STA version number", ResponseType.TEXT),
        ChecklistItem(30, "Confirm STA and ZEF version numbers are identical", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_visual_inspection_section() -> ChecklistSection:
    """Create visual inspection section."""
    section = ChecklistSection(name="VII. Visual Inspections")
    items = [
        ChecklistItem(61, "Equipment is free from damage (dents, scratches, etc.)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(62, "Equipment is level and secure", ResponseType.PASS_FAIL_NA),
        ChecklistItem(63, "All doors and latches are firmly secured and locked (as applicable)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(64, "All ancillary meters, switches, gauges, actuators, etc. are installed and operational", ResponseType.PASS_FAIL_NA),
        ChecklistItem(65, "Pressure and temperature indicators are installed and have proper tags", ResponseType.PASS_FAIL_NA),
        ChecklistItem(66, "Permanent labels are applied and accurate", ResponseType.PASS_FAIL_NA),
        ChecklistItem(67, "All naming conventions are accurately displayed on local displays", ResponseType.PASS_FAIL_NA),
        ChecklistItem(68, "Power distribution panel breakers are labeled correctly", ResponseType.PASS_FAIL_NA),
        ChecklistItem(69, "Danger labels and/or permanent Arc Flash labels are applied as required", ResponseType.PASS_FAIL_NA),
        ChecklistItem(70, "Unit electrical disconnects are in place and labeled", ResponseType.PASS_FAIL_NA),
        ChecklistItem(71, "All piping is in place and installed to meet project requirements", ResponseType.PASS_FAIL_NA),
        ChecklistItem(72, "All piping connections are sealed, tight, and weatherproof as applicable", ResponseType.PASS_FAIL_NA),
        ChecklistItem(73, "All piping is insulated as required", ResponseType.PASS_FAIL_NA),
        ChecklistItem(74, "All piping isolation valves are fully operable", ResponseType.PASS_FAIL_NA),
        ChecklistItem(75, "All piping labels are installed as applicable", ResponseType.PASS_FAIL_NA),
        ChecklistItem(76, "All valve tags are installed as applicable", ResponseType.PASS_FAIL_NA),
        ChecklistItem(77, "System has been flushed and cleaned per project requirements", ResponseType.PASS_FAIL_NA),
        ChecklistItem(78, "Verify all ductwork is in place and installed to meet project requirements", ResponseType.PASS_FAIL_NA),
        ChecklistItem(79, "All sensors are installed and properly labeled", ResponseType.PASS_FAIL_NA),
        ChecklistItem(80, "VFD/VSD time and date parameters are accurate", ResponseType.PASS_FAIL_NA),
        ChecklistItem(81, "Control panel drawings are installed in control panels, are current, and legible", ResponseType.PASS_FAIL_NA),
        ChecklistItem(82, "All drain pan and/or piping is installed, sloped properly, and clear of debris", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_graphics_review_section() -> ChecklistSection:
    """Create BMS Graphics review section."""
    section = ChecklistSection(name="VIII. Graphics/BMS Review")
    items = [
        ChecklistItem(83, "Unit Identification is correct on the graphic display", ResponseType.PASS_FAIL_NA),
        ChecklistItem(84, "Confirm window title follows guidelines within the Client Graphics Standard", ResponseType.PASS_FAIL_NA),
        ChecklistItem(85, "Confirm the popup includes the correct equipment mechanical schedule data", ResponseType.PASS_FAIL_NA),
        ChecklistItem(86, "Unit is in correct location on floor plan layout", ResponseType.PASS_FAIL_NA),
        ChecklistItem(87, "All equipment accessories are correctly represented on the graphics", ResponseType.PASS_FAIL_NA),
        ChecklistItem(88, "All graphic animations of equipment actions have been programmed correctly", ResponseType.PASS_FAIL_NA),
        ChecklistItem(89, "All adjustable setpoints are correctly and neatly represented on the graphic", ResponseType.PASS_FAIL_NA),
        ChecklistItem(90, "All feedbacks are correctly and neatly represented on the graphic", ResponseType.PASS_FAIL_NA),
        ChecklistItem(91, "Alerts are correctly represented on graphic display (parameters, priorities, delays)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(92, "Alert priorities have been set and any 'page out' Alerts have been configured correctly", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_setpoint_verification_section(setpoints: list[dict] = None) -> ChecklistSection:
    """Create setpoint verification section based on SOO setpoints."""
    section = ChecklistSection(name="IX. Setpoint Verification")

    # Default CRAH setpoints if none provided
    default_setpoints = [
        {"name": "Eco Mode Room Temp Setpoint", "value": "77°F", "delay": "N/A"},
        {"name": "Supply Air Temp Setpoint on Utility Power", "value": "73°F", "delay": "N/A"},
        {"name": "Room Temp Setpoint on UPS Power (Battery Mode)", "value": "85°F", "delay": "N/A"},
        {"name": "Supply Air High Temperature Alert Setpoint", "value": "Setpoint + 3°F", "delay": "30 sec"},
        {"name": "Room High Temperature Alert Setpoint", "value": "Setpoint + 3°F", "delay": "30 sec"},
    ]

    setpoints = setpoints or default_setpoints
    base_num = 100
    items = []

    for i, sp in enumerate(setpoints):
        items.append(ChecklistItem(
            base_num + i,
            f"Verify {sp['name']} is set to {sp['value']} (Time Delay: {sp.get('delay', 'N/A')})",
            ResponseType.PASS_FAIL_NA
        ))

    items.append(ChecklistItem(
        base_num + len(setpoints),
        "All setpoints match approved SOO document",
        ResponseType.PASS_FAIL_NA
    ))

    section.items = items
    return section


def create_crah_normal_operation_section() -> ChecklistSection:
    """Create normal operation verification section."""
    section = ChecklistSection(name="X. Normal Operation Verification")
    items = [
        ChecklistItem(150, "This section is to be performed separately for each CRAH Unit", ResponseType.YES_NO_NA),
        ChecklistItem(151, "Ensure the unit enable command is active", ResponseType.YES_NO_NA),
        ChecklistItem(152, "Ensure ULM Mode is not active", ResponseType.YES_NO_NA),
        ChecklistItem(153, "Ensure all sensor Channel Alerts are 'Healthy'. If not, investigate and resolve before continuing.", ResponseType.YES_NO_NA),
        ChecklistItem(154, "Facility Water Return Valve modulates to maintain Supply Air Temperature", ResponseType.PASS_FAIL_NA),
        ChecklistItem(155, "Fan Array speed modulates to maintain Room Temperature Setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(156, "Room Temperature is within tolerance of setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(157, "Supply Air Temperature is within tolerance of setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(158, "All BMS points are reading correctly and updating", ResponseType.PASS_FAIL_NA),
        ChecklistItem(159, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_cooling_valve_test_section() -> ChecklistSection:
    """Create cooling valve functional test section."""
    section = ChecklistSection(name="XI. Facility Water Return Control Valve Test")
    items = [
        ChecklistItem(160, "Confirm valve is pressure-independent control type", ResponseType.PASS_FAIL_NA),
        ChecklistItem(161, "Manual override valve to 100% open position", ResponseType.YES_NO_NA),
        ChecklistItem(162, "Valve travels to fully open position", ResponseType.PASS_FAIL_NA),
        ChecklistItem(163, "BMS feedback shows fully open (within tolerance)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(164, "Supply Air Temperature decreases (increased cooling)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(165, "Manual override valve to 0% (fully closed) position", ResponseType.YES_NO_NA),
        ChecklistItem(166, "Valve travels to fully closed position", ResponseType.PASS_FAIL_NA),
        ChecklistItem(167, "BMS feedback shows fully closed (within tolerance)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(168, "Supply Air Temperature increases (decreased cooling)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(169, "Release valve to automatic control", ResponseType.YES_NO_NA),
        ChecklistItem(170, "Valve modulates to maintain Supply Air Temperature setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(171, "Verify failure mode: Loss of power - valve fails OPEN", ResponseType.PASS_FAIL_NA),
        ChecklistItem(172, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_fan_array_test_section() -> ChecklistSection:
    """Create fan array functional test section."""
    section = ChecklistSection(name="XII. Fan Array Control Test")
    items = [
        ChecklistItem(180, "Manual override fan speed to minimum speed", ResponseType.YES_NO_NA),
        ChecklistItem(181, "Fan speed decreases to minimum", ResponseType.PASS_FAIL_NA),
        ChecklistItem(182, "BMS feedback shows minimum speed (within tolerance)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(183, "Manual override fan speed to maximum speed", ResponseType.YES_NO_NA),
        ChecklistItem(184, "Fan speed increases to maximum", ResponseType.PASS_FAIL_NA),
        ChecklistItem(185, "BMS feedback shows maximum speed (within tolerance)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(186, "Release fan to automatic control", ResponseType.YES_NO_NA),
        ChecklistItem(187, "Fan speed modulates to maintain Room Temperature setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(188, "Adjust Room Temperature setpoint up by 2°F", ResponseType.YES_NO_NA),
        ChecklistItem(189, "Fan speed decreases in response to higher setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(190, "Adjust Room Temperature setpoint down by 2°F", ResponseType.YES_NO_NA),
        ChecklistItem(191, "Fan speed increases in response to lower setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(192, "Return setpoint to original value", ResponseType.YES_NO_NA),
        ChecklistItem(193, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_temperature_sensor_alert_section() -> ChecklistSection:
    """Create temperature and pressure sensor alerts test section."""
    section = ChecklistSection(name="XIII. Temperature and Pressure Sensor Alerts")
    items = [
        ChecklistItem(200, "Perform the following sections for each temperature and pressure sensor", ResponseType.YES_NO_NA),

        # Channel/Hardware Failure
        ChecklistItem(201, "Simulate a Channel and/or Hardware Failure Alert by disconnecting the sensor or simulating out-of-range", ResponseType.YES_NO_NA),
        ChecklistItem(202, "Alert is initiated at BMS graphic(s)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(203, "Alert generated at the Alert graphic screen and Priority is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(204, "Email notification sent (Priority 1 Alert only)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(205, "Alert Verbiage and Time Delay are correct per APPROVED SOO", ResponseType.PASS_FAIL_NA),
        ChecklistItem(206, "Sensor is removed from control calculation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(207, "Reset failure/Alert", ResponseType.YES_NO_NA),
        ChecklistItem(208, "Alert is cleared at BMS", ResponseType.PASS_FAIL_NA),
        ChecklistItem(209, "Sensor is returned to control calculation", ResponseType.PASS_FAIL_NA),

        # High Alert
        ChecklistItem(210, "Simulate a High Alert by adjusting the Alert Setpoint below the current reading", ResponseType.YES_NO_NA),
        ChecklistItem(211, "Alert is initiated at BMS graphic(s)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(212, "Alert generated at the Alert graphic screen and Priority is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(213, "Email notification sent (Priority 1 Alert only)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(214, "Alert Verbiage and Time Delay are correct per APPROVED SOO", ResponseType.PASS_FAIL_NA),
        ChecklistItem(215, "Reset failure/Alert", ResponseType.YES_NO_NA),
        ChecklistItem(216, "Alert is cleared at BMS", ResponseType.PASS_FAIL_NA),

        # Low Alert
        ChecklistItem(217, "Simulate a Low Alert by adjusting the Alert Setpoint above the current reading", ResponseType.YES_NO_NA),
        ChecklistItem(218, "Alert is initiated at BMS graphic(s)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(219, "Alert generated at the Alert graphic screen and Priority is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(220, "Email notification sent (Priority 1 Alert only)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(221, "Alert Verbiage and Time Delay are correct per APPROVED SOO", ResponseType.PASS_FAIL_NA),
        ChecklistItem(222, "Reset failure/Alert", ResponseType.YES_NO_NA),
        ChecklistItem(223, "Alert is cleared at BMS", ResponseType.PASS_FAIL_NA),

        # Out of Tolerance
        ChecklistItem(224, "Simulate an Out of Tolerance Alert by adjusting the tolerance setpoint", ResponseType.YES_NO_NA),
        ChecklistItem(225, "Alert is initiated at BMS graphic(s)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(226, "Alert generated at the Alert graphic screen and Priority is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(227, "Email notification sent (Priority 1 Alert only)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(228, "Alert Verbiage and Time Delay are correct per APPROVED SOO", ResponseType.PASS_FAIL_NA),
        ChecklistItem(229, "Sensor is removed from control calculation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(230, "Reset failure/Alert", ResponseType.YES_NO_NA),
        ChecklistItem(231, "Alert is cleared at BMS", ResponseType.PASS_FAIL_NA),
        ChecklistItem(232, "Sensor is returned to control calculation", ResponseType.PASS_FAIL_NA),

        ChecklistItem(233, "Release all manual overrides and simulations, return all setpoints to original values", ResponseType.YES_NO_NA),
    ]
    section.items = items
    return section


def create_crah_loss_of_power_section() -> ChecklistSection:
    """Create CRAH loss of power and recovery test section."""
    section = ChecklistSection(name="XIV. CRAH Unit Loss of Power and Recovery")
    items = [
        ChecklistItem(240, "This section is to be performed separately for each CRAH Unit power feed", ResponseType.YES_NO_NA),
        ChecklistItem(241, "While the unit is running normally, place its feeder breaker in the OFF position", ResponseType.YES_NO_NA),
        ChecklistItem(242, "Unit shuts down", ResponseType.PASS_FAIL_NA),
        ChecklistItem(243, "Alert is initiated at BMS graphic(s)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(244, "Alert generated at the Alert graphic screen and Priority is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(245, "Alert Verbiage and Time Delay are correct per APPROVED SOO", ResponseType.PASS_FAIL_NA),
        ChecklistItem(246, "After 1-minute, place the feeder breaker for the unit in the ON position", ResponseType.YES_NO_NA),
        ChecklistItem(247, "Unit starts up and runs normally", ResponseType.PASS_FAIL_NA),
        ChecklistItem(248, "Alert clears at BMS", ResponseType.PASS_FAIL_NA),
        ChecklistItem(249, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_water_detection_section() -> ChecklistSection:
    """Create water detection monitoring system test section."""
    section = ChecklistSection(name="XV. Water Detection Monitoring System")
    items = [
        ChecklistItem(260, "This section is to be performed separately for each CRAH Unit", ResponseType.YES_NO_NA),
        ChecklistItem(261, "Ensure the unit enable command is active", ResponseType.YES_NO_NA),
        ChecklistItem(262, "Ensure ULM Mode is not active", ResponseType.YES_NO_NA),
        ChecklistItem(263, "Ensure all sensor Channel Alerts are 'Healthy'. If not, investigate and resolve before continuing.", ResponseType.YES_NO_NA),
        ChecklistItem(264, "Simulate a leak by activating the Water Detection device (Consult with vendor for preferred method)", ResponseType.YES_NO_NA),
        ChecklistItem(265, "Verify Audible and Visual alarm at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(266, "After the delay, the common fault alert is generated", ResponseType.PASS_FAIL_NA),
        ChecklistItem(267, "Operating CRAH Unit is commanded OFF and all process areas shutdown", ResponseType.PASS_FAIL_NA),
        ChecklistItem(268, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(269, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(270, "Remove the Leak simulation and reset the alert", ResponseType.YES_NO_NA),
        ChecklistItem(271, "Alarm clears at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(272, "Common fault alert clears", ResponseType.PASS_FAIL_NA),
        ChecklistItem(273, "Duty CRAH Unit is commanded ON and starts up", ResponseType.PASS_FAIL_NA),
        ChecklistItem(274, "On-coming CRAH Unit Supply Fan is commanded on and ramps to speed", ResponseType.PASS_FAIL_NA),
        ChecklistItem(275, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(276, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(277, "Release all manual overrides and simulations, return all setpoints to original values", ResponseType.YES_NO_NA),
    ]
    section.items = items
    return section


def create_crah_phase_failure_section() -> ChecklistSection:
    """Create phase failure alarm test section."""
    section = ChecklistSection(name="XVI. Phase Failure Alarm")
    items = [
        ChecklistItem(280, "This section is to be performed separately for each CRAH Unit", ResponseType.YES_NO_NA),
        ChecklistItem(281, "Ensure the unit enable command is active", ResponseType.YES_NO_NA),
        ChecklistItem(282, "Ensure ULM Mode is not active", ResponseType.YES_NO_NA),
        ChecklistItem(283, "Ensure all sensor Channel Alerts are 'Healthy'. If not, investigate and resolve before continuing.", ResponseType.YES_NO_NA),
        ChecklistItem(284, "Simulate a Phase Failure Alarm (Consult with vendor for preferred method)", ResponseType.YES_NO_NA),
        ChecklistItem(285, "Verify alarm at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(286, "After the delay, the common fault alert is generated", ResponseType.PASS_FAIL_NA),
        ChecklistItem(287, "Operating CRAH Unit is commanded OFF and all process areas shutdown", ResponseType.PASS_FAIL_NA),
        ChecklistItem(288, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(289, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(290, "Remove the Phase Failure simulation and reset the alert", ResponseType.YES_NO_NA),
        ChecklistItem(291, "Alarm clears at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(292, "Common fault alert clears", ResponseType.PASS_FAIL_NA),
        ChecklistItem(293, "CRAH Unit is commanded ON and starts up", ResponseType.PASS_FAIL_NA),
        ChecklistItem(294, "On-coming CRAH Unit Supply Fan is commanded on and ramps to speed", ResponseType.PASS_FAIL_NA),
        ChecklistItem(295, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(296, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(297, "Release all manual overrides and simulations, return all setpoints to original values", ResponseType.YES_NO_NA),
    ]
    section.items = items
    return section


def create_crah_freeze_protection_section() -> ChecklistSection:
    """Create freeze protection test section."""
    section = ChecklistSection(name="XVII. Freeze Protection")
    items = [
        ChecklistItem(300, "This section is to be performed separately for each CRAH Unit", ResponseType.YES_NO_NA),
        ChecklistItem(301, "Ensure the unit enable command is active", ResponseType.YES_NO_NA),
        ChecklistItem(302, "Ensure ULM Mode is not active", ResponseType.YES_NO_NA),
        ChecklistItem(303, "Ensure all sensor Channel Alerts are 'Healthy'. If not, investigate and resolve before continuing.", ResponseType.YES_NO_NA),
        ChecklistItem(304, "Simulate a need for Freeze Protection by adjusting the control setpoint", ResponseType.YES_NO_NA),
        ChecklistItem(305, "Verify alarm at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(306, "CRAH Unit remains operating", ResponseType.PASS_FAIL_NA),
        ChecklistItem(307, "Cooling Valve management is disabled and the Temperature Control Valve closes", ResponseType.PASS_FAIL_NA),
        ChecklistItem(308, "Supply Fan speed continues to modulate based on room temperature", ResponseType.PASS_FAIL_NA),
        ChecklistItem(309, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(310, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(311, "Remove the Freeze Protection simulation and reset the alert", ResponseType.YES_NO_NA),
        ChecklistItem(312, "Alarm clears at the local controller", ResponseType.PASS_FAIL_NA),
        ChecklistItem(313, "Cooling Valve management resumes normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(314, "Temperature Control Valve modulates to maintain setpoint", ResponseType.PASS_FAIL_NA),
        ChecklistItem(315, "Other CRAH Unit remains in normal operation", ResponseType.PASS_FAIL_NA),
        ChecklistItem(316, "BMS status is correct", ResponseType.PASS_FAIL_NA),
        ChecklistItem(317, "Release all manual overrides and simulations, return all setpoints to original values", ResponseType.YES_NO_NA),
    ]
    section.items = items
    return section


def create_crah_utility_loss_section() -> ChecklistSection:
    """Create utility loss mode test section based on SOO."""
    section = ChecklistSection(name="XVIII. Utility Loss Mode")
    items = [
        # Momentary Disturbance (3 seconds)
        ChecklistItem(320, "Momentary Disturbance (3 seconds)", ResponseType.GROUP_HEADER),
        ChecklistItem(321, "Simulate momentary utility loss (< 3 seconds)", ResponseType.YES_NO_NA),
        ChecklistItem(322, "CRAH is de-energized on loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(323, "PLC removes the CRAH Enable signal during loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(324, "Upon return to utility power, CRAH is re-enabled", ResponseType.PASS_FAIL_NA),
        ChecklistItem(325, "CRAH ramps up to setpoint", ResponseType.PASS_FAIL_NA),

        # Battery Operation Transition (3-45 seconds)
        ChecklistItem(326, "Battery Operation Transition (between 3 and 45 seconds)", ResponseType.GROUP_HEADER),
        ChecklistItem(327, "Simulate utility loss lasting between 3 and 45 seconds", ResponseType.YES_NO_NA),
        ChecklistItem(328, "CRAH is de-energized on loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(329, "PLC removes the CRAH Enable signal during loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(330, "Upon Generator Running signal, CRAH is re-enabled", ResponseType.PASS_FAIL_NA),
        ChecklistItem(331, "CRAH ramps up to setpoint (Battery Discharge)", ResponseType.PASS_FAIL_NA),

        # Controlled Shutdown (> 45 seconds)
        ChecklistItem(332, "Controlled Shutdown (greater than 45 seconds)", ResponseType.GROUP_HEADER),
        ChecklistItem(333, "Simulate utility loss lasting greater than 45 seconds", ResponseType.YES_NO_NA),
        ChecklistItem(334, "CRAH is de-energized on loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(335, "PLC removes the CRAH Enable signal during loss of utility power", ResponseType.PASS_FAIL_NA),
        ChecklistItem(336, "Upon Generator Running signal, CRAH is re-enabled", ResponseType.PASS_FAIL_NA),
        ChecklistItem(337, "CRAH ramps up to setpoint (Battery Discharge)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(338, "After 5 minutes on generator power, PLC removes CRAH enable signal", ResponseType.PASS_FAIL_NA),
        ChecklistItem(339, "CRAH units are disabled, split systems provide cooling", ResponseType.PASS_FAIL_NA),
        ChecklistItem(340, "Upon re-establishment of utility source, MSB transitions back to utility", ResponseType.PASS_FAIL_NA),
        ChecklistItem(341, "CRAHs begin normal operations for Eco Mode Room Temperature Setpoint", ResponseType.PASS_FAIL_NA),

        ChecklistItem(342, "Release all manual overrides and simulations, return all setpoints to original values", ResponseType.YES_NO_NA),
        ChecklistItem(343, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_communication_loss_section() -> ChecklistSection:
    """Create communication loss test section."""
    section = ChecklistSection(name="XIX. Loss of Communication Test")
    items = [
        ChecklistItem(350, "Simulate loss of communication to SCADA", ResponseType.YES_NO_NA),
        ChecklistItem(351, "CRAH units continue to operate independently", ResponseType.PASS_FAIL_NA),
        ChecklistItem(352, "Alert is generated at SCADA (once communication restored)", ResponseType.PASS_FAIL_NA),
        ChecklistItem(353, "Restore communication", ResponseType.YES_NO_NA),
        ChecklistItem(354, "Alert clears at SCADA", ResponseType.PASS_FAIL_NA),
        ChecklistItem(355, "Simulate loss of communication between CRAH units", ResponseType.YES_NO_NA),
        ChecklistItem(356, "CRAH units continue to operate independently", ResponseType.PASS_FAIL_NA),
        ChecklistItem(357, "Alert is generated at SCADA", ResponseType.PASS_FAIL_NA),
        ChecklistItem(358, "Restore communication between units", ResponseType.YES_NO_NA),
        ChecklistItem(359, "Alert clears at SCADA", ResponseType.PASS_FAIL_NA),
        ChecklistItem(360, "Normal coordinated operation resumes", ResponseType.PASS_FAIL_NA),
        ChecklistItem(361, "BMS status is correct", ResponseType.PASS_FAIL_NA),
    ]
    section.items = items
    return section


def create_crah_completion_section() -> ChecklistSection:
    """Create test completion section."""
    section = ChecklistSection(name="XX. Test Completion")
    items = [
        ChecklistItem(400, "All sections have been completed satisfactorily", ResponseType.PASS_FAIL_NA),
        ChecklistItem(401, "All alerts and alarms have been cleared", ResponseType.PASS_FAIL_NA),
        ChecklistItem(402, "All manual overrides have been released", ResponseType.PASS_FAIL_NA),
        ChecklistItem(403, "All setpoints returned to design values", ResponseType.PASS_FAIL_NA),
        ChecklistItem(404, "System is operating normally", ResponseType.PASS_FAIL_NA),
        ChecklistItem(405, "All non-conformances have been documented", ResponseType.PASS_FAIL_NA),
        ChecklistItem(406, "Commissioning Authority Signature", ResponseType.TEXT),
        ChecklistItem(407, "Completion Date", ResponseType.DATE),
        ChecklistItem(408, "Comments/Notes", ResponseType.TEXT),
    ]
    section.items = items
    return section


def create_l3l4_crah_fpt_template(setpoints: list[dict] = None) -> CRAHTemplate:
    """
    Create a complete L3/L4 CRAH Functional Performance Test template.

    This template is based on the actual BIM360 ACC form structure from
    238123_L3L4_CRAH Unit_FunctionalPerformanceTest.
    """
    template = CRAHTemplate(
        template_id="L3L4_CRAH_FPT",
        display_name="L3L4 CRAH Unit Functional Performance Test",
        level="L3L4",
        equipment_type="CRAH",
        variant="KND"
    )

    template.sections = [
        create_crah_header_section(),
        create_crah_prerequisites_section(),
        create_crah_software_versions_section(),
        create_crah_visual_inspection_section(),
        create_crah_graphics_review_section(),
        create_crah_setpoint_verification_section(setpoints),
        create_crah_normal_operation_section(),
        create_crah_cooling_valve_test_section(),
        create_crah_fan_array_test_section(),
        create_crah_temperature_sensor_alert_section(),
        create_crah_loss_of_power_section(),
        create_crah_water_detection_section(),
        create_crah_phase_failure_section(),
        create_crah_freeze_protection_section(),
        create_crah_utility_loss_section(),
        create_crah_communication_loss_section(),
        create_crah_completion_section(),
    ]

    return template

