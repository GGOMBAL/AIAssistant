import yaml
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentManagementSystem:
    """Manual management system for multi-agent collaboration"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.interfaces_config = None
        self.file_ownership_config = None
        self.collaboration_matrix = None
        self.load_configurations()
        
    def load_configurations(self):
        """Load all configuration files"""
        try:
            # Load agent interfaces
            with open(self.config_dir / "agent_interfaces.yaml", 'r') as f:
                self.interfaces_config = yaml.safe_load(f)
                
            # Load file ownership
            with open(self.config_dir / "file_ownership.yaml", 'r') as f:
                self.file_ownership_config = yaml.safe_load(f)
                
            # Load collaboration matrix
            with open(self.config_dir / "collaboration_matrix.yaml", 'r') as f:
                self.collaboration_matrix = yaml.safe_load(f)
                
            logger.info("All configuration files loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise
    
    def get_agent_collaborators(self, agent_name: str) -> Dict[str, Any]:
        """Get all collaborators for a specific agent"""
        if agent_name not in self.interfaces_config:
            return {"error": f"Agent {agent_name} not found"}
        
        collaborators = self.interfaces_config[agent_name].get("collaborates_with", [])
        return {
            "agent": agent_name,
            "collaborators": collaborators,
            "total_collaborators": len(collaborators)
        }
    
    def get_agent_managed_files(self, agent_name: str) -> Dict[str, Any]:
        """Get all files managed by a specific agent"""
        if agent_name not in self.interfaces_config:
            return {"error": f"Agent {agent_name} not found"}
        
        managed_files = self.interfaces_config[agent_name].get("managed_files", [])
        return {
            "agent": agent_name,
            "managed_files": managed_files,
            "total_files": len(managed_files)
        }
    
    def get_file_owner(self, file_path: str) -> Dict[str, Any]:
        """Find which agent owns a specific file"""
        ownership = self.file_ownership_config.get("file_ownership", {})
        
        for category, data in ownership.items():
            owner = data.get("owner")
            files = data.get("files", [])
            
            for file_info in files:
                if file_info.get("path") == file_path:
                    return {
                        "file_path": file_path,
                        "owner": owner,
                        "permissions": file_info.get("permissions", []),
                        "description": file_info.get("description", "")
                    }
        
        return {"error": f"File {file_path} ownership not found"}
    
    def get_shared_access(self, file_path: str) -> Dict[str, Any]:
        """Get shared access information for a file"""
        ownership = self.file_ownership_config.get("file_ownership", {})
        
        for category, data in ownership.items():
            files = data.get("files", [])
            
            for file_info in files:
                if file_info.get("path") == file_path:
                    shared_access = data.get("shared_access", [])
                    
                    relevant_access = []
                    for access in shared_access:
                        if file_path in access.get("files", []):
                            relevant_access.append(access)
                    
                    return {
                        "file_path": file_path,
                        "owner": data.get("owner"),
                        "shared_access": relevant_access
                    }
        
        return {"error": f"File {file_path} not found"}
    
    def get_collaboration_details(self, agent1: str, agent2: str) -> Dict[str, Any]:
        """Get collaboration details between two agents"""
        matrix = self.collaboration_matrix.get("collaboration_matrix", {})
        
        if agent1 not in matrix:
            return {"error": f"Agent {agent1} not found in collaboration matrix"}
        
        agent1_collabs = matrix[agent1]
        
        # Check primary collaborations
        for collab in agent1_collabs.get("primary_collaborations", []):
            if collab.get("partner") == agent2:
                return {
                    "agent1": agent1,
                    "agent2": agent2,
                    "collaboration_type": "primary",
                    "details": collab
                }
        
        # Check secondary collaborations
        for collab in agent1_collabs.get("secondary_collaborations", []):
            if collab.get("partner") == agent2:
                return {
                    "agent1": agent1,
                    "agent2": agent2,
                    "collaboration_type": "secondary",
                    "details": collab
                }
        
        return {"error": f"No collaboration found between {agent1} and {agent2}"}
    
    def validate_agent_setup(self, agent_name: str) -> Dict[str, Any]:
        """Validate that an agent is properly configured"""
        issues = []
        
        # Check if agent exists in interfaces
        if agent_name not in self.interfaces_config:
            issues.append(f"Agent {agent_name} not found in interfaces config")
            return {"agent": agent_name, "valid": False, "issues": issues}
        
        # Check managed files exist
        managed_files = self.interfaces_config[agent_name].get("managed_files", [])
        for file_path in managed_files:
            if not Path(file_path).exists():
                issues.append(f"Managed file {file_path} does not exist")
        
        # Check collaborators are valid
        collaborators = self.interfaces_config[agent_name].get("collaborates_with", [])
        for collab in collaborators:
            partner = collab.get("agent")
            if partner not in self.interfaces_config:
                issues.append(f"Collaborator {partner} not found in interfaces")
        
        # Check file ownership consistency
        ownership_files = []
        ownership = self.file_ownership_config.get("file_ownership", {})
        for category, data in ownership.items():
            if data.get("owner") == agent_name:
                ownership_files.extend([f.get("path") for f in data.get("files", [])])
        
        for managed_file in managed_files:
            if managed_file not in ownership_files:
                issues.append(f"Managed file {managed_file} not in ownership config")
        
        return {
            "agent": agent_name,
            "valid": len(issues) == 0,
            "issues": issues,
            "managed_files_count": len(managed_files),
            "collaborators_count": len(collaborators)
        }
    
    def generate_agent_report(self, agent_name: str) -> Dict[str, Any]:
        """Generate comprehensive report for an agent"""
        report = {
            "agent_name": agent_name,
            "generated_at": datetime.now().isoformat(),
            "validation": self.validate_agent_setup(agent_name),
            "collaborators": self.get_agent_collaborators(agent_name),
            "managed_files": self.get_agent_managed_files(agent_name)
        }
        
        # Add collaboration matrix details
        matrix = self.collaboration_matrix.get("collaboration_matrix", {})
        if agent_name in matrix:
            report["collaboration_matrix"] = matrix[agent_name]
        
        return report
    
    def update_agent_collaborator(self, agent_name: str, partner_name: str, 
                                 collaboration_details: Dict[str, Any]):
        """Update collaboration details between agents"""
        if agent_name not in self.interfaces_config:
            return {"error": f"Agent {agent_name} not found"}
        
        collaborators = self.interfaces_config[agent_name].get("collaborates_with", [])
        
        # Find existing collaboration
        for i, collab in enumerate(collaborators):
            if collab.get("agent") == partner_name:
                collaborators[i].update(collaboration_details)
                break
        else:
            # Add new collaboration
            new_collab = {"agent": partner_name, **collaboration_details}
            collaborators.append(new_collab)
        
        # Save updated config
        self._save_interfaces_config()
        
        return {"success": f"Updated collaboration between {agent_name} and {partner_name}"}
    
    def add_managed_file(self, agent_name: str, file_path: str, description: str = ""):
        """Add a new managed file to an agent"""
        if agent_name not in self.interfaces_config:
            return {"error": f"Agent {agent_name} not found"}
        
        managed_files = self.interfaces_config[agent_name].get("managed_files", [])
        
        if file_path not in managed_files:
            managed_files.append(file_path)
            self._save_interfaces_config()
            
            # Also add to file ownership
            self._add_file_to_ownership(agent_name, file_path, description)
            
            return {"success": f"Added {file_path} to {agent_name} managed files"}
        
        return {"info": f"File {file_path} already managed by {agent_name}"}
    
    def _add_file_to_ownership(self, owner: str, file_path: str, description: str):
        """Add file to ownership configuration"""
        ownership = self.file_ownership_config.get("file_ownership", {})
        
        # Find the appropriate category for this agent
        for category, data in ownership.items():
            if data.get("owner") == owner:
                files = data.get("files", [])
                files.append({
                    "path": file_path,
                    "permissions": ["read", "write", "execute"],
                    "description": description
                })
                break
        
        self._save_ownership_config()
    
    def _save_interfaces_config(self):
        """Save interfaces configuration to file"""
        try:
            with open(self.config_dir / "agent_interfaces.yaml", 'w') as f:
                yaml.dump(self.interfaces_config, f, default_flow_style=False)
            logger.info("Interfaces configuration saved")
        except Exception as e:
            logger.error(f"Error saving interfaces config: {e}")
    
    def _save_ownership_config(self):
        """Save ownership configuration to file"""
        try:
            with open(self.config_dir / "file_ownership.yaml", 'w') as f:
                yaml.dump(self.file_ownership_config, f, default_flow_style=False)
            logger.info("Ownership configuration saved")
        except Exception as e:
            logger.error(f"Error saving ownership config: {e}")
    
    def list_all_agents(self) -> List[str]:
        """List all configured agents"""
        # Filter to only return the 4 core agents
        core_agents = ["data_agent", "strategy_agent", "service_agent", "helper_agent"]
        return [agent for agent in self.interfaces_config.keys() if agent in core_agents]
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get overview of entire multi-agent system"""
        agents = self.list_all_agents()
        
        total_files = 0
        total_collaborations = 0
        
        for agent in agents:
            managed_files = len(self.interfaces_config[agent].get("managed_files", []))
            collaborators = len(self.interfaces_config[agent].get("collaborates_with", []))
            
            total_files += managed_files
            total_collaborations += collaborators
        
        return {
            "total_agents": len(agents),
            "agents": agents,
            "total_managed_files": total_files,
            "total_collaborations": total_collaborations,
            "configuration_files": [
                "agent_interfaces.yaml",
                "file_ownership.yaml", 
                "collaboration_matrix.yaml"
            ]
        }

# CLI Interface for manual management
class AgentManagementCLI:
    def __init__(self):
        self.management_system = AgentManagementSystem()
    
    def interactive_menu(self):
        """Interactive menu for agent management"""
        while True:
            print("\n=== Agent Management System ===")
            print("1. List all agents")
            print("2. Get agent details")
            print("3. Validate agent setup")
            print("4. Get file owner")
            print("5. Check collaboration")
            print("6. System overview")
            print("7. Add managed file")
            print("8. Update collaboration")
            print("0. Exit")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "0":
                break
            elif choice == "1":
                self._list_agents()
            elif choice == "2":
                self._get_agent_details()
            elif choice == "3":
                self._validate_agent()
            elif choice == "4":
                self._get_file_owner()
            elif choice == "5":
                self._check_collaboration()
            elif choice == "6":
                self._system_overview()
            elif choice == "7":
                self._add_managed_file()
            elif choice == "8":
                self._update_collaboration()
            else:
                print("Invalid choice. Please try again.")
    
    def _list_agents(self):
        agents = self.management_system.list_all_agents()
        print(f"\nConfigured Agents ({len(agents)}):")
        for i, agent in enumerate(agents, 1):
            print(f"{i}. {agent}")
    
    def _get_agent_details(self):
        agent_name = input("Enter agent name: ")
        report = self.management_system.generate_agent_report(agent_name)
        print(json.dumps(report, indent=2))
    
    def _validate_agent(self):
        agent_name = input("Enter agent name to validate: ")
        validation = self.management_system.validate_agent_setup(agent_name)
        print(json.dumps(validation, indent=2))
    
    def _get_file_owner(self):
        file_path = input("Enter file path: ")
        owner_info = self.management_system.get_file_owner(file_path)
        print(json.dumps(owner_info, indent=2))
    
    def _check_collaboration(self):
        agent1 = input("Enter first agent name: ")
        agent2 = input("Enter second agent name: ")
        collab_details = self.management_system.get_collaboration_details(agent1, agent2)
        print(json.dumps(collab_details, indent=2))
    
    def _system_overview(self):
        overview = self.management_system.get_system_overview()
        print(json.dumps(overview, indent=2))
    
    def _add_managed_file(self):
        agent_name = input("Enter agent name: ")
        file_path = input("Enter file path: ")
        description = input("Enter file description (optional): ")
        result = self.management_system.add_managed_file(agent_name, file_path, description)
        print(json.dumps(result, indent=2))
    
    def _update_collaboration(self):
        agent_name = input("Enter agent name: ")
        partner_name = input("Enter partner agent name: ")
        purpose = input("Enter collaboration purpose: ")
        interface = input("Enter interface name: ")
        
        collab_details = {
            "purpose": purpose,
            "interface": interface,
            "required_data": input("Enter required data (comma-separated): ").split(",")
        }
        
        result = self.management_system.update_agent_collaborator(
            agent_name, partner_name, collab_details
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    cli = AgentManagementCLI()
    cli.interactive_menu()