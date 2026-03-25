"""Parser for BMS/Controls points lists.

Supports multiple formats:
- Simple CSV with column headers
- Complex enterprise format (GTN-style) with hierarchical structure
"""

import csv
import io
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PointType(Enum):
    """Types of control points."""
    AI = "Analog Input"
    AO = "Analog Output"
    DI = "Digital Input"
    DO = "Digital Output"
    AV = "Analog Value"
    BV = "Binary Value"
    IAV = "Internal Analog Value"
    IBV = "Internal Binary Value"
    UNKNOWN = "Unknown"


@dataclass
class ControlPoint:
    """A single control/BMS point."""
    point_name: str
    tag: str = ""
    point_type: PointType = PointType.UNKNOWN
    description: str = ""
    units: str = ""
    range_min: str = ""
    range_max: str = ""
    design_value: str = ""
    alarms: list[str] = field(default_factory=list)
    system_ref: str = ""
    equipment_ref: str = ""
    area: str = ""
    process_area: str = ""
    end_device: str = ""
    software_function: str = ""


@dataclass
class PointsList:
    """Collection of control points."""
    name: str = ""
    points: list[ControlPoint] = field(default_factory=list)

    @property
    def ai_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type == PointType.AI]

    @property
    def ao_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type == PointType.AO]

    @property
    def di_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type in (PointType.DI, PointType.BV, PointType.IBV)]

    @property
    def do_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type == PointType.DO]

    @property
    def av_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type in (PointType.AV, PointType.IAV)]

    @property
    def bv_points(self) -> list[ControlPoint]:
        return [p for p in self.points if p.point_type in (PointType.BV, PointType.IBV)]


class PointsListParser:
    """Parser for CSV/TSV points lists.

    Supports:
    - Simple CSV with standard column headers
    - Complex enterprise format (GTN-style) with hierarchical structure
    """

    COLUMN_ALIASES = {
        'point_name': ['point name', 'pointname', 'name', 'point', 'point id', 'pointid'],
        'tag': ['tag', 'tag name', 'tagname', 'object name', 'objectname', 'address'],
        'point_type': ['type', 'point type', 'pointtype', 'i/o type', 'io type', 'iotype'],
        'description': ['description', 'desc', 'label', 'point description', 'plc comment', 'plc\ncomment'],
        'units': ['units', 'unit', 'eng units', 'engineering units', 'eng.\nunits'],
        'range': ['range', 'limits', 'min/max', 'scaled\nrange'],
        'range_min': ['min', 'minimum', 'low limit', 'low'],
        'range_max': ['max', 'maximum', 'high limit', 'high'],
        'alarms': ['alarms', 'alarm', 'alarm limits', 'alarm points'],
        'system': ['system', 'system name', 'systemname', 'system ref'],
        'equipment': ['equipment', 'equipment name', 'equip', 'device', 'equipment tag'],
        'design_value': ['design value', 'design value\nsetpoint', 'setpoint', 'default'],
        'area': ['area'],
        'process_area': ['process area'],
        'end_device': ['end device'],
        'software_function': ['software function'],
        'item_name': ['item name'],
    }

    TYPE_PATTERNS = {
        PointType.AI: [r'\bAI\b', r'analog\s*in', r'input.*analog'],
        PointType.AO: [r'\bAO\b', r'analog\s*out', r'output.*analog'],
        PointType.DI: [r'\bDI\b', r'\bBI\b', r'digital\s*in', r'binary\s*in', r'input.*digital'],
        PointType.DO: [r'\bDO\b', r'\bBO\b', r'digital\s*out', r'binary\s*out', r'output.*digital'],
        PointType.AV: [r'\bAV\b', r'analog\s*value'],
        PointType.BV: [r'\bBV\b', r'binary\s*value'],
        PointType.IAV: [r'\biAV\b', r'internal\s*analog'],
        PointType.IBV: [r'\biBV\b', r'internal\s*binary'],
    }

    def parse(self, content: str) -> PointsList:
        """Parse points list from CSV/TSV content."""
        # Detect if this is GTN-style format (has multiple header rows)
        lines = content.split('\n')
        if self._is_gtn_format(lines):
            return self._parse_gtn_format(content)

        # Standard CSV parsing
        dialect = self._detect_dialect(content)
        reader = csv.DictReader(io.StringIO(content), dialect=dialect)

        column_map = self._map_columns(reader.fieldnames or [])

        points_list = PointsList()

        for row in reader:
            point = self._parse_row(row, column_map)
            if point and point.point_name:
                points_list.points.append(point)

        return points_list

    def _is_gtn_format(self, lines: list[str]) -> bool:
        """Detect GTN-style format with hierarchical headers."""
        if len(lines) < 5:
            return False
        # GTN format has 'Version Control' in first cell and 'Point Name' in row 2
        first_line = lines[0].lower()
        return 'version control' in first_line or 'derived point name' in lines[1].lower()

    def _parse_gtn_format(self, content: str) -> PointsList:
        """Parse GTN-style points list format."""
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        if len(rows) < 5:
            return PointsList()

        # GTN format columns (0-indexed):
        # Col 5 (Area), Col 6 (System), Col 7 (Process Area), Col 8 (Equipment)
        # Col 9 (End Device), Col 10 (Software Function), Col 11 (Item Name)
        # Col 12 (Point Name), Col 13 (Description), Col 14 (I/O Type)
        # Col 17 (Units), Col 20 (Design Value)

        COL_AREA = 4
        COL_SYSTEM = 5
        COL_PROCESS_AREA = 6
        COL_EQUIPMENT = 7
        COL_END_DEVICE = 8
        COL_SW_FUNCTION = 9
        COL_ITEM_NAME = 10
        COL_POINT_NAME = 11
        COL_DESCRIPTION = 12
        COL_IO_TYPE = 13
        COL_UNITS = 16
        COL_DESIGN_VALUE = 19

        points_list = PointsList()

        # Skip header rows (typically first 4 rows)
        for row in rows[4:]:
            if len(row) <= COL_IO_TYPE:
                continue

            # Only include rows that have an I/O type (actual points, not hierarchy objects)
            io_type_str = row[COL_IO_TYPE].strip() if len(row) > COL_IO_TYPE else ""
            if not io_type_str:
                continue

            point_name = row[COL_POINT_NAME].strip() if len(row) > COL_POINT_NAME else ""
            if not point_name:
                continue

            description = row[COL_DESCRIPTION].strip() if len(row) > COL_DESCRIPTION else ""
            units = row[COL_UNITS].strip() if len(row) > COL_UNITS else ""
            design_value = row[COL_DESIGN_VALUE].strip() if len(row) > COL_DESIGN_VALUE else ""
            system = row[COL_SYSTEM].strip() if len(row) > COL_SYSTEM else ""
            equipment = row[COL_EQUIPMENT].strip() if len(row) > COL_EQUIPMENT else ""
            area = row[COL_AREA].strip() if len(row) > COL_AREA else ""
            process_area = row[COL_PROCESS_AREA].strip() if len(row) > COL_PROCESS_AREA else ""
            end_device = row[COL_END_DEVICE].strip() if len(row) > COL_END_DEVICE else ""
            sw_function = row[COL_SW_FUNCTION].strip() if len(row) > COL_SW_FUNCTION else ""

            point_type = self._infer_point_type(io_type_str, point_name)

            point = ControlPoint(
                point_name=point_name,
                tag=point_name,
                point_type=point_type,
                description=description,
                units=units,
                design_value=design_value,
                system_ref=system,
                equipment_ref=equipment,
                area=area,
                process_area=process_area,
                end_device=end_device,
                software_function=sw_function,
            )
            points_list.points.append(point)

        return points_list

    def _detect_dialect(self, content: str) -> str:
        """Detect CSV dialect (comma or tab separated)."""
        first_line = content.split('\n')[0]
        if '\t' in first_line:
            return 'excel-tab'
        return 'excel'

    def _map_columns(self, fieldnames: list[str]) -> dict[str, str]:
        """Map actual column names to standard names."""
        column_map = {}
        fieldnames_lower = {f.lower().strip(): f for f in fieldnames}

        for standard_name, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in fieldnames_lower:
                    column_map[standard_name] = fieldnames_lower[alias]
                    break

        return column_map

    def _parse_row(
        self,
        row: dict[str, str],
        column_map: dict[str, str]
    ) -> Optional[ControlPoint]:
        """Parse a single row into a ControlPoint."""
        def get_value(key: str) -> str:
            col = column_map.get(key)
            if col and col in row:
                return row[col].strip()
            return ""

        point_name = get_value('point_name')
        if not point_name:
            return None

        point_type_str = get_value('point_type')
        point_type = self._infer_point_type(point_type_str, point_name)

        range_str = get_value('range')
        range_min = get_value('range_min')
        range_max = get_value('range_max')

        if range_str and not (range_min or range_max):
            range_min, range_max = self._parse_range(range_str)

        alarms_str = get_value('alarms')
        alarms = [a.strip() for a in alarms_str.split(',') if a.strip()] if alarms_str else []

        equipment_ref = get_value('equipment')
        if not equipment_ref:
            equipment_ref = self._extract_equipment_tag(point_name)

        return ControlPoint(
            point_name=point_name,
            tag=get_value('tag') or point_name,
            point_type=point_type,
            description=get_value('description'),
            units=get_value('units'),
            range_min=range_min,
            range_max=range_max,
            alarms=alarms,
            system_ref=get_value('system'),
            equipment_ref=equipment_ref,
        )

    def _infer_point_type(self, type_str: str, point_name: str) -> PointType:
        """Infer point type from type string or point name."""
        text = f"{type_str} {point_name}".upper()

        for point_type, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return point_type

        name_upper = point_name.upper()
        if any(kw in name_upper for kw in ['TEMP', 'PRESS', 'FLOW', 'LEVEL', 'HUMID', 'SPEED', 'FREQ']):
            return PointType.AI
        if any(kw in name_upper for kw in ['CMD', 'SP', 'SETPOINT', 'OUTPUT']):
            return PointType.AO
        if any(kw in name_upper for kw in ['STATUS', 'STS', 'PROOF', 'ALARM', 'FAULT', 'RUN']):
            return PointType.DI
        if any(kw in name_upper for kw in ['START', 'STOP', 'ENABLE', 'ON', 'OFF']):
            return PointType.DO

        return PointType.UNKNOWN

    def _parse_range(self, range_str: str) -> tuple[str, str]:
        """Parse range string like '0-100' or '32 to 212'."""
        patterns = [
            r'(-?[\d.]+)\s*[-–—to]+\s*(-?[\d.]+)',
            r'(-?[\d.]+)\s*,\s*(-?[\d.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, range_str, re.IGNORECASE)
            if match:
                return match.group(1), match.group(2)

        return "", ""

    def _extract_equipment_tag(self, point_name: str) -> str:
        """Extract equipment tag from point name."""
        patterns = [
            r'^([A-Z]{2,4}[-_]?\d{1,3}[A-Z]?)',
            r'^([A-Z]+\d+)',
        ]

        for pattern in patterns:
            match = re.match(pattern, point_name.upper())
            if match:
                return match.group(1)

        return ""
