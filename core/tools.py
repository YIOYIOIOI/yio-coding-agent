"""
工具系统 - Agent可用的工具集
"""
import os
import subprocess
import sys
import tempfile
import json
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable

    def to_claude_format(self) -> Dict[str, Any]:
        clean_props = {}
        required_fields = []

        for name, prop in self.parameters.items():
            clean_prop = {k: v for k, v in prop.items() if k != "required"}
            clean_props[name] = clean_prop
            if prop.get("required", False):
                required_fields.append(name)

        schema = {
            "type": "object",
            "properties": clean_props
        }
        if required_fields:
            schema["required"] = required_fields

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": schema
        }

    def execute(self, **kwargs) -> str:
        return self.function(**kwargs)


class ToolRegistry:
    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.path.join(os.path.dirname(__file__), "..", "workspace")
        os.makedirs(self.workspace, exist_ok=True)

        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        # read_file
        self.register(Tool(
            name="read_file",
            description="Read the contents of a file.",
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "File path relative to workspace",
                    "required": True
                }
            },
            function=self._read_file
        ))

        # write_file
        self.register(Tool(
            name="write_file",
            description="Create or overwrite a file.",
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "File path relative to workspace",
                    "required": True
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                    "required": True
                }
            },
            function=self._write_file
        ))

        # execute_python
        self.register(Tool(
            name="execute_python",
            description="Execute Python code and return the result.",
            parameters={
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                    "required": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 30)",
                    "required": False
                }
            },
            function=self._execute_python
        ))

        # execute_shell
        self.register(Tool(
            name="execute_shell",
            description="Execute a shell command.",
            parameters={
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                    "required": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 60)",
                    "required": False
                }
            },
            function=self._execute_shell
        ))

        # create_directory
        self.register(Tool(
            name="create_directory",
            description="Create a directory. Ignored if already exists.",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Directory path relative to workspace",
                    "required": True
                }
            },
            function=self._create_directory
        ))

        # list_directory
        self.register(Tool(
            name="list_directory",
            description="List files and subdirectories in a directory.",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Directory path (default: current directory)",
                    "required": False
                }
            },
            function=self._list_directory
        ))

        # search_in_files
        self.register(Tool(
            name="search_in_files",
            description="Search for content in files.",
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Text or regex pattern to search",
                    "required": True
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern (e.g. *.py)",
                    "required": False
                }
            },
            function=self._search_in_files
        ))

        # ask_user
        self.register(Tool(
            name="ask_user",
            description="Ask the user a question when clarification is needed.",
            parameters={
                "question": {
                    "type": "string",
                    "description": "Question to ask",
                    "required": True
                }
            },
            function=self._ask_user
        ))

        # task_complete
        self.register(Tool(
            name="task_complete",
            description="Call this when the task is complete.",
            parameters={
                "summary": {
                    "type": "string",
                    "description": "Summary of what was accomplished",
                    "required": True
                },
                "files_created": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of created files",
                    "required": False
                }
            },
            function=self._task_complete
        ))

        # reflect
        self.register(Tool(
            name="reflect",
            description="Reflect on current progress and adjust strategy if needed.",
            parameters={
                "current_state": {
                    "type": "string",
                    "description": "Current state description",
                    "required": True
                },
                "problems": {
                    "type": "string",
                    "description": "Problems encountered",
                    "required": False
                },
                "next_steps": {
                    "type": "string",
                    "description": "Planned next steps",
                    "required": False
                }
            },
            function=self._reflect
        ))

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self.tools.values())

    def get_claude_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_claude_format() for tool in self.tools.values()]

    def execute_tool(self, name: str, **kwargs) -> str:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return f"Tool execution error: {str(e)}"

    # Tool implementations

    def _get_full_path(self, relative_path: str) -> str:
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.workspace, relative_path)

    def _read_file(self, file_path: str) -> str:
        full_path = self._get_full_path(file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File contents ({file_path}):\n```\n{content}\n```"
        except FileNotFoundError:
            return f"Error: File not found - {file_path}"
        except Exception as e:
            return f"Read error: {str(e)}"

    def _write_file(self, file_path: str, content: str) -> str:
        full_path = self._get_full_path(file_path)
        try:
            os.makedirs(os.path.dirname(full_path) if os.path.dirname(full_path) else self.workspace, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Success: File saved to {file_path} ({len(content)} chars)"
        except Exception as e:
            return f"Write error: {str(e)}"

    def _execute_python(self, code: str, timeout: int = 30) -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace
            )

            output = ""
            if result.stdout:
                output += f"stdout:\n```\n{result.stdout}\n```\n"
            if result.stderr:
                output += f"stderr:\n```\n{result.stderr}\n```\n"

            if result.returncode == 0:
                return f"Execution successful (code: 0)\n{output}" if output else "Execution successful (no output)"
            else:
                return f"Execution failed (code: {result.returncode})\n{output}"

        except subprocess.TimeoutExpired:
            return f"Timeout ({timeout}s)"
        except Exception as e:
            return f"Execution error: {str(e)}"
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def _execute_shell(self, command: str, timeout: int = 60) -> str:
        import platform
        if platform.system() == "Windows":
            if command.strip().startswith("mkdir -p "):
                dir_path = command.strip()[9:].strip().strip('"').strip("'")
                return self._create_directory(dir_path)
            if command.strip().startswith("mkdir "):
                dir_path = command.strip()[6:].strip().strip('"').strip("'")
                return self._create_directory(dir_path)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace
            )

            output = ""
            if result.stdout:
                output += f"Output:\n```\n{result.stdout}\n```\n"
            if result.stderr:
                output += f"Error:\n```\n{result.stderr}\n```\n"

            if result.returncode == 0:
                return f"Command successful\n{output}" if output else "Command successful (no output)"
            else:
                return f"Command failed (code: {result.returncode})\n{output}"

        except subprocess.TimeoutExpired:
            return f"Timeout ({timeout}s)"
        except Exception as e:
            return f"Command error: {str(e)}"

    def _create_directory(self, path: str) -> str:
        full_path = self._get_full_path(path)
        try:
            os.makedirs(full_path, exist_ok=True)
            return f"Success: Directory created - {path}"
        except Exception as e:
            return f"Directory creation error: {str(e)}"

    def _list_directory(self, path: str = "") -> str:
        full_path = self._get_full_path(path) if path else self.workspace
        try:
            items = os.listdir(full_path)
            if not items:
                return f"Directory empty: {path or '.'}"

            files = []
            dirs = []
            for item in items:
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    dirs.append(f"[dir] {item}/")
                else:
                    size = os.path.getsize(item_path)
                    files.append(f"[file] {item} ({size} bytes)")

            result = f"Contents of {path or '.'}:\n"
            for d in sorted(dirs):
                result += f"  {d}\n"
            for f in sorted(files):
                result += f"  {f}\n"
            return result

        except FileNotFoundError:
            return f"Error: Directory not found - {path}"
        except Exception as e:
            return f"List error: {str(e)}"

    def _search_in_files(self, pattern: str, file_pattern: str = "*") -> str:
        import glob
        import re

        search_path = os.path.join(self.workspace, "**", file_pattern)
        matches = []

        try:
            for file_path in glob.glob(search_path, recursive=True):
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                if re.search(pattern, line):
                                    rel_path = os.path.relpath(file_path, self.workspace)
                                    matches.append(f"{rel_path}:{i}: {line.strip()}")
                    except:
                        continue

            if matches:
                return f"Found {len(matches)} matches:\n" + "\n".join(matches[:50])
            else:
                return f"No matches found: {pattern}"

        except Exception as e:
            return f"Search error: {str(e)}"

    def _ask_user(self, question: str) -> str:
        return f"__ASK_USER__:{question}"

    def _task_complete(self, summary: str, files_created: List[str] = None) -> str:
        result = f"__TASK_COMPLETE__\nSummary: {summary}"
        if files_created:
            result += f"\nFiles created: {', '.join(files_created)}"
        return result

    def _reflect(self, current_state: str, problems: str = None, next_steps: str = None) -> str:
        result = f"Reflection:\n- Current state: {current_state}"
        if problems:
            result += f"\n- Problems: {problems}"
        if next_steps:
            result += f"\n- Next steps: {next_steps}"
        return result
