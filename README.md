# Coding Agent

基于 Claude API 的自主编程助手，采用 ReAct 架构。

## 功能

- 自动编写和执行代码
- 文件读写操作
- Shell 命令执行
- 自主决策和错误修复

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，填入 API 配置：

```
ANTHROPIC_API_KEY=your_key
ANTHROPIC_BASE_URL=  # 可选，代理地址
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

## 运行

```bash
python app.py
```

打开 http://127.0.0.1:7860

## 项目结构

```
├── app.py          # Web 界面
├── core/
│   ├── agent.py    # Agent 核心逻辑
│   ├── tools.py    # 工具定义
│   └── memory.py   # 对话记忆
├── workspace/      # 生成的代码保存位置
└── test.py         # 测试脚本
```

## 技术栈

- Claude API (Tool Use)
- Gradio
- ReAct 架构
