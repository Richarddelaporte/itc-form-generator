"""Equipment Templates - Based on actual BIM360/ACC form data.

This module contains equipment-specific templates extracted from
the idc_acc_form_responses_datamart Hive table.

Template naming convention: [SpecCode_Level_EquipmentType]_FormType
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class FormType(Enum):
    """Form types based on commissioning phases."""
    # Level 2 - Installation/Verification
    CEV = "Commissioning & Equipment Verification"
    IEV = "Installation & Equipment Verification"
    SET_IN_PLACE = "Set In Place Inspection"
    INSTALLATION_WIRING = "Installation & Wiring"

    # Level 3 - Pre-Commissioning
    PRE_ENERGIZATION = "Pre-Energization Checklist"
    MANUFACTURER_PRESTARTUP = "Manufacturer Equipment Pre-Startup"
    POINT_TO_POINT = "Point-to-Point Checkout"
    ENERGIZATION_VERIFICATION = "Energization Verification"
    TAB_VERIFICATION = "TAB Verification"

    # Level 4 - Functional Performance Testing
    FPT = "Functional Performance Test"
    FPT_PART_1 = "Functional Performance Test Part 1"
    FPT_PART_2 = "Functional Performance Test Part 2"
    FPT_CABLE = "Functional Performance Test - Cable"

    # General
    INSPECTION = "General Inspection"


class EquipmentLevel(Enum):
    """Inspection levels (L1-L4)."""
    L1 = "Level 1 - Installation"
    L2 = "Level 2 - Verification"
    L3 = "Level 3 - Commissioning"
    L4 = "Level 4 - Final"


@dataclass
class CheckItemTemplate:
    """Template for a single check item."""
    description: str
    acceptance_criteria: str = ""
    response_type: str = "choice"  # choice, text, number, toggle, date
    presets: list = field(default_factory=lambda: ["Pass", "Fail", "N/A"])
    priority: str = "Medium"  # Critical, High, Medium, Low
    method: str = ""


@dataclass
class SectionTemplate:
    """Template for a form section."""
    name: str
    display_order: int
    items: list = field(default_factory=list)


@dataclass
class EquipmentTemplate:
    """Complete template for equipment type."""
    spec_code: str
    equipment_type: str
    display_name: str
    form_types: list = field(default_factory=list)
    sections: dict = field(default_factory=dict)


def get_mua_template() -> EquipmentTemplate:
    """Get Makeup Air Unit template."""
    return EquipmentTemplate(
        spec_code="238200",
        equipment_type="MakeupAirUnit",
        display_name="Makeup Air Unit (MUA)",
        form_types=[FormType.SET_IN_PLACE, FormType.MANUFACTURER_PRESTARTUP, FormType.CEV],
        sections={
            FormType.CEV: [
                SectionTemplate(
                    name="Documentation Verification",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify 25 90 05 - Common Work Results available", "Document available"),
                        CheckItemTemplate("Verify 25 60 10 - Mechanical Points List available", "Document available"),
                        CheckItemTemplate("Verify IC712 - P&ID available", "Document available"),
                        CheckItemTemplate("Verify TAB report with setpoint values", "TAB report complete"),
                    ]
                ),
                SectionTemplate(
                    name="Component Verification",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Verify supply air isolation damper operation", "Damper strokes fully"),
                        CheckItemTemplate("Verify outside air isolation damper operation", "Damper strokes fully"),
                        CheckItemTemplate("Verify supply fan array VFD operation", "VFD responds to commands"),
                        CheckItemTemplate("Test fan rotation direction", "Rotation correct"),
                        CheckItemTemplate("Verify electric heating coil SCR operation", "SCR modulates 0-100%"),
                        CheckItemTemplate("Verify filter DP sensor operation", "DP sensor reading correctly", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Setpoint Verification",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Verify Supply Air Low Temperature Setpoint", "50°F", response_type="number"),
                        CheckItemTemplate("Verify Supply Air High RH Setpoint", "90% RH", response_type="number"),
                        CheckItemTemplate("Verify High Humidity Offset", "5%", response_type="number"),
                        CheckItemTemplate("Verify Duct Static Pressure Setpoint", "Per TAB", response_type="number"),
                        CheckItemTemplate("Verify Min Fan Speed Setpoint", "Per TAB", response_type="number"),
                        CheckItemTemplate("Verify Max Fan Speed Setpoint", "Per TAB", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Operating Mode Tests",
                    display_order=4,
                    items=[
                        CheckItemTemplate("Test Heating Mode operation", "Heater modulates when OA temp < 50°F"),
                        CheckItemTemplate("Test High Relative Humidity Mode", "Heater modulates when OA RH > 90%"),
                        CheckItemTemplate("Test Economization Mode", "Heater locked out when conditions met"),
                    ]
                ),
                SectionTemplate(
                    name="Alert Testing",
                    display_order=5,
                    items=[
                        CheckItemTemplate("Test MUA Run Status Mismatch alert", "Alert after 120 seconds", priority="Critical"),
                        CheckItemTemplate("Test MUA Fault Status alert", "Alert on fault, requires manual reset", priority="Critical"),
                        CheckItemTemplate("Test Low Duct Static Pressure alert", "Alert after 300 seconds"),
                        CheckItemTemplate("Test High Discharge Pressure shutdown", "Unit shuts down", priority="Critical"),
                    ]
                ),
                SectionTemplate(
                    name="Safety Interlocks",
                    display_order=6,
                    items=[
                        CheckItemTemplate("Test smoke alarm interlock", "MUA shuts down on smoke alarm", priority="Critical"),
                        CheckItemTemplate("Test fire alarm interlock", "MUA shuts down on fire alarm", priority="Critical"),
                    ]
                ),
                SectionTemplate(
                    name="Utility Loss Mode Testing",
                    display_order=7,
                    items=[
                        CheckItemTemplate("Test Momentary Disturbance (<5 sec)", "MUA restarts automatically"),
                        CheckItemTemplate("Test Battery Operation (5-45 sec)", "MUA disabled by BMS"),
                        CheckItemTemplate("Test Controlled Shutdown (>45 sec)", "MUA restarts on utility restoration"),
                    ]
                ),
            ],
        }
    )


def get_fcu_template() -> EquipmentTemplate:
    """Get Fan Coil Unit template."""
    return EquipmentTemplate(
        spec_code="238123",
        equipment_type="FanCoilAssembly",
        display_name="Fan Coil Unit (FCU)",
        form_types=[FormType.SET_IN_PLACE, FormType.MANUFACTURER_PRESTARTUP, FormType.CEV],
        sections={
            FormType.SET_IN_PLACE: [
                SectionTemplate(
                    name="General Information",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify equipment tag matches drawings", "Tag matches design documents"),
                        CheckItemTemplate("Verify unit location per drawings", "Location correct"),
                        CheckItemTemplate("Verify unit orientation correct", "Orientation per design"),
                        CheckItemTemplate("Verify mounting/support adequate", "Mounting secure and level"),
                    ]
                ),
                SectionTemplate(
                    name="Physical Inspection",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Inspect for shipping damage", "No visible damage"),
                        CheckItemTemplate("Verify all components present", "All components accounted for"),
                        CheckItemTemplate("Check coil fins for damage", "Fins straight, no damage"),
                        CheckItemTemplate("Verify drain pan installed correctly", "Drain pan properly pitched"),
                    ]
                ),
                SectionTemplate(
                    name="Piping Connections",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Verify chilled water supply connection", "Connection complete and leak-free"),
                        CheckItemTemplate("Verify chilled water return connection", "Connection complete and leak-free"),
                        CheckItemTemplate("Verify condensate drain connection", "Drain properly connected and trapped"),
                    ]
                ),
            ],
            FormType.CEV: [
                SectionTemplate(
                    name="Pre-Commissioning Checks",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify power supply connected", "Power available at rated voltage"),
                        CheckItemTemplate("Verify control wiring complete", "All control wiring terminated"),
                        CheckItemTemplate("Check motor rotation direction", "Rotation correct per arrow"),
                    ]
                ),
                SectionTemplate(
                    name="Functional Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Test fan operation at minimum speed", "Fan operates smoothly"),
                        CheckItemTemplate("Test fan operation at maximum speed", "Fan operates smoothly"),
                        CheckItemTemplate("Verify airflow direction", "Airflow in correct direction"),
                        CheckItemTemplate("Test control valve operation", "Valve strokes full range"),
                        CheckItemTemplate("Verify BMS communication", "All points reading correctly"),
                    ]
                ),
                SectionTemplate(
                    name="Setpoint Verification",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Verify supply air temperature setpoint", "Setpoint matches design", response_type="number"),
                        CheckItemTemplate("Verify fan speed setpoint", "Speed setpoint correct", response_type="number"),
                        CheckItemTemplate("Test high temperature alarm", "Alarm activates at setpoint"),
                        CheckItemTemplate("Test low temperature alarm", "Alarm activates at setpoint"),
                    ]
                ),
            ],
        }
    )


def get_cdu_template() -> EquipmentTemplate:
    """Get Coolant Distribution Unit template."""
    return EquipmentTemplate(
        spec_code="238123",
        equipment_type="CoolantDistributionUnit",
        display_name="Coolant Distribution Unit (CDU)",
        form_types=[FormType.SET_IN_PLACE, FormType.MANUFACTURER_PRESTARTUP, FormType.CEV],
        sections={
            FormType.CEV: [
                SectionTemplate(
                    name="Pump Verification",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify pump rotation direction", "Rotation correct"),
                        CheckItemTemplate("Test pump operation", "Pump operates smoothly"),
                        CheckItemTemplate("Verify pump VFD operation", "VFD responds to commands"),
                        CheckItemTemplate("Check pump vibration levels", "Vibration within limits", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Temperature Control",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Verify supply temperature setpoint", "Setpoint matches design", response_type="number"),
                        CheckItemTemplate("Test mixing valve operation", "Valve modulates correctly"),
                        CheckItemTemplate("Test high temperature alarm", "Alarm at correct setpoint"),
                        CheckItemTemplate("Test low temperature alarm", "Alarm at correct setpoint"),
                    ]
                ),
            ],
        }
    )


def get_rdb_template() -> EquipmentTemplate:
    """Get Row Distribution Board template."""
    return EquipmentTemplate(
        spec_code="260401",
        equipment_type="RowDistributionBoard",
        display_name="Row Distribution Board (RDB)",
        form_types=[FormType.IEV, FormType.SET_IN_PLACE, FormType.PRE_ENERGIZATION, FormType.CEV],
        sections={
            FormType.PRE_ENERGIZATION: [
                SectionTemplate(
                    name="Pre-Energization Checklist",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify all connections torqued", "Torque values recorded"),
                        CheckItemTemplate("Check for debris/foreign objects", "Interior clean"),
                        CheckItemTemplate("Verify breaker positions (OFF)", "All breakers OFF"),
                        CheckItemTemplate("Check bus bar connections", "Connections tight"),
                    ]
                ),
                SectionTemplate(
                    name="Insulation Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Megger test - Phase A to Ground", "IR acceptable", response_type="number"),
                        CheckItemTemplate("Megger test - Phase B to Ground", "IR acceptable", response_type="number"),
                        CheckItemTemplate("Megger test - Phase C to Ground", "IR acceptable", response_type="number"),
                    ]
                ),
            ],
            FormType.CEV: [
                SectionTemplate(
                    name="Energization Verification",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify incoming voltage", "Voltage within tolerance", response_type="number"),
                        CheckItemTemplate("Check phase rotation", "Rotation correct"),
                        CheckItemTemplate("Verify metering accuracy", "Meters reading correctly"),
                        CheckItemTemplate("Test breaker operation", "Breakers trip/close correctly"),
                    ]
                ),
            ],
        }
    )


def get_ats_template() -> EquipmentTemplate:
    """Get Automatic Transfer Switch template."""
    return EquipmentTemplate(
        spec_code="260627",
        equipment_type="AutomaticTransferSwitch",
        display_name="Automatic Transfer Switch (ATS)",
        form_types=[FormType.CEV, FormType.FPT],
        sections={
            FormType.CEV: [
                SectionTemplate(
                    name="Functional Testing",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Test transfer to emergency", "Transfer completes"),
                        CheckItemTemplate("Verify transfer time", "Within specification", response_type="number"),
                        CheckItemTemplate("Test retransfer to normal", "Retransfer completes"),
                        CheckItemTemplate("Test manual transfer operation", "Manual transfer functions"),
                    ]
                ),
                SectionTemplate(
                    name="Alarm Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Test normal source failure alarm", "Alarm activates"),
                        CheckItemTemplate("Test emergency source failure alarm", "Alarm activates"),
                        CheckItemTemplate("Test transfer failure alarm", "Alarm activates"),
                    ]
                ),
            ],
            FormType.FPT: [
                SectionTemplate(
                    name="Pre-Test Verification",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify normal source available", "Normal source energized"),
                        CheckItemTemplate("Verify emergency source available", "Emergency source ready"),
                        CheckItemTemplate("Confirm load connected", "Load verified"),
                        CheckItemTemplate("Review previous test results", "Previous tests reviewed"),
                    ]
                ),
                SectionTemplate(
                    name="Transfer Performance Test",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Simulate normal source failure", "Source failure simulated"),
                        CheckItemTemplate("Record transfer initiation time", "Time recorded", response_type="number"),
                        CheckItemTemplate("Verify emergency source starts", "Generator/UPS starts"),
                        CheckItemTemplate("Record total transfer time", "Transfer time acceptable", response_type="number"),
                        CheckItemTemplate("Verify load maintained during transfer", "No load interruption beyond spec"),
                        CheckItemTemplate("Verify ATS position indication", "Position correct on BMS"),
                    ]
                ),
                SectionTemplate(
                    name="Retransfer Performance Test",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Restore normal source", "Normal source restored"),
                        CheckItemTemplate("Verify time delay before retransfer", "Delay per specification", response_type="number"),
                        CheckItemTemplate("Record retransfer time", "Retransfer time acceptable", response_type="number"),
                        CheckItemTemplate("Verify load maintained during retransfer", "No load interruption"),
                        CheckItemTemplate("Verify emergency source shutdown sequence", "Proper cooldown cycle"),
                    ]
                ),
            ],
        }
    )


def get_generator_template() -> EquipmentTemplate:
    """Get Diesel Generator template."""
    return EquipmentTemplate(
        spec_code="260620",
        equipment_type="DieselGenerator",
        display_name="Diesel Generator",
        form_types=[FormType.CEV, FormType.FPT_PART_1, FormType.FPT_PART_2],
        sections={
            FormType.FPT_PART_1: [
                SectionTemplate(
                    name="Pre-Start Checks",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify fuel level", "Fuel at required level", response_type="number"),
                        CheckItemTemplate("Check coolant level", "Coolant at proper level"),
                        CheckItemTemplate("Verify oil level", "Oil at proper level"),
                        CheckItemTemplate("Check battery voltage", "Battery voltage acceptable", response_type="number"),
                        CheckItemTemplate("Inspect for leaks", "No leaks detected"),
                    ]
                ),
                SectionTemplate(
                    name="Start Sequence Test",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Initiate remote start command", "Start command sent"),
                        CheckItemTemplate("Record cranking time", "Cranking time within spec", response_type="number"),
                        CheckItemTemplate("Verify engine starts", "Engine running"),
                        CheckItemTemplate("Record time to rated speed", "Speed ramp acceptable", response_type="number"),
                        CheckItemTemplate("Record time to rated voltage", "Voltage ramp acceptable", response_type="number"),
                    ]
                ),
            ],
            FormType.FPT_PART_2: [
                SectionTemplate(
                    name="Load Bank Test",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Apply 25% load", "Load applied"),
                        CheckItemTemplate("Record voltage and frequency at 25%", "Parameters stable", response_type="number"),
                        CheckItemTemplate("Apply 50% load", "Load applied"),
                        CheckItemTemplate("Record voltage and frequency at 50%", "Parameters stable", response_type="number"),
                        CheckItemTemplate("Apply 75% load", "Load applied"),
                        CheckItemTemplate("Record voltage and frequency at 75%", "Parameters stable", response_type="number"),
                        CheckItemTemplate("Apply 100% load", "Load applied"),
                        CheckItemTemplate("Record voltage and frequency at 100%", "Parameters stable", response_type="number"),
                        CheckItemTemplate("Verify governor response", "Frequency stable under load changes"),
                    ]
                ),
                SectionTemplate(
                    name="Alarm Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Test low oil pressure alarm", "Alarm activates"),
                        CheckItemTemplate("Test high coolant temperature alarm", "Alarm activates"),
                        CheckItemTemplate("Test overspeed shutdown", "Shutdown activates", priority="Critical"),
                        CheckItemTemplate("Test emergency stop", "E-stop functions", priority="Critical"),
                    ]
                ),
            ],
        }
    )


def get_ups_template() -> EquipmentTemplate:
    """Get UPS template."""
    return EquipmentTemplate(
        spec_code="260614",
        equipment_type="UninterruptiblePowerSupply",
        display_name="Uninterruptible Power Supply (UPS)",
        form_types=[FormType.CEV, FormType.FPT_PART_1, FormType.FPT_PART_2],
        sections={
            FormType.FPT_PART_1: [
                SectionTemplate(
                    name="Normal Operation Test",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify input voltage", "Voltage within range", response_type="number"),
                        CheckItemTemplate("Verify output voltage", "Voltage within spec", response_type="number"),
                        CheckItemTemplate("Verify output frequency", "Frequency stable", response_type="number"),
                        CheckItemTemplate("Record load percentage", "Load recorded", response_type="number"),
                        CheckItemTemplate("Verify battery float voltage", "Float voltage correct", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Battery Discharge Test",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Simulate utility failure", "Utility disconnected"),
                        CheckItemTemplate("Verify transfer to battery", "Transfer seamless"),
                        CheckItemTemplate("Record transfer time", "Transfer time within spec", response_type="number"),
                        CheckItemTemplate("Monitor battery voltage during discharge", "Voltage recorded", response_type="number"),
                        CheckItemTemplate("Verify runtime at current load", "Runtime meets spec", response_type="number"),
                    ]
                ),
            ],
            FormType.FPT_PART_2: [
                SectionTemplate(
                    name="Bypass Operation Test",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Test manual bypass transfer", "Transfer successful"),
                        CheckItemTemplate("Verify load on bypass", "Load maintained"),
                        CheckItemTemplate("Test return from bypass", "Return successful"),
                        CheckItemTemplate("Test automatic bypass on UPS fault", "Auto-bypass functions"),
                    ]
                ),
                SectionTemplate(
                    name="Alarm Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Test on battery alarm", "Alarm activates"),
                        CheckItemTemplate("Test low battery alarm", "Alarm activates"),
                        CheckItemTemplate("Test overload alarm", "Alarm activates"),
                        CheckItemTemplate("Test UPS fault alarm", "Alarm activates"),
                        CheckItemTemplate("Verify BMS alarm integration", "Alarms received at BMS"),
                    ]
                ),
            ],
        }
    )


def get_mv_switch_template() -> EquipmentTemplate:
    """Get Medium Voltage Switch template."""
    return EquipmentTemplate(
        spec_code="260310",
        equipment_type="MediumVoltageSwitch",
        display_name="Medium Voltage Switch",
        form_types=[FormType.CEV, FormType.FPT],
        sections={
            FormType.FPT: [
                SectionTemplate(
                    name="Pre-Test Verification",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Verify switch position indicators", "Indicators correct"),
                        CheckItemTemplate("Verify interlock operation", "Interlocks functional"),
                        CheckItemTemplate("Check protective relay settings", "Settings per coordination study"),
                        CheckItemTemplate("Verify grounding", "Grounding verified"),
                    ]
                ),
                SectionTemplate(
                    name="Switching Operations",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Test local open operation", "Switch opens"),
                        CheckItemTemplate("Test local close operation", "Switch closes"),
                        CheckItemTemplate("Test remote open operation", "Remote open successful"),
                        CheckItemTemplate("Test remote close operation", "Remote close successful"),
                        CheckItemTemplate("Record operation time", "Time within spec", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Protection Testing",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Test overcurrent protection", "Protection operates"),
                        CheckItemTemplate("Test ground fault protection", "Protection operates"),
                        CheckItemTemplate("Test arc flash detection (if equipped)", "Detection operates"),
                        CheckItemTemplate("Verify trip-free operation", "Trip-free verified"),
                    ]
                ),
            ],
        }
    )


def get_battery_template() -> EquipmentTemplate:
    """Get VRLA Battery template."""
    return EquipmentTemplate(
        spec_code="260613",
        equipment_type="VRLABatteries",
        display_name="VRLA Battery System",
        form_types=[FormType.CEV, FormType.FPT],
        sections={
            FormType.FPT: [
                SectionTemplate(
                    name="Visual Inspection",
                    display_order=1,
                    items=[
                        CheckItemTemplate("Check for swelling or damage", "No damage observed"),
                        CheckItemTemplate("Verify terminal connections tight", "Connections secure"),
                        CheckItemTemplate("Check for electrolyte leaks", "No leaks detected"),
                        CheckItemTemplate("Verify ventilation adequate", "Ventilation adequate"),
                    ]
                ),
                SectionTemplate(
                    name="Electrical Testing",
                    display_order=2,
                    items=[
                        CheckItemTemplate("Measure float voltage (string)", "Float voltage correct", response_type="number"),
                        CheckItemTemplate("Measure individual cell voltages", "Cell voltages balanced", response_type="number"),
                        CheckItemTemplate("Record ambient temperature", "Temperature within range", response_type="number"),
                        CheckItemTemplate("Perform impedance test", "Impedance acceptable", response_type="number"),
                    ]
                ),
                SectionTemplate(
                    name="Discharge Test",
                    display_order=3,
                    items=[
                        CheckItemTemplate("Record initial voltage", "Voltage recorded", response_type="number"),
                        CheckItemTemplate("Apply test load", "Load applied"),
                        CheckItemTemplate("Monitor discharge curve", "Curve acceptable"),
                        CheckItemTemplate("Record end voltage", "End voltage recorded", response_type="number"),
                        CheckItemTemplate("Calculate capacity", "Capacity meets spec", response_type="number"),
                    ]
                ),
            ],
        }
    )


# Equipment Template Registry
EQUIPMENT_TEMPLATES = {
    "MUA": get_mua_template,
    "MakeupAirUnit": get_mua_template,
    "FCU": get_fcu_template,
    "FanCoilAssembly": get_fcu_template,
    "FanCoilUnit": get_fcu_template,
    "CDU": get_cdu_template,
    "CoolantDistributionUnit": get_cdu_template,
    "RDB": get_rdb_template,
    "RowDistributionBoard": get_rdb_template,
    "RSB": get_rdb_template,
    "RowSwitchBoard": get_rdb_template,
    "ATS": get_ats_template,
    "AutomaticTransferSwitch": get_ats_template,
    "Generator": get_generator_template,
    "DieselGenerator": get_generator_template,
    "UPS": get_ups_template,
    "UninterruptiblePowerSupply": get_ups_template,
    "MVS": get_mv_switch_template,
    "MediumVoltageSwitch": get_mv_switch_template,
    "Battery": get_battery_template,
    "VRLABatteries": get_battery_template,
}


def get_template(equipment_type: str) -> Optional[EquipmentTemplate]:
    """Get equipment template by type name."""
    template_func = EQUIPMENT_TEMPLATES.get(equipment_type)
    if template_func:
        return template_func()
    return None


def list_equipment_types() -> list:
    """List all available equipment types."""
    return list(set(EQUIPMENT_TEMPLATES.keys()))


# =============================================================================
# RSB TEMPLATE INTEGRATION (Based on Query 4 Production Data)
# =============================================================================

def get_rsb_template_advanced(
    level: str = "L3",
    form_type: str = "BMS",
    area: str = None,
    number: str = None,
    variant: str = None
) -> Optional[EquipmentTemplate]:
    """Get advanced RSB template with parameterized equipment identification.

    This uses the production form data patterns from Query 4 results to generate
    accurate RSB forms with proper response types and presets.

    Args:
        level: Commissioning level (L3 or L4)
        form_type: Type of form (BMS, FPT, CEV, Cable, LCO3)
        area: Area code (ERA, ERB, ERC, ERD, DHA, etc.)
        number: Equipment number (01-40, R1, R2)
        variant: Equipment variant (KND1, TTX1, UCO2, LCO1, etc.)

    Returns:
        EquipmentTemplate configured for the specified RSB form

    Examples:
        >>> template = get_rsb_template_advanced("L3", "BMS", "ERA", "03", "KND1")
        >>> template = get_rsb_template_advanced("L4", "FPT")
        >>> template = get_rsb_template_advanced("L4", "CEV")
    """
    try:
        from .rsb_templates import (
            RSBTemplateFactory,
            convert_template_to_form_sections,
            get_rsb_l4_fpt_template,
            get_rsb_l4_cev_template,
            get_rsb_l4_cable_template,
            get_rsb_l4_lco3_template,
        )

        if level == "L4":
            template_funcs = {
                "FPT": get_rsb_l4_fpt_template,
                "CEV": get_rsb_l4_cev_template,
                "Cable": get_rsb_l4_cable_template,
                "LCO3": get_rsb_l4_lco3_template,
            }
            rsb_template = template_funcs.get(form_type, get_rsb_l4_fpt_template)()
        else:
            area = area or "ERA"
            number = number or "01"
            variant = variant or "KND1"
            rsb_template = RSBTemplateFactory.create_l3_template(area, number, variant)

        sections_data = convert_template_to_form_sections(rsb_template)

        sections = []
        for idx, section_data in enumerate(sections_data, start=1):
            items = []
            for item_data in section_data.get("items", []):
                response_type = item_data.get("response_type", "choice")
                if response_type == "toggle":
                    response_type = "choice"

                items.append(CheckItem(
                    description=item_data["description"],
                    acceptance_criteria=item_data.get("acceptance_criteria", "Pass"),
                    response_type=response_type,
                    priority=item_data.get("priority", "Medium"),
                ))

            sections.append(Section(
                name=section_data["name"],
                display_name=section_data.get("display_name", section_data["name"]),
                display_order=section_data.get("order", idx),
                items=items,
            ))

        return EquipmentTemplate(
            equipment_type="RSB",
            display_name=rsb_template.display_name,
            spec_code="260401",
            level=level,
            sections=sections,
        )
    except ImportError:
        return get_rdb_template()


def list_rsb_variants() -> list:
    """List available RSB equipment variants from production data."""
    try:
        from .rsb_templates import RSB_VARIANTS
        return list(RSB_VARIANTS.keys())
    except ImportError:
        return ["KND1", "TTX1", "UCO2", "LCO1", "LCO2", "RMN1", "MCA1", "RIN1"]


def list_rsb_areas() -> list:
    """List available RSB area codes from production data."""
    try:
        from .rsb_templates import AREA_CODES
        return list(AREA_CODES.keys())
    except ImportError:
        return ["ERA", "ERB", "ERC", "ERD", "DHA"]


def list_rsb_form_types() -> dict:
    """List available RSB form types with descriptions."""
    return {
        "L3": {
            "BMS": "Combined BMS form for equipment instance",
        },
        "L4": {
            "FPT": "Functional Performance Test (24,892 uses)",
            "CEV": "Commissioning Equipment Verification (45,770 uses)",
            "Cable": "Cable FPT (5,358 uses)",
            "LCO3": "LCO3 Line Circuit (8,160 uses)",
        }
    }

