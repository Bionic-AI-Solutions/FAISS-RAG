# Enterprise Multi-Modal RAG System - Usage Guide with MCP

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Server Setup](#mcp-server-setup)
3. [Available MCP Tools](#available-mcp-tools)
4. [Usage Examples](#usage-examples)
5. [Integration Patterns](#integration-patterns)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 1. Overview

### 1.1 What is MCP?

The Model Context Protocol (MCP) provides a standardized way to expose tools and data sources to Large Language Models. For this RAG system, we provide an MCP server that exposes all system capabilities as tools that can be called by Claude or other MCP-compatible LLMs.

### 1.2 Benefits of Using MCP

**For Users:**
- Natural language interface to all RAG system features
- No need to learn API endpoints or write code
- Seamless integration with Claude Desktop or other MCP clients

**For Developers:**
- Standardized tool interface
- Automatic schema generation
- Built-in error handling and validation
- Easy to extend with new tools

**For Administrators:**
- Centralized access control
- Audit logging of all operations
- Resource usage tracking per user

---

## 2. MCP Server Setup

### 2.1 MCP Server Implementation

```python
# mcp_server.py
"""
MCP Server for Enterprise RAG System

This server exposes all RAG system capabilities as MCP tools.
Compatible with Claude Desktop, Claude API, and other MCP clients.
"""

import asyncio
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import json

# Initialize RAG API client
class RAGAPIClient:
    def __init__(self, base_url: str, api_key: str, tenant_id: str):
        self.base_url = base_url
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Tenant-ID": tenant_id
            },
            timeout=30.0
        )
    
    async def request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated request to RAG API"""
        url = f"{self.base_url}{endpoint}"
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

# Initialize MCP Server
app = Server("enterprise-rag-mcp")

# Global API client (initialized from config)
api_client: Optional[RAGAPIClient] = None

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Define all available MCP tools"""
    return [
        # Document Management Tools
        Tool(
            name="upload_document",
            description="Upload a document to the RAG system for processing and indexing",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the document file to upload"
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "category": {
                        "type": "string",
                        "description": "Document category (e.g., 'finance', 'legal', 'technical')"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for organizing the document"
                    }
                },
                "required": ["file_path"]
            }
        ),
        
        Tool(
            name="list_documents",
            description="List all documents in the system with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "modality": {
                        "type": "string",
                        "enum": ["text", "image", "audio", "video", "table"],
                        "description": "Filter by document modality"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "page": {
                        "type": "integer",
                        "default": 1,
                        "description": "Page number for pagination"
                    },
                    "page_size": {
                        "type": "integer",
                        "default": 20,
                        "description": "Number of results per page"
                    }
                }
            }
        ),
        
        Tool(
            name="get_document_status",
            description="Get the processing status of a document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document to check"
                    }
                },
                "required": ["document_id"]
            }
        ),
        
        Tool(
            name="delete_document",
            description="Delete a document from the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document to delete"
                    }
                },
                "required": ["document_id"]
            }
        ),
        
        # Query Tools
        Tool(
            name="query_documents",
            description="Query the RAG system to find relevant information from indexed documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or search query"
                    },
                    "modalities": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["text", "image", "audio", "video", "table"]
                        },
                        "description": "Which modalities to search (default: all)"
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by categories"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"}
                        },
                        "description": "Filter by date range"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of results to return"
                    },
                    "include_sources": {
                        "type": "boolean",
                        "default": true,
                        "description": "Include source documents in response"
                    },
                    "llm_provider": {
                        "type": "string",
                        "enum": ["claude", "openai", "ollama"],
                        "default": "ollama",
                        "description": "LLM provider to use for response generation"
                    }
                },
                "required": ["query"]
            }
        ),
        
        Tool(
            name="semantic_search",
            description="Perform semantic search across documents without LLM generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "keyword", "hybrid"],
                        "default": "hybrid",
                        "description": "Type of search to perform"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 20,
                        "description": "Number of results to return"
                    },
                    "min_score": {
                        "type": "number",
                        "default": 0.7,
                        "description": "Minimum relevance score (0-1)"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # Session Management Tools
        Tool(
            name="create_session",
            description="Create a new conversation session for context-aware queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Session title"
                    },
                    "document_scope": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Limit session to specific document IDs"
                    }
                }
            }
        ),
        
        Tool(
            name="query_with_session",
            description="Query with conversation history from a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to use"
                    },
                    "query": {
                        "type": "string",
                        "description": "The question or query"
                    },
                    "use_history": {
                        "type": "boolean",
                        "default": true,
                        "description": "Use conversation history for context"
                    }
                },
                "required": ["session_id", "query"]
            }
        ),
        
        Tool(
            name="get_session_history",
            description="Retrieve conversation history from a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        
        # Analytics Tools
        Tool(
            name="get_usage_statistics",
            description="Get system usage statistics and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date for statistics"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "End date for statistics"
                    },
                    "granularity": {
                        "type": "string",
                        "enum": ["hour", "day", "week", "month"],
                        "default": "day",
                        "description": "Time granularity for aggregation"
                    }
                }
            }
        ),
        
        Tool(
            name="get_popular_documents",
            description="Get most frequently accessed documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of documents to return"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["day", "week", "month"],
                        "default": "week",
                        "description": "Time period to analyze"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MCP tool calls"""
    
    if not api_client:
        return [TextContent(
            type="text",
            text="Error: RAG API client not initialized. Please check configuration."
        )]
    
    try:
        if name == "upload_document":
            result = await upload_document_impl(arguments)
        elif name == "list_documents":
            result = await list_documents_impl(arguments)
        elif name == "get_document_status":
            result = await get_document_status_impl(arguments)
        elif name == "delete_document":
            result = await delete_document_impl(arguments)
        elif name == "query_documents":
            result = await query_documents_impl(arguments)
        elif name == "semantic_search":
            result = await semantic_search_impl(arguments)
        elif name == "create_session":
            result = await create_session_impl(arguments)
        elif name == "query_with_session":
            result = await query_with_session_impl(arguments)
        elif name == "get_session_history":
            result = await get_session_history_impl(arguments)
        elif name == "get_usage_statistics":
            result = await get_usage_statistics_impl(arguments)
        elif name == "get_popular_documents":
            result = await get_popular_documents_impl(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

# Tool Implementations
async def upload_document_impl(args: dict) -> dict:
    """Upload document to RAG system"""
    file_path = args["file_path"]
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        metadata = {
            "title": args.get("title", ""),
            "category": args.get("category", ""),
            "tags": args.get("tags", [])
        }
        
        result = await api_client.request(
            "POST",
            "/v1/documents/upload",
            files=files,
            data={"metadata": json.dumps(metadata)}
        )
    
    return {
        "success": True,
        "document_id": result["document_id"],
        "status": result["status"],
        "message": f"Document uploaded successfully. Processing status: {result['status']}"
    }

async def list_documents_impl(args: dict) -> dict:
    """List documents with filters"""
    params = {
        "page": args.get("page", 1),
        "page_size": args.get("page_size", 20)
    }
    
    if "modality" in args:
        params["modality"] = args["modality"]
    if "category" in args:
        params["category"] = args["category"]
    if "tags" in args:
        params["tags"] = ",".join(args["tags"])
    
    result = await api_client.request("GET", "/v1/documents", params=params)
    
    return {
        "documents": result["documents"],
        "pagination": result["pagination"]
    }

async def get_document_status_impl(args: dict) -> dict:
    """Get document processing status"""
    document_id = args["document_id"]
    result = await api_client.request(
        "GET",
        f"/v1/documents/{document_id}/status"
    )
    return result

async def delete_document_impl(args: dict) -> dict:
    """Delete document"""
    document_id = args["document_id"]
    result = await api_client.request(
        "DELETE",
        f"/v1/documents/{document_id}"
    )
    return {
        "success": True,
        "message": f"Document {document_id} deleted successfully"
    }

async def query_documents_impl(args: dict) -> dict:
    """Query documents with RAG"""
    payload = {
        "query": args["query"],
        "filters": {},
        "options": {
            "top_k": args.get("top_k", 10),
            "include_sources": args.get("include_sources", True),
            "llm_provider": args.get("llm_provider", "ollama")
        }
    }
    
    # Add filters
    if "modalities" in args:
        payload["filters"]["modality"] = args["modalities"]
    if "categories" in args:
        payload["filters"]["categories"] = args["categories"]
    if "tags" in args:
        payload["filters"]["tags"] = args["tags"]
    if "date_range" in args:
        payload["filters"]["date_range"] = args["date_range"]
    
    result = await api_client.request("POST", "/v1/query", json=payload)
    
    return {
        "response": result["response"],
        "sources": result.get("sources", []),
        "metadata": result.get("metadata", {})
    }

async def semantic_search_impl(args: dict) -> dict:
    """Perform semantic search"""
    payload = {
        "query": args["query"],
        "search_type": args.get("search_type", "hybrid"),
        "options": {
            "top_k": args.get("top_k", 20),
            "min_score": args.get("min_score", 0.7)
        }
    }
    
    result = await api_client.request("POST", "/v1/search", json=payload)
    return result

async def create_session_impl(args: dict) -> dict:
    """Create new session"""
    payload = {
        "title": args.get("title", ""),
        "context": {
            "document_scope": args.get("document_scope", [])
        }
    }
    
    result = await api_client.request("POST", "/v1/sessions", json=payload)
    return {
        "session_id": result["session_id"],
        "created_at": result["created_at"],
        "message": "Session created successfully"
    }

async def query_with_session_impl(args: dict) -> dict:
    """Query with session context"""
    session_id = args["session_id"]
    payload = {
        "query": args["query"],
        "use_history": args.get("use_history", True)
    }
    
    result = await api_client.request(
        "POST",
        f"/v1/sessions/{session_id}/query",
        json=payload
    )
    
    return {
        "response": result["response"],
        "sources": result.get("sources", []),
        "conversation_length": len(result.get("conversation_history", []))
    }

async def get_session_history_impl(args: dict) -> dict:
    """Get session history"""
    session_id = args["session_id"]
    result = await api_client.request(
        "GET",
        f"/v1/sessions/{session_id}/history"
    )
    return result

async def get_usage_statistics_impl(args: dict) -> dict:
    """Get usage statistics"""
    params = {
        "granularity": args.get("granularity", "day")
    }
    if "start_date" in args:
        params["start_date"] = args["start_date"]
    if "end_date" in args:
        params["end_date"] = args["end_date"]
    
    result = await api_client.request(
        "GET",
        "/v1/analytics/usage",
        params=params
    )
    return result

async def get_popular_documents_impl(args: dict) -> dict:
    """Get popular documents"""
    params = {
        "limit": args.get("limit", 10),
        "time_period": args.get("time_period", "week")
    }
    
    result = await api_client.request(
        "GET",
        "/v1/analytics/popular",
        params=params
    )
    return result

# Server initialization
async def main():
    """Run MCP server"""
    global api_client
    
    # Load configuration
    import os
    api_client = RAGAPIClient(
        base_url=os.getenv("RAG_API_URL", "http://localhost:8000"),
        api_key=os.getenv("RAG_API_KEY"),
        tenant_id=os.getenv("RAG_TENANT_ID")
    )
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 MCP Server Configuration

```json
# mcp-config.json
{
  "mcpServers": {
    "enterprise-rag": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "RAG_API_URL": "https://api.rag-system.com",
        "RAG_API_KEY": "your-api-key-here",
        "RAG_TENANT_ID": "your-tenant-id-here"
      }
    }
  }
}
```

### 2.3 Deployment

#### Docker Deployment

```dockerfile
# Dockerfile.mcp
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server
COPY mcp_server.py .

# Run server
CMD ["python", "mcp_server.py"]
```

```yaml
# requirements.txt
mcp>=0.9.0
httpx>=0.24.0
python-dotenv>=1.0.0
```

#### Kubernetes Deployment

```yaml
# mcp-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: rag-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/rag-mcp-server:latest
        env:
        - name: RAG_API_URL
          value: "http://query-service:8000"
        - name: RAG_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-credentials
              key: api-key
        - name: RAG_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: mcp-credentials
              key: tenant-id
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
  namespace: rag-system
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: mcp-server
```

---

## 3. Available MCP Tools

### 3.1 Document Management Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `upload_document` | Upload and index a document | Add new documents to the system |
| `list_documents` | List all documents with filters | Browse or search for existing documents |
| `get_document_status` | Check processing status | Monitor document ingestion progress |
| `delete_document` | Remove a document | Clean up unwanted documents |

### 3.2 Query Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `query_documents` | Full RAG query with LLM | Ask questions, get AI-generated answers |
| `semantic_search` | Search without LLM generation | Find relevant documents quickly |

### 3.3 Session Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `create_session` | Start a conversation session | Multi-turn conversations with context |
| `query_with_session` | Query with conversation history | Ask follow-up questions |
| `get_session_history` | View conversation history | Review past interactions |

### 3.4 Analytics Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `get_usage_statistics` | System usage metrics | Monitor system activity |
| `get_popular_documents` | Most accessed documents | Identify valuable content |

---

## 4. Usage Examples

### 4.1 Using with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "enterprise-rag": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "RAG_API_URL": "https://api.rag-system.com",
        "RAG_API_KEY": "your-api-key",
        "RAG_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

### 4.2 Example Conversations

#### Example 1: Upload and Query Documents

```
User: Upload the Q4 financial report from /documents/q4_report.pdf

Claude: I'll upload that document for you.
[Uses upload_document tool]

The document has been uploaded successfully! 
- Document ID: doc-123-456
- Status: Processing
- Estimated time: ~30 seconds

The system is now processing the document to make it searchable.

User: Great! What were the key revenue figures in that report?

Claude: Let me search the Q4 report for revenue information.
[Uses query_documents tool with document filter]

Based on the Q4 financial report, here are the key revenue figures:

**Total Revenue**: $45M (23% increase YoY)
- Q4 2024: $45M
- Q4 2023: $36.6M

**Revenue Breakdown by Segment**:
- Enterprise: $28M (62%)
- SMB: $12M (27%)  
- Government: $5M (11%)

**Key Highlights**:
- Largest quarter ever
- Strong growth in enterprise segment (+35%)
- International revenue grew to 40% of total

Sources: Q4 Financial Report, pages 3-5
```

#### Example 2: Multi-Document Analysis

```
User: Compare our Q3 and Q4 revenue performance

Claude: I'll analyze both quarterly reports for you.
[Uses query_documents tool searching across multiple documents]

Here's a comparison of Q3 vs Q4 2024 revenue performance:

**Total Revenue Growth**:
- Q3: $42M
- Q4: $45M
- Growth: +$3M (+7.1%)

**Quarter-over-Quarter Trends**:
1. Enterprise segment accelerated (Q3: +18%, Q4: +35%)
2. SMB remained steady (~$12M both quarters)
3. Government contracts increased in Q4 (+25%)

**Notable Changes**:
- Customer acquisition cost decreased by 15% in Q4
- Average deal size increased from $125K to $145K
- Churn rate improved from 3.2% to 2.8%

The Q4 performance exceeded Q3 in all key metrics, with particularly strong enterprise growth.

Sources: Q3 Report (pages 2-4), Q4 Report (pages 3-5, 12)
```

#### Example 3: Session-Based Conversation

```
User: Create a session to discuss our financial strategy

Claude: I've created a conversation session for discussing financial strategy.
[Uses create_session tool]
Session ID: session-789
You can now ask follow-up questions and I'll maintain the context.

User: What's our revenue trend over the past year?

Claude: [Uses query_with_session tool]
Looking at the full year 2024 data:

**Revenue Progression**:
- Q1: $35M
- Q2: $38M (+8.5%)
- Q3: $42M (+10.5%)
- Q4: $45M (+7.1%)

**Annual Total**: $160M
**YoY Growth**: +24%

The trend shows consistent growth with acceleration in mid-year.

User: How does this compare to our targets?

Claude: [Uses query_with_session tool - maintains context]
Comparing actual vs. targets for 2024:

**Annual Target**: $155M
**Actual**: $160M
**Performance**: +3.2% above target

**By Quarter**:
- Q1: On target
- Q2: 2% above target
- Q3: 5% above target  
- Q4: 4% above target

We exceeded our annual revenue target, with particularly strong performance in Q3 and Q4. The strategy of focusing on enterprise sales clearly paid off.
```

#### Example 4: Multi-Modal Search

```
User: Find all charts and tables showing our customer growth metrics

Claude: I'll search for visual and tabular data about customer growth.
[Uses semantic_search with modalities: ["image", "table"]]

Found 8 relevant items:

**Charts (5)**:
1. Monthly Customer Acquisition Chart (Q4 Deck, slide 12)
   - Shows 23% MoM growth trend
   
2. Customer Segment Distribution (Annual Report, page 8)
   - Pie chart of enterprise vs SMB vs government

3. Churn Rate Trend (Operations Dashboard)
   - Line graph showing decline from 4.1% to 2.8%

**Tables (3)**:
1. Customer Metrics by Quarter (Q4 Report, page 7)
   - New customers, churn, net growth
   
2. Top 10 Customers by Revenue (Sales Report)
   - Enterprise customer breakdown

3. Geographic Distribution (International Expansion Doc)
   - Customer count by region

Would you like me to provide details from any specific chart or table?
```

#### Example 5: Analytics and Insights

```
User: Show me which documents are most frequently accessed this month

Claude: [Uses get_popular_documents tool]

Here are the top 10 most accessed documents this month:

1. **Product Roadmap 2025** (456 views)
   - Category: Product
   - Last updated: Dec 15, 2024

2. **Q4 Financial Report** (389 views)
   - Category: Finance
   - Last updated: Dec 20, 2024

3. **Sales Playbook** (312 views)
   - Category: Sales
   - Last updated: Nov 30, 2024

4. **API Documentation v2.0** (287 views)
   - Category: Technical
   - Last updated: Dec 10, 2024

5. **Customer Onboarding Guide** (245 views)
   - Category: Support
   - Last updated: Dec 5, 2024

[... 5 more documents]

The Product Roadmap and Q4 Financial Report are clearly the most valuable resources this month.
```

---

## 5. Integration Patterns

### 5.1 Claude Desktop Integration

**Full workflow:**

1. Install MCP server
2. Configure Claude Desktop
3. Use natural language to interact with RAG system
4. All tools available automatically

**Benefits:**
- No coding required
- Natural conversation interface
- Automatic tool selection
- Context maintained across conversations

### 5.2 Claude API Integration

```python
# Using MCP with Claude API
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")

# MCP tools are automatically available when configured
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": "Upload the report at /docs/annual_report.pdf and summarize the key findings"
    }],
    tools=[
        # MCP tools automatically injected
    ]
)

print(response.content)
```

### 5.3 Custom Application Integration

```python
# custom_app.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_rag_system():
    """Use RAG system via MCP"""
    
    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env={
            "RAG_API_URL": "https://api.rag-system.com",
            "RAG_API_KEY": "your-api-key",
            "RAG_TENANT_ID": "your-tenant-id"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")
            
            # Upload document
            result = await session.call_tool(
                "upload_document",
                {
                    "file_path": "/docs/report.pdf",
                    "title": "Annual Report",
                    "category": "finance"
                }
            )
            print(f"Upload result: {result}")
            
            # Query
            result = await session.call_tool(
                "query_documents",
                {
                    "query": "What were the main achievements?",
                    "top_k": 5
                }
            )
            print(f"Query result: {result}")

# Run
asyncio.run(use_rag_system())
```

### 5.4 Web Interface Integration

```javascript
// web-app.js
// Using MCP via WebSocket proxy

class RAGSystemClient {
    constructor(mcpServerUrl) {
        this.ws = new WebSocket(mcpServerUrl);
        this.requestId = 0;
        this.pending = new Map();
    }
    
    async callTool(toolName, args) {
        const id = ++this.requestId;
        
        return new Promise((resolve, reject) => {
            this.pending.set(id, { resolve, reject });
            
            this.ws.send(JSON.stringify({
                jsonrpc: "2.0",
                id: id,
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: args
                }
            }));
            
            // Timeout after 30 seconds
            setTimeout(() => {
                if (this.pending.has(id)) {
                    this.pending.delete(id);
                    reject(new Error("Request timeout"));
                }
            }, 30000);
        });
    }
    
    async uploadDocument(filePath, metadata) {
        return await this.callTool("upload_document", {
            file_path: filePath,
            ...metadata
        });
    }
    
    async query(question, options = {}) {
        return await this.callTool("query_documents", {
            query: question,
            ...options
        });
    }
}

// Usage
const rag = new RAGSystemClient("wss://mcp.rag-system.com");

// Upload
await rag.uploadDocument("/uploads/doc.pdf", {
    title: "Important Document",
    category: "legal"
});

// Query
const result = await rag.query("What are the key points?");
console.log(result);
```

---

## 6. Best Practices

### 6.1 Tool Selection

**Use the right tool for the task:**

| Task | Recommended Tool | Why |
|------|------------------|-----|
| Ask questions | `query_documents` | Includes LLM generation |
| Find documents | `semantic_search` | Faster, no LLM overhead |
| Multi-turn chat | `query_with_session` | Maintains conversation context |
| Browse content | `list_documents` | Structured filtering |
| Monitor system | `get_usage_statistics` | Track metrics |

### 6.2 Performance Optimization

```python
# Good: Batch operations
documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
for doc in documents:
    await upload_document(doc)  # Each upload processed

# Better: Use filters effectively
result = await query_documents(
    query="revenue trends",
    categories=["finance"],  # Narrow scope
    date_range={"start": "2024-01-01", "end": "2024-12-31"}
)

# Best: Use sessions for related queries
session = await create_session(title="Financial Analysis")
for question in questions:
    await query_with_session(session_id, question)
```

### 6.3 Error Handling

```python
# Always handle errors
try:
    result = await query_documents(query="complex question")
    if "error" in result:
        print(f"Query failed: {result['error']}")
    else:
        print(result["response"])
except Exception as e:
    print(f"Request failed: {e}")
    # Implement retry logic if appropriate
```

### 6.4 Security Best Practices

```bash
# 1. Never hardcode credentials
export RAG_API_KEY="your-api-key"
export RAG_TENANT_ID="your-tenant-id"

# 2. Use environment-specific configs
# dev-config.json, staging-config.json, prod-config.json

# 3. Rotate API keys regularly
# Set key expiration to 90 days

# 4. Monitor API usage
# Track unusual patterns, high error rates

# 5. Use least privilege
# Only grant necessary tool access per user
```

---

## 7. Troubleshooting

### 7.1 Common Issues

#### MCP Server Not Starting

```bash
# Check Python version (requires 3.11+)
python --version

# Install dependencies
pip install -r requirements.txt

# Check environment variables
env | grep RAG

# Test connection to RAG API
curl -H "Authorization: Bearer $RAG_API_KEY" \
     -H "X-Tenant-ID: $RAG_TENANT_ID" \
     https://api.rag-system.com/v1/health
```

#### Tool Execution Failures

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check API response
try:
    result = await api_client.request("GET", "/v1/documents")
    print(f"Response: {result}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
```

#### Slow Tool Responses

```python
# Check query performance
import time

start = time.time()
result = await query_documents(query="test")
duration = time.time() - start

print(f"Query took {duration:.2f} seconds")

# If slow:
# 1. Check network latency to API
# 2. Reduce top_k parameter
# 3. Add more specific filters
# 4. Use semantic_search instead of query_documents
```

### 7.2 Debugging Tips

```python
# Enable verbose logging
import os
os.environ["MCP_DEBUG"] = "1"

# Test individual tools
async def test_tools():
    # Test upload
    result = await upload_document({
        "file_path": "test.txt",
        "title": "Test Document"
    })
    assert result["success"], "Upload failed"
    
    # Test query
    result = await query_documents({
        "query": "test query"
    })
    assert "response" in result, "Query failed"
    
    print("All tests passed!")

# Check API health
async def check_health():
    result = await api_client.request("GET", "/v1/health")
    print(f"API Health: {result}")
```

### 7.3 Performance Monitoring

```python
# Track tool usage
from collections import defaultdict
import time

tool_stats = defaultdict(lambda: {"count": 0, "total_time": 0})

async def monitored_call_tool(name: str, arguments: dict):
    start = time.time()
    result = await call_tool(name, arguments)
    duration = time.time() - start
    
    tool_stats[name]["count"] += 1
    tool_stats[name]["total_time"] += duration
    
    return result

# Print stats
def print_stats():
    for tool, stats in tool_stats.items():
        avg_time = stats["total_time"] / stats["count"]
        print(f"{tool}: {stats['count']} calls, {avg_time:.2f}s avg")
```

---

## 8. Advanced Usage

### 8.1 Custom Tool Development

```python
# Add custom tool to MCP server

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Add custom tools"""
    base_tools = [...]  # existing tools
    
    custom_tools = [
        Tool(
            name="analyze_trends",
            description="Analyze document trends over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "time_period": {"type": "string"}
                }
            }
        )
    ]
    
    return base_tools + custom_tools

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_trends":
        return await analyze_trends_impl(arguments)
    # ... handle other tools
```

### 8.2 Workflow Automation

```python
# Automated document processing workflow

async def process_new_documents(folder_path: str):
    """Auto-process all documents in folder"""
    
    import os
    from pathlib import Path
    
    # Find all documents
    docs = list(Path(folder_path).glob("**/*"))
    docs = [d for d in docs if d.suffix in [".pdf", ".docx", ".txt"]]
    
    print(f"Found {len(docs)} documents to process")
    
    # Upload all
    for doc in docs:
        result = await call_tool("upload_document", {
            "file_path": str(doc),
            "title": doc.stem,
            "category": doc.parent.name  # Use folder name as category
        })
        
        print(f"Uploaded: {doc.name} -> {result['document_id']}")
        
        # Wait for processing
        await asyncio.sleep(2)
    
    print("All documents uploaded!")

# Run workflow
asyncio.run(process_new_documents("/data/new_documents"))
```

---

## Appendix A: Complete MCP Tool Reference

| Tool Name | Required Args | Optional Args | Returns |
|-----------|---------------|---------------|---------|
| `upload_document` | file_path | title, category, tags | document_id, status |
| `list_documents` | - | modality, category, tags, page | documents[], pagination |
| `get_document_status` | document_id | - | status, progress, errors |
| `delete_document` | document_id | - | success |
| `query_documents` | query | modalities, filters, top_k, llm_provider | response, sources[], metadata |
| `semantic_search` | query | search_type, top_k, min_score | results[], search_time_ms |
| `create_session` | - | title, document_scope | session_id, created_at |
| `query_with_session` | session_id, query | use_history | response, sources[], conversation_length |
| `get_session_history` | session_id | - | messages[], pagination |
| `get_usage_statistics` | - | start_date, end_date, granularity | metrics, usage_by_period[] |
| `get_popular_documents` | - | limit, time_period | documents[] |

---

## Appendix B: Configuration Examples

### Claude Desktop Config

```json
{
  "mcpServers": {
    "enterprise-rag": {
      "command": "python",
      "args": ["/usr/local/bin/rag_mcp_server.py"],
      "env": {
        "RAG_API_URL": "https://api.rag-system.com",
        "RAG_API_KEY": "sk_live_...",
        "RAG_TENANT_ID": "tenant_abc123"
      }
    }
  }
}
```

### Docker Compose

```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    environment:
      - RAG_API_URL=http://query-service:8000
      - RAG_API_KEY=${RAG_API_KEY}
      - RAG_TENANT_ID=${RAG_TENANT_ID}
    ports:
      - "3000:3000"
    restart: unless-stopped
```

---

**End of Usage Guide**

For system architecture, see: ARCHITECTURE.md
For API details, see: API_SPECIFICATION.md
For deployment instructions, see: DEPLOYMENT.md
