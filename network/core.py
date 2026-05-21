import json
import sys
from pathlib import Path

class AgentRunner:
    """
    Base class for MayaOS Agent standalone runners.
    Reduces code duplication across invoke_*.py scripts.
    """
    def __init__(self, agent_id: str, role_title: str):
        self.agent_id = agent_id
        self.role_title = role_title
        self.root = Path(__file__).resolve().parent.parent
        self.agent_dir = self.root / "agents" / agent_id
        self.state_dir = self.root / "state"

    def load_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def save_json(self, path: Path, data):
        # A central place to implement atomic writes or locks in the future.
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def update_history(self, entry: dict):
        history_path = self.agent_dir / "history.json"
        history = self.load_json(history_path)
        history.append(entry)
        self.save_json(history_path, history)

    def update_state(self, updates: dict):
        state_path = self.agent_dir / "state.json"
        state = self.load_json(state_path)
        state.update(updates)
        self.save_json(state_path, state)

    def build_boot_prompt(self, user_message: str, custom_blocks: list = None) -> str:
        persona = self.load_text(self.agent_dir / "persona.md")
        state = self.load_json(self.agent_dir / "state.json")
        history = self.load_json(self.agent_dir / "history.json")
        
        system_mode = {}
        if (self.state_dir / "system_mode.json").exists():
            system_mode = self.load_json(self.state_dir / "system_mode.json")
            
        user_state = {}
        if (self.state_dir / "user_state.json").exists():
            user_state = self.load_json(self.state_dir / "user_state.json")

        parts = []
        parts.append("=" * 72)
        parts.append(f"AGENT BOOT — {self.agent_id.upper()} ({self.role_title})")
        parts.append("=" * 72)
        parts.append("")
        parts.append("# PERSONA")
        parts.append(persona)
        parts.append("")
        
        if custom_blocks:
            parts.extend(custom_blocks)
            parts.append("")

        parts.append("# CURRENT STATE")
        parts.append("```json")
        parts.append(json.dumps(state, indent=2, ensure_ascii=False))
        parts.append("```")
        parts.append("")
        parts.append("# HISTORY (most recent first)")
        parts.append("```json")
        parts.append(json.dumps(list(reversed(history))[:10], indent=2, ensure_ascii=False))
        parts.append("```")
        parts.append("")
        parts.append("# SYSTEM CONTEXT")
        parts.append("```json")
        parts.append(json.dumps({
            "system_mode": system_mode,
            "user_state": user_state,
        }, indent=2, ensure_ascii=False))
        parts.append("```")
        parts.append("")
        parts.append("# USER MESSAGE")
        parts.append(user_message)
        parts.append("")
        parts.append("=" * 72)
        parts.append(f"Respond in {self.agent_id.capitalize()}'s strict format. Do not exceed it.")
        parts.append("=" * 72)
        return "\n".join(parts)
