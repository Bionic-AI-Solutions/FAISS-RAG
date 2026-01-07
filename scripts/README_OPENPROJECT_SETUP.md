# OpenProject Parent-Child Relationship Setup

This script sets up parent-child relationships for work packages in the Mem0-RAG project using the OpenProject API v3.

## Prerequisites

1. **OpenProject API Key**: You need an API key from your OpenProject instance
2. **Python 3.7+**: With `requests` library installed
3. **Network Access**: To your OpenProject instance

## Getting Your OpenProject API Key

1. Log in to OpenProject: `https://openproject.bionicaisolutions.com`
2. Go to your user profile (click your avatar in top right)
3. Navigate to "Access tokens" or "API" section
4. Create a new API token
5. Copy the token (you'll only see it once!)

## Installation

```bash
# Install required Python package
pip install requests

# Or if using poetry
poetry add requests
```

## Configuration

Set the following environment variables:

```bash
export OPENPROJECT_URL="https://openproject.bionicaisolutions.com"
export OPENPROJECT_API_KEY="your-api-key-here"
export OPENPROJECT_PROJECT_ID="8"  # Optional, defaults to 8 for Mem0-RAG
```

Or create a `.env` file in the project root:

```bash
OPENPROJECT_URL=https://openproject.bionicaisolutions.com
OPENPROJECT_API_KEY=your-api-key-here
OPENPROJECT_PROJECT_ID=8
```

Then load it before running:

```bash
source .env
```

## Usage

```bash
# From project root
python scripts/set_openproject_parents.py

# Or if script is executable
./scripts/set_openproject_parents.py
```

## What It Does

The script establishes the following hierarchy:

```
Mem0-RAG Project (ID: 8)
├── Epic 1: Platform Foundation (82)
│   ├── Feature 1.1: Multi-Tenant Authentication (85)
│   │   ├── Story 1.1.1: OAuth 2.0 Implementation (94)
│   │   └── Story 1.1.2: Tenant Isolation Middleware (95)
│   ├── Feature 1.2: Database Schema & Models (86)
│   │   ├── Story 1.2.1: Core Schema Design (96)
│   │   └── Story 1.2.2: RLS Policies Implementation (97)
│   └── Feature 1.3: MCP Server Framework (87)
│       ├── Story 1.3.1: FastMCP Server Setup (98)
│       └── Story 1.3.2: Tool Registration System (99)
├── Epic 2: RAG Capabilities (83)
│   ├── Feature 2.1: Document Ingestion (88)
│   │   ├── Story 2.1.1: Document Parser Implementation (100)
│   │   └── Story 2.1.2: Text Chunking & Embedding (101)
│   ├── Feature 2.2: Vector Search (89)
│   │   ├── Story 2.2.1: Vector Index Management (102)
│   │   └── Story 2.2.2: Similarity Search Implementation (103)
│   └── Feature 2.3: Query Processing (90)
│       └── Story 2.3.1: LLM Query Processing (104)
└── Epic 3: Mem0 Integration (84)
    ├── Feature 3.1: Mem0 Service Integration (91)
    │   └── Story 3.1.1: Mem0 API Client (105)
    ├── Feature 3.2: Memory Management (92)
    │   └── Story 3.2.1: Memory Storage & Retrieval (106)
    └── Feature 3.3: User Context Tracking (93)
        └── Story 3.3.1: Session Context Tracking (107)
```

## Expected Output

```
================================================================================
OpenProject Parent-Child Relationship Setup
================================================================================

📋 Configuration:
   OpenProject URL: https://openproject.bionicaisolutions.com
   Project ID: 8
   API Key: ********************...

🔍 Testing connection...
✅ Connection successful!

🔗 Setting parent-child relationships...

✅ Set Feature 1.1: Multi-Tenant Authentication → Epic 1: Platform Foundation
✅ Set Feature 1.2: Database Schema & Models → Epic 1: Platform Foundation
✅ Set Feature 1.3: MCP Server Framework → Epic 1: Platform Foundation
...
✅ Set Story 3.3.1: Session Context Tracking → Feature 3.3: User Context Tracking

================================================================================
Summary
================================================================================
✅ Successful: 24
❌ Failed: 0
📊 Total: 24

🎉 All parent-child relationships set successfully!

You can now view the hierarchy in OpenProject:
  https://openproject.bionicaisolutions.com/projects/8/work_packages
```

## Troubleshooting

### Error: "Failed to connect to OpenProject"

- Check that `OPENPROJECT_URL` is correct
- Verify network connectivity
- Ensure OpenProject instance is accessible

### Error: "401 Unauthorized"

- Verify your `OPENPROJECT_API_KEY` is correct
- Check that the API key hasn't expired
- Ensure the API key has proper permissions

### Error: "404 Not Found"

- Verify work package IDs exist in the project
- Check that `OPENPROJECT_PROJECT_ID` is correct

### Error: "422 Unprocessable Entity"

- This usually means the parent-child relationship is invalid
- Check that you're not creating circular dependencies
- Verify work package types allow parent-child relationships

## Manual Alternative

If the script doesn't work, you can set parent relationships manually in OpenProject:

1. Open each work package
2. Click "More actions" → "Change parent"
3. Select the parent work package
4. Save

## Notes

- The script uses `lockVersion` to prevent concurrent modification conflicts
- Each work package is fetched first to get the current `lockVersion`
- Parent relationships are set using OpenProject API v3 `_links` structure
- The script is idempotent - you can run it multiple times safely


















