# SOO and Points List Integration Guide

## Overview

The **Sequence of Operations (SOO)** and **Points List** work together to generate comprehensive ITC forms:

- **SOO** describes **WHAT** the system should do (control logic, sequences, alerts)
- **Points List** describes **HOW** it's implemented (actual BMS point names, ranges, setpoints)

## SOO Structure (GTN Data Hall Example)

### Document Hierarchy

```
1. Introduction
   └── Executive Summary, Control System Overview
2. Network Architecture
   └── EIO Ring, DIO1/DIO2 Networks
3. Alerting Standards
   └── Alert Levels, Notification Rules
4. PID Control
   └── Direct/Reverse Acting, Tracking, Manual Control
5. Manual Control
   └── Output Control Override
6. Setpoints
   └── Global Common/Applied Setpoints
7. Area Setpoints (DHA)
   └── Temperature, Dewpoint, Humidity Sensors
8. TWMUS (Technical Water Makeup) System
   └── Tank Level, Pressure, Pumps
9. CDU (Coolant Distribution Unit) System
   └── TWSL, FWSL, FWRL Process Areas
10. FC (Fan Coil) System
    └── Supply Air, Return Air Process Areas
```

### SOO Tag Naming Convention

SOO uses template tags with `#` placeholders:
```
[DH#.CDU#.FWRL.VLV.ACT.DevAlrt.Sp]
  │   │    │    │   │     │      │
  │   │    │    │   │     │      └── Property (Setpoint)
  │   │    │    │   │     └── Alert Type (Deviation Alert)
  │   │    │    │   └── Device (Actuator)
  │   │    │    └── Equipment (Valve)
  │   │    └── Process Area (Facility Water Return Line)
  │   └── System ID placeholder (CDU01, CDU02, etc.)
  └── Area ID placeholder (DH5A1, DH6A1, etc.)
```

### Key SOO Elements for Form Generation

#### 1. Control Sequences
```
Example from SOO:
"When the building operator sets the unit enable flag
[DH#.FC#n.UNIT.Enable.vCmd] to 'ON', the FC will start up
in sequence..."

This generates check items:
- Verify unit enable command functionality
- Test startup sequence timing
- Confirm device states after enable
```

#### 2. Setpoint Tables
```
SOO Table:
┌────────────────────────────────────────┬─────────────┐
│ Tag Name                               │ Set Point   │
├────────────────────────────────────────┼─────────────┤
│ [DH#.CDU#.FWRL.VLV.MinPos.Sp]         │ 0.0 %       │
│ [DH#.CDU#.FWRL.VLV.MaxPos.Sp]         │ 85.0 %      │
└────────────────────────────────────────┴─────────────┘

This generates check items:
- Verify valve minimum position setpoint = 0.0%
- Verify valve maximum position setpoint = 85.0%
```

#### 3. Alert Definitions
```
SOO Alert Table:
┌────────────────────────────────────┬──────────┬─────────┬────────────┐
│ Tag Name                           │ Setpoint │ Delay   │ Reset DB   │
├────────────────────────────────────┼──────────┼─────────┼────────────┤
│ [DH#.CDU#.TWSL.TEMP.HiAlrt.#]     │ 90.0 °F  │ 30 s    │ 2.0 °F     │
└────────────────────────────────────┴──────────┴─────────┴────────────┘

Alert Text: "High: Technical Water Supply Line Temperature"
Alert Level: 2

This generates check items:
- Test high temperature alert triggers at 90.0°F
- Verify 30-second delay before alert activation
- Confirm alert clears at 88.0°F (90.0 - 2.0)
```

#### 4. Device Fallback States
```
SOO Fallback Table:
┌─────────────────────────────────────┬──────────┬──────────┬──────────┐
│ Output Tag Name                     │ Fallback │ Unit Off │ Power    │
│                                     │ State    │ State    │ Loss     │
├─────────────────────────────────────┼──────────┼──────────┼──────────┤
│ [DH#.FC#n.SA.FAN.ECM.SpdSig]       │ Last     │ 0.0%     │ OFF      │
│ [DH#.FC#n.FWRL.VLV.ACT.PosSig]     │ Last     │ 0.0%     │ Last     │
└─────────────────────────────────────┴──────────┴──────────┴──────────┘

This generates check items:
- Test comms loss fallback to last state
- Verify unit off drives outputs to 0.0%
- Confirm power loss behavior
```

## Points List Structure (GTN Format)

### Column Layout
```
Col 5:  Area (DH5A1)
Col 6:  System (CDU01F)
Col 7:  Process Area (FWRL)
Col 8:  Equipment (VLV)
Col 9:  End Device (ACT)
Col 10: Software Function (DevAlrt)
Col 11: Item Name (Sp)
Col 12: Point Name (DH5A1.CDU01F.FWRL.VLV.ACT.DevAlrt.Sp)
Col 13: Description (Deviation Alert Setpoint)
Col 14: I/O Type (AV)
Col 17: Units (%)
Col 20: Design Value (5.0)
```

### I/O Types and Test Categories

| I/O Type | Description | Test Category |
|----------|-------------|---------------|
| AI | Analog Input | Sensor Testing & Calibration |
| AO | Analog Output | Control Output Verification |
| AV | Analog Value | Setpoint Verification |
| BI | Binary Input | Status Verification |
| BV | Binary Value | Command/Status Testing |
| DI | Digital Input | Status Verification |
| DO | Digital Output | Command Testing |

## How They Link Together

### 1. Tag Resolution
SOO template tags resolve to actual Points List points:
```
SOO:        [DH#.CDU#.FWRL.VLV.MaxPos.Sp]
Points:     DH5A1.CDU01F.FWRL.VLV.MaxPos.Sp
            DH5A1.CDU02F.FWRL.VLV.MaxPos.Sp
            DH5A1.CDU03F.FWRL.VLV.MaxPos.Sp
            ... (for all CDUs)
```

### 2. Setpoint Values
Points List provides actual design values:
```
Point:      DH5A1.CDU01F.FWRL.VLV.MaxPos.Sp
I/O Type:   AV
Design Val: 85.0
Units:      %

This populates the check item:
"Verify DH5A1.CDU01F.FWRL.VLV.MaxPos.Sp = 85.0%"
```

### 3. Alert Ranges
Points List provides alert thresholds:
```
Point:      DH5A1.CDU01F.TWSL.TEMP.HiAlrt.Sp
I/O Type:   AV
Design Val: 90.0
Units:      °F

Point:      DH5A1.CDU01F.TWSL.TEMP.HiAlrt.Dly
I/O Type:   AV
Design Val: 30000
Units:      ms

This generates detailed alert tests with actual values.
```

## Form Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT FILES                             │
├─────────────────────┬───────────────────────────────────────┤
│ SOO Document        │ Points List                           │
│ - Control sequences │ - Actual point names                  │
│ - Alert definitions │ - Design values/setpoints             │
│ - Setpoint tables   │ - I/O types                          │
│ - Fallback states   │ - Engineering units                   │
└─────────────────────┴───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FORM GENERATOR                           │
│  1. Parse SOO to extract systems and sequences              │
│  2. Parse Points List to get actual point data              │
│  3. Match points to systems (by system_ref)                 │
│  4. Generate check items with actual values                 │
│  5. Add unmatched points as "Additional Tests"              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT FORMS                             │
├─────────────────────────────────────────────────────────────┤
│ PFI (Pre-Functional Inspection)                             │
│  - Visual inspections                                       │
│  - Equipment verification                                   │
│  - Wiring and labeling checks                              │
├─────────────────────────────────────────────────────────────┤
│ FPT (Functional Performance Test)                           │
│  - Control sequence testing                                 │
│  - Setpoint verification (with actual values from points)   │
│  - Alert testing (with thresholds from points)             │
│  - Deviation alert testing                                  │
│  - Fallback state verification                             │
├─────────────────────────────────────────────────────────────┤
│ IST (Integrated Systems Test)                               │
│  - Inter-system communication                               │
│  - Cascading control verification                          │
│  - Network failover testing                                │
└─────────────────────────────────────────────────────────────┘
```

## Example: CDU Valve Control Test

### From SOO:
```
"The Facility Water Return Line Valve automatic control signal
[DH#.CDU#.FWRL.VLV.ACT.CntrlSel.AutoSig] operates proportionally
over the 0.0 percent to 100.0 percent range..."

Setpoints:
- [DH#.CDU#.FWRL.VLV.MinPos.Sp] = 0.0%
- [DH#.CDU#.FWRL.VLV.MaxPos.Sp] = 85.0%

Deviation Alert:
- [DH#.CDU#.FWRL.VLV.ACT.DevAlrt.Sp] = ±5.0%
- [DH#.CDU#.FWRL.VLV.ACT.DevAlrt.Dly] = 300 s
- [DH#.CDU#.FWRL.VLV.ACT.DevAlrt.RstDb] = ±2.5%
```

### From Points List (for CDU01F):
```
DH5A1.CDU01F.FWRL.VLV.MaxPos.Sp      = 85.0%
DH5A1.CDU01F.FWRL.VLV.MinPos.Sp      = 0.0%
DH5A1.CDU01F.FWRL.VLV.ACT.DevAlrt.Sp = 5.0%
DH5A1.CDU01F.FWRL.VLV.ACT.DevAlrt.Dly = 300000 ms
DH5A1.CDU01F.FWRL.VLV.ACT.DevAlrt.RstDb = 2.5%
DH5A1.CDU01F.FWRL.VLV.ACT.PosFb      = (AI)
DH5A1.CDU01F.FWRL.VLV.ACT.PosSig     = (AO)
```

### Generated Check Items:
```
SETPOINT VERIFICATION:
[ ] Verify DH5A1.CDU01F.FWRL.VLV.MinPos.Sp = 0.0%
[ ] Verify DH5A1.CDU01F.FWRL.VLV.MaxPos.Sp = 85.0%

CONTROL TESTING:
[ ] Verify valve modulates proportionally with control signal
[ ] Confirm valve position limited to 0.0% - 85.0% range
[ ] Test DH5A1.CDU01F.FWRL.VLV.ACT.PosFb tracks command

DEVIATION ALERT TESTING:
[ ] Force 6% deviation between command and feedback
[ ] Verify alert DH5A1.CDU01F.FWRL.VLV.ACT.DevAlrt.Alrt
    activates after 300 seconds
[ ] Return deviation to 2.4%
[ ] Confirm alert clears (within 2.5% reset deadband)

CHANNEL ALERT TESTING:
[ ] Simulate sensor failure
[ ] Verify DH5A1.CDU01F.FWRL.VLV.ACT.ChnlAlrt.Alrt activates
```

## Summary Statistics (GTN Data Hall)

| Metric | Count |
|--------|-------|
| SOO Pages | 57 |
| Systems Defined | CDU, FC, TWMUS, DHA |
| Tag Templates in SOO | 297 |
| Alert Definitions | 87 |
| Setpoint Definitions | 56 |
| Points List Total | 47,184 |
| Unique Systems | 513 |
| Points with Design Values | 17,100 |

This integration ensures every control sequence in the SOO can be tested with specific, verifiable values from the Points List.
