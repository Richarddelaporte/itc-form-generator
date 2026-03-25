# ITC Form Generator v2.0.0 — Integration Guide

## How to Set Up the New Architecture

### Step 1: Organize Your Project Directory

```
itc_form_generator/          # Your project root
├── app.py                   # ← flask_app.py (rename)
├── config.py                # ← flask_config.py (rename)
├── wsgi.py                  # ← flask_wsgi.py (rename)
├── cli.py                   # NEW: CLI entry point
├── build.py                 # NEW: Build automation
├── __main__.py              # ← __main___v2.py (rename, put in itc_form_generator/)
├── pyproject.toml           # ← pyproject_v2.toml (rename, replaces old one)
├── requirements.txt         # ← requirements_v2.txt (rename)
├── Dockerfile               # ← Dockerfile_v2 (rename)
├── docker-compose.yml       # ← docker-compose_v2.txt (rename to .yml)
├── gunicorn.conf.py         # NEW
├── ITC_Form_Generator.spec  # ← ITC_Form_Generator_v2.spec (rename)
├── routes/                  # NEW directory
│   ├── __init__.py          # Create empty file
│   ├── main.py              # ← routes_main.py
│   ├── api.py               # ← routes_api.py
│   ├── export.py            # ← routes_export.py
│   ├── feedback.py          # ← routes_feedback.py
│   └── templates_api.py     # ← routes_templates_api.py
├── templates/               # NEW directory
│   ├── base.html            # ← template_base.html
│   ├── index.html           # ← template_index.html
│   ├── results.html         # ← template_results.html
│   └── error.html           # ← template_error.html
├── static/                  # NEW directory
│   ├── css/
│   │   └── style.css        # ← static_style.css
│   └── js/
│       └── app.js           # ← static_app.js
├── tests/                   # NEW directory
│   ├── test_app.py          # ← test_flask_app.py
│   └── test_parsers.py      # ← test_parsers.py
└── itc_form_generator/      # Core package (existing)
    ├── __init__.py           # ← __init___v2.py (rename, replaces old one)
    ├── ai_service.py         # ← ai_service_v2.py (rename, replaces old one)
    ├── parser.py             # ← parser_v2.py (rename, replaces old one)
    ├── points_parser.py      # ← points_parser_v2.py (rename, replaces old one)
    ├── form_generator.py     # (keep existing)
    ├── models.py             # (keep existing)
    ├── exporter.py           # (keep existing)
    ├── renderer.py           # (keep existing)
    └── ... (other existing files)
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\\Scripts\\activate  # Windows

# Install all dependencies
pip install -e ".[all,dev]"
```

### Step 3: Run the Application

```bash
# Development mode (auto-opens browser)
python cli.py serve

# Or using the package entry point
itc-form-generator serve --port 8080

# Batch generation from command line
itc-form-generator generate my_soo.md --points points.csv --output ./forms/
```

### Step 4: Run Tests

```bash
pytest tests/ -v
```

### Step 5: Build for Distribution

```bash
# Build pip package
python build.py pip

# Build standalone executable
python build.py exe

# Build Docker image
python build.py docker

# Build everything
python build.py all
```

### Step 6: Deploy as Webapp

```bash
# Option A: Docker (simplest)
docker-compose up -d
# App available at http://localhost:8080

# Option B: Direct deployment
gunicorn wsgi:app --config gunicorn.conf.py
```

## AI Backend Configuration

Set environment variables to configure the AI backend:

```bash
# Meta internal (default)
export AI_BACKEND=metagen

# OpenAI
export AI_BACKEND=openai
export OPENAI_API_KEY=sk-...

# Anthropic  
export AI_BACKEND=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Local Ollama (no API key needed)
export AI_BACKEND=ollama
export OLLAMA_HOST=http://localhost:11434

# Disable AI entirely (regex-only parsing)
export USE_AI=false
```

## What Changed (Summary)

| Component | Before (v1) | After (v2) |
|-----------|-------------|------------|
| Web server | Raw HTTPServer (1 file, 157KB) | Flask with blueprints (8 files) |
| Templates | Inline HTML strings | Jinja2 templates (4 files) |
| CSS/JS | Inline in Python | Separate static files |
| AI service | MetaGen only | Multi-backend (MetaGen/OpenAI/Anthropic/Ollama) |
| SOO parser | Regex only | Hybrid: regex + AI multi-pass |
| Points parser | CSV only, hardcoded columns | CSV/Excel, fuzzy matching, AI mapping |
| CLI | None | Full CLI (serve + batch generate) |
| Packaging | Basic PyInstaller | pip + PyInstaller + Docker |
| Testing | Minimal | Comprehensive pytest suite |

