import gradio as gr
import time
import random
import json
from tomori_chat import chat_logic
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from gradio.routes import mount_gradio_app

app = FastAPI()


live2d_html_iframe = '<iframe src="/static/live2d_view.html" width="100%" height="600" style="border:none; border-radius: 12px;"></iframe>'

js_library = """
<script src="https://cdn.jsdelivr.net/gh/dylanNew/live2d/webgl/Live2D/lib/live2d.min.js"></script>
<script src="https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi.js@7/dist/pixi.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display/dist/index.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display/dist/cubism2.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display/dist/cubism4.min.js"></script>
"""

js_library_imports = """
<script src="/static/js/live2d.min.js"></script>
<script src="/static/js/live2dcubismcore.min.js"></script>
<script src="/static/js/pixi.min.js"></script>
<script src="/static/js/index.min.js"></script>
<script src="/static/js/logic.js"></script>
"""

js_script = """
function() { // 添加了外层自执行函数的开括号
    function setupBridge() {
        const commandComponent = document.getElementById('live2d_command_stream');
        const iframe = document.querySelector('iframe');

        if (!commandComponent) {
            console.log('[Gradio Parent] 正在等待指令组件 (#live2d_command_stream)...');
        }
        if (!iframe) {
            console.log('[Gradio Parent] 正在等待 iFrame...');
        }

        if (commandComponent && iframe && iframe.contentWindow) {
            const commandTextarea = commandComponent.querySelector('textarea');
            if (commandTextarea) {
                console.log('[Gradio Parent] ✅ 成功找到所有元素，正在附加监听器。');

                const observer = new MutationObserver(() => {
                    const command = commandTextarea.value;
                    console.log('[Gradio Parent] 监听到指令变化，准备发送:', command);

                    if (command && command.trim() !== '{}' && command.trim() !== '') {
                        iframe.contentWindow.postMessage(command, '*');
                        console.log('[Gradio Parent] ✅ 指令已发送至 iFrame。');
                    }
                });

                observer.observe(commandTextarea, {
                    attributes: true, childList: true, characterData: true, subtree: true
                });

                console.log('[Gradio Parent] ✅ 通信桥梁已成功激活。');
                return;
            }
        }
        setTimeout(setupBridge, 200);
    }

    setupBridge();

function scrollChatbotToBottom() {
        // !!! 修正为直接使用 #chatbot 作为滚动目标 !!!
        const chatbotMessagesContainer = document.getElementById('chatbot'); // 直接获取 #chatbot 元素

        if (chatbotMessagesContainer) {
            // 稍作延迟，确保DOM渲染完成，这对流式输出尤其有用
            setTimeout(() => {
                chatbotMessagesContainer.scrollTop = chatbotMessagesContainer.scrollHeight;
                // console.log('[Gradio JS] Chatbot 已尝试滚动。'); // 用于调试
            }, 50); // 50毫秒的延迟
        } else {
            // console.log('[Gradio JS] 错误：未找到 Chatbot 滚动容器！'); // 用于调试
        }
    }

    const chatbotElement = document.getElementById('chatbot'); // 这依然是 #chatbot 元素

    if (chatbotElement) {
        const observer = new MutationObserver(function(mutationsList) {
            for (const mutation of mutationsList) {
                // 检查是否有新的子节点（即新消息）被添加到聊天机器人中
                // 观察 bubble-wrap 的子节点变化更准确，因为消息直接添加到它里面
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // console.log('[Gradio JS] 检测到 Chatbot 内容变化。'); // 用于调试
                    scrollChatbotToBottom();
                }
            }
        });

        // 观察 #chatbot 内部的 bubble-wrap 元素，因为实际的消息是添加到 bubble-wrap 内部的
        // 如果直接观察 #chatbot，它可能只在它的直接子元素变化时触发，而消息在更深的层次
        const bubbleWrap = chatbotElement.querySelector('.bubble-wrap.svelte-1nyobg5');
        if (bubbleWrap) {
            observer.observe(bubbleWrap, { childList: true, subtree: true });
        } else {
            // Fallback: 如果 bubble-wrap 找不到，就观察整个 chatbotElement
            // console.log('[Gradio JS] 未找到 .bubble-wrap，将观察整个 #chatbot 元素。');
            observer.observe(chatbotElement, { childList: true, subtree: true });
        }

        // 页面加载时进行一次初始滚动，防止已有历史消息
        scrollChatbotToBottom();
    }
}
"""
# ==============================================================================
# 5. Gradio 应用界面
# ==============================================================================

with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {background-color: #f0f4f8;}",js=js_script) as demo:
    gr.Markdown("# 高松灯 Live2D 聊天机器人")
    gr.Markdown("和灯聊天，看看她的反应吧！")

    with gr.Row():
        with gr.Column(scale=1):
            # 用于显示 Live2D 模型的 HTML 组件

            live2d_viewer = gr.HTML(live2d_html_iframe)

            # 用于从后端向前端JS传递指令的隐藏组件
            live2d_command_stream = gr.Textbox(
                "",
                elem_id="live2d_command_stream",
                visible=True
            )

        with gr.Column(scale=1):

            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
                height=600,
                autoscroll=True
            )
            chat_input = gr.Textbox(
                show_label=False,
                placeholder="在这里输入你想对灯说的话...",
                container=False
            )


    def predict(query, history):
        if not query.strip():
            yield history, json.dumps({}), ""
            return
        history.append([query, None])
        # 预先更新UI，显示用户输入
        yield history, json.dumps({}), ""

        # 流式处理聊天逻辑
        response = ""
        for resp, command in chat_logic(query, history[:-1]):
            response = resp
            history[-1][1] = response
            if not isinstance(command, str):
                command = json.dumps(command)
            else:
                try:
                    json.loads(command)
                except Exception as e:
                    print("❌ 非法 JSON 指令，强制回退:", command)
                    command = json.dumps({})
            yield history, command, ""
            time.sleep(0.05)


    chat_input.submit(predict, [chat_input, chatbot], [chatbot, live2d_command_stream, chat_input])

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app = mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # 允许从本地文件系统加载 Live2D 模型
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
