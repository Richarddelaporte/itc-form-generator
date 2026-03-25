"""ATS (Automatic Transfer Switch) Templates - Based on actual BIM360/ACC form data.

This module contains ATS-specific templates extracted from the
idc_acc_form_responses_datamart Hive table (Query 5 results).

ATS forms follow a structured naming convention:
    {SpecCode}_{Level}_{EquipmentType}_{Area} - ATS - {Identifier}_{Variant} - {Rev}_{Integration}

Example: 260627_L3_Automatic Transfer Switch_ERA - ATS - FCA-3_KND1_Rev0_CombinedBMS

Equipment Categories (from query data):
    - FCA: Fire Control Area ATS
    - CDU: Coolant Distribution Unit ATS
    - House: House ATS
    - MSG: Medium Switchgear ATS
    - HMD: Harmonic Mitigation Device ATS
    - mCUP: Modular Critical Power Unit ATS
    - FirePump: Fire Pump ATS
    - GEN: Generator ATS
    - NLH: No-Load House ATS
    - Admin: Administrative ATS

Equipment Variants (from query data):
    - KND1: High frequency (204-881 per instance) - Primary distribution
    - TTX1/TTX2: Transfer/transformer (7-122)
    - UCO1/UCO2: UPS/critical power (97-102)
    - LCO1/LCO2: Line circuit text entry (102)
    - RMN1: Remote monitoring (24-68)
    - MCA1/MCA2: Motor control (14-102)
    - MAL1/MAL2: Main alignment (6-92)
    - SNB5/SNB6: Specialized network bus (90-102)
    - GTN5/GTN6: Ground/transfer network (29-194)
    - RIN: Ring interconnect (1-102)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ResponseType(Enum):
    """Response types from ACC form data."""
    TOGGLE = "toggle"
    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"
    DATE = "date"
    SIGNATURE = "signature"


class PresetType(Enum):
    """Common preset configurations from ACC forms."""
    YES_NO_NA = "No/Yes/NA"
    PASS_FAIL_NA = "Fail/Pass/NA"
    PASS_FAIL = "Pass/Fail"
    NONE = ""


@dataclass
class ATSCheckItem:
    """ATS check item with response configuration."""
    description: str
    presets: PresetType = PresetType.YES_NO_NA
    response_type: ResponseType = ResponseType.TOGGLE
    acceptance_criteria: str = "Pass"
    priority: str = "Medium"
    frequency: int = 0


@dataclass
class ATSSection:
    """ATS form section with ordered check items."""
    name: str
    display_name: str
    section_order: int
    items: List[ATSCheckItem] = field(default_factory=list)
    usage_count: int = 0


@dataclass
class ATSTemplate:
    """Complete ATS form template."""
    template_id: str
    display_name: str
    level: str  # L2C, L3, L4, L4C
    equipment_type: str  # ATS
    category: str  # FCA, CDU, House, MSG, etc.
    variant: str  # KND1, TTX1, etc.
    sections: List[ATSSection] = field(default_factory=list)
    frequency: int = 0


# =============================================================================
# ATS SECTIONS FROM PRODUCTION DATA (Query 5 Results)
# =============================================================================

# Safety Procedure Section (most common check item)
ATS_SAFETY_PROCEDURE = ATSSection(
    name="Safety Procedure Acknowledgment",
    display_name="Safety Procedure Acknowledgment",
    section_order=1,
    usage_count=881,
    items=[
        ATSCheckItem(
            "While Performing This Procedure: "
            "**Items that do not apply shall be noted with a reason in the comment box of the associated item. "
            "**Contractors and Vendors are responsible for the safety of equipment and personnel while performing this procedure.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=881
        ),
    ]
)

# Equipment Identification Section
ATS_EQUIPMENT_ID = ATSSection(
    name="Equipment Identification",
    display_name="Equipment Identification",
    section_order=1,
    usage_count=81123,
    items=[
        ATSCheckItem("Equipment Designation", PresetType.NONE, ResponseType.TEXT, frequency=81123),
        ATSCheckItem("Project", PresetType.NONE, ResponseType.TEXT, frequency=102),
        ATSCheckItem("Location", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Asset Tag Number", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Model number or name", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Manufacturer or Vendor (make)", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Serial Number", PresetType.NONE, ResponseType.TEXT),
    ]
)

# Site Arrival Section
ATS_SITE_ARRIVAL = ATSSection(
    name="Electrical Equipment Site Arrival - ATS",
    display_name="Site Arrival Inspection",
    section_order=2,
    usage_count=612,
    items=[
        ATSCheckItem("Date Received:", PresetType.NONE, ResponseType.DATE, frequency=612),
        ATSCheckItem("Time Received:", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Received By:", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Shipping Carrier:", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Shipping condition satisfactory?", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Equipment matches packing slip?", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Visual inspection complete - no visible damage?", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Bill of Lading uploaded to ACC?", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Photos taken and uploaded?", PresetType.YES_NO_NA, ResponseType.TOGGLE),
    ]
)

# Pre-Energization Section (L2C forms)
ATS_PRE_ENERGIZATION = ATSSection(
    name="L2C - ELEC - ATS Pre-energization - Rev0",
    display_name="Pre-Energization Verification",
    section_order=2,
    usage_count=102,
    items=[
        ATSCheckItem("Date", PresetType.NONE, ResponseType.DATE, frequency=102),
        ATSCheckItem("QAQC Authority Name:", PresetType.NONE, ResponseType.TEXT),
        ATSCheckItem("Verify all prerequisite inspections completed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("LOTO procedures completed and documented", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("All torque checklists completed and uploaded", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("NETA testing documentation complete", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Visual inspection of all connections complete", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("No debris or foreign objects in enclosure", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("All covers and panels secured", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Safety barriers in place", PresetType.YES_NO_NA, ResponseType.TOGGLE),
    ]
)

# Functional Test Section (from 7.0 Auxiliary Equipment Functional Tests)
ATS_FUNCTIONAL_TEST = ATSSection(
    name="7.0 Auxiliary Equipment Functional Tests - Automatic Transfer Switch",
    display_name="ATS Functional Tests",
    section_order=7,
    usage_count=306,
    items=[
        ATSCheckItem(
            "ATS test complete, successful, and fully documented",
            PresetType.PASS_FAIL_NA,
            ResponseType.TOGGLE,
            frequency=306
        ),
        ATSCheckItem("Verify ATS source indication is correct", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify automatic transfer sequence operates correctly", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify retransfer sequence operates correctly", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify time delay settings are correct per design", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify voltage/frequency sensing is correct", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify manual transfer operation", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
        ATSCheckItem("Verify all alarms/status indications function correctly", PresetType.PASS_FAIL_NA, ResponseType.TOGGLE),
    ]
)

# BMS/EPMS Verification Section
ATS_BMS_VERIFICATION = ATSSection(
    name="BMS/EPMS Point Verification",
    display_name="BMS/EPMS Point Verification",
    section_order=8,
    usage_count=102,
    items=[
        ATSCheckItem("ATS status is correct at BMS/EPMS", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Source 1 available indication correct", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Source 2 available indication correct", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Transfer position indication correct", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("All alarms correctly configured per points list", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Alert time delays correct per points list", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Email notifications configured (Priority 1 alerts)", PresetType.YES_NO_NA, ResponseType.TOGGLE),
    ]
)

# Documentation Verification Section
ATS_DOCUMENTATION = ATSSection(
    name="Documentation Verification",
    display_name="Documentation Verification",
    section_order=3,
    usage_count=102,
    items=[
        ATSCheckItem("Site arrival inspection completed and uploaded", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("NETA documentation reviewed with passing results", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Vendor/manufacturer pre-startup checklist reviewed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Electrical contractor torque checklists reviewed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Electrical contractor installation checklist completed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Cable testing documentation reviewed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("All equipment issues addressed and closed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
    ]
)

# End of Test Section
ATS_END_OF_TEST = ATSSection(
    name="End of Test",
    display_name="End of Test",
    section_order=99,
    usage_count=102,
    items=[
        ATSCheckItem("All test procedures completed successfully", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Equipment panels and covers in place and secured", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("All simulated variables restored at BMS", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Equipment placed in specified operating condition", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Test documentation complete and uploaded", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        ATSCheckItem("Operating Condition Notes:", PresetType.NONE, ResponseType.TEXT),
    ]
)


# =============================================================================
# ATS TEMPLATE GENERATORS
# =============================================================================

def get_ats_l3_bms_template(
    area: str = "ERA",
    identifier: str = "FCA-1",
    variant: str = "KND1"
) -> ATSTemplate:
    """Generate L3 ATS BMS Combined template.

    Args:
        area: Building/area code (ERA, ERB, ERC, ERD, ERN1-4, UPSA-D, etc.)
        identifier: Equipment identifier (FCA-1, CDU-1, H1, etc.)
        variant: Equipment variant (KND1, TTX1, UCO1, etc.)

    Returns:
        ATSTemplate configured for the specific equipment instance
    """
    template_id = f"260627_L3_Automatic Transfer Switch_{area} - ATS - {identifier}_{variant}_Rev0_CombinedBMS"

    # Determine category from identifier
    if identifier.startswith("FCA"):
        category = "FCA"
    elif identifier.startswith("CDU"):
        category = "CDU"
    elif identifier.startswith("H"):
        category = "House"
    else:
        category = "General"

    return ATSTemplate(
        template_id=template_id,
        display_name=f"L3 ATS {area}-{identifier} ({variant}) - Combined BMS",
        level="L3",
        equipment_type="ATS",
        category=category,
        variant=variant,
        sections=[
            ATS_SAFETY_PROCEDURE,
            ATS_DOCUMENTATION,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=102 if variant in ["LCO1", "LCO2"] else 204
    )


def get_ats_l4_fca_template() -> ATSTemplate:
    """Generate L4 ATS FCA Functional Performance Test template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - FCA - Rev B",
        display_name="L4 ATS FCA Commissioning",
        level="L4",
        equipment_type="ATS",
        category="FCA",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=15073
    )


def get_ats_l4_house_template() -> ATSTemplate:
    """Generate L4 ATS House Commissioning template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - House - Rev 0",
        display_name="L4 ATS House Commissioning",
        level="L4",
        equipment_type="ATS",
        category="House",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=1367
    )


def get_ats_l4_house_gen_template() -> ATSTemplate:
    """Generate L4 ATS House with Generator template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - House with Gen - Rev 0",
        display_name="L4 ATS House with Generator Commissioning",
        level="L4",
        equipment_type="ATS",
        category="House_Gen",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=536
    )


def get_ats_l4_msg_template() -> ATSTemplate:
    """Generate L4 ATS MSG (Medium Switchgear) template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - MSG - Rev 0",
        display_name="L4 ATS MSG Commissioning",
        level="L4",
        equipment_type="ATS",
        category="MSG",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=1438
    )


def get_ats_l4_msg_fpt_template() -> ATSTemplate:
    """Generate L4 ATS MSG FPT template (260627 variant)."""
    return ATSTemplate(
        template_id="260627_L4_AutomaticTransferSwitch(MSG)_FunctionalPerformanceTest_Rev0",
        display_name="L4 ATS MSG Functional Performance Test",
        level="L4",
        equipment_type="ATS",
        category="MSG",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=6224
    )


def get_ats_l4_hmd_template() -> ATSTemplate:
    """Generate L4 ATS HMD (Harmonic Mitigation Device) template."""
    return ATSTemplate(
        template_id="260627_L4_AutomaticTransferSwitch(HMD)_FunctionalPerformanceTest_Rev0",
        display_name="L4 ATS HMD Functional Performance Test",
        level="L4",
        equipment_type="ATS",
        category="HMD",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=3035
    )


def get_ats_l4_mcup_template() -> ATSTemplate:
    """Generate L4 ATS mCUP (Modular Critical Power Unit) template."""
    return ATSTemplate(
        template_id="260627_L4_AutomaticTransferSwitch(mCUP)_FunctionalPerformanceTest_Rev0",
        display_name="L4 ATS mCUP Functional Performance Test",
        level="L4",
        equipment_type="ATS",
        category="mCUP",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=1788
    )


def get_ats_l4_firepump_template() -> ATSTemplate:
    """Generate L4 ATS Fire Pump template."""
    return ATSTemplate(
        template_id="213113_L4_AutomaticTransferSwitch(FirePump)_FunctionalPerformanceTest_Rev0",
        display_name="L4 ATS Fire Pump Functional Performance Test",
        level="L4",
        equipment_type="ATS",
        category="FirePump",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_END_OF_TEST,
        ],
        frequency=1297
    )


def get_ats_l4_cdu_template() -> ATSTemplate:
    """Generate L4 ATS CDU Commissioning template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - CDU - Rev 0",
        display_name="L4 ATS CDU Commissioning",
        level="L4",
        equipment_type="ATS",
        category="CDU",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=182
    )


def get_ats_l4_admin_template() -> ATSTemplate:
    """Generate L4 ATS Admin Commissioning template."""
    return ATSTemplate(
        template_id="L4 - Cx - ELEC - ATS - Admin - Rev 0",
        display_name="L4 ATS Admin Commissioning",
        level="L4",
        equipment_type="ATS",
        category="Admin",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
            ATS_FUNCTIONAL_TEST,
            ATS_END_OF_TEST,
        ],
        frequency=208
    )


def get_ats_l4_nlh_template() -> ATSTemplate:
    """Generate L4C ATS NLH template."""
    return ATSTemplate(
        template_id="L4C - ELEC - ATS - NLH - Rev0",
        display_name="L4C ATS NLH Commissioning",
        level="L4C",
        equipment_type="ATS",
        category="NLH",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_END_OF_TEST,
        ],
        frequency=252
    )


def get_ats_l4_cable_house_template() -> ATSTemplate:
    """Generate L4 ATS House Cable FPT template."""
    return ATSTemplate(
        template_id="260627_L4_AutomaticTransferSwitch(House)_FunctionalPerformanceTest_Cable_Rev0",
        display_name="L4 ATS House Cable FPT",
        level="L4",
        equipment_type="ATS",
        category="House_Cable",
        variant="Cable",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
        ],
        frequency=141
    )


def get_ats_l4_cable_gen_template() -> ATSTemplate:
    """Generate L4 ATS Generator Cable FPT template."""
    return ATSTemplate(
        template_id="260627_L4_AutomaticTransferSwitch(GEN)_FunctionalPerformanceTest_Cable_Rev0",
        display_name="L4 ATS Generator Cable FPT",
        level="L4",
        equipment_type="ATS",
        category="GEN_Cable",
        variant="Cable",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_DOCUMENTATION,
        ],
        frequency=58
    )


def get_ats_l2c_pre_energization_template() -> ATSTemplate:
    """Generate L2C ATS Pre-Energization template."""
    return ATSTemplate(
        template_id="L2C - ELEC - ATS Pre-energization - Rev0",
        display_name="L2C ATS Pre-Energization",
        level="L2C",
        equipment_type="ATS",
        category="Pre-Energization",
        variant="L2C",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_PRE_ENERGIZATION,
        ],
        frequency=102
    )


def get_ats_site_arrival_template() -> ATSTemplate:
    """Generate ATS Site Arrival Inspection template."""
    return ATSTemplate(
        template_id="Electrical Equipment Site Arrival - ATS",
        display_name="ATS Site Arrival Inspection",
        level="L2",
        equipment_type="ATS",
        category="Site_Arrival",
        variant="SAI",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_SITE_ARRIVAL,
        ],
        frequency=612
    )


def get_ats_nats_busway_template() -> ATSTemplate:
    """Generate L4C NATs and Busway Cx template (highest frequency)."""
    return ATSTemplate(
        template_id="L4C - ELEC - NATs and Busway Cx VNA1",
        display_name="L4C NATs and Busway Commissioning",
        level="L4C",
        equipment_type="ATS",
        category="NATs_Busway",
        variant="FPT",
        sections=[
            ATS_EQUIPMENT_ID,
            ATS_FUNCTIONAL_TEST,
            ATS_BMS_VERIFICATION,
            ATS_END_OF_TEST,
        ],
        frequency=81123
    )


# =============================================================================
# VARIANT CONFIGURATION
# =============================================================================

ATS_VARIANTS = {
    "KND1": {
        "description": "Primary distribution",
        "frequency": 881,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4", "IWM", "SUB1", "SUB2"],
    },
    "TTX1": {
        "description": "Transfer/transformer type 1",
        "frequency": 122,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4", "IWM", "UPSA1", "UPSA2", "UPSB1", "UPSB2", "UPSC1", "UPSC2", "UPSD1", "UPSD2"],
    },
    "TTX2": {
        "description": "Transfer/transformer type 2",
        "frequency": 102,
        "areas": ["ERA", "ERB", "IWM", "UPSB1", "UPSB2", "UPSC1", "UPSC2", "UPSD1", "UPSD2"],
    },
    "UCO1": {
        "description": "UPS/critical power type 1",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4", "EY1", "EY2", "SUB1", "SUB2", "UPSA1", "UPSA2", "UPSB1", "UPSB2", "UPSC1", "UPSC2", "UPSD1", "UPSD2"],
    },
    "UCO2": {
        "description": "UPS/critical power type 2",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD", "EY1", "EY2", "UPSA1", "UPSA2", "UPSB1", "UPSB2", "UPSC1", "UPSC2", "UPSD1", "UPSD2"],
    },
    "LCO1": {
        "description": "Line circuit type 1 (text entry)",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4", "EY1", "EY2", "IWM"],
    },
    "LCO2": {
        "description": "Line circuit type 2 (text entry)",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "UPSA1", "UPSA2", "UPSB1", "UPSB2", "UPSC1", "UPSC2", "UPSD1", "UPSD2", "EY1", "EY2", "IWM"],
    },
    "RMN1": {
        "description": "Remote monitoring",
        "frequency": 68,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4", "UPSA", "UPSB", "UPSC", "UPSD"],
    },
    "MCA1": {
        "description": "Motor control type 1",
        "frequency": 102,
        "areas": ["ERA", "ERN1", "ERN2", "ERN3", "ERN4", "UPSA1", "UPSA2", "UPSB1", "UPSB2"],
    },
    "MCA2": {
        "description": "Motor control type 2",
        "frequency": 102,
        "areas": ["UPSD2"],
    },
    "MAL1": {
        "description": "Main alignment type 1",
        "frequency": 92,
        "areas": ["ERA", "ERN1", "ERN4", "SUB1", "UPSD"],
    },
    "MAL2": {
        "description": "Main alignment type 2",
        "frequency": 14,
        "areas": ["SUB2"],
    },
    "SNB5": {
        "description": "Specialized network bus type 5",
        "frequency": 102,
        "areas": ["ER-BDF1", "ER-BDF2", "ER-BDF3", "ER-BDF4", "MR-BDF12", "MR-BDF34"],
    },
    "SNB6": {
        "description": "Specialized network bus type 6",
        "frequency": 102,
        "areas": ["ER-BDF1", "ER-BDF2", "ER-BDF3", "ER-BDF4", "MR-BDF12", "MR-BDF34"],
    },
    "GTN5": {
        "description": "Ground/transfer network type 5",
        "frequency": 194,
        "areas": ["ER-BDF1", "ER-BDF2", "ER-BDF3", "ER-BDF4", "EY2", "MR-BDF12", "MR-BDF34", "SSB"],
    },
    "GTN6": {
        "description": "Ground/transfer network type 6",
        "frequency": 102,
        "areas": ["ER-BDF1", "ER-BDF2", "ER-BDF3", "ER-BDF4", "EY2", "MR-BDF12", "MR-BDF34"],
    },
    "RIN": {
        "description": "Ring interconnect",
        "frequency": 102,
        "areas": ["ERA", "ERN1"],
    },
}

ATS_AREA_CODES = {
    "ERA": "East Row A",
    "ERB": "East Row B",
    "ERC": "East Row C",
    "ERD": "East Row D",
    "ERN1": "East Row Network 1",
    "ERN2": "East Row Network 2",
    "ERN3": "East Row Network 3",
    "ERN4": "East Row Network 4",
    "EY1": "East Yard 1",
    "EY2": "East Yard 2",
    "IWM": "Interior Water Main",
    "SSB": "Service Switchboard",
    "SUB1": "Substation 1",
    "SUB2": "Substation 2",
    "UPSA": "UPS Area A",
    "UPSA1": "UPS Area A1",
    "UPSA2": "UPS Area A2",
    "UPSB": "UPS Area B",
    "UPSB1": "UPS Area B1",
    "UPSB2": "UPS Area B2",
    "UPSC": "UPS Area C",
    "UPSC1": "UPS Area C1",
    "UPSC2": "UPS Area C2",
    "UPSD": "UPS Area D",
    "UPSD1": "UPS Area D1",
    "UPSD2": "UPS Area D2",
    "ER-BDF1": "East Row BDF 1",
    "ER-BDF2": "East Row BDF 2",
    "ER-BDF3": "East Row BDF 3",
    "ER-BDF4": "East Row BDF 4",
    "MR-BDF12": "Main Row BDF 1-2",
    "MR-BDF34": "Main Row BDF 3-4",
}

ATS_CATEGORIES = {
    "FCA": {"description": "Fire Control Area ATS", "l4_frequency": 15073},
    "House": {"description": "House ATS", "l4_frequency": 1367},
    "House_Gen": {"description": "House with Generator ATS", "l4_frequency": 536},
    "MSG": {"description": "Medium Switchgear ATS", "l4_frequency": 7662},
    "HMD": {"description": "Harmonic Mitigation Device ATS", "l4_frequency": 3035},
    "mCUP": {"description": "Modular Critical Power Unit ATS", "l4_frequency": 1788},
    "FirePump": {"description": "Fire Pump ATS", "l4_frequency": 1297},
    "CDU": {"description": "Coolant Distribution Unit ATS", "l4_frequency": 182},
    "Admin": {"description": "Administrative ATS", "l4_frequency": 208},
    "NLH": {"description": "No-Load House ATS", "l4_frequency": 252},
    "NATs_Busway": {"description": "NATs and Busway", "l4_frequency": 81123},
}


# =============================================================================
# TEMPLATE FACTORY
# =============================================================================

class ATSTemplateFactory:
    """Factory for generating ATS form templates."""

    @staticmethod
    def create_l3_template(
        area: str,
        identifier: str,
        variant: str
    ) -> ATSTemplate:
        """Create an L3 ATS template for a specific equipment instance."""
        return get_ats_l3_bms_template(area, identifier, variant)

    @staticmethod
    def create_l4_template(category: str = "FCA") -> ATSTemplate:
        """Create an L4 ATS template by category.

        Args:
            category: ATS category (FCA, House, House_Gen, MSG, HMD, mCUP,
                     FirePump, CDU, Admin, NLH, NATs_Busway)
        """
        templates = {
            "FCA": get_ats_l4_fca_template,
            "House": get_ats_l4_house_template,
            "House_Gen": get_ats_l4_house_gen_template,
            "MSG": get_ats_l4_msg_template,
            "MSG_FPT": get_ats_l4_msg_fpt_template,
            "HMD": get_ats_l4_hmd_template,
            "mCUP": get_ats_l4_mcup_template,
            "FirePump": get_ats_l4_firepump_template,
            "CDU": get_ats_l4_cdu_template,
            "Admin": get_ats_l4_admin_template,
            "NLH": get_ats_l4_nlh_template,
            "House_Cable": get_ats_l4_cable_house_template,
            "GEN_Cable": get_ats_l4_cable_gen_template,
            "NATs_Busway": get_ats_nats_busway_template,
        }
        factory_func = templates.get(category, get_ats_l4_fca_template)
        return factory_func()

    @staticmethod
    def create_l2c_template() -> ATSTemplate:
        """Create an L2C ATS Pre-Energization template."""
        return get_ats_l2c_pre_energization_template()

    @staticmethod
    def create_site_arrival_template() -> ATSTemplate:
        """Create an ATS Site Arrival Inspection template."""
        return get_ats_site_arrival_template()

    @staticmethod
    def get_available_categories() -> List[str]:
        """Get list of available ATS categories."""
        return list(ATS_CATEGORIES.keys())

    @staticmethod
    def get_available_variants() -> List[str]:
        """Get list of available ATS variants."""
        return list(ATS_VARIANTS.keys())

    @staticmethod
    def get_available_areas() -> List[str]:
        """Get list of available area codes."""
        return list(ATS_AREA_CODES.keys())

    @staticmethod
    def generate_fca_identifiers(count: int = 8) -> List[str]:
        """Generate FCA equipment identifiers (FCA-1 through FCA-8)."""
        return [f"FCA-{i}" for i in range(1, count + 1)]

    @staticmethod
    def generate_cdu_identifiers(count: int = 6) -> List[str]:
        """Generate CDU equipment identifiers (CDU-1 through CDU-6)."""
        return [f"CDU-{i}" for i in range(1, count + 1)]

    @staticmethod
    def generate_house_identifiers() -> List[str]:
        """Generate House equipment identifiers (H1, H2, H3)."""
        return ["H1", "H2", "H3"]


def convert_template_to_form_sections(template: ATSTemplate) -> List[Dict[str, Any]]:
    """Convert ATSTemplate to form generator format.

    Args:
        template: ATSTemplate instance

    Returns:
        List of section dictionaries for form generation
    """
    sections = []

    for section in template.sections:
        items = []
        for item in section.items:
            item_dict = {
                "description": item.description,
                "acceptance_criteria": item.acceptance_criteria,
                "response_type": item.response_type.value,
                "priority": item.priority,
            }

            if item.presets != PresetType.NONE:
                item_dict["presets"] = item.presets.value

            items.append(item_dict)

        sections.append({
            "name": section.name,
            "display_name": section.display_name,
            "order": section.section_order,
            "items": items,
        })

    return sections


def get_template_summary() -> Dict[str, Any]:
    """Get summary of available ATS templates."""
    return {
        "equipment_type": "ATS",
        "spec_code": "260627",
        "l3_templates": {
            "description": "L3 Combined BMS templates",
            "variants": list(ATS_VARIANTS.keys()),
            "areas": list(ATS_AREA_CODES.keys()),
            "identifier_types": ["FCA-1 to FCA-8", "CDU-1 to CDU-6", "H1-H3", "N1-N7"],
        },
        "l4_templates": {
            category: {
                "description": info["description"],
                "frequency": info["l4_frequency"],
            }
            for category, info in ATS_CATEGORIES.items()
        },
        "l2c_templates": {
            "Pre-Energization": {
                "description": "Pre-Energization Verification",
                "frequency": 102,
            },
        },
        "site_arrival": {
            "description": "Site Arrival Inspection",
            "frequency": 612,
        },
        "total_categories": len(ATS_CATEGORIES),
        "total_variants": len(ATS_VARIANTS),
        "total_areas": len(ATS_AREA_CODES),
        "variant_info": ATS_VARIANTS,
    }

