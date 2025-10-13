"""
Verify 5 Sub-Agents Configuration
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from orchestrator.hybrid_model_manager import HybridModelManager
from orchestrator.prompt_generator import PromptGenerator

print("="*70)
print("  5 Sub-Agents Configuration Verification")
print("="*70)

# 1. Check HybridModelManager
print("\n[1] HybridModelManager Agent List:")
print("-"*70)
manager = HybridModelManager()
agent_models = manager.agent_models

sub_agents = [name for name in agent_models.keys() if name != 'orchestrator']
print(f"\nSub-Agents detected: {len(sub_agents)}")
for i, agent_name in enumerate(sorted(sub_agents), 1):
    model_info = agent_models[agent_name]
    print(f"{i}. {agent_name}")
    print(f"   Provider: {model_info['provider'].value}")
    print(f"   Model ID: {model_info['model_id']}")

# 2. Check PromptGenerator
print("\n[2] PromptGenerator Agent Templates:")
print("-"*70)
generator = PromptGenerator()
templates = generator.agent_templates

agent_names = list(templates.keys())
print(f"\nAgent templates available: {len(agent_names)}")
for i, agent_name in enumerate(sorted(agent_names), 1):
    print(f"{i}. {agent_name}")

# 3. Summary
print("\n"+"="*70)
print("SUMMARY:")
print("="*70)
if 'run_agent' in agent_models:
    print("[OK] run_agent is in HybridModelManager")
else:
    print("[FAIL] run_agent is NOT in HybridModelManager")

if 'run_agent' in templates:
    print("[OK] run_agent is in PromptGenerator")
else:
    print("[FAIL] run_agent is NOT in PromptGenerator")

if len(sub_agents) == 5:
    print(f"\n[SUCCESS] All 5 sub-agents are configured!")
    print(f"Agents: {', '.join(sorted(sub_agents))}")
else:
    print(f"\n[WARNING] Expected 5 sub-agents, found {len(sub_agents)}")
    print(f"Agents: {', '.join(sorted(sub_agents))}")

print("="*70)
