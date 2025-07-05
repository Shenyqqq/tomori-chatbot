[中文]()[English](https://github.com/Shenyqqq/tomori-chatbot/blob/master/README.md)

-----

# tomori-chatbot

一个旨在模拟《BanG Dream\! It's MyGO\!\!\!\!\!》中高松灯（Takamatsu Tomori）角色的 AI 聊天机器人。

本项目集成了经过 LoRA 微调的大型语言模型与检索增强生成（RAG）系统，以实现上下文感知的响应。前端是 Gradio Web UI，其中包含一个 Live2D 模型，其表情会根据语言模型的输出动态控制。

[🤗Hugging Face 模型](https://huggingface.co/gumigumi/qwen2.5-7B-Int4-tomori_lora)

-----

## 功能

  * **角色专属对话**：使用 LoRA 微调的 **Qwen2.5-7B-Instruct-GPTQ-Int4** 模型，以特定角色（高松灯）的口吻生成文本。
  * **检索增强生成 (RAG)**：在生成之前通过从向量知识库中检索相关信息来增强响应的上下文。
  * **动态 Live2D 表情**：解析生成的文本以确定情感倾向，然后触发 Web UI 上渲染的 Live2D 模型中相应的动画。
  * **Web 界面**：使用 Gradio 构建，便于用户交互和演示。

## 演示

[Bilibili](https://www.bilibili.com/video/BV1AU39zzESa/)

## 系统架构

应用程序按照以下数据流运行：

*(建议使用简单的框图来可视化此流程。)*

1.  **输入**：用户通过 Gradio Web 界面提交文本字符串。
2.  **检索**：输入字符串被转换为嵌入向量，并用于对预构建的向量数据库（FAISS/ChromaDB）执行相似性搜索。检索出 top-k 结果作为上下文。
3.  **提示构建**：使用包含系统角色、检索到的上下文和用户原始输入的模板，组装最终提示。
4.  **生成**：构建好的提示传递给 Qwen2.5-7B 模型与附加的 LoRA 适配器。模型生成响应文本。
5.  **情感分析**：生成的文本通过一个轻量级函数（例如，基于关键词的分类器）进行处理，将其映射到预定义的情感类别（例如，`neutral`、`happy`、`sad`）。
6.  **输出**：生成的文本和情感类别被发送回 Gradio 前端。文本显示在聊天记录中，情感类别由 JavaScript 监听器用于触发相应的 Live2D 表情。

## 技术栈

  * **LLM**：`Qwen2.5-7B-Instruct-GPTQ-Int4`
  * **微调**：`LoRA (Low-Rank Adaptation)`
  * **后端**：`Python`、`Gradio`
  * **前端**：`HTML`、`JavaScript`
  * **动画**：`Live2D Cubism SDK for Web`
  * **RAG**：基于 `ChromaDB` 的向量数据库库。

## 数据与微调

模型的性能依赖于多源数据集策略，用于微调和检索。

### 微调数据

LoRA 适配器在一个复合数据集上进行训练：

1.  **游戏脚本**：直接从游戏数据文件中提取的基础对话。这提供了基础的角色设定，但在体量和对话质量上不足。
2.  **LLM 增强问答**：由辅助 LLM 生成的大量问答对。创建此数据集是为了扩展数据量，改善对话流畅性，并弥补原始脚本数据的局限性。
3.  **通用对话数据**：包含一小部分精选的通用对话数据，以提高模型的泛化能力并防止过拟合。

### RAG 知识库

为了提高效率，**LLM 增强问答数据集**被重新用作 RAG 系统的知识库。这种方法确保了检索到的上下文在风格上与微调模型的预期输出保持一致。

## 设置与安装

1.  **克隆仓库：**

    ```bash
    git clone https://github.com/Shenyqqq/tomori-chatbot.git
    cd tomori-chatbot
    ```

2.  **创建 Python 虚拟环境并安装依赖项：**

    ```bash
    # 建议使用虚拟环境
    python -m venv venv
    source venv/bin/activate  # 在 Windows 上，使用 `venv\Scripts\activate`
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
    pip install -r requirements.txt
    ```

3.  **运行应用程序：**

    首先构建向量数据库：

    ```bash
    python build_VecDB.py
    ```

    然后运行 `app.py`：

    ```bash
    python app.py
    ```

    Web 界面将在 `http://127.0.0.1:7860` 上可用。

    或者，解压发布版 `.zip` 文件，然后运行 `setup.bat` 构建环境，再运行 `start.bat` 启动聊天机器人。

## 未来开发

  * **TTS 集成**：实现文本转语音模型以进行语音输出，主要使用 GPT-Sovits。
  * **Live2D 模型选择**：添加一个按钮来选择不同的 Live2D 模型。
  * **其他角色 LoRA 微调**：在 BanG Dream\! 中创建其他角色的聊天机器人。
