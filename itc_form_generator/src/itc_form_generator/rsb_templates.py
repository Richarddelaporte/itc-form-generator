"""RSB (Row Switch Board) Templates - Based on actual BIM360/ACC form data.

This module contains RSB-specific templates extracted from the
idc_acc_form_responses_datamart Hive table (Query 4 results).

RSB forms follow a structured naming convention:
    {SpecCode}_{Level}_{EquipmentType}_{Area} - RSB - {Number}_{Variant} - {Rev}_{Integration}

Example: 260000_L3_Data Hall Electrical Skid_ERA - RSB - 03_KND1 - Rev0_CombinedBMS

Equipment Variants (from query data):
    - KND1: High frequency (200+ per instance) - Primary distribution
    - TTX1: High frequency (100-200) - Transformer/transfer
    - UCO2: Medium-high (100-200) - UPS/critical power
    - LCO1/LCO2: Text entry forms (102 frequency) - Line circuit
    - RMN1: Remote monitoring
    - MCA1: Motor control
    - RIN1: Ring interconnect
    - SNB5/GTN5/GTN6: Lower frequency (45-57) - Specialized
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ResponseType(Enum):
    """Response types from ACC form data."""
    TOGGLE = "toggle"      # Yes/No/NA selection
    TEXT = "text"          # Free text input
    NUMBER = "number"      # Numeric input
    CHOICE = "choice"      # Multiple choice
    DATE = "date"          # Date picker
    SIGNATURE = "signature"  # Signature capture


class PresetType(Enum):
    """Common preset configurations from ACC forms."""
    YES_NO_NA = "No/Yes/NA"
    PASS_FAIL_NA = "Fail/Pass/NA"
    PASS_FAIL = "Pass/Fail"
    COMPLETE_INCOMPLETE = "Complete/Incomplete"
    NONE = ""


@dataclass
class RSBCheckItem:
    """RSB check item with response configuration."""
    description: str
    presets: PresetType = PresetType.YES_NO_NA
    response_type: ResponseType = ResponseType.TOGGLE
    acceptance_criteria: str = "Pass"
    priority: str = "Medium"
    frequency: int = 0  # How often this appears in production


@dataclass
class RSBSection:
    """RSB form section with ordered check items."""
    name: str
    display_name: str
    section_order: int
    items: List[RSBCheckItem] = field(default_factory=list)
    usage_count: int = 0


@dataclass
class RSBTemplate:
    """Complete RSB form template."""
    template_id: str
    display_name: str
    level: str  # L3 or L4
    equipment_type: str  # RSB, RDB, etc.
    variant: str  # KND1, TTX1, etc.
    sections: List[RSBSection] = field(default_factory=list)
    frequency: int = 0


# =============================================================================
# RSB SECTIONS FROM PRODUCTION DATA (Query 3 & 4 Results)
# =============================================================================

# Pre-Energization Section (from Query 4)
RSB_PRE_ENERGIZATION = RSBSection(
    name="Pre-Energization (Applies to MVS, PTX, and RSB)",
    display_name="Pre-Energization",
    section_order=1,
    usage_count=233,
    items=[
        RSBCheckItem("QAQC Authority Name:", PresetType.NONE, ResponseType.TEXT, frequency=233),
        RSBCheckItem("While performing this procedure:", PresetType.YES_NO_NA, ResponseType.TOGGLE, frequency=204),
        RSBCheckItem("Verify all prerequisite inspections have been completed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        RSBCheckItem("Confirm equipment energization status is correct", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        RSBCheckItem("Verify all safety procedures are in place", PresetType.YES_NO_NA, ResponseType.TOGGLE),
        RSBCheckItem("Review LOTO procedures completed", PresetType.YES_NO_NA, ResponseType.TOGGLE),
    ]
)

# Device & Network Info Verification (from Query 4)
RSB_DEVICE_NETWORK_INFO = RSBSection(
    name="Device & Network Info Verification",
    display_name="Device & Network Information",
    section_order=2,
    usage_count=102,
    items=[
        RSBCheckItem(
            "DEVICE & NETWORK INFO VERIFICATION: Device Type, Device Name, Make, Model, "
            "FDM Parent Name, EPMS Requirement, Variant",
            PresetType.PASS_FAIL_NA,
            ResponseType.TOGGLE,
            frequency=102
        ),
        RSBCheckItem("Device Type:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Device Name:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Make:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Model:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("FDM Parent Name:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("EPMS Requirement:", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Variant:", PresetType.NONE, ResponseType.TEXT),
    ]
)

# Documentation Verification (from Query 3)
RSB_DOCUMENTATION = RSBSection(
    name="Documentation Verification",
    display_name="Documentation Verification",
    section_order=3,
    usage_count=267677,
    items=[
        RSBCheckItem(
            "Review equipment issues and confirm that each closed issue has been adequately "
            "addressed and that no open issues prevent the equipment from moving to L3 activities",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=267677
        ),
        RSBCheckItem(
            "Confirm electrical cable testing documentation is reviewed and loaded into Build",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=179954
        ),
        RSBCheckItem(
            "Review NETA documentation in Build to confirm passing results for all applicable devices.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=177344
        ),
        RSBCheckItem(
            "Confirm vendor or manufacturer pre startup checklist is reviewed and loaded into Build.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=177344
        ),
        RSBCheckItem(
            "Confirm electrical contractor torque checklists are reviewed and loaded into Build.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=175257
        ),
        RSBCheckItem(
            "Confirm site arrival inspection is in Build and is complete",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=170221
        ),
        RSBCheckItem(
            "Confirm oil sampling test has been completed and documentation in Build",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=170221
        ),
        RSBCheckItem(
            "Confirm electrical contractor installation checklist is completed in Build.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=170221
        ),
    ]
)

# Confirm Submittal Documentation (from Query 3)
RSB_SUBMITTAL_DOC = RSBSection(
    name="Confirm Submittal Documentation",
    display_name="Submittal Documentation",
    section_order=4,
    usage_count=29215,
    items=[
        RSBCheckItem(
            "Compare submittal to equipment provided and verify there are no deviations. "
            "Create BIM issues for items that do not match.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=29215
        ),
        RSBCheckItem(
            "Confirm contractor site acceptance inspection (SAI) with photos has been loaded "
            "to Build with any issues recorded.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=29215
        ),
        RSBCheckItem(
            "Confirm approved submittal data has been reviewed prior to inspection.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=29215
        ),
    ]
)

# Damage and Equipment Protection (from Query 3)
RSB_DAMAGE_PROTECTION = RSBSection(
    name="Damage and Equipment Protection",
    display_name="Damage and Equipment Protection",
    section_order=5,
    usage_count=49129,
    items=[
        RSBCheckItem(
            "Confirm equipment is visually inspected for damage, and if damage is present, "
            "an issue has already been recorded.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=49129
        ),
        RSBCheckItem(
            "Attach photos of current equipment condition and installation to the header of "
            "this checklist. At a minimum, include a photo of the equipment nameplate, a photo "
            "from each side of equipment exterior, and a photo of each interior section. "
            "(when applicable) There should be both close views and overall views of all sides and sections.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=49129
        ),
        RSBCheckItem(
            "Confirm equipment is protected from potential dust, debris and environmental "
            "elements which may cause rust/deterioration of components and motors, belts, etc.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=29215
        ),
    ]
)

# Controls Installation (from Query 3)
RSB_CONTROLS_INSTALLATION = RSBSection(
    name="Controls Installation",
    display_name="Controls Installation",
    section_order=6,
    usage_count=35565,
    items=[
        RSBCheckItem(
            "Confirm all controls devices are connected; ie. Sensors, etc.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
        RSBCheckItem(
            "Has multi-point airflow sensor/tubing been visually confirmed and connected?",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
        RSBCheckItem(
            "Confirm wire terminations are secure using tug test.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
        RSBCheckItem(
            "Confirm installation of associated duct pressure sensor/transmitter and "
            "connection to unit control damper.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
        RSBCheckItem(
            "Confirm if CO2 sensor is required, and if so, the proper sensor was installed "
            "within space. (may be a T & CO2 combination sensor)",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
        RSBCheckItem(
            "Confirm that zone temperature sensor is installed in the correct location per the drawings.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=35565
        ),
    ]
)

# Alerts Section (from Query 3)
RSB_ALERTS = RSBSection(
    name="Alerts",
    display_name="Alert Verification",
    section_order=7,
    usage_count=9696,
    items=[
        RSBCheckItem(
            "Alert Time Delay correct and in correct place per Points List "
            "(P or P/S - in graphic, S - in Alert Manager)",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Alert is cleared both locally and at BMS/EPMS",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Email notification sent (Priority 1 Alert only)",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Exhaust fan status is accurate at the BMS",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Alert is initiated locally",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Reset H2 Alert",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Alert generated at the Alert Manager and Priority matches Points List",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Alert is initiated at BMS and/or EPMS graphic(s) (if applies)",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Exhaust fan is disabled",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "Exhaust fan is enabled and ramps to speed setpoint",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=9696
        ),
        RSBCheckItem(
            "With system in auto, initiate a H2 Lvl 1 Alert by using test gas to raise "
            "H2 level above H2 Lvl 1 Alert setpoint. If test gas is not available, use test button.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
        RSBCheckItem(
            "With system in auto, initiate a H2 Lvl 2 Alert by using test gas to raise "
            "H2 level above H2 Lvl 2 Alert setpoint. If test gas is not available, use test button.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
        RSBCheckItem(
            "H2 Detection",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
    ]
)

# End of Test Section (from Query 3)
RSB_END_OF_TEST = RSBSection(
    name="End of Test",
    display_name="End of Test",
    section_order=8,
    usage_count=4848,
    items=[
        RSBCheckItem(
            "Test, Adjust, Balance (TAB) preliminary and/or final testing is complete, "
            "documented, reviewed and approved",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
        RSBCheckItem(
            "Verify that all equipment panels and covers are in place and secured",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
        RSBCheckItem(
            "Verify that all simulated variables are restored and removed at the BMS",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
        RSBCheckItem(
            "Place the unit in the condition specified by the Project. Note Condition Here:",
            PresetType.NONE,
            ResponseType.TEXT,
            frequency=4848
        ),
        RSBCheckItem(
            "TAB Verification sampling requirement has been completed by CxA",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
    ]
)

# Equipment Identification Section (for L4 forms)
RSB_EQUIPMENT_ID = RSBSection(
    name="Equipment Identification",
    display_name="Equipment Identification",
    section_order=1,
    usage_count=45770,
    items=[
        RSBCheckItem("Equipment Designation", PresetType.NONE, ResponseType.TEXT, frequency=45770),
        RSBCheckItem("Project", PresetType.NONE, ResponseType.TEXT, frequency=8160),
        RSBCheckItem("Location", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Asset Tag Number", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Date Received", PresetType.NONE, ResponseType.DATE),
        RSBCheckItem("Model number or name", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Manufacturer or Vendor (make)", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Serial Number", PresetType.NONE, ResponseType.TEXT),
        RSBCheckItem("Equipment type", PresetType.NONE, ResponseType.TEXT),
    ]
)

# Commissioning Support Section
RSB_COMMISSIONING_SUPPORT = RSBSection(
    name="Commissioning Support",
    display_name="Commissioning Support",
    section_order=2,
    usage_count=4848,
    items=[
        RSBCheckItem(
            "All necessary personnel are available to exercise the equipment and ancillary systems. "
            "**DO NOT PROCEED IF PERSONNEL IS NOT AVAILABLE.",
            PresetType.YES_NO_NA,
            ResponseType.TOGGLE,
            frequency=4848
        ),
    ]
)


# =============================================================================
# RSB TEMPLATE GENERATORS
# =============================================================================

def get_rsb_l3_bms_template(
    area: str = "ERA",
    number: str = "01",
    variant: str = "KND1"
) -> RSBTemplate:
    """Generate L3 RSB BMS Combined template.

    Args:
        area: Building/area code (ERA, ERB, ERC, ERD, DHA, etc.)
        number: Equipment number (01-40, R1, R2)
        variant: Equipment variant (KND1, TTX1, UCO2, etc.)

    Returns:
        RSBTemplate configured for the specific equipment instance
    """
    template_id = f"260000_L3_Data Hall Electrical Skid_{area} - RSB - {number}_{variant} - Rev0_CombinedBMS"

    return RSBTemplate(
        template_id=template_id,
        display_name=f"L3 RSB {area}-{number} ({variant}) - Combined BMS",
        level="L3",
        equipment_type="RSB",
        variant=variant,
        sections=[
            RSB_PRE_ENERGIZATION,
            RSB_DEVICE_NETWORK_INFO,
            RSB_DOCUMENTATION,
            RSB_SUBMITTAL_DOC,
            RSB_DAMAGE_PROTECTION,
            RSB_CONTROLS_INSTALLATION,
            RSB_ALERTS,
            RSB_END_OF_TEST,
        ],
        frequency=204 if variant == "KND1" else 102
    )


def get_rsb_l4_fpt_template(
    area: str = "ERA",
    number: str = "01"
) -> RSBTemplate:
    """Generate L4 RSB Functional Performance Test template.

    Args:
        area: Building/area code
        number: Equipment number

    Returns:
        RSBTemplate configured for L4 FPT
    """
    template_id = f"260401_L4_Row Switch Board (RSB)_FunctionalPerformanceTest_Rev0"

    return RSBTemplate(
        template_id=template_id,
        display_name=f"L4 RSB Functional Performance Test",
        level="L4",
        equipment_type="RSB",
        variant="FPT",
        sections=[
            RSB_EQUIPMENT_ID,
            RSB_COMMISSIONING_SUPPORT,
            RSB_DOCUMENTATION,
            RSB_DAMAGE_PROTECTION,
            RSB_CONTROLS_INSTALLATION,
            RSB_ALERTS,
            RSB_END_OF_TEST,
        ],
        frequency=24892
    )


def get_rsb_l4_cev_template() -> RSBTemplate:
    """Generate L4 RSB Commissioning Equipment Verification template."""
    template_id = "L4 - Cx - ELEC - RSB - Rev 0"

    return RSBTemplate(
        template_id=template_id,
        display_name="L4 RSB Commissioning Equipment Verification",
        level="L4",
        equipment_type="RSB",
        variant="CEV",
        sections=[
            RSB_EQUIPMENT_ID,
            RSB_DOCUMENTATION,
            RSB_DAMAGE_PROTECTION,
            RSB_CONTROLS_INSTALLATION,
            RSB_END_OF_TEST,
        ],
        frequency=45770
    )


def get_rsb_l4_cable_template() -> RSBTemplate:
    """Generate L4 RSB Cable Functional Performance Test template."""
    template_id = "260401_L4_RowSwitchBoard(RSB)_FunctionalPerformanceTest_Cable_Rev0"

    return RSBTemplate(
        template_id=template_id,
        display_name="L4 RSB Cable FPT",
        level="L4",
        equipment_type="RSB",
        variant="Cable",
        sections=[
            RSB_EQUIPMENT_ID,
            RSB_DOCUMENTATION,
        ],
        frequency=5358
    )


def get_rsb_l4_lco3_template() -> RSBTemplate:
    """Generate L4 RSB LCO3 template."""
    template_id = "L4 - ELEC - RowSwitchBoard(RSB) - LCO3 - Rev0"

    return RSBTemplate(
        template_id=template_id,
        display_name="L4 RSB LCO3",
        level="L4",
        equipment_type="RSB",
        variant="LCO3",
        sections=[
            RSB_EQUIPMENT_ID,
            RSB_DOCUMENTATION,
        ],
        frequency=8160
    )


# =============================================================================
# VARIANT CONFIGURATION
# =============================================================================

RSB_VARIANTS = {
    "KND1": {
        "description": "Primary distribution",
        "frequency": 204,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "TTX1": {
        "description": "Transformer/transfer",
        "frequency": 186,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "UCO2": {
        "description": "UPS/critical power",
        "frequency": 204,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "LCO1": {
        "description": "Line circuit 1",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "LCO2": {
        "description": "Line circuit 2",
        "frequency": 102,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "RMN1": {
        "description": "Remote monitoring",
        "frequency": 8,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "MCA1": {
        "description": "Motor control",
        "frequency": 20,
        "areas": ["ERA", "ERB", "ERC", "ERD"],
    },
    "RIN1": {
        "description": "Ring interconnect",
        "frequency": 42,
        "areas": ["ERA", "ERB", "ERC", "ERD", "ERN1", "ERN2", "ERN3", "ERN4"],
    },
    "SNB5": {
        "description": "Specialized network bus",
        "frequency": 190,
        "areas": ["DHA"],
    },
    "GTN5": {
        "description": "Ground/transfer network 5",
        "frequency": 57,
        "areas": ["DHA"],
    },
    "GTN6": {
        "description": "Ground/transfer network 6",
        "frequency": 51,
        "areas": ["DHA"],
    },
    "CHY1": {
        "description": "Chiller yard",
        "frequency": 6,
        "areas": ["ERA"],
    },
    "MAL1": {
        "description": "Main alignment",
        "frequency": 15,
        "areas": ["ERN4"],
    },
}

AREA_CODES = {
    "ERA": "East Row A",
    "ERB": "East Row B",
    "ERC": "East Row C",
    "ERD": "East Row D",
    "DHA": "Data Hall A",
    "ERN1": "East Row Network 1",
    "ERN2": "East Row Network 2",
    "ERN3": "East Row Network 3",
    "ERN4": "East Row Network 4",
}


# =============================================================================
# TEMPLATE FACTORY
# =============================================================================

class RSBTemplateFactory:
    """Factory for generating RSB form templates."""

    @staticmethod
    def create_l3_template(
        area: str,
        number: str,
        variant: str
    ) -> RSBTemplate:
        """Create an L3 RSB template for a specific equipment instance."""
        return get_rsb_l3_bms_template(area, number, variant)

    @staticmethod
    def create_l4_template(form_type: str = "FPT") -> RSBTemplate:
        """Create an L4 RSB template.

        Args:
            form_type: Type of L4 form (FPT, CEV, Cable, LCO3)
        """
        templates = {
            "FPT": get_rsb_l4_fpt_template,
            "CEV": get_rsb_l4_cev_template,
            "Cable": get_rsb_l4_cable_template,
            "LCO3": get_rsb_l4_lco3_template,
        }
        factory_func = templates.get(form_type, get_rsb_l4_fpt_template)
        return factory_func()

    @staticmethod
    def get_available_variants() -> List[str]:
        """Get list of available RSB variants."""
        return list(RSB_VARIANTS.keys())

    @staticmethod
    def get_available_areas() -> List[str]:
        """Get list of available area codes."""
        return list(AREA_CODES.keys())

    @staticmethod
    def generate_equipment_numbers(count: int = 40) -> List[str]:
        """Generate equipment numbers (01-40, R1, R2)."""
        numbers = [f"{i:02d}" for i in range(1, count + 1)]
        numbers.extend(["R1", "R2"])
        return numbers

    @staticmethod
    def create_batch_templates(
        area: str,
        variants: List[str] = None,
        equipment_count: int = 40
    ) -> List[RSBTemplate]:
        """Generate batch of templates for an area.

        Args:
            area: Area code (ERA, ERB, etc.)
            variants: List of variants to generate (default: all)
            equipment_count: Number of equipment instances per variant

        Returns:
            List of RSBTemplate instances
        """
        if variants is None:
            variants = [v for v, cfg in RSB_VARIANTS.items()
                       if area in cfg.get("areas", [])]

        templates = []
        numbers = RSBTemplateFactory.generate_equipment_numbers(equipment_count)

        for variant in variants:
            for number in numbers:
                templates.append(
                    RSBTemplateFactory.create_l3_template(area, number, variant)
                )

        return templates


def convert_template_to_form_sections(template: RSBTemplate) -> List[Dict[str, Any]]:
    """Convert RSBTemplate to form generator format.

    Args:
        template: RSBTemplate instance

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
    """Get summary of available RSB templates."""
    return {
        "l3_templates": {
            "description": "L3 Combined BMS templates",
            "variants": list(RSB_VARIANTS.keys()),
            "areas": list(AREA_CODES.keys()),
            "equipment_range": "01-40, R1, R2",
        },
        "l4_templates": {
            "FPT": {
                "description": "Functional Performance Test",
                "frequency": 24892,
            },
            "CEV": {
                "description": "Commissioning Equipment Verification",
                "frequency": 45770,
            },
            "Cable": {
                "description": "Cable FPT",
                "frequency": 5358,
            },
            "LCO3": {
                "description": "LCO3 Line Circuit",
                "frequency": 8160,
            },
        },
        "total_section_types": 9,
        "variant_info": RSB_VARIANTS,
    }
