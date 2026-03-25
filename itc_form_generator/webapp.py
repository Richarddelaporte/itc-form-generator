#!/usr/bin/env python3
"""
ITC Form Generator Web Application

A zero-dependency web server for generating inspection and testing forms
from Sequence of Operation documents and BMS points lists.

Usage:
    python webapp.py [port]

    Default port is 8080 (or PORT environment variable for Nest deployment).
    Open http://localhost:8080 in your browser.

Nest Deployment:
    This app is compatible with Meta's Nest platform. It includes:
    - /api/health endpoint for health checks
    - PORT environment variable support
    - IPv6 hostname binding
"""

import cgi
import html
import io
import json
import os
import sys
import tempfile
import time
import uuid
import zipfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuration from environment (for Nest deployment)
PORT = int(os.environ.get('PORT', 8080))
# Use localhost for local development, IPv6 '::' for Nest deployment
_default_host = '::' if os.environ.get('PORT') or os.environ.get('NEST_APP_NAME') else 'localhost'
HOSTNAME = os.environ.get('HOSTNAME', _default_host)

# App version for health checks
APP_VERSION = "1.0.0"
APP_NAME = "itc_form_generator"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from itc_form_generator.parser import SOOParser, detect_document_type
from itc_form_generator.form_generator import FormGenerator
from itc_form_generator.renderer import HTMLRenderer
from itc_form_generator.points_parser import PointsListParser
from itc_form_generator.pdf_parser import PDFParser, check_pdf_support
from itc_form_generator.exporter import FormExporter, check_excel_support
from itc_form_generator.feedback_store import (
    get_feedback_store, create_feedback_entry, FeedbackStore
)
from itc_form_generator.example_form_parser import (
    ExampleFormParser, get_example_store, ExampleFormStore
)
# MUA-specific imports
from itc_form_generator.mua_parser import MUASOOParser, parse_mua_soo
from itc_form_generator.mua_form_generator import MUAFormGenerator, generate_mua_form


def get_pdf_status():
    """Check PDF support dynamically (not cached)."""
    return check_pdf_support()


SESSIONS: dict[str, dict] = {}


PAGE_UPLOAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ITC Form Generator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 700px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 8px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .upload-section {
            margin-bottom: 25px;
        }
        .upload-section h3 {
            color: #444;
            margin-bottom: 12px;
            font-size: 16px;
        }
        .drop-zone {
            display: block;
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #fafafa;
            margin-bottom: 0;
            min-height: 120px;
        }
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .drop-zone.has-file {
            border-color: #22c55e;
            background: #f0fdf4;
        }
        .drop-zone input[type="file"] {
            display: none;
        }
        .drop-zone .icon {
            font-size: 40px;
            margin-bottom: 10px;
            display: block;
        }
        .drop-zone .text {
            color: #666;
            font-size: 14px;
            display: block;
        }
        .drop-zone .filename {
            margin-top: 10px;
            font-weight: bold;
            color: #333;
            display: block;
        }
        .drop-zone .formats {
            font-size: 11px;
            color: #888;
            margin-top: 8px;
            display: block;
        }
        .optional-badge {
            background: #e5e7eb;
            color: #6b7280;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 8px;
        }
        button[type="submit"] {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }
        button[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        button[type="submit"]:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        /* Progress overlay styles */
        .progress-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .progress-overlay.active {
            display: flex;
        }
        .progress-modal {
            background: white;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            max-width: 450px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .progress-title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .progress-subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 25px;
        }
        .progress-bar-container {
            background: #e5e7eb;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-bar.indeterminate {
            width: 30%;
            animation: indeterminate 1.5s ease-in-out infinite;
        }
        @keyframes indeterminate {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(400%); }
        }
        .progress-percent {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .progress-time {
            color: #666;
            font-size: 13px;
        }
        .progress-status {
            color: #888;
            font-size: 12px;
            margin-top: 15px;
            font-style: italic;
        }
        .info-box {
            background: #f0f4ff;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-size: 13px;
            color: #555;
        }
        .info-box h4 {
            margin-bottom: 8px;
            color: #333;
        }
        .info-box ul {
            margin-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 ITC Form Generator</h1>
        <p class="subtitle">Generate Inspection, Testing & Commissioning forms from Sequence of Operations documents</p>

        <form method="POST" action="/generate" enctype="multipart/form-data" id="uploadForm">
            <div class="upload-section">
                <h3>📄 Sequence of Operations Document <span style="color: red;">*</span></h3>
                <label for="sooFile" class="drop-zone" id="sooDropZone">
                    <input type="file" name="soo_file" id="sooFile" accept=".md,.txt,.pdf,.doc,.docx" required
                           onchange="document.getElementById('sooFilename').textContent = this.files[0] ? '✓ ' + this.files[0].name : ''; this.parentElement.classList.toggle('has-file', this.files.length > 0);">
                    <span class="icon">📋</span>
                    <span class="text">Drag & drop your SOO file here, or click to browse</span>
                    <span class="formats">Supported: PDF, Markdown (.md), Text (.txt)</span>
                    <span class="filename" id="sooFilename"></span>
                </label>
            </div>

            <div class="upload-section">
                <h3>📊 Points List <span class="optional-badge">Optional</span></h3>
                <label for="pointsFile" class="drop-zone" id="pointsDropZone">
                    <input type="file" name="points_file" id="pointsFile" accept=".csv,.tsv,.txt,.xlsx"
                           onchange="document.getElementById('pointsFilename').textContent = this.files[0] ? '✓ ' + this.files[0].name : ''; this.parentElement.classList.toggle('has-file', this.files.length > 0);">
                    <span class="icon">📈</span>
                    <span class="text">Drag & drop your points list CSV/TSV, or click to browse</span>
                    <span class="filename" id="pointsFilename"></span>
                </label>
            </div>

            <div class="upload-section">
                <h3>🤖 AI Enhancement <span class="optional-badge">Beta</span></h3>
                <div style="background: #f8f9fa; border-radius: 8px; padding: 15px;">
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="checkbox" name="use_ai" value="true" id="useAiCheckbox" style="width: 20px; height: 20px; margin-right: 12px; accent-color: #667eea;">
                        <div>
                            <strong style="color: #333;">Enable AI-Enhanced Form Generation</strong>
                            <p style="color: #666; font-size: 12px; margin-top: 4px;">
                                Uses Meta's Llama AI to generate context-specific check items and acceptance criteria.
                                Results in more accurate, system-specific inspection forms.
                            </p>
                        </div>
                    </label>
                    <div id="aiInfoBox" style="display: none; margin-top: 12px; padding: 10px; background: #e8f4fd; border-radius: 6px; font-size: 12px; color: #1e40af;">
                        ⚡ <strong>Note:</strong> AI enhancement may take 30-60 seconds longer but produces more specific check items tailored to your system's setpoints, operating modes, and interlocks.
                    </div>
                </div>
            </div>

            <button type="submit" id="submitBtn">Generate ITC Forms</button>
        </form>

        <!-- Example Form Upload Section -->
        <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e5e7eb;">
            <h2 style="color: #333; margin-bottom: 8px;">📚 Train AI with Example Forms</h2>
            <p style="color: #666; margin-bottom: 20px; font-size: 14px;">
                Upload existing ITC forms (Excel/CSV) from other companies to help the AI learn industry best practices and generate better forms.
            </p>

            <form method="POST" action="/upload-example" enctype="multipart/form-data" id="exampleForm">
                <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
                    <div style="flex: 2; min-width: 250px;">
                        <span style="display: block; font-weight: 500; color: #555; margin-bottom: 5px;">Example Form File *</span>
                        <label for="exampleFile" class="drop-zone" id="exampleDropZone" style="padding: 20px;">
                            <input type="file" name="example_file" id="exampleFile" accept=".xlsx,.xls,.csv" required
                                   onchange="document.getElementById('exampleFilename').textContent = this.files[0] ? '✓ ' + this.files[0].name : ''; this.parentElement.classList.toggle('has-file', this.files.length > 0);">
                            <span class="icon" style="font-size: 30px;">📑</span>
                            <span class="text" style="font-size: 13px;">Drop Excel/CSV form here</span>
                            <span class="filename" id="exampleFilename"></span>
                        </label>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 5px;">Source/Company *</label>
                            <input type="text" name="source" placeholder="e.g., Acme Commissioning" required
                                   style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 5px;">System Type</label>
                            <select name="system_type" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
                                <option value="General">General / Multiple</option>
                                <option value="RSB">RSB - Row Switch Board</option>
                                <option value="ATS">ATS - Automatic Transfer Switch</option>
                                <option value="Generator">Generator / Genset</option>
                                <option value="UPS">UPS - Uninterruptible Power</option>
                                <option value="PDU">PDU - Power Distribution Unit</option>
                                <option value="Transformer">Transformer</option>
                                <option value="AHU">Air Handling Unit (AHU)</option>
                                <option value="FCU">Fan Coil Unit (FCU)</option>
                                <option value="Chiller">Chiller</option>
                                <option value="CRAH">CRAH/CRAC</option>
                                <option value="Cooling Tower">Cooling Tower</option>
                                <option value="Pump">Pump</option>
                                <option value="Data Hall">Data Hall/Data Center</option>
                            </select>
                        </div>
                    </div>
                </div>
                <button type="submit" style="padding: 12px 24px; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer;">
                    📤 Upload & Learn from Example
                </button>
            </form>

            <!-- Learned Examples Stats -->
            <div id="learnedExamplesStats" style="margin-top: 20px; padding: 15px; background: #f0fdf4; border-radius: 8px; display: none;">
                <h4 style="color: #166534; margin-bottom: 10px;">🧠 Learned Examples</h4>
                <div id="examplesContent"></div>
            </div>
        </div>

        <!-- Quick Generate from Template Section -->
        <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e5e7eb;">
            <h2 style="color: #333; margin-bottom: 8px;">⚡ Quick Generate from Template</h2>
            <p style="color: #666; margin-bottom: 20px; font-size: 14px;">
                Generate ITC forms instantly using pre-built templates based on production data from BIM360/ACC.
                No document upload required.
            </p>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <!-- RSB Template Card -->
                <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; border: 2px solid #e5e7eb;">
                    <h3 style="color: #333; margin-bottom: 10px;">🔌 RSB - Row Switch Board</h3>
                    <p style="color: #666; font-size: 13px; margin-bottom: 15px;">
                        Electrical distribution equipment forms with 45,770+ production uses
                    </p>
                    <form id="rsbTemplateForm" style="display: flex; flex-direction: column; gap: 12px;">
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 13px;">Level</label>
                            <select id="rsbLevel" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                                <option value="L4">L4 - Commissioning</option>
                                <option value="L3">L3 - Combined BMS</option>
                            </select>
                        </div>
                        <div id="rsbL4Options">
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 13px;">Form Type</label>
                            <select id="rsbFormType" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                                <option value="CEV">CEV - Commissioning Equipment Verification (45,770 uses)</option>
                                <option value="FPT">FPT - Functional Performance Test (24,892 uses)</option>
                                <option value="LCO3">LCO3 - Line Circuit (8,160 uses)</option>
                                <option value="Cable">Cable FPT (5,358 uses)</option>
                            </select>
                        </div>
                        <div id="rsbL3Options" style="display: none;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Area</label>
                                    <select id="rsbArea" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="ERA">ERA</option>
                                        <option value="ERB">ERB</option>
                                        <option value="ERC">ERC</option>
                                        <option value="ERD">ERD</option>
                                        <option value="DHA">DHA</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Number</label>
                                    <select id="rsbNumber" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="01">01</option>
                                        <option value="02">02</option>
                                        <option value="03">03</option>
                                        <option value="04">04</option>
                                        <option value="05">05</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Variant</label>
                                    <select id="rsbVariant" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="KND1">KND1</option>
                                        <option value="TTX1">TTX1</option>
                                        <option value="UCO2">UCO2</option>
                                        <option value="LCO1">LCO1</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <button type="button" onclick="generateRSBForm()" style="padding: 10px; background: linear-gradient(135deg, #333 0%, #555 100%); color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                            Generate RSB Form →
                        </button>
                    </form>
                </div>

                <!-- ATS Template Card -->
                <div style="background: #f0f4ff; border-radius: 12px; padding: 20px; border: 2px solid #ddd;">
                    <h3 style="color: #1e40af; margin-bottom: 10px;">⚡ ATS - Automatic Transfer Switch</h3>
                    <p style="color: #666; font-size: 13px; margin-bottom: 15px;">
                        Transfer switch commissioning forms with 81,000+ production uses
                    </p>
                    <form id="atsTemplateForm" style="display: flex; flex-direction: column; gap: 12px;">
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 13px;">Level</label>
                            <select id="atsLevel" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                                <option value="L4">L4 - Commissioning</option>
                                <option value="L3">L3 - Combined BMS</option>
                                <option value="L2C">L2C - Pre-Energization</option>
                                <option value="L2">L2 - Site Arrival</option>
                            </select>
                        </div>
                        <div id="atsL4Options">
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 13px;">Category</label>
                            <select id="atsCategory" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                                <option value="NATs_Busway">NATs & Busway (81,123 uses)</option>
                                <option value="FCA">FCA - Fire Control Area (15,073 uses)</option>
                                <option value="MSG">MSG - Medium Switchgear (7,662 uses)</option>
                                <option value="HMD">HMD - Harmonic Mitigation (3,035 uses)</option>
                                <option value="mCUP">mCUP - Modular Critical Power (1,788 uses)</option>
                                <option value="House">House ATS (1,367 uses)</option>
                                <option value="FirePump">Fire Pump ATS (1,297 uses)</option>
                                <option value="House_Gen">House with Generator (536 uses)</option>
                                <option value="CDU">CDU - Coolant Distribution (182 uses)</option>
                            </select>
                        </div>
                        <div id="atsL3Options" style="display: none;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Area</label>
                                    <select id="atsArea" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="ERA">ERA</option>
                                        <option value="ERB">ERB</option>
                                        <option value="ERC">ERC</option>
                                        <option value="ERD">ERD</option>
                                        <option value="UPSA1">UPSA1</option>
                                        <option value="UPSB1">UPSB1</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Identifier</label>
                                    <select id="atsIdentifier" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="FCA-1">FCA-1</option>
                                        <option value="FCA-2">FCA-2</option>
                                        <option value="FCA-3">FCA-3</option>
                                        <option value="CDU-1">CDU-1</option>
                                        <option value="H1">H1</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-weight: 500; color: #555; margin-bottom: 4px; font-size: 12px;">Variant</label>
                                    <select id="atsVariant" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;">
                                        <option value="KND1">KND1</option>
                                        <option value="TTX1">TTX1</option>
                                        <option value="UCO1">UCO1</option>
                                        <option value="RMN1">RMN1</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <button type="button" onclick="generateATSForm()" style="padding: 10px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                            Generate ATS Form →
                        </button>
                    </form>
                </div>
            </div>

            <p style="margin-top: 15px; font-size: 12px; color: #888; text-align: center;">
                Templates are based on production data from the idc_acc_form_responses_datamart Hive table
            </p>
        </div>

        <!-- Integrated Testing Form Section -->
        <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e5e7eb;">
            <h2 style="color: #333; margin-bottom: 8px;">🔗 Integrated Testing Form</h2>
            <p style="color: #666; margin-bottom: 20px; font-size: 14px;">
                Combine multiple SOO documents and Points Lists to generate a complete, unified testing form for an entire system or project.
            </p>

            <form method="POST" action="/generate-integrated" enctype="multipart/form-data" id="integratedForm">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <!-- Multiple SOO PDFs -->
                    <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; border: 2px solid #e5e7eb;">
                        <h3 style="color: #333; margin-bottom: 15px; font-size: 16px;">📄 SOO Documents <span style="color: red;">*</span></h3>
                        <p style="color: #666; font-size: 12px; margin-bottom: 15px;">
                            Select SOO PDFs (CRAH, IWM, FCU, AHU, etc.) - use as many slots as needed
                        </p>
                        <div style="display: flex; flex-direction: column; gap: 10px;">
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">SOO #1:</span>
                                <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">SOO #2:</span>
                                <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">SOO #3:</span>
                                <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">SOO #4:</span>
                                <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">SOO #5:</span>
                                <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                        </div>
                    </div>

                    <!-- Multiple Points Lists -->
                    <div style="background: #f0f4ff; border-radius: 12px; padding: 20px; border: 2px solid #ddd;">
                        <h3 style="color: #1e40af; margin-bottom: 15px; font-size: 16px;">📊 Points Lists <span class="optional-badge">Optional</span></h3>
                        <p style="color: #666; font-size: 12px; margin-bottom: 15px;">
                            Add points lists to enrich forms with BMS point names
                        </p>
                        <div style="display: flex; flex-direction: column; gap: 10px;">
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">Pts #1:</span>
                                <input type="file" name="points_files" accept=".csv,.tsv,.txt,.xlsx"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">Pts #2:</span>
                                <input type="file" name="points_files" accept=".csv,.tsv,.txt,.xlsx"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #666; font-size: 12px; width: 60px;">Pts #3:</span>
                                <input type="file" name="points_files" accept=".csv,.tsv,.txt,.xlsx"
                                       style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Project Settings -->
                <div style="background: #fefce8; border-radius: 12px; padding: 20px; border: 2px solid #fde047; margin-bottom: 20px;">
                    <h3 style="color: #854d0e; margin-bottom: 15px; font-size: 16px;">⚙️ Project Settings</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 5px; font-size: 13px;">Project Number</label>
                            <input type="text" name="project_number" placeholder="e.g., KND1-2"
                                   style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 5px; font-size: 13px;">Building/Area</label>
                            <input type="text" name="building_area" placeholder="e.g., Data Hall A"
                                   style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
                        </div>
                        <div>
                            <label style="display: block; font-weight: 500; color: #555; margin-bottom: 5px; font-size: 13px;">Output Format</label>
                            <select name="output_format" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
                                <option value="combined">Combined Single Form</option>
                                <option value="separate">Separate Forms per SOO</option>
                                <option value="both">Both Combined & Separate</option>
                            </select>
                        </div>
                    </div>
                </div>

                <button type="submit" id="integratedSubmitBtn" style="width: 100%; padding: 16px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;">
                    🔗 Generate Integrated Testing Form
                </button>
            </form>

            <div style="margin-top: 15px; padding: 15px; background: #fffbeb; border-radius: 8px; font-size: 13px; color: #92400e;">
                <strong>💡 Tip:</strong> Just fill in the SOO slots you need - empty slots will be ignored. The tool will automatically detect document types (CRAH, IWM, etc.) and combine them.
            </div>
        </div>

        <!-- Progress Overlay -->
        <div class="progress-overlay" id="progressOverlay">
            <div class="progress-modal">
                <div class="progress-title">🔧 Generating Forms</div>
                <div class="progress-subtitle">Processing your SOO document...</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <div class="progress-percent" id="progressPercent">0%</div>
                <div class="progress-time" id="progressTime">Elapsed: 0s</div>
                <div class="progress-status" id="progressStatus">Initializing...</div>
            </div>
        </div>

        <div class="info-box">
            <h4>Supported Formats</h4>
            <ul>
                <li><strong>SOO Document:</strong> PDF, Markdown (.md), or plain text (.txt)</li>
                <li><strong>Points List:</strong> CSV or TSV with columns for Point Name, Type, Description, Units, Range</li>
            </ul>
            <p style="margin-top: 10px; font-size: 12px;"><em>{pdf_status}</em></p>
        </div>
    </div>

    <script>
        function setupDropZone(dropZoneId, inputId, filenameId) {
            const dropZone = document.getElementById(dropZoneId);
            const input = document.getElementById(inputId);
            const filenameEl = document.getElementById(filenameId);

            if (!dropZone || !input || !filenameEl) {
                console.error('Drop zone elements not found:', dropZoneId, inputId, filenameId);
                return;
            }

            // Drag and drop support
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            });

            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            });

            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    updateFilename();
                }
            });

            // File input change event - this is the key one!
            input.addEventListener('change', function(e) {
                console.log('File selected:', inputId, this.files[0]?.name);
                updateFilename();
            });

            function updateFilename() {
                if (input.files && input.files.length > 0) {
                    const fileName = input.files[0].name;
                    filenameEl.textContent = '\u2713 ' + fileName;
                    filenameEl.style.color = '#22c55e';
                    filenameEl.style.fontWeight = 'bold';
                    dropZone.classList.add('has-file');
                    console.log('Filename updated:', fileName);
                } else {
                    filenameEl.textContent = '';
                    dropZone.classList.remove('has-file');
                }
            }
        }

        // Initialize drop zones immediately (elements exist before script runs)
        setupDropZone('sooDropZone', 'sooFile', 'sooFilename');
        setupDropZone('pointsDropZone', 'pointsFile', 'pointsFilename');
        setupDropZone('exampleDropZone', 'exampleFile', 'exampleFilename');
        console.log('Drop zones initialized');

        // AI checkbox toggle info box
        const aiCheckbox = document.getElementById('useAiCheckbox');
        const aiInfoBox = document.getElementById('aiInfoBox');
        aiCheckbox.addEventListener('change', () => {
            aiInfoBox.style.display = aiCheckbox.checked ? 'block' : 'none';
        });

        // Load learned examples stats
        async function loadExamplesStats() {
            try {
                const response = await fetch('/api/examples/stats');
                const data = await response.json();

                const statsDiv = document.getElementById('learnedExamplesStats');
                const contentDiv = document.getElementById('examplesContent');

                if (data.total_examples > 0) {
                    statsDiv.style.display = 'block';

                    let systemTags = '';
                    for (const [sys, count] of Object.entries(data.by_system || {})) {
                        systemTags += `<span style="background: #dcfce7; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px;">${sys}: ${count}</span>`;
                    }

                    let sourceTags = '';
                    for (const [src, count] of Object.entries(data.by_source || {})) {
                        sourceTags += `<span style="background: #dbeafe; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px;">${src}: ${count}</span>`;
                    }

                    contentDiv.innerHTML = `
                        <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                            <div><strong>${data.total_examples}</strong> example forms</div>
                            <div><strong>${data.total_items_learned}</strong> check items learned</div>
                        </div>
                        <div style="margin-bottom: 8px;"><strong>By System:</strong> ${systemTags || 'None'}</div>
                        <div><strong>By Source:</strong> ${sourceTags || 'None'}</div>
                    `;
                }
            } catch (error) {
                console.log('No examples data yet');
            }
        }
        loadExamplesStats();

        // Handle example form upload
        document.getElementById('exampleForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            // Debug logging
            console.log('Form submit triggered');

            const fileInput = document.getElementById('exampleFile');
            const sourceInput = document.querySelector('input[name="source"]');

            console.log('File selected:', fileInput.files.length > 0 ? fileInput.files[0].name : 'NONE');
            console.log('Source value:', sourceInput.value);

            if (!fileInput.files.length) {
                alert('Please select an Excel or CSV file first');
                return;
            }

            if (!sourceInput.value.trim()) {
                alert('Please enter a Source/Company name');
                return;
            }

            const formData = new FormData(this);

            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading & Learning...';

            try {
                console.log('Sending fetch request...');
                const response = await fetch('/upload-example', {
                    method: 'POST',
                    body: formData
                });

                console.log('Response status:', response.status);
                const result = await response.json();
                console.log('Response data:', result);

                if (result.success) {
                    let message = `Successfully learned from "${result.filename}"\n\n`;
                    message += `Extracted:\n`;
                    message += `- ${result.items_learned} check items\n`;
                    message += `- ${result.sections_learned} sections\n`;

                    if (result.equipment_type) {
                        message += `\nDetected Equipment:\n`;
                        message += `- Type: ${result.equipment_type}\n`;
                        if (result.level) message += `- Level: ${result.level}\n`;
                        if (result.variant) message += `- Variant: ${result.variant}\n`;
                    }

                    if (result.section_names && result.section_names.length > 0) {
                        message += `\nSections Found:\n`;
                        message += result.section_names.slice(0, 5).map(s => `- ${s}`).join('\n');
                    }

                    alert(message);
                    this.reset();
                    document.getElementById('exampleFilename').textContent = '';
                    document.getElementById('exampleDropZone').classList.remove('has-file');
                    loadExamplesStats();
                } else {
                    alert('Failed to process example: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Upload failed: ' + error.message + '\n\nCheck browser console (F12) for details.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Upload & Learn from Example';
            }
        });

        // Progress tracking
        const form = document.getElementById('uploadForm');
        const progressOverlay = document.getElementById('progressOverlay');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressTime = document.getElementById('progressTime');
        const progressStatus = document.getElementById('progressStatus');

        let startTime;
        let progressInterval;
        let currentProgress = 0;

        const statusMessages = [
            'Initializing...',
            'Reading document...',
            'Parsing systems and equipment...',
            'Extracting setpoints and parameters...',
            'Generating PFI forms...',
            'Generating FPT forms...',
            'Generating IST forms...',
            'Generating CXC forms...',
            'Rendering HTML output...',
            'Finalizing...'
        ];

        function formatTime(seconds) {
            if (seconds < 60) return seconds + 's';
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return mins + 'm ' + secs + 's';
        }

        function updateProgress() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            progressTime.textContent = 'Elapsed: ' + formatTime(elapsed);

            // Simulate progress (actual progress is indeterminate)
            if (currentProgress < 90) {
                currentProgress += Math.random() * 3;
                if (currentProgress > 90) currentProgress = 90;
                progressBar.style.width = currentProgress + '%';
                progressPercent.textContent = Math.floor(currentProgress) + '%';
            }

            // Update status message based on progress
            const statusIndex = Math.min(Math.floor(currentProgress / 10), statusMessages.length - 1);
            progressStatus.textContent = statusMessages[statusIndex];
        }

        form.addEventListener('submit', function(e) {
            // Show progress overlay
            progressOverlay.classList.add('active');
            startTime = Date.now();
            currentProgress = 0;
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';

            // Start progress updates
            progressInterval = setInterval(updateProgress, 200);

            // Store start time for results page
            sessionStorage.setItem('formGenStartTime', startTime);
        });

        // RSB/ATS Template Level Toggle
        document.getElementById('rsbLevel').addEventListener('change', function() {
            const l4Options = document.getElementById('rsbL4Options');
            const l3Options = document.getElementById('rsbL3Options');
            if (this.value === 'L3') {
                l4Options.style.display = 'none';
                l3Options.style.display = 'block';
            } else {
                l4Options.style.display = 'block';
                l3Options.style.display = 'none';
            }
        });

        document.getElementById('atsLevel').addEventListener('change', function() {
            const l4Options = document.getElementById('atsL4Options');
            const l3Options = document.getElementById('atsL3Options');
            if (this.value === 'L3') {
                l4Options.style.display = 'none';
                l3Options.style.display = 'block';
            } else if (this.value === 'L4') {
                l4Options.style.display = 'block';
                l3Options.style.display = 'none';
            } else {
                // L2 or L2C - hide both
                l4Options.style.display = 'none';
                l3Options.style.display = 'none';
            }
        });

        // Generate RSB Form
        function generateRSBForm() {
            const level = document.getElementById('rsbLevel').value;
            let url = '/api/rsb/generate?format=html&level=' + level;

            if (level === 'L4') {
                const formType = document.getElementById('rsbFormType').value;
                url += '&form_type=' + formType;
            } else {
                const area = document.getElementById('rsbArea').value;
                const number = document.getElementById('rsbNumber').value;
                const variant = document.getElementById('rsbVariant').value;
                url += '&area=' + area + '&number=' + number + '&variant=' + variant;
            }

            window.open(url, '_blank');
        }

        // Generate ATS Form
        function generateATSForm() {
            const level = document.getElementById('atsLevel').value;
            let url = '/api/ats/generate?format=html&level=' + level;

            if (level === 'L4') {
                const category = document.getElementById('atsCategory').value;
                url += '&category=' + category;
            } else if (level === 'L3') {
                const area = document.getElementById('atsArea').value;
                const identifier = document.getElementById('atsIdentifier').value;
                const variant = document.getElementById('atsVariant').value;
                url += '&area=' + area + '&identifier=' + identifier + '&variant=' + variant;
            }
            // L2 and L2C don't need additional params

            window.open(url, '_blank');
        }

        // Multi-file display update function
        function updateMultiFileDisplay(inputId, displayId) {
            const input = document.getElementById(inputId);
            const display = document.getElementById(displayId);
            const dropZone = input.parentElement;

            if (input.files && input.files.length > 0) {
                let fileNames = [];
                for (let i = 0; i < input.files.length; i++) {
                    fileNames.push('✓ ' + input.files[i].name);
                }
                display.innerHTML = fileNames.join('<br>');
                display.style.color = '#22c55e';
                display.style.fontWeight = 'bold';
                dropZone.classList.add('has-file');
                console.log('Files selected:', input.files.length, fileNames);
            } else {
                display.textContent = '';
                dropZone.classList.remove('has-file');
            }
        }

        // Add more SOO file inputs
        let sooFileCount = 1;
        function addSooFile() {
            sooFileCount++;
            const container = document.getElementById('sooFilesList');
            const newEntry = document.createElement('div');
            newEntry.className = 'soo-file-entry';
            newEntry.style.marginBottom = '10px';
            newEntry.innerHTML = `
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                           style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                    <span style="color: #666; font-size: 12px;">SOO #${sooFileCount}</span>
                    <button type="button" onclick="this.parentElement.parentElement.remove()"
                            style="padding: 4px 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">✕</button>
                </div>
            `;
            container.appendChild(newEntry);
        }

        // Add more Points file inputs
        let pointsFileCount = 1;
        function addPointsFile() {
            pointsFileCount++;
            const container = document.getElementById('pointsFilesList');
            const newEntry = document.createElement('div');
            newEntry.className = 'points-file-entry';
            newEntry.style.marginBottom = '10px';
            newEntry.innerHTML = `
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="file" name="points_files" accept=".csv,.tsv,.txt,.xlsx"
                           style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                    <span style="color: #666; font-size: 12px;">Points #${pointsFileCount}</span>
                    <button type="button" onclick="this.parentElement.parentElement.remove()"
                            style="padding: 4px 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">✕</button>
                </div>
            `;
            container.appendChild(newEntry);
        }

        // Handle integrated form submission
        document.getElementById('integratedForm').addEventListener('submit', function(e) {
            const sooInputs = document.querySelectorAll('input[name="soo_files"]');
            let hasFile = false;
            sooInputs.forEach(input => {
                if (input.files && input.files.length > 0) hasFile = true;
            });

            if (!hasFile) {
                e.preventDefault();
                alert('Please select at least one SOO document');
                return;
            }

            // Show progress overlay
            progressOverlay.classList.add('active');
            document.querySelector('.progress-title').textContent = '🔗 Generating Integrated Form';
            document.querySelector('.progress-subtitle').textContent = 'Processing SOO documents...';
            startTime = Date.now();
            currentProgress = 0;
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            progressInterval = setInterval(updateProgress, 200);
            sessionStorage.setItem('formGenStartTime', startTime);
        });
    </script>
</body>
</html>"""


PAGE_RESULTS = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated ITC Forms</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 40px 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            margin-bottom: 8px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px 30px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            flex: 1;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
            margin-top: 4px;
        }
        .actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: white;
            color: #333;
            border: 2px solid #ddd;
        }
        .system-card {
            background: white;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .system-header {
            background: #333;
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
        }
        .form-list {
            padding: 15px 20px;
        }
        .form-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .form-item:last-child {
            border-bottom: none;
        }
        .form-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .form-type-badge {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-pfi { background: #dbeafe; color: #1e40af; }
        .badge-fpt { background: #dcfce7; color: #166534; }
        .badge-ist { background: #fef3c7; color: #92400e; }
        .badge-cxc { background: #f3e8ff; color: #7c3aed; }
        .badge-itc { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .ai-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            margin-left: 12px;
        }
        .ai-indicator.ai-on {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .ai-indicator.ai-off {
            background: #e5e7eb;
            color: #6b7280;
        }
        .ai-detail {
            background: white;
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .ai-detail.ai-detail-off {
            border-color: #d1d5db;
        }
        .ai-detail-icon {
            font-size: 28px;
        }
        .ai-detail-text {
            flex: 1;
        }
        .ai-detail-text strong {
            display: block;
            font-size: 15px;
            color: #333;
        }
        .ai-detail-text span {
            font-size: 13px;
            color: #666;
        }
        .form-name {
            font-weight: 500;
        }
        .form-count {
            color: #666;
            font-size: 13px;
        }
        .form-actions a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
        }
        .form-actions a:hover {
            text-decoration: underline;
        }
        .points-info {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 30px;
        }
        .points-info h3 {
            color: #166534;
            margin-bottom: 8px;
        }
        /* Feedback Section Styles */
        .feedback-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .feedback-section h3 {
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .feedback-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .feedback-type-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .feedback-type-btn {
            padding: 10px 20px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        .feedback-type-btn:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .feedback-type-btn.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }
        .feedback-type-btn.positive.selected { background: #22c55e; border-color: #22c55e; }
        .feedback-type-btn.negative.selected { background: #ef4444; border-color: #ef4444; }
        .feedback-type-btn.suggestion.selected { background: #3b82f6; border-color: #3b82f6; }
        .feedback-type-btn.correction.selected { background: #f59e0b; border-color: #f59e0b; }
        .feedback-textarea {
            width: 100%;
            min-height: 100px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
        }
        .feedback-textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .feedback-row {
            display: flex;
            gap: 15px;
        }
        .feedback-row > * {
            flex: 1;
        }
        .feedback-select, .feedback-input {
            padding: 10px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            width: 100%;
        }
        .feedback-select:focus, .feedback-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .feedback-submit-btn {
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            align-self: flex-start;
        }
        .feedback-submit-btn:hover {
            transform: translateY(-2px);
        }
        .feedback-submit-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .feedback-success {
            background: #f0fdf4;
            border: 1px solid #22c55e;
            color: #166534;
            padding: 12px 20px;
            border-radius: 8px;
            display: none;
        }
        .feedback-success.show {
            display: block;
        }
        .feedback-label {
            font-weight: 500;
            color: #555;
            margin-bottom: 5px;
            display: block;
        }
        /* Learning Dashboard Styles */
        .learning-stats {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .learning-progress {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .progress-label {
            font-weight: 600;
            color: #333;
        }
        .progress-value {
            font-weight: bold;
            color: #667eea;
        }
        .progress-bar-bg {
            background: #e5e7eb;
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        .progress-message {
            margin-top: 10px;
            color: #666;
            font-size: 13px;
        }
        .stats-grid {
            display: flex;
            gap: 15px;
        }
        .stat-mini {
            flex: 1;
            background: #f0f4ff;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-mini-value {
            display: block;
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-mini-label {
            font-size: 12px;
            color: #666;
        }
        .feedback-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }
        .feedback-tag {
            background: #e5e7eb;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 12px;
            color: #555;
        }
        .recent-feedback {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }
        .recent-feedback ul {
            margin: 10px 0 0 20px;
            font-size: 13px;
            color: #555;
        }
        .recent-feedback li {
            margin-bottom: 8px;
        }
        .ai-context-details {
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }
        .ai-context-details summary {
            padding: 12px 15px;
            background: #334155;
            color: white;
            cursor: pointer;
            font-weight: 500;
        }
        .ai-context-details summary:hover {
            background: #475569;
        }
        .ai-context-code {
            padding: 15px;
            margin: 0;
            color: #10b981;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .ai-context-note {
            padding: 12px 15px;
            margin: 0;
            background: #0f172a;
            color: #94a3b8;
            font-size: 12px;
            border-top: 1px solid #334155;
        }
        .ai-context-empty {
            background: #fef3c7;
            padding: 12px 15px;
            border-radius: 8px;
            color: #92400e;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Forms Generated Successfully <span class="{ai_indicator_class}">{ai_indicator_icon} {ai_indicator_text}</span></h1>
        <p class="subtitle">{project_name}</p>

        <div class="{ai_detail_class}">
            <div class="ai-detail-icon">{ai_detail_icon}</div>
            <div class="ai-detail-text">
                <strong>{ai_detail_title}</strong>
                <span>{ai_detail_description}</span>
            </div>
        </div>

        {points_info}

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{system_count}</div>
                <div class="stat-label">Systems</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{form_count}</div>
                <div class="stat-label">Forms</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{item_count}</div>
                <div class="stat-label">Check Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{elapsed_time}</div>
                <div class="stat-label">Generation Time</div>
            </div>
        </div>

        <div class="actions">
            <a href="/download-zip?session={session_id}" class="btn btn-primary">
                📦 Download All (HTML ZIP)
            </a>
            <a href="/download-csv?session={session_id}" class="btn btn-primary" style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);">
                📊 Download CSV
            </a>
            <a href="/download-excel?session={session_id}" class="btn btn-primary" style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);">
                📈 Download Excel
            </a>
            <a href="/" class="btn btn-secondary">
                &larr; Generate More Forms
            </a>
        </div>

        {systems_html}

        <!-- Feedback Learning Dashboard -->
        <div class="feedback-section" style="margin-bottom: 20px;">
            <h3>🧠 AI Learning Progress</h3>
            <div id="learningDashboard">
                <p style="color: #666;">Loading feedback data...</p>
            </div>
        </div>

        <!-- Feedback Section -->
        <div class="feedback-section">
            <h3>💬 Help Us Improve</h3>
            <p style="color: #666; margin-bottom: 20px;">
                Your feedback helps the AI generate better forms. Tell us what worked well or what could be improved.
            </p>

            <div class="feedback-success" id="feedbackSuccess">
                ✅ Thank you! Your feedback has been saved and will help improve future form generation.
            </div>

            <form class="feedback-form" id="feedbackForm">
                <input type="hidden" name="session_id" value="{session_id}">

                <div>
                    <label class="feedback-label">What type of feedback?</label>
                    <div class="feedback-type-buttons">
                        <button type="button" class="feedback-type-btn positive" data-type="positive">👍 Works Well</button>
                        <button type="button" class="feedback-type-btn negative" data-type="negative">👎 Needs Improvement</button>
                        <button type="button" class="feedback-type-btn suggestion" data-type="suggestion">💡 Suggestion</button>
                        <button type="button" class="feedback-type-btn correction" data-type="correction">✏️ Correction</button>
                    </div>
                </div>

                <div class="feedback-row">
                    <div>
                        <label class="feedback-label">System Type</label>
                        <select class="feedback-select" name="system_type" id="systemType">
                            <option value="">Select system type...</option>
                            {system_options}
                        </select>
                    </div>
                    <div>
                        <label class="feedback-label">Section (optional)</label>
                        <select class="feedback-select" name="section_name" id="sectionName">
                            <option value="">All sections / General</option>
                            <option value="Safety">Safety</option>
                            <option value="Installation">Installation</option>
                            <option value="Electrical">Electrical</option>
                            <option value="Controls">Controls</option>
                            <option value="Setpoints">Setpoint Verification</option>
                            <option value="Functional Tests">Functional Tests</option>
                            <option value="Interlocks">Interlock Testing</option>
                            <option value="Alarms">Alarm Testing</option>
                            <option value="Documentation">Documentation</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="feedback-label">Your Feedback</label>
                    <textarea class="feedback-textarea" name="feedback_text" id="feedbackText"
                              placeholder="Tell us what you liked, what needs improvement, or suggest specific check items that should be added..."></textarea>
                </div>

                <div>
                    <label class="feedback-label">Suggested Improvement (optional)</label>
                    <input type="text" class="feedback-input" name="suggested_improvement" id="suggestedImprovement"
                           placeholder="e.g., Add check item for refrigerant leak detection">
                </div>

                <button type="submit" class="feedback-submit-btn" id="submitFeedback">Submit Feedback</button>
            </form>
        </div>
    </div>

    <script>
        // Load and display feedback learning dashboard
        async function loadLearningDashboard() {
            try {
                const response = await fetch('/api/feedback/stats');
                const data = await response.json();

                const dashboard = document.getElementById('learningDashboard');

                const progressBarColor = data.learning_status.level === 'trained' ? '#22c55e' :
                                         data.learning_status.level === 'improving' ? '#3b82f6' : '#f59e0b';

                let systemsHtml = '';
                for (const [system, count] of Object.entries(data.by_system || {})) {
                    systemsHtml += `<span class="feedback-tag">${system}: ${count}</span>`;
                }

                let typesHtml = '';
                const typeEmoji = { positive: '👍', negative: '👎', suggestion: '💡', correction: '✏️' };
                for (const [type, count] of Object.entries(data.by_type || {})) {
                    typesHtml += `<span class="feedback-tag">${typeEmoji[type] || '📝'} ${type}: ${count}</span>`;
                }

                let recentHtml = '';
                if (data.recent_feedback && data.recent_feedback.length > 0) {
                    recentHtml = '<div class="recent-feedback"><strong>Recent Feedback:</strong><ul>';
                    for (const fb of data.recent_feedback.slice(0, 5)) {
                        const emoji = typeEmoji[fb.feedback_type] || '📝';
                        recentHtml += `<li>${emoji} <strong>[${fb.system_type}]</strong> ${fb.feedback_text}</li>`;
                    }
                    recentHtml += '</ul></div>';
                }

                dashboard.innerHTML = `
                    <div class="learning-stats">
                        <div class="learning-progress">
                            <div class="progress-header">
                                <span class="progress-label">Learning Progress</span>
                                <span class="progress-value">${data.learning_status.progress}%</span>
                            </div>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: ${data.learning_status.progress}%; background: ${progressBarColor};"></div>
                            </div>
                            <p class="progress-message">${data.learning_status.message}</p>
                        </div>

                        <div class="stats-grid">
                            <div class="stat-mini">
                                <span class="stat-mini-value">${data.total_feedback}</span>
                                <span class="stat-mini-label">Total Feedback</span>
                            </div>
                            <div class="stat-mini">
                                <span class="stat-mini-value">${data.recent_count}</span>
                                <span class="stat-mini-label">This Week</span>
                            </div>
                            <div class="stat-mini">
                                <span class="stat-mini-value">${Object.keys(data.by_system || {}).length}</span>
                                <span class="stat-mini-label">Systems Learned</span>
                            </div>
                        </div>

                        ${systemsHtml ? `<div class="feedback-tags"><strong>By System:</strong> ${systemsHtml}</div>` : ''}
                        ${typesHtml ? `<div class="feedback-tags"><strong>By Type:</strong> ${typesHtml}</div>` : ''}
                        ${recentHtml}

                        <div class="ai-context-preview" id="aiContextPreview"></div>
                    </div>
                `;

                // Load AI context for the first system
                if (Object.keys(data.by_system || {}).length > 0) {
                    const firstSystem = Object.keys(data.by_system)[0];
                    loadAIContext(firstSystem);
                }

            } catch (error) {
                console.error('Failed to load learning dashboard:', error);
                document.getElementById('learningDashboard').innerHTML =
                    '<p style="color: #666;">No feedback data yet. Submit feedback below to start improving AI generation!</p>';
            }
        }

        async function loadAIContext(systemType) {
            try {
                const response = await fetch(`/api/feedback/context?system_type=${encodeURIComponent(systemType)}`);
                const data = await response.json();

                const preview = document.getElementById('aiContextPreview');
                if (!preview) return;

                if (data.ai_context && data.ai_context.trim()) {
                    preview.innerHTML = `
                        <details class="ai-context-details">
                            <summary>🤖 AI Context for ${systemType} (Click to expand)</summary>
                            <pre class="ai-context-code">${escapeHtml(data.ai_context)}</pre>
                            <p class="ai-context-note">
                                <strong>This context is added to AI prompts</strong> when generating forms for ${systemType} systems,
                                helping the AI learn from your feedback and produce better check items.
                            </p>
                        </details>
                    `;
                } else {
                    preview.innerHTML = `
                        <p class="ai-context-empty">
                            💡 No feedback yet for ${systemType} systems. Submit feedback to help the AI learn!
                        </p>
                    `;
                }
            } catch (error) {
                console.error('Failed to load AI context:', error);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load dashboard on page load
        loadLearningDashboard();

        // Feedback form handling
        let selectedFeedbackType = '';
        const feedbackForm = document.getElementById('feedbackForm');
        const feedbackSuccess = document.getElementById('feedbackSuccess');
        const typeButtons = document.querySelectorAll('.feedback-type-btn');

        typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                typeButtons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selectedFeedbackType = btn.dataset.type;
            });
        });

        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!selectedFeedbackType) {
                alert('Please select a feedback type');
                return;
            }

            const feedbackText = document.getElementById('feedbackText').value.trim();
            if (!feedbackText) {
                alert('Please enter your feedback');
                return;
            }

            const submitBtn = document.getElementById('submitFeedback');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        feedback_type: selectedFeedbackType,
                        system_type: document.getElementById('systemType').value || 'General',
                        system_name: document.getElementById('systemType').options[document.getElementById('systemType').selectedIndex]?.text || 'General',
                        form_type: 'ITC',
                        section_name: document.getElementById('sectionName').value,
                        feedback_text: feedbackText,
                        suggested_improvement: document.getElementById('suggestedImprovement').value
                    })
                });

                if (response.ok) {
                    feedbackSuccess.classList.add('show');
                    feedbackForm.reset();
                    typeButtons.forEach(b => b.classList.remove('selected'));
                    selectedFeedbackType = '';

                    setTimeout(() => {
                        feedbackSuccess.classList.remove('show');
                    }, 5000);
                } else {
                    throw new Error('Failed to submit feedback');
                }
            } catch (error) {
                alert('Failed to submit feedback. Please try again.');
                console.error(error);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Feedback';
            }
        });
    </script>
</body>
</html>"""


class ITCHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ITC Form Generator."""

    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        print(f"[{self.address_string()}] {args[0]}")

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Health check endpoint for Nest deployment
        if path == '/api/health':
            self._serve_health_check()
        elif path == '/api/feedback/stats':
            self._serve_feedback_stats()
        elif path == '/api/feedback/context':
            self._serve_feedback_context(query)
        elif path == '/api/examples/stats':
            self._serve_examples_stats()
        elif path == '/api/examples/context':
            self._serve_examples_context(query)
        elif path == '/api/rsb/templates':
            self._serve_rsb_templates(query)
        elif path == '/api/rsb/variants':
            self._serve_rsb_variants()
        elif path == '/api/rsb/areas':
            self._serve_rsb_areas()
        elif path == '/api/rsb/generate':
            self._serve_rsb_generate_form(query)
        elif path == '/api/ats/templates':
            self._serve_ats_templates(query)
        elif path == '/api/ats/variants':
            self._serve_ats_variants()
        elif path == '/api/ats/areas':
            self._serve_ats_areas()
        elif path == '/api/ats/categories':
            self._serve_ats_categories()
        elif path == '/api/ats/generate':
            self._serve_ats_generate_form(query)
        elif path == '/':
            self._serve_upload_page()
        elif path.startswith('/preview/'):
            self._serve_preview(path[9:], query)
        elif path.startswith('/download/'):
            self._serve_download(path[10:], query)
        elif path == '/download-zip':
            self._serve_zip(query)
        elif path == '/download-csv':
            self._serve_csv(query)
        elif path == '/download-excel':
            self._serve_excel(query)
        else:
            self._send_error(404, "Page not found")

    def _serve_health_check(self):
        """Serve health check endpoint for Nest/container orchestration."""
        health_data = {
            "status": "healthy",
            "service": APP_NAME,
            "version": APP_VERSION,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checks": {
                "pdf_support": check_pdf_support()[0],
                "excel_support": check_excel_support(),
                "active_sessions": len(SESSIONS)
            }
        }
        response = json.dumps(health_data, indent=2)
        encoded = response.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_feedback_stats(self):
        """Serve feedback statistics for the dashboard."""
        try:
            store = get_feedback_store()
            stats = store.get_stats()

            # Get recent feedback entries for display
            recent = store.get_all_feedback(limit=10)
            recent_list = []
            for entry in recent:
                recent_list.append({
                    'id': entry.id,
                    'timestamp': entry.timestamp,
                    'system_type': entry.system_type,
                    'feedback_type': entry.feedback_type,
                    'feedback_text': entry.feedback_text[:100] + '...' if len(entry.feedback_text) > 100 else entry.feedback_text,
                    'section_name': entry.section_name,
                    'suggested_improvement': entry.suggested_improvement
                })

            response_data = {
                'total_feedback': stats['total_entries'],
                'by_type': stats['by_type'],
                'by_system': stats['by_system'],
                'recent_count': stats['recent_count'],
                'recent_feedback': recent_list,
                'learning_status': self._get_learning_status(stats)
            }

            response = json.dumps(response_data, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        except Exception as e:
            self._send_error(500, f"Failed to get feedback stats: {str(e)}")

    def _serve_feedback_context(self, query):
        """Show the AI context generated from feedback for a system type."""
        try:
            system_type = query.get('system_type', ['General'])[0]

            store = get_feedback_store()
            context = store.generate_ai_context(system_type, system_type)

            positive = store.get_positive_patterns(system_type)
            negative = store.get_negative_patterns(system_type)
            suggestions = store.get_improvement_suggestions(system_type)

            response_data = {
                'system_type': system_type,
                'ai_context': context,
                'patterns': {
                    'positive': positive,
                    'negative': negative,
                    'suggestions': suggestions
                },
                'context_length': len(context),
                'will_improve_generation': len(context) > 0
            }

            response = json.dumps(response_data, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        except Exception as e:
            self._send_error(500, f"Failed to get feedback context: {str(e)}")

    def _serve_rsb_templates(self, query):
        """Serve available RSB template information."""
        try:
            from itc_form_generator.rsb_templates import get_template_summary

            summary = get_template_summary()

            response = json.dumps(summary, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"RSB templates not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get RSB templates: {str(e)}")

    def _serve_rsb_variants(self):
        """Serve available RSB equipment variants."""
        try:
            from itc_form_generator.rsb_templates import RSB_VARIANTS

            response = json.dumps(RSB_VARIANTS, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"RSB variants not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get RSB variants: {str(e)}")

    def _serve_rsb_areas(self):
        """Serve available RSB area codes."""
        try:
            from itc_form_generator.rsb_templates import AREA_CODES

            response = json.dumps(AREA_CODES, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"RSB areas not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get RSB areas: {str(e)}")

    def _serve_rsb_generate_form(self, query):
        """Generate an RSB form based on query parameters.

        Query parameters:
            level: L3 or L4
            form_type: BMS, FPT, CEV, Cable, LCO3
            area: ERA, ERB, ERC, ERD, DHA, etc.
            number: 01-40, R1, R2
            variant: KND1, TTX1, UCO2, etc.
            format: json (default) or html
        """
        try:
            from itc_form_generator.rsb_templates import (
                RSBTemplateFactory,
                convert_template_to_form_sections,
                get_rsb_l4_fpt_template,
                get_rsb_l4_cev_template,
                get_rsb_l4_cable_template,
                get_rsb_l4_lco3_template,
            )

            level = query.get('level', ['L3'])[0]
            form_type = query.get('form_type', ['BMS'])[0]
            area = query.get('area', ['ERA'])[0]
            number = query.get('number', ['01'])[0]
            variant = query.get('variant', ['KND1'])[0]
            output_format = query.get('format', ['json'])[0]

            if level == 'L4':
                template_funcs = {
                    'FPT': get_rsb_l4_fpt_template,
                    'CEV': get_rsb_l4_cev_template,
                    'Cable': get_rsb_l4_cable_template,
                    'LCO3': get_rsb_l4_lco3_template,
                }
                template = template_funcs.get(form_type, get_rsb_l4_fpt_template)()
            else:
                template = RSBTemplateFactory.create_l3_template(area, number, variant)

            sections = convert_template_to_form_sections(template)

            response_data = {
                'template_id': template.template_id,
                'display_name': template.display_name,
                'level': template.level,
                'equipment_type': template.equipment_type,
                'variant': template.variant,
                'frequency': template.frequency,
                'sections': sections,
            }

            if output_format == 'html':
                html_content = self._generate_rsb_html_form(response_data)
                encoded = html_content.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(encoded))
                self.end_headers()
                self.wfile.write(encoded)
            else:
                response = json.dumps(response_data, indent=2)
                encoded = response.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(encoded))
                self.end_headers()
                self.wfile.write(encoded)

        except ImportError as e:
            self._send_error(500, f"RSB templates not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to generate RSB form: {str(e)}")

    def _generate_rsb_html_form(self, form_data):
        """Generate HTML representation of RSB form."""
        sections_html = []
        for section in form_data.get('sections', []):
            items_html = []
            for item in section.get('items', []):
                response_type = item.get('response_type', 'choice')
                presets = item.get('presets', '')

                if response_type == 'toggle' and presets:
                    input_html = f'''
                        <select class="form-control">
                            <option value="">-- Select --</option>
                            {''.join(f'<option value="{opt}">{opt}</option>' for opt in presets.split('/'))}
                        </select>
                    '''
                elif response_type == 'text':
                    input_html = '<input type="text" class="form-control" placeholder="Enter text...">'
                elif response_type == 'number':
                    input_html = '<input type="number" class="form-control" placeholder="Enter value...">'
                elif response_type == 'date':
                    input_html = '<input type="date" class="form-control">'
                else:
                    input_html = '''
                        <select class="form-control">
                            <option value="">-- Select --</option>
                            <option value="Pass">Pass</option>
                            <option value="Fail">Fail</option>
                            <option value="NA">N/A</option>
                        </select>
                    '''

                items_html.append(f'''
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{html.escape(item.get('description', ''))}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; width: 150px;">{input_html}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; width: 200px;">
                            <input type="text" class="form-control" placeholder="Comments...">
                        </td>
                    </tr>
                ''')

            sections_html.append(f'''
                <div class="section" style="margin-bottom: 30px;">
                    <h3 style="background: #333; color: white; padding: 12px 15px; margin: 0; border-radius: 8px 8px 0 0;">
                        {html.escape(section.get('display_name', section.get('name', '')))}
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; background: white; border: 1px solid #ddd; border-radius: 0 0 8px 8px;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Check Item</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 150px;">Response</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 200px;">Comments</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(items_html)}
                        </tbody>
                    </table>
                </div>
            ''')

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(form_data.get('display_name', 'RSB Form'))}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            margin-bottom: 5px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        .form-control {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .form-header {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}
        .header-field label {{
            display: block;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="no-print" style="margin-bottom: 20px;">
            <a href="/" style="color: #667eea;">← Back to Generator</a>
        </div>

        <h1>{html.escape(form_data.get('display_name', 'RSB Form'))}</h1>
        <p class="subtitle">
            Level: {html.escape(form_data.get('level', ''))} |
            Equipment: {html.escape(form_data.get('equipment_type', ''))} |
            Variant: {html.escape(form_data.get('variant', ''))} |
            Template ID: {html.escape(form_data.get('template_id', ''))}
        </p>

        <div class="form-header">
            <div class="header-grid">
                <div class="header-field">
                    <label>Equipment Designation:</label>
                    <input type="text" class="form-control" placeholder="Enter equipment tag...">
                </div>
                <div class="header-field">
                    <label>Inspector Name:</label>
                    <input type="text" class="form-control" placeholder="Enter name...">
                </div>
                <div class="header-field">
                    <label>Date:</label>
                    <input type="date" class="form-control">
                </div>
            </div>
        </div>

        {''.join(sections_html)}

        <div class="form-header no-print">
            <button onclick="window.print()" style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
                🖨️ Print Form
            </button>
</button>
        </div>
    </div>
</body>
</html>'''

    def _serve_ats_templates(self, query):
        """Serve available ATS template information."""
        try:
            from itc_form_generator.ats_templates import get_template_summary

            summary = get_template_summary()

            response = json.dumps(summary, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"ATS templates not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get ATS templates: {str(e)}")

    def _serve_ats_variants(self):
        """Serve available ATS equipment variants."""
        try:
            from itc_form_generator.ats_templates import ATS_VARIANTS

            response = json.dumps(ATS_VARIANTS, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"ATS variants not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get ATS variants: {str(e)}")

    def _serve_ats_areas(self):
        """Serve available ATS area codes."""
        try:
            from itc_form_generator.ats_templates import ATS_AREA_CODES

            response = json.dumps(ATS_AREA_CODES, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"ATS areas not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get ATS areas: {str(e)}")

    def _serve_ats_categories(self):
        """Serve available ATS categories."""
        try:
            from itc_form_generator.ats_templates import ATS_CATEGORIES

            response = json.dumps(ATS_CATEGORIES, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        except ImportError as e:
            self._send_error(500, f"ATS categories not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to get ATS categories: {str(e)}")

    def _serve_ats_generate_form(self, query):
        """Generate an ATS form based on query parameters.

        Query parameters:
            level: L2, L2C, L3, L4, or L4C
            category: FCA, House, MSG, HMD, mCUP, etc. (for L4)
            area: ERA, ERB, ERC, ERD, etc. (for L3)
            identifier: FCA-1, CDU-3, H1, etc. (for L3)
            variant: KND1, TTX1, UCO1, etc. (for L3)
            format: json (default) or html
        """
        try:
            from itc_form_generator.ats_templates import (
                ATSTemplateFactory,
                convert_template_to_form_sections,
            )

            level = query.get('level', ['L4'])[0]
            category = query.get('category', ['FCA'])[0]
            area = query.get('area', ['ERA'])[0]
            identifier = query.get('identifier', ['FCA-1'])[0]
            variant = query.get('variant', ['KND1'])[0]
            output_format = query.get('format', ['json'])[0]

            if level == 'L3':
                template = ATSTemplateFactory.create_l3_template(area, identifier, variant)
            elif level == 'L2C':
                template = ATSTemplateFactory.create_l2c_template()
            elif level == 'L2':
                template = ATSTemplateFactory.create_site_arrival_template()
            else:
                template = ATSTemplateFactory.create_l4_template(category)

            sections = convert_template_to_form_sections(template)

            response_data = {
                'template_id': template.template_id,
                'display_name': template.display_name,
                'level': template.level,
                'equipment_type': template.equipment_type,
                'category': template.category,
                'variant': template.variant,
                'frequency': template.frequency,
                'sections': sections,
            }

            if output_format == 'html':
                html_content = self._generate_ats_html_form(response_data)
                encoded = html_content.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(encoded))
                self.end_headers()
                self.wfile.write(encoded)
            else:
                response = json.dumps(response_data, indent=2)
                encoded = response.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(encoded))
                self.end_headers()
                self.wfile.write(encoded)

        except ImportError as e:
            self._send_error(500, f"ATS templates not available: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Failed to generate ATS form: {str(e)}")

    def _generate_ats_html_form(self, form_data):
        """Generate HTML representation of ATS form."""
        sections_html = []
        for section in form_data.get('sections', []):
            items_html = []
            for item in section.get('items', []):
                response_type = item.get('response_type', 'choice')
                presets = item.get('presets', '')

                if response_type == 'toggle' and presets:
                    input_html = f'''
                        <select class="form-control">
                            <option value="">-- Select --</option>
                            {''.join(f'<option value="{opt}">{opt}</option>' for opt in presets.split('/'))}
                        </select>
                    '''
                elif response_type == 'text':
                    input_html = '<input type="text" class="form-control" placeholder="Enter text...">'
                elif response_type == 'number':
                    input_html = '<input type="number" class="form-control" placeholder="Enter value...">'
                elif response_type == 'date':
                    input_html = '<input type="date" class="form-control">'
                else:
                    input_html = '''
                        <select class="form-control">
                            <option value="">-- Select --</option>
                            <option value="Pass">Pass</option>
                            <option value="Fail">Fail</option>
                            <option value="NA">N/A</option>
                        </select>
                    '''

                items_html.append(f'''
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{html.escape(item.get('description', ''))}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; width: 150px;">{input_html}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; width: 200px;">
                            <input type="text" class="form-control" placeholder="Comments...">
                        </td>
                    </tr>
                ''')

            sections_html.append(f'''
                <div class="section" style="margin-bottom: 30px;">
                    <h3 style="background: #2563eb; color: white; padding: 12px 15px; margin: 0; border-radius: 8px 8px 0 0;">
                        {html.escape(section.get('display_name', section.get('name', '')))}
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; background: white; border: 1px solid #ddd; border-radius: 0 0 8px 8px;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Check Item</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 150px;">Response</th>
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 200px;">Comments</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(items_html)}
                        </tbody>
                    </table>
                </div>
            ''')

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(form_data.get('display_name', 'ATS Form'))}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            color: #1e40af;
            margin-bottom: 5px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        .form-control {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .form-header {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}
        .header-field label {{
            display: block;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="no-print" style="margin-bottom: 20px;">
            <a href="/" style="color: #2563eb;">← Back to Generator</a>
        </div>

        <h1>{html.escape(form_data.get('display_name', 'ATS Form'))}</h1>
        <p class="subtitle">
            Level: {html.escape(form_data.get('level', ''))} |
            Equipment: {html.escape(form_data.get('equipment_type', ''))} |
            Category: {html.escape(form_data.get('category', ''))} |
            Template ID: {html.escape(form_data.get('template_id', ''))}
        </p>

        <div class="form-header">
            <div class="header-grid">
                <div class="header-field">
                    <label>Equipment Designation:</label>
                    <input type="text" class="form-control" placeholder="Enter equipment tag...">
                </div>
                <div class="header-field">
                    <label>Inspector Name:</label>
                    <input type="text" class="form-control" placeholder="Enter name...">
                </div>
                <div class="header-field">
                    <label>Date:</label>
                    <input type="date" class="form-control">
                </div>
            </div>
        </div>

        {''.join(sections_html)}

        <div class="form-header no-print">
            <button onclick="window.print()" style="padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
                🖨️ Print Form
            </button>
        </div>
    </div>
</body>
</html>'''

    def _get_learning_status(self, stats):
        """Generate a learning status message based on feedback count."""
        total = stats['total_entries']
        if total == 0:
            return {
                'level': 'new',
                'message': 'No feedback yet. Submit feedback to help improve form generation!',
                'progress': 0
            }
        elif total < 5:
            return {
                'level': 'learning',
                'message': f'Learning from {total} feedback entries. More feedback helps improve accuracy!',
                'progress': total * 10
            }
        elif total < 15:
            return {
                'level': 'improving',
                'message': f'Good progress! {total} feedback entries are shaping better forms.',
                'progress': min(50 + total * 3, 80)
            }
        else:
            return {
                'level': 'trained',
                'message': f'Well-trained! {total} feedback entries provide strong guidance for form generation.',
                'progress': min(80 + total, 100)
            }

    def _serve_examples_stats(self):
        """Serve statistics about learned example forms."""
        try:
            store = get_example_store()
            stats = store.get_stats()

            examples = store.get_all_examples()
            examples_list = []
            for ex in examples[:10]:
                examples_list.append({
                    'id': ex.id,
                    'filename': ex.filename,
                    'source': ex.source,
                    'system_type': ex.system_type,
                    'form_type': ex.form_type,
                    'total_items': ex.total_items,
                    'sections': len(ex.sections),
                    'key_patterns': ex.key_patterns[:5]
                })

            response_data = {
                'total_examples': stats['total_examples'],
                'total_items_learned': stats['total_items_learned'],
                'by_system': stats['by_system'],
                'by_source': stats['by_source'],
                'key_patterns': stats['key_patterns'],
                'examples': examples_list
            }

            response = json.dumps(response_data, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        except Exception as e:
            self._send_error(500, f"Failed to get examples stats: {str(e)}")

    def _serve_examples_context(self, query):
        """Show the AI context generated from example forms for a system type."""
        try:
            system_type = query.get('system_type', ['General'])[0]

            store = get_example_store()
            context = store.generate_ai_context(system_type)
            examples = store.get_examples_for_system(system_type, limit=5)

            response_data = {
                'system_type': system_type,
                'ai_context': context,
                'example_count': len(examples),
                'examples': [
                    {
                        'source': ex.source,
                        'filename': ex.filename,
                        'total_items': ex.total_items,
                        'sections': [s.name for s in ex.sections[:5]]
                    }
                    for ex in examples
                ],
                'context_length': len(context),
                'will_improve_generation': len(context) > 0
            }

            response = json.dumps(response_data, indent=2)
            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        except Exception as e:
            self._send_error(500, f"Failed to get examples context: {str(e)}")

    def _handle_example_upload(self):
        """Handle example form upload for learning."""
        try:
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_json_error(400, "Invalid content type")
                return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )

            if 'example_file' not in form:
                self._send_json_error(400, "No example file uploaded")
                return

            example_field = form['example_file']
            source = form.getvalue('source', 'Unknown')
            system_type = form.getvalue('system_type', 'General')

            if not hasattr(example_field, 'file') or not example_field.file:
                self._send_json_error(400, "Could not read uploaded file")
                return

            raw_data = example_field.file.read()
            filename = example_field.filename or "unknown.xlsx"

            print(f"[EXAMPLE] Processing example form: {filename} from {source}")

            parser = ExampleFormParser()

            if filename.lower().endswith(('.xlsx', '.xls')):
                if not parser.is_available:
                    self._send_json_error(400, "Excel support not available. Install openpyxl.")
                    return
                example = parser.parse_excel(raw_data, filename, source, system_type)
            elif filename.lower().endswith('.csv'):
                content = raw_data.decode('utf-8', errors='ignore')
                example = parser.parse_csv(content, filename, source, system_type)
            else:
                self._send_json_error(400, "Unsupported file format. Use Excel (.xlsx) or CSV.")
                return

            if not example:
                self._send_json_error(400, "Failed to parse example form. Check file format.")
                return

            # Store the learned example
            store = get_example_store()
            store.add_example(example)

            # Build detailed response with equipment detection info
            section_names = [s.name for s in example.sections]

            print(f"[EXAMPLE] Learned {example.total_items} items, {len(example.sections)} sections")
            if example.equipment_type:
                print(f"[EXAMPLE] Detected equipment type: {example.equipment_type}, Level: {example.level}, Variant: {example.variant}")

            response = json.dumps({
                'success': True,
                'filename': filename,
                'source': source,
                'system_type': example.system_type,  # Use detected type
                'items_learned': example.total_items,
                'sections_learned': len(example.sections),
                'section_names': section_names[:10],
                'equipment_type': example.equipment_type or None,
                'level': example.level or None,
                'variant': example.variant or None,
                'key_patterns': example.key_patterns[:5],
                'message': self._build_learning_message(example)
            })

            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Example upload failed: {error_details}")
            self._send_json_error(500, f"Failed to process example: {str(e)}")

    def _build_learning_message(self, example) -> str:
        """Build a detailed message about what was learned from the form."""
        parts = []

        if example.equipment_type:
            parts.append(f"Detected {example.equipment_type} equipment")
            if example.level:
                parts.append(f"Level: {example.level}")
            if example.variant:
                parts.append(f"Variant: {example.variant}")

        if example.sections:
            section_names = [s.name for s in example.sections[:5]]
            parts.append(f"Sections: {', '.join(section_names)}")

        if example.key_patterns:
            parts.append(f"Patterns: {', '.join(example.key_patterns[:3])}")

        return " | ".join(parts) if parts else "Form patterns learned successfully"

    def _send_json_error(self, code: int, message: str):
        """Send a JSON error response."""
        response = json.dumps({'success': False, 'error': message})
        encoded = response.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/generate':
            self._handle_generate()
        elif self.path == '/generate-integrated':
            self._handle_generate_integrated()
        elif self.path == '/api/feedback':
            self._handle_feedback()
        elif self.path == '/upload-example':
            self._handle_example_upload()
        else:
            self._send_error(404, "Endpoint not found")

    def _handle_feedback(self):
        """Handle feedback submission."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # Create feedback entry
            feedback = create_feedback_entry(
                system_type=data.get('system_type', 'Unknown'),
                system_name=data.get('system_name', 'Unknown'),
                form_type=data.get('form_type', 'ITC'),
                feedback_type=data.get('feedback_type', 'suggestion'),
                feedback_text=data.get('feedback_text', ''),
                section_name=data.get('section_name'),
                check_item_id=data.get('check_item_id'),
                check_item_description=data.get('check_item_description'),
                suggested_improvement=data.get('suggested_improvement'),
                user_id=data.get('user_id')
            )

            # Store feedback
            store = get_feedback_store()
            store.add_feedback(feedback)

            # Return success response
            response = json.dumps({
                'success': True,
                'message': 'Feedback submitted successfully',
                'feedback_id': feedback.id
            })

            encoded = response.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

            print(f"[FEEDBACK] Received {feedback.feedback_type} feedback for {feedback.system_type}")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Feedback submission failed: {error_details}")
            self._send_error(500, f"Failed to submit feedback: {str(e)}")

    def _serve_upload_page(self):
        """Serve the upload page."""
        pdf_available, _ = get_pdf_status()
        pdf_status = "✅ PDF support enabled" if pdf_available else "⚠️ PDF support requires: pip install pymupdf"
        page_html = PAGE_UPLOAD.replace("{pdf_status}", pdf_status)
        self._send_html(page_html)

    def _handle_generate(self):
        """Handle form generation from uploaded files."""
        start_time = time.time()  # Start timing
        try:
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_error(400, "Invalid content type")
                return

            # Read the raw POST data
            content_length = int(self.headers.get('Content-Length', 0))

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )

            # Check if soo_file exists in form
            if 'soo_file' not in form:
                self._send_error(400, "No SOO file uploaded")
                return

            soo_field = form['soo_file']

            # Handle file upload
            if hasattr(soo_field, 'file') and soo_field.file:
                raw_data = soo_field.file.read()
                filename = soo_field.filename.lower() if soo_field.filename else ""

                if not raw_data:
                    self._send_error(400, "Uploaded file is empty")
                    return

                print(f"[DEBUG] Uploaded file: {filename}, size: {len(raw_data)} bytes")
                print(f"[DEBUG] First 20 bytes: {raw_data[:20]}")

                # Check if it's a PDF file
                if filename.endswith('.pdf') or raw_data[:4] == b'%PDF':
                    print("[DEBUG] Detected PDF file, extracting text...")
                    pdf_parser = PDFParser()
                    if not pdf_parser.is_available:
                        self._send_error(400,
                            "PDF support not available. Please install pymupdf:\n"
                            "pip install pymupdf"
                        )
                        return
                    soo_content = pdf_parser.extract_text(raw_data)
                    print(f"[DEBUG] Extracted {len(soo_content)} characters from PDF")
                    print(f"[DEBUG] First 200 chars: {soo_content[:200]}")
                else:
                    soo_content = raw_data.decode('utf-8', errors='ignore')
                    print(f"[DEBUG] Text file, {len(soo_content)} characters")
            elif hasattr(soo_field, 'value') and soo_field.value:
                soo_content = soo_field.value
                if isinstance(soo_content, bytes):
                    soo_content = soo_content.decode('utf-8', errors='ignore')
                print(f"[DEBUG] Got value directly: {len(soo_content)} chars")
            else:
                self._send_error(400, "Could not read uploaded file")
                return

            points_content = None
            if 'points_file' in form and form['points_file'].file:
                points_content = form['points_file'].file.read().decode('utf-8', errors='ignore')

            # Check if AI enhancement is enabled
            use_ai = False
            if 'use_ai' in form:
                ai_field = form['use_ai']
                use_ai = (hasattr(ai_field, 'value') and ai_field.value == 'true') or \
                         (isinstance(ai_field, str) and ai_field == 'true')

            print(f"[DEBUG] AI enhancement enabled: {use_ai}")

            # Detect document type and use specialized parser if available
            doc_type = detect_document_type(soo_content)
            print(f"[DEBUG] Detected document type: {doc_type}")

            forms = []
            soo = None
            points_list = None  # Initialize points_list for all code paths

            if doc_type == 'MUA':
                # Use specialized MUA parser and form generator
                print("[DEBUG] Using MUA-specific parser and form generator")
                mua_system = parse_mua_soo(soo_content)
                print(f"[DEBUG] MUA System: {mua_system.name}")
                print(f"[DEBUG] Components: {len(mua_system.components)}")
                print(f"[DEBUG] Setpoints: {len(mua_system.setpoints)}")
                print(f"[DEBUG] Alerts: {len(mua_system.alerts)}")
                print(f"[DEBUG] Operating Modes: {len(mua_system.operating_modes)}")

                # Generate MUA-specific form
                mua_form = generate_mua_form(mua_system)
                forms = [mua_form]

                # Create a minimal SOO object for compatibility
                from itc_form_generator.models import SequenceOfOperation, System
                soo = SequenceOfOperation(title=mua_system.name)
                soo.systems.append(System(
                    name=mua_system.name,
                    tag=mua_system.tag,
                    description=mua_system.description
                ))
            elif doc_type == 'CRAH':
                # Use specialized CRAH parser and form generator
                print("[DEBUG] Using CRAH-specific parser and form generator")
                from itc_form_generator.crah_form_generator import (
                    parse_crah_soo, generate_crah_forms_from_soo
                )
                crah_system = parse_crah_soo(soo_content)
                print(f"[DEBUG] CRAH System: {crah_system.name}")
                print(f"[DEBUG] Setpoints: {len(crah_system.setpoints)}")
                print(f"[DEBUG] Alerts: {len(crah_system.alerts)}")
                print(f"[DEBUG] Failure Modes: {len(crah_system.failure_modes)}")
                print(f"[DEBUG] Equipment: {len(crah_system.equipment)}")

                # Generate CRAH-specific forms
                forms = generate_crah_forms_from_soo(soo_content)

                # Create a minimal SOO object for compatibility
                from itc_form_generator.models import SequenceOfOperation, System
                soo = SequenceOfOperation(title=crah_system.name)
                soo.systems.append(System(
                    name=crah_system.name,
                    tag=crah_system.tag,
                    description=crah_system.description
                ))
            elif doc_type == 'IWM':
                # Use specialized IWM parser and form generator
                print("[DEBUG] Using IWM-specific parser and form generator")
                from itc_form_generator.iwm_form_generator import (
                    parse_iwm_soo, generate_iwm_forms_from_soo
                )
                iwm_system = parse_iwm_soo(soo_content)
                print(f"[DEBUG] IWM System: {iwm_system.name}")
                print(f"[DEBUG] Sensors: {len(iwm_system.sensors)}")
                print(f"[DEBUG] Equipment: {len(iwm_system.equipment)}")
                print(f"[DEBUG] Setpoints: {len(iwm_system.setpoints)}")
                print(f"[DEBUG] Failure Modes: {len(iwm_system.failure_modes)}")

                # Generate IWM-specific forms
                forms = generate_iwm_forms_from_soo(soo_content)

                # Create a minimal SOO object for compatibility
                from itc_form_generator.models import SequenceOfOperation, System
                soo = SequenceOfOperation(title=iwm_system.name)
                soo.systems.append(System(
                    name=iwm_system.name,
                    tag=iwm_system.tag,
                    description=iwm_system.description
                ))
            else:
                # Use generic parser
                parser = SOOParser(use_ai=use_ai)
                soo = parser.parse(soo_content)

                if points_content:
                    points_parser = PointsListParser()
                    points_list = points_parser.parse(points_content)

                generator = FormGenerator(soo, points_list, use_ai=use_ai)
                forms = generator.generate_all_forms()

            # Debug logging
            print(f"[DEBUG] SOO Title: {soo.title}")
            print(f"[DEBUG] Systems found: {len(soo.systems)}")
            for s in soo.systems:
                print(f"[DEBUG]   - {s.name} ({s.tag})")
            print(f"[DEBUG] Forms generated: {len(forms)}")

            renderer = HTMLRenderer()

            session_id = str(uuid.uuid4())[:8]
            session_data = {
                'forms': {},
                'forms_list': forms,  # Store the forms list directly
                'project': soo.title,
                'points_count': len(points_list.points) if points_list else 0,
            }

            for form in forms:
                filename = renderer._form_filename(form)
                html_content = renderer.render_form(form)
                session_data['forms'][filename] = {
                    'content': html_content,
                    'form': form,
                }

            index_html = renderer.render_index(forms, soo.title)
            session_data['forms']['index.html'] = {
                'content': index_html,
                'form': None,
            }

            SESSIONS[session_id] = session_data

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            self._serve_results(session_id, forms, soo.title, points_list, elapsed_time)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] {error_details}")
            self._send_error(500, f"Error processing files: {str(e)}\n\nDetails:\n{error_details}")

    def _handle_generate_integrated(self):
        """Handle integrated form generation from multiple SOO files."""
        start_time = time.time()
        try:
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_error(400, "Invalid content type")
                return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )

            # Get project settings
            project_number = form.getvalue('project_number', '')
            building_area = form.getvalue('building_area', '')
            output_format = form.getvalue('output_format', 'combined')

            print(f"[INTEGRATED] Starting integrated form generation")
            print(f"[INTEGRATED] Project: {project_number}, Building: {building_area}, Format: {output_format}")
            print(f"[INTEGRATED] Form keys: {list(form.keys())}")

            # Process multiple SOO files - handle both single and multiple file inputs
            soo_files = []
            if 'soo_files' in form:
                soo_field = form['soo_files']
                # Check if it's a list (multiple files) or single file
                if isinstance(soo_field, list):
                    soo_files = soo_field
                    print(f"[INTEGRATED] Got list of {len(soo_files)} SOO files")
                else:
                    # Single file
                    soo_files = [soo_field]
                    print(f"[INTEGRATED] Got single SOO file")

            if not soo_files:
                self._send_error(400, "No SOO files uploaded")
                return

            print(f"[INTEGRATED] Processing {len(soo_files)} SOO file(s)")

            # Process each SOO file
            all_forms = []
            detected_types = []
            pdf_parser = PDFParser()

            for soo_field in soo_files:
                if not hasattr(soo_field, 'file') or not soo_field.file:
                    continue

                raw_data = soo_field.file.read()
                filename = soo_field.filename.lower() if soo_field.filename else ""

                if not raw_data:
                    continue

                print(f"[INTEGRATED] Processing: {soo_field.filename}")

                # Extract text from file
                if filename.endswith('.pdf') or raw_data[:4] == b'%PDF':
                    if not pdf_parser.is_available:
                        continue
                    soo_content = pdf_parser.extract_text(raw_data)
                else:
                    soo_content = raw_data.decode('utf-8', errors='ignore')

                # Detect document type and generate forms
                doc_type = detect_document_type(soo_content)
                detected_types.append(doc_type)
                print(f"[INTEGRATED] Detected type: {doc_type}")

                forms = []
                if doc_type == 'CRAH':
                    from itc_form_generator.crah_form_generator import generate_crah_forms_from_soo
                    forms = generate_crah_forms_from_soo(soo_content, project_number)
                elif doc_type == 'IWM':
                    from itc_form_generator.iwm_form_generator import generate_iwm_forms_from_soo
                    forms = generate_iwm_forms_from_soo(soo_content, project_number)
                elif doc_type == 'MUA':
                    mua_system = parse_mua_soo(soo_content)
                    mua_form = generate_mua_form(mua_system)
                    forms = [mua_form]
                else:
                    # Generic parser
                    parser = SOOParser()
                    soo = parser.parse(soo_content)
                    generator = FormGenerator(soo, None)
                    forms = generator.generate_all_forms()

                all_forms.extend(forms)
                print(f"[INTEGRATED] Generated {len(forms)} form(s) from {soo_field.filename}")

            # Process points lists if provided
            points_files = form.getlist('points_files') if hasattr(form, 'getlist') else []
            if not points_files and 'points_files' in form:
                pf = form['points_files']
                if isinstance(pf, list):
                    points_files = pf
                else:
                    points_files = [pf] if hasattr(pf, 'file') else []

            points_content = ""
            for points_field in points_files:
                if hasattr(points_field, 'file') and points_field.file:
                    content = points_field.file.read().decode('utf-8', errors='ignore')
                    points_content += content + "\n"
                    print(f"[INTEGRATED] Added points list: {points_field.filename}")

            # Create combined form if requested
            if output_format in ('combined', 'both') and len(all_forms) > 1:
                combined_form = self._combine_forms(all_forms, project_number, building_area, detected_types)
                if output_format == 'combined':
                    all_forms = [combined_form]
                else:
                    all_forms.insert(0, combined_form)

            print(f"[INTEGRATED] Total forms to render: {len(all_forms)}")

            # Create session and render
            renderer = HTMLRenderer()
            session_id = str(uuid.uuid4())[:8]

            # Create project title
            project_title = f"Integrated Testing Form"
            if project_number:
                project_title = f"{project_number} - {project_title}"
            if building_area:
                project_title += f" - {building_area}"

            session_data = {
                'forms': {},
                'forms_list': all_forms,
                'project': project_title,
                'points_count': len(points_content.split('\n')) if points_content else 0,
            }

            for form in all_forms:
                filename = renderer._form_filename(form)
                html_content = renderer.render_form(form)
                session_data['forms'][filename] = {
                    'content': html_content,
                    'form': form,
                }

            # Create SOO object for compatibility
            from itc_form_generator.models import SequenceOfOperation, System
            soo = SequenceOfOperation(title=project_title)
            for form in all_forms:
                soo.systems.append(System(
                    name=form.system,
                    tag=form.system_tag,
                    description=""
                ))

            index_html = renderer.render_index(all_forms, project_title)
            session_data['forms']['index.html'] = {
                'content': index_html,
                'form': None,
            }

            SESSIONS[session_id] = session_data

            elapsed_time = time.time() - start_time
            self._serve_results(session_id, all_forms, project_title, None, elapsed_time)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Integrated generation failed: {error_details}")
            self._send_error(500, f"Error processing files: {str(e)}\n\nDetails:\n{error_details}")

    def _combine_forms(self, forms: list, project_number: str, building_area: str, detected_types: list):
        """Combine multiple forms into a single integrated testing form."""
        from itc_form_generator.models import InspectionForm, FormSection, CheckItem, FormType, CheckItemType, Priority

        # Create combined form
        title = "Integrated Functional Performance Test"
        if project_number:
            title = f"{project_number} - {title}"
        if building_area:
            title += f" - {building_area}"

        combined_form = InspectionForm(
            form_type=FormType.FPT,
            system="Integrated Systems",
            system_tag="INT",
            title=title
        )

        # Add a summary section
        summary_section = FormSection(
            title="Integrated Test Summary",
            description="Overview of all systems covered in this integrated test"
        )

        summary_section.check_items.append(CheckItem(
            id="INT-001",
            description=f"Systems Covered: {', '.join(set(detected_types))}",
            check_type=CheckItemType.DOCUMENTATION,
            priority=Priority.HIGH
        ))
        summary_section.check_items.append(CheckItem(
            id="INT-002",
            description=f"Total Equipment Forms: {len(forms)}",
            check_type=CheckItemType.DOCUMENTATION,
            priority=Priority.MEDIUM
        ))
        summary_section.check_items.append(CheckItem(
            id="INT-003",
            description="Project Number",
            check_type=CheckItemType.DOCUMENTATION,
            priority=Priority.HIGH,
            expected_value=project_number or "Enter Project Number"
        ))
        summary_section.check_items.append(CheckItem(
            id="INT-004",
            description="Building/Area",
            check_type=CheckItemType.DOCUMENTATION,
            priority=Priority.HIGH,
            expected_value=building_area or "Enter Building/Area"
        ))

        combined_form.sections.append(summary_section)

        # Add sections from each form
        for form in forms:
            # Add a separator section for each system
            separator = FormSection(
                title=f"=== {form.system} ({form.system_tag}) ===",
                description=f"Sections from {form.title}"
            )
            separator.check_items.append(CheckItem(
                id=f"{form.system_tag}-SEP",
                description=f"Begin {form.system} Testing",
                check_type=CheckItemType.DOCUMENTATION,
                priority=Priority.MEDIUM
            ))
            combined_form.sections.append(separator)

            # Add all sections from this form
            for section in form.sections:
                # Prefix section title with system tag
                new_section = FormSection(
                    title=f"[{form.system_tag}] {section.title}",
                    description=section.description
                )
                for item in section.check_items:
                    # Create new item with prefixed ID
                    new_item = CheckItem(
                        id=f"{form.system_tag}-{item.id}",
                        description=item.description,
                        check_type=item.check_type,
                        priority=item.priority,
                        acceptance_criteria=item.acceptance_criteria,
                        expected_value=item.expected_value
                    )
                    new_section.check_items.append(new_item)

                if new_section.check_items:
                    combined_form.sections.append(new_section)

        print(f"[INTEGRATED] Combined form has {len(combined_form.sections)} sections, {combined_form.total_items} items")
        return combined_form

    def _serve_results(self, session_id, forms, project_name, points_list, elapsed_time=0):
        """Serve the results page."""
        forms_by_system = {}
        for form in forms:
            key = (form.system, form.system_tag)
            if key not in forms_by_system:
                forms_by_system[key] = []
            forms_by_system[key].append(form)

        renderer = HTMLRenderer()

        systems_html = ""
        system_options = ""  # For feedback form dropdown
        for (system_name, system_tag), system_forms in forms_by_system.items():
            # Add to system options for feedback form
            system_type = self._extract_system_type(system_name, system_tag)
            system_options += f'<option value="{html.escape(system_type)}">{html.escape(system_name)}</option>\n'

            form_items = ""
            for form in system_forms:
                filename = renderer._form_filename(form)
                badge_class = f"badge-{form.form_type.name.lower()}"
                form_items += f"""
                <div class="form-item">
                    <div class="form-info">
                        <span class="form-type-badge {badge_class}">{form.form_type.name}</span>
                        <span class="form-name">{form.form_type.value}</span>
                        <span class="form-count">{form.total_items} items</span>
                    </div>
                    <div class="form-actions">
                        <a href="/preview/{filename}?session={session_id}" target="_blank">Preview</a>
                        &nbsp;|&nbsp;
                        <a href="/download/{filename}?session={session_id}">Download</a>
                    </div>
                </div>"""

            systems_html += f"""
            <div class="system-card">
                <div class="system-header">{system_name} ({system_tag})</div>
                <div class="form-list">
                    {form_items}
                </div>
            </div>"""

        points_info = ""
        if points_list and points_list.points:
            points_info = f"""
            <div class="points-info">
                <h3>📊 Points List Loaded</h3>
                <p>{len(points_list.points)} control points imported
                   (AI: {len(points_list.ai_points)},
                    AO: {len(points_list.ao_points)},
                    DI: {len(points_list.di_points)},
                    DO: {len(points_list.do_points)})</p>
            </div>"""

        total_items = sum(f.total_items for f in forms)

        # Format elapsed time
        if elapsed_time < 1:
            elapsed_str = f"{elapsed_time*1000:.0f}ms"
        elif elapsed_time < 60:
            elapsed_str = f"{elapsed_time:.1f}s"
        else:
            mins = int(elapsed_time // 60)
            secs = elapsed_time % 60
            elapsed_str = f"{mins}m {secs:.0f}s"

        # Determine AI status for display
        ai_was_used = getattr(soo, '_ai_enhanced', False) if hasattr(soo, '_ai_enhanced') else use_ai
        ai_backend_name = ""
        try:
            if use_ai and hasattr(parser, 'ai_service') and parser.ai_service:
                ai_svc = parser.ai_service
                if hasattr(ai_svc, 'backend') and ai_svc.backend:
                    ai_backend_name = ai_svc.backend.name
                    ai_was_used = True
                else:
                    ai_was_used = False
        except Exception:
            ai_was_used = False

        if ai_was_used:
            ai_indicator_class = "ai-indicator ai-on"
            ai_indicator_icon = "🤖"
            ai_indicator_text = "AI Enhanced"
            ai_detail_class = "ai-detail"
            ai_detail_icon = "🤖"
            ai_detail_title = f"AI-Enhanced Parsing ({ai_backend_name or 'Active'})"
            ai_detail_description = "This output was generated using AI for improved accuracy. Components, setpoints, and modes were extracted using LLM analysis."
        else:
            ai_indicator_class = "ai-indicator ai-off"
            ai_indicator_icon = "📋"
            ai_indicator_text = "Regex Only"
            ai_detail_class = "ai-detail ai-detail-off"
            ai_detail_icon = "📋"
            ai_detail_title = "Standard Parsing (Regex Only)"
            ai_detail_description = "Enable AI Enhancement for more thorough extraction. Set ITC_AI_BACKEND and check the AI checkbox."

        result_html = PAGE_RESULTS.replace(
            "{project_name}", html.escape(project_name)
        ).replace(
            "{session_id}", session_id
        ).replace(
            "{system_count}", str(len(forms_by_system))
        ).replace(
            "{form_count}", str(len(forms))
        ).replace(
            "{item_count}", str(total_items)
        ).replace(
            "{elapsed_time}", elapsed_str
        ).replace(
            "{systems_html}", systems_html
        ).replace(
            "{points_info}", points_info
        ).replace(
            "{system_options}", system_options
        ).replace(
            "{ai_indicator_class}", ai_indicator_class
        ).replace(
            "{ai_indicator_icon}", ai_indicator_icon
        ).replace(
            "{ai_indicator_text}", ai_indicator_text
        ).replace(
            "{ai_detail_class}", ai_detail_class
        ).replace(
            "{ai_detail_icon}", ai_detail_icon
        ).replace(
            "{ai_detail_title}", ai_detail_title
        ).replace(
            "{ai_detail_description}", ai_detail_description
        )

        self._send_html(result_html)

    def _extract_system_type(self, system_name: str, system_tag: str) -> str:
        """Extract system type from name/tag for feedback categorization."""
        name_lower = system_name.lower()
        tag_upper = system_tag.upper() if system_tag else ""

        # Common HVAC system type mappings
        type_keywords = {
            'AHU': ['ahu', 'air handling', 'air handler'],
            'FCU': ['fcu', 'fan coil'],
            'VAV': ['vav', 'variable air volume'],
            'Chiller': ['chiller', 'ch-', 'chlr'],
            'Boiler': ['boiler', 'blr'],
            'Cooling Tower': ['cooling tower', 'ct-'],
            'Pump': ['pump', 'pmp'],
            'RTU': ['rtu', 'rooftop'],
            'CRAH': ['crah', 'computer room'],
            'CRAC': ['crac'],
            'Data Hall': ['data hall', 'dh-'],
            'UPS': ['ups'],
            'PDU': ['pdu'],
            'Generator': ['generator', 'gen-'],
        }

        for sys_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in name_lower or kw.upper() in tag_upper:
                    return sys_type

        # Default to tag prefix or generic
        if tag_upper:
            return tag_upper.split('-')[0] if '-' in tag_upper else tag_upper[:3]
        return 'General'

    def _serve_preview(self, filename, query):
        """Serve a form preview."""
        session_id = query.get('session', [''])[0]
        if session_id not in SESSIONS:
            self._send_error(404, "Session not found")
            return

        session = SESSIONS[session_id]
        if filename not in session['forms']:
            self._send_error(404, "Form not found")
            return

        content = session['forms'][filename]['content']
        self._send_html(content)

    def _serve_download(self, filename, query):
        """Serve a form for download."""
        session_id = query.get('session', [''])[0]
        if session_id not in SESSIONS:
            self._send_error(404, "Session not found")
            return

        session = SESSIONS[session_id]
        if filename not in session['forms']:
            self._send_error(404, "Form not found")
            return

        content = session['forms'][filename]['content']

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', len(content.encode('utf-8')))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _serve_zip(self, query):
        """Serve all forms as a ZIP file."""
        session_id = query.get('session', [''])[0]
        if session_id not in SESSIONS:
            self._send_error(404, "Session not found")
            return

        session = SESSIONS[session_id]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, data in session['forms'].items():
                zf.writestr(filename, data['content'].encode('utf-8'))

        zip_data = zip_buffer.getvalue()
        zip_filename = f"ITC_Forms_{session_id}.zip"

        self.send_response(200)
        self.send_header('Content-Type', 'application/zip')
        self.send_header('Content-Disposition', f'attachment; filename="{zip_filename}"')
        self.send_header('Content-Length', len(zip_data))
        self.end_headers()
        self.wfile.write(zip_data)

    def _serve_csv(self, query):
        """Serve all forms as a CSV file."""
        session_id = query.get('session', [''])[0]
        if session_id not in SESSIONS:
            self._send_error(404, "Session not found")
            return

        session = SESSIONS[session_id]

        # Get all forms from session - try forms_list first, then fall back to extracting from forms dict
        forms = session.get('forms_list', [])
        if not forms:
            forms = [data['form'] for data in session['forms'].values() if data.get('form')]

        # Debug: print what we found
        print(f"[DEBUG] Session {session_id}: forms_list has {len(session.get('forms_list', []))} forms")
        print(f"[DEBUG] Session {session_id}: forms dict has {len(session['forms'])} entries")
        print(f"[DEBUG] Final forms count: {len(forms)}")

        if not forms:
            self._send_error(404, f"No forms found in session.")
            return

        # Export to CSV
        exporter = FormExporter()
        csv_content = exporter.export_all_to_csv(forms)

        csv_filename = f"ITC_Forms_{session_id}.csv"
        encoded = csv_content.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{csv_filename}"')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_excel(self, query):
        """Serve all forms as an Excel file."""
        session_id = query.get('session', [''])[0]
        if session_id not in SESSIONS:
            self._send_error(404, "Session not found")
            return

        session = SESSIONS[session_id]

        # Get all forms from session - try forms_list first, then fall back to extracting from forms dict
        forms = session.get('forms_list', [])
        if not forms:
            forms = [data['form'] for data in session['forms'].values() if data.get('form')]

        if not forms:
            self._send_error(404, "No forms found")
            return

        # Export to Excel
        exporter = FormExporter()
        excel_data = exporter.export_to_excel(forms)

        if excel_data is None:
            self._send_error(500, "Excel export not available. Install openpyxl: pip install openpyxl")
            return

        excel_filename = f"ITC_Forms_{session_id}.xlsx"

        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.send_header('Content-Disposition', f'attachment; filename="{excel_filename}"')
        self.send_header('Content-Length', len(excel_data))
        self.end_headers()
        self.wfile.write(excel_data)

    def _send_html(self, content):
        """Send HTML response."""
        encoded = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, code, message):
        """Send error response."""
        content = f"""<!DOCTYPE html>
<html>
<head><title>Error {code}</title></head>
<body style="font-family: Arial; padding: 40px; text-align: center;">
    <h1>Error {code}</h1>
    <p>{html.escape(message)}</p>
    <a href="/">← Back to Home</a>
</body>
</html>"""
        encoded = content.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)


def main():
    """Run the web server."""
    # Allow command line port override, otherwise use PORT env var
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT

    # Use IPv6 hostname for Nest compatibility (accepts both IPv4 and IPv6)
    server_address = (HOSTNAME, port)
    httpd = HTTPServer(server_address, ITCHandler)

    # Detect if running in Nest/container environment
    is_nest = os.environ.get('PORT') is not None or os.environ.get('NEST_APP_NAME') is not None

    if is_nest:
        print(f"""
+--------------------------------------------------------------+
|                    ITC Form Generator                        |
|                  (Nest Deployment Mode)                      |
+--------------------------------------------------------------+
|  Service: {APP_NAME}
|  Version: {APP_VERSION}
|  Port: {port}
|  Health: /api/health
+--------------------------------------------------------------+
""")
    else:
        print(f"""
+--------------------------------------------------------------+
|                    ITC Form Generator                        |
|                     Web Application                          |
+--------------------------------------------------------------+
|                                                              |
|  Server running at: http://localhost:{port:<5}                 |
|                                                              |
|  Open the URL above in your browser to start generating      |
|  inspection and testing forms.                               |
|                                                              |
|  Press Ctrl+C to stop the server.                            |
|                                                              |
+--------------------------------------------------------------+
""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == '__main__':
    main()

