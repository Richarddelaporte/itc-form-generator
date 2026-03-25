# 🚀 ITC Form Generator - NEST Deployment Guide

This guide walks you through deploying the ITC Form Generator to NEST with MetaGen AI support.

## Prerequisites

- Access to a Meta OD (OnDemand) or Devserver
- VS Code with Remote SSH extension (recommended)
- Your app files from `c:\Users\rdelaporte\Desktop\itc_form_generator`

---

## Option A: Quick Deploy (VS Code Remote SSH)

### Step 1: Connect to Your Devserver

1. Open VS Code
2. Press `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
3. Enter your devserver: `devvm` or `your-devserver.facebook.com`

### Step 2: Copy App Files

In the VS Code terminal (connected to devserver):

```bash
# Create destination directory
mkdir -p ~/itc_form_generator

# Exit VS Code Remote, then from local Windows PowerShell:
scp -r "c:\Users\rdelaporte\Desktop\itc_form_generator\*" devvm:~/itc_form_generator/
```

Or use VS Code's file explorer to drag-and-drop files.

### Step 3: Deploy to NEST

```bash
# SSH to devserver
ssh devvm

# Navigate to app
cd ~/itc_form_generator

# Make deploy script executable and run
chmod +x deploy_to_nest.sh
./deploy_to_nest.sh
```

---

## Option B: Manual Deployment

### Step 1: Copy to fbsource

```bash
# On devserver
cd ~/fbsource/fbcode

# Create destination
mkdir -p datacenter_cx/tools/itc_form_generator

# Copy files
cp -r ~/itc_form_generator/* datacenter_cx/tools/itc_form_generator/
```

### Step 2: Verify Files

```bash
cd ~/fbsource/fbcode/datacenter_cx/tools/itc_form_generator

# Check required files exist
ls -la
# Should see:
#   - webapp.py
#   - requirements.txt
#   - nest.json
#   - Dockerfile
#   - src/
```

### Step 3: Test MetaGen Locally

```bash
# Test if MetaGen works on devserver
python3 -c "from metagen import MetaGenPlatform; print('MetaGen OK!')"
```

### Step 4: Deploy

```bash
cd ~/fbsource/fbcode/datacenter_cx/tools/itc_form_generator

# Deploy to NEST
nest deploy
```

---

## Post-Deployment

### Check Status

```bash
nest status
```

### View Logs

```bash
nest logs
```

### Access Your App

After deployment, your app will be available at:

```
https://itc_form_generator.nest.meta.net
```

---

## Verify MetaGen is Working

1. Open the app URL in your browser
2. Upload an SOO document
3. **Enable "AI Enhancement" checkbox** ✓
4. Click "Generate ITC Forms"
5. Check that AI-enhanced items appear (should see "AI-" prefixed items)

---

## Troubleshooting

### "metagen not found" Error

MetaGen only works on Meta internal infrastructure. Make sure you're:
- On a Devserver/OD (not local Windows)
- Running within fbsource environment

### Deployment Failed

```bash
# Check NEST configuration
cat nest.json

# Validate Dockerfile
docker build -t itc_form_generator .

# Check logs
nest logs --tail 100
```

### App Not Accessible

```bash
# Check if deployed
nest status

# Check health endpoint
curl https://itc_form_generator.nest.meta.net/api/health
```

---

## Files Required for Deployment

| File | Purpose |
|------|---------|
| `webapp.py` | Main web application |
| `src/` | Python package with all modules |
| `requirements.txt` | Python dependencies |
| `nest.json` | NEST deployment configuration |
| `Dockerfile` | Container build instructions |
| `feedback_data.json` | Stored feedback (optional) |
| `learned_examples.json` | Learned form examples (optional) |

---

## MetaGen Features Enabled

Once deployed to NEST, the following AI features become active:

| Feature | Description |
|---------|-------------|
| AI SOO Parsing | Extracts systems, setpoints, modes from documents |
| Smart Check Items | Generates context-aware inspection items |
| Acceptance Criteria | Creates specific pass/fail criteria |
| Form Review | AI reviews forms for completeness |
| Test Procedures | Suggests detailed test methods |

---

## Need Help?

- **NEST Documentation**: https://www.internalfb.com/nest
- **MetaGen Docs**: https://www.internalfb.com/metagen
- **Oncall**: dec_operations_quality
