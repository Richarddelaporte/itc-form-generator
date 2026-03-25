# Points List Integration Guide

## Overview

The ITC Form Generator can use a **BMS/Controls Points List** in combination with the **Sequence of Operations (SOO)** document to generate more refined and detailed commissioning forms.

## Current State

Currently, the points list is:
- ✅ Parsed from CSV/TSV files
- ✅ Categorized by type (AI, AO, DI, DO)
- ✅ Displayed as statistics on results page
- ❌ **NOT used to enhance form generation**

## Integration Opportunities

### 1. **Sensor Testing Section (FPT)**
**Current**: Generic sensor testing items
**Enhanced**: Specific test items for each AI point with calibration ranges

```
For each AI point in points_list:
  - Create check item: "Verify {point_name} ({description})"
  - Add acceptance criteria: "{range_min} to {range_max} {units}"
  - Add measurement field for actual reading
```

**Example Output:**
| Check Item | Description | Expected | Actual | Pass/Fail |
|------------|-------------|----------|--------|-----------|
| AI-001 | Verify AHU-01_SAT (Supply Air Temperature) | 40-90 °F | _____ | ☐ |
| AI-002 | Verify AHU-01_RAT (Return Air Temperature) | 55-85 °F | _____ | ☐ |

### 2. **Setpoint Verification Section (FPT)**
**Current**: Generic setpoint checks
**Enhanced**: Specific verification for each AO point

```
For each AO point in points_list:
  - Create check item: "Verify {point_name} setpoint"
  - Add design setpoint from SOO if available
  - Add commanded value verification
```

**Example Output:**
| Check Item | Setpoint | Design Value | Actual | Match |
|------------|----------|--------------|--------|-------|
| AO-001 | AHU-01_SAT_SP | 55°F | _____ | ☐ |
| AO-002 | AHU-01_SAP_SP | 1.5 inWC | _____ | ☐ |

### 3. **Status Verification Section (PFI/FPT)**
**Current**: Generic equipment status checks
**Enhanced**: Specific DI point status verification

```
For each DI point in points_list:
  - Create check item: "Verify {description} status indication"
  - Add expected state for given condition
```

**Example Output:**
| Check Item | Status Point | Expected State | Actual | Verified |
|------------|--------------|----------------|--------|----------|
| DI-001 | AHU-01_SF_STS | On when fan running | _____ | ☐ |
| DI-002 | AHU-01_FILTER_DP | Normal (no alarm) | _____ | ☐ |

### 4. **Control Output Verification (FPT)**
**Current**: Generic output testing
**Enhanced**: Specific DO point command verification

```
For each DO point in points_list:
  - Create check item: "Verify {description} command"
  - Add test procedure for commanding output
```

### 5. **Alarm Testing Section (IST)**
**Current**: Generic alarm tests
**Enhanced**: Specific alarm point testing

```
For each DI point with "Alarm" or "Fault" in description:
  - Create alarm simulation test
  - Create alarm acknowledgment test
  - Create alarm reset test
```

### 6. **Graphics/BMS Review Section (FPT)**
**Current**: Generic graphics review items
**Enhanced**: Point-by-point BMS verification

```
For each point in points_list by equipment:
  - Verify point displayed on graphics
  - Verify point trending configured
  - Verify point addressing correct
```

## Implementation Approach

### Phase 1: Modify FormGenerator

```python
class FormGenerator:
    def __init__(self, soo: SequenceOfOperation, points_list: PointsList = None):
        self.soo = soo
        self.points_list = points_list
        self.item_counter = 0

    def _get_points_for_system(self, system: System) -> list[ControlPoint]:
        """Get points matching this system's equipment."""
        if not self.points_list:
            return []

        matching_points = []
        for point in self.points_list.points:
            # Match by equipment tag or system reference
            if (point.equipment_ref == system.tag or
                point.system_ref == system.name or
                system.tag in point.point_name):
                matching_points.append(point)

        return matching_points
```

### Phase 2: Enhanced Section Generators

```python
def _create_sensor_testing_section(self, system: System) -> FormSection:
    section = FormSection(
        title="Sensor Testing & Calibration",
        description="Verify all sensor readings are within calibration"
    )

    # Get AI points for this system
    system_points = self._get_points_for_system(system)
    ai_points = [p for p in system_points if p.point_type == PointType.AI]

    if ai_points:
        # Create specific check items for each sensor
        for point in ai_points:
            acceptance = f"{point.range_min} to {point.range_max} {point.units}" if point.range_min else "Within design range"
            section.check_items.append(CheckItem(
                id=self._next_id("FPT"),
                description=f"Verify {point.point_name}: {point.description}",
                check_type=CheckItemType.MEASUREMENT,
                priority=Priority.HIGH,
                acceptance_criteria=acceptance,
                expected_value=f"{point.range_min}-{point.range_max} {point.units}",
                system_tag=system.tag,
                component_tag=point.equipment_ref
            ))
    else:
        # Fall back to generic sensor checks
        # ... existing generic items ...

    return section
```

### Phase 3: Update Webapp Integration

```python
# In _handle_generate():
generator = FormGenerator(soo, points_list)  # Pass points_list
forms = generator.generate_all_forms()
```

## Points-SOO Cross-Reference

The integration creates a cross-reference between:

| SOO Element | Points List Element | Integration |
|-------------|---------------------|-------------|
| System Tag (e.g., AHU-01) | Equipment Reference | Match points to systems |
| Setpoints | AO Points | Verify commanded values |
| Sensors | AI Points | Calibration verification |
| Equipment Status | DI Points | Status indication checks |
| Control Commands | DO Points | Output verification |
| Alarms | DI Points (Alarm/Fault) | Alarm testing |

## Sample Points List Format

The points list parser supports flexible CSV/TSV formats:

### Minimal Format:
```csv
Point Name,Type,Description
AHU-01_SAT,AI,Supply Air Temperature
AHU-01_SAT_SP,AO,Supply Air Temp Setpoint
```

### Full Format:
```csv
Point Name,Type,Description,Units,Range,Equipment,System
AHU-01_SAT,AI,Supply Air Temperature,°F,40-90,AHU-01,Air Handling Unit 01
AHU-01_SAT_SP,AO,Supply Air Temp Setpoint,°F,55-75,AHU-01,Air Handling Unit 01
```

### Supported Column Names:
- **Point Name**: `point name`, `pointname`, `name`, `point`, `point id`
- **Type**: `type`, `point type`, `i/o type`, `io type`
- **Description**: `description`, `desc`, `label`
- **Units**: `units`, `unit`, `eng units`
- **Range**: `range`, `min/max`, or separate `min` and `max` columns
- **Equipment**: `equipment`, `equipment name`, `device`, `equipment tag`
- **System**: `system`, `system name`, `system ref`

## Benefits of Integration

1. **More Accurate Forms**: Check items match actual installed points
2. **Complete Coverage**: Every point gets a corresponding test item
3. **Calibration Ranges**: Acceptance criteria include actual sensor ranges
4. **Reduced Manual Effort**: No need to manually add point-specific items
5. **Consistency**: Forms match the BMS configuration
6. **Traceability**: Clear link between points and test items

## Files to Modify

1. **form_generator.py**: Add points_list parameter, enhance section generators
2. **webapp.py**: Pass points_list to FormGenerator
3. **models.py**: No changes needed (already has component_tag field)

## Sample Enhanced Output

With points integration, a sensor testing section would look like:

**Before (Generic):**
- Verify temperature sensors are calibrated
- Verify pressure sensors are calibrated
- Verify humidity sensors are calibrated

**After (Points-Enhanced):**
- Verify AHU-01_SAT: Supply Air Temperature (40-90°F)
- Verify AHU-01_RAT: Return Air Temperature (55-85°F)
- Verify AHU-01_MAT: Mixed Air Temperature (40-85°F)
- Verify AHU-01_OAT: Outside Air Temperature (-20-120°F)
- Verify AHU-01_SAP: Supply Air Pressure (0-5 inWC)
- Verify AHU-01_SF_SPD: Supply Fan Speed Feedback (0-100%)
- ... (all AI points for this system)
