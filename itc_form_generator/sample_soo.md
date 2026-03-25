# Sequence of Operation - Data Center HVAC Systems

## AHU-01: Air Handling Unit

### Components
- VFD-01: Supply Fan Variable Frequency Drive
- SF-01: Supply Fan
- RF-01: Return Fan
- VFD-02: Return Fan Variable Frequency Drive
- CC-01: Cooling Coil
- CV-01: Cooling Coil Valve
- PRE-F: Pre-Filter Bank
- FINAL-F: Final Filter Bank
- OA-D: Outside Air Damper
- RA-D: Return Air Damper
- EA-D: Exhaust Air Damper
- HUM-01: Humidifier
- SAT: Supply Air Temperature Sensor
- RAT: Return Air Temperature Sensor
- OAT: Outside Air Temperature Sensor
- SAP: Supply Air Pressure Sensor
- RAF: Return Air Flow Station
- SAF: Supply Air Flow Station
- CO2: CO2 Sensor

### Setpoints
- Supply Air Temperature Setpoint: 55°F
- Supply Air Pressure Setpoint: 1.5 inwc
- Minimum Outside Air: 20%
- Cooling Coil Discharge Temperature: 52°F
- Space Temperature Setpoint: 72°F
- Space Humidity Setpoint: 50%
- CO2 Setpoint: 1000 ppm

### Operating Modes

#### Occupied Mode
- When building is in occupied mode
- Supply fan operates to maintain duct static pressure setpoint
- Return fan tracks supply fan speed minus 10%
- Outside air damper modulates to maintain minimum ventilation
- Cooling coil valve modulates to maintain discharge air temperature
- Economizer enabled when OAT < 65°F

#### Unoccupied Mode
- When building is in unoccupied mode
- Supply fan operates at minimum speed
- Return fan operates at minimum speed
- Outside air damper closes to minimum position
- Cooling coil valve modulates to maintain setback temperature

#### Morning Warmup Mode
- When transitioning from unoccupied to occupied
- Supply fan operates at 75% speed
- Return air damper fully open
- Outside air damper closed
- Duration: 30 minutes maximum

#### Economizer Mode
- When OAT is between 55°F and 65°F
- When OAT < RAT
- Outside air damper modulates for free cooling
- Mechanical cooling disabled when OA provides sufficient cooling

### Interlocks
- Supply fan proof required before cooling coil valve opens
- Freeze stat trips below 38°F, closes OA damper and stops fans
- High duct static trips supply fan at 3.0 inwc
- Smoke detector interlock stops all fans and closes dampers
- Fire alarm closes all dampers and stops fans

### Alarms
- Supply fan failure alarm
- Return fan failure alarm
- High supply air temperature alarm (>62°F)
- Low supply air temperature alarm (<48°F)
- High duct static pressure alarm (>2.5 inwc)
- Freeze stat alarm
- Filter differential pressure high alarm
- Smoke detector alarm
- VFD fault alarm

## CH-01: Chiller Plant

### Components
- CH-01: Centrifugal Chiller
- CHP-01: Primary Chilled Water Pump
- CHP-02: Primary Chilled Water Pump (Standby)
- CHS-01: Secondary Chilled Water Pump
- CHS-02: Secondary Chilled Water Pump
- CT-01: Cooling Tower
- CT-02: Cooling Tower
- CWP-01: Condenser Water Pump
- CWP-02: Condenser Water Pump
- CHWST: Chilled Water Supply Temperature Sensor
- CHWRT: Chilled Water Return Temperature Sensor
- CWST: Condenser Water Supply Temperature Sensor
- CWRT: Condenser Water Return Temperature Sensor
- DP-CHW: Chilled Water Differential Pressure Sensor

### Setpoints
- Chilled Water Supply Temperature: 44°F
- Chilled Water Return Temperature: 54°F
- Condenser Water Supply Temperature: 85°F
- Chilled Water DP Setpoint: 15 psid
- Cooling Tower Approach: 7°F
- Chiller Minimum Load: 25%

### Operating Modes

#### Cooling Mode
- When cooling demand exists
- Chiller operates to maintain CHWST setpoint
- Primary pump runs when chiller operates
- Secondary pumps modulate to maintain DP setpoint
- Cooling towers operate to maintain CWST setpoint

#### Staging Mode
- When load exceeds 80% for 10 minutes, stage up
- When load below 40% for 10 minutes, stage down
- Minimum runtime 15 minutes before staging change
- Lead/lag rotation weekly

#### Free Cooling Mode
- When OAT < 45°F for 30 minutes
- Waterside economizer enabled
- Chiller disabled
- Cooling towers provide direct cooling

### Interlocks
- Chilled water flow required before chiller starts
- Condenser water flow required before chiller starts
- Minimum flow through chiller required
- Cooling tower fan proof required for condenser pump
- Low refrigerant pressure trips chiller
- High refrigerant pressure trips chiller
- High motor temperature trips chiller

### Alarms
- Chiller fault alarm
- Low chilled water temperature alarm (<40°F)
- High chilled water temperature alarm (>50°F)
- Primary pump failure alarm
- Secondary pump failure alarm
- Cooling tower fan failure alarm
- Condenser pump failure alarm
- Low condenser water flow alarm
- High condenser water temperature alarm (>95°F)
- Chiller high current alarm
