"""Parser for Sequence of Operation documents."""

import re
import logging
from typing import Optional
from .models import (
    SequenceOfOperation, System, Component, OperatingMode, Setpoint
)

logger = logging.getLogger(__name__)


def detect_document_type(content: str) -> str:
    """Detect the type of SOO document.

    Returns:
        'CRAH' for Computer Room Air Handler documents
        'IWM' for Industrial Water Manager documents
        'MUA' for Makeup Air Unit documents
        'FCU' for Fan Coil Unit documents
        'AHU' for Air Handling Unit documents
        'generic' for unrecognized formats
    """
    content_lower = content.lower()

    # Check for CRAH (Computer Room Air Handler) documents
    if ('computer room air' in content_lower or
        'crah' in content_lower or
        ('network electrical room' in content_lower and 'cooling' in content_lower)):
        return 'CRAH'

    # Check for IWM (Industrial Water Manager) documents
    if ('industrial water manager' in content_lower or
        'iwm manager' in content_lower or
        ('iwm' in content_lower and 'mcup' in content_lower) or
        ('facility water' in content_lower and 'mcup' in content_lower)):
        return 'IWM'

    # Check for MUA (Makeup Air Unit) documents
    if 'makeup air unit' in content_lower or 'control sequences for makeup air' in content_lower:
        return 'MUA'

    # Check for FCU documents
    if 'fan coil' in content_lower and 'data hall' in content_lower:
        return 'FCU'

    # Check for AHU documents
    if 'air handling unit' in content_lower:
        return 'AHU'

    return 'generic'


class SOOParser:
    """Parser for Sequence of Operation documents.

    Supports both markdown-formatted and plain text (OCR'd) documents.
    Can optionally use AI for enhanced parsing accuracy.
    """

    TAG_PATTERN = re.compile(r'\b([A-Z]{2,4}[-_]?\d{1,3}[A-Z]?)\b')
    SETPOINT_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*([°]?[FCKfck]|%|psi|kPa|GPM|CFM|Hz|V|A|kW)?'
    )
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    BULLET_PATTERN = re.compile(r'^\s*[-*•]\s+(.+)$', re.MULTILINE)

    # Patterns for detecting systems/equipment in plain text
    SYSTEM_KEYWORDS = [
        'air handling unit', 'ahu', 'chiller', 'boiler', 'pump', 'fan',
        'cooling tower', 'vav', 'fcu', 'fan coil', 'rtu', 'mau', 'doas',
        'heat exchanger', 'humidifier', 'dehumidifier', 'exhaust',
        'supply fan', 'return fan', 'condenser', 'evaporator',
        'data hall', 'manager', 'controller', 'plc', 'bms'
    ]

    MODE_KEYWORDS = [
        'normal operation', 'occupied mode', 'unoccupied mode', 'standby',
        'cooling mode', 'heating mode', 'economizer', 'free cooling',
        'emergency', 'shutdown', 'startup', 'morning warmup', 'night setback',
        'demand response', 'load shedding', 'failure mode', 'backup mode'
    ]

    def __init__(self, use_ai: bool = False, ai_service=None):
        """Initialize parser with optional AI enhancement.

        Args:
            use_ai: Whether to use AI for enhanced parsing
            ai_service: AIService instance (created if None and use_ai=True)
        """
        self.current_system: Optional[System] = None
        self.current_component: Optional[Component] = None
        self.current_mode: Optional[OperatingMode] = None
        self.use_ai = use_ai
        self._ai_service = ai_service

    @property
    def ai_service(self):
        """Lazy initialization of AI service."""
        if self._ai_service is None and self.use_ai:
            try:
                from .ai_service import AIService
                self._ai_service = AIService()
            except ImportError:
                logger.warning("AI service not available, falling back to regex parsing")
                self.use_ai = False
        return self._ai_service

    def parse(self, content: str) -> SequenceOfOperation:
        """Parse SOO document content.

        Automatically detects format (markdown or plain text) and parses accordingly.
        If AI is enabled, uses AI for enhanced extraction.
        """
        # Try AI-enhanced parsing first if enabled
        if self.use_ai and self.ai_service:
            ai_result = self._parse_with_ai(content)
            if ai_result and ai_result.systems:
                logger.info(f"AI parsing extracted {len(ai_result.systems)} systems")
                return ai_result
            logger.info("AI parsing returned no results, falling back to regex")

        # Fall back to regex-based parsing
        has_markdown_headers = bool(self.HEADER_PATTERN.search(content))

        if has_markdown_headers:
            return self._parse_markdown(content)
        else:
            return self._parse_plain_text(content)

    def _parse_with_ai(self, content: str) -> Optional[SequenceOfOperation]:
        """Parse SOO document using AI for better extraction.

        Args:
            content: Raw document content

        Returns:
            SequenceOfOperation object, or None if AI parsing fails
        """
        try:
            ai_data = self.ai_service.parse_soo_document(content)
            if not ai_data:
                return None

            return self._convert_ai_result(ai_data)
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return None

    def _convert_ai_result(self, ai_data: dict) -> SequenceOfOperation:
        """Convert AI parsing result to SequenceOfOperation object.

        Args:
            ai_data: Dict from AI service

        Returns:
            SequenceOfOperation object
        """
        soo = SequenceOfOperation(
            title=ai_data.get('title', 'Sequence of Operation'),
            project=ai_data.get('project', ''),
        )

        # Convert systems
        for sys_data in ai_data.get('systems', []):
            system = System(
                name=sys_data.get('name', 'Unknown System'),
                tag=sys_data.get('tag', ''),
                description=sys_data.get('description', '')
            )

            # Convert components
            for comp_data in sys_data.get('components', []):
                component = Component(
                    tag=comp_data.get('tag', ''),
                    name=comp_data.get('name', ''),
                    component_type=comp_data.get('type', ''),
                    parent_system=system.tag
                )
                system.components.append(component)

            # Convert operating modes
            for mode_data in sys_data.get('operating_modes', []):
                mode = OperatingMode(
                    name=mode_data.get('name', ''),
                    description=mode_data.get('description', ''),
                    conditions=mode_data.get('conditions', []),
                    actions=mode_data.get('actions', [])
                )
                system.operating_modes.append(mode)

            # Convert setpoints
            for sp_data in sys_data.get('setpoints', []):
                setpoint = Setpoint(
                    name=sp_data.get('name', ''),
                    value=str(sp_data.get('value', '')),
                    units=sp_data.get('units', ''),
                    description=sp_data.get('description', ''),
                    adjustable=sp_data.get('adjustable', False),
                    min_value=sp_data.get('min_value'),
                    max_value=sp_data.get('max_value')
                )
                system.setpoints.append(setpoint)

            # Convert interlocks and alarms
            system.interlocks = sys_data.get('interlocks', [])
            system.alarms = sys_data.get('alarms', [])

            soo.systems.append(system)

        # Add general requirements
        soo.general_requirements = ai_data.get('general_requirements', [])

        return soo

    def _parse_markdown(self, content: str) -> SequenceOfOperation:
        """Parse markdown-formatted SOO document."""
        lines = content.split('\n')
        soo = SequenceOfOperation(title="Sequence of Operation")

        current_section = ""
        section_content: list[str] = []

        for line in lines:
            header_match = self.HEADER_PATTERN.match(line)
            if header_match:
                if section_content:
                    self._process_section(
                        soo, current_section, section_content
                    )
                    section_content = []

                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                if level == 1:
                    soo.title = title
                elif level == 2:
                    system = self._parse_system_header(title)
                    if system:
                        soo.systems.append(system)
                        self.current_system = system
                    current_section = title.lower()
                elif level == 3:
                    current_section = title.lower()
                    if self.current_system:
                        self._handle_subsection(title)
            else:
                section_content.append(line)

        if section_content:
            self._process_section(soo, current_section, section_content)

        # If no systems found after markdown parsing, create a default system
        if not soo.systems:
            default_system = self._create_default_system(content)
            if default_system:
                soo.systems.append(default_system)

        return soo

    def _parse_plain_text(self, content: str) -> SequenceOfOperation:
        """Parse plain text (OCR'd) SOO document."""
        soo = SequenceOfOperation(title="Sequence of Operation")

        # Extract title from content
        title = self._extract_title(content)
        if title:
            soo.title = title

        # Find systems from content
        systems = self._extract_systems_from_text(content)
        soo.systems = systems

        # If no systems found, create a default system with the document content
        if not systems:
            default_system = self._create_default_system(content)
            if default_system:
                soo.systems.append(default_system)

        return soo

    def _extract_title(self, content: str) -> str:
        """Extract document title from plain text."""
        # Look for common title patterns
        title_patterns = [
            r'Document Title[:\s]+(.+?)(?:\n|Rev)',
            r'Sequence of Operation[s]?\s*[-–—:]\s*(.+?)(?:\n|$)',
            r'SOO\s*[-–—:]\s*(.+?)(?:\n|$)',
            r'(?:Project|System)[:\s]+(.+?)(?:\n|$)',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 200:
                    return title

        # Fallback: look for a line with "SOO" or "Sequence"
        lines = content.split('\n')
        for line in lines[:50]:  # Check first 50 lines
            if 'sequence of operation' in line.lower() or 'soo' in line.lower():
                clean = re.sub(r'[#*_]', '', line).strip()
                if len(clean) > 5:
                    return clean[:100]

        return "Sequence of Operation"

    def _extract_systems_from_text(self, content: str) -> list[System]:
        """Extract systems from plain text content."""
        systems = []
        content_lower = content.lower()

        # Strategy 1: Look for equipment tags with context
        # Find all equipment tags and their surrounding context
        tag_contexts = []
        for match in self.TAG_PATTERN.finditer(content):
            tag = match.group(1)
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            tag_contexts.append((tag, context))

        # Group tags by prefix (e.g., AHU-01, AHU-02 -> AHU group)
        tag_prefixes = {}
        for tag, context in tag_contexts:
            # Extract prefix (letters before numbers)
            prefix_match = re.match(r'^([A-Z]+)', tag)
            if prefix_match:
                prefix = prefix_match.group(1)
                if prefix not in tag_prefixes:
                    tag_prefixes[prefix] = []
                tag_prefixes[prefix].append((tag, context))

        # Strategy 2: Look for system keywords
        system_names_found = set()

        for keyword in self.SYSTEM_KEYWORDS:
            if keyword in content_lower:
                # Find the line containing this keyword
                for line in content.split('\n'):
                    if keyword in line.lower():
                        # Extract potential system name
                        name = self._clean_system_name(line)
                        if name and len(name) > 3:
                            # Look for an associated tag
                            tag_match = self.TAG_PATTERN.search(line)
                            tag = tag_match.group(1) if tag_match else ""

                            # Avoid duplicates
                            key = (name.lower(), tag)
                            if key not in system_names_found:
                                system_names_found.add(key)
                                system = System(
                                    name=name,
                                    tag=tag,
                                    description=""
                                )
                                # Add components and modes from surrounding content
                                self._enrich_system_from_content(system, content)
                                systems.append(system)
                        break  # Only use first occurrence

        # If we found tag prefixes but no named systems, create systems from tags
        if not systems and tag_prefixes:
            for prefix, tags_list in tag_prefixes.items():
                if len(tags_list) >= 1:
                    # Use the most common tag as the system
                    main_tag = tags_list[0][0]
                    name = self._tag_to_name(prefix)
                    system = System(
                        name=name,
                        tag=main_tag,
                        description=""
                    )

                    # Add other tags as components
                    for tag, context in tags_list[1:5]:  # Limit to 5 components
                        component = Component(
                            tag=tag,
                            name=tag,
                            parent_system=main_tag
                        )
                        system.components.append(component)

                    self._enrich_system_from_content(system, content)
                    systems.append(system)

        return systems[:10]  # Limit to 10 systems

    def _clean_system_name(self, line: str) -> str:
        """Clean up a system name from a line of text."""
        # Remove common prefixes/suffixes
        line = re.sub(r'^[#*\-•\d.)\s]+', '', line)
        line = re.sub(r'\s*[-–—:]\s*$', '', line)
        line = line.strip()

        # Remove page numbers and other artifacts
        line = re.sub(r'Page\s+\d+', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\d+\s*of\s*\d+', '', line, flags=re.IGNORECASE)

        # Truncate if too long
        if len(line) > 80:
            line = line[:80]

        return line.strip()

    def _tag_to_name(self, tag_prefix: str) -> str:
        """Convert a tag prefix to a readable name."""
        tag_names = {
            'AHU': 'Air Handling Unit',
            'FCU': 'Fan Coil Unit',
            'VAV': 'Variable Air Volume',
            'RTU': 'Rooftop Unit',
            'MAU': 'Makeup Air Unit',
            'DOAS': 'Dedicated Outdoor Air System',
            'CH': 'Chiller',
            'CT': 'Cooling Tower',
            'HX': 'Heat Exchanger',
            'P': 'Pump',
            'SF': 'Supply Fan',
            'RF': 'Return Fan',
            'EF': 'Exhaust Fan',
            'DH': 'Data Hall',
            'FC': 'Fan Coil',
            'MNGR': 'Manager',
            'PLC': 'PLC Controller',
        }
        return tag_names.get(tag_prefix, tag_prefix)

    def _enrich_system_from_content(self, system: System, content: str) -> None:
        """Add modes, setpoints, and interlocks from content."""
        content_lower = content.lower()

        # Find operating modes
        for keyword in self.MODE_KEYWORDS:
            if keyword in content_lower:
                mode = OperatingMode(name=keyword.title())
                system.operating_modes.append(mode)

        # Find setpoints (numbers with units)
        setpoint_pattern = r'(\w+(?:\s+\w+)?)\s*[=:]\s*(\d+(?:\.\d+)?)\s*(°?[FCfcKk]|%|psi|kPa|GPM|CFM|Hz|V|A|kW|seconds?|minutes?|hours?)?'
        for match in re.finditer(setpoint_pattern, content, re.IGNORECASE):
            name = match.group(1).strip()
            value = match.group(2)
            units = match.group(3) or ""

            if len(name) > 2 and len(name) < 50:
                setpoint = Setpoint(
                    name=name,
                    value=value,
                    units=units,
                    description=f"{name} = {value} {units}"
                )
                system.setpoints.append(setpoint)

                if len(system.setpoints) >= 20:  # Limit setpoints
                    break

        # Find interlocks
        interlock_patterns = [
            r'interlock[:\s]+(.+?)(?:\n|$)',
            r'safety[:\s]+(.+?)(?:\n|$)',
            r'shutdown[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in interlock_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                interlock = match.group(1).strip()
                if len(interlock) > 5 and len(interlock) < 200:
                    system.interlocks.append(interlock)
                    if len(system.interlocks) >= 10:
                        break

    def _create_default_system(self, content: str) -> Optional[System]:
        """Create a default system when no specific systems are found."""
        title = self._extract_title(content)

        # Try to find any equipment tag in the content
        tag_match = self.TAG_PATTERN.search(content)
        tag = tag_match.group(1) if tag_match else "SYS-01"

        system = System(
            name=title or "System",
            tag=tag,
            description="Auto-generated from document content"
        )

        # Add content as operating modes and setpoints
        self._enrich_system_from_content(system, content)

        # Ensure at least one mode exists
        if not system.operating_modes:
            system.operating_modes.append(OperatingMode(name="Normal Operation"))

        return system

    def _parse_system_header(self, title: str) -> Optional[System]:
        """Parse a system from header text."""
        tag_match = self.TAG_PATTERN.search(title)
        tag = tag_match.group(1) if tag_match else ""
        name = self.TAG_PATTERN.sub('', title).strip(' -:()')

        if name or tag:
            return System(name=name or tag, tag=tag, description="")
        return None

    def _handle_subsection(self, title: str) -> None:
        """Handle a level-3 subsection header."""
        title_lower = title.lower()

        if any(kw in title_lower for kw in ['component', 'equipment']):
            pass
        elif any(kw in title_lower for kw in ['mode', 'operating', 'sequence']):
            mode = OperatingMode(name=title)
            if self.current_system:
                self.current_system.operating_modes.append(mode)
            self.current_mode = mode
        elif 'setpoint' in title_lower:
            pass
        elif any(kw in title_lower for kw in ['interlock', 'safety']):
            pass
        elif 'alarm' in title_lower:
            pass

    def _process_section(
        self,
        soo: SequenceOfOperation,
        section: str,
        content: list[str]
    ) -> None:
        """Process a section's content."""
        text = '\n'.join(content)
        bullets = self.BULLET_PATTERN.findall(text)

        section_lower = section.lower()

        if 'component' in section_lower or 'equipment' in section_lower:
            self._parse_components(bullets)
        elif 'setpoint' in section_lower:
            self._parse_setpoints(bullets)
        elif 'interlock' in section_lower or 'safety' in section_lower:
            self._parse_interlocks(bullets)
        elif 'alarm' in section_lower:
            self._parse_alarms(bullets)
        elif any(kw in section_lower for kw in ['mode', 'sequence', 'operation']):
            self._parse_mode_content(bullets)
        elif 'general' in section_lower or 'requirement' in section_lower:
            soo.general_requirements.extend(bullets)

    def _parse_components(self, bullets: list[str]) -> None:
        """Parse component list."""
        if not self.current_system:
            return

        for bullet in bullets:
            tag_match = self.TAG_PATTERN.search(bullet)
            if tag_match:
                tag = tag_match.group(1)
                name = self.TAG_PATTERN.sub('', bullet).strip(' -:')
                name = re.sub(r'\s+', ' ', name).strip()

                component = Component(
                    tag=tag,
                    name=name or tag,
                    parent_system=self.current_system.tag
                )
                self.current_system.components.append(component)
            else:
                name = bullet.strip(' -:')
                if name:
                    component = Component(
                        tag="",
                        name=name,
                        parent_system=self.current_system.tag if self.current_system else ""
                    )
                    self.current_system.components.append(component)

    def _parse_setpoints(self, bullets: list[str]) -> None:
        """Parse setpoints list."""
        for bullet in bullets:
            setpoint = self._extract_setpoint(bullet)
            if setpoint:
                if self.current_component:
                    self.current_component.setpoints.append(setpoint)
                elif self.current_system:
                    self.current_system.setpoints.append(setpoint)

    def _extract_setpoint(self, text: str) -> Optional[Setpoint]:
        """Extract setpoint from text."""
        value_match = self.SETPOINT_PATTERN.search(text)
        if value_match:
            value = value_match.group(1)
            units = value_match.group(2) or ""
            name = text[:value_match.start()].strip(' -:')

            return Setpoint(
                name=name or "Setpoint",
                value=value,
                units=units,
                description=text
            )
        return None

    def _parse_interlocks(self, bullets: list[str]) -> None:
        """Parse interlocks list."""
        if self.current_system:
            self.current_system.interlocks.extend(bullets)

    def _parse_alarms(self, bullets: list[str]) -> None:
        """Parse alarms list."""
        if self.current_system:
            self.current_system.alarms.extend(bullets)

    def _parse_mode_content(self, bullets: list[str]) -> None:
        """Parse operating mode content."""
        if self.current_mode:
            for bullet in bullets:
                if any(kw in bullet.lower() for kw in ['when', 'if', 'condition']):
                    self.current_mode.conditions.append(bullet)
                else:
                    self.current_mode.actions.append(bullet)
