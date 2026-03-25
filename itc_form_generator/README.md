# ITC Form Generator

A Python tool for generating Inspection, Testing, and Commissioning (ITC) forms from Sequence of Operation (SOO) documents.

## Features

- **PDF Support with OCR**: Extract text from scanned PDF documents using Tesseract OCR
- **Multiple Form Types**: Generate PFI, FPT, IST, and CXC forms
- **Procore-Compatible Export**: Export to Excel format compatible with Procore checklist import
- **Web Interface**: Simple drag-and-drop web interface for file upload
- **CSV Export**: Export all forms to CSV for use in spreadsheets
- **Standalone Executable**: Double-click to run without Python installation

## Form Types

| Form Type | Description |
|-----------|-------------|
| **PFI** | Pre-Functional Inspection - Physical installation verification |
| **FPT** | Functional Performance Test - Operational testing |
| **IST** | Integrated Systems Test - System integration testing |
| **CXC** | Commissioning Checklist - Final commissioning verification |

---

## Quick Start (Executable)

The easiest way to use the ITC Form Generator:

1. **Double-click** the desktop shortcut **"ITC Form Generator"** (or run `dist\ITC_Form_Generator_Web.exe`)
2. Your **web browser will open automatically** to http://localhost:8080
3. **Upload** your SOO document (PDF or Markdown)
4. **Select** form types (PFI, FPT, IST, CXC)
5. Click **Generate Forms**
6. **Download** your forms as Excel, CSV, or HTML

### Stopping the Application

- Close the console window, or
- Press `Ctrl+C` in the console

---

## Usage Instructions

### Step 1: Launch the Application

**Option A - Desktop Shortcut (Recommended)**
- Double-click the **"ITC Form Generator"** shortcut on your Desktop

**Option B - Run the Executable**
- Navigate to `dist\ITC_Form_Generator_Web.exe` and double-click it

**Option C - Run with Python**
```bash
python webapp.py
```
Then open http://localhost:8080 in your browser

### Step 2: Upload Your SOO Document

1. Click **"Choose Files"** or drag and drop your file onto the upload area
2. Supported file types:
   - **PDF** - Scanned or digital PDFs (OCR supported)
   - **Markdown (.md)** - Text-based SOO documents

### Step 3: Select Form Types

Check the boxes for the form types you want to generate:

- ☑️ **PFI** - Pre-Functional Inspection
- ☑️ **FPT** - Functional Performance Test
- ☑️ **IST** - Integrated Systems Test
- ☑️ **CXC** - Commissioning Checklist

### Step 4: Generate Forms

Click the **"Generate Forms"** button. The application will:
1. Parse your SOO document
2. Extract systems and equipment
3. Generate check items for each form type
4. Display the generated forms

### Step 5: Export Your Forms

After generation, download your forms:

| Export Format | Description | Use Case |
|---------------|-------------|----------|
| **Excel (.xlsx)** | Procore-compatible format | Import directly into Procore |
| **CSV (.csv)** | All forms in one file | Spreadsheet editing |
| **HTML (.zip)** | Individual HTML files | Printing or web viewing |

---

## Procore Import Instructions

1. Generate forms and download the **Excel** file
2. Log into **Procore**
3. Navigate to **Project Tools > Inspections**
4. Click **Configure Settings** (gear icon)
5. Select **Import Checklists**
6. Upload the Excel file
7. Map columns if prompted
8. Click **Import**

---

## Sample Document

A sample SOO document is included for testing:

```
sample_soo.md
```

This contains example HVAC equipment (AHU-01, CRAH-01, etc.) with:
- Components and sensors
- Setpoints
- Operating modes
- Control sequences

---

## Installation (Development)

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR (for scanned PDF support)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Tesseract OCR (Windows)

```bash
winget install UB-Mannheim.TesseractOCR
```

Or download from: https://github.com/UB-Mannheim/tesseract/wiki

### Run the Web Application

```bash
python webapp.py
```

### Build the Executable

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console launcher.py --name "ITC_Form_Generator_Web"
```

---

## Project Structure

```
itc_form_generator/
├── dist/
│   └── ITC_Form_Generator_Web.exe  # Standalone executable
├── src/
│   └── itc_form_generator/
│       ├── __init__.py
│       ├── models.py         # Data models (System, Form, CheckItem)
│       ├── parser.py         # SOO document parser
│       ├── pdf_parser.py     # PDF extraction with OCR
│       ├── form_generator.py # Form generation logic
│       ├── renderer.py       # HTML rendering
│       ├── exporter.py       # CSV/Excel export
│       └── points_parser.py  # BMS points list parser
├── launcher.py           # Executable launcher
├── webapp.py             # Web application server
├── sample_soo.md         # Sample SOO document
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

---

## Excel Output Format

The Excel export follows the Procore checklist import format:

| Column | Description |
|--------|-------------|
| Checklist Name | Name of the checklist |
| Permissions | Access control (all, admin) |
| Auto Create Issue | Auto-create issues on fail (True/False) |
| Display Number | Item number |
| Item Text | Check item description |
| Response Type | Group Header, Yes/No/N/A, Pass/Fail/N/A, Text, Date |
| Drop-down Answers | Custom dropdown options |
| Default Answer | Pre-selected answer |
| Answers that create Non-conformance | Answers triggering NC |
| Default Issue Description | Default issue text |
| Company | Assigned company |
| Spec Reference | Specification reference |
| Root Cause Category | Root cause classification |
| More Information | Additional details |
| Priority | Priority level |

---

## Form Sections

### PFI (Pre-Functional Inspection)
- Equipment Information
- General Requirements
- Commissioning Support
- Documentation
- Safety & Equipment Requirements
- Installation Verification
- Electrical Verification
- Piping Verification
- Controls Verification
- Labeling & Identification

### FPT (Functional Performance Test)
- Equipment Information
- General Requirements
- Commissioning Support
- Prerequisites
- Documentation
- Safety Requirements
- Equipment Settings & Firmware
- Visual Inspections
- Graphics/BMS Review
- Automated Test Reports
- Startup Sequence
- Operating Mode Tests
- Sensor Testing
- Setpoint Verification
- Control Response

### IST (Integrated Systems Test)
- Safety Interlock Tests
- Alarm Tests
- Systems Integration
- Failover and Recovery

### CXC (Commissioning Checklist)
- Training Verification
- Handover Documentation
- Warranty and Final Acceptance

---

## Troubleshooting

### Port Already in Use
If you see "Address already in use", another instance may be running:
- Close all console windows running the application
- Or change the port: `python webapp.py 8081`

### PDF Not Parsing Correctly
- Ensure Tesseract OCR is installed
- Try a higher quality scan
- Convert to Markdown format for best results

### Browser Doesn't Open Automatically
- Manually open http://localhost:8080
- Check firewall settings

---

## License

Internal use only - Meta Platforms, Inc.

## Author

Richard Delaporte - DEC Operations Quality
