#!/usr/bin/env python3
"""
Audit existing epics and stories in OpenProject to identify what needs updating
based on the new BMAD workflow requirements.

This script checks:
1. Epics have comprehensive descriptions
2. Epics have story breakdowns
3. Epics have test stories (Story X.T)
4. Epics have design documents attached
5. Stories have test tasks (Task X.Y.T)
6. Stories have UI documents attached (if UI stories)
"""

import sys
import json
from typing import Dict, List, Any

# MCP tool imports would go here
# For now, this is a reference implementation showing what to check

PROJECT_ID = 8

# Status IDs
STATUS_NEW = 71
STATUS_IN_PROGRESS = 77
STATUS_IN_TESTING = 79
STATUS_CLOSED = 82

# Type IDs
TYPE_EPIC = 40
TYPE_FEATURE = 39
TYPE_USER_STORY = 41
TYPE_TASK = 36
TYPE_BUG = 42


def audit_epic(epic_id: int, epic_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audit a single epic against BMAD workflow requirements.
    
    Returns audit results with missing requirements.
    """
    audit_results = {
        "epic_id": epic_id,
        "subject": epic_data.get("subject", "Unknown"),
        "issues": [],
        "recommendations": []
    }
    
    # Check 1: Comprehensive description
    description = epic_data.get("description", {}).get("raw", "")
    if not description or len(description) < 200:
        audit_results["issues"].append("Epic description is too brief or missing")
        audit_results["recommendations"].append("Add comprehensive description with business goal, scope, success criteria, dependencies, technical considerations, timeline")
    
    # Check 2: Story breakdown in description
    if "Story Breakdown" not in description and "story breakdown" not in description.lower():
        audit_results["issues"].append("Epic description missing story breakdown")
        audit_results["recommendations"].append("Add story breakdown section listing all stories with goals and dependencies")
    
    # Check 3: Test story exists
    # This would require checking children
    # children = mcp_openproject_get_work_package_children(parent_id=epic_id, status="all")
    # stories = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_USER_STORY]
    # test_story = next((s for s in stories if ".T" in s["subject"] or "Test Story" in s["subject"]), None)
    # if not test_story:
    #     audit_results["issues"].append("Epic missing test story (Story X.T)")
    #     audit_results["recommendations"].append("Create test story: 'Test Story X: Epic X Validation'")
    
    # Check 4: Design document attached
    # attachments = epic_data.get("attachments", [])
    # design_doc = next((a for a in attachments if "design" in a.get("filename", "").lower()), None)
    # if not design_doc:
    #     audit_results["issues"].append("Epic missing design document attachment")
    #     audit_results["recommendations"].append("Attach design document: epic-X-design.md")
    
    return audit_results


def audit_story(story_id: int, story_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audit a single story against BMAD workflow requirements.
    
    Returns audit results with missing requirements.
    """
    audit_results = {
        "story_id": story_id,
        "subject": story_data.get("subject", "Unknown"),
        "issues": [],
        "recommendations": []
    }
    
    # Check 1: Well-written description with acceptance criteria
    description = story_data.get("description", {}).get("raw", "")
    if not description or len(description) < 100:
        audit_results["issues"].append("Story description is too brief or missing")
        audit_results["recommendations"].append("Add comprehensive description with user story format and acceptance criteria")
    
    # Check 2: Acceptance criteria present
    if "Acceptance Criteria" not in description and "acceptance criteria" not in description.lower():
        audit_results["issues"].append("Story description missing acceptance criteria")
        audit_results["recommendations"].append("Add acceptance criteria section with Given/When/Then format")
    
    # Check 3: Test task exists
    # This would require checking children
    # children = mcp_openproject_get_work_package_children(parent_id=story_id, status="all")
    # tasks = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_TASK]
    # test_task = next((t for t in tasks if ".T:" in t["subject"] or "Testing and Validation" in t["subject"]), None)
    # if not test_task:
    #     audit_results["issues"].append("Story missing test task (Task X.Y.T)")
    #     audit_results["recommendations"].append("Create test task: 'Task X.Y.T: Story X.Y Testing and Validation'")
    
    # Check 4: UI document attached (if UI story)
    # is_ui_story = "ui" in story_data.get("subject", "").lower() or "interface" in story_data.get("subject", "").lower()
    # if is_ui_story:
    #     attachments = story_data.get("attachments", [])
    #     ui_doc = next((a for a in attachments if "ui" in a.get("filename", "").lower() or "wireframe" in a.get("filename", "").lower()), None)
    #     if not ui_doc:
    #         audit_results["issues"].append("UI story missing UI design document")
    #         audit_results["recommendations"].append("Attach UI design document: story-X-Y-ui-design.md")
    
    return audit_results


def main():
    """Main audit function."""
    print("=" * 80)
    print("OpenProject Epic and Story Audit")
    print("=" * 80)
    print()
    print("This script audits existing epics and stories against BMAD workflow requirements.")
    print()
    print("Requirements checked:")
    print("1. Epics have comprehensive descriptions")
    print("2. Epics have story breakdowns")
    print("3. Epics have test stories (Story X.T)")
    print("4. Epics have design documents attached")
    print("5. Stories have test tasks (Task X.Y.T)")
    print("6. Stories have UI documents attached (if UI stories)")
    print()
    print("=" * 80)
    print()
    print("⚠️  This is a reference implementation.")
    print("   To run actual audit, implement MCP tool calls:")
    print("   - mcp_openproject_list_work_packages(project_id=8, filters=[...])")
    print("   - mcp_openproject_get_work_package(work_package_id=...)")
    print("   - mcp_openproject_get_work_package_children(parent_id=..., status='all')")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()



