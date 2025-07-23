#!/usr/bin/env python3
"""
Validate GitHub Actions workflow files
"""

from pathlib import Path

import yaml


def validate_workflow_file(file_path):
    """Validate a single workflow file"""
    try:
        with open(file_path, "r") as f:
            workflow = yaml.safe_load(f)

        # Check required fields
        required_fields = ["name", "jobs"]
        for field in required_fields:
            if field not in workflow:
                return False, f"Missing required field: {field}"

        # Check for 'on' field (which might be parsed as True boolean)
        if "on" not in workflow and True not in workflow:
            return False, "Missing required field: on"

        # Check that jobs have required fields
        for job_name, job_config in workflow["jobs"].items():
            if "runs-on" not in job_config:
                return False, f"Job {job_name} missing 'runs-on'"
            if "steps" not in job_config:
                return False, f"Job {job_name} missing 'steps'"

        return True, "Valid workflow file"

    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main validation function"""
    workflows_dir = Path(__file__).parent / "workflows"

    if not workflows_dir.exists():
        print("❌ Workflows directory not found")
        return 1

    workflow_files = list(workflows_dir.glob("*.yml"))

    if not workflow_files:
        print("❌ No workflow files found")
        return 1

    print(f"🔍 Found {len(workflow_files)} workflow files:")

    all_valid = True
    for workflow_file in workflow_files:
        is_valid, message = validate_workflow_file(workflow_file)

        if is_valid:
            print(f"✅ {workflow_file.name}: {message}")
        else:
            print(f"❌ {workflow_file.name}: {message}")
            all_valid = False

    if all_valid:
        print("\n🎉 All workflow files are valid!")
        return 0
    else:
        print("\n❌ Some workflow files have issues")
        return 1


if __name__ == "__main__":
    exit(main())
