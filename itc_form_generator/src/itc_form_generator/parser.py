"""Enhanced Parser for Sequence of Operation documents.

Multi-pass hybrid parsing: regex structure detection + AI-powered extraction + 
regex validation. Handles markdown, plain text, and OCR'd documents.
"""

import re
import logging
from typing import Optional
from .models import (
    SequenceOfOperation, System, Component, OperatingMode, Setpoint
)

logger = logging.getLogger(__name__)


def detect_document_type(content: str) -> str:
    """Detect the type of SOO document.

    Returns equipment type string: CRAH, IWM, MUA, FCU, AHU, ATS, RSB, or generic.
    """
    content_lower = content.lower()

    # Ordered by specificity (most specific first)
    type_patterns = {
        'CRAH': ['computer room air handler', 'computer room air', 'crah', 
                  'network electrical room.*cooling'],
        'IWM': ['industrial water manager', 'iwm manager', 'facility water.*mcup',
                'iwm.*mcup'],
        'MUA': ['makeup air unit', 'make-up air unit', 'make up air',
                'control sequences for makeup air'],
        'FCU': ['fan coil unit', 'fan coil.*data hall'],
        'AHU': ['air handling unit', 'ahu '],
        'ATS': ['automatic transfer switch', 'ats '],
        'RSB': ['remote switchboard', 'rsb '],
    }

    for doc_type, patterns in type_patterns.items():
        for pattern in patterns:
            if re.search(pattern, content_lower):
                return doc_type

    return 'generic'


# ============================================================================
# Enhanced Regex Patterns
# ============================================================================

class Patterns:
    """Enhanced regex patterns for SOO parsing."""

    # Equipment tags — broader pattern to catch more formats
    # Matches: AHU-01, CRAH-01A, DH-MGR-01, CT-1, P-101, VFD-AHU-01, etc.
    TAG = re.compile(
        r'\b([A-Z]{1,6}(?:[-_][A-Z]{1,6})*[-_]?\d{1,4}[A-Z]?)\b'
    )

    # Setpoint values with units
    SETPOINT_VALUE = re.compile(
        r'(\d+(?:\.\d+)?)\s*'
        r'(°[FCK]|[°]?F|[°]?C|%|psi|kPa|GPM|gpm|CFM|cfm|Hz|'
        r'V|A|kW|kw|seconds?|sec|minutes?|min|hours?|hr|'
        r'in\.?\s*w\.?g\.?|inwg|wg)?'
    )

    # Named setpoint: "Name = Value Units" or "Name: Value Units"
    NAMED_SETPOINT = re.compile(
        r'([\w\s]{3,50?})\s*[=:]\s*'
        r'(\d+(?:\.\d+)?)\s*'
        r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|V|A|kW|'
        r'seconds?|minutes?|hours?|in\.?\s*w\.?g\.?)?',
        re.IGNORECASE
    )

    # Markdown headers
    HEADER = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    # Numbered sections: "1.2.3 Title" or "1.2.3. Title"
    NUMBERED_SECTION = re.compile(
        r'^\s*(\d+(?:\.\d+)*)\s*\.?\s+([A-Z][\w\s,/&-]{3,80})$', 
        re.MULTILINE
    )

    # Bullet points
    BULLET = re.compile(r'^\s*[-*•▪○◦]\s+(.+)$', re.MULTILINE)

    # Numbered list items
    NUMBERED_LIST = re.compile(r'^\s*(?:\d+[.)\s]|[a-z][.)\s])\s*(.+)$', re.MULTILINE)

    # System/equipment keyword patterns (with context)
    SYSTEM_PATTERNS = [
        (r'(?:computer\s+room\s+air\s+handler|CRAH)', 'CRAH'),
        (r'(?:air\s+handling\s+unit|AHU)', 'AHU'),
        (r'(?:makeup\s+air\s+unit|make-up\s+air|MUA|MAU)', 'MUA'),
        (r'(?:fan\s+coil\s+unit|FCU)', 'FCU'),
        (r'(?:variable\s+air\s+volume|VAV)', 'VAV'),
        (r'(?:rooftop\s+unit|RTU)', 'RTU'),
        (r'(?:dedicated\s+outdoor\s+air|DOAS)', 'DOAS'),
        (r'(?:industrial\s+water\s+manager|IWM)', 'IWM'),
        (r'(?:chiller|CH[-_])', 'Chiller'),
        (r'(?:cooling\s+tower|CT[-_])', 'Cooling Tower'),
        (r'(?:heat\s+exchanger|HX[-_])', 'Heat Exchanger'),
        (r'(?:data\s+hall\s+manager|DH[-_]MGR)', 'Data Hall Manager'),
        (r'(?:supply\s+fan|SF[-_])', 'Supply Fan'),
        (r'(?:return\s+fan|RF[-_])', 'Return Fan'),
        (r'(?:exhaust\s+fan|EF[-_])', 'Exhaust Fan'),
        (r'(?:humidifier|HUM[-_])', 'Humidifier'),
        (r'(?:automatic\s+transfer\s+switch|ATS)', 'ATS'),
        (r'(?:remote\s+switchboard|RSB)', 'RSB'),
        (r'(?:uninterruptible\s+power|UPS)', 'UPS'),
        (r'(?:power\s+distribution|PDU)', 'PDU'),
    ]

    # Operating mode keywords (expanded)
    MODE_KEYWORDS = [
        'normal operation', 'normal mode', 'occupied mode', 'unoccupied mode',
        'standby', 'standby mode', 'hot standby', 'cold standby',
        'cooling mode', 'heating mode', 'economizer', 'economizer mode',
        'free cooling', 'mechanical cooling', 'mixed mode',
        'emergency', 'emergency mode', 'emergency shutdown',
        'shutdown', 'startup', 'start-up', 'start up',
        'morning warmup', 'morning warm-up', 'night setback',
        'demand response', 'load shedding', 'peak shaving',
        'failure mode', 'fault mode', 'backup mode', 'redundancy',
        'lead/lag', 'lead-lag', 'staging', 'changeover',
        'commissioning mode', 'test mode', 'manual mode', 'auto mode',
        'occupied', 'unoccupied', 'holiday mode', 'weekend mode',
        'alarm mode', 'smoke mode', 'fire mode',
        'dehumidification', 'humidification',
        'trim and respond', 'pid control',
    ]

    # Section type detection keywords
    SECTION_TYPES = {
        'components': ['component', 'equipment', 'device', 'hardware', 'instrument'],
        'operating_mode': ['mode', 'operating', 'sequence', 'control logic', 'operation'],
        'setpoints': ['setpoint', 'set point', 'parameter', 'threshold', 'limit'],
        'interlocks': ['interlock', 'safety', 'protection', 'lockout'],
        'alarms': ['alarm', 'fault', 'warning', 'notification'],
        'general': ['general', 'requirement', 'overview', 'introduction', 'scope'],
        'network': ['network', 'communication', 'bacnet', 'modbus', 'protocol'],
        'schedule': ['schedule', 'time', 'calendar', 'occupancy'],
    }


# ============================================================================
# Document Structure Analyzer
# ============================================================================

class DocumentStructure:
    """Analyzes and stores document structure."""

    def __init__(self):
        self.title: str = ""
        self.project: str = ""
        self.doc_type: str = "generic"
        self.sections: list[dict] = []  # {heading, level, type, line_start, line_end, content}
        self.format: str = "unknown"  # markdown, plain, numbered

    @classmethod
    def analyze(cls, content: str) -> "DocumentStructure":
        """Analyze document to identify structure."""
        doc = cls()
        lines = content.split('\n')

        # Detect format
        has_markdown = bool(Patterns.HEADER.search(content))
        has_numbered = bool(Patterns.NUMBERED_SECTION.search(content))

        if has_markdown:
            doc.format = "markdown"
            doc._analyze_markdown(lines)
        elif has_numbered:
            doc.format = "numbered"
            doc._analyze_numbered(lines)
        else:
            doc.format = "plain"
            doc._analyze_plain(lines)

        doc.doc_type = detect_document_type(content)
        doc._extract_title(content)

        return doc

    def _analyze_markdown(self, lines: list[str]) -> None:
        """Analyze markdown-formatted document."""
        current_section = None

        for i, line in enumerate(lines):
            match = Patterns.HEADER.match(line)
            if match:
                # Close previous section
                if current_section:
                    current_section["line_end"] = i - 1
                    self.sections.append(current_section)

                level = len(match.group(1))
                heading = match.group(2).strip()
                section_type = self._classify_section(heading)

                current_section = {
                    "heading": heading,
                    "level": level,
                    "type": section_type,
                    "line_start": i,
                    "line_end": len(lines) - 1,
                }

        if current_section:
            current_section["line_end"] = len(lines) - 1
            self.sections.append(current_section)

    def _analyze_numbered(self, lines: list[str]) -> None:
        """Analyze numbered-section document."""
        current_section = None

        for i, line in enumerate(lines):
            match = Patterns.NUMBERED_SECTION.match(line)
            if match:
                if current_section:
                    current_section["line_end"] = i - 1
                    self.sections.append(current_section)

                number = match.group(1)
                heading = match.group(2).strip()
                level = len(number.split('.'))
                section_type = self._classify_section(heading)

                current_section = {
                    "heading": heading,
                    "level": level,
                    "type": section_type,
                    "line_start": i,
                    "line_end": len(lines) - 1,
                }

        if current_section:
            current_section["line_end"] = len(lines) - 1
            self.sections.append(current_section)

    def _analyze_plain(self, lines: list[str]) -> None:
        """Analyze plain text — treat as single section."""
        if lines:
            self.sections.append({
                "heading": "Document Content",
                "level": 1,
                "type": "general",
                "line_start": 0,
                "line_end": len(lines) - 1,
            })

    def _classify_section(self, heading: str) -> str:
        """Classify section type from heading text."""
        heading_lower = heading.lower()
        for section_type, keywords in Patterns.SECTION_TYPES.items():
            if any(kw in heading_lower for kw in keywords):
                return section_type

        # Check if heading contains equipment keywords
        for pattern, _ in Patterns.SYSTEM_PATTERNS:
            if re.search(pattern, heading, re.IGNORECASE):
                return "system"

        return "other"

    def _extract_title(self, content: str) -> None:
        """Extract document title."""
        # From first H1 header
        for sec in self.sections:
            if sec["level"] == 1:
                self.title = sec["heading"]
                return

        # From title patterns
        title_patterns = [
            r'Document\s+Title[:\s]+(.+?)(?:\n|Rev)',
            r'Sequence\s+of\s+Operations?\s*[-–—:]\s*(.+?)(?:\n|$)',
            r'SOO\s*[-–—:]\s*(.+?)(?:\n|$)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                self.title = match.group(1).strip()[:100]
                return

        self.title = "Sequence of Operation"

    def get_section_content(self, lines: list[str], section: dict) -> str:
        """Get content of a section."""
        start = section["line_start"]
        end = min(section["line_end"] + 1, len(lines))
        return '\n'.join(lines[start:end])


# ============================================================================
# Enhanced SOO Parser
# ============================================================================

class SOOParser:
    """Enhanced parser for Sequence of Operation documents.

    Uses multi-pass hybrid parsing:
    1. Regex: Analyze document structure (sections, hierarchy)
    2. AI: Extract systems, components, modes, setpoints per section
    3. Regex: Fill gaps, validate, cross-reference

    Falls back gracefully to regex-only when AI is unavailable.
    """

    def __init__(self, use_ai: bool = False, ai_service=None):
        """Initialize parser with optional AI enhancement."""
        self.use_ai = use_ai
        self._ai_service = ai_service
        self.current_system: Optional[System] = None
        self.current_component: Optional[Component] = None
        self.current_mode: Optional[OperatingMode] = None

    @property
    def ai_service(self):
        """Lazy initialization of AI service."""
        if self._ai_service is None and self.use_ai:
            try:
                from .ai_service import AIService
                self._ai_service = AIService()
                if not self._ai_service.is_available:
                    logger.warning("AI service not available, using regex-only parsing")
                    self.use_ai = False
            except ImportError:
                logger.warning("AI service not importable, using regex-only parsing")
                self.use_ai = False
        return self._ai_service

    def parse(self, content: str) -> SequenceOfOperation:
        """Parse SOO document content with multi-pass hybrid approach."""

        # Pass 1: Document structure analysis (always regex)
        structure = DocumentStructure.analyze(content)
        lines = content.split('\n')

        logger.info(f"Document: format={structure.format}, type={structure.doc_type}, "
                     f"sections={len(structure.sections)}")

        # Pass 2: AI-enhanced extraction (if available)
        if self.use_ai and self.ai_service:
            ai_result = self._parse_with_ai(content, structure)
            if ai_result and ai_result.systems:
                # Pass 3: Regex validation and enrichment
                self._enrich_with_regex(ai_result, content, structure, lines)
                logger.info(f"Hybrid parsing: {len(ai_result.systems)} systems extracted")
                return ai_result
            logger.info("AI parsing returned no results, falling back to regex")

        # Regex-only parsing
        return self._parse_regex_only(content, structure, lines)

    # ========================================================================
    # AI-Enhanced Parsing
    # ========================================================================

    def _parse_with_ai(self, content: str, structure: DocumentStructure) -> Optional[SequenceOfOperation]:
        """Parse using AI service with document structure guidance."""
        try:
            ai_data = self.ai_service.parse_soo_document(content)
            if not ai_data:
                return None
            return self._convert_ai_result(ai_data, structure)
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return None

    def _convert_ai_result(self, ai_data: dict, structure: DocumentStructure) -> SequenceOfOperation:
        """Convert AI parsing result to SequenceOfOperation object.
        
        Handles both nested format (systems contain components/setpoints) 
        and flat format (components/setpoints at top level with parent_system refs).
        """
        soo = SequenceOfOperation(
            title=ai_data.get('title', '') or structure.title,
            project=ai_data.get('project', ''),
        )

        for sys_data in ai_data.get('systems', []):
            system = System(
                name=sys_data.get('name', 'Unknown System'),
                tag=sys_data.get('tag', ''),
                description=sys_data.get('description', '')
            )

            for comp_data in sys_data.get('components', []):
                if isinstance(comp_data, str):
                    component = Component(name=comp_data, parent_system=system.tag)
                else:
                    component = Component(
                        tag=comp_data.get('tag', ''),
                        name=comp_data.get('name', ''),
                        component_type=comp_data.get('type', comp_data.get('component_type', '')),
                        parent_system=comp_data.get('parent_system', system.tag)
                    )
                system.components.append(component)

            for mode_data in sys_data.get('operating_modes', []):
                if isinstance(mode_data, str):
                    mode = OperatingMode(name=mode_data)
                else:
                    conditions = mode_data.get('conditions', [])
                    if isinstance(conditions, str):
                        conditions = [conditions] if conditions else []
                    actions = mode_data.get('actions', [])
                    if isinstance(actions, str):
                        actions = [actions] if actions else []
                    mode = OperatingMode(
                        name=mode_data.get('name', ''),
                        description=mode_data.get('description', ''),
                        conditions=conditions,
                        actions=actions
                    )
                system.operating_modes.append(mode)

            for sp_data in sys_data.get('setpoints', []):
                if isinstance(sp_data, str):
                    setpoint = Setpoint(name=sp_data, description=sp_data)
                else:
                    setpoint = Setpoint(
                        name=sp_data.get('name', ''),
                        value=str(sp_data.get('value', '')),
                        units=sp_data.get('units', ''),
                        description=sp_data.get('description', sp_data.get('context', '')),
                        adjustable=sp_data.get('adjustable', False),
                        min_value=sp_data.get('min_value'),
                        max_value=sp_data.get('max_value')
                    )
                    if sp_data.get('time_delay'):
                        setpoint.description = f"{setpoint.description} (Delay: {sp_data['time_delay']})".strip(' ()')
                system.setpoints.append(setpoint)

            # Handle interlocks - can be list of dicts or list of strings
            interlocks = sys_data.get('interlocks', [])
            if interlocks:
                system.interlocks = []
                for item in interlocks:
                    if isinstance(item, dict):
                        system.interlocks.append(
                            f"{item.get('name', '')}: {item.get('condition', '')} -> {item.get('action', '')}".strip(': ->')
                        )
                    else:
                        system.interlocks.append(str(item))

            # Handle alarms - can be list of dicts or list of strings  
            alarms = sys_data.get('alarms', [])
            if alarms:
                system.alarms = []
                for item in alarms:
                    if isinstance(item, dict):
                        system.alarms.append(
                            f"{item.get('name', '')}: {item.get('condition', '')} [{item.get('threshold', '')}]".strip(': []')
                        )
                    else:
                        system.alarms.append(str(item))

            soo.systems.append(system)

        soo.general_requirements = ai_data.get('general_requirements', [])
        
        logger.info(f"AI conversion: {len(soo.systems)} systems, "
                     f"{sum(len(s.components) for s in soo.systems)} components, "
                     f"{sum(len(s.setpoints) for s in soo.systems)} setpoints, "
                     f"{sum(len(s.operating_modes) for s in soo.systems)} modes")
        return soo

    def _enrich_with_regex(self, soo: SequenceOfOperation, content: str,
                           structure: DocumentStructure, lines: list[str]) -> None:
        """Pass 3: Use regex to fill gaps in AI extraction."""

        # Find tags in content that AI may have missed
        content_tags = set()
        for match in Patterns.TAG.finditer(content):
            content_tags.add(match.group(1))

        # Collect tags already found by AI
        ai_tags = set()
        for system in soo.systems:
            if system.tag:
                ai_tags.add(system.tag)
            for comp in system.components:
                if comp.tag:
                    ai_tags.add(comp.tag)

        # Find modes from content that AI may have missed
        content_lower = content.lower()
        for system in soo.systems:
            existing_modes = {m.name.lower() for m in system.operating_modes}
            for keyword in Patterns.MODE_KEYWORDS:
                if keyword in content_lower and keyword not in existing_modes:
                    # Only add if not similar to existing mode
                    if not any(keyword in em for em in existing_modes):
                        system.operating_modes.append(OperatingMode(name=keyword.title()))

        # Find setpoints that AI may have missed
        for system in soo.systems:
            existing_sp_names = {sp.name.lower() for sp in system.setpoints}
            for match in Patterns.NAMED_SETPOINT.finditer(content):
                name = match.group(1).strip()
                value = match.group(2)
                units = match.group(3) or ""
                if name.lower() not in existing_sp_names and len(name) > 3:
                    system.setpoints.append(Setpoint(
                        name=name, value=value, units=units,
                        description=f"{name} = {value} {units}"
                    ))

    # ========================================================================
    # Regex-Only Parsing
    # ========================================================================

    def _parse_regex_only(self, content: str, structure: DocumentStructure,
                          lines: list[str]) -> SequenceOfOperation:
        """Full regex-based parsing when AI is unavailable."""
        soo = SequenceOfOperation(title=structure.title)

        if structure.format == "markdown":
            self._parse_markdown_sections(soo, structure, lines)
        elif structure.format == "numbered":
            self._parse_numbered_sections(soo, structure, lines)
        else:
            self._parse_plain_text(soo, content)

        # Ensure at least one system
        if not soo.systems:
            default = self._create_default_system(content, structure)
            if default:
                soo.systems.append(default)

        return soo

    def _parse_markdown_sections(self, soo: SequenceOfOperation,
                                  structure: DocumentStructure, lines: list[str]) -> None:
        """Parse document using markdown section structure."""
        for section in structure.sections:
            content = structure.get_section_content(lines, section)
            heading = section["heading"]
            level = section["level"]
            section_type = section["type"]

            if level <= 2 and section_type == "system":
                system = self._parse_system_header(heading)
                if system:
                    soo.systems.append(system)
                    self.current_system = system
                    # Parse subsections for this system
                    self._extract_system_details(system, content)
            elif section_type == "components" and self.current_system:
                self._parse_components_from_text(self.current_system, content)
            elif section_type == "operating_mode" and self.current_system:
                mode = OperatingMode(name=heading)
                self.current_system.operating_modes.append(mode)
                self._parse_mode_content_from_text(mode, content)
            elif section_type == "setpoints" and self.current_system:
                self._parse_setpoints_from_text(self.current_system, content)
            elif section_type == "interlocks" and self.current_system:
                self._parse_interlocks_from_text(self.current_system, content)
            elif section_type == "alarms" and self.current_system:
                self._parse_alarms_from_text(self.current_system, content)
            elif section_type == "general":
                bullets = Patterns.BULLET.findall(content)
                soo.general_requirements.extend(bullets)

    def _parse_numbered_sections(self, soo: SequenceOfOperation,
                                  structure: DocumentStructure, lines: list[str]) -> None:
        """Parse document with numbered sections."""
        # Similar to markdown but uses numbered section structure
        for section in structure.sections:
            content = structure.get_section_content(lines, section)
            heading = section["heading"]
            section_type = section["type"]
            level = section["level"]

            if level <= 2 and section_type in ("system", "other"):
                system = self._parse_system_header(heading)
                if system:
                    soo.systems.append(system)
                    self.current_system = system
                    self._extract_system_details(system, content)
            elif section_type == "operating_mode" and self.current_system:
                mode = OperatingMode(name=heading)
                self.current_system.operating_modes.append(mode)
                self._parse_mode_content_from_text(mode, content)
            elif section_type == "setpoints" and self.current_system:
                self._parse_setpoints_from_text(self.current_system, content)

    def _parse_plain_text(self, soo: SequenceOfOperation, content: str) -> None:
        """Parse unstructured plain text."""
        systems = self._extract_systems_from_text(content)
        soo.systems = systems

    # ========================================================================
    # Extraction Helpers
    # ========================================================================

    def _parse_system_header(self, title: str) -> Optional[System]:
        """Parse a system from header text."""
        tag_match = Patterns.TAG.search(title)
        tag = tag_match.group(1) if tag_match else ""
        name = Patterns.TAG.sub('', title).strip(' -:()')
        name = re.sub(r'\s+', ' ', name).strip()

        if name or tag:
            return System(name=name or tag, tag=tag, description="")
        return None

    def _extract_system_details(self, system: System, content: str) -> None:
        """Extract components, modes, setpoints from system section content."""
        self._parse_components_from_text(system, content)

        # Find modes (deduplicated)
        content_lower = content.lower()
        existing_modes = {m.name.lower() for m in system.operating_modes}
        for keyword in Patterns.MODE_KEYWORDS:
            if keyword in content_lower and keyword not in existing_modes:
                system.operating_modes.append(OperatingMode(name=keyword.title()))
                existing_modes.add(keyword)

        # Find setpoints via named patterns
        self._parse_setpoints_from_text(system, content)
        
        # BUG-5: Parse whitespace-aligned tables
        self._parse_whitespace_tables(system, content)
        
        # BUG-6: Extract inline setpoints from prose
        self._extract_inline_setpoints(system, content)

        # Find interlocks
        self._parse_interlocks_from_text(system, content)

    def _parse_components_from_text(self, system: System, content: str) -> None:
        """Extract components from text content."""
        existing_tags = {c.tag for c in system.components}

        for match in Patterns.TAG.finditer(content):
            tag = match.group(1)
            if tag not in existing_tags and tag != system.tag:
                # Get context around the tag
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]

                # Try to extract name from context
                name = self._extract_component_name(tag, context)

                component = Component(
                    tag=tag, name=name or tag,
                    parent_system=system.tag
                )
                system.components.append(component)
                existing_tags.add(tag)

    def _extract_component_name(self, tag: str, context: str) -> str:
        """Extract component name from surrounding context."""
        # Look for "Tag - Name" or "Tag: Name" or "Name (Tag)"
        patterns = [
            re.compile(rf'{re.escape(tag)}\s*[-–—:]\s*([\w\s]{{3,40}})', re.IGNORECASE),
            re.compile(rf'([\w\s]{{3,40}})\s*\({re.escape(tag)}\)', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(context)
            if m:
                return m.group(1).strip()
        return ""

    def _parse_setpoints_from_text(self, system: System, content: str) -> None:
        """Extract setpoints from text content."""
        existing = {sp.name.lower() for sp in system.setpoints}

        for match in Patterns.NAMED_SETPOINT.finditer(content):
            name = match.group(1).strip()
            value = match.group(2)
            units = match.group(3) or ""

            if len(name) > 2 and len(name) < 50 and name.lower() not in existing:
                system.setpoints.append(Setpoint(
                    name=name, value=value, units=units,
                    description=f"{name} = {value} {units}"
                ))
                existing.add(name.lower())

                if len(system.setpoints) >= 30:
                    break

    def _parse_interlocks_from_text(self, system: System, content: str) -> None:
        """Extract interlocks from text."""
        patterns = [
            r'interlock[:\s]+(.+?)(?:\n|$)',
            r'safety[:\s]+(.+?)(?:\n|$)',
            r'shutdown[:\s]+(.+?)(?:\n|$)',
            r'lockout[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                interlock = match.group(1).strip()
                if 5 < len(interlock) < 200 and interlock not in system.interlocks:
                    system.interlocks.append(interlock)
                    if len(system.interlocks) >= 15:
                        return

    def _parse_alarms_from_text(self, system: System, content: str) -> None:
        """Extract alarms from text."""
        patterns = [
            r'alarm[:\s]+(.+?)(?:\n|$)',
            r'fault[:\s]+(.+?)(?:\n|$)',
            r'warning[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                alarm = match.group(1).strip()
                if 5 < len(alarm) < 200 and alarm not in system.alarms:
                    system.alarms.append(alarm)
                    if len(system.alarms) >= 15:
                        return

    def _parse_mode_content_from_text(self, mode: OperatingMode, content: str) -> None:
        """Parse operating mode actions and conditions from text."""
        bullets = Patterns.BULLET.findall(content)
        numbered = Patterns.NUMBERED_LIST.findall(content)
        items = bullets + numbered

        for item in items:
            item = item.strip()
            if any(kw in item.lower() for kw in ['when', 'if', 'condition', 'upon', 'provided']):
                mode.conditions.append(item)
            else:
                mode.actions.append(item)

    def _extract_systems_from_text(self, content: str) -> list[System]:
        """Extract systems from unstructured plain text."""
        systems = []
        found_tags = set()
        content_lower = content.lower()

        # Strategy 1: Look for known system patterns with context
        for pattern, sys_type in Patterns.SYSTEM_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                for match in matches[:3]:  # Limit per type
                    # Get surrounding context for tag extraction
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    tag_match = Patterns.TAG.search(context)
                    tag = tag_match.group(1) if tag_match else ""

                    if tag and tag in found_tags:
                        continue

                    name = match.group(0).strip()
                    system = System(name=name, tag=tag, description="")
                    self._extract_system_details(system, content)
                    systems.append(system)

                    if tag:
                        found_tags.add(tag)

        # Strategy 2: Group equipment tags by prefix
        if not systems:
            tag_groups = {}
            for match in Patterns.TAG.finditer(content):
                tag = match.group(1)
                prefix = re.match(r'^([A-Z]+)', tag)
                if prefix:
                    key = prefix.group(1)
                    if key not in tag_groups:
                        tag_groups[key] = []
                    tag_groups[key].append(tag)

            for prefix, tags in tag_groups.items():
                if len(tags) >= 1:
                    main_tag = tags[0]
                    name = self._tag_to_name(prefix)
                    system = System(name=name, tag=main_tag)

                    for tag in tags[1:5]:
                        system.components.append(Component(
                            tag=tag, name=tag, parent_system=main_tag
                        ))

                    self._extract_system_details(system, content)
                    systems.append(system)

        return systems[:15]


    def _parse_whitespace_tables(self, system: System, content: str) -> None:
        """BUG-5 fix: Parse whitespace-aligned setpoint/parameter tables.
        
        Handles tables like:
            PARAMETER               SET POINT       TIME DELAY
            Supply Air Temp         72°F            N/A
            High Temp Alarm         85°F            30 sec
        
        Also handles pipe-delimited markdown tables:
            | Parameter | Value | Units |
            |-----------|-------|-------|
            | Supply Temp | 72 | °F |
        """
        lines = content.split('\n')
        existing = {sp.name.lower() for sp in system.setpoints}
        
        # Strategy 1: Detect table headers with PARAMETER/SET POINT/VALUE
        table_header_re = re.compile(
            r'(PARAMETER|SET\s*POINT|SETPOINT|VALUE|TIME\s*DELAY|UNITS|DESCRIPTION)',
            re.IGNORECASE
        )
        
        i = 0
        while i < len(lines):
            line = lines[i]
            headers = list(table_header_re.finditer(line))
            
            if len(headers) >= 2:
                # Found a table header row — extract column positions
                col_positions = [(m.start(), m.end(), m.group(0).strip().lower()) for m in headers]
                
                # Parse subsequent rows
                i += 1
                # Skip separator lines (--- or ===)
                while i < len(lines) and re.match(r'^[\s\-=|]+$', lines[i]):
                    i += 1
                
                while i < len(lines):
                    row = lines[i]
                    # Stop at blank lines or new sections
                    if not row.strip() or row.strip().startswith('#') or row.strip().startswith('##'):
                        break
                    
                    # Skip separator lines
                    if re.match(r'^[\s\-=|]+$', row):
                        i += 1
                        continue
                    
                    # Extract columns by position
                    cols = {}
                    for j, (start, end, col_name) in enumerate(col_positions):
                        # Get text from this column start to next column start
                        if j + 1 < len(col_positions):
                            next_start = col_positions[j + 1][0]
                            cols[col_name] = row[start:next_start].strip()
                        else:
                            cols[col_name] = row[start:].strip()
                    
                    # Extract name and value
                    name = ''
                    value = ''
                    units = ''
                    time_delay = ''
                    
                    for col_name, col_val in cols.items():
                        cn = col_name.lower().replace(' ', '')
                        if cn in ('parameter', 'description', 'name'):
                            name = col_val.strip(' |')
                        elif cn in ('setpoint', 'set point', 'value'):
                            value = col_val.strip(' |')
                        elif cn in ('units', 'unit'):
                            units = col_val.strip(' |')
                        elif cn in ('timedelay', 'time delay', 'delay'):
                            time_delay = col_val.strip(' |')
                    
                    if name and name.lower() not in existing and len(name) > 2:
                        # Extract units from value if not separate
                        if value and not units:
                            val_match = Patterns.SETPOINT_VALUE.match(value)
                            if val_match:
                                value = val_match.group(1)
                                units = val_match.group(2) or ''
                        
                        desc = f"{name} = {value} {units}".strip()
                        if time_delay:
                            desc += f" (Delay: {time_delay})"
                        
                        system.setpoints.append(Setpoint(
                            name=name, value=value, units=units,
                            description=desc
                        ))
                        existing.add(name.lower())
                    
                    i += 1
                continue
            
            # Strategy 2: Detect pipe-delimited markdown tables
            if '|' in line and re.search(r'\|.*\|.*\|', line):
                cells = [c.strip() for c in line.split('|') if c.strip()]
                is_header = any(
                    kw in ' '.join(cells).lower()
                    for kw in ['parameter', 'setpoint', 'set point', 'value', 'description']
                )
                
                if is_header and len(cells) >= 2:
                    header_cells = cells
                    i += 1
                    # Skip separator
                    while i < len(lines) and re.match(r'^[\s|\-:]+$', lines[i]):
                        i += 1
                    
                    while i < len(lines) and '|' in lines[i]:
                        row_cells = [c.strip() for c in lines[i].split('|') if c.strip()]
                        if len(row_cells) >= 2:
                            name = row_cells[0] if len(row_cells) > 0 else ''
                            value = row_cells[1] if len(row_cells) > 1 else ''
                            units = row_cells[2] if len(row_cells) > 2 else ''
                            
                            if name and name.lower() not in existing and len(name) > 2:
                                if not units:
                                    val_match = Patterns.SETPOINT_VALUE.match(value)
                                    if val_match:
                                        value = val_match.group(1)
                                        units = val_match.group(2) or ''
                                
                                system.setpoints.append(Setpoint(
                                    name=name, value=value, units=units,
                                    description=f"{name} = {value} {units}".strip()
                                ))
                                existing.add(name.lower())
                        i += 1
                    continue
            
            i += 1

    def _extract_inline_setpoints(self, system: System, content: str) -> None:
        """BUG-6 fix: Extract setpoints embedded in prose text.
        
        Finds patterns like:
        - "maintain temperature above 72°F"
        - "shall not exceed 85°F"
        - "setpoint of 55°F"
        - "alarm at 95°F"
        - "minimum of 200 CFM"
        - "speed shall be limited to 80%"
        """
        existing = {sp.name.lower() for sp in system.setpoints}
        
        # Patterns for inline setpoints in prose
        inline_patterns = [
            # "maintain X above/below/at Y units"
            (r'maintain\s+(\w[\w\s]{2,30}?)\s+(?:above|below|at|to)\s+(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).strip(), m.group(2), m.group(3))),
            
            # "shall not exceed Y units" (look back for subject)
            (r'(\w[\w\s]{2,30}?)\s+shall\s+not\s+exceed\s+(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).strip() + ' Max', m.group(2), m.group(3))),
            
            # "setpoint of Y units" or "set point of Y units"
            (r'(\w[\w\s]{2,30}?)\s+set\s*point\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).strip(), m.group(2), m.group(3))),
            
            # "alarm at Y units" or "trip at Y units"
            (r'(\w[\w\s]{2,30}?)\s+(?:alarm|trip|fault)\s+(?:at|@)\s+(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).strip() + ' Alarm', m.group(2), m.group(3))),
            
            # "minimum/maximum of Y units"
            (r'(minimum|maximum)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).title(), m.group(2), m.group(3))),
            
            # "limited to Y units" or "Y units limit"  
            (r'(\w[\w\s]{2,30}?)\s+(?:limited\s+to|limit\s+of)\s+(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz|seconds?|minutes?|in\.?\s*w\.?g\.?)',
             lambda m: (m.group(1).strip() + ' Limit', m.group(2), m.group(3))),
            
            # "Y units ± tolerance" 
            (r'(\w[\w\s]{2,30}?)\s*[=:]\s*(\d+(?:\.\d+)?)\s*'
             r'(°[FCK]|%|psi|kPa|GPM|CFM|Hz)\s*±\s*(\d+)',
             lambda m: (m.group(1).strip(), m.group(2), m.group(3))),
        ]
        
        for pattern, extractor in inline_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                try:
                    name, value, units = extractor(match)
                    name = re.sub(r'\s+', ' ', name).strip()
                    
                    # Skip generic/short names
                    if len(name) < 3 or name.lower() in existing:
                        continue
                    if name.lower() in ('the', 'this', 'that', 'when', 'shall', 'will', 'must'):
                        continue
                    
                    system.setpoints.append(Setpoint(
                        name=name, value=value, units=units or '',
                        description=f"{name} = {value} {units or ''} (from text)"
                    ))
                    existing.add(name.lower())
                except Exception:
                    continue

    def _create_default_system(self, content: str, structure: DocumentStructure) -> Optional[System]:
        """Create a default system when no specific systems found."""
        tag_match = Patterns.TAG.search(content)
        tag = tag_match.group(1) if tag_match else "SYS-01"

        system = System(
            name=structure.title or "System",
            tag=tag,
            description="Auto-generated from document content"
        )
        self._extract_system_details(system, content)

        if not system.operating_modes:
            system.operating_modes.append(OperatingMode(name="Normal Operation"))

        return system

    @staticmethod
    def _tag_to_name(tag_prefix: str) -> str:
        """Convert tag prefix to readable name."""
        names = {
            'AHU': 'Air Handling Unit', 'FCU': 'Fan Coil Unit',
            'VAV': 'Variable Air Volume', 'RTU': 'Rooftop Unit',
            'MAU': 'Makeup Air Unit', 'MUA': 'Makeup Air Unit',
            'DOAS': 'Dedicated Outdoor Air System',
            'CRAH': 'Computer Room Air Handler',
            'CH': 'Chiller', 'CT': 'Cooling Tower',
            'HX': 'Heat Exchanger', 'P': 'Pump',
            'SF': 'Supply Fan', 'RF': 'Return Fan', 'EF': 'Exhaust Fan',
            'DH': 'Data Hall', 'FC': 'Fan Coil',
            'VFD': 'Variable Frequency Drive',
            'ATS': 'Automatic Transfer Switch',
            'RSB': 'Remote Switchboard',
            'UPS': 'Uninterruptible Power Supply',
            'PDU': 'Power Distribution Unit',
            'HUM': 'Humidifier', 'IWM': 'Industrial Water Manager',
        }
        return names.get(tag_prefix, tag_prefix)

