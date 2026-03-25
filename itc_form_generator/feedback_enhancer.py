"""Feedback Enhancer - Converts feedback into actionable check items.

This module analyzes user feedback and generates specific, detailed check items
that can be injected into the appropriate form sections.

Works WITHOUT MetaGen by using rule-based parsing of feedback text.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCheckItem:
    """A check item generated from feedback."""
    description: str
    section: str  # Which section this belongs to
    acceptance_criteria: str
    method: str
    priority: str
    check_type: str


class FeedbackEnhancer:
    """Converts feedback into specific check items for forms.

    This class analyzes feedback text and generates actionable check items
    that improve form quality based on user suggestions.
    """

    # Map feedback keywords to form sections
    SECTION_MAPPING = {
        'setpoint': 'Setpoint Verification',
        'sensor': 'Sensor Testing',
        'mode': 'Mode Testing',
        'operating mode': 'Mode Testing',
        'alarm': 'Alarm Testing',
        'alert': 'Alarm Testing',
        'interlock': 'Interlock Testing',
        'safety': 'Safety',
        'vfd': 'Electrical',
        'motor': 'Electrical',
        'electrical': 'Electrical',
        'control': 'Controls',
        'bms': 'Graphics/BMS',
        'graphic': 'Graphics/BMS',
        'startup': 'Startup',
        'install': 'Installation',
        'label': 'Labeling',
        'document': 'Documentation',
        'training': 'Training',
    }

    # Common patterns that indicate specific test requirements
    TEST_PATTERNS = {
        r'tolerance|oot|out of tolerance': 'tolerance_test',
        r'setpoint.*rang|rang.*setpoint': 'setpoint_range_test',
        r'sensor.*group|group.*sensor': 'sensor_group_test',
        r'vfd|variable frequency|frequency rang': 'vfd_test',
        r'time delay|delay.*time': 'time_delay_test',
        r'hardware failure|failure.*hardware': 'failure_test',
        r'emergency|e-stop|shutdown': 'emergency_test',
    }

    def __init__(self):
        self._feedback_store = None
        self._load_feedback_store()

    def _load_feedback_store(self):
        """Load the feedback store."""
        try:
            from .feedback_store import get_feedback_store
            self._feedback_store = get_feedback_store()
        except Exception as e:
            logger.warning(f"Could not load feedback store: {e}")

    def get_enhanced_items_for_section(self, section_name: str, system_type: str) -> list[EnhancedCheckItem]:
        """Get enhanced check items for a specific section.

        Args:
            section_name: Name of the section (e.g., "Setpoint Verification")
            system_type: Type of system (e.g., "AHU", "FCU")

        Returns:
            List of EnhancedCheckItem objects
        """
        if not self._feedback_store:
            return []

        items = []

        # Get feedback for this system type AND general feedback
        feedback_entries = self._feedback_store.get_feedback_for_system_type(system_type, limit=20)

        # Also get feedback from similar system types (any HVAC feedback is useful)
        all_feedback = self._feedback_store.get_all_feedback(limit=50)

        # Combine and deduplicate
        seen_ids = set(entry.id for entry in feedback_entries)
        for entry in all_feedback:
            if entry.id not in seen_ids:
                feedback_entries.append(entry)
                seen_ids.add(entry.id)

        for entry in feedback_entries:
            # Check if this feedback relates to this section
            if not self._feedback_relates_to_section(entry, section_name):
                continue

            # Generate check items from this feedback
            new_items = self._generate_items_from_feedback(entry, section_name, system_type)
            items.extend(new_items)

        return items[:15]  # Limit to 15 items per section

    def _feedback_relates_to_section(self, entry, section_name: str) -> bool:
        """Check if feedback relates to a specific section."""
        section_lower = section_name.lower()

        # Direct section match
        if entry.section_name:
            entry_section_lower = entry.section_name.lower()
            if entry_section_lower in section_lower or section_lower in entry_section_lower:
                return True

        # Check feedback text for section keywords
        text_lower = entry.feedback_text.lower()

        for keyword, mapped_section in self.SECTION_MAPPING.items():
            if keyword in text_lower and mapped_section.lower() in section_lower:
                return True

        return False

    def _generate_items_from_feedback(self, entry, section_name: str, system_type: str) -> list[EnhancedCheckItem]:
        """Generate specific check items from feedback text."""
        items = []
        text = entry.feedback_text

        # Check for specific test patterns
        for pattern, test_type in self.TEST_PATTERNS.items():
            if re.search(pattern, text.lower()):
                new_items = self._generate_items_for_test_type(test_type, text, section_name, system_type)
                items.extend(new_items)

        # If no specific patterns found, generate generic improvements
        if not items:
            items = self._generate_generic_improvements(entry, section_name, system_type)

        return items

    def _generate_items_for_test_type(self, test_type: str, feedback_text: str,
                                       section_name: str, system_type: str) -> list[EnhancedCheckItem]:
        """Generate specific items based on test type detected in feedback."""
        items = []

        if test_type == 'tolerance_test':
            # Out of Tolerance testing
            items.extend([
                EnhancedCheckItem(
                    description=f"Verify Out of Tolerance Alert Setpoint [SUPVTAG.OotAlrt.Sp] is configured correctly",
                    section=section_name,
                    acceptance_criteria="Setpoint value matches design specification",
                    method="1. Navigate to supervisory point in BMS\n2. Record current setpoint value\n3. Compare to design documentation",
                    priority="HIGH",
                    check_type="VERIFICATION"
                ),
                EnhancedCheckItem(
                    description=f"Test sensor group Out of Tolerance detection with 3+ sensors",
                    section=section_name,
                    acceptance_criteria="System correctly identifies sensor with value furthest from group average",
                    method="1. Identify sensor group with 3+ sensors\n2. Force one sensor to deviate beyond OOT setpoint\n3. Verify correct sensor flagged after time delay\n4. Verify [TAG.OotAlrt.Alrt] activates",
                    priority="HIGH",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Test Out of Tolerance with only 2 sensors remaining in group",
                    section=section_name,
                    acceptance_criteria="Supervisory OOT Alert [SUPVTAG.OotAlrt.Alrt] activates; individual sensor alerts remain OFF",
                    method="1. Configure sensor group with only 2 active sensors\n2. Force difference to exceed OOT setpoint\n3. Verify supervisory alert activates after time delay\n4. Confirm individual sensor OOT alerts stay OFF",
                    priority="HIGH",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Verify OOT Time Delay [SUPVTAG.OotAlrt.Dly] functions correctly",
                    section=section_name,
                    acceptance_criteria="Alert activates only after configured time delay expires",
                    method="1. Record configured time delay value\n2. Create OOT condition\n3. Start timer\n4. Verify alert activates at correct time",
                    priority="MEDIUM",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Test Hardware Failure exclusion from sensor group",
                    section=section_name,
                    acceptance_criteria="Sensor with [TAG.ChnlAlrt.Alrt] is excluded from OOT evaluation",
                    method="1. Force hardware failure on one sensor\n2. Verify sensor excluded from group calculations\n3. Verify OOT evaluation continues with remaining sensors",
                    priority="HIGH",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Test Out of Service [TAG.Oos] exclusion from sensor group",
                    section=section_name,
                    acceptance_criteria="Sensor commanded OOS is excluded from OOT evaluation",
                    method="1. Command one sensor to Out of Service\n2. Verify sensor excluded from group calculations\n3. Return sensor to service\n4. Verify sensor rejoins group evaluation",
                    priority="MEDIUM",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Verify No Sensors Available notification [SUPVTAG.NoSensors.vFlag]",
                    section=section_name,
                    acceptance_criteria="Notification activates when all sensors are OOS or in failure",
                    method="1. Command all sensors to OOS or simulate failures\n2. Verify NoSensors flag activates\n3. Verify PID output holds last value\n4. Return one sensor to service\n5. Verify flag clears and operation resumes",
                    priority="CRITICAL",
                    check_type="FUNCTIONAL"
                ),
            ])

        elif test_type == 'vfd_test':
            items.extend([
                EnhancedCheckItem(
                    description=f"Verify VFD frequency range configuration",
                    section=section_name,
                    acceptance_criteria="Min/Max frequency matches design: Min=__Hz, Max=__Hz",
                    method="1. Access VFD parameters\n2. Record min frequency setting\n3. Record max frequency setting\n4. Compare to design specification",
                    priority="HIGH",
                    check_type="VERIFICATION"
                ),
                EnhancedCheckItem(
                    description=f"Test VFD speed command response across full range",
                    section=section_name,
                    acceptance_criteria="VFD responds to commands from 0-100% within ±2% accuracy",
                    method="1. Command VFD to 0%, record actual\n2. Command to 25%, record actual\n3. Command to 50%, record actual\n4. Command to 75%, record actual\n5. Command to 100%, record actual",
                    priority="HIGH",
                    check_type="FUNCTIONAL"
                ),
                EnhancedCheckItem(
                    description=f"Verify VFD motor amp draw at various loads",
                    section=section_name,
                    acceptance_criteria="Motor amps within FLA rating at all tested speeds",
                    method="1. Record nameplate FLA\n2. Measure amps at 25% speed\n3. Measure amps at 50% speed\n4. Measure amps at 75% speed\n5. Measure amps at 100% speed",
                    priority="HIGH",
                    check_type="MEASUREMENT"
                ),
                EnhancedCheckItem(
                    description=f"Test VFD fault/alarm feedback to BMS",
                    section=section_name,
                    acceptance_criteria="VFD faults correctly reported to BMS within 5 seconds",
                    method="1. Simulate VFD fault condition\n2. Verify fault appears in BMS\n3. Record response time\n4. Clear fault and verify BMS updates",
                    priority="CRITICAL",
                    check_type="FUNCTIONAL"
                ),
            ])

        elif test_type == 'setpoint_range_test':
            items.extend([
                EnhancedCheckItem(
                    description=f"Document all setpoint names with associated sensor tags",
                    section=section_name,
                    acceptance_criteria="Each setpoint has documented sensor tag and description",
                    method="1. List all setpoints from SOO\n2. Identify associated sensor for each\n3. Record sensor tag [TAG] format\n4. Document in table format",
                    priority="HIGH",
                    check_type="DOCUMENTATION"
                ),
                EnhancedCheckItem(
                    description=f"Record setpoint acceptable ranges and out-of-tolerance thresholds",
                    section=section_name,
                    acceptance_criteria="Each setpoint has documented: Normal range, Warning range, Alarm range",
                    method="1. For each setpoint, document:\n   - Normal operating range\n   - Warning threshold (if applicable)\n   - Alarm/fault threshold\n2. Include units for all values",
                    priority="HIGH",
                    check_type="DOCUMENTATION"
                ),
                EnhancedCheckItem(
                    description=f"Verify setpoint out-of-range impacts on system mode",
                    section=section_name,
                    acceptance_criteria="Document what mode changes occur when setpoint exceeds range",
                    method="1. For each critical setpoint:\n   - Force value above normal range\n   - Record system mode change\n   - Record any alarms generated\n   - Return to normal and verify recovery",
                    priority="HIGH",
                    check_type="FUNCTIONAL"
                ),
            ])

        elif test_type == 'sensor_group_test':
            items.extend([
                EnhancedCheckItem(
                    description=f"Verify sensor group configuration and member sensors",
                    section=section_name,
                    acceptance_criteria="All member sensors correctly assigned to group",
                    method="1. Identify all sensor groups\n2. List member sensors for each group\n3. Verify against design documentation",
                    priority="MEDIUM",
                    check_type="VERIFICATION"
                ),
                EnhancedCheckItem(
                    description=f"Test sensor group Min/Max/Average calculations",
                    section=section_name,
                    acceptance_criteria="Calculated values match manual verification within ±0.1",
                    method="1. Record all sensor values in group\n2. Manually calculate min, max, average\n3. Compare to BMS displayed values",
                    priority="MEDIUM",
                    check_type="VERIFICATION"
                ),
            ])

        return items

    def _generate_generic_improvements(self, entry, section_name: str, system_type: str) -> list[EnhancedCheckItem]:
        """Generate generic improvements when no specific pattern detected."""
        items = []

        # If feedback mentions "more detail" or "detailed"
        if 'detail' in entry.feedback_text.lower():
            items.append(EnhancedCheckItem(
                description=f"[Enhanced] Perform detailed verification with documented values",
                section=section_name,
                acceptance_criteria="All values recorded with units and compared to design specification",
                method="1. Record actual value with units\n2. Record expected value from design\n3. Calculate deviation\n4. Document pass/fail based on tolerance",
                priority="MEDIUM",
                check_type="VERIFICATION"
            ))

        # If feedback mentions specific suggestion
        if entry.suggested_improvement:
            items.append(EnhancedCheckItem(
                description=f"[Suggested] {entry.suggested_improvement}",
                section=section_name,
                acceptance_criteria="Verify per suggestion requirements",
                method="Perform verification as described",
                priority="MEDIUM",
                check_type="VERIFICATION"
            ))

        return items


# Global enhancer instance
_enhancer: Optional[FeedbackEnhancer] = None


def get_feedback_enhancer() -> FeedbackEnhancer:
    """Get the global feedback enhancer instance."""
    global _enhancer
    if _enhancer is None:
        _enhancer = FeedbackEnhancer()
    return _enhancer

