import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone


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


# ══════════════════════════════════════════════════════════════════
# MessageBus — Inter-Agent Messaging (COWORK)
# ══════════════════════════════════════════════════════════════════

class MessageBus:
    """
    Handles inter-agent messaging via inbox/outbox JSON files.
    All messages are validated against network/hierarchy.json before routing.
    Trigger-based only — no autonomous loops.
    """

    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent
        self.network_dir = Path(__file__).resolve().parent
        self.agents_dir = self.root / "agents"
        self.hierarchy_path = self.network_dir / "hierarchy.json"
        self.log_path = self.network_dir / "message_log.json"

    # ── Hierarchy ──────────────────────────────────────────────────

    def get_hierarchy(self, agent: str) -> dict:
        """Return hierarchy entry for agent."""
        h = json.loads(self.hierarchy_path.read_text(encoding="utf-8"))
        if agent not in h:
            raise ValueError(f"Unknown agent: '{agent}'. Check hierarchy.json.")
        return h[agent]

    def can_message(self, from_agent: str, to_agent: str) -> bool:
        """
        Returns True if from_agent is allowed to message to_agent.
        Rules:
          UP   — to direct superior (reports_to)
          DOWN — to direct report (direct_reports)
          CROSS — to agent in cross_links
          BROADCAST — only tier-0 (maya) to 'broadcast'
        """
        if to_agent == "broadcast":
            src = self.get_hierarchy(from_agent)
            return src.get("tier", 99) == 0

        h = json.loads(self.hierarchy_path.read_text(encoding="utf-8"))
        if from_agent not in h or to_agent not in h:
            return False

        src = h[from_agent]
        allowed = set()
        if src.get("reports_to"):
            allowed.add(src["reports_to"])
        allowed.update(src.get("direct_reports", []))
        allowed.update(src.get("cross_links", []))
        return to_agent in allowed

    # ── Core send/receive ──────────────────────────────────────────

    def send(
        self,
        from_agent: str,
        to_agent: str,
        intent: str,
        data: dict = None,
        msg_type: str = "request",
        confidence: str = "medium",
        requires_response: bool = False,
        context_refs: list = None,
    ) -> str:
        """
        Write message to target agent's inbox.json.
        Validates routing permissions first.
        Returns msg_id.
        """
        if not self.can_message(from_agent, to_agent):
            raise PermissionError(
                f"COWORK: '{from_agent}' → '{to_agent}' is not an allowed route. "
                f"Check hierarchy.json for valid UP/DOWN/CROSS links."
            )

        msg_id = str(uuid.uuid4())[:8]
        msg = {
            "msg_id": msg_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": msg_type,
            "payload": {
                "intent": intent,
                "data": data or {},
                "context_refs": context_refs or [],
            },
            "confidence_level": confidence,
            "requires_response": requires_response,
            "status": "delivered",
        }

        # Write to recipient inbox
        if to_agent != "broadcast":
            inbox_path = self.agents_dir / to_agent / "inbox.json"
            inbox = self._load_or_empty(inbox_path)
            inbox.append(msg)
            self._save_json(inbox_path, inbox)
        else:
            # Broadcast: write to all agents' inboxes
            h = json.loads(self.hierarchy_path.read_text(encoding="utf-8"))
            for agent_name in h:
                if agent_name == from_agent:
                    continue
                inbox_path = self.agents_dir / agent_name / "inbox.json"
                if inbox_path.exists():
                    inbox = self._load_or_empty(inbox_path)
                    inbox.append({**msg, "to": agent_name})
                    self._save_json(inbox_path, inbox)

        # Log it
        self.log(msg, "delivered")
        return msg_id

    def read_inbox(self, agent: str) -> list:
        """Return all messages from agent's inbox.json."""
        inbox_path = self.agents_dir / agent / "inbox.json"
        return self._load_or_empty(inbox_path)

    def read_unread(self, agent: str) -> list:
        """Return only unread (non-'read') messages."""
        return [m for m in self.read_inbox(agent) if m.get("status") != "read"]

    def mark_read(self, agent: str, msg_id: str):
        """Mark a specific message as read in the agent's inbox."""
        inbox_path = self.agents_dir / agent / "inbox.json"
        inbox = self._load_or_empty(inbox_path)
        for msg in inbox:
            if msg.get("msg_id") == msg_id:
                msg["status"] = "read"
                break
        self._save_json(inbox_path, inbox)

    def mark_all_read(self, agent: str):
        """Mark all inbox messages as read."""
        inbox_path = self.agents_dir / agent / "inbox.json"
        inbox = self._load_or_empty(inbox_path)
        for msg in inbox:
            msg["status"] = "read"
        self._save_json(inbox_path, inbox)

    def reply(self, original_msg: dict, from_agent: str, data: dict, intent: str = "response"):
        """Write a reply to the original sender's inbox."""
        return self.send(
            from_agent=from_agent,
            to_agent=original_msg["from"],
            intent=intent,
            data=data,
            msg_type="response",
            requires_response=False,
            context_refs=[original_msg["msg_id"]],
        )

    def write_outbox(self, agent: str, msg: dict):
        """Append a message record to agent's outbox.json."""
        outbox_path = self.agents_dir / agent / "outbox.json"
        outbox = self._load_or_empty(outbox_path)
        outbox.append(msg)
        self._save_json(outbox_path, outbox)

    def log(self, msg: dict, status: str = "delivered"):
        """Append a compact log entry to network/message_log.json."""
        log_entry = {
            "msg_id": msg.get("msg_id"),
            "timestamp": msg.get("timestamp"),
            "from": msg.get("from"),
            "to": msg.get("to"),
            "intent": msg.get("payload", {}).get("intent"),
            "summary": str(msg.get("payload", {}).get("data", ""))[:120],
            "status": status,
        }
        log = self._load_or_empty(self.log_path)
        log.append(log_entry)
        self._save_json(self.log_path, log)

    def update_log_status(self, msg_id: str, status: str):
        """Update status of an existing log entry."""
        log = self._load_or_empty(self.log_path)
        for entry in log:
            if entry.get("msg_id") == msg_id:
                entry["status"] = status
                break
        self._save_json(self.log_path, log)

    def get_log(self, limit: int = 20) -> list:
        """Return recent log entries (most recent first)."""
        log = self._load_or_empty(self.log_path)
        return list(reversed(log))[:limit]

    def agent_status(self, agent: str) -> dict:
        """Return a status summary for an agent."""
        inbox = self.read_inbox(agent)
        unread = [m for m in inbox if m.get("status") != "read"]
        state_path = self.agents_dir / agent / "state.json"
        state = {}
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        h_entry = {}
        try:
            h_entry = self.get_hierarchy(agent)
        except ValueError:
            pass
        return {
            "agent": agent,
            "tier": h_entry.get("tier"),
            "division": h_entry.get("division"),
            "inbox_total": len(inbox),
            "inbox_unread": len(unread),
            "unread_messages": unread,
            "state_summary": {
                k: v for k, v in state.items()
                if k in ("system_mode", "last_invoked", "active_blockers")
            },
        }

    def _load_or_empty(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_json(self, path: Path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
