#!/usr/bin/env python3
"""
Create tasks for Epic 6 stories in OpenProject.

Epic 6: Session Continuity & User Recognition
Stories:
- Story 6.1: Session Context Storage
- Story 6.2: Session Continuity Support
- Story 6.3: Context-Aware Search Results
- Story 6.4: Returning User Recognition
"""

import json
from mcp_openproject_bulk_create_work_packages import mcp_openproject_bulk_create_work_packages

# Project ID
PROJECT_ID = 8

# Story IDs
STORY_6_1_ID = 145
STORY_6_2_ID = 146
STORY_6_3_ID = 147
STORY_6_4_ID = 148

# Task type ID (Task)
TASK_TYPE_ID = 36

# Status IDs
STATUS_NEW = 71
STATUS_IN_PROGRESS = 77
STATUS_CLOSED = 82

# Priority IDs
PRIORITY_NORMAL = 73

# Task definitions for Story 6.1: Session Context Storage
story_6_1_tasks = [
    {
        "subject": "Task 6.1.1: Create SessionContextService for Redis storage",
        "description": "Create SessionContextService class to handle session context storage and retrieval in Redis with key format tenant_id:user_id:session_id.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.2: Implement session context storage with TTL",
        "description": "Implement store_session_context method that stores session context in Redis with TTL (default 24 hours). Context includes: conversation_state, interrupted_queries, recent_interactions, user_preferences.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.3: Implement incremental session context updates",
        "description": "Implement update_session_context method that allows incremental updates to session context without overwriting existing data.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.4: Implement session context retrieval",
        "description": "Implement get_session_context method that retrieves session context by session_id, user_id, tenant_id. Ensure retrieval completes within <100ms (p95).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.5: Implement background cleanup job",
        "description": "Create background cleanup job that runs daily to remove orphaned sessions (sessions with no recent activity for 48+ hours). Make cleanup configurable per tenant (TTL and cleanup frequency).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.6: Write unit tests",
        "description": "Write comprehensive unit tests for SessionContextService covering storage, retrieval, incremental updates, TTL, and cleanup job.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
    {
        "subject": "Task 6.1.7: Create verification documentation",
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_1_ID,
    },
]

# Task definitions for Story 6.2: Session Continuity Support
story_6_2_tasks = [
    {
        "subject": "Task 6.2.1: Create SessionContinuityService",
        "description": "Create SessionContinuityService class to handle session interruption detection and resumption.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.2: Implement session interruption detection and storage",
        "description": "Implement logic to detect conversation interruptions and automatically store session context using SessionContextService.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.3: Implement session resumption",
        "description": "Implement resume_session method that retrieves session context and restores previous conversation state. Ensure resumption completes within <500ms (cold start acceptable).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.4: Implement interrupted query preservation",
        "description": "Implement logic to preserve interrupted queries and enable their resumption when session is resumed.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.5: Create session continuity MCP tools",
        "description": "Create MCP tools for session interruption and resumption: rag_interrupt_session and rag_resume_session.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.6: Write unit tests",
        "description": "Write comprehensive unit tests for SessionContinuityService and MCP tools covering interruption detection, storage, resumption, and query preservation.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
    {
        "subject": "Task 6.2.7: Create verification documentation",
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_2_ID,
    },
]

# Task definitions for Story 6.3: Context-Aware Search Results
story_6_3_tasks = [
    {
        "subject": "Task 6.3.1: Create ContextAwareSearchService",
        "description": "Create ContextAwareSearchService class to handle context-aware search result personalization.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.2: Integrate user memory for personalization",
        "description": "Implement logic to retrieve user memory and use it for search result personalization. Ensure personalization doesn't degrade search performance (<200ms p95).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.3: Integrate session context for personalization",
        "description": "Implement logic to retrieve session context and use it for search result personalization.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.4: Implement result ranking with personalization",
        "description": "Implement ranking algorithm that considers both relevance (from knowledge base search) and personalization (from user memory and session context).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.5: Make personalization configurable per tenant",
        "description": "Add tenant configuration option to enable/disable personalization. Personalization should be optional and configurable per tenant.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.6: Integrate with existing rag_search tool",
        "description": "Integrate ContextAwareSearchService with existing rag_search MCP tool to enable context-aware search results.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.7: Write unit tests",
        "description": "Write comprehensive unit tests for ContextAwareSearchService covering user memory integration, session context integration, ranking, and tenant configuration.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
    {
        "subject": "Task 6.3.8: Create verification documentation",
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_3_ID,
    },
]

# Task definitions for Story 6.4: Returning User Recognition
story_6_4_tasks = [
    {
        "subject": "Task 6.4.1: Create UserRecognitionService",
        "description": "Create UserRecognitionService class to handle returning user recognition by user_id and tenant_id.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.2: Implement user recognition logic",
        "description": "Implement recognize_user method that checks if user is returning and retrieves user memory. Ensure recognition completes within <100ms (p95).",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.3: Implement personalized greeting generation",
        "description": "Implement generate_greeting method that creates personalized greeting based on user memory.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.4: Implement context summary generation",
        "description": "Implement generate_context_summary method that provides context summary including recent interactions and preferences.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.5: Implement Redis caching for user memory",
        "description": "Implement caching mechanism for user memory in Redis to achieve >80% cache hit rate. Configure cache TTL appropriately and implement cache invalidation on memory updates.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.6: Create user recognition MCP tool",
        "description": "Create rag_recognize_user MCP tool that recognizes returning users and provides personalized greeting and context summary.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.7: Write unit tests",
        "description": "Write comprehensive unit tests for UserRecognitionService and MCP tool covering recognition, greeting generation, context summary, and caching.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
    {
        "subject": "Task 6.4.8: Create verification documentation",
        "description": "Create verification document documenting all acceptance criteria and attach to OpenProject story.",
        "type_id": TASK_TYPE_ID,
        "status_id": STATUS_NEW,
        "priority_id": PRIORITY_NORMAL,
        "parent_id": STORY_6_4_ID,
    },
]

# Combine all tasks
all_tasks = (
    story_6_1_tasks
    + story_6_2_tasks
    + story_6_3_tasks
    + story_6_4_tasks
)

# Convert to JSON string for bulk creation
work_packages_json = json.dumps(all_tasks)

print(f"Creating {len(all_tasks)} tasks for Epic 6 stories...")
print(f"Story 6.1 tasks: {len(story_6_1_tasks)}")
print(f"Story 6.2 tasks: {len(story_6_2_tasks)}")
print(f"Story 6.3 tasks: {len(story_6_3_tasks)}")
print(f"Story 6.4 tasks: {len(story_6_4_tasks)}")

# Create tasks in OpenProject
result = mcp_openproject_bulk_create_work_packages(
    project_id=PROJECT_ID,
    work_packages=work_packages_json,
    continue_on_error=True
)

print(f"\nResult: {result}")

if result.get("success"):
    created_count = len(result.get("work_packages", []))
    print(f"\n✅ Successfully created {created_count} tasks")
    
    if result.get("errors"):
        print(f"\n⚠️ Errors encountered: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  - {error}")
else:
    print(f"\n❌ Failed to create tasks: {result.get('message', 'Unknown error')}")








