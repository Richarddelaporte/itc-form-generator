"""Form generator - creates ITC forms from parsed SOO.

Generates detailed Procore-style commissioning checklists with:
- Header information (equipment, dates, personnel)
- Prerequisites and documentation verification
- Safety requirements and LOTO
- Equipment settings and firmware verification
- Visual inspections
- BMS/Graphics review
- Automated test reports
- Detailed functional tests

Enhanced with BMS Points List integration for:
- Specific sensor testing items per AI point
- Setpoint verification per AO point
- Status verification per DI point
- Control output testing per DO point

AI-Enhanced Features (when enabled):
- Context-aware check item generation
- Intelligent acceptance criteria
- Form completeness review

Feedback-Enhanced Features (always active):
- Learned check items from user feedback
- Patterns from example forms
"""

import logging
from typing import Optional
from .models import (
    SequenceOfOperation, System, Component, InspectionForm, FormSection,
    CheckItem, FormType, Priority, CheckItemType
)
from .points_parser import PointsList, ControlPoint, PointType

logger = logging.getLogger(__name__)


class FormGenerator:
    """Generates inspection and testing forms from parsed SOO.

    Supports optional AI enhancement for more specific, context-aware
    check items and acceptance criteria.

    Also applies learned patterns from feedback and example forms
    even without AI (MetaGen) being available.
    """

    def __init__(self, soo: SequenceOfOperation, points_list: Optional[PointsList] = None,
                 use_ai: bool = False, ai_service=None):
        """Initialize form generator.

        Args:
            soo: Parsed Sequence of Operation
            points_list: Optional BMS points list for enhanced forms
            use_ai: Whether to use AI for enhanced check items
            ai_service: AIService instance (created if None and use_ai=True)
        """
        self.soo = soo
        self.points_list = points_list
        self.item_counter = 0
        self.use_ai = use_ai
        self._ai_service = ai_service
        self._feedback_store = None
        self._example_store = None
        self._load_learning_stores()

    def _load_learning_stores(self):
        """Load feedback and example stores for learning."""
        try:
            from .feedback_store import get_feedback_store
            self._feedback_store = get_feedback_store()
            logger.info(f"Loaded feedback store with {self._feedback_store.get_stats()['total_entries']} entries")
        except Exception as e:
            logger.debug(f"Could not load feedback store: {e}")

        try:
            from .example_form_parser import get_example_store
            self._example_store = get_example_store()
            logger.info(f"Loaded example store with {self._example_store.get_stats()['total_examples']} examples")
        except Exception as e:
            logger.debug(f"Could not load example store: {e}")

        # Load feedback enhancer for generating specific check items
        self._feedback_enhancer = None
        try:
            from .feedback_enhancer import get_feedback_enhancer
            self._feedback_enhancer = get_feedback_enhancer()
            logger.info("Loaded feedback enhancer for improved check items")
        except Exception as e:
            logger.debug(f"Could not load feedback enhancer: {e}")

        # Load template integrator for production-validated check items
        self._template_integrator = None
        try:
            from .template_integration import get_template_integrator
            self._template_integrator = get_template_integrator()
            logger.info("Loaded template integrator for production-validated items")
        except Exception as e:
            logger.debug(f"Could not load template integrator: {e}")

    @property
    def ai_service(self):
        """Lazy initialization of AI service."""
        if self._ai_service is None and self.use_ai:
            try:
                from .ai_service import AIService
                self._ai_service = AIService()
                if not self._ai_service.is_available:
                    logger.warning("AI service not available, using template-based generation")
                    self.use_ai = False
            except ImportError:
                logger.warning("AI service not available, using template-based generation")
                self.use_ai = False
        return self._ai_service

    def _get_system_type(self, system: System) -> str:
        """Extract system type from system name/tag."""
        name_lower = system.name.lower()
        tag_upper = system.tag.upper() if system.tag else ""

        type_keywords = {
            'AHU': ['ahu', 'air handling', 'air handler'],
            'FCU': ['fcu', 'fan coil'],
            'VAV': ['vav', 'variable air volume'],
            'Chiller': ['chiller', 'ch-'],
            'Boiler': ['boiler', 'blr'],
            'Cooling Tower': ['cooling tower', 'ct-'],
            'Pump': ['pump', 'pmp'],
            'CRAH': ['crah', 'computer room'],
            'Data Hall': ['data hall', 'dh-', 'dhm'],
        }

        for sys_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in name_lower or kw.upper() in tag_upper:
                    return sys_type

        if tag_upper:
            return tag_upper.split('-')[0] if '-' in tag_upper else tag_upper[:3]
        return 'General'

    def _add_enhanced_items_to_section(self, section: FormSection, section_name: str, system: System) -> FormSection:
        """Add feedback-enhanced check items to a section.

        This injects specific check items generated from user feedback
        directly into the appropriate section.
        """
        if not self._feedback_enhancer:
            return section

        system_type = self._get_system_type(system)
        enhanced_items = self._feedback_enhancer.get_enhanced_items_for_section(section_name, system_type)

        if not enhanced_items:
            return section

        logger.info(f"Adding {len(enhanced_items)} enhanced items to section '{section_name}'")

        for item in enhanced_items:
            check_item = CheckItem(
                id=self._next_id("ENH"),
                description=item.description,
                check_type=self._map_check_type(item.check_type),
                priority=self._map_priority(item.priority),
                acceptance_criteria=item.acceptance_criteria,
                method=item.method,
                system_tag=system.tag
            )
            section.check_items.append(check_item)

        return section

    def _add_template_items_to_section(self, section: FormSection, section_name: str, system: System) -> FormSection:
        """Add production-validated check items from templates to a section.

        This integrates check items from RSB, ATS, and other production templates
        that have been validated through actual commissioning work.
        """
        if not self._template_integrator:
            return section

        try:
            from .template_integration import get_template_items_for_system

            template_items = get_template_items_for_system(
                system.name,
                system.tag or "",
                section_name
            )

            if not template_items:
                return section

            logger.info(f"Adding {len(template_items)} template items to section '{section_name}' for {system.name}")

            # Track existing descriptions to avoid duplicates
            existing_descriptions = {item.description.lower() for item in section.check_items}

            for item in template_items:
                # Skip if similar item already exists
                if item.description.lower() in existing_descriptions:
                    continue

                # Map priority from template
                priority = Priority.MEDIUM
                if item.priority.upper() == "CRITICAL":
                    priority = Priority.CRITICAL
                elif item.priority.upper() == "HIGH":
                    priority = Priority.HIGH
                elif item.priority.upper() == "LOW":
                    priority = Priority.LOW

                check_item = CheckItem(
                    id=self._next_id("TPL"),
                    description=item.description,
                    check_type=CheckItemType.VERIFICATION,
                    priority=priority,
                    acceptance_criteria=item.acceptance_criteria,
                    method=f"Response: {item.presets}" if item.presets else "",
                    system_tag=system.tag
                )
                section.check_items.append(check_item)
                existing_descriptions.add(item.description.lower())

        except Exception as e:
            logger.debug(f"Could not add template items: {e}")

        return section

    def _get_equipment_type_from_system(self, system: System) -> str:
        """Detect equipment type for template matching.

        Returns equipment type like 'RSB', 'ATS', or generic type.
        """
        try:
            from .template_integration import detect_equipment_type
            equip_type = detect_equipment_type(system.name, system.tag or "")
            if equip_type:
                return equip_type
        except Exception:
            pass

        return self._get_system_type(system)

    def _create_template_based_sections(self, system: System) -> list:
        """Create form sections based on production templates.

        For electrical equipment (RSB, ATS, etc.), this creates sections
        directly from production-validated templates.
        """
        sections = []

        if not self._template_integrator:
            return sections

        try:
            from .template_integration import detect_equipment_type, extract_equipment_details

            equip_type = detect_equipment_type(system.name, system.tag or "")
            if not equip_type:
                return sections

            details = extract_equipment_details(system.name)
            template_sections = self._template_integrator.get_template_sections(
                equip_type,
                level=details.get("level", "L3"),
                area=details.get("area", ""),
                identifier=details.get("identifier", ""),
                variant=details.get("variant", ""),
            )

            for tmpl_section in template_sections:
                section = FormSection(
                    title=tmpl_section.display_name,
                    description=f"Production-validated checks ({tmpl_section.usage_count:,} uses)"
                )

                for item in tmpl_section.items:
                    priority = Priority.MEDIUM
                    if item.priority.upper() == "CRITICAL":
                        priority = Priority.CRITICAL
                    elif item.priority.upper() == "HIGH":
                        priority = Priority.HIGH
                    elif item.priority.upper() == "LOW":
                        priority = Priority.LOW

                    check_item = CheckItem(
                        id=self._next_id("TPL"),
                        description=item.description,
                        check_type=CheckItemType.VERIFICATION,
                        priority=priority,
                        acceptance_criteria=item.acceptance_criteria,
                        method=f"Response options: {item.presets}" if item.presets else "",
                        system_tag=system.tag
                    )
                    section.check_items.append(check_item)

                if section.check_items:
                    sections.append(section)
                    logger.info(f"Created template section '{tmpl_section.display_name}' with {len(section.check_items)} items")

        except Exception as e:
            logger.warning(f"Could not create template sections: {e}")

        return sections

    def _create_end_of_test_section(self, system: System) -> FormSection:
        """Create End of Test section for commissioning completion.

        Returns template-based section if available, else creates default.
        """
        if self._template_integrator:
            try:
                from .template_integration import get_template_items_for_system

                items = get_template_items_for_system(
                    system.name,
                    system.tag or "",
                    "End of Test"
                )

                if items:
                    section = FormSection(
                        title="End of Test",
                        description="Commissioning completion verification"
                    )

                    for item in items:
                        priority = Priority.MEDIUM
                        if item.priority.upper() == "HIGH":
                            priority = Priority.HIGH

                        check_item = CheckItem(
                            id=self._next_id("EOT"),
                            description=item.description,
                            check_type=CheckItemType.VERIFICATION,
                            priority=priority,
                            acceptance_criteria=item.acceptance_criteria,
                            method="",
                            system_tag=system.tag
                        )
                        section.check_items.append(check_item)

                    return section
            except Exception as e:
                logger.debug(f"Could not create template End of Test section: {e}")

        # Default End of Test section
        section = FormSection(
            title="End of Test",
            description="Commissioning completion verification"
        )

        items = [
            ("All tests completed successfully", "All functional tests passed"),
            ("Punch list items resolved", "No outstanding issues"),
            ("Documentation package complete", "All required documents submitted"),
            ("Training completed", "Operations personnel trained"),
            ("System ready for occupancy/use", "System fully operational"),
        ]

        for desc, criteria in items:
            section.check_items.append(CheckItem(
                id=self._next_id("EOT"),
                description=desc,
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH,
                acceptance_criteria=criteria,
                system_tag=system.tag
            ))

        return section

    def _map_priority(self, priority_str: str) -> Priority:
        """Map string priority to enum."""
        priority_map = {
            'CRITICAL': Priority.CRITICAL,
            'HIGH': Priority.HIGH,
            'MEDIUM': Priority.MEDIUM,
            'LOW': Priority.LOW,
        }
        return priority_map.get(priority_str.upper(), Priority.MEDIUM)

    def _get_system_info(self, system: System) -> dict:
        """Convert System to dict for AI service."""
        return {
            'name': system.name,
            'tag': system.tag,
            'description': system.description,
            'components': [
                {'tag': c.tag, 'name': c.name, 'type': c.component_type}
                for c in system.components
            ],
            'setpoints': [
                {'name': s.name, 'value': s.value, 'units': s.units, 'adjustable': s.adjustable}
                for s in system.setpoints
            ],
            'operating_modes': [
                {'name': m.name, 'conditions': m.conditions, 'actions': m.actions}
                for m in system.operating_modes
            ],
            'interlocks': system.interlocks,
            'alarms': system.alarms
        }

    def _map_check_type(self, type_str: str) -> CheckItemType:
        """Map string check type to enum."""
        type_map = {
            'VISUAL': CheckItemType.VISUAL,
            'MEASUREMENT': CheckItemType.MEASUREMENT,
            'FUNCTIONAL': CheckItemType.FUNCTIONAL,
            'DOCUMENTATION': CheckItemType.DOCUMENTATION,
            'VERIFICATION': CheckItemType.VERIFICATION
        }
        return type_map.get(type_str.upper(), CheckItemType.VERIFICATION)

    def _map_priority(self, priority_str: str) -> Priority:
        """Map string priority to enum."""
        priority_map = {
            'CRITICAL': Priority.CRITICAL,
            'HIGH': Priority.HIGH,
            'MEDIUM': Priority.MEDIUM,
            'LOW': Priority.LOW
        }
        return priority_map.get(priority_str.upper(), Priority.MEDIUM)

    def _generate_ai_section(self, system: System, form_type: FormType) -> Optional[FormSection]:
        """Generate AI-enhanced check items section.

        Args:
            system: System to generate checks for
            form_type: Type of form being generated

        Returns:
            FormSection with AI-generated check items, or None if AI unavailable
        """
        if not self.use_ai or not self.ai_service:
            return None

        try:
            system_info = self._get_system_info(system)
            ai_items = self.ai_service.generate_check_items(system_info, form_type.value)

            if not ai_items:
                return None

            section = FormSection(
                title="AI-Enhanced Checks",
                description="Context-specific check items generated by AI analysis of system requirements"
            )

            for item in ai_items:
                check_item = CheckItem(
                    id=self._next_id("AI"),
                    description=item.get('description', ''),
                    check_type=self._map_check_type(item.get('check_type', 'VERIFICATION')),
                    priority=self._map_priority(item.get('priority', 'MEDIUM')),
                    acceptance_criteria=item.get('acceptance_criteria', ''),
                    method=item.get('method', ''),
                    expected_value=item.get('expected_value', ''),
                    system_tag=system.tag
                )
                section.check_items.append(check_item)

            logger.info(f"AI generated {len(section.check_items)} check items for {system.name}")
            return section

        except Exception as e:
            logger.error(f"Failed to generate AI section: {e}")
            return None

    def _enhance_check_item_with_ai(self, item: CheckItem, system: System) -> CheckItem:
        """Enhance a check item with AI-generated acceptance criteria.

        Args:
            item: Original check item
            system: System context

        Returns:
            Enhanced check item (or original if AI fails)
        """
        if not self.use_ai or not self.ai_service:
            return item

        try:
            context = f"System: {system.name} ({system.tag}), Setpoints: {[(s.name, s.value, s.units) for s in system.setpoints[:5]]}"
            enhanced = self.ai_service.enhance_check_item(item.description, context)

            if enhanced:
                if enhanced.get('acceptance_criteria'):
                    item.acceptance_criteria = enhanced['acceptance_criteria']
                if enhanced.get('method'):
                    item.method = enhanced['method']
                if enhanced.get('expected_value'):
                    item.expected_value = enhanced['expected_value']

            return item
        except Exception as e:
            logger.debug(f"AI enhancement failed: {e}")
            return item

    def review_form(self, form: InspectionForm) -> Optional[dict]:
        """Review form for completeness using AI.

        Args:
            form: Generated inspection form

        Returns:
            Review results with score, missing items, and suggestions
        """
        if not self.use_ai or not self.ai_service:
            return None

        try:
            form_summary = {
                'title': form.title,
                'system': form.system,
                'total_items': form.total_items,
                'sections': [s.title for s in form.sections]
            }

            # Get the matching system
            system = next((s for s in self.soo.systems if s.tag == form.system_tag or s.name == form.system), None)
            if not system:
                return None

            soo_summary = {
                'system_count': 1,
                'component_count': len(system.components),
                'setpoint_count': len(system.setpoints),
                'mode_count': len(system.operating_modes),
                'interlock_count': len(system.interlocks),
                'alarm_count': len(system.alarms)
            }

            return self.ai_service.review_form_completeness(form_summary, soo_summary)
        except Exception as e:
            logger.error(f"Form review failed: {e}")
            return None

    def _get_points_for_system(self, system: System) -> list[ControlPoint]:
        """Get control points matching this system's equipment."""
        if not self.points_list or not self.points_list.points:
            return []

        matching_points = []
        system_tag_upper = system.tag.upper() if system.tag else ""
        system_name_upper = system.name.upper() if system.name else ""

        for point in self.points_list.points:
            point_name_upper = point.point_name.upper()
            equip_ref_upper = point.equipment_ref.upper() if point.equipment_ref else ""
            system_ref_upper = point.system_ref.upper() if point.system_ref else ""

            # Match by equipment tag, system reference, or point name prefix
            if (system_tag_upper and (
                    equip_ref_upper == system_tag_upper or
                    system_ref_upper == system_tag_upper or
                    point_name_upper.startswith(system_tag_upper) or
                    system_tag_upper in point_name_upper)):
                matching_points.append(point)
            elif system_name_upper and system_ref_upper == system_name_upper:
                matching_points.append(point)

        return matching_points

    def _get_unmatched_points(self) -> list[ControlPoint]:
        """Get all points that don't match any system."""
        if not self.points_list or not self.points_list.points:
            return []

        # Collect all matched points across all systems
        all_matched = set()
        for system in self.soo.systems:
            for point in self._get_points_for_system(system):
                all_matched.add(point.point_name)

        # Return points not in matched set
        return [p for p in self.points_list.points if p.point_name not in all_matched]

    def _get_unmatched_points_by_type(self, point_type: PointType) -> list[ControlPoint]:
        """Get unmatched points of a specific type."""
        unmatched = self._get_unmatched_points()
        return [p for p in unmatched if p.point_type == point_type]

    def _get_points_by_type(self, system: System, point_type: PointType) -> list[ControlPoint]:
        """Get control points of a specific type for a system."""
        system_points = self._get_points_for_system(system)
        return [p for p in system_points if p.point_type == point_type]

    def generate_all_forms(self) -> list[InspectionForm]:
        """Generate a single combined form for each system."""
        forms = []
        for system in self.soo.systems:
            forms.append(self.generate_combined_form(system))
        return forms

    def generate_combined_form(self, system: System) -> InspectionForm:
        """Generate a single comprehensive ITC form combining all sections.

        This creates one form that includes:
        - Pre-Functional Inspection (PFI) sections
        - Functional Performance Test (FPT) sections
        - Integrated Systems Test (IST) sections
        - Commissioning Checklist (CXC) sections
        """
        self.item_counter = 0
        form = InspectionForm(
            form_type=FormType.ITC,
            title=f"Inspection, Testing & Commissioning - {system.name}",
            system=system.name,
            system_tag=system.tag,
            project=self.soo.project,
            version=self.soo.version
        )

        # ===== HEADER & GENERAL INFORMATION =====
        form.sections.append(self._create_header_section("ITC"))
        form.sections.append(self._create_general_section("ITC"))
        form.sections.append(self._create_commissioning_support_section("ITC"))

        # ===== DOCUMENTATION & PREREQUISITES =====
        form.sections.append(self._create_prerequisites_section(system, "ITC"))
        form.sections.append(self._create_documentation_section(system, "ITC"))

        # ===== SAFETY =====
        form.sections.append(self._create_safety_section("ITC"))

        # Check if this is an electrical equipment type (RSB, ATS, etc.)
        equip_type = self._get_equipment_type_from_system(system)
        is_electrical_equip = equip_type in ["RSB", "ATS", "RDB", "UPS", "Generator", "MVS"]

        if is_electrical_equip:
            # For electrical equipment, add template-based sections first
            template_sections = self._create_template_based_sections(system)
            for section in template_sections:
                form.sections.append(section)

        # ===== PRE-FUNCTIONAL INSPECTION (PFI) =====
        form.sections.append(self._create_installation_section(system))
        electrical_section = self._create_electrical_section(system)
        electrical_section = self._add_enhanced_items_to_section(electrical_section, "Electrical", system)
        electrical_section = self._add_template_items_to_section(electrical_section, "Electrical", system)
        form.sections.append(electrical_section)
        form.sections.append(self._create_piping_section(system))
        controls_section = self._create_controls_section(system)
        controls_section = self._add_enhanced_items_to_section(controls_section, "Controls", system)
        controls_section = self._add_template_items_to_section(controls_section, "Controls Installation", system)
        form.sections.append(controls_section)
        form.sections.append(self._create_labeling_section(system))

        # ===== FUNCTIONAL PERFORMANCE TEST (FPT) =====
        form.sections.append(self._create_equipment_settings_section(system))
        form.sections.append(self._create_visual_inspection_section(system))
        graphics_section = self._create_graphics_bms_section(system)
        graphics_section = self._add_enhanced_items_to_section(graphics_section, "Graphics/BMS", system)
        graphics_section = self._add_template_items_to_section(graphics_section, "BMS Verification", system)
        form.sections.append(graphics_section)
        form.sections.append(self._create_automated_reports_section(system))
        form.sections.append(self._create_startup_section(system))
        mode_section = self._create_mode_testing_section(system)
        mode_section = self._add_enhanced_items_to_section(mode_section, "Mode Testing", system)
        mode_section = self._add_template_items_to_section(mode_section, "Functional Test", system)
        form.sections.append(mode_section)
        sensor_section = self._create_sensor_testing_section(system)
        sensor_section = self._add_enhanced_items_to_section(sensor_section, "Sensor Testing", system)
        form.sections.append(sensor_section)
        setpoint_section = self._create_setpoint_verification_section(system)
        setpoint_section = self._add_enhanced_items_to_section(setpoint_section, "Setpoint Verification", system)
        form.sections.append(setpoint_section)
        form.sections.append(self._create_control_response_section(system))

        # ===== INTEGRATED SYSTEMS TEST (IST) =====
        interlock_section = self._create_interlock_testing_section(system)
        interlock_section = self._add_enhanced_items_to_section(interlock_section, "Interlock Testing", system)
        form.sections.append(interlock_section)
        alarm_section = self._create_alarm_testing_section(system)
        alarm_section = self._add_enhanced_items_to_section(alarm_section, "Alarm Testing", system)
        alarm_section = self._add_template_items_to_section(alarm_section, "Alerts", system)
        form.sections.append(alarm_section)
        form.sections.append(self._create_integration_section(system))
        form.sections.append(self._create_failover_section(system))

        # ===== COMMISSIONING COMPLETION (CXC) =====
        form.sections.append(self._create_training_section(system))
        form.sections.append(self._create_handover_section(system))
        form.sections.append(self._create_warranty_section(system))

        # Add End of Test section from templates (if applicable)
        end_section = self._create_end_of_test_section(system)
        if end_section:
            form.sections.append(end_section)

        # ===== AI-ENHANCED CHECKS (requires MetaGen) =====
        ai_section = self._generate_ai_section(system, FormType.ITC)
        if ai_section:
            form.sections.append(ai_section)

        return form

    def _next_id(self, prefix: str) -> str:
        """Generate next item ID."""
        self.item_counter += 1
        return f"{prefix}-{self.item_counter:03d}"

    def generate_pfi(self, system: System) -> InspectionForm:
        """Generate Pre-Functional Inspection form."""
        self.item_counter = 0
        form = InspectionForm(
            form_type=FormType.PFI,
            title=f"Pre-Functional Inspection - {system.name}",
            system=system.name,
            system_tag=system.tag,
            project=self.soo.project,
            version=self.soo.version
        )

        form.sections.append(self._create_header_section("PFI"))
        form.sections.append(self._create_general_section("PFI"))
        form.sections.append(self._create_commissioning_support_section("PFI"))
        form.sections.append(self._create_documentation_section(system, "PFI"))
        form.sections.append(self._create_safety_section("PFI"))
        form.sections.append(self._create_installation_section(system))
        form.sections.append(self._create_electrical_section(system))
        form.sections.append(self._create_piping_section(system))
        form.sections.append(self._create_controls_section(system))
        form.sections.append(self._create_labeling_section(system))

        # Add AI-enhanced section if enabled
        ai_section = self._generate_ai_section(system, FormType.PFI)
        if ai_section:
            form.sections.append(ai_section)

        return form

    def generate_fpt(self, system: System) -> InspectionForm:
        """Generate Functional Performance Test form."""
        self.item_counter = 0
        form = InspectionForm(
            form_type=FormType.FPT,
            title=f"Functional Performance Test - {system.name}",
            system=system.name,
            system_tag=system.tag,
            project=self.soo.project,
            version=self.soo.version
        )

        form.sections.append(self._create_header_section("FPT"))
        form.sections.append(self._create_general_section("FPT"))
        form.sections.append(self._create_commissioning_support_section("FPT"))
        form.sections.append(self._create_prerequisites_section(system, "FPT"))
        form.sections.append(self._create_documentation_section(system, "FPT"))
        form.sections.append(self._create_safety_section("FPT"))
        form.sections.append(self._create_equipment_settings_section(system))
        form.sections.append(self._create_visual_inspection_section(system))
        form.sections.append(self._create_graphics_bms_section(system))
        form.sections.append(self._create_automated_reports_section(system))
        form.sections.append(self._create_startup_section(system))
        form.sections.append(self._create_mode_testing_section(system))
        form.sections.append(self._create_sensor_testing_section(system))
        form.sections.append(self._create_setpoint_verification_section(system))
        form.sections.append(self._create_control_response_section(system))

        # Add AI-enhanced section if enabled
        ai_section = self._generate_ai_section(system, FormType.FPT)
        if ai_section:
            form.sections.append(ai_section)

        return form

    def generate_ist(self, system: System) -> InspectionForm:
        """Generate Integrated Systems Test form."""
        self.item_counter = 0
        form = InspectionForm(
            form_type=FormType.IST,
            title=f"Integrated Systems Test - {system.name}",
            system=system.name,
            system_tag=system.tag,
            project=self.soo.project,
            version=self.soo.version
        )

        form.sections.append(self._create_header_section("IST"))
        form.sections.append(self._create_general_section("IST"))
        form.sections.append(self._create_commissioning_support_section("IST"))
        form.sections.append(self._create_prerequisites_section(system, "IST"))
        form.sections.append(self._create_documentation_section(system, "IST"))
        form.sections.append(self._create_safety_section("IST"))
        form.sections.append(self._create_interlock_testing_section(system))
        form.sections.append(self._create_alarm_testing_section(system))
        form.sections.append(self._create_integration_section(system))
        form.sections.append(self._create_failover_section(system))

        # Add AI-enhanced section if enabled
        ai_section = self._generate_ai_section(system, FormType.IST)
        if ai_section:
            form.sections.append(ai_section)

        return form

    def generate_cxc(self, system: System) -> InspectionForm:
        """Generate Commissioning Checklist form."""
        self.item_counter = 0
        form = InspectionForm(
            form_type=FormType.CXC,
            title=f"Commissioning Checklist - {system.name}",
            system=system.name,
            system_tag=system.tag,
            project=self.soo.project,
            version=self.soo.version
        )

        form.sections.append(self._create_header_section("CXC"))
        form.sections.append(self._create_general_section("CXC"))
        form.sections.append(self._create_commissioning_support_section("CXC"))
        form.sections.append(self._create_documentation_section(system, "CXC"))
        form.sections.append(self._create_training_section(system))
        form.sections.append(self._create_handover_section(system))
        form.sections.append(self._create_warranty_section(system))

        # Add AI-enhanced section if enabled
        ai_section = self._generate_ai_section(system, FormType.CXC)
        if ai_section:
            form.sections.append(ai_section)

        return form

    # ========== HEADER SECTIONS ==========

    def _create_header_section(self, prefix: str) -> FormSection:
        """Create header information section."""
        section = FormSection(title="Equipment Information", description="Record equipment and test information")
        items = [
            ("Equipment Designation", CheckItemType.DOCUMENTATION),
            ("Commence Date", CheckItemType.DOCUMENTATION),
            ("Commissioning Authority (Name)", CheckItemType.DOCUMENTATION),
            ("Completion Date", CheckItemType.DOCUMENTATION),
        ]
        for desc, check_type in items:
            section.check_items.append(CheckItem(id=self._next_id(prefix), description=desc, check_type=check_type, priority=Priority.HIGH, acceptance_criteria="Record information"))
        return section

    def _create_general_section(self, prefix: str) -> FormSection:
        """Create general requirements section."""
        section = FormSection(title="General", description="General requirements and acknowledgments")
        section.check_items.append(CheckItem(id=self._next_id(prefix), description="While Performing This Procedure:\n**Items that do not apply shall be noted with a reason in the comments section.", check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria="Acknowledged"))
        section.check_items.append(CheckItem(id=self._next_id(prefix), description="TEST EXECUTION / COMPLETION REQUIREMENTS:\nThe actual testing procedure shall be executed by the Contractor and/or their representative(s) in the presence of the Commissioning Agent.", check_type=CheckItemType.VERIFICATION, priority=Priority.CRITICAL, acceptance_criteria="Acknowledged"))
        return section

    def _create_commissioning_support_section(self, prefix: str) -> FormSection:
        """Create commissioning support section."""
        section = FormSection(title="Commissioning Support", description="Document participating personnel")
        section.check_items.append(CheckItem(id=self._next_id(prefix), description="All necessary personnel are available to exercise the equipment and ancillary systems.\n**DO NOT PROCEED until coordination is complete.", check_type=CheckItemType.VERIFICATION, priority=Priority.CRITICAL, acceptance_criteria="Personnel available"))
        for person in ["Electrical Contractor", "Mechanical Contractor", "Equipment Vendor", "Controls Contractor", "CSI Representative", "Client Representative", "Commissioning Agent"]:
            section.check_items.append(CheckItem(id=self._next_id(prefix), description=person, check_type=CheckItemType.DOCUMENTATION, priority=Priority.MEDIUM, acceptance_criteria="Record name"))
        section.check_items.append(CheckItem(id=self._next_id(prefix), description="Modification to or any additional testing not specifically indicated in the approved procedure shall be documented.", check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria="Acknowledged"))
        return section

    def _create_safety_section(self, prefix: str) -> FormSection:
        """Create safety requirements section."""
        section = FormSection(title="Safety & Equipment Requirements", description="Safety verification prior to testing")
        items = [
            ("Lock Out Tag Out (LOTO) Plan has been reviewed and is available", Priority.CRITICAL),
            ("All parties have been notified, equipped with the necessary PPE and work area signage has been established", Priority.CRITICAL),
            ("Emergency stop locations have been identified and tested", Priority.CRITICAL),
            ("Fire suppression system status has been verified", Priority.HIGH),
            ("Coordination with operations/facilities has been completed", Priority.HIGH),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(id=self._next_id(prefix), description=desc, check_type=CheckItemType.VERIFICATION, priority=priority, acceptance_criteria="Safety requirement confirmed"))
        return section

    def _create_prerequisites_section(self, system: System, prefix: str) -> FormSection:
        """Create prerequisites section for testing."""
        section = FormSection(title="Prerequisites", description="Verify prerequisites are complete before testing")
        items = [
            ("Pre-Functional Inspection (PFI) has been completed and approved", Priority.CRITICAL),
            ("All punch list items from PFI have been resolved", Priority.CRITICAL),
            ("Equipment has been started up by the manufacturer/installer", Priority.CRITICAL),
            ("Test and Balance (TAB) has been completed", Priority.HIGH),
            ("Building automation system is operational", Priority.HIGH),
            ("All control sequences have been programmed", Priority.HIGH),
            ("Temporary construction power has been removed (if applicable)", Priority.MEDIUM),
            ("Area is clean and free of construction debris", Priority.MEDIUM),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id(prefix),
                description=desc,
                check_type=CheckItemType.VERIFICATION,
                priority=priority,
                acceptance_criteria="Prerequisite confirmed",
                system_tag=system.tag
            ))
        return section
        """Create documentation review section."""
        section = FormSection(
            title="Documentation Review",
            description="Review of submittal documents and project documentation"
        )

        docs = [
            ("Equipment submittals reviewed and approved", Priority.HIGH),
            ("O&M manuals received", Priority.HIGH),
            ("As-built drawings available", Priority.MEDIUM),
            ("Control drawings reviewed", Priority.HIGH),
            ("Wiring diagrams verified", Priority.MEDIUM),
            ("Sequence of Operations document reviewed", Priority.CRITICAL),
            ("Test and balance report available", Priority.MEDIUM),
        ]

        for desc, priority in docs:
            section.check_items.append(CheckItem(
                id=self._next_id(prefix),
                description=desc,
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria="Document complete and approved",
                system_tag=system.tag
            ))

        return section

    def _create_installation_section(self, system: System) -> FormSection:
        """Create installation verification section."""
        section = FormSection(
            title="Installation Verification",
            description="Physical installation inspection"
        )

        items = [
            ("Equipment installed per drawings", Priority.HIGH),
            ("Mounting and supports adequate", Priority.HIGH),
            ("Access for maintenance provided", Priority.MEDIUM),
            ("Clearances per manufacturer requirements", Priority.MEDIUM),
            ("Vibration isolation installed correctly", Priority.MEDIUM),
            ("Equipment identification labels installed", Priority.LOW),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description=desc,
                check_type=CheckItemType.VISUAL,
                priority=priority,
                acceptance_criteria="Installation meets specifications",
                system_tag=system.tag
            ))

        return section

    def _create_component_inspection_section(
        self, system: System
    ) -> FormSection:
        """Create component inspection section from SOO components."""
        section = FormSection(
            title="Component Inspection",
            description="Inspection of system components"
        )

        for component in system.components:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description=f"{component.tag} {component.name} - Visual inspection complete",
                check_type=CheckItemType.VISUAL,
                priority=Priority.MEDIUM,
                acceptance_criteria="Component installed correctly, no visible damage",
                component_tag=component.tag,
                system_tag=system.tag
            ))

            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description=f"{component.tag} {component.name} - Nameplate data recorded",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.LOW,
                acceptance_criteria="Nameplate matches submittal data",
                component_tag=component.tag,
                system_tag=system.tag
            ))

        return section

    def _create_electrical_section(self, system: System) -> FormSection:
        """Create electrical verification section."""
        section = FormSection(
            title="Electrical Verification",
            description="Electrical connections and safety checks"
        )

        items = [
            ("Power connections verified", Priority.CRITICAL),
            ("Grounding verified", Priority.CRITICAL),
            ("Voltage measurements within tolerance", Priority.HIGH),
            ("Phase rotation correct (3-phase equipment)", Priority.HIGH),
            ("Motor amp draws recorded", Priority.MEDIUM),
            ("Disconnect switches operational", Priority.HIGH),
            ("Overload protection verified", Priority.HIGH),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description=desc,
                check_type=CheckItemType.MEASUREMENT,
                priority=priority,
                acceptance_criteria="Within design parameters",
                system_tag=system.tag
            ))

        return section

    def _create_controls_section(self, system: System) -> FormSection:
        """Create controls verification section enhanced with DI points."""
        section = FormSection(
            title="Controls Verification",
            description="Control system installation, configuration, and status point verification"
        )

        # Standard control verification items
        items = [
            ("Controller installed and powered", Priority.HIGH),
            ("Network communication verified", Priority.HIGH),
            ("All I/O points connected", Priority.HIGH),
            ("Sensor calibration verified", Priority.MEDIUM),
            ("Actuators stroke-tested", Priority.MEDIUM),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description=desc,
                check_type=CheckItemType.VERIFICATION,
                priority=priority,
                acceptance_criteria="Controls operational",
                system_tag=system.tag
            ))

        # Get DI points for this system (status/feedback points)
        di_points = self._get_points_by_type(system, PointType.DI)

        if di_points:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description="=== STATUS POINT VERIFICATION (DI Points) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in di_points:
                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} status indication"

                # Determine expected state based on description
                if any(kw in point.description.upper() for kw in ['ALARM', 'FAULT', 'FAIL']):
                    acceptance = "Normal state (no alarm/fault)"
                    priority = Priority.HIGH
                elif any(kw in point.description.upper() for kw in ['RUN', 'STATUS', 'ON']):
                    acceptance = "Status matches equipment state"
                    priority = Priority.MEDIUM
                else:
                    acceptance = "Status indication correct"
                    priority = Priority.MEDIUM

                section.check_items.append(CheckItem(
                    id=self._next_id("PFI"),
                    description=desc,
                    check_type=CheckItemType.VERIFICATION,
                    priority=priority,
                    acceptance_criteria=acceptance,
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        # Add unmatched DI points as additional status tests
        unmatched_di = self._get_unmatched_points_by_type(PointType.DI)
        if unmatched_di:
            section.check_items.append(CheckItem(
                id=self._next_id("PFI"),
                description="=== ADDITIONAL STATUS POINTS (Other Equipment) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.MEDIUM,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in unmatched_di:
                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} status indication"

                if point.description and any(kw in point.description.upper() for kw in ['ALARM', 'FAULT', 'FAIL']):
                    acceptance = "Normal state (no alarm/fault)"
                    priority = Priority.HIGH
                elif point.description and any(kw in point.description.upper() for kw in ['RUN', 'STATUS', 'ON']):
                    acceptance = "Status matches equipment state"
                    priority = Priority.MEDIUM
                else:
                    acceptance = "Status indication correct"
                    priority = Priority.MEDIUM

                section.check_items.append(CheckItem(
                    id=self._next_id("PFI"),
                    description=desc,
                    check_type=CheckItemType.VERIFICATION,
                    priority=priority,
                    acceptance_criteria=acceptance,
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        return section

    def _create_documentation_section(self, system: System, prefix: str) -> FormSection:
        """Create documentation verification section."""
        section = FormSection(title="Documentation", description="Confirm availability and note revision prior to testing")
        docs = [
            ("Sequence of Operation (record rev)", CheckItemType.DOCUMENTATION, Priority.CRITICAL),
            ("BMS Points List (record rev)", CheckItemType.DOCUMENTATION, Priority.HIGH),
            ("Control Drawings (record rev)", CheckItemType.DOCUMENTATION, Priority.HIGH),
            ("Electrical One-Line Diagrams (record rev)", CheckItemType.DOCUMENTATION, Priority.HIGH),
            ("P&ID Drawings (record rev)", CheckItemType.DOCUMENTATION, Priority.MEDIUM),
            ("Equipment Submittals (record rev)", CheckItemType.DOCUMENTATION, Priority.HIGH),
            ("O&M Manuals available", CheckItemType.VERIFICATION, Priority.MEDIUM),
            ("Test & Balance (TAB) report", CheckItemType.VERIFICATION, Priority.HIGH),
            ("NETA Testing Report", CheckItemType.VERIFICATION, Priority.HIGH),
        ]
        for desc, check_type, priority in docs:
            section.check_items.append(CheckItem(id=self._next_id(prefix), description=desc, check_type=check_type, priority=priority, acceptance_criteria="Document available and revision noted", system_tag=system.tag))
        return section

    def _create_equipment_settings_section(self, system: System) -> FormSection:
        """Create equipment settings and firmware section."""
        section = FormSection(title="Equipment Settings & Firmware (As Found)", description="Record equipment settings and firmware versions")
        items = [
            "OPC Server Type (DA or UA)", "OPC Server Version", "BMS/EPMS version number",
            "Graphics file name", "Graphics version number", "PLC/Controller Firmware Version",
            "PLC Development Software Version", "VFD/VSD Firmware Version",
        ]
        for desc in items:
            section.check_items.append(CheckItem(id=self._next_id("FPT"), description=desc, check_type=CheckItemType.DOCUMENTATION, priority=Priority.MEDIUM, acceptance_criteria="Version recorded", system_tag=system.tag))
        section.check_items.append(CheckItem(id=self._next_id("FPT"), description="All firmware versions are in concurrence with the latest APPROVED versions", check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria="Firmware versions match", system_tag=system.tag))
        section.check_items.append(CheckItem(id=self._next_id("FPT"), description="TAB values have been uploaded to applicable parameters/setpoints", check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria="TAB values uploaded", system_tag=system.tag))
        section.check_items.append(CheckItem(id=self._next_id("FPT"), description="VFD/VSD as-found settings match the approved project settings", check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria="Settings match", system_tag=system.tag))
        return section

    def _create_visual_inspection_section(self, system: System) -> FormSection:
        """Create visual inspection section for FPT."""
        section = FormSection(title="Visual Inspections", description="Pre-test visual verification")
        items = [
            ("Equipment is free from damage (dents, scratches, etc.)", Priority.MEDIUM),
            ("Equipment is level and secure", Priority.HIGH),
            ("All doors and latches are firmly secured and locked (as applicable)", Priority.MEDIUM),
            ("All ancillary meters, switches, gauges, actuators are secured and operational", Priority.HIGH),
            ("Pressure and temperature indicators are installed and have proper ranges", Priority.HIGH),
            ("Permanent labels are applied and accurate", Priority.MEDIUM),
            ("All naming conventions are accurately displayed on local display/HMI, BMS, equipment label", Priority.HIGH),
            ("Power distribution panel breakers are labeled correctly", Priority.MEDIUM),
            ("Danger labels and/or permanent Arc Flash labels are applied to unit", Priority.HIGH),
            ("Unit electrical disconnects are in place and labeled", Priority.HIGH),
            ("All piping connections are sealed, tight, and weatherproof as applicable", Priority.HIGH),
            ("All piping is insulated as required", Priority.MEDIUM),
            ("All sensors are installed and properly labeled", Priority.HIGH),
            ("VFD/VSD time and date parameters are accurate", Priority.LOW),
            ("Control panel drawings are installed, up to date, and accurate", Priority.MEDIUM),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(id=self._next_id("FPT"), description=desc, check_type=CheckItemType.VISUAL, priority=priority, acceptance_criteria="Visual inspection passed", system_tag=system.tag))
        return section

    def _create_graphics_bms_section(self, system: System) -> FormSection:
        """Create Graphics/BMS review section enhanced with all point types."""
        section = FormSection(title="Graphics/BMS Review", description="BMS graphics, point display, and control output verification")

        # Standard graphics review items
        items = [
            ("Unit Identification is correct on the graphic display", Priority.HIGH),
            ("Confirm window title follows guidelines within the Client Graphics Specification", Priority.MEDIUM),
            ("Unit is in correct location on floor plan layout", Priority.HIGH),
            ("All equipment accessories are correctly represented (Fans, Dampers, valves, etc.)", Priority.HIGH),
            ("All graphic animations have been programmed (Fan rotation, Damper modulation, etc.)", Priority.HIGH),
            ("All adjustable setpoints are correctly represented on the graphic display", Priority.HIGH),
            ("All feedbacks are correctly represented (air temperature, damper position, etc.)", Priority.HIGH),
            ("Alerts are correctly represented on graphic display", Priority.HIGH),
            ("Alert priorities have been set and any 'page out' Alerts have been identified", Priority.HIGH),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(id=self._next_id("FPT"), description=desc, check_type=CheckItemType.VERIFICATION, priority=priority, acceptance_criteria="Graphics verified", system_tag=system.tag))

        # Get DO points for this system (control command outputs)
        do_points = self._get_points_by_type(system, PointType.DO)

        if do_points:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== CONTROL OUTPUT VERIFICATION (DO Points) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in do_points:
                desc = f"Test {point.point_name}: {point.description}" if point.description else f"Test {point.point_name} command output"

                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria="Command executes and equipment responds",
                    method="Command from BMS, verify equipment response",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        # Add unmatched DO points as additional control output tests
        unmatched_do = self._get_unmatched_points_by_type(PointType.DO)
        if unmatched_do:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== ADDITIONAL CONTROL OUTPUTS (Other Equipment) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.MEDIUM,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in unmatched_do:
                desc = f"Test {point.point_name}: {point.description}" if point.description else f"Test {point.point_name} command output"

                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.MEDIUM,
                    acceptance_criteria="Command executes and equipment responds",
                    method="Command from BMS, verify equipment response",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        return section

    def _create_automated_reports_section(self, system: System) -> FormSection:
        """Create automated test reports section."""
        section = FormSection(title="Automated Test Reports", description="Run automated reports prior to testing")
        reports = [
            ("Run Automated Report to show any setpoints set differently than design value", "Report run"),
            ("Confirm setpoint report is blank. If not, place all points back to design value.", "Report blank or corrected"),
            ("Run Automated Report to show any points 'In Manual' on associated equipment", "Report run"),
            ("Confirm 'In Manual' report is blank. If not, safely place all points in auto.", "Report blank or corrected"),
            ("Run Automated Report to show any active Alerts on associated equipment", "Report run"),
            ("Confirm Active Alerts Report is blank. If not, attempt to clear all active alerts.", "Report blank or corrected"),
        ]
        for desc, criteria in reports:
            section.check_items.append(CheckItem(id=self._next_id("FPT"), description=desc, check_type=CheckItemType.VERIFICATION, priority=Priority.HIGH, acceptance_criteria=criteria, system_tag=system.tag))
        return section

    def _create_sensor_testing_section(self, system: System) -> FormSection:
        """Create sensor testing section enhanced with AI points from points list."""
        section = FormSection(title="Sensor Testing & Calibration", description="Test sensor readings, calibration, and fault handling")

        # Get AI points for this system
        ai_points = self._get_points_by_type(system, PointType.AI)

        if ai_points:
            # Create specific check items for each AI sensor point
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== SENSOR POINT VERIFICATION ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in ai_points:
                # Build acceptance criteria from range info
                if point.range_min and point.range_max:
                    acceptance = f"{point.range_min} to {point.range_max} {point.units}".strip()
                elif point.units:
                    acceptance = f"Within design range ({point.units})"
                else:
                    acceptance = "Within design range"

                # Create verification item for this sensor
                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} reading"
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.HIGH,
                    acceptance_criteria=acceptance,
                    expected_value=f"{point.range_min}-{point.range_max} {point.units}".strip() if point.range_min else "",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

            # Add generic sensor calculation tests after point-specific items
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== SENSOR CALCULATION & FAULT TESTS ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

        # Standard sensor testing items (always included)
        tests = [
            ("Open the associated sensor(s) popup and record current values", CheckItemType.DOCUMENTATION),
            ("Set selection to average - verify signal matches calculated average value", CheckItemType.FUNCTIONAL),
            ("Set selection to maximum - verify signal is the maximum value", CheckItemType.FUNCTIONAL),
            ("Set selection to minimum - verify signal is the minimum value", CheckItemType.FUNCTIONAL),
            ("Place sensor out of service (OOS) - verify average/max/min do not include OOS sensor", CheckItemType.FUNCTIONAL),
            ("Place sensor back in service - verify values return to previous", CheckItemType.FUNCTIONAL),
            ("Place sensor in channel fault - verify average/max/min do not include faulted sensor", CheckItemType.FUNCTIONAL),
            ("Verify associated popups properly indicate the alert (check text and highlights)", CheckItemType.VERIFICATION),
            ("Place sensor out of channel fault and acknowledge alert", CheckItemType.FUNCTIONAL),
            ("Verify values return to previous after clearing fault", CheckItemType.FUNCTIONAL),
        ]
        for desc, check_type in tests:
            section.check_items.append(CheckItem(id=self._next_id("FPT"), description=desc, check_type=check_type, priority=Priority.HIGH, acceptance_criteria="Test passed", system_tag=system.tag))

        # Add unmatched AI points as additional sensor tests
        unmatched_ai = self._get_unmatched_points_by_type(PointType.AI)
        if unmatched_ai:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== ADDITIONAL SENSOR POINTS (Other Equipment) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.MEDIUM,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in unmatched_ai:
                if point.range_min and point.range_max:
                    acceptance = f"{point.range_min} to {point.range_max} {point.units}".strip()
                elif point.units:
                    acceptance = f"Within design range ({point.units})"
                else:
                    acceptance = "Within design range"

                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} reading"
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.MEDIUM,
                    acceptance_criteria=acceptance,
                    expected_value=f"{point.range_min}-{point.range_max} {point.units}".strip() if point.range_min else "",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        return section

    def _create_piping_section(self, system: System) -> FormSection:
        """Create piping verification section."""
        section = FormSection(title="Piping Verification", description="Piping installation and connection verification")
        items = [
            ("All piping is in place and installed to meet project requirements", Priority.HIGH),
            ("All piping connections are sealed, tight, and weatherproof as applicable", Priority.HIGH),
            ("All piping is insulated as required", Priority.MEDIUM),
            ("All piping isolation valves are fully operable", Priority.HIGH),
            ("All piping labels are installed as applicable", Priority.LOW),
            ("All valve tags are installed as applicable", Priority.LOW),
            ("System has been flushed and cleaned per project requirements", Priority.HIGH),
            ("Pressure test completed and documented", Priority.HIGH),
            ("All drain pans and piping are installed, sloped properly, and free of debris", Priority.MEDIUM),
            ("Strainers installed and cleaned", Priority.MEDIUM),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(id=self._next_id("PFI"), description=desc, check_type=CheckItemType.VISUAL, priority=priority, acceptance_criteria="Piping verified", system_tag=system.tag))
        return section

    def _create_labeling_section(self, system: System) -> FormSection:
        """Create labeling verification section."""
        section = FormSection(title="Labeling & Identification", description="Equipment labeling verification")
        items = [
            ("Permanent labels are applied and accurate", Priority.MEDIUM),
            ("All naming conventions are accurately displayed on local display/HMI", Priority.HIGH),
            ("All naming conventions are accurately displayed in BMS", Priority.HIGH),
            ("Equipment labels match BIM360/asset management system", Priority.MEDIUM),
            ("Valve tags match P&ID drawings", Priority.MEDIUM),
            ("Electrical panel schedules are accurate", Priority.MEDIUM),
        ]
        for desc, priority in items:
            section.check_items.append(CheckItem(id=self._next_id("PFI"), description=desc, check_type=CheckItemType.VISUAL, priority=priority, acceptance_criteria="Labeling verified", system_tag=system.tag))
        return section
        """Create prerequisites section for testing."""
        section = FormSection(
            title="Test Prerequisites",
            description="Prerequisites before functional testing"
        )

        prereqs = [
            ("Pre-Functional Inspection complete", Priority.CRITICAL),
            ("System energized and operational", Priority.CRITICAL),
            ("TAB complete (if applicable)", Priority.HIGH),
            ("Control sequences loaded", Priority.HIGH),
            ("Test equipment calibrated", Priority.MEDIUM),
            ("Safety briefing completed", Priority.HIGH),
        ]

        for desc, priority in prereqs:
            section.check_items.append(CheckItem(
                id=self._next_id(prefix),
                description=desc,
                check_type=CheckItemType.VERIFICATION,
                priority=priority,
                acceptance_criteria="Prerequisite confirmed",
                system_tag=system.tag
            ))

        return section

    def _create_startup_section(self, system: System) -> FormSection:
        """Create startup sequence section."""
        section = FormSection(
            title="Startup Sequence",
            description="System startup verification"
        )

        items = [
            ("Normal startup sequence initiated", Priority.HIGH),
            ("Startup timing verified", Priority.MEDIUM),
            ("No abnormal sounds or vibration", Priority.HIGH),
            ("Operating parameters within range", Priority.HIGH),
            ("Status indications correct", Priority.MEDIUM),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL,
                priority=priority,
                acceptance_criteria="Startup successful",
                system_tag=system.tag
            ))

        return section

    def _create_mode_testing_section(self, system: System) -> FormSection:
        """Create operating mode testing section from SOO modes."""
        section = FormSection(
            title="Operating Mode Tests",
            description="Test each operating mode defined in SOO"
        )

        for mode in system.operating_modes:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=f"Mode: {mode.name} - Entry conditions verified",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH,
                acceptance_criteria="Mode transitions correctly",
                reference=mode.description,
                system_tag=system.tag
            ))

            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=f"Mode: {mode.name} - All actions executed correctly",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH,
                acceptance_criteria="Actions per SOO",
                system_tag=system.tag
            ))

            for action in mode.actions[:3]:
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=f"Verify: {action}",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.MEDIUM,
                    acceptance_criteria="Action verified",
                    system_tag=system.tag
                ))

        return section

    def _create_setpoint_verification_section(
        self, system: System
    ) -> FormSection:
        """Create setpoint verification section from SOO setpoints and AO points."""
        section = FormSection(
            title="Setpoint Verification",
            description="Verify all setpoints per SOO and BMS configuration"
        )

        # Get AO points for this system (setpoint/command outputs)
        ao_points = self._get_points_by_type(system, PointType.AO)

        if ao_points:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== BMS SETPOINT OUTPUTS (AO Points) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in ao_points:
                # Build acceptance criteria from range info
                if point.range_min and point.range_max:
                    acceptance = f"Command range: {point.range_min} to {point.range_max} {point.units}".strip()
                elif point.units:
                    acceptance = f"Within valid range ({point.units})"
                else:
                    acceptance = "Setpoint matches design"

                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} setpoint"
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.HIGH,
                    acceptance_criteria=acceptance,
                    expected_value=f"{point.range_min}-{point.range_max} {point.units}".strip() if point.range_min else "",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        # SOO-defined setpoints (if any)
        if system.setpoints:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== SOO-DEFINED SETPOINTS ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.HIGH,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

        for setpoint in system.setpoints:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=f"Setpoint: {setpoint.name}",
                check_type=CheckItemType.MEASUREMENT,
                priority=Priority.MEDIUM,
                acceptance_criteria=f"Value = {setpoint.value} {setpoint.units}",
                expected_value=f"{setpoint.value} {setpoint.units}",
                system_tag=system.tag
            ))

        for component in system.components:
            for setpoint in component.setpoints:
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=f"{component.tag} - {setpoint.name}",
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.MEDIUM,
                    acceptance_criteria=f"Value = {setpoint.value} {setpoint.units}",
                    expected_value=f"{setpoint.value} {setpoint.units}",
                    component_tag=component.tag,
                    system_tag=system.tag
                ))

        # Add unmatched AO points as additional setpoint tests
        unmatched_ao = self._get_unmatched_points_by_type(PointType.AO)
        if unmatched_ao:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description="=== ADDITIONAL SETPOINTS (Other Equipment) ===",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.MEDIUM,
                acceptance_criteria="Section header",
                system_tag=system.tag
            ))

            for point in unmatched_ao:
                if point.range_min and point.range_max:
                    acceptance = f"Command range: {point.range_min} to {point.range_max} {point.units}".strip()
                elif point.units:
                    acceptance = f"Within valid range ({point.units})"
                else:
                    acceptance = "Setpoint matches design"

                desc = f"Verify {point.point_name}: {point.description}" if point.description else f"Verify {point.point_name} setpoint"
                section.check_items.append(CheckItem(
                    id=self._next_id("FPT"),
                    description=desc,
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.MEDIUM,
                    acceptance_criteria=acceptance,
                    expected_value=f"{point.range_min}-{point.range_max} {point.units}".strip() if point.range_min else "",
                    system_tag=system.tag,
                    component_tag=point.equipment_ref
                ))

        return section

    def _create_control_response_section(self, system: System) -> FormSection:
        """Create control response testing section."""
        section = FormSection(
            title="Control Response",
            description="Verify control loop response"
        )

        items = [
            ("Control loops stable", Priority.HIGH),
            ("Response time acceptable", Priority.MEDIUM),
            ("No hunting or oscillation", Priority.HIGH),
            ("Deadband appropriate", Priority.MEDIUM),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL,
                priority=priority,
                acceptance_criteria="Control response acceptable",
                system_tag=system.tag
            ))

        return section

    def _create_interlock_testing_section(self, system: System) -> FormSection:
        """Create interlock testing section from SOO interlocks."""
        section = FormSection(
            title="Safety Interlock Tests",
            description="Test all safety interlocks defined in SOO"
        )

        for i, interlock in enumerate(system.interlocks, 1):
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description=f"Interlock {i}: {interlock}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                acceptance_criteria="Interlock functions correctly",
                system_tag=system.tag
            ))

        if not system.interlocks:
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description="Safety shutdown interlock test",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                acceptance_criteria="System shuts down safely",
                system_tag=system.tag
            ))

        return section

    def _create_alarm_testing_section(self, system: System) -> FormSection:
        """Create alarm testing section from SOO alarms."""
        section = FormSection(
            title="Alarm Tests",
            description="Test all alarms defined in SOO"
        )

        for i, alarm in enumerate(system.alarms, 1):
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description=f"Alarm {i}: {alarm}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH,
                acceptance_criteria="Alarm triggers and clears correctly",
                system_tag=system.tag
            ))

        standard_alarms = [
            "High temperature alarm",
            "Low temperature alarm",
            "Equipment fault alarm",
            "Communication loss alarm",
        ]

        for alarm in standard_alarms:
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description=alarm,
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH,
                acceptance_criteria="Alarm functions correctly",
                system_tag=system.tag
            ))

        return section

    def _create_integration_section(self, system: System) -> FormSection:
        """Create systems integration testing section."""
        section = FormSection(
            title="Systems Integration",
            description="Test integration with other systems"
        )

        items = [
            ("BMS communication verified", Priority.HIGH),
            ("Data points trending correctly", Priority.MEDIUM),
            ("Remote start/stop functional", Priority.HIGH),
            ("Setpoint adjustment from BMS", Priority.MEDIUM),
            ("Alarm routing to BMS verified", Priority.HIGH),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL,
                priority=priority,
                acceptance_criteria="Integration successful",
                system_tag=system.tag
            ))

        return section

    def _create_failover_section(self, system: System) -> FormSection:
        """Create failover testing section."""
        section = FormSection(
            title="Failover and Recovery",
            description="Test system failover and recovery procedures"
        )

        items = [
            ("Power failure recovery", Priority.CRITICAL),
            ("Network failure response", Priority.HIGH),
            ("Controller failover (if redundant)", Priority.HIGH),
            ("Manual override functionality", Priority.HIGH),
            ("Emergency shutdown procedure", Priority.CRITICAL),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("IST"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL,
                priority=priority,
                acceptance_criteria="Failover/recovery successful",
                system_tag=system.tag
            ))

        return section

    def _create_training_section(self, system: System) -> FormSection:
        """Create training verification section."""
        section = FormSection(
            title="Training Verification",
            description="Verify operator training completed"
        )

        items = [
            ("Operations training completed", Priority.HIGH),
            ("Maintenance training completed", Priority.HIGH),
            ("Emergency procedures reviewed", Priority.CRITICAL),
            ("Training documentation provided", Priority.MEDIUM),
            ("Training sign-off obtained", Priority.HIGH),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("CXC"),
                description=desc,
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria="Training confirmed",
                system_tag=system.tag
            ))

        return section

    def _create_handover_section(self, system: System) -> FormSection:
        """Create handover documentation section."""
        section = FormSection(
            title="Handover Documentation",
            description="Verify all handover documentation"
        )

        items = [
            ("O&M manuals delivered", Priority.HIGH),
            ("As-built drawings delivered", Priority.HIGH),
            ("Spare parts list provided", Priority.MEDIUM),
            ("Warranty information provided", Priority.HIGH),
            ("Emergency contact list provided", Priority.HIGH),
            ("System passwords documented", Priority.CRITICAL),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("CXC"),
                description=desc,
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria="Documentation complete",
                system_tag=system.tag
            ))

        return section

    def _create_warranty_section(self, system: System) -> FormSection:
        """Create warranty verification section."""
        section = FormSection(
            title="Warranty and Final Acceptance",
            description="Warranty registration and final acceptance"
        )

        items = [
            ("Equipment warranties registered", Priority.HIGH),
            ("Extended warranty options documented", Priority.LOW),
            ("Substantial completion achieved", Priority.HIGH),
            ("Punch list items resolved", Priority.HIGH),
            ("Final acceptance signed", Priority.CRITICAL),
        ]

        for desc, priority in items:
            section.check_items.append(CheckItem(
                id=self._next_id("CXC"),
                description=desc,
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria="Warranty/acceptance complete",
                system_tag=system.tag
            ))

        return section

