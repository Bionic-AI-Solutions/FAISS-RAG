#!/usr/bin/env python3
"""
BMAD Project Setup Script

This script helps configure BMAD projects with OpenProject and Archon integrations.

Usage:
    python scripts/bmad-setup.py init              # Interactive project initialization
    python scripts/bmad-setup.py generate-claude-md # Regenerate CLAUDE.md from config
    python scripts/bmad-setup.py validate          # Validate current configuration
    python scripts/bmad-setup.py show-config       # Display current configuration
"""

import argparse
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Project root detection
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Configuration paths
CONFIG_PATH = PROJECT_ROOT / "_bmad" / "_config" / "project-config.yaml"
TEMPLATE_PATH = PROJECT_ROOT / "_bmad" / "templates" / "CLAUDE.md.template"
CLAUDE_MD_PATH = PROJECT_ROOT / "CLAUDE.md"
OUTPUT_DIR = PROJECT_ROOT / "_bmad-output"


def load_config():
    """Load project configuration from YAML file."""
    if not CONFIG_PATH.exists():
        print(f"❌ Configuration file not found: {CONFIG_PATH}")
        print("   Run 'python scripts/bmad-setup.py init' to create it.")
        return None
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def save_config(config):
    """Save configuration to YAML file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Configuration saved to {CONFIG_PATH}")


def generate_claude_md():
    """Generate CLAUDE.md from template using current configuration."""
    config = load_config()
    if not config:
        return False
    
    if not TEMPLATE_PATH.exists():
        print(f"❌ Template file not found: {TEMPLATE_PATH}")
        return False
    
    with open(TEMPLATE_PATH, 'r') as f:
        template = f.read()
    
    # Build replacement map from config
    op = config.get('openproject', {})
    ar = config.get('archon', {})
    wf = config.get('workflows', {})
    
    replacements = {
        '{{PROJECT_NAME}}': config.get('project', {}).get('display_name', 'Unknown Project'),
        '{{OPENPROJECT_PROJECT_ID}}': str(op.get('project_id', 'NOT_CONFIGURED')),
        '{{ARCHON_PROJECT_ID}}': str(ar.get('project_id', 'NOT_CONFIGURED')),
        
        # Types
        '{{TYPE_EPIC}}': str(op.get('types', {}).get('epic', 40)),
        '{{TYPE_FEATURE}}': str(op.get('types', {}).get('feature', 39)),
        '{{TYPE_USER_STORY}}': str(op.get('types', {}).get('user_story', 41)),
        '{{TYPE_TASK}}': str(op.get('types', {}).get('task', 36)),
        '{{TYPE_BUG}}': str(op.get('types', {}).get('bug', 42)),
        
        # Statuses
        '{{STATUS_NEW}}': str(op.get('statuses', {}).get('new', 71)),
        '{{STATUS_IN_PROGRESS}}': str(op.get('statuses', {}).get('in_progress', 77)),
        '{{STATUS_IN_TESTING}}': str(op.get('statuses', {}).get('in_testing', 79)),
        '{{STATUS_CLOSED}}': str(op.get('statuses', {}).get('closed', 82)),
        '{{STATUS_ON_HOLD}}': str(op.get('statuses', {}).get('on_hold', 83)),
        
        # Priorities
        '{{PRIORITY_LOW}}': str(op.get('priorities', {}).get('low', 72)),
        '{{PRIORITY_NORMAL}}': str(op.get('priorities', {}).get('normal', 73)),
        '{{PRIORITY_HIGH}}': str(op.get('priorities', {}).get('high', 74)),
        '{{PRIORITY_IMMEDIATE}}': str(op.get('priorities', {}).get('immediate', 75)),
        
        # Workflows
        '{{STORY_MIN_HOURS}}': str(wf.get('story_min_hours', 0.5)),
        '{{STORY_MAX_HOURS}}': str(wf.get('story_max_hours', 4)),
    }
    
    # Apply replacements
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    # Write output
    with open(CLAUDE_MD_PATH, 'w') as f:
        f.write(result)
    
    print(f"✅ Generated {CLAUDE_MD_PATH}")
    return True


def validate_config():
    """Validate the current configuration."""
    config = load_config()
    if not config:
        return False
    
    issues = []
    warnings = []
    
    # Check required fields
    if not config.get('project', {}).get('name'):
        issues.append("project.name is not set")
    
    op = config.get('openproject', {})
    if op.get('enabled', True):
        if not op.get('project_id'):
            issues.append("openproject.project_id is not set")
        if not op.get('types', {}).get('epic'):
            warnings.append("openproject.types.epic not configured (using default)")
    
    ar = config.get('archon', {})
    if ar.get('enabled', True):
        if not ar.get('project_id'):
            issues.append("archon.project_id is not set")
    
    # Display results
    print("\n" + "=" * 60)
    print("BMAD Configuration Validation")
    print("=" * 60)
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not issues and not warnings:
        print("\n✅ Configuration is valid!")
    
    print("\n" + "=" * 60)
    
    return len(issues) == 0


def show_config():
    """Display current configuration."""
    config = load_config()
    if not config:
        return
    
    print("\n" + "=" * 60)
    print("Current BMAD Configuration")
    print("=" * 60)
    print(yaml.dump(config, default_flow_style=False, sort_keys=False))
    print("=" * 60)


def init_project():
    """Interactive project initialization."""
    print("\n" + "=" * 60)
    print("BMAD Project Initialization")
    print("=" * 60)
    print("\nThis wizard will help you set up your BMAD project.\n")
    
    # Load existing config or create new
    if CONFIG_PATH.exists():
        print(f"⚠️  Existing configuration found at {CONFIG_PATH}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
    
    config = {
        'project': {},
        'team': {},
        'paths': {},
        'openproject': {'enabled': True},
        'archon': {'enabled': True},
        'testing': {},
        'workflows': {},
        'custom': {}
    }
    
    # Project info
    print("\n--- Project Information ---")
    config['project']['name'] = input("Project name (kebab-case): ").strip()
    config['project']['display_name'] = input("Display name: ").strip()
    config['project']['description'] = input("Description: ").strip()
    config['project']['github_repo'] = input("GitHub repo URL (optional): ").strip()
    
    # Team info
    print("\n--- Team Information ---")
    config['team']['user_name'] = input("Your name/alias: ").strip()
    config['team']['user_skill_level'] = "intermediate"
    config['team']['communication_language'] = "English"
    config['team']['document_output_language'] = "English"
    
    # Paths
    config['paths']['output_folder'] = "{project-root}/_bmad-output"
    config['paths']['planning_artifacts'] = "{project-root}/_bmad-output/planning-artifacts"
    config['paths']['implementation_artifacts'] = "{project-root}/_bmad-output/implementation-artifacts"
    config['paths']['project_knowledge'] = "{project-root}/docs"
    
    # OpenProject
    print("\n--- OpenProject Configuration ---")
    print("You'll need to get these values from OpenProject.")
    print("Run these MCP commands to find them:")
    print("  - mcp_openproject_list_projects()")
    print("  - mcp_openproject_list_types(project_id=X)")
    print("  - mcp_openproject_list_statuses()")
    print("")
    
    op_id = input("OpenProject project_id (or 'skip'): ").strip()
    if op_id.lower() != 'skip':
        config['openproject']['project_id'] = int(op_id) if op_id.isdigit() else None
    else:
        config['openproject']['project_id'] = None
        print("⚠️  OpenProject not configured. Update project-config.yaml later.")
    
    # Set defaults for types/statuses/priorities
    config['openproject']['types'] = {
        'epic': 40,
        'feature': 39,
        'user_story': 41,
        'task': 36,
        'bug': 42,
        'milestone': 37
    }
    config['openproject']['statuses'] = {
        'new': 71,
        'in_specification': 72,
        'specified': 73,
        'confirmed': 74,
        'to_be_scheduled': 75,
        'scheduled': 76,
        'in_progress': 77,
        'developed': 78,
        'in_testing': 79,
        'tested': 80,
        'test_failed': 81,
        'closed': 82,
        'on_hold': 83,
        'rejected': 84
    }
    config['openproject']['priorities'] = {
        'low': 72,
        'normal': 73,
        'high': 74,
        'immediate': 75
    }
    config['openproject']['workflow'] = {
        'default_status': 71,
        'start_work_status': 77,
        'review_status': 79,
        'complete_status': 82
    }
    
    # Archon
    print("\n--- Archon Configuration ---")
    print("You'll need the Archon project UUID.")
    print("Run: mcp_archon_find_projects() or create with mcp_archon_manage_project()")
    print("")
    
    ar_id = input("Archon project_id UUID (or 'skip'): ").strip()
    if ar_id.lower() != 'skip' and ar_id:
        config['archon']['project_id'] = ar_id
    else:
        config['archon']['project_id'] = None
        print("⚠️  Archon not configured. Update project-config.yaml later.")
    
    config['archon']['rag'] = {
        'default_match_count': 5,
        'code_examples_match_count': 3,
        'preferred_sources': []
    }
    
    # Testing
    config['testing'] = {
        'tea_use_mcp_enhancements': False,
        'tea_use_playwright_utils': False
    }
    
    # Workflows
    config['workflows'] = {
        'story_min_hours': 0.5,
        'story_max_hours': 4,
        'sprint_duration_days': 14,
        'require_acceptance_criteria': True,
        'require_technical_notes': True
    }
    
    # Save config
    save_config(config)
    
    # Create directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "planning-artifacts").mkdir(exist_ok=True)
    (OUTPUT_DIR / "implementation-artifacts").mkdir(exist_ok=True)
    print(f"✅ Created output directories")
    
    # Generate CLAUDE.md
    print("\nGenerating CLAUDE.md...")
    generate_claude_md()
    
    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"""
Files created/updated:
  ✅ {CONFIG_PATH}
  ✅ {CLAUDE_MD_PATH}
  ✅ {OUTPUT_DIR}/planning-artifacts/
  ✅ {OUTPUT_DIR}/implementation-artifacts/

Next steps:
  1. Review {CONFIG_PATH}
  2. Update type/status/priority IDs if needed
  3. Start with @bmad/bmm/agents/pm for product brief
""")


def main():
    parser = argparse.ArgumentParser(
        description="BMAD Project Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  init              Interactive project initialization
  generate-claude-md  Regenerate CLAUDE.md from config
  validate          Validate current configuration
  show-config       Display current configuration
        """
    )
    parser.add_argument('command', choices=['init', 'generate-claude-md', 'validate', 'show-config'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_project()
    elif args.command == 'generate-claude-md':
        generate_claude_md()
    elif args.command == 'validate':
        sys.exit(0 if validate_config() else 1)
    elif args.command == 'show-config':
        show_config()


if __name__ == '__main__':
    main()






