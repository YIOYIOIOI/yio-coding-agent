"""
核心Agent模块 - 基于ReAct架构实现
"""
import os
import json
from typing import Dict, Any, List, Optional, Callable, Generator
from dataclasses import dataclass
import anthropic

from .tools import ToolRegistry
from .memory import Memory


@dataclass
class AgentConfig:
    max_iterations: int = 25
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.7
    max_tokens: int = 4096


class CodingAgent:
    """基于ReAct架构的编程助手Agent"""

    SYSTEM_PROMPT = """You are an AI coding assistant agent. You complete programming tasks by calling tools.

## How You Work

You use the ReAct (Reasoning + Acting) pattern:
1. **Reasoning**: Analyze the situation and decide what to do next
2. **Acting**: Call the appropriate tool
3. **Observation**: Review the tool result
4. **Reflection**: Adjust strategy if needed

## Available Tools

- `read_file`: Read file contents
- `write_file`: Create or modify files
- `execute_python`: Run Python code
- `execute_shell`: Run shell commands
- `list_directory`: View directory structure
- `search_in_files`: Search within files
- `ask_user`: Ask the user a question
- `reflect`: Reflect on current progress
- `task_complete`: Mark task as complete

## Principles

1. Understand requirements - ask for clarification if needed
2. Work incrementally - complete tasks step by step
3. Test your code - always verify with execute_python
4. Handle errors - analyze and fix failures
5. Iterate - keep improving until the code works
6. Complete properly - always call task_complete when done

## Notes

- Generated code must be complete and runnable
- Python code should include if __name__ == "__main__"
- Don't give up on errors - analyze and fix them
- Keep code simple, avoid over-engineering
- Always call task_complete when finished"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        config: AgentConfig = None,
        workspace: str = None
    ):
        """
        初始化Agent

        Args:
            api_key: Anthropic API密钥
            base_url: API基础URL（用于代理）
            config: Agent配置
            workspace: 工作目录
        """
        self.config = config or AgentConfig()

        # 初始化Anthropic客户端
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = anthropic.Anthropic(**client_kwargs)

        # 初始化工具和记忆
        self.tools = ToolRegistry(workspace=workspace)
        self.memory = Memory()

        # 状态
        self.is_running = False
        self.should_stop = False
        self._user_input_callback: Optional[Callable[[str], str]] = None
        self._progress_callback: Optional[Callable[[str, str, int], None]] = None

    def set_user_input_callback(self, callback: Callable[[str], str]):
        """设置用户输入回调（用于ask_user工具）"""
        self._user_input_callback = callback

    def set_progress_callback(self, callback: Callable[[str, str, int], None]):
        """设置进度回调 callback(stage, message, iteration)"""
        self._progress_callback = callback

    def _report_progress(self, stage: str, message: str):
        """报告进度"""
        if self._progress_callback:
            self._progress_callback(stage, message, self.memory.iteration_count)

    def run(self, task: str) -> Generator[Dict[str, Any], Optional[str], Dict[str, Any]]:
        """
        运行Agent完成任务（生成器模式，支持交互）

        Args:
            task: 用户任务描述

        Yields:
            进度信息字典

        Returns:
            最终结果字典
        """
        self.is_running = True
        self.should_stop = False
        self.memory.clear()
        self.memory.set_task(task)

        self._report_progress("start", f"开始处理任务: {task[:50]}...")

        # 初始用户消息
        self.memory.add_user_message(task)

        result = {
            "success": False,
            "summary": "",
            "files_created": [],
            "iterations": 0,
            "error": None
        }

        try:
            while self.memory.iteration_count < self.config.max_iterations and not self.should_stop:
                self.memory.increment_iteration()
                iteration = self.memory.iteration_count

                self._report_progress("thinking", f"迭代 {iteration}: 思考中...")

                # 调用Claude
                response = self._call_claude()

                # 处理响应
                assistant_content = response.content
                self.memory.add_assistant_message(assistant_content)

                # 提取文本和工具调用
                text_parts = []
                tool_calls = []

                for block in assistant_content:
                    if block.type == "text":
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append(block)

                # 报告思考过程
                if text_parts:
                    thinking = "\n".join(text_parts)
                    self._report_progress("thinking", thinking[:200])
                    yield {"type": "thinking", "content": thinking, "iteration": iteration}

                # 如果没有工具调用，检查是否应该结束
                if not tool_calls:
                    if response.stop_reason == "end_turn":
                        result["summary"] = "\n".join(text_parts) if text_parts else "任务处理完成"
                        result["success"] = True
                        break
                    continue

                # 执行工具调用
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    tool_input = tool_call.input
                    tool_use_id = tool_call.id

                    self._report_progress("action", f"执行工具: {tool_name}")
                    yield {
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                        "iteration": iteration
                    }

                    # 执行工具
                    tool_result = self.tools.execute_tool(tool_name, **tool_input)

                    # 检查特殊结果
                    if tool_result.startswith("__ASK_USER__:"):
                        # 需要用户输入
                        question = tool_result.replace("__ASK_USER__:", "")
                        yield {"type": "ask_user", "question": question, "iteration": iteration}

                        # 等待用户输入
                        if self._user_input_callback:
                            user_answer = self._user_input_callback(question)
                            tool_result = f"用户回答: {user_answer}"
                        else:
                            # 生成器模式：通过send接收用户输入
                            user_answer = yield {"type": "waiting_input", "question": question}
                            tool_result = f"用户回答: {user_answer}" if user_answer else "用户未回答"

                    elif tool_result.startswith("__TASK_COMPLETE__"):
                        # 任务完成
                        self._report_progress("complete", "任务完成")
                        result["success"] = True
                        result["summary"] = tool_input.get("summary", "")
                        result["files_created"] = tool_input.get("files_created", [])
                        yield {"type": "complete", "summary": result["summary"], "iteration": iteration}
                        self.is_running = False
                        result["iterations"] = iteration
                        return result

                    # 添加工具结果到记忆
                    self.memory.add_tool_result(tool_use_id, tool_name, tool_result)

                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": tool_result[:500],  # 截断长结果
                        "iteration": iteration
                    }

            # 循环结束
            if self.memory.iteration_count >= self.config.max_iterations:
                result["error"] = f"达到最大迭代次数 ({self.config.max_iterations})"
                self._report_progress("error", result["error"])

        except Exception as e:
            result["error"] = str(e)
            self._report_progress("error", f"错误: {str(e)}")
            yield {"type": "error", "message": str(e)}

        finally:
            self.is_running = False
            result["iterations"] = self.memory.iteration_count

        return result

    def run_sync(self, task: str, user_input_callback: Callable[[str], str] = None) -> Dict[str, Any]:
        """
        同步运行Agent（非生成器模式）

        Args:
            task: 用户任务
            user_input_callback: 用户输入回调

        Returns:
            结果字典
        """
        if user_input_callback:
            self.set_user_input_callback(user_input_callback)

        gen = self.run(task)
        result = None

        try:
            while True:
                event = next(gen)
                if event.get("type") == "waiting_input":
                    if user_input_callback:
                        answer = user_input_callback(event["question"])
                        event = gen.send(answer)
                    else:
                        event = gen.send(None)
        except StopIteration as e:
            result = e.value

        return result or {"success": False, "error": "未知错误"}

    def _call_claude(self) -> Any:
        """调用Claude API"""
        messages = self.memory.get_claude_messages()

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=self.SYSTEM_PROMPT,
            tools=self.tools.get_claude_tools(),
            messages=messages
        )

        return response

    def stop(self):
        """停止Agent"""
        self.should_stop = True

    def get_workspace(self) -> str:
        """获取工作目录"""
        return self.tools.workspace
