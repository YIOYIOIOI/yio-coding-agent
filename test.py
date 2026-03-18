"""
测试脚本
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def test_imports():
    print("Test 1: imports...")
    try:
        from core import CodingAgent, ToolRegistry, Memory
        from core.agent import AgentConfig
        print("  [OK] all imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tools():
    print("\nTest 2: tools...")
    from core.tools import ToolRegistry

    workspace = os.path.join(os.path.dirname(__file__), "test_workspace")
    os.makedirs(workspace, exist_ok=True)

    tools = ToolRegistry(workspace=workspace)

    result = tools.execute_tool("write_file",
                                file_path="test.py",
                                content="print('Hello, Agent!')")
    print(f"  - write_file: {'[OK]' if 'Success' in result else '[FAIL]'}")

    result = tools.execute_tool("read_file", file_path="test.py")
    print(f"  - read_file: {'[OK]' if 'Hello' in result else '[FAIL]'}")

    result = tools.execute_tool("execute_python", code="print(1+1)")
    print(f"  - execute_python: {'[OK]' if '2' in result else '[FAIL]'}")

    result = tools.execute_tool("list_directory", path="")
    print(f"  - list_directory: {'[OK]' if 'test.py' in result else '[FAIL]'}")

    try:
        os.remove(os.path.join(workspace, "test.py"))
        os.rmdir(workspace)
    except:
        pass

    print("  [OK] tools test done")
    return True


def test_memory():
    print("\nTest 3: memory...")
    from core.memory import Memory

    memory = Memory()
    memory.set_task("test task")
    memory.add_user_message("Hello")
    memory.add_assistant_message([{"type": "text", "text": "Hi there!"}])

    messages = memory.get_claude_messages()
    print(f"  - message count: {len(messages)}")
    print(f"  - context: {memory.get_context_summary()}")
    print("  [OK] memory test done")
    return True


def test_claude_tools_format():
    print("\nTest 4: claude tools format...")
    from core.tools import ToolRegistry

    tools = ToolRegistry()
    claude_tools = tools.get_claude_tools()

    print(f"  - tool count: {len(claude_tools)}")
    for tool in claude_tools:
        print(f"    - {tool['name']}")

    print("  [OK] format test done")
    return True


def test_agent_creation():
    print("\nTest 5: agent creation...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")

    if not api_key:
        print("  - skipped (no API key)")
        return False

    try:
        from core.agent import CodingAgent, AgentConfig

        config = AgentConfig(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            max_iterations=5
        )

        agent = CodingAgent(
            api_key=api_key,
            base_url=base_url if base_url else None,
            config=config
        )

        print(f"  - agent created")
        print(f"  - workspace: {agent.get_workspace()}")
        print("  [OK] agent creation test done")
        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_simple_task():
    print("\nTest 6: simple task...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")

    if not api_key:
        print("  - skipped (no API key)")
        return False

    try:
        from core.agent import CodingAgent, AgentConfig

        config = AgentConfig(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            max_iterations=10
        )

        workspace = os.path.join(os.path.dirname(__file__), "test_workspace_agent")
        os.makedirs(workspace, exist_ok=True)

        agent = CodingAgent(
            api_key=api_key,
            base_url=base_url if base_url else None,
            config=config,
            workspace=workspace
        )

        print("  - running task: write and run hello world")

        result = agent.run_sync(
            "Write a Python program that prints 'Hello World', then run it"
        )

        print(f"  - success: {result.get('success')}")
        print(f"  - iterations: {result.get('iterations')}")
        if result.get('summary'):
            print(f"  - summary: {result['summary'][:100]}...")
        if result.get('error'):
            print(f"  - error: {result['error']}")

        return result.get('success', False)

    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 50)
    print("Coding Agent - Tests")
    print("=" * 50)

    results = []

    results.append(("imports", test_imports()))
    results.append(("tools", test_tools()))
    results.append(("memory", test_memory()))
    results.append(("claude format", test_claude_tools_format()))

    print("\n" + "-" * 50)
    print("API tests (requires API key):")
    print("-" * 50)

    results.append(("agent creation", test_agent_creation()))
    results.append(("simple task", test_simple_task()))

    print("\n" + "=" * 50)
    print("Results:")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {name}: {status}")

    print(f"\nPassed: {passed}/{total}")


if __name__ == "__main__":
    main()
