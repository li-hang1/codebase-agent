# codebase_agent

一个基于 Ollama `qwen3`、LangChain 和 LangGraph 的本地代码仓库 Agent。它会根据用户问题自动决定是否调用工具读取、搜索、分析、运行或删除仓库内代码。

## 目录

```text
codebase_agent/
├── main.py
├── config.py
├── graph/
│   ├── state.py
│   ├── nodes.py
│   └── workflow.py
├── tools/
│   ├── list_files_tool.py
│   ├── read_file_tool.py
│   ├── search_code_tool.py
│   ├── run_python_tool.py
│   ├── delete_file_tool.py
│   └── analyze_project_tool.py
├── prompts/
│   ├── router_prompt.py
│   └── answer_prompt.py
└── memory/
    └── sqlite_memory.py
```

## 运行

确保 Ollama 服务已启动，并且 `qwen3:latest` 已下载：

```bash
ollama list
```

也可以单次提问：

```bash
python main.py --repo /root/codebase --once "这个项目的入口文件是什么？"
```

如果要分析 `/root/codebase` 下所有内容：

```bash
python main.py --repo /root/codebase
```

## 可用工具

- `list_files`：列出仓库内文件。
- `read_file`：读取仓库内文本/代码文件，并显示行号。
- `search_code`：按字符串或正则搜索代码。
- `analyze_project`：总结项目结构、文件类型和可能入口。
- `run_python_file`：运行仓库内 `.py` 文件。
- `delete_path`：删除仓库内路径，但实际会移动到 `.codebase_agent_trash`，避免永久删除。

所有路径都会限制在 `--repo` 指定的根目录内，不能访问仓库外文件。

## 示例问题

```text
这个项目大概是做什么的？
请分析 models 文件夹下每个文件的作用。
ResNet.py 里的 Bottleneck 类有什么用？
搜索项目里哪里调用了 train 函数。
运行 python_code.py 看看输出。
删除 tmp/demo.py。
```
