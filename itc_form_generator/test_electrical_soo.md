# Sequence of Operations - Electrical Equipment Test

## System: 260627_L3_Automatic Transfer Switch_ERA - ATS - FCA-3_KND1_Rev0_CombinedBMS

### Equipment Description
Automatic Transfer Switch (ATS) for Fire Control Area 3, located in East Row A.
This ATS provides automatic switching between normal utility power and emergency
generator power for critical fire protection systems.

### Components
- ATS-FCA-3: Main transfer switch unit
- CT-FCA-3: Current transformers
- PT-FCA-3: Potential transformers
- CPT-FCA-3: Control power transformer
- CB-N: Normal source circuit breaker
- CB-E: Emergency source circuit breaker

### Setpoints
| Parameter | Value | Units | Adjustable |
|-----------|-------|-------|------------|
| Transfer Time | 10 | seconds | Yes |
| Retransfer Delay | 5 | minutes | Yes |
| Voltage Low | 90 | % | Yes |
| Voltage High | 110 | % | Yes |
| Frequency Low | 59 | Hz | Yes |
| Frequency High | 61 | Hz | Yes |

### Operating Modes

#### Normal Mode
- ATS connected to utility source (Normal)
- All protection and monitoring active
- BMS communication enabled

#### Emergency Mode
- ATS transfers to generator source (Emergency)
- Transfer initiated on utility power failure
- Load shed sequence as required

#### Test Mode
- Manual test of transfer operation
- Exercise generator without load transfer
- Verify all indicating lights and alarms

### Interlocks
- Generator ready signal required before transfer to emergency
- Utility source must be stable for 5 minutes before retransfer
- Fire pump start shall not initiate during transfer
- Load shed sequence before emergency transfer

### Alarms
- Source 1 (Normal) Not Available
- Source 2 (Emergency) Not Available
- ATS in Emergency Position
- ATS Transfer Failure
- Ground Fault Detected
- Overcurrent Warning
- Communication Failure

---

## System: 260000_L3_Row Switch Board_ERA - RSB - 03_KND1_Rev0_CombinedBMS

### Equipment Description
Row Switch Board (RSB) #03 in East Row A serving data hall power distribution.
Provides 480V power distribution to downstream equipment.

### Components
- RSB-ERA-03: Main switchboard assembly
- CB-MAIN: Main circuit breaker (2000A)
- CB-F1 through CB-F8: Feeder circuit breakers
- PT-RSB-03: Potential transformers
- CT-RSB-03: Current transformers
- GFI: Ground fault indication system
- EPMS: Electrical Power Monitoring System integration

### Setpoints
| Parameter | Value | Units | Adjustable |
|-----------|-------|-------|------------|
| Overcurrent Pickup | 110 | % | Yes |
| Ground Fault Pickup | 1200 | A | Yes |
| Undervoltage Pickup | 80 | % | No |
| Overvoltage Pickup | 110 | % | No |

### Operating Modes

#### Normal Operation
- All feeders energized
- Continuous power quality monitoring
- BMS/EPMS data transmission active

#### Load Transfer
- Coordinated with upstream ATS
- Sequential feeder transfer as required

#### Maintenance
- Individual feeder isolation capability
- Arc flash protection active

### Interlocks
- Main breaker position interlock with upstream source
- Feeder breakers interlocked with downstream equipment
- Door safety interlock for arc flash protection
- Kirk key interlock system

### Alarms
- Main Breaker Trip
- Feeder Breaker Trip
- Ground Fault Alarm
- High Temperature Alarm
- Communication Failure
- Power Quality Event
