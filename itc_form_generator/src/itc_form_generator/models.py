"""Data models for Sequence of Operations and ITC Forms."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FormType(Enum):
    """Types of inspection/testing forms."""
    PFI = "Pre-Functional Inspection"
    FPT = "Functional Performance Test"
    IST = "Integrated Systems Test"
    CXC = "Commissioning Checklist"
    ITC = "Inspection, Testing & Commissioning"  # Combined comprehensive form


class Priority(Enum):
    """Priority levels for check items."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CheckItemType(Enum):
    """Types of check items."""
    VISUAL = "Visual Inspection"
    MEASUREMENT = "Measurement"
    FUNCTIONAL = "Functional Test"
    DOCUMENTATION = "Documentation Review"
    VERIFICATION = "Verification"


@dataclass
class Setpoint:
    """A control setpoint from the SOO."""
    name: str
    value: str
    units: str = ""
    description: str = ""
    adjustable: bool = False
    min_value: Optional[str] = None
    max_value: Optional[str] = None


@dataclass
class OperatingMode:
    """An operating mode defined in the SOO."""
    name: str
    description: str = ""
    conditions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    setpoints: list[Setpoint] = field(default_factory=list)


@dataclass
class Component:
    """A component or equipment item in the system."""
    tag: str
    name: str
    description: str = ""
    component_type: str = ""
    parent_system: str = ""
    setpoints: list[Setpoint] = field(default_factory=list)
    operating_modes: list[OperatingMode] = field(default_factory=list)
    interlocks: list[str] = field(default_factory=list)
    alarms: list[str] = field(default_factory=list)


@dataclass
class System:
    """A system defined in the SOO."""
    name: str
    tag: str = ""
    description: str = ""
    components: list[Component] = field(default_factory=list)
    operating_modes: list[OperatingMode] = field(default_factory=list)
    setpoints: list[Setpoint] = field(default_factory=list)
    interlocks: list[str] = field(default_factory=list)
    alarms: list[str] = field(default_factory=list)
    sequences: list[str] = field(default_factory=list)


@dataclass
class SequenceOfOperation:
    """Complete Sequence of Operation document."""
    title: str
    project: str = ""
    version: str = "1.0"
    systems: list[System] = field(default_factory=list)
    general_requirements: list[str] = field(default_factory=list)
    safety_interlocks: list[str] = field(default_factory=list)


@dataclass
class CheckItem:
    """A single check item on an inspection form."""
    id: str
    description: str
    check_type: CheckItemType
    priority: Priority = Priority.MEDIUM
    acceptance_criteria: str = ""
    method: str = ""
    expected_value: str = ""
    actual_value: str = ""
    pass_fail: str = ""
    comments: str = ""
    reference: str = ""
    system_tag: str = ""
    component_tag: str = ""


@dataclass
class FormSection:
    """A section within an inspection form."""
    title: str
    description: str = ""
    check_items: list[CheckItem] = field(default_factory=list)


@dataclass
class InspectionForm:
    """An inspection or testing form."""
    form_type: FormType
    title: str
    system: str
    system_tag: str = ""
    project: str = ""
    version: str = "1.0"
    sections: list[FormSection] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return sum(len(s.check_items) for s in self.sections)
