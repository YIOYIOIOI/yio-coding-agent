"""
Coding Agent - Main Application
"""
import os
import sys
import gradio as gr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent import CodingAgent, AgentConfig
from dotenv import load_dotenv

load_dotenv()

# Config
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
os.makedirs(WORKSPACE, exist_ok=True)

# CSS
CUSTOM_CSS = """
.gradio-container {
    padding: 0 !important;
    max-width: 100% !important;
    background: #1e1e1e !important;
}
footer { display: none !important; }

/* Sidebar */
#sidebar {
    background: #252526 !important;
    min-height: 100vh;
    padding: 0 !important;
    border-right: 1px solid #3c3c3c;
}

.sidebar-header {
    background: #3c3c3c;
    padding: 10px 16px;
    font-size: 11px;
    font-weight: 600;
    color: #bbbbbb;
    text-transform: uppercase;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Folder Accordion */
#sidebar .accordion {
    border: none !important;
    background: transparent !important;
}

#sidebar .label-wrap {
    background: transparent !important;
    padding: 6px 12px !important;
    color: #cccccc !important;
    font-size: 13px !important;
    border: none !important;
}

#sidebar .label-wrap:hover {
    background: #2a2d2e !important;
}

#sidebar .icon {
    color: #dcb67a !important;
}

/* File Button */
.file-btn {
    background: transparent !important;
    border: none !important;
    color: #cccccc !important;
    text-align: left !important;
    padding: 5px 12px 5px 28px !important;
    margin: 0 !important;
    font-size: 13px !important;
    width: 100% !important;
    justify-content: flex-start !important;
    border-radius: 0 !important;
}

.file-btn:hover {
    background: #094771 !important;
}

/* Refresh Button */
.refresh-btn {
    background: transparent !important;
    border: none !important;
    color: #888 !important;
    padding: 2px 6px !important;
    font-size: 14px !important;
    min-width: auto !important;
}

.refresh-btn:hover {
    color: #fff !important;
}

/* Main Area */
#main-area {
    background: #1e1e1e !important;
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* Preview */
#preview-box {
    background: #252526;
    border-bottom: 1px solid #3c3c3c;
    max-height: 220px;
    overflow: auto;
}

#preview-box .prose {
    color: #d4d4d4 !important;
    font-size: 13px !important;
}

.preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    background: #2d2d2d;
    border-bottom: 1px solid #3c3c3c;
    color: #ccc;
    font-size: 12px;
}

.close-btn {
    background: transparent !important;
    border: none !important;
    color: #888 !important;
    padding: 0 4px !important;
    font-size: 16px !important;
    min-width: auto !important;
}

.close-btn:hover {
    color: #fff !important;
}

/* Chat */
#chatbot {
    flex: 1;
    background: #1e1e1e !important;
    border: none !important;
}

#chatbot .message {
    max-width: 800px;
    margin: 0 auto;
    padding: 16px 24px !important;
    border-bottom: 1px solid #3c3c3c !important;
    color: #d4d4d4 !important;
}

#chatbot .message.bot {
    background: #252526 !important;
}

/* Input */
#input-area {
    background: #1e1e1e;
    padding: 16px 24px;
    border-top: 1px solid #3c3c3c;
}

#input-row {
    max-width: 800px;
    margin: 0 auto;
    background: #3c3c3c;
    border-radius: 8px;
    padding: 10px 14px;
    border: 1px solid #555;
}

#input-row:focus-within {
    border-color: #007acc;
}

#msg-input textarea {
    background: transparent !important;
    border: none !important;
    color: #d4d4d4 !important;
}

#send-btn {
    background: #0e639c !important;
    border: none !important;
    border-radius: 4px !important;
    color: white !important;
}

#send-btn:hover {
    background: #1177bb !important;
}

/* New Chat Button */
.new-chat-btn {
    margin: 8px !important;
    background: #3c3c3c !important;
    border: none !important;
    color: #ccc !important;
    padding: 8px 12px !important;
    border-radius: 4px !important;
    font-size: 13px !important;
}

.new-chat-btn:hover {
    background: #4c4c4c !important;
}

pre {
    background: #1e1e1e !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1e1e1e; }
::-webkit-scrollbar-thumb { background: #424242; }
"""


def create_agent() -> CodingAgent:
    config = AgentConfig(model=MODEL, max_iterations=25, temperature=0.7)
    return CodingAgent(
        api_key=API_KEY,
        base_url=BASE_URL if BASE_URL else None,
        config=config,
        workspace=WORKSPACE
    )


def get_workspace_folders():
    try:
        items = os.listdir(WORKSPACE)
        folders = [f for f in items if os.path.isdir(os.path.join(WORKSPACE, f))]
        return sorted(folders)
    except:
        return []


def get_folder_files(folder_name):
    try:
        folder_path = os.path.join(WORKSPACE, folder_name)
        items = os.listdir(folder_path)
        files = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
        return sorted(files)
    except:
        return []


def read_file(folder, filename):
    filepath = os.path.join(WORKSPACE, folder, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ext = filename.split('.')[-1] if '.' in filename else ''
        lang = {'py': 'python', 'js': 'javascript', 'json': 'json', 'html': 'html', 'md': 'markdown'}.get(ext, '')
        return gr.update(visible=True), f"{folder}/{filename}", f"```{lang}\n{content}\n```"
    except Exception as e:
        return gr.update(visible=True), f"{folder}/{filename}", f"Error: {e}"


def close_preview():
    return gr.update(visible=False), "", ""


def chat_with_agent(message: str, history: list):
    if not message.strip():
        return history, ""

    if not API_KEY:
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "Error: Configure ANTHROPIC_API_KEY"}
        ]
        return history, ""

    history = history + [{"role": "user", "content": message}]
    history = history + [{"role": "assistant", "content": "..."}]
    yield history, ""

    try:
        agent = create_agent()
        gen = agent.run(message)
        response_parts = []
        files_created = []

        for event in gen:
            t = event.get("type", "")
            if t == "thinking":
                content = event.get("content", "")
                if content:
                    response_parts = [content]
                    history[-1]["content"] = content
                    yield history, ""
            elif t == "tool_call":
                tool = event.get("tool", "")
                inp = event.get("input", {})
                if tool == "write_file":
                    files_created.append(inp.get("file_path", ""))
                    history[-1]["content"] = f"Creating {inp.get('file_path', '')}..."
                    yield history, ""
                elif tool == "execute_python":
                    history[-1]["content"] = "Running..."
                    yield history, ""
            elif t == "complete":
                if event.get("summary"):
                    response_parts = [event["summary"]]
            elif t == "error":
                response_parts = [f"Error: {event.get('message', '')}"]

        final = response_parts[-1] if response_parts else "Done"
        if files_created:
            final += f"\n\n📁 Created: {', '.join(files_created)}"
        history[-1]["content"] = final
        yield history, ""

    except Exception as e:
        history[-1]["content"] = f"Error: {str(e)}"
        yield history, ""


def new_chat():
    return None, ""


# UI
with gr.Blocks(css=CUSTOM_CSS, title="Coding Agent") as app:

    with gr.Row():
        with gr.Column(scale=1, elem_id="sidebar", min_width=240):
            with gr.Row():
                gr.HTML('<div class="sidebar-header"><span>EXPLORER</span></div>')
                refresh_btn = gr.Button("↻", elem_classes=["refresh-btn"], size="sm")

            new_btn = gr.Button("+ New Chat", elem_classes=["new-chat-btn"], size="sm")
            @gr.render(triggers=[app.load, refresh_btn.click])
            def render_folders():
                folders = get_workspace_folders()

                if not folders:
                    gr.Markdown("*No projects yet*", elem_classes=["empty-msg"])
                    return

                for folder in folders:
                    with gr.Accordion(f"📁 {folder}", open=False):
                        files = get_folder_files(folder)
                        if files:
                            for f in files:
                                icon = "🐍" if f.endswith('.py') else "📄"
                                btn = gr.Button(f"{icon} {f}", elem_classes=["file-btn"], size="sm")
                                btn.click(
                                    fn=lambda fo=folder, fi=f: read_file(fo, fi),
                                    outputs=[preview_box, preview_title, preview_content]
                                )
                        else:
                            gr.Markdown("*Empty folder*")

        with gr.Column(scale=4, elem_id="main-area"):
            with gr.Group(visible=False, elem_id="preview-box") as preview_box:
                with gr.Row():
                    preview_title = gr.Markdown("", elem_classes=["preview-header"])
                    close_btn = gr.Button("✕", elem_classes=["close-btn"], size="sm")
                preview_content = gr.Markdown("")

            close_btn.click(fn=close_preview, outputs=[preview_box, preview_title, preview_content])

            # 聊天
            chatbot = gr.Chatbot(elem_id="chatbot", height=420, show_label=False, container=False)

            # 输入
            with gr.Group(elem_id="input-area"):
                with gr.Row(elem_id="input-row"):
                    msg_input = gr.Textbox(
                        placeholder="Ask me to create projects, write code...",
                        show_label=False, container=False, scale=6, elem_id="msg-input"
                    )
                    send_btn = gr.Button("Send", elem_id="send-btn", scale=1)

    # 事件
    msg_input.submit(fn=chat_with_agent, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
    send_btn.click(fn=chat_with_agent, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
    new_btn.click(fn=new_chat, outputs=[chatbot, msg_input])


if __name__ == "__main__":
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    os.environ['no_proxy'] = 'localhost,127.0.0.1'
    print(f"\n  AI Coding Agent\n  http://127.0.0.1:7860\n")
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
