import gradio as gr
import time
import random
import json
from tomori_chat import chat_logic


live2d_model_path = "live2d_model/tomori/model.json"

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Live2D Tomori</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: transparent;
        }}
        #live2d-canvas {{
            position: absolute;
            width: 100%;
            height: 100%;
            left: 0;
            top: 0;
        }}
    </style>
</head>
<body>
    <canvas id="live2d-canvas"></canvas>

    <!-- 引入 Live2D Cubism SDK for Web -->
    <script src="js/live2dcubismcore.min.js"></script>
    <script src="js/pixi.min.js"></script>
    <script src="js/pixi-live2d-display.min.js"></script>

    <script>
        const modelPath = "{live2d_model_path}";

        (async function() {{
            const app = new PIXI.Application({{
                view: document.getElementById('live2d-canvas'),
                autoStart: true,
                resizeTo: window,
                backgroundAlpha: 0,
            }});

            const model = await PIXI.live2d.Live2DModel.from(modelPath);
            app.stage.addChild(model);

            // 调整模型大小和位置
            model.scale.set(0.25); // 根据你的模型大小调整
            model.anchor.set(0.5, 0.5);

            function onResize() {{
                model.position.set(window.innerWidth / 2, window.innerHeight / 1.8);
            }}
            window.addEventListener('resize', onResize);
            onResize();

            // 存储动作和表情
            const motions = {{}};
            const expressions = {{}};

            model.on('load', () => {{
                // 加载所有动作
                Object.keys(model.motions).forEach(group => {{
                    model.motions[group].forEach((motion, i) => {{
                        const motionName = `${{group}}_${{i}}`;
                        motions[motionName] = motion;
                    }});
                }});

                // 加载所有表情
                Object.keys(model.expressions).forEach((name, i) => {{
                    expressions[name] = model.expressions[name];
                }});

                console.log("Live2D Model loaded.", {{ motions, expressions }});
            }});
            
            // 核心功能：监听来自 Gradio 的指令
        function handleCommand(command) {{
            // 确保 command 对象存在且包含 live2d_motion 属性
            if (!command || !command.live2d_motion) {{
                console.warn("Received invalid command or missing 'live2d_motion' property:", command);
                if (model) {{
                    // 如果模型已加载，尝试恢复默认表情或播放空闲动作
                    model.expression(null); 
                    // 也可以明确播放 idle01 动作，如果模型有这个动作组
                    // if (model.motions && model.motions.idle01) {{
                    //     model.motion('idle01', 0, PIXI.live2d.MotionPriority.NORMAL);
                    // }}
                }}
                return;
            }}
        
            console.log("Received command from Gradio:", command);
            const motionToPlay = command.live2d_motion; // 从 Gradio 获取的动作名称
        
            if (model) {{ // 确保 Live2D 模型已经加载
                // 直接使用从 Gradio 接收到的动作文件名（不含.mtn后缀）来尝试播放动作。
                // PIXI.live2d.Live2DModel.from() 通常会将 .mtn 文件名作为可直接调用的动作键。
                // 第一个参数是动作的名称（例如 'angry01'）。
                // 第二个参数是动作在组中的索引（这里我们设为0，因为我们假设它是直接的动作名）。
                // 第三个参数是优先级，FORCE 表示强制播放，会打断当前低优先级的动作。
                if (model.motion(motionToPlay, 0, PIXI.live2d.MotionPriority.FORCE)) {{
                    console.log(`Playing Live2D motion: ${{motionToPlay}}`);
                }} else {{
                    // 如果指定的动作不存在，打印警告并尝试恢复默认
                    console.warn(`Motion '${{motionToPlay}}' not found or failed to play. Falling back to idle.`);
                    // 如果你有一个特定的默认空闲动作，可以尝试播放
                    if (model.motions && Object.keys(model.motions).includes('idle01')) {{ // 检查是否有 'idle01' 这个动作组
                         model.motion('idle01', 0, PIXI.live2d.MotionPriority.NORMAL);
                    }} else {{
                        model.expression(null); // 最保险的方法是恢复默认表情
                    }}
                }}
            }} else {{
                console.warn("Live2D model not yet loaded, cannot play motion:", motionToPlay);
            }}
        }}

            // 使用 MutationObserver 监听 Gradio UI 中隐藏元素的变化
            // 这是 Gradio 前后端通信的常用技巧
            const targetNode = window.parent.document.querySelector('#live2d_command_stream');
            if (targetNode) {{
                const observer = new MutationObserver(mutationsList => {{
                    for(let mutation of mutationsList) {{
                        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                            const commandText = mutation.addedNodes[0].textContent;
                            try {{
                                const command = JSON.parse(commandText);
                                handleCommand(command);
                            }} catch (e) {{
                                console.error("Failed to parse command:", commandText, e);
                            }}
                        }}
                    }}
                }});
                observer.observe(targetNode, {{ childList: true }});
                console.log("Observer attached to #live2d_command_stream");
            }} else {{
                console.error("#live2d_command_stream not found in parent document.");
            }}
        }})();
    </script>
</body>
</html>
"""

# ==============================================================================
# 5. Gradio 应用界面
# ==============================================================================

with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {background-color: #f0f4f8;}") as demo:
    gr.Markdown("# 高松灯 Live2D 聊天机器人")
    gr.Markdown("和灯聊天，看看她的反应吧！")

    with gr.Row():
        with gr.Column(scale=1):
            # 用于显示 Live2D 模型的 HTML 组件
            live2d_viewer = gr.HTML(html_code)

            # 用于从后端向前端JS传递指令的隐藏组件
            live2d_command_stream = gr.Textbox(
                "",
                elem_id="live2d_command_stream",
                visible=False
            )

        with gr.Column(scale=1):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
                height=600
            )
            chat_input = gr.Textbox(
                show_label=False,
                placeholder="在这里输入你想对灯说的话...",
                container=False
            )


    def predict(query, history):
        history.append([query, None])
        # 预先更新UI，显示用户输入
        yield history, ""

        # 流式处理聊天逻辑
        response = ""
        for resp, command in chat_logic(query, history[:-1]):
            response = resp
            history[-1][1] = response
            # 流式更新聊天气泡和发送指令
            yield history, command


    chat_input.submit(predict, [chat_input, chatbot], [chatbot, live2d_command_stream])

if __name__ == "__main__":
    # 允许从本地文件系统加载 Live2D 模型
    demo.launch(share=False,allowed_paths=["live2d_model", "js"])