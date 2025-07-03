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

live2d_html_code = """
<div id="live2d-container" style="width:100%; height:500px; position:relative;">
  <canvas id="live2d-canvas" style="position:absolute; width:100%; height:100%; left:0; top:0;"></canvas>
</div>

<script type="text/javascript">
(async function () {
    // 动态加载 PIXI 和 Cubism2 脚本
    const loadScript = (src) => new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = src;
        s.onload = resolve;
        s.onerror = reject;
        document.body.appendChild(s);
    });
    await loadScript("https://cdn.jsdelivr.net/gh/dylanNew/live2d/webgl/Live2D/lib/live2d.min.js");
    await loadScript("https://cdn.jsdelivr.net/npm/pixi.js@7/dist/pixi.min.js");
    await loadScript("https://cdn.jsdelivr.net/npm/pixi-live2d-display/dist/cubism2.min.js");

    // 模型加载
    const modelPath = "/static/live2d_model/tomori/model.json";
    const app = new PIXI.Application({
        view: document.getElementById('live2d-canvas'),
        autoStart: true,
        resizeTo: window,
        backgroundAlpha: 0,
    });

    const model = await PIXI.live2d.Live2DModel.from(modelPath, { cubism2: true });
    app.stage.addChild(model);

    model.scale.set(0.25);
    model.anchor.set(0.5, 0.5);
    model.position.set(window.innerWidth / 2, window.innerHeight / 1.8);

    console.log("✅ Cubism2 模型加载成功");

    // 自动测试一个动作（可删）
    setTimeout(() => {
        model.motion("thinking02", 0, PIXI.live2d.MotionPriority.FORCE);
    }, 1000);

    // 尝试绑定 Gradio 的 Textbox textarea（必须等 DOM 完成）
    const tryBindCommandListener = () => {
        const wrapper = document.querySelector('#live2d_command_stream');
        if (!wrapper) return console.warn("⚠ #live2d_command_stream wrapper not found");

        const textarea = wrapper.querySelector('textarea');
        if (!textarea) return console.warn("⚠ textarea not found inside wrapper");

        console.log("✅ Live2D 指令监听器绑定成功");

        textarea.addEventListener('input', () => {
            const val = textarea.value?.trim();
            if (!val) return;
            try {
                const command = JSON.parse(val);
                if (command.live2d_motion) {
                    console.log("🎬 执行动作：", command.live2d_motion);
                    model.motion(command.live2d_motion, 0, PIXI.live2d.MotionPriority.FORCE);
                }
            } catch (e) {
                console.error("❌ 无法解析指令：", val, e);
            }
        });
    };

    // 等待 Gradio 渲染完成后尝试绑定 textarea
    let retries = 0;
    const pollInterval = setInterval(() => {
        tryBindCommandListener();
        retries++;
        if (document.querySelector('#live2d_command_stream textarea') || retries > 20) {
            clearInterval(pollInterval);
        }
    }, 500);
})();
</script>
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
        yield history, json.dumps({})

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
            # 流式更新聊天气泡和发送指令
            print("✅ 向前端发送指令：", command)
            yield history, command


    chat_input.submit(predict, [chat_input, chatbot], [chatbot, live2d_command_stream])

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app = mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # 允许从本地文件系统加载 Live2D 模型
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
