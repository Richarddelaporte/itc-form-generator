"""Example Form Parser - Learn from existing ITC forms.

Parses Excel/CSV forms from other companies to extract:
- Form structure and sections
- Check item patterns
- Acceptance criteria examples
- Testing methodologies

This learned knowledge is used to improve AI-generated forms.

Enhanced with electrical equipment detection (RSB, ATS, Generator, etc.)
and production template pattern matching.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict, field
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Storage location for learned examples
DEFAULT_EXAMPLES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'learned_examples.json'
)


@dataclass
class LearnedCheckItem:
    """A check item learned from an example form."""
    description: str
    section: str
    check_type: str = ""
    acceptance_criteria: str = ""
    method: str = ""
    priority: str = ""
    system_type: str = ""
    response_type: str = ""  # toggle, text, number, choice
    presets: str = ""  # e.g., "Pass/Fail/NA", "Yes/No/NA"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'LearnedCheckItem':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LearnedSection:
    """A form section learned from an example."""
    name: str
    description: str = ""
    typical_items: list[str] = field(default_factory=list)
    item_count: int = 0
    equipment_type: str = ""  # RSB, ATS, Generator, etc.

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'LearnedSection':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LearnedFormExample:
    """A complete form example that has been learned."""
    id: str
    filename: str
    timestamp: float
    system_type: str
    form_type: str
    source: str  # Company or source name
    total_items: int
    equipment_type: str = ""  # RSB, ATS, Generator, UPS, etc.
    level: str = ""  # L2, L3, L4, etc.
    variant: str = ""  # KND1, TTX1, etc.
    sections: list[LearnedSection] = field(default_factory=list)
    check_items: list[LearnedCheckItem] = field(default_factory=list)
    key_patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = asdict(self)
        result['sections'] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.sections]
        result['check_items'] = [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.check_items]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'LearnedFormExample':
        sections = [LearnedSection.from_dict(s) if isinstance(s, dict) else s
                   for s in data.get('sections', [])]
        check_items = [LearnedCheckItem.from_dict(c) if isinstance(c, dict) else c
                      for c in data.get('check_items', [])]
        return cls(
            id=data['id'],
            filename=data['filename'],
            timestamp=data['timestamp'],
            system_type=data['system_type'],
            form_type=data['form_type'],
            source=data['source'],
            total_items=data['total_items'],
            equipment_type=data.get('equipment_type', ''),
            level=data.get('level', ''),
            variant=data.get('variant', ''),
            sections=sections,
            check_items=check_items,
            key_patterns=data.get('key_patterns', [])
        )


class ExampleFormParser:
    """Parser for learning from example ITC forms (Excel/CSV)."""

    # Electrical equipment patterns for auto-detection
    EQUIPMENT_PATTERNS = {
        'RSB': [r'rsb', r'row.?switch.?board', r'switchboard', r'260000', r'260401'],
        'ATS': [r'ats', r'transfer.?switch', r'automatic.?transfer', r'260627'],
        'Generator': [r'generator', r'genset', r'diesel.?gen', r'standby.?gen', r'260620'],
        'UPS': [r'ups', r'uninterrupt', r'battery.?backup', r'262000'],
        'RDB': [r'rdb', r'row.?distribution', r'distribution.?board'],
        'MVS': [r'mvs', r'medium.?voltage', r'switchgear', r'261000'],
        'PDU': [r'pdu', r'power.?distribution.?unit'],
        'Transformer': [r'transformer', r'xfmr', r'xformer'],
    }

    # Production-validated section patterns (from BIM360/ACC data)
    SECTION_PATTERNS = [
        # Electrical equipment sections (high frequency in production)
        (r'document.*verif|verif.*document', 'Documentation Verification'),
        (r'damage.*protect|protect.*damage|equipment.*protection', 'Damage and Equipment Protection'),
        (r'control.*install|install.*control', 'Controls Installation'),
        (r'alert|alarm.*verif', 'Alert Verification'),
        (r'end.?of.?test', 'End of Test'),
        (r'pre.?energiz', 'Pre-Energization'),
        (r'bms.*verif|epms.*verif|point.*verif', 'BMS/EPMS Point Verification'),
        (r'submittal', 'Submittal Documentation'),
        (r'device.*network|network.*info', 'Device & Network Information'),
        (r'functional.*test|fpt', 'Functional Tests'),
        (r'site.*arrival|arrival.*inspect', 'Site Arrival Inspection'),
        (r'equipment.*id|equipment.*ident', 'Equipment Identification'),
        # Standard commissioning sections
        (r'safety|loto|lockout', 'Safety'),
        (r'pre.?func|pfi|installation', 'Pre-Functional'),
        (r'electric|power|voltage', 'Electrical'),
        (r'control|bms|ddc|plc', 'Controls'),
        (r'sensor|instrument|calibr', 'Sensors'),
        (r'setpoint|parameter|config', 'Setpoints'),
        (r'sequence|mode|operat', 'Operating Modes'),
        (r'alarm|fault|trip', 'Alarms'),
        (r'interlock|safety.?shut', 'Interlocks'),
        (r'document|submit|review', 'Documentation'),
        (r'function|perform|test', 'Functional Tests'),
        (r'commission|handover|accept', 'Commissioning'),
    ]

    # Response type patterns
    RESPONSE_TYPE_PATTERNS = {
        'toggle': [r'yes.*no', r'pass.*fail', r'no.*yes', r'fail.*pass', r'true.*false'],
        'number': [r'enter.*value', r'numeric', r'\d+\.\d+', r'measurement'],
        'text': [r'enter.*text', r'describe', r'comments?', r'notes?', r'explain'],
        'date': [r'date', r'when', r'\d{1,2}/\d{1,2}/\d{2,4}'],
        'choice': [r'select', r'choose', r'option'],
    }

    # Preset patterns
    PRESET_PATTERNS = [
        (r'pass.*fail.*n/?a', 'Pass/Fail/NA'),
        (r'fail.*pass.*n/?a', 'Fail/Pass/NA'),
        (r'yes.*no.*n/?a', 'Yes/No/NA'),
        (r'no.*yes.*n/?a', 'No/Yes/NA'),
        (r'pass.*fail', 'Pass/Fail'),
        (r'yes.*no', 'Yes/No'),
        (r'complete.*incomplete', 'Complete/Incomplete'),
        (r'accept.*reject', 'Accept/Reject'),
    ]

    # Priority indicators
    PRIORITY_PATTERNS = {
        'CRITICAL': [r'critical', r'safety', r'emergency', r'life.?safety'],
        'HIGH': [r'high', r'important', r'required', r'mandatory'],
        'MEDIUM': [r'medium', r'standard', r'normal'],
        'LOW': [r'low', r'optional', r'recommended'],
    }

    # Check type indicators
    CHECK_TYPE_PATTERNS = {
        'VISUAL': [r'visual', r'inspect', r'verify.*install', r'check.*label'],
        'MEASUREMENT': [r'measure', r'record', r'reading', r'value', r'\d+.*[°%]'],
        'FUNCTIONAL': [r'test', r'operate', r'function', r'sequence', r'mode'],
        'DOCUMENTATION': [r'document', r'submit', r'review', r'approve', r'sign'],
        'VERIFICATION': [r'verify', r'confirm', r'ensure', r'validate'],
    }

    def __init__(self):
        self._openpyxl_available = None

    @property
    def is_available(self) -> bool:
        """Check if Excel parsing is available."""
        if self._openpyxl_available is None:
            try:
                import openpyxl
                self._openpyxl_available = True
            except ImportError:
                self._openpyxl_available = False
        return self._openpyxl_available

    def parse_excel(self, file_data: bytes, filename: str, source: str,
                    system_type: str = "General") -> Optional[LearnedFormExample]:
        """Parse an Excel file to extract form patterns.

        Args:
            file_data: Raw Excel file bytes
            filename: Original filename
            source: Source company/origin name
            system_type: Type of system this form is for

        Returns:
            LearnedFormExample with extracted patterns
        """
        if not self.is_available:
            logger.error("openpyxl not available for Excel parsing")
            return None

        try:
            import openpyxl
            from io import BytesIO

            wb = openpyxl.load_workbook(BytesIO(file_data), data_only=True)

            all_check_items = []
            all_sections = []
            current_section = None
            section_items = []
            all_text = []  # Collect all text for equipment detection

            # Process all sheets
            for sheet in wb.worksheets:
                logger.info(f"Processing sheet: {sheet.title}")

                for row in sheet.iter_rows(values_only=True):
                    if not row or all(cell is None for cell in row):
                        continue

                    # Convert row to strings
                    row_text = [str(cell) if cell else "" for cell in row]
                    row_combined = " ".join(row_text).strip()

                    if not row_combined or row_combined == "None":
                        continue

                    all_text.append(row_combined)

                    # Check if this is a section header
                    detected_section = self._detect_section(row_combined)
                    if detected_section and len(row_combined) < 100:
                        # Save previous section
                        if current_section and section_items:
                            all_sections.append(LearnedSection(
                                name=current_section,
                                typical_items=section_items[:10],
                                item_count=len(section_items),
                                equipment_type=self._detect_equipment_type("\n".join(all_text[:50]))
                            ))
                        current_section = detected_section
                        section_items = []
                        continue

                    # Try to parse as a check item
                    check_item = self._parse_check_item(row_text, row_combined,
                                                        current_section or "General",
                                                        system_type)
                    if check_item:
                        all_check_items.append(check_item)
                        section_items.append(check_item.description[:80])

            # Save last section
            if current_section and section_items:
                all_sections.append(LearnedSection(
                    name=current_section,
                    typical_items=section_items[:10],
                    item_count=len(section_items),
                    equipment_type=self._detect_equipment_type("\n".join(all_text[:50]))
                ))

            # Detect equipment type from all text
            full_text = "\n".join(all_text)
            equipment_type = self._detect_equipment_type(full_text)
            level = self._detect_level(full_text)
            variant = self._detect_variant(full_text)

            # Extract key patterns
            key_patterns = self._extract_key_patterns(all_check_items)

            # Create learned example
            import uuid
            example = LearnedFormExample(
                id=str(uuid.uuid4())[:8],
                filename=filename,
                timestamp=time.time(),
                system_type=system_type if system_type != "General" else equipment_type or "General",
                form_type=self._detect_form_type(filename, all_sections),
                source=source,
                total_items=len(all_check_items),
                equipment_type=equipment_type,
                level=level,
                variant=variant,
                sections=all_sections,
                check_items=all_check_items[:200],  # Increased limit
                key_patterns=key_patterns
            )

            logger.info(f"Parsed {len(all_check_items)} check items, {len(all_sections)} sections, equipment: {equipment_type}")
            return example

        except Exception as e:
            logger.error(f"Failed to parse Excel: {e}")
            import traceback
            traceback.print_exc()
            return None

    def parse_csv(self, content: str, filename: str, source: str,
                  system_type: str = "General") -> Optional[LearnedFormExample]:
        """Parse a CSV file to extract form patterns.

        Args:
            content: CSV content as string
            filename: Original filename
            source: Source company/origin name
            system_type: Type of system this form is for

        Returns:
            LearnedFormExample with extracted patterns
        """
        try:
            import csv
            from io import StringIO

            reader = csv.reader(StringIO(content))

            all_check_items = []
            all_sections = []
            current_section = None
            section_items = []
            all_text = []

            for row in reader:
                if not row or all(not cell.strip() for cell in row):
                    continue

                row_text = [str(cell).strip() for cell in row]
                row_combined = " ".join(row_text).strip()
                all_text.append(row_combined)

                # Check if this is a section header
                detected_section = self._detect_section(row_combined)
                if detected_section and len(row_combined) < 100:
                    if current_section and section_items:
                        all_sections.append(LearnedSection(
                            name=current_section,
                            typical_items=section_items[:10],
                            item_count=len(section_items),
                            equipment_type=self._detect_equipment_type("\n".join(all_text[:50]))
                        ))
                    current_section = detected_section
                    section_items = []
                    continue

                # Try to parse as a check item
                check_item = self._parse_check_item(row_text, row_combined,
                                                    current_section or "General",
                                                    system_type)
                if check_item:
                    all_check_items.append(check_item)
                    section_items.append(check_item.description[:80])

            # Save last section
            if current_section and section_items:
                all_sections.append(LearnedSection(
                    name=current_section,
                    typical_items=section_items[:10],
                    item_count=len(section_items),
                    equipment_type=self._detect_equipment_type("\n".join(all_text[:50]))
                ))

            # Detect equipment details
            full_text = "\n".join(all_text)
            equipment_type = self._detect_equipment_type(full_text)
            level = self._detect_level(full_text)
            variant = self._detect_variant(full_text)

            key_patterns = self._extract_key_patterns(all_check_items)

            import uuid
            example = LearnedFormExample(
                id=str(uuid.uuid4())[:8],
                filename=filename,
                timestamp=time.time(),
                system_type=system_type if system_type != "General" else equipment_type or "General",
                form_type=self._detect_form_type(filename, all_sections),
                source=source,
                total_items=len(all_check_items),
                equipment_type=equipment_type,
                level=level,
                variant=variant,
                sections=all_sections,
                check_items=all_check_items[:200],
                key_patterns=key_patterns
            )

            return example

        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            return None

    def _detect_equipment_type(self, text: str) -> str:
        """Detect electrical equipment type from text content."""
        text_lower = text.lower()

        for equip_type, patterns in self.EQUIPMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.debug(f"Detected equipment type: {equip_type}")
                    return equip_type

        return ""

    def _detect_level(self, text: str) -> str:
        """Detect commissioning level (L2, L3, L4, etc.) from text."""
        text_upper = text.upper()

        level_patterns = [
            (r'\bL4C\b', 'L4C'),
            (r'\bL4\b', 'L4'),
            (r'\bL3\b', 'L3'),
            (r'\bL2C\b', 'L2C'),
            (r'\bL2\b', 'L2'),
        ]

        for pattern, level in level_patterns:
            if re.search(pattern, text_upper):
                return level

        return ""

    def _detect_variant(self, text: str) -> str:
        """Detect equipment variant (KND1, TTX1, etc.) from text."""
        text_upper = text.upper()

        variant_patterns = [
            'KND1', 'TTX1', 'TTX2', 'UCO1', 'UCO2', 'LCO1', 'LCO2', 'LCO3',
            'RMN1', 'MCA1', 'MCA2', 'MAL1', 'MAL2', 'SNB5', 'SNB6',
            'GTN5', 'GTN6', 'RIN', 'RIN1', 'CHY1'
        ]

        for variant in variant_patterns:
            if variant in text_upper:
                return variant

        return ""

    def _detect_response_type(self, text: str) -> str:
        """Detect response type from text content."""
        text_lower = text.lower()

        for resp_type, patterns in self.RESPONSE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return resp_type

        return "toggle"  # Default

    def _detect_presets(self, text: str) -> str:
        """Detect preset values from text content."""
        text_lower = text.lower()

        for pattern, preset in self.PRESET_PATTERNS:
            if re.search(pattern, text_lower):
                return preset

        return ""

    def _detect_section(self, text: str) -> Optional[str]:
        """Detect if text represents a section header."""
        text_lower = text.lower()

        for pattern, section_name in self.SECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return section_name

        return None

    def _parse_check_item(self, row: list[str], combined: str,
                          section: str, system_type: str) -> Optional[LearnedCheckItem]:
        """Parse a row as a check item with response type detection."""
        # Skip if too short or looks like a header
        if len(combined) < 15:
            return None
        if combined.lower().startswith(('item', 'description', 'check', 'no.', '#')):
            return None

        # Extract description (usually first non-empty substantial cell)
        description = ""
        acceptance = ""
        method = ""
        response_text = ""

        for i, cell in enumerate(row):
            cell = cell.strip()
            if not cell or cell.lower() in ('none', 'n/a', '-'):
                continue

            if not description and len(cell) > 10:
                description = cell
            elif description and len(cell) > 5:
                # Check if it looks like acceptance criteria
                if any(kw in cell.lower() for kw in ['pass', 'fail', 'accept', 'criteria', '±', '%', '°']):
                    acceptance = cell
                    response_text += " " + cell
                elif any(kw in cell.lower() for kw in ['method', 'procedure', 'step', 'using']):
                    method = cell
                elif any(kw in cell.lower() for kw in ['yes', 'no', 'n/a', 'toggle', 'select']):
                    response_text += " " + cell

        if not description:
            description = combined[:200]

        # Detect check type
        check_type = self._detect_check_type(description + " " + acceptance)

        # Detect priority
        priority = self._detect_priority(description + " " + acceptance)

        # Detect response type and presets
        full_text = combined + " " + response_text
        response_type = self._detect_response_type(full_text)
        presets = self._detect_presets(full_text)

        return LearnedCheckItem(
            description=description[:300],
            section=section,
            check_type=check_type,
            acceptance_criteria=acceptance[:200],
            method=method[:200],
            priority=priority,
            system_type=system_type,
            response_type=response_type,
            presets=presets
        )

    def _detect_check_type(self, text: str) -> str:
        """Detect the type of check from text."""
        text_lower = text.lower()

        for check_type, patterns in self.CHECK_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return check_type

        return "VERIFICATION"

    def _detect_priority(self, text: str) -> str:
        """Detect priority from text."""
        text_lower = text.lower()

        for priority, patterns in self.PRIORITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return priority

        return "MEDIUM"

    def _detect_form_type(self, filename: str, sections: list[LearnedSection]) -> str:
        """Detect the form type from filename and sections."""
        filename_lower = filename.lower()

        if 'pfi' in filename_lower or 'pre-func' in filename_lower:
            return "PFI"
        elif 'fpt' in filename_lower or 'functional' in filename_lower:
            return "FPT"
        elif 'ist' in filename_lower or 'integrat' in filename_lower:
            return "IST"
        elif 'cxc' in filename_lower or 'commission' in filename_lower:
            return "CXC"
        elif 'itc' in filename_lower:
            return "ITC"

        # Infer from sections
        section_names = [s.name.lower() for s in sections]
        if any('pre-func' in s or 'install' in s for s in section_names):
            return "PFI"
        if any('functional' in s or 'test' in s for s in section_names):
            return "FPT"

        return "ITC"

    def _extract_key_patterns(self, check_items: list[LearnedCheckItem]) -> list[str]:
        """Extract key patterns from check items for learning."""
        patterns = []

        # Count common phrases
        phrase_counts = {}
        for item in check_items:
            # Extract verb phrases
            words = item.description.lower().split()
            for i, word in enumerate(words[:3]):  # First 3 words often key
                if word in ('verify', 'check', 'confirm', 'ensure', 'test', 'measure',
                           'record', 'inspect', 'review', 'validate'):
                    phrase = " ".join(words[i:i+3])
                    phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        # Get top patterns
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        patterns = [phrase for phrase, count in sorted_phrases[:15] if count >= 2]

        # Extract acceptance criteria patterns
        criteria_patterns = set()
        for item in check_items:
            if item.acceptance_criteria:
                # Look for measurement patterns
                if re.search(r'±\s*\d+', item.acceptance_criteria):
                    criteria_patterns.add("Uses tolerance ranges (±X)")
                if re.search(r'\d+\s*-\s*\d+', item.acceptance_criteria):
                    criteria_patterns.add("Uses value ranges")
                if 'pass' in item.acceptance_criteria.lower() and 'fail' in item.acceptance_criteria.lower():
                    criteria_patterns.add("Explicit pass/fail criteria")

        patterns.extend(list(criteria_patterns)[:5])

        return patterns


class ExampleFormStore:
    """Storage for learned form examples."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or DEFAULT_EXAMPLES_FILE
        self._examples: list[LearnedFormExample] = []
        self._load()

    def _load(self) -> None:
        """Load examples from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._examples = [
                        LearnedFormExample.from_dict(ex)
                        for ex in data.get('examples', [])
                    ]
                logger.info(f"Loaded {len(self._examples)} learned form examples")
            except Exception as e:
                logger.error(f"Failed to load examples: {e}")
                self._examples = []

    def _save(self) -> None:
        """Save examples to storage."""
        try:
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                'version': '1.0',
                'last_updated': time.time(),
                'example_count': len(self._examples),
                'examples': [ex.to_dict() for ex in self._examples]
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self._examples)} learned examples")
        except Exception as e:
            logger.error(f"Failed to save examples: {e}")

    def add_example(self, example: LearnedFormExample) -> None:
        """Add a new learned example."""
        self._examples.append(example)
        self._save()

    def get_examples_for_system(self, system_type: str, limit: int = 5) -> list[LearnedFormExample]:
        """Get examples for a system type."""
        system_lower = system_type.lower()

        relevant = [
            ex for ex in self._examples
            if system_lower in ex.system_type.lower()
        ]

        # Also include general examples
        if len(relevant) < limit:
            general = [ex for ex in self._examples if ex.system_type.lower() == 'general']
            relevant.extend(general[:limit - len(relevant)])

        return relevant[:limit]

    def get_all_examples(self) -> list[LearnedFormExample]:
        """Get all examples."""
        return self._examples

    def get_stats(self) -> dict:
        """Get statistics about learned examples."""
        if not self._examples:
            return {
                'total_examples': 0,
                'total_items_learned': 0,
                'by_system': {},
                'by_source': {},
                'key_patterns': []
            }

        by_system = {}
        by_source = {}
        total_items = 0
        all_patterns = []

        for ex in self._examples:
            by_system[ex.system_type] = by_system.get(ex.system_type, 0) + 1
            by_source[ex.source] = by_source.get(ex.source, 0) + 1
            total_items += ex.total_items
            all_patterns.extend(ex.key_patterns)

        # Get unique patterns
        pattern_counts = {}
        for p in all_patterns:
            pattern_counts[p] = pattern_counts.get(p, 0) + 1
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_examples': len(self._examples),
            'total_items_learned': total_items,
            'by_system': by_system,
            'by_source': by_source,
            'key_patterns': [p[0] for p in top_patterns]
        }

    def generate_ai_context(self, system_type: str) -> str:
        """Generate AI context from learned examples.

        Args:
            system_type: Type of system to get context for

        Returns:
            Formatted context string for AI prompts
        """
        examples = self.get_examples_for_system(system_type, limit=3)

        if not examples:
            return ""

        context_parts = [
            f"\n--- LEARNED FROM EXAMPLE FORMS ({len(examples)} examples) ---"
        ]

        for ex in examples:
            context_parts.append(f"\nExample from {ex.source} ({ex.system_type} - {ex.total_items} items):")

            # Add section structure
            if ex.sections:
                context_parts.append("  Sections used:")
                for section in ex.sections[:8]:
                    context_parts.append(f"    - {section.name} ({section.item_count} items)")

            # Add sample check items
            if ex.check_items:
                context_parts.append("  Sample check items:")
                for item in ex.check_items[:5]:
                    context_parts.append(f"    - [{item.check_type}] {item.description[:100]}")
                    if item.acceptance_criteria:
                        context_parts.append(f"      Criteria: {item.acceptance_criteria[:80]}")

        # Add key patterns
        all_patterns = []
        for ex in examples:
            all_patterns.extend(ex.key_patterns)
        if all_patterns:
            unique_patterns = list(set(all_patterns))[:8]
            context_parts.append("\nKey patterns to follow:")
            for p in unique_patterns:
                context_parts.append(f"  - {p}")

        context_parts.append("--- END EXAMPLES ---\n")

        return "\n".join(context_parts)


# Global store instance
_example_store: Optional[ExampleFormStore] = None


def get_example_store() -> ExampleFormStore:
    """Get the global example store instance."""
    global _example_store
    if _example_store is None:
        _example_store = ExampleFormStore()
    return _example_store
