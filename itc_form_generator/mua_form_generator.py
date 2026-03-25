"""MUA Form Generator - Creates ITC forms specifically for Makeup Air Units.

Generates check items that directly match the MUA SOO structure:
- Setpoint verification from tables
- Operating mode tests
- Alert/alarm testing
- Component failure state verification
- Interlock testing
"""

import logging
from typing import Optional
from .models import (
    InspectionForm, FormSection, CheckItem, FormType, Priority, CheckItemType
)
from .mua_parser import MUASystem, MUASetpoint, MUAAlert, MUAOperatingMode, MUAComponent

logger = logging.getLogger(__name__)


class MUAFormGenerator:
    """Generates ITC forms specifically for MUA systems."""

    def __init__(self, mua_system: MUASystem):
        self.system = mua_system
        self.item_counter = 0

    def _next_id(self, prefix: str) -> str:
        """Generate next item ID."""
        self.item_counter += 1
        return f"{prefix}-{self.item_counter:03d}"

    def generate_form(self) -> InspectionForm:
        """Generate complete ITC form for MUA system."""
        self.item_counter = 0

        form = InspectionForm(
            form_type=FormType.ITC,
            title=f"ITC - {self.system.name}",
            system=self.system.name,
            system_tag=self.system.tag,
            project="",
            version="1.0"
        )

        # Add sections in logical order
        form.sections.append(self._create_header_section())
        form.sections.append(self._create_documentation_section())
        form.sections.append(self._create_safety_section())
        form.sections.append(self._create_component_verification_section())
        form.sections.append(self._create_setpoint_verification_section())
        form.sections.append(self._create_operating_modes_section())
        form.sections.append(self._create_alerts_section())
        form.sections.append(self._create_failure_states_section())
        form.sections.append(self._create_interlocks_section())
        form.sections.append(self._create_communications_section())
        form.sections.append(self._create_utility_loss_section())
        form.sections.append(self._create_final_verification_section())

        return form

    def _create_header_section(self) -> FormSection:
        """Create header/general information section."""
        section = FormSection(
            title="General Information",
            description="Project and equipment identification"
        )

        items = [
            ("Verify equipment nameplate matches drawings", "Nameplate data matches design documents"),
            ("Record MUA unit tag/identifier", "Tag recorded: ____________"),
            ("Verify unit location matches drawings", "Location correct per design"),
            ("Confirm MUA is sized for N+1 redundancy as specified", "Redundancy configuration verified"),
            ("Verify lead-lag configuration with paired unit", "Lead-lag partner identified: ____________"),
        ]

        for desc, criteria in items:
            section.check_items.append(CheckItem(
                id=self._next_id("GEN"),
                description=desc,
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH,
                acceptance_criteria=criteria
            ))

        return section

    def _create_documentation_section(self) -> FormSection:
        """Create documentation verification section."""
        section = FormSection(
            title="Documentation Verification",
            description="Verify all required documentation per SOO Section 1.2"
        )

        docs = [
            ("25 90 05 - Common Work Results for Integrated Automation Control Sequences", Priority.CRITICAL),
            ("25 60 10 - Mechanical Points List", Priority.CRITICAL),
            ("25 60 15 - EPMS Points List", Priority.HIGH),
            ("IC712 - P&ID, MUA", Priority.CRITICAL),
            ("Test and Balance (TAB) report with setpoint values", Priority.HIGH),
            ("Manufacturer O&M manuals for unitary controller", Priority.MEDIUM),
        ]

        for doc, priority in docs:
            section.check_items.append(CheckItem(
                id=self._next_id("DOC"),
                description=f"Verify availability of: {doc}",
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria="Document available and current revision confirmed"
            ))

        return section

    def _create_safety_section(self) -> FormSection:
        """Create safety verification section."""
        section = FormSection(
            title="Safety & Interlocks",
            description="Verify safety systems and interlocks per SOO"
        )

        safety_items = [
            ("Verify smoke alarm interlock shuts down MUA", "MUA shuts down on smoke alarm activation", Priority.CRITICAL, True),
            ("Verify fire alarm system interlock", "MUA shuts down on fire alarm", Priority.CRITICAL, True),
            ("Confirm LOTO procedures are in place", "LOTO procedures documented and accessible", Priority.CRITICAL, False),
            ("Verify emergency stop functionality", "E-stop shuts down unit immediately", Priority.CRITICAL, True),
        ]

        for desc, criteria, priority, is_functional in safety_items:
            section.check_items.append(CheckItem(
                id=self._next_id("SAF"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL if is_functional else CheckItemType.VERIFICATION,
                priority=priority,
                acceptance_criteria=criteria,
                method="1. Coordinate with facility personnel\n2. Simulate alarm condition\n3. Verify MUA shutdown\n4. Reset and verify normal operation" if is_functional else ""
            ))

        return section

    def _create_component_verification_section(self) -> FormSection:
        """Create component verification section from parsed components."""
        section = FormSection(
            title="Component Verification",
            description=f"Verify all {len(self.system.components)} components per SOO Section 3.1"
        )

        if not self.system.components:
            # Default components if none parsed
            default_components = [
                "Supply Air Isolation Damper",
                "Outside Air Isolation Damper",
                "Supply Fan Array (VFD-driven)",
                "Electric Heating Coil Assembly (SCR-controlled)",
                "Air Filter Bank with Differential Pressure Sensor",
                "Supply Air Combination Temperature & Humidity Transmitter",
                "Outside Air Combination Temperature & Humidity Transmitter",
                "Supply Air Duct Pressure Transmitter"
            ]
            for comp_name in default_components:
                self.system.components.append(MUAComponent(name=comp_name))

        for comp in self.system.components:
            # Installation verification
            section.check_items.append(CheckItem(
                id=self._next_id("CMP"),
                description=f"Verify {comp.name} is installed per drawings",
                check_type=CheckItemType.VISUAL,
                priority=Priority.HIGH,
                acceptance_criteria="Component installed correctly, accessible, and labeled"
            ))

            # Add specific checks based on component type
            if 'damper' in comp.name.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("CMP"),
                    description=f"Verify {comp.name} actuator stroke and end switches",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria="Damper strokes fully open/closed, end switches indicate correctly",
                    method="1. Command damper OPEN\n2. Verify end switch indicates OPEN\n3. Command damper CLOSED\n4. Verify end switch indicates CLOSED\n5. Record actuator stroke time: ______ seconds"
                ))

            elif 'fan' in comp.name.lower() or 'vfd' in comp.name.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("CMP"),
                    description=f"Verify {comp.name} rotation and VFD operation",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria="Fan rotates correct direction, VFD responds to speed commands",
                    method="1. Bump test to verify rotation direction\n2. Command to minimum speed, record: ____%\n3. Command to maximum speed, record: ____%\n4. Verify smooth acceleration/deceleration"
                ))

            elif 'heater' in comp.name.lower() or 'heating' in comp.name.lower() or 'scr' in comp.name.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("CMP"),
                    description=f"Verify {comp.name} stages and SCR modulation",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria="Heater stages operate, SCR modulates smoothly 0-100%",
                    method="1. Enable heating mode\n2. Command SCR to 25%, verify operation\n3. Command SCR to 50%, verify operation\n4. Command SCR to 100%, verify operation\n5. Record supply air temp rise: _____°F"
                ))

            elif 'filter' in comp.name.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("CMP"),
                    description=f"Verify {comp.name} DP sensor and alert setpoint",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.MEDIUM,
                    acceptance_criteria="DP sensor reads correctly, high DP alert functions",
                    method="1. Record current filter DP: _____\"WC\n2. Verify DP reading is reasonable for clean filters\n3. Verify High Filter DP setpoint: _____\"WC\n4. Verify time delay: _____ seconds"
                ))

            elif 'transmitter' in comp.name.lower() or 'sensor' in comp.name.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("CMP"),
                    description=f"Verify {comp.name} calibration and reading",
                    check_type=CheckItemType.MEASUREMENT,
                    priority=Priority.HIGH,
                    acceptance_criteria="Sensor reading within ±2% of reference instrument",
                    method="1. Compare reading to calibrated reference instrument\n2. Record sensor reading: _____\n3. Record reference reading: _____\n4. Calculate deviation: _____%"
                ))

        return section

    def _create_setpoint_verification_section(self) -> FormSection:
        """Create setpoint verification section from parsed setpoints."""
        section = FormSection(
            title="Setpoint Verification",
            description=f"Verify all {len(self.system.setpoints)} setpoints per SOO tables"
        )

        if not self.system.setpoints:
            # Default setpoints from MUA SOO if none parsed
            default_setpoints = [
                MUASetpoint("Supply Air Low Temperature Setpoint", "50°F", "N/A", "°F"),
                MUASetpoint("Supply Air High Relative Humidity Setpoint", "90%", "N/A", "%"),
                MUASetpoint("High Humidity Offset", "5%", "N/A", "%"),
                MUASetpoint("Duct Static Pressure Setpoint", "TBD at TAB", "N/A", "inWC"),
                MUASetpoint("Min Fan Array Speed Setpoint", "TBD at TAB", "N/A", "%"),
                MUASetpoint("Max Fan Array Speed Setpoint", "TBD at TAB", "N/A", "%"),
                MUASetpoint("Fan Array Run Status Mismatch", "N/A", "120 Seconds", ""),
                MUASetpoint("Low Duct Static Pressure", "50% of Pressure SP", "300 Seconds", ""),
                MUASetpoint("High Filter Differential Pressure Setpoint", "TBD at TAB", "300 Seconds", "inWC"),
                MUASetpoint("Damper Actuator End Switch Mismatch Alert", "N/A", "Runtime + 60s", ""),
            ]
            self.system.setpoints = default_setpoints

        for sp in self.system.setpoints:
            # Create verification item
            method_steps = [
                "1. Navigate to setpoint in BMS/SCADA",
                f"2. Record current value: _____ {sp.units}",
                f"3. Compare to design value: {sp.value}",
            ]

            if sp.time_delay and sp.time_delay != "N/A":
                method_steps.append(f"4. Verify time delay: {sp.time_delay}")

            if sp.adjustable:
                method_steps.append(f"5. Verify setpoint is field adjustable")

            section.check_items.append(CheckItem(
                id=self._next_id("SP"),
                description=f"Verify {sp.parameter}",
                check_type=CheckItemType.VERIFICATION,
                priority=Priority.HIGH,
                acceptance_criteria=f"Setpoint matches design: {sp.value}" +
                                   (f", Time Delay: {sp.time_delay}" if sp.time_delay != "N/A" else ""),
                expected_value=sp.value,
                method="\n".join(method_steps)
            ))

            # If setpoint has a time delay, create functional test
            if sp.time_delay and sp.time_delay != "N/A" and 'seconds' in sp.time_delay.lower():
                section.check_items.append(CheckItem(
                    id=self._next_id("SP"),
                    description=f"Test {sp.parameter} time delay function",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria=f"Alert/action occurs after {sp.time_delay}",
                    method=f"1. Create condition that triggers {sp.parameter}\n"
                           f"2. Start timer\n"
                           f"3. Verify alert/action at {sp.time_delay}\n"
                           f"4. Record actual time: _____ seconds"
                ))

        return section

    def _create_operating_modes_section(self) -> FormSection:
        """Create operating modes test section from parsed modes."""
        section = FormSection(
            title="Operating Mode Tests",
            description=f"Test all {len(self.system.operating_modes)} operating modes per SOO Section 3.6"
        )

        if not self.system.operating_modes:
            # Default modes from MUA SOO
            default_modes = [
                MUAOperatingMode(
                    name="Heating Mode",
                    conditions=["Outside Air Dry Bulb Temperature is below Supply Air Low Temperature Setpoint"],
                    actions=["Electric heating SCR bank modulates to maintain Supply Air Temperature at setpoint"]
                ),
                MUAOperatingMode(
                    name="High Relative Humidity Mode",
                    conditions=["Outside Air Relative Humidity is above Supply Air High Relative Humidity Setpoint"],
                    actions=["Electric heating SCR bank modulates to maintain Supply Air RH between setpoint and setpoint minus offset"]
                ),
                MUAOperatingMode(
                    name="Economization Mode",
                    conditions=[
                        "Outside Air Dry Bulb Temperature is above Supply Air Low Temperature Setpoint",
                        "Outside Air Relative Humidity is below Supply Air High RH Setpoint minus Offset"
                    ],
                    actions=["Electric heating SCR bank is locked out"]
                ),
            ]
            self.system.operating_modes = default_modes

        for mode in self.system.operating_modes:
            # Create test for each mode
            method_steps = ["Test Procedure:"]

            for i, condition in enumerate(mode.conditions, 1):
                method_steps.append(f"{i}. Create condition: {condition[:100]}")

            method_steps.append(f"{len(mode.conditions)+1}. Observe system response")

            for i, action in enumerate(mode.actions, len(mode.conditions)+2):
                method_steps.append(f"{i}. Verify: {action[:100]}")

            method_steps.append(f"{len(mode.conditions)+len(mode.actions)+2}. Return to normal conditions")
            method_steps.append(f"{len(mode.conditions)+len(mode.actions)+3}. Verify system returns to normal operation")

            section.check_items.append(CheckItem(
                id=self._next_id("MODE"),
                description=f"Test {mode.name}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                acceptance_criteria=f"System enters {mode.name} under correct conditions and performs specified actions",
                method="\n".join(method_steps)
            ))

            # Add mode transition test
            section.check_items.append(CheckItem(
                id=self._next_id("MODE"),
                description=f"Verify {mode.name} entry/exit transitions",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.HIGH,
                acceptance_criteria="Smooth transition with no oscillation or hunting",
                method=f"1. Monitor system during transition into {mode.name}\n"
                       f"2. Record any oscillation or hunting: Yes/No\n"
                       f"3. Monitor system during transition out of {mode.name}\n"
                       f"4. Verify proper handoff to next mode"
            ))

        return section

    def _create_alerts_section(self) -> FormSection:
        """Create alerts/alarms test section from parsed alerts."""
        section = FormSection(
            title="Alert & Alarm Testing",
            description=f"Test all {len(self.system.alerts)} alerts per SOO"
        )

        if not self.system.alerts:
            # Default alerts from MUA SOO
            default_alerts = [
                MUAAlert("MUA Run Status Mismatch", "Supply Fan Array indicates Off when unit is enabled", "120 Seconds", True, True),
                MUAAlert("MUA Fault Status", "MUA controller reports fault", "", True, True),
                MUAAlert("Low Duct Static Pressure", "Duct static below 50% of setpoint when fan running", "300 Seconds", False, False),
                MUAAlert("High Discharge Pressure", "High discharge pressure switch indicates on", "", False, True),
                MUAAlert("Damper End Switch Mismatch", "Damper position doesn't match command after timeout", "Runtime + 60s", False, False),
                MUAAlert("Electric Heater Fail to Run", "Heater fails to operate when commanded", "", False, False),
                MUAAlert("High Filter Differential Pressure", "Filter DP exceeds setpoint", "300 Seconds", False, False),
            ]
            self.system.alerts = default_alerts

        for alert in self.system.alerts:
            method_steps = [
                f"1. Document pre-test conditions",
                f"2. Simulate fault condition for: {alert.name}",
            ]

            if alert.time_delay:
                method_steps.append(f"3. Start timer - expected delay: {alert.time_delay}")
                method_steps.append(f"4. Verify alert activates after time delay")
                method_steps.append(f"5. Record actual time: _____ seconds")
            else:
                method_steps.append(f"3. Verify alert activates immediately")

            if alert.causes_shutdown:
                method_steps.append(f"6. Verify MUA shuts down on this alert")

            if alert.is_latching:
                method_steps.append(f"7. Clear fault condition")
                method_steps.append(f"8. Verify alert remains latched (requires manual reset)")
                method_steps.append(f"9. Perform manual reset")
                method_steps.append(f"10. Verify alert clears and unit can restart")
            else:
                method_steps.append(f"6. Clear fault condition")
                method_steps.append(f"7. Verify alert clears automatically")

            section.check_items.append(CheckItem(
                id=self._next_id("ALT"),
                description=f"Test Alert: {alert.name}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL if alert.causes_shutdown else Priority.HIGH,
                acceptance_criteria=f"Alert activates correctly" +
                                   (f" after {alert.time_delay}" if alert.time_delay else "") +
                                   (", causes shutdown" if alert.causes_shutdown else "") +
                                   (", requires manual reset" if alert.is_latching else ", auto-clears"),
                method="\n".join(method_steps)
            ))

        return section

    def _create_failure_states_section(self) -> FormSection:
        """Create failure states verification section."""
        section = FormSection(
            title="Failure States Verification",
            description="Verify component failure states per SOO TABLE 1"
        )

        # Find components with failure states defined
        components_with_states = [c for c in self.system.components
                                  if c.failure_state_off or c.failure_state_signal_loss or c.failure_state_power_loss]

        if not components_with_states:
            # Default failure states from MUA SOO
            default_states = [
                ("Supply Air Isolation Damper", "Closed", "Fail Closed", "Fail Closed"),
                ("Outside Air Isolation Damper", "Closed", "Fail Closed", "Fail Closed"),
                ("MUA Supply Fan Array", "Off", "Off", "Off"),
            ]
            for name, off, signal, power in default_states:
                comp = MUAComponent(
                    name=name,
                    failure_state_off=off,
                    failure_state_signal_loss=signal,
                    failure_state_power_loss=power
                )
                components_with_states.append(comp)

        for comp in components_with_states:
            # Test Unit Off state
            if comp.failure_state_off:
                section.check_items.append(CheckItem(
                    id=self._next_id("FAIL"),
                    description=f"Verify {comp.name} position when unit is OFF",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.HIGH,
                    acceptance_criteria=f"Component is {comp.failure_state_off} when unit disabled",
                    method=f"1. Disable MUA unit\n2. Observe {comp.name}\n3. Verify position: {comp.failure_state_off}"
                ))

            # Test Signal Loss state
            if comp.failure_state_signal_loss:
                section.check_items.append(CheckItem(
                    id=self._next_id("FAIL"),
                    description=f"Verify {comp.name} on loss of control signal",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.CRITICAL,
                    acceptance_criteria=f"Component goes to {comp.failure_state_signal_loss} on signal loss",
                    method=f"1. With unit running, disconnect control signal to {comp.name}\n"
                           f"2. Verify component goes to: {comp.failure_state_signal_loss}\n"
                           f"3. Reconnect signal and verify normal operation resumes"
                ))

            # Test Power Loss state
            if comp.failure_state_power_loss:
                section.check_items.append(CheckItem(
                    id=self._next_id("FAIL"),
                    description=f"Verify {comp.name} on loss of power",
                    check_type=CheckItemType.FUNCTIONAL,
                    priority=Priority.CRITICAL,
                    acceptance_criteria=f"Component goes to {comp.failure_state_power_loss} on power loss",
                    method=f"1. With unit running, remove power to {comp.name}\n"
                           f"2. Verify component goes to: {comp.failure_state_power_loss}\n"
                           f"3. Restore power and verify normal operation resumes"
                ))

        return section

    def _create_interlocks_section(self) -> FormSection:
        """Create interlocks verification section."""
        section = FormSection(
            title="Interlock Verification",
            description=f"Verify all {len(self.system.interlocks)} interlocks per SOO"
        )

        if not self.system.interlocks:
            # Default interlocks
            self.system.interlocks = [
                "Smoke alarm shutdown",
                "Fire alarm system interlock",
                "Damper end switch interlock to VFD Enable",
                "DO Enable/Disable Command from BMS",
                "DI Run Status to BMS",
                "DI Fault Status to BMS"
            ]

        for interlock in self.system.interlocks:
            section.check_items.append(CheckItem(
                id=self._next_id("INT"),
                description=f"Test interlock: {interlock}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                acceptance_criteria=f"Interlock functions correctly",
                method=f"1. Document pre-test conditions\n"
                       f"2. Activate interlock condition: {interlock}\n"
                       f"3. Verify expected system response\n"
                       f"4. Clear interlock condition\n"
                       f"5. Verify system returns to normal"
            ))

        return section

    def _create_communications_section(self) -> FormSection:
        """Create communications verification section."""
        section = FormSection(
            title="Communications Verification",
            description="Verify Modbus RTU communication per SOO Section 3.2"
        )

        comm_checks = [
            ("Verify unitary controller Modbus RTU address", "Address documented: _____", Priority.HIGH),
            ("Verify RS-485 connection to BMS ICP", "Physical connection verified", Priority.HIGH),
            ("Test Modbus communication from BMS to MUA controller", "All points read correctly", Priority.CRITICAL),
            ("Verify Enable/Disable command (DO) from BMS", "Command toggles MUA on/off", Priority.CRITICAL),
            ("Verify Run Status feedback (DI) to BMS", "Status matches actual unit state", Priority.CRITICAL),
            ("Verify Fault Status feedback (DI) to BMS", "Fault status indicates correctly", Priority.CRITICAL),
            ("Test communication failure handling", "BMS alarms on comm loss", Priority.HIGH),
        ]

        for desc, criteria, priority in comm_checks:
            section.check_items.append(CheckItem(
                id=self._next_id("COM"),
                description=desc,
                check_type=CheckItemType.FUNCTIONAL,
                priority=priority,
                acceptance_criteria=criteria
            ))

        return section

    def _create_utility_loss_section(self) -> FormSection:
        """Create utility loss mode testing section per SOO Section 3.8."""
        section = FormSection(
            title="Utility Loss Mode Testing",
            description="Test utility loss scenarios per SOO Section 3.8"
        )

        scenarios = [
            (
                "Momentary Disturbance (<5 seconds)",
                "MUA de-energizes on power loss, restarts automatically on power restoration",
                "1. Simulate momentary power loss (<5 seconds)\n"
                "2. Verify MUA de-energizes\n"
                "3. Restore power\n"
                "4. Verify MUA restarts automatically"
            ),
            (
                "Battery Operation Transition (5-45 seconds)",
                "MUA disabled by BMS after 5 seconds, does not run on generator, restarts on utility restoration",
                "1. Simulate utility power loss\n"
                "2. Verify MUA disabled by BMS after 5 seconds\n"
                "3. Confirm MUA does NOT run on generator power\n"
                "4. Restore utility power\n"
                "5. Verify Enable signal automatically restored"
            ),
            (
                "Controlled Shutdown (>45 seconds)",
                "MUA disabled by BMS after 5 seconds, remains off during generator operation, restarts on utility restoration",
                "1. Simulate extended utility power loss\n"
                "2. Verify MUA disabled by BMS after 5 seconds\n"
                "3. Confirm MUA remains off during generator operation\n"
                "4. Restore utility power\n"
                "5. Verify Enable signal automatically restored\n"
                "6. Verify MUA restarts normally"
            ),
        ]

        for name, criteria, method in scenarios:
            section.check_items.append(CheckItem(
                id=self._next_id("UTL"),
                description=f"Test {name}",
                check_type=CheckItemType.FUNCTIONAL,
                priority=Priority.CRITICAL,
                acceptance_criteria=criteria,
                method=method
            ))

        return section

    def _create_final_verification_section(self) -> FormSection:
        """Create final verification and sign-off section."""
        section = FormSection(
            title="Final Verification & Sign-off",
            description="Complete final checks and documentation"
        )

        final_checks = [
            ("Verify all setpoints documented in as-built records", "As-built documentation complete", Priority.HIGH),
            ("Confirm TAB values entered for TBD setpoints", "All TAB-determined values recorded", Priority.HIGH),
            ("Verify lead-lag rotation programming", "Runtime equalization verified", Priority.MEDIUM),
            ("Confirm all alerts route to SCADA correctly", "SCADA alarm routing verified", Priority.HIGH),
            ("Complete operator training on MUA operation", "Training sign-off obtained", Priority.MEDIUM),
            ("Provide O&M documentation to facility", "Documentation handover complete", Priority.MEDIUM),
        ]

        for desc, criteria, priority in final_checks:
            section.check_items.append(CheckItem(
                id=self._next_id("FIN"),
                description=desc,
                check_type=CheckItemType.DOCUMENTATION,
                priority=priority,
                acceptance_criteria=criteria
            ))

        return section


def generate_mua_form(mua_system: MUASystem) -> InspectionForm:
    """Convenience function to generate MUA ITC form."""
    generator = MUAFormGenerator(mua_system)
    return generator.generate_form()

