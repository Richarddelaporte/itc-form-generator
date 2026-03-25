"""MUA SOO Parser - Specialized parser for Makeup Air Unit control sequences.

Parses structured SOO documents in the Meta data center format with:
- Numbered sections (3.1, 3.2, etc.)
- Setpoint tables (PARAMETER, SET POINT, TIME DELAY)
- Operating modes (Heating, High RH, Economization, Utility Loss)
- Alerts and failure modes
- Component specifications
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MUASetpoint:
    """A setpoint extracted from the SOO."""
    parameter: str
    value: str
    time_delay: str = "N/A"
    units: str = ""
    adjustable: bool = True
    notes: str = ""


@dataclass
class MUAAlert:
    """An alert/alarm extracted from the SOO."""
    name: str
    description: str
    time_delay: str = ""
    is_latching: bool = False
    causes_shutdown: bool = False
    section: str = ""


@dataclass
class MUAOperatingMode:
    """An operating mode extracted from the SOO."""
    name: str
    conditions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    section: str = ""


@dataclass
class MUAComponent:
    """A component extracted from the SOO."""
    name: str
    tag: str = ""
    component_type: str = ""
    failure_state_off: str = ""
    failure_state_signal_loss: str = ""
    failure_state_power_loss: str = ""
    section: str = ""


@dataclass
class MUASystem:
    """Complete MUA system extracted from SOO."""
    name: str = "Makeup Air Unit"
    tag: str = "MUA"
    description: str = ""
    components: list[MUAComponent] = field(default_factory=list)
    setpoints: list[MUASetpoint] = field(default_factory=list)
    alerts: list[MUAAlert] = field(default_factory=list)
    operating_modes: list[MUAOperatingMode] = field(default_factory=list)
    interlocks: list[str] = field(default_factory=list)
    sections: dict = field(default_factory=dict)


class MUASOOParser:
    """Parser for MUA control sequence documents."""

    def __init__(self):
        self.system = MUASystem()

    def parse(self, content: str) -> MUASystem:
        """Parse MUA SOO content and extract all elements."""
        logger.info("Parsing MUA SOO document...")

        # Clean content
        content = self._clean_content(content)

        # Extract system info
        self._extract_system_info(content)

        # Extract components
        self._extract_components(content)

        # Extract setpoint tables
        self._extract_setpoints(content)

        # Extract operating modes
        self._extract_operating_modes(content)

        # Extract alerts
        self._extract_alerts(content)

        # Extract interlocks
        self._extract_interlocks(content)

        # Extract failure states table
        self._extract_failure_states(content)

        logger.info(f"Parsed MUA system with {len(self.system.components)} components, "
                   f"{len(self.system.setpoints)} setpoints, {len(self.system.alerts)} alerts, "
                   f"{len(self.system.operating_modes)} modes")

        return self.system

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        # Normalize quotes
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        return content

    def _extract_system_info(self, content: str):
        """Extract system name and description."""
        # Look for title
        title_match = re.search(r'CONTROL SEQUENCES FOR\s+(.+?)(?:\n|V\d)', content, re.IGNORECASE)
        if title_match:
            self.system.name = title_match.group(1).strip()
            # Create tag from name
            words = self.system.name.split()
            self.system.tag = ''.join(w[0].upper() for w in words if w[0].isalpha())

        # Look for general overview
        overview_match = re.search(
            r'3\.1\s+GENERAL OVERVIEW\s*(.*?)(?=3\.2|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if overview_match:
            desc = overview_match.group(1).strip()
            # Get first paragraph
            first_para = desc.split('\n\n')[0]
            self.system.description = re.sub(r'\s+', ' ', first_para)[:500]

    def _extract_components(self, content: str):
        """Extract components from Major Equipment section."""
        # Look for Major Equipment list
        equip_match = re.search(
            r'Major Equipment[:\s]*(.*?)(?:Major Instruments|2\.|B\.|C\.|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if equip_match:
            equip_text = equip_match.group(1)
            # Extract items like "a. Supply Air Isolation Damper"
            items = re.findall(r'[a-z]\.\s*([^\n]+)', equip_text, re.IGNORECASE)

            for item in items:
                item = item.strip()
                if item:
                    comp = MUAComponent(name=item)
                    # Try to extract type
                    if 'damper' in item.lower():
                        comp.component_type = 'Damper'
                    elif 'fan' in item.lower():
                        comp.component_type = 'Fan'
                    elif 'coil' in item.lower() or 'heating' in item.lower():
                        comp.component_type = 'Heater'
                    elif 'filter' in item.lower():
                        comp.component_type = 'Filter'
                    elif 'vfd' in item.lower():
                        comp.component_type = 'VFD'
                    self.system.components.append(comp)

        # Look for Major Instruments
        instr_match = re.search(
            r'Major Instruments[:\s]*(.*?)(?:C\.|D\.|3\.\d|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if instr_match:
            instr_text = instr_match.group(1)
            items = re.findall(r'[a-z]\.\s*([^\n]+)', instr_text, re.IGNORECASE)

            for item in items:
                item = item.strip()
                if item:
                    comp = MUAComponent(name=item, component_type='Instrument')
                    self.system.components.append(comp)

    def _extract_setpoints(self, content: str):
        """Extract setpoint tables from the document."""
        # Pattern for setpoint tables
        # Look for "Critical set points" or "Critical Setpoints" sections
        table_sections = re.findall(
            r'(?:Critical [Ss]et\s*[Pp]oints?|PARAMETER).*?(?=B\.\s+Manual|C\.\s+Normal|\Z)',
            content,
            re.DOTALL
        )

        for section in table_sections:
            # Extract table rows
            # Pattern: PARAMETER | SET POINT | TIME DELAY
            rows = re.findall(
                r'([A-Z][A-Za-z\s]+(?:Setpoint|Alert|Pressure|Speed|Temperature|Humidity|Offset)[^\n]*?)\s+'
                r'((?:\d+[°%#.\d]*\s*[°%FfCc]?[A-Za-z."\']*|N/A|TBD)[^\n]*?)\s+'
                r'((?:\d+\s*[Ss]econds?|N/A)[^\n]*)',
                section
            )

            for row in rows:
                param = row[0].strip()
                value = row[1].strip()
                delay = row[2].strip()

                # Parse units from value
                units = ""
                if '°F' in value or '°f' in value:
                    units = '°F'
                elif '%' in value:
                    units = '%'
                elif 'w.c.' in value.lower() or '"' in value:
                    units = 'inWC'

                # Check for notes
                note_match = re.search(r'\{Note\s*\d+\}', value)
                notes = ""
                if note_match:
                    notes = note_match.group(0)
                    value = value.replace(notes, '').strip()

                sp = MUASetpoint(
                    parameter=param,
                    value=value,
                    time_delay=delay,
                    units=units,
                    notes=notes
                )
                self.system.setpoints.append(sp)

        # Also look for inline setpoints
        inline_setpoints = re.findall(
            r'(?:maintain|setpoint|set\s*point)[:\s]+([^.]+?(?:\d+[°%]?\s*[°FfCc%]?[A-Za-z.]*)[^.]*)',
            content,
            re.IGNORECASE
        )

        for sp_text in inline_setpoints:
            # Extract value
            val_match = re.search(r'(\d+(?:\.\d+)?)\s*([°%]?\s*[°FfCcRrHh%]*)', sp_text)
            if val_match:
                value = val_match.group(1) + val_match.group(2).strip()
                param = sp_text[:sp_text.find(value)].strip()
                if param and value:
                    sp = MUASetpoint(
                        parameter=param[:100],
                        value=value
                    )
                    # Check if not duplicate
                    if not any(s.parameter == sp.parameter for s in self.system.setpoints):
                        self.system.setpoints.append(sp)

    def _extract_operating_modes(self, content: str):
        """Extract operating modes from the document."""
        # Look for numbered mode sections
        mode_patterns = [
            (r'Heating Mode\s*(.*?)(?=\d+\.\s+[A-Z]|\Z)', 'Heating Mode'),
            (r'High Relative Humidity Mode\s*(.*?)(?=\d+\.\s+[A-Z]|\Z)', 'High Relative Humidity Mode'),
            (r'Economization Mode\s*(.*?)(?=D\.\s+Failure|E\.\s+Alert|\Z)', 'Economization Mode'),
            (r'Utility Loss Mode\s*(.*?)(?=END OF SECTION|\Z)', 'Utility Loss Mode'),
            (r'Momentary Disturbance[^\n]*\s*(.*?)(?=B\.\s+Battery|\Z)', 'Momentary Disturbance'),
            (r'Battery Operation Transition[^\n]*\s*(.*?)(?=C\.\s+Controlled|\Z)', 'Battery Operation Transition'),
            (r'Controlled Shutdown[^\n]*\s*(.*?)(?=END|\Z)', 'Controlled Shutdown'),
        ]

        for pattern, mode_name in mode_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                mode_text = match.group(1).strip()

                # Extract conditions (when/if statements)
                conditions = re.findall(
                    r'(?:When|If|Upon)[^,.:]+(?:[,:][^.]+)?',
                    mode_text,
                    re.IGNORECASE
                )

                # Extract actions (shall/will statements)
                actions = re.findall(
                    r'(?:shall|will)[^.]+\.',
                    mode_text,
                    re.IGNORECASE
                )

                mode = MUAOperatingMode(
                    name=mode_name,
                    conditions=[c.strip()[:200] for c in conditions[:5]],
                    actions=[a.strip()[:200] for a in actions[:5]]
                )
                self.system.operating_modes.append(mode)

    def _extract_alerts(self, content: str):
        """Extract alerts and alarms from the document."""
        # Look for Alerts sections
        alert_sections = re.findall(
            r'(?:E\.\s+)?Alerts?(?: and Faults)?\s*(.*?)(?=3\.\d|END|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        for section in alert_sections:
            # Extract numbered alerts
            alerts = re.findall(
                r'\d+\.\s*([^\n]+(?:\n(?!\d+\.)[^\n]+)*)',
                section
            )

            for alert_text in alerts:
                alert_text = alert_text.strip()
                if len(alert_text) < 10:
                    continue

                # Extract time delay if present
                delay_match = re.search(r'(\d+)\s*[Ss]econds?', alert_text)
                delay = f"{delay_match.group(1)} Seconds" if delay_match else ""

                # Check if causes shutdown
                causes_shutdown = 'shutdown' in alert_text.lower() or 'shut down' in alert_text.lower()

                # Check if latching
                is_latching = 'latching' in alert_text.lower() or 'manual reset' in alert_text.lower()

                alert = MUAAlert(
                    name=alert_text[:100],
                    description=alert_text,
                    time_delay=delay,
                    causes_shutdown=causes_shutdown,
                    is_latching=is_latching
                )
                self.system.alerts.append(alert)

        # Also extract alerts from inline text
        inline_alerts = re.findall(
            r'(?:an alert shall be generated|alert is raised)[^.]*\.',
            content,
            re.IGNORECASE
        )

        for alert_text in inline_alerts:
            # Find the context before this
            idx = content.find(alert_text)
            context_start = max(0, idx - 200)
            context = content[context_start:idx]

            # Get the condition that triggers the alert
            condition = re.search(r'(?:If|When|Upon)[^.]+$', context)
            if condition:
                alert = MUAAlert(
                    name=condition.group(0)[:100],
                    description=condition.group(0) + " " + alert_text
                )
                self.system.alerts.append(alert)

    def _extract_interlocks(self, content: str):
        """Extract interlocks from the document."""
        # Look for interlock mentions
        interlock_patterns = [
            r'interlocked to ([^.]+)',
            r'interlock[^.]*fire[^.]+',
            r'interlock[^.]*smoke[^.]+',
            r'(?:shutdown|shut down) on ([^.]+)',
        ]

        for pattern in interlock_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                interlock = match.strip()
                if interlock and interlock not in self.system.interlocks:
                    self.system.interlocks.append(interlock[:200])

        # Look for hardwired points (these are often interlocks)
        hardwired = re.findall(
            r'(?:DO|DI)\s+([^\n]+)',
            content
        )
        for hw in hardwired:
            if hw.strip() and hw.strip() not in self.system.interlocks:
                self.system.interlocks.append(hw.strip())

    def _extract_failure_states(self, content: str):
        """Extract failure states table."""
        # Look for TABLE 1 – FAILURE STATES
        table_match = re.search(
            r'TABLE\s*\d+\s*[–-]\s*FAILURE STATES\s*(.*?)(?=E\.\s+When|3\.\d|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if table_match:
            table_text = table_match.group(1)

            # Extract rows: Device Name | Off Position | Loss of Signal | Loss of Power
            rows = re.findall(
                r'([A-Z][A-Za-z\s]+(?:Damper|Fan|Array|Coil))\s+'
                r'(Closed|Off|Open|Fail\s*\w+)\s+'
                r'(Fail\s*\w+|Off|Open|Closed)\s+'
                r'(Fail\s*\w+|Off|Open|Closed)',
                table_text
            )

            for row in rows:
                device_name = row[0].strip()
                # Find matching component and update
                for comp in self.system.components:
                    if device_name.lower() in comp.name.lower():
                        comp.failure_state_off = row[1].strip()
                        comp.failure_state_signal_loss = row[2].strip()
                        comp.failure_state_power_loss = row[3].strip()
                        break
                else:
                    # Add as new component if not found
                    comp = MUAComponent(
                        name=device_name,
                        failure_state_off=row[1].strip(),
                        failure_state_signal_loss=row[2].strip(),
                        failure_state_power_loss=row[3].strip()
                    )
                    self.system.components.append(comp)


def parse_mua_soo(content: str) -> MUASystem:
    """Convenience function to parse MUA SOO content."""
    parser = MUASOOParser()
    return parser.parse(content)

