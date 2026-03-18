"""
记忆系统 - 对话历史管理
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    role: str  # "user", "assistant", "tool_result"
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    tool_use_id: Optional[str] = None
    tool_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_use_id": self.tool_use_id,
            "tool_name": self.tool_name
        }


class Memory:
    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.task_context: Dict[str, Any] = {}
        self.completed_steps: List[str] = []
        self.iteration_count: int = 0

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))
        self._compress_if_needed()

    def add_assistant_message(self, content: Any):
        self.messages.append(Message(role="assistant", content=content))
        self._compress_if_needed()

    def add_tool_result(self, tool_use_id: str, tool_name: str, result: str):
        self.messages.append(Message(
            role="user",
            content=[{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result
            }],
            tool_use_id=tool_use_id,
            tool_name=tool_name
        ))

    def get_claude_messages(self) -> List[Dict[str, Any]]:
        claude_messages = []

        for msg in self.messages:
            if msg.role == "user":
                if isinstance(msg.content, list):
                    claude_messages.append({
                        "role": "user",
                        "content": msg.content
                    })
                else:
                    claude_messages.append({
                        "role": "user",
                        "content": msg.content
                    })
            elif msg.role == "assistant":
                claude_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })

        return claude_messages

    def add_completed_step(self, step: str):
        self.completed_steps.append(step)

    def get_context_summary(self) -> str:
        summary = []
        if self.task_context:
            summary.append(f"Task: {self.task_context.get('task', 'N/A')}")
        if self.completed_steps:
            summary.append(f"Steps: {len(self.completed_steps)}")
        summary.append(f"Iterations: {self.iteration_count}")
        return " | ".join(summary)

    def _compress_if_needed(self):
        if len(self.messages) > self.max_messages:
            keep_count = int(self.max_messages * 0.8)
            self.messages = self.messages[-keep_count:]

    def clear(self):
        self.messages = []
        self.task_context = {}
        self.completed_steps = []
        self.iteration_count = 0

    def set_task(self, task: str):
        self.task_context["task"] = task
        self.task_context["start_time"] = datetime.now().isoformat()

    def increment_iteration(self):
        self.iteration_count += 1

    def export(self) -> Dict[str, Any]:
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "task_context": self.task_context,
            "completed_steps": self.completed_steps,
            "iteration_count": self.iteration_count
        }
