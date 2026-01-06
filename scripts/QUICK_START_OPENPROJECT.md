# Quick Start: Setting OpenProject Parent Relationships

## One-Time Setup

1. **Get OpenProject API Key**:
   - Go to: https://openproject.bionicaisolutions.com
   - Login → Profile → Access tokens → Create new token
   - Copy the token

2. **Set Environment Variables**:
   ```bash
   export OPENPROJECT_URL="https://openproject.bionicaisolutions.com"
   export OPENPROJECT_API_KEY="your-token-here"
   ```

3. **Install Dependencies**:
   ```bash
   pip install requests
   ```

## Run the Script

```bash
cd /workspaces/mem0-rag
python scripts/set_openproject_parents.py
```

## What Gets Set

- **24 parent-child relationships** total
- **3 Epics** (Platform Foundation, RAG Capabilities, Mem0 Integration)
- **9 Features** (3 per Epic)
- **15 User Stories** (distributed across Features)

## Verification

After running, check in OpenProject:
- Open project: https://openproject.bionicaisolutions.com/projects/8/work_packages
- Work packages should show hierarchical structure
- Each Feature should be nested under its Epic
- Each Story should be nested under its Feature

## Troubleshooting

**"401 Unauthorized"**: Check your API key
**"404 Not Found"**: Verify work package IDs exist
**"Connection failed"**: Check OPENPROJECT_URL and network access

For detailed help, see: `scripts/README_OPENPROJECT_SETUP.md`











