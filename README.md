# ITC Form Generator 🏗️

AI-powered form generator for Data Center Engineering operations. Parses Sequence of Operations (SOO) documents and Points Lists to auto-generate commissioning forms.

## Features
- 📄 **SOO Document Parsing** — Extracts systems, components, setpoints, operating modes, interlocks, and alarms
- 📊 **Points List Processing** — Reads CSV/Excel BMS points lists with fuzzy column matching
- 🤖 **AI Enhancement** — Optional LLM-powered extraction (OpenAI, Anthropic, Ollama, or MetaGen)
- 📋 **Form Generation** — Creates equipment-specific commissioning forms (CRAH, MUA, IWM, ATS)
- 📥 **Export** — Download forms as PDF, Excel, or JSON

## Quick Start (Local)
```bash
pip install -r requirements.txt
python wsgi.py
```
Open http://localhost:8080

## Deploy to Render.com (Free)

### Step 1: Create GitHub Repository
1. Go to https://github.com/new → Name: `itc-form-generator`, Private
2. Download this folder as ZIP from Google Drive
3. In GitHub repo click "uploading an existing file" → drag all files → Commit

### Step 2: Deploy on Render
1. Go to https://render.com → sign up (free) → New → Web Service
2. Connect GitHub → select `itc-form-generator`
3. Render auto-detects render.yaml → click Deploy

### Step 3: Configure AI (Optional)
In Render dashboard → Environment → Add: `OPENAI_API_KEY` = `sk-your-key`

Your app will be live at: `https://itc-form-generator.onrender.com`

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | production | Flask environment |
| SECRET_KEY | auto-generated | Session encryption key |
| USE_AI | true | Enable AI enhancement option |
| AI_BACKEND | openai | AI backend (openai/anthropic/ollama/metagen) |
| OPENAI_API_KEY | — | OpenAI API key (required for AI mode) |
| PORT | 8080 | Server port |

## Supported Formats
- **SOO Documents**: Markdown (.md), Text (.txt), PDF (.pdf)
- **Points Lists**: CSV (.csv), Excel (.xlsx)
- **Equipment Types**: AHU, CRAH, MUA, IWM, ATS, and generic

