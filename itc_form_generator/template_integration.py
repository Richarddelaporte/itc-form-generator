"""Template Integration Module - Integrates production templates with SOO-based form generation.

This module bridges the production templates (RSB, ATS, etc.) with the
SOO-based form generator, allowing forms generated from SOO documents
to be enhanced with production-validated check items.

The integration works by:
1. Detecting equipment type from SOO system name/tag
2. Loading matching template sections
3. Merging template check items with generated items
4. Prioritizing production-validated items (higher frequency = higher priority)
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TemplateCheckItem:
    """Check item from production template."""
    description: str
    response_type: str = "toggle"
    presets: str = "No/Yes/NA"
    acceptance_criteria: str = "Pass"
    priority: str = "Medium"
    frequency: int = 0
    source_template: str = ""


@dataclass
class TemplateSection:
    """Section from production template."""
    name: str
    display_name: str
    order: int
    items: List[TemplateCheckItem] = field(default_factory=list)
    usage_count: int = 0


# Equipment type detection patterns
EQUIPMENT_PATTERNS = {
    "RSB": {
        "keywords": ["rsb", "row switch board", "rowswitchboard", "row switchboard"],
        "tags": ["RSB", "RSB-"],
        "spec_codes": ["260000", "260401"],
    },
    "ATS": {
        "keywords": ["ats", "automatic transfer switch", "transfer switch", "autotransfer"],
        "tags": ["ATS", "ATS-"],
        "spec_codes": ["260627", "213113"],
    },
    "RDB": {
        "keywords": ["rdb", "row distribution board", "distribution board"],
        "tags": ["RDB", "RDB-"],
        "spec_codes": ["260000"],
    },
    "UPS": {
        "keywords": ["ups", "uninterruptible power", "battery backup"],
        "tags": ["UPS", "UPS-"],
        "spec_codes": ["262000"],
    },
    "Generator": {
        "keywords": ["generator", "genset", "diesel generator", "standby generator"],
        "tags": ["GEN", "GEN-", "DG-"],
        "spec_codes": ["263000"],
    },
    "MVS": {
        "keywords": ["mvs", "medium voltage", "mv switch", "switchgear"],
        "tags": ["MVS", "MVS-", "SWG-"],
        "spec_codes": ["261000"],
    },
}


def detect_equipment_type(system_name: str, system_tag: str = "", spec_code: str = "") -> Optional[str]:
    """Detect equipment type from system name, tag, or spec code.

    Args:
        system_name: Name of the system (e.g., "ERA - RSB - 03")
        system_tag: Equipment tag (e.g., "RSB-03")
        spec_code: CSI spec code (e.g., "260627")

    Returns:
        Equipment type string (e.g., "RSB", "ATS") or None
    """
    name_lower = system_name.lower()
    tag_upper = system_tag.upper() if system_tag else ""

    for equip_type, patterns in EQUIPMENT_PATTERNS.items():
        # Check spec code first (most specific)
        if spec_code:
            for code in patterns["spec_codes"]:
                if spec_code.startswith(code):
                    logger.debug(f"Matched {equip_type} by spec code {code}")
                    return equip_type

        # Check keywords in name
        for keyword in patterns["keywords"]:
            if keyword in name_lower:
                logger.debug(f"Matched {equip_type} by keyword '{keyword}'")
                return equip_type

        # Check tag patterns
        for tag_pattern in patterns["tags"]:
            if tag_upper.startswith(tag_pattern) or tag_pattern in tag_upper:
                logger.debug(f"Matched {equip_type} by tag pattern '{tag_pattern}'")
                return equip_type

    return None


def extract_equipment_details(system_name: str) -> Dict[str, str]:
    """Extract equipment details from naming convention.

    Naming convention: {SpecCode}_{Level}_{EquipmentType}_{Area} - {Type} - {ID}_{Variant}
    Example: 260627_L3_Automatic Transfer Switch_ERA - ATS - FCA-3_KND1_Rev0_CombinedBMS

    Returns:
        Dict with keys: area, identifier, variant, level
    """
    details = {
        "area": "",
        "identifier": "",
        "variant": "",
        "level": "L3",
    }

    # Try to extract from structured name
    parts = system_name.split("_")

    # Look for level (L2, L3, L4, etc.)
    for part in parts:
        if part.upper() in ["L2", "L2C", "L3", "L4", "L4C"]:
            details["level"] = part.upper()
            break

    # Look for area codes (ERA, ERB, etc.)
    area_patterns = ["ERA", "ERB", "ERC", "ERD", "DHA", "DHB", "DHC", "DHD",
                     "ERN1", "ERN2", "ERN3", "ERN4", "UPSA", "UPSB", "UPSC", "UPSD",
                     "EY1", "EY2", "SUB1", "SUB2", "IWM", "SSB"]

    for part in parts:
        part_upper = part.upper().split(" - ")[0] if " - " in part else part.upper()
        for area in area_patterns:
            if area in part_upper:
                details["area"] = area
                break
        if details["area"]:
            break

    # Look for variant (KND1, TTX1, UCO2, etc.)
    variant_patterns = ["KND1", "TTX1", "TTX2", "UCO1", "UCO2", "LCO1", "LCO2",
                        "RMN1", "MCA1", "MCA2", "MAL1", "MAL2", "SNB5", "SNB6",
                        "GTN5", "GTN6", "RIN", "RIN1", "CHY1"]

    for part in parts:
        part_upper = part.upper()
        for variant in variant_patterns:
            if variant in part_upper:
                details["variant"] = variant
                break
        if details["variant"]:
            break

    # Look for identifier (FCA-1, CDU-3, H1, etc.)
    import re
    id_patterns = [
        r"(FCA-\d+)",
        r"(CDU-\d+)",
        r"(H\d+)",
        r"(N\d+)",
        r"(\d{2})",  # Two digit number like 03
    ]

    for part in parts:
        for pattern in id_patterns:
            match = re.search(pattern, part.upper())
            if match:
                details["identifier"] = match.group(1)
                break
        if details["identifier"]:
            break

    return details


class TemplateIntegrator:
    """Integrates production templates with form generation."""

    def __init__(self):
        self._rsb_templates = None
        self._ats_templates = None
        self._loaded = False

    def _load_templates(self):
        """Lazy load template modules."""
        if self._loaded:
            return

        try:
            from . import rsb_templates
            self._rsb_templates = rsb_templates
            logger.info("Loaded RSB templates")
        except ImportError as e:
            logger.warning(f"Could not load RSB templates: {e}")

        try:
            from . import ats_templates
            self._ats_templates = ats_templates
            logger.info("Loaded ATS templates")
        except ImportError as e:
            logger.warning(f"Could not load ATS templates: {e}")

        self._loaded = True

    def get_template_sections(
        self,
        equipment_type: str,
        level: str = "L3",
        **kwargs
    ) -> List[TemplateSection]:
        """Get template sections for an equipment type.

        Args:
            equipment_type: Type of equipment (RSB, ATS, etc.)
            level: Commissioning level (L2, L3, L4, etc.)
            **kwargs: Additional parameters (area, variant, identifier, category, form_type)

        Returns:
            List of TemplateSection with production-validated check items
        """
        self._load_templates()

        sections = []

        if equipment_type == "RSB" and self._rsb_templates:
            sections = self._get_rsb_sections(level, **kwargs)
        elif equipment_type == "ATS" and self._ats_templates:
            sections = self._get_ats_sections(level, **kwargs)

        return sections

    def _get_rsb_sections(self, level: str, **kwargs) -> List[TemplateSection]:
        """Get RSB template sections."""
        sections = []

        try:
            if level in ["L4", "L4C"]:
                form_type = kwargs.get("form_type", "CEV")
                template = self._rsb_templates.RSBTemplateFactory.create_l4_template(form_type)
            else:
                area = kwargs.get("area", "ERA")
                number = kwargs.get("number", kwargs.get("identifier", "01"))
                variant = kwargs.get("variant", "KND1")
                template = self._rsb_templates.RSBTemplateFactory.create_l3_template(area, number, variant)

            for rsb_section in template.sections:
                items = []
                for rsb_item in rsb_section.items:
                    items.append(TemplateCheckItem(
                        description=rsb_item.description,
                        response_type=rsb_item.response_type.value,
                        presets=rsb_item.presets.value if hasattr(rsb_item.presets, 'value') else str(rsb_item.presets),
                        acceptance_criteria=rsb_item.acceptance_criteria,
                        priority=rsb_item.priority,
                        frequency=rsb_item.frequency,
                        source_template=f"RSB-{level}",
                    ))

                sections.append(TemplateSection(
                    name=rsb_section.name,
                    display_name=rsb_section.display_name,
                    order=rsb_section.section_order,
                    items=items,
                    usage_count=rsb_section.usage_count,
                ))
        except Exception as e:
            logger.error(f"Error loading RSB sections: {e}")

        return sections

    def _get_ats_sections(self, level: str, **kwargs) -> List[TemplateSection]:
        """Get ATS template sections."""
        sections = []

        try:
            if level in ["L4", "L4C"]:
                category = kwargs.get("category", "FCA")
                template = self._ats_templates.ATSTemplateFactory.create_l4_template(category)
            elif level == "L2C":
                template = self._ats_templates.ATSTemplateFactory.create_l2c_template()
            elif level == "L2":
                template = self._ats_templates.ATSTemplateFactory.create_site_arrival_template()
            else:
                area = kwargs.get("area", "ERA")
                identifier = kwargs.get("identifier", "FCA-1")
                variant = kwargs.get("variant", "KND1")
                template = self._ats_templates.ATSTemplateFactory.create_l3_template(area, identifier, variant)

            for ats_section in template.sections:
                items = []
                for ats_item in ats_section.items:
                    items.append(TemplateCheckItem(
                        description=ats_item.description,
                        response_type=ats_item.response_type.value,
                        presets=ats_item.presets.value if hasattr(ats_item.presets, 'value') else str(ats_item.presets),
                        acceptance_criteria=ats_item.acceptance_criteria,
                        priority=ats_item.priority,
                        frequency=ats_item.frequency,
                        source_template=f"ATS-{level}",
                    ))

                sections.append(TemplateSection(
                    name=ats_section.name,
                    display_name=ats_section.display_name,
                    order=ats_section.section_order,
                    items=items,
                    usage_count=ats_section.usage_count,
                ))
        except Exception as e:
            logger.error(f"Error loading ATS sections: {e}")

        return sections

    def get_matching_check_items(
        self,
        equipment_type: str,
        section_name: str,
        level: str = "L3",
        **kwargs
    ) -> List[TemplateCheckItem]:
        """Get check items for a specific section from templates.

        Args:
            equipment_type: Type of equipment (RSB, ATS, etc.)
            section_name: Name of section to match (fuzzy matching)
            level: Commissioning level
            **kwargs: Additional parameters

        Returns:
            List of matching TemplateCheckItem
        """
        sections = self.get_template_sections(equipment_type, level, **kwargs)

        # Fuzzy match section name
        section_lower = section_name.lower()
        matching_items = []

        for section in sections:
            section_name_lower = section.name.lower()
            section_display_lower = section.display_name.lower()

            # Check for keyword matches
            if (section_lower in section_name_lower or
                section_name_lower in section_lower or
                section_lower in section_display_lower or
                section_display_lower in section_lower):
                matching_items.extend(section.items)
                continue

            # Check for common section name mappings
            section_mappings = {
                "safety": ["procedure", "safety", "personnel"],
                "documentation": ["documentation", "submittal", "review"],
                "functional": ["functional", "test", "performance"],
                "bms": ["bms", "epms", "point", "verification"],
                "installation": ["installation", "wiring", "termination"],
                "energization": ["energization", "pre-energization", "voltage"],
                "end of test": ["end of test", "completion", "final"],
                "equipment": ["equipment", "identification", "designation"],
                "alert": ["alert", "alarm", "notification"],
            }

            for keyword, matches in section_mappings.items():
                if any(m in section_lower for m in matches):
                    if any(m in section_name_lower or m in section_display_lower for m in matches):
                        matching_items.extend(section.items)
                        break

        # Sort by frequency (higher frequency = more validated)
        matching_items.sort(key=lambda x: x.frequency, reverse=True)

        return matching_items

    def enhance_form_with_templates(
        self,
        system_name: str,
        system_tag: str = "",
        existing_sections: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Enhance a form with template-based check items.

        Args:
            system_name: Name of the system from SOO
            system_tag: Equipment tag
            existing_sections: Existing sections from SOO-based generation

        Returns:
            Dict with:
                - equipment_type: Detected equipment type
                - template_sections: List of template sections to add/merge
                - enhanced_items: Dict mapping section name to additional items
                - details: Extracted equipment details
        """
        equipment_type = detect_equipment_type(system_name, system_tag)

        if not equipment_type:
            return {
                "equipment_type": None,
                "template_sections": [],
                "enhanced_items": {},
                "details": {},
            }

        details = extract_equipment_details(system_name)
        template_sections = self.get_template_sections(
            equipment_type,
            level=details.get("level", "L3"),
            area=details.get("area", ""),
            identifier=details.get("identifier", ""),
            variant=details.get("variant", ""),
        )

        # Map existing sections to template enhancements
        enhanced_items = {}
        if existing_sections:
            for section in existing_sections:
                section_name = section.get("name", section.get("title", ""))
                items = self.get_matching_check_items(
                    equipment_type,
                    section_name,
                    level=details.get("level", "L3"),
                    **details,
                )
                if items:
                    enhanced_items[section_name] = items

        return {
            "equipment_type": equipment_type,
            "template_sections": template_sections,
            "enhanced_items": enhanced_items,
            "details": details,
        }


# Singleton instance
_integrator = None


def get_template_integrator() -> TemplateIntegrator:
    """Get singleton template integrator instance."""
    global _integrator
    if _integrator is None:
        _integrator = TemplateIntegrator()
    return _integrator


def get_template_items_for_system(
    system_name: str,
    system_tag: str = "",
    section_name: str = None,
) -> List[TemplateCheckItem]:
    """Convenience function to get template items for a system.

    Args:
        system_name: Name of the system
        system_tag: Equipment tag
        section_name: Optional section name to filter items

    Returns:
        List of TemplateCheckItem from matching templates
    """
    integrator = get_template_integrator()
    equipment_type = detect_equipment_type(system_name, system_tag)

    if not equipment_type:
        return []

    details = extract_equipment_details(system_name)

    if section_name:
        return integrator.get_matching_check_items(
            equipment_type,
            section_name,
            level=details.get("level", "L3"),
            **details,
        )
    else:
        sections = integrator.get_template_sections(
            equipment_type,
            level=details.get("level", "L3"),
            **details,
        )
        all_items = []
        for section in sections:
            all_items.extend(section.items)
        return all_items

