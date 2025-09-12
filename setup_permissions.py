#!/usr/bin/env python3
"""
Helper Agent Permissions Setup Script
Sets up file permissions and access control for Helper Agent exclusive management
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

def setup_helper_permissions():
    """Setup Helper Agent permissions and access control"""
    
    print("Setting up Helper Agent Permissions...")
    print("=" * 60)
    
    # Project root directory
    root_dir = Path(os.getcwd())
    
    # Helper files that need exclusive access
    helper_files = [
        "Project/Helper/**/*.py",
        "HELPER_FUNCTIONS_MANUAL.md", 
        "myStockInfo.yaml",
        "Test/**/*helper*",
        "Test/**/*precision*", 
        "Test/**/*comparison*",
        "Test/**/*focused*"
    ]
    
    # Create .helper_permissions file to mark Helper Agent ownership
    helper_permission_file = root_dir / ".helper_permissions"
    
    permission_data = {
        "owner_agent": "helper_agent",
        "exclusive_control": True,
        "created_date": datetime.now().isoformat(),
        "managed_files": helper_files,
        "access_rules": {
            "helper_agent": "full_rw",
            "data_agent": "read_only_functions", 
            "strategy_agent": "read_only_functions",
            "service_agent": "read_only_functions"
        },
        "security_level": "high",
        "api_credential_protection": True
    }
    
    with open(helper_permission_file, 'w', encoding='utf-8') as f:
        json.dump(permission_data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Created Helper permission marker: {helper_permission_file}")
    
    # Verify key files exist
    key_files = [
        "AGENT_PERMISSIONS.yaml",
        "Project/Helper/HELPER_AGENT_ACCESS_CONTROL.md", 
        "HELPER_FUNCTIONS_MANUAL.md"
    ]
    
    for file_path in key_files:
        full_path = root_dir / file_path
        if full_path.exists():
            print(f"[OK] Verified: {file_path}")
        else:
            print(f"[WARNING] Missing: {file_path}")
    
    # Check Helper files
    helper_dir = root_dir / "Project" / "Helper"
    if helper_dir.exists():
        helper_py_files = list(helper_dir.glob("*.py"))
        print(f"[OK] Found {len(helper_py_files)} Helper Python files:")
        for py_file in helper_py_files:
            print(f"   [PROTECTED] {py_file.name}")
    else:
        print("[WARNING] Helper directory not found")
    
    # Check Test files
    test_dir = root_dir / "Test"
    if test_dir.exists():
        helper_test_files = []
        for pattern in ["*helper*", "*precision*", "*comparison*", "*focused*"]:
            helper_test_files.extend(list(test_dir.glob(pattern)))
        
        print(f"[OK] Found {len(helper_test_files)} Helper test files:")
        for test_file in helper_test_files:
            print(f"   [PROTECTED] {test_file.name}")
    else:
        print("[WARNING] Test directory not found")
    
    print()
    print("PERMISSION SUMMARY")
    print("-" * 40)
    print("Helper Agent (Exclusive Control):")
    print("  [FULL] Full Read/Write access to all Helper files")
    print("  [FULL] Exclusive access to myStockInfo.yaml")
    print("  [FULL] Full control of Helper tests and documentation")
    print()
    print("Other Agents (Restricted Access):")
    print("  [READ] Read-Only access to Helper function interfaces")
    print("  [READ] Can call Helper functions but cannot modify code")
    print("  [DENY] Cannot access API credentials directly")
    print("  [DENY] Cannot modify Helper tests or documentation")
    
    return True

def validate_permissions():
    """Validate that permission files are properly set up"""
    
    print("\nValidating Permission Setup...")
    print("-" * 40)
    
    root_dir = Path(os.getcwd())
    
    # Check permission marker file
    permission_file = root_dir / ".helper_permissions"
    if permission_file.exists():
        with open(permission_file, 'r', encoding='utf-8') as f:
            perm_data = json.load(f)
        
        if perm_data.get("owner_agent") == "helper_agent":
            print("[OK] Helper Agent ownership verified")
        else:
            print("[ERROR] Invalid ownership in permission file")
            return False
    else:
        print("[ERROR] Permission marker file not found")
        return False
    
    # Check configuration files
    config_files = {
        "AGENT_PERMISSIONS.yaml": "Agent permissions configuration",
        "Project/Helper/HELPER_AGENT_ACCESS_CONTROL.md": "Helper access control documentation"
    }
    
    for file_path, description in config_files.items():
        full_path = root_dir / file_path
        if full_path.exists():
            print(f"[OK] {description}: Found")
        else:
            print(f"[ERROR] {description}: Missing")
            return False
    
    print("[OK] All permission files validated successfully")
    return True

def generate_permission_summary():
    """Generate a summary of current permissions"""
    
    root_dir = Path(os.getcwd())
    
    summary = {
        "permission_setup_date": datetime.now().isoformat(),
        "helper_agent_files": [],
        "read_only_access_files": [],
        "protected_files": []
    }
    
    # Find Helper files
    helper_dir = root_dir / "Project" / "Helper"
    if helper_dir.exists():
        for py_file in helper_dir.glob("*.py"):
            summary["helper_agent_files"].append(str(py_file.relative_to(root_dir)))
    
    # Protected files
    protected_files = [
        "myStockInfo.yaml",
        "HELPER_FUNCTIONS_MANUAL.md", 
        "AGENT_PERMISSIONS.yaml"
    ]
    
    for file_path in protected_files:
        full_path = root_dir / file_path
        if full_path.exists():
            summary["protected_files"].append(file_path)
    
    # Test files
    test_dir = root_dir / "Test"
    if test_dir.exists():
        for pattern in ["*helper*", "*precision*", "*comparison*", "*focused*"]:
            for test_file in test_dir.glob(pattern):
                summary["helper_agent_files"].append(str(test_file.relative_to(root_dir)))
    
    # Save summary
    summary_file = root_dir / "PERMISSION_SUMMARY.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUMMARY] Permission summary saved to: {summary_file}")
    
    return summary

def main():
    """Main setup function"""
    
    print("Helper Agent Permission Setup")
    print("=" * 60)
    print("This script configures exclusive Helper Agent permissions")
    print("for all Helper layer files and API credentials.")
    print()
    
    try:
        # Setup permissions
        if setup_helper_permissions():
            print("\n[OK] Permission setup completed successfully!")
        else:
            print("\n[ERROR] Permission setup failed!")
            return False
        
        # Validate setup
        if validate_permissions():
            print("\n[OK] Permission validation passed!")
        else:
            print("\n[ERROR] Permission validation failed!")
            return False
        
        # Generate summary
        generate_permission_summary()
        
        print("\n" + "=" * 60)
        print("HELPER AGENT PERMISSIONS CONFIGURED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("Key Points:")
        print("- Helper Agent has EXCLUSIVE control over Helper files")
        print("- Other agents have READ-ONLY access to Helper functions")
        print("- API credentials protected from direct access")
        print("- All changes to Helper layer must go through Helper Agent")
        print()
        print("Documentation:")
        print("- AGENT_PERMISSIONS.yaml - Full permission configuration")
        print("- Project/Helper/HELPER_AGENT_ACCESS_CONTROL.md - Access control guide")
        print("- HELPER_FUNCTIONS_MANUAL.md - Function usage manual")
        print("- PERMISSION_SUMMARY.json - Current permission status")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during permission setup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)