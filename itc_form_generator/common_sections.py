"""Common Sections Module - Based on real BIM360/ACC form data.

This module contains standard section definitions extracted from
the idc_acc_form_responses_datamart Hive table.

Section usage counts from production data (as of 2026-03):
- Point to Point Continued: 3,732,772 uses
- L2 - Site Arrival Inspection: 1,022,134 uses
- L2 - Electrical Installation Verification: 835,902 uses
- Signatures: 713,071 uses
- General: 586,802 uses
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SectionCategory(Enum):
    """Section categories based on commissioning phases."""
    PREREQUISITES = "Prerequisites"
    DOCUMENTATION = "Documentation"
    INSTALLATION = "Installation"
    VERIFICATION = "Verification"
    ELECTRICAL = "Electrical"
    CONTROLS = "Controls/BMS"
    TESTING = "Testing"
    FUNCTIONAL = "Functional"
    SIGNATURES = "Signatures"


@dataclass
class StandardCheckItem:
    """Standard check item from production forms."""
    description: str
    acceptance_criteria: str = "Pass"
    response_type: str = "choice"  # choice, text, number, toggle
    priority: str = "Medium"


@dataclass
class StandardSection:
    """Standard section from production forms."""
    name: str
    display_name: str
    category: SectionCategory
    display_order: int
    items: list = field(default_factory=list)
    usage_count: int = 0


# =============================================================================
# STANDARD SECTIONS FROM PRODUCTION DATA
# =============================================================================

PREREQUISITES_SECTION = StandardSection(
    name="Prerequisites",
    display_name="Prerequisites",
    category=SectionCategory.PREREQUISITES,
    display_order=1,
    usage_count=106614,
    items=[
        StandardCheckItem("Verify all prerequisite work completed", "Prerequisites met"),
        StandardCheckItem("Confirm equipment energization status", "Status confirmed"),
        StandardCheckItem("Verify safety procedures in place", "Safety procedures followed"),
        StandardCheckItem("Confirm test equipment available and calibrated", "Equipment ready"),
        StandardCheckItem("Review previous test results if applicable", "Results reviewed"),
    ]
)

DOCUMENTATION_SECTION = StandardSection(
    name="Documentation Verification",
    display_name="Documentation Verification",
    category=SectionCategory.DOCUMENTATION,
    display_order=2,
    usage_count=175375,
    items=[
        StandardCheckItem("Verify design drawings available", "Drawings available"),
        StandardCheckItem("Confirm specifications available", "Specs available"),
        StandardCheckItem("Verify O&M manuals available", "O&M manuals available"),
        StandardCheckItem("Confirm submittal documents approved", "Submittals approved"),
        StandardCheckItem("Verify TAB report available (if applicable)", "TAB report available"),
    ]
)

SAI_SECTION = StandardSection(
    name="L2 - Site Arrival Inspection (SAI)",
    display_name="Site Arrival Inspection (SAI)",
    category=SectionCategory.INSTALLATION,
    display_order=3,
    usage_count=1022134,
    items=[
        StandardCheckItem("Was the equipment covered, secured, and protected appropriately to avoid possible weather and shipping damage?", "Yes"),
        StandardCheckItem("Were the weather conditions DRY upon receiving? (If 'NO' or other extreme conditions please describe in comments)", "Yes"),
        StandardCheckItem("List weather conditions upon arrival.", "Conditions recorded", response_type="text"),
        StandardCheckItem("Is the equipment clean, and free of all loose debris, material, and parts?", "Yes"),
        StandardCheckItem("Confirm equipment is visually inspected for damage, and if damage is present, an issue has already been recorded.", "Confirmed"),
        StandardCheckItem("if OFCI equipment, is packing slip attached to the asset per 01 92 20 specifications", "Yes"),
        StandardCheckItem("Has Bill of Lading been uploaded to ACC?", "Yes"),
        StandardCheckItem("Date Received", "Date recorded", response_type="text"),
        StandardCheckItem("Received By:", "Name recorded", response_type="text"),
        StandardCheckItem("Have photos been taken prior to covering and securing equipment?", "Yes"),
        StandardCheckItem("Has the Manufacturer provided the required QA/QC Level 1 (Factory Test) Documentation? (Collect and indicate where filed)", "Yes"),
    ]
)

GENERAL_SECTION = StandardSection(
    name="General",
    display_name="General Information",
    category=SectionCategory.PREREQUISITES,
    display_order=1,
    usage_count=586802,
    items=[
        StandardCheckItem("Equipment Tag:", "Tag recorded", response_type="text"),
        StandardCheckItem("Location", "Location recorded", response_type="text"),
        StandardCheckItem("Equipment Manufacturer:", "Manufacturer recorded", response_type="text"),
        StandardCheckItem("Model Number:", "Model recorded", response_type="text"),
        StandardCheckItem("Serial Number:", "Serial recorded", response_type="text"),
        StandardCheckItem("NEMA Rating:", "Rating recorded", response_type="text"),
        StandardCheckItem("Voltage Rating:", "Voltage recorded", response_type="text"),
        StandardCheckItem("Current Rating:", "Current recorded", response_type="text"),
        StandardCheckItem("kAIC Rating:", "kAIC recorded", response_type="text"),
        StandardCheckItem("Phase / Wire Rating: (e.g.; 3ph,4wire)", "Rating recorded", response_type="text"),
        StandardCheckItem("Asset Tag Number", "Asset tag recorded", response_type="text"),
    ]
)

ELECTRICAL_INSTALLATION_SECTION = StandardSection(
    name="L2 - Electrical Installation Verification",
    display_name="Electrical Installation Verification",
    category=SectionCategory.ELECTRICAL,
    display_order=4,
    usage_count=835902,
    items=[
        StandardCheckItem("Verify electrical connections complete", "Connections complete"),
        StandardCheckItem("Confirm proper wire sizing", "Wire sizing correct"),
        StandardCheckItem("Verify grounding complete", "Grounding complete"),
        StandardCheckItem("Check conduit installation", "Conduit correct"),
        StandardCheckItem("Verify wire labeling", "Labels correct"),
    ]
)

WIRE_TERMINATION_SECTION = StandardSection(
    name="EIV: WIRE & TERMINATION VERIFICATION",
    display_name="Wire & Termination Verification",
    category=SectionCategory.ELECTRICAL,
    display_order=5,
    usage_count=129696,
    items=[
        StandardCheckItem("Are all the wires formed neatly and secure, including being kept clear of all sharp edges and panel cover screws?", "Yes"),
        StandardCheckItem("Is the correct cabling installed for each system?", "Yes"),
        StandardCheckItem("Are the cables properly labeled per the project requirements?", "Yes"),
        StandardCheckItem("Verify wire conductors are terminated to correct terminals at the panel per approved shop drawings.", "Yes"),
        StandardCheckItem("Verify each wire conductor termination is tight by performing pull test.", "Yes"),
        StandardCheckItem("Verify wire copper strands are grouped and not splayed at terminals.", "Yes"),
        StandardCheckItem("Verify no butt splice, wire nuts, or other splicing elements are in line with the device to PLC panel cabling.", "Yes"),
        StandardCheckItem("Verify wire ferrules (correct size) are used if the panel has terminal blocks with push fit terminals.", "Yes"),
        StandardCheckItem("Verify cable shield is terminated on the panel side only.", "Yes"),
        StandardCheckItem("Confirm feeder insulation has been cut back so that copper is visible between insulation and lug.", "Yes"),
        StandardCheckItem("Confirm lugs have proper number of crimps per manufacturer recommendations.", "Yes"),
    ]
)

CONDUIT_SECTION = StandardSection(
    name="EIV: CONDUIT INSTALLATION VERIFICATION",
    display_name="Conduit Installation Verification",
    category=SectionCategory.ELECTRICAL,
    display_order=6,
    usage_count=94693,
    items=[
        StandardCheckItem("Have all required conduits been installed for these systems?", "Yes"),
        StandardCheckItem("Do all conduits meet the conduit wire fill requirements per spec and NEC?", "Yes"),
        StandardCheckItem("Are all conduits sealed per design and spec requirements?", "Yes"),
        StandardCheckItem("Are all conduit connector set screws or compression fittings and lock rings tight?", "Yes"),
        StandardCheckItem("Are all spec and NEC required bond bushings installed?", "Yes"),
        StandardCheckItem("Are all bond bushing set screws and lug screws tight?", "Yes"),
        StandardCheckItem("Are all specified conduit connectors installed per spec and NEC requirements?", "Yes"),
        StandardCheckItem("Are all conduit connectors in EC scope installed per spec and NEC requirements using required insulated throat connectors and bushings?", "Yes"),
        StandardCheckItem("Verify conduits and cable trays are properly routed in accordance with approved site model.", "Yes"),
        StandardCheckItem("Verify conduits and cable trays are properly supported per owner furnished requirements.", "Yes"),
        StandardCheckItem("Confirm all conduit are properly installed with anti-rub bushing installed.", "Yes"),
    ]
)

EQUIPMENT_ENERGIZATION_SECTION = StandardSection(
    name="Equipment Energization (Source 1 Voltage)",
    display_name="Equipment Energization",
    category=SectionCategory.ELECTRICAL,
    display_order=7,
    usage_count=356088,
    items=[
        StandardCheckItem("Review Lockout Tagout of this equipment from all sources. Apply lock to all connected sources or group lockout.", "LOTO complete"),
        StandardCheckItem("Has visual inspection been preformed of electrical/mechanical conditions and verify no tools or materials are in equipment to be energized?", "Yes"),
        StandardCheckItem("Has point to point been verified and is correct per the one-line?", "Yes"),
        StandardCheckItem("Has TILT meter been used to verify no electrical shorts or faults?", "Yes"),
        StandardCheckItem("Have all covers been closed and securely fastened?", "Yes"),
        StandardCheckItem("Multi Meter calibration date", "Date recorded", response_type="text"),
        StandardCheckItem("Multi Meter serial number", "Serial recorded", response_type="text"),
        StandardCheckItem("Phase Rotation Meter serial number", "Serial recorded", response_type="text"),
        StandardCheckItem("Phase A to Phase B", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase B to Phase C", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase A to Phase C", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase A to Neutral", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase B to Neutral", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase C to Neutral", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase A to Ground", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase B to Ground", "Voltage recorded", response_type="number"),
        StandardCheckItem("Phase C to Ground", "Voltage recorded", response_type="number"),
        StandardCheckItem("Record S1 rotation.", "Rotation recorded", response_type="text"),
        StandardCheckItem("Has visual inspection been performed to insure all tools have been removed and covers have been reinstalled.", "Yes"),
        StandardCheckItem("Have barricades been removed from area and signage placed on equipment.", "Yes"),
    ]
)

PRE_ENERGIZATION_SECTION = StandardSection(
    name="Pre-Energization",
    display_name="Pre-Energization Verifications",
    category=SectionCategory.ELECTRICAL,
    display_order=6,
    usage_count=43214,
    items=[
        StandardCheckItem("Verify all connections torqued", "Torque complete"),
        StandardCheckItem("Check for debris/foreign objects in enclosure", "Enclosure clean"),
        StandardCheckItem("Verify all breakers/disconnects in OFF position", "Breakers OFF"),
        StandardCheckItem("Confirm insulation resistance testing complete", "IR testing complete"),
        StandardCheckItem("Verify safety barriers in place", "Barriers in place"),
        StandardCheckItem("Confirm LOTO procedures followed", "LOTO complete"),
    ]
)

NETA_TESTING_SECTION = StandardSection(
    name="L2 - NETA Testing",
    display_name="NETA Testing",
    category=SectionCategory.TESTING,
    display_order=8,
    usage_count=145980,
    items=[
        StandardCheckItem("Perform insulation resistance test", "IR acceptable", response_type="number"),
        StandardCheckItem("Perform contact resistance test", "Contact resistance acceptable", response_type="number"),
        StandardCheckItem("Verify protective relay settings", "Settings correct"),
        StandardCheckItem("Perform trip testing", "Trip functions correct"),
        StandardCheckItem("Record test results", "Results recorded"),
    ]
)

TORQUE_REPORT_SECTION = StandardSection(
    name="L2 - Electrical Torque Report",
    display_name="Electrical Torque Report",
    category=SectionCategory.ELECTRICAL,
    display_order=9,
    usage_count=61424,
    items=[
        StandardCheckItem("Has all required Torque documentation been reviewed for accuracy and completeness?", "Yes"),
        StandardCheckItem("Has all Torque documentation been uploaded to ACC?", "Yes"),
        StandardCheckItem("Confirm electrical contractor torque checklists are reviewed and loaded into Build.", "Yes"),
        StandardCheckItem("GF / Foreman responsible for install:", "Name recorded", response_type="text"),
        StandardCheckItem("Foreman Signature", "Signed", response_type="text"),
    ]
)

EPMS_BMS_SECTION = StandardSection(
    name="II. EPMS - Point Config, Graphic, Trend and Alarm Verification",
    display_name="EPMS/BMS Point Verification",
    category=SectionCategory.CONTROLS,
    display_order=10,
    usage_count=328190,
    items=[
        StandardCheckItem("Confirm the modbus address and scaling are properly configured per design deliverables", "Configured"),
        StandardCheckItem("BMS status is correct", "Status correct"),
        StandardCheckItem("Alarm is initiated at the EPMS graphic as required and matches points list (alarm name, priority, alert timer, etc.)", "Alarm correct"),
        StandardCheckItem("Alert generated at the Alert graphic screen and Priority matches Points List", "Alert correct"),
        StandardCheckItem("Alert Verbiage and Time Delay are correct per APPROVED Points List", "Correct"),
        StandardCheckItem("Verify Indication on EPMS", "Indication verified"),
        StandardCheckItem("Verify no 'Forces' exist in the PLC for the device being tested.", "No forces"),
        StandardCheckItem("BMS/EPMS version number", "Version recorded", response_type="text"),
        StandardCheckItem("PLC Firmware version number/program", "Version recorded", response_type="text"),
        StandardCheckItem("HMI firmware version/program", "Version recorded", response_type="text"),
        StandardCheckItem("PQM firmware version", "Version recorded", response_type="text"),
        StandardCheckItem("Client Global Settings (record rev)", "Revision recorded", response_type="text"),
    ]
)

BMS_INSTALLATION_SECTION = StandardSection(
    name="BMS Installation Verification",
    display_name="BMS Installation Verification",
    category=SectionCategory.CONTROLS,
    display_order=11,
    usage_count=81671,
    items=[
        StandardCheckItem("Verify controller installed correctly", "Controller installed"),
        StandardCheckItem("Confirm network connection", "Network connected"),
        StandardCheckItem("Verify communication to supervisory", "Communication verified"),
        StandardCheckItem("Check sensor wiring", "Sensor wiring correct"),
        StandardCheckItem("Verify actuator wiring", "Actuator wiring correct"),
    ]
)

POINT_TO_POINT_SECTION = StandardSection(
    name="Point to Point",
    display_name="Point to Point Checkout",
    category=SectionCategory.CONTROLS,
    display_order=12,
    usage_count=3732772,
    items=[
        StandardCheckItem("Verify no alerts are active and all alerts are acknowledged before starting PTP test.", "Verified"),
        StandardCheckItem("Verify no active alarms are associated with this device.", "No active alarms"),
        StandardCheckItem("Tagname", "Tagname recorded", response_type="text"),
        StandardCheckItem("Verify From Field Device -> 0% Test", "0% verified", response_type="number"),
        StandardCheckItem("Verify From Field Device -> 25% Test", "25% verified", response_type="number"),
        StandardCheckItem("Verify From Field Device -> 50% Test", "50% verified", response_type="number"),
        StandardCheckItem("Verify From Field Device -> 75% Test", "75% verified", response_type="number"),
        StandardCheckItem("Verify From Field Device -> 100% Test", "100% verified", response_type="number"),
        StandardCheckItem("Bad I/O Test (Verify by Power Disconnect and Signal Disconnect)", "Bad I/O verified"),
        StandardCheckItem("Signal Injection From SCADA/Client -> De-Energized Test", "De-energized verified"),
        StandardCheckItem("Signal Injection From SCADA/Client -> Energized Test", "Energized verified"),
        StandardCheckItem("Verify continuity test has been completed satisfactorily on the conductors between device and panel.", "Continuity verified"),
        StandardCheckItem("Record calibration equipment's serial number.", "Serial recorded", response_type="text"),
    ]
)

DEVICE_SIDE_SECTION = StandardSection(
    name="Device Side Installation/Wiring",
    display_name="Device Side Installation/Wiring",
    category=SectionCategory.CONTROLS,
    display_order=13,
    usage_count=217599,
    items=[
        StandardCheckItem("Verify the device aluminum metal tags are present and adhere to the guidelines found in Meta Owner requirements", "Tags present"),
        StandardCheckItem("Verify the Meta approved device asset tag is present and adheres to the guidelines found in Meta Owner requirements", "Asset tag present"),
        StandardCheckItem("Record device asset tag number.", "Tag recorded", response_type="text"),
        StandardCheckItem("Record point description as shown on line 2 of the aluminum metal tag.", "Description recorded", response_type="text"),
        StandardCheckItem("Verify the device sensor cables have been neatly routed to the appropriate junction box, cable tray, or basket tray.", "Routing verified"),
        StandardCheckItem("Verify hardwire terminations meet requirements outlined in Meta Owner requirements and approved shop drawings.", "Terminations verified"),
        StandardCheckItem("Verify device cable or wire conductors are labeled and adhere to the guidelines found in Meta Owner requirements. All labels are facing the same direction and legible.", "Labels verified"),
        StandardCheckItem("Verify correct cables, per approved shop drawings, have been pulled between device and panel.", "Cables verified"),
        StandardCheckItem("Verify shield on signal cable to panel is cut flush with jacket and dressed per specification.", "Shield verified"),
        StandardCheckItem("Verify junction box is clean and free of any defects, debris, or damage.", "Junction box clean"),
        StandardCheckItem("Verify junction box screws have been installed.", "Screws installed"),
    ]
)

PANEL_SIDE_SECTION = StandardSection(
    name="Panel Side Installation/Wiring",
    display_name="Panel Side Installation/Wiring",
    category=SectionCategory.CONTROLS,
    display_order=14,
    usage_count=110290,
    items=[
        StandardCheckItem("Verify terminations at panel", "Panel terminations correct"),
        StandardCheckItem("Check wire routing in panel", "Routing correct"),
        StandardCheckItem("Verify fuse/breaker sizing", "Sizing correct"),
        StandardCheckItem("Confirm shield grounding", "Shield grounded"),
    ]
)

VISUAL_INSPECTION_SECTION = StandardSection(
    name="Visual Inspection",
    display_name="Visual Inspection",
    category=SectionCategory.VERIFICATION,
    display_order=15,
    usage_count=75596,
    items=[
        StandardCheckItem("Inspect for physical damage", "No damage"),
        StandardCheckItem("Verify nameplate legible", "Nameplate legible"),
        StandardCheckItem("Check for proper clearances", "Clearances adequate"),
        StandardCheckItem("Verify ventilation adequate", "Ventilation adequate"),
        StandardCheckItem("Inspect for leaks", "No leaks"),
    ]
)

LABELING_SECTION = StandardSection(
    name="Labeling and Identification Data",
    display_name="Labeling and Identification",
    category=SectionCategory.VERIFICATION,
    display_order=16,
    usage_count=115615,
    items=[
        StandardCheckItem("Are the breakers properly labeled per project design and specification requirements with the correct project nomenclature?", "Yes"),
        StandardCheckItem("Is phenolic label provided by vendor? If so, is phenolic label installed and correct per specifications?", "Yes"),
        StandardCheckItem("Is the asset tag present and in correct location on equipment?", "Yes"),
        StandardCheckItem("Have asset tag fields been populated?", "Yes"),
        StandardCheckItem("Has asset tag been installed?", "Yes"),
        StandardCheckItem("Permanent phenolic labels are applied and accurate", "Yes"),
        StandardCheckItem("Verify arc flash sticker is affixed in all required locations with proper voltage and equipment noted per the approved arc flash study.", "Yes"),
        StandardCheckItem("Verify Asset Tags, aluminum metal tags, and phenolic tags (when applicable) are present and adhere to the guidelines found Meta Owner requirements.", "Yes"),
        StandardCheckItem("Confirm correctly colored ID label is installed and indicates the correct power source(s). Ensure naming is aligned with contract documents and BIM.", "Yes"),
        StandardCheckItem("Confirm that labeling is installed for all breakers and applicable devices including panel schedule.", "Yes"),
    ]
)

POST_INSTALLATION_SECTION = StandardSection(
    name="Post Installation Check",
    display_name="Post Installation Check",
    category=SectionCategory.VERIFICATION,
    display_order=17,
    usage_count=145954,
    items=[
        StandardCheckItem("Verify installation complete per scope", "Installation complete"),
        StandardCheckItem("Confirm all covers/panels secured", "Covers secured"),
        StandardCheckItem("Check for debris removal", "Debris removed"),
        StandardCheckItem("Verify area clean and safe", "Area clean"),
    ]
)

FUNCTIONAL_SECTION = StandardSection(
    name="Functional and Performance Acceptance",
    display_name="Functional Performance Test",
    category=SectionCategory.FUNCTIONAL,
    display_order=18,
    usage_count=99885,
    items=[
        StandardCheckItem("Test normal operation", "Normal operation verified"),
        StandardCheckItem("Test all operating modes", "All modes function"),
        StandardCheckItem("Verify setpoint response", "Setpoint response correct"),
        StandardCheckItem("Test alarm functions", "Alarms function"),
        StandardCheckItem("Verify interlock operations", "Interlocks function"),
        StandardCheckItem("Test emergency shutdown", "E-stop functions", priority="Critical"),
    ]
)

POST_COMMISSIONING_SECTION = StandardSection(
    name="Post Commissioning Check",
    display_name="Post Commissioning Check",
    category=SectionCategory.VERIFICATION,
    display_order=19,
    usage_count=112836,
    items=[
        StandardCheckItem("Verify all tests complete", "Tests complete"),
        StandardCheckItem("Confirm all deficiencies resolved", "Deficiencies resolved"),
        StandardCheckItem("Verify documentation updated", "Documentation updated"),
        StandardCheckItem("Confirm system ready for turnover", "Ready for turnover"),
    ]
)

SIGNATURES_SECTION = StandardSection(
    name="Signatures",
    display_name="Signatures",
    category=SectionCategory.SIGNATURES,
    display_order=99,
    usage_count=713071,
    items=[
        StandardCheckItem("Name of individual verifying CEV:", "Name recorded", response_type="text"),
        StandardCheckItem("QA/Cx Inspector:", "Name recorded", response_type="text"),
        StandardCheckItem("QAQC Authority Name", "Name recorded", response_type="text"),
        StandardCheckItem("Inspection Attendees (List Company Names)", "Attendees recorded", response_type="text"),
        StandardCheckItem("Date of Inspection", "Date recorded", response_type="text"),
        StandardCheckItem("Date:", "Date recorded", response_type="text"),
        StandardCheckItem("Signature", "Signed", response_type="text"),
        StandardCheckItem("QA/QC Inspection By:", "Name recorded", response_type="text"),
        StandardCheckItem("General Contractor", "Name recorded", response_type="text"),
        StandardCheckItem("Installing Contractor", "Name recorded", response_type="text"),
        StandardCheckItem("Electrical Contractor", "Name recorded", response_type="text"),
        StandardCheckItem("Commissioning Authority (Name)", "Name recorded", response_type="text"),
        StandardCheckItem("All CEV sections have been reviewed for completeness?", "Yes"),
    ]
)

# =============================================================================
# SECTION REGISTRY BY CATEGORY
# =============================================================================

STANDARD_SECTIONS = {
    # Prerequisites/General
    "Prerequisites": PREREQUISITES_SECTION,
    "General": GENERAL_SECTION,
    "Documentation Verification": DOCUMENTATION_SECTION,

    # Installation
    "Site Arrival Inspection": SAI_SECTION,
    "L2 - Site Arrival Inspection (SAI)": SAI_SECTION,
    "Post Installation Check": POST_INSTALLATION_SECTION,

    # Electrical
    "L2 - Electrical Installation Verification": ELECTRICAL_INSTALLATION_SECTION,
    "Wire & Termination Verification": WIRE_TERMINATION_SECTION,
    "EIV: WIRE & TERMINATION VERIFICATION": WIRE_TERMINATION_SECTION,
    "Conduit Installation Verification": CONDUIT_SECTION,
    "EIV: CONDUIT INSTALLATION VERIFICATION": CONDUIT_SECTION,
    "Equipment Energization": EQUIPMENT_ENERGIZATION_SECTION,
    "Pre-Energization": PRE_ENERGIZATION_SECTION,
    "L2 - NETA Testing": NETA_TESTING_SECTION,
    "Electrical Torque Report": TORQUE_REPORT_SECTION,
    "L2 - Electrical Torque Report": TORQUE_REPORT_SECTION,

    # Controls/BMS
    "EPMS/BMS Point Verification": EPMS_BMS_SECTION,
    "BMS Installation Verification": BMS_INSTALLATION_SECTION,
    "Point to Point": POINT_TO_POINT_SECTION,
    "Device Side Installation/Wiring": DEVICE_SIDE_SECTION,
    "Panel Side Installation/Wiring": PANEL_SIDE_SECTION,

    # Verification
    "Visual Inspection": VISUAL_INSPECTION_SECTION,
    "Labeling and Identification": LABELING_SECTION,

    # Functional/Testing
    "Functional Performance Test": FUNCTIONAL_SECTION,
    "Post Commissioning Check": POST_COMMISSIONING_SECTION,

    # Signatures
    "Signatures": SIGNATURES_SECTION,
}


def get_section(name: str) -> Optional[StandardSection]:
    """Get a standard section by name."""
    return STANDARD_SECTIONS.get(name)


def get_sections_by_category(category: SectionCategory) -> list:
    """Get all sections in a category."""
    return [s for s in STANDARD_SECTIONS.values() if s.category == category]


def get_installation_sections() -> list:
    """Get standard sections for installation forms."""
    return [
        GENERAL_SECTION,
        SAI_SECTION,
        DOCUMENTATION_SECTION,
        ELECTRICAL_INSTALLATION_SECTION,
        WIRE_TERMINATION_SECTION,
        LABELING_SECTION,
        POST_INSTALLATION_SECTION,
        SIGNATURES_SECTION,
    ]


def get_cev_sections() -> list:
    """Get standard sections for CEV (Commissioning & Equipment Verification) forms."""
    return [
        PREREQUISITES_SECTION,
        DOCUMENTATION_SECTION,
        VISUAL_INSPECTION_SECTION,
        PRE_ENERGIZATION_SECTION,
        EQUIPMENT_ENERGIZATION_SECTION,
        TORQUE_REPORT_SECTION,
        BMS_INSTALLATION_SECTION,
        FUNCTIONAL_SECTION,
        POST_COMMISSIONING_SECTION,
        SIGNATURES_SECTION,
    ]


def get_fpt_sections() -> list:
    """Get standard sections for FPT (Functional Performance Test) forms."""
    return [
        PREREQUISITES_SECTION,
        DOCUMENTATION_SECTION,
        VISUAL_INSPECTION_SECTION,
        FUNCTIONAL_SECTION,
        EPMS_BMS_SECTION,
        POST_COMMISSIONING_SECTION,
        SIGNATURES_SECTION,
    ]


def get_point_to_point_sections() -> list:
    """Get standard sections for Point-to-Point checkout forms."""
    return [
        PREREQUISITES_SECTION,
        DEVICE_SIDE_SECTION,
        PANEL_SIDE_SECTION,
        POINT_TO_POINT_SECTION,
        BMS_INSTALLATION_SECTION,
        SIGNATURES_SECTION,
    ]

