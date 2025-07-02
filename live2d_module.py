# live2d_module.py
import os
import sys


# --- Live2D 模型路径配置 ---
LIVE2D_MODEL_PATH = "assets\live2d_model\live2d_download\tomori\model.json"  # 你的 Live2D 模型主文件

# --- Live2D Canvas HTML/JavaScript ---
# 这个 HTML 包含了 Live2D Cubism SDK 的加载和渲染逻辑
# 确保 live2dcubismcore.min.js, live2d.min.js 等文件存在于 assets/live2d_js/ 目录下
LIVE2D_HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Live2D Canvas</title>
    <style>
        body {{ margin: 0; overflow: hidden; }}
        canvas {{ display: block; }}
        /* 确保 Gradio 容器有足够高度 */
        #live2d-container {{ height: 600px; width: 100%; display: flex; justify-content: center; align-items: center; background-color: #f0f0f0; }}
        #live2d-canvas {{ max-width: 100%; max-height: 100%; }}
    </style>
</head>
<body>
    <div id="live2d-container">
        <canvas id="live2d-canvas"></canvas>
    </div>

    <script src="{get_resource_path('assets/live2d_js/live2dcubismcore.min.js')}"></script>
    <script src="{get_resource_path('assets/live2d_js/cubism4.min.js')}"></script>

    <script>
        // 定义模型路径和表情文件映射
        const modelPath = "{get_resource_path(LIVE2D_MODEL_PATH)}";
        const expressionMap = {{
            "neutral": "{get_resource_path('assets/live2d_model/taki/expressions/neutral.exp3.json')}",
            "happy": "{get_resource_path('assets/live2d_model/taki/expressions/happy.exp3.json')}",
            "sad": "{get_resource_path('assets/live2d_model/taki/expressions/sad.exp3.json')}",
            "confused": "{get_resource_path('assets/live2d_model/taki/expressions/confused.exp3.json')}",
            "hesitant": "{get_resource_path('assets/live2d_model/taki/expressions/hesitant.exp3.json')}",
            "angry": "{get_resource_path('assets/live2d_model/taki/expressions/angry.exp3.json')}",
            "thinking": "{get_resource_path('assets/live2d_model/taki/expressions/thinking.exp3.json')}",
            // 添加更多表情映射，确保文件存在
        }};

        let app = null; // Live2D 应用实例
        let currentExpression = null;
        let live2dModel = null; // Live2D Model 实例

        // 初始化 Live2D 应用
        async function initializeLive2D() {{
            const canvas = document.getElementById('live2d-canvas');
            if (!canvas) {{
                console.error("Live2D canvas element not found.");
                return;
            }}

            // 获取父容器尺寸，确保 canvas 充满容器
            const container = document.getElementById('live2d-container');
            if (container) {{
                canvas.width = container.clientWidth;
                canvas.height = container.clientHeight;
            }}


            app = new PIXI.Application({{
                view: canvas,
                width: canvas.width,
                height: canvas.height,
                transparent: true,
                resizeTo: container, // 自动适应父容器大小
            }});

            try {{
                live2dModel = await PIXI.live2d.Live2DModel.from(modelPath);
                app.stage.addChild(live2dModel);

                // 模型缩放和定位 (根据你的模型调整，确保能完全显示)
                // 推荐根据模型原始大小和画布大小计算缩放比例
                live2dModel.scale.set(0.25); // 示例缩放，你可能需要调整
                live2dModel.x = app.view.width / 2;
                live2dModel.y = app.view.height * 0.7; // 调整 Y 轴位置，让模型底部在屏幕底部

                // 自动眨眼、呼吸等物理效果 (通常模型自带)
                live2dModel.motion('Idle'); // 播放待机动作 (如果模型有这个动作)

                // 加载所有表情
                live2dModel.expressions = {{}}; // 清空默认表情，以便我们自己的映射
                for (const emotionName in expressionMap) {{
                    try {{
                        const exprPath = expressionMap[emotionName];
                        const exprData = await fetch(exprPath).then(res => {{
                            if (!res.ok) throw new Error(`HTTP error! status: ${{res.status}} for ${{exprPath}}`);
                            return res.json();
                        }});
                        live2dModel.expressions[emotionName] = new PIXI.live2d.Expression(exprData);
                        console.log(`Loaded expression: ${emotionName}`);
                    }} catch (e) {{
                        console.error(`Failed to load expression ${emotionName} from ${expressionMap[emotionName]}:`, e);
                    }}
                }}

                // 监听窗口大小变化以调整模型位置
                window.addEventListener('resize', () => {{
                    if (container) {{
                        canvas.width = container.clientWidth;
                        canvas.height = container.clientHeight;
                        app.renderer.resize(canvas.width, canvas.height); // 调整渲染器尺寸
                    }}
                    live2dModel.x = app.view.width / 2;
                    live2dModel.y = app.view.height * 0.7;
                }});

                console.log("Live2D model loaded and initialized.");
                setLive2DExpression("neutral"); // 加载后默认设置为中立表情

            }} catch (e) {{
                console.error("Failed to load Live2D model:", e);
            }}
        }}

        // 切换表情的函数
        function setLive2DExpression(expressionName) {{
            if (!live2dModel) {{
                console.warn("Live2D model not ready to set expression.");
                return;
            }}

            if (live2dModel.expressions && live2dModel.expressions[expressionName]) {{
                if (currentExpression === expressionName) {{
                    // console.log(`Expression '${expressionName}' is already active.`);
                    return; // 避免重复设置相同的表情
                }}
                console.log(`Setting Live2D expression: ${expressionName}`);
                live2dModel.setExpression(live2dModel.expressions[expressionName]);
                currentExpression = expressionName;
            }} else {{
                console.warn(`Expression '${expressionName}' not found or not loaded. Attempting neutral.`);
                // 尝试恢复默认表情
                if (live2dModel.expressions && live2dModel.expressions["neutral"] && currentExpression !== "neutral") {{
                    live2dModel.setExpression(live2dModel.expressions["neutral"]);
                    currentExpression = "neutral";
                    console.log("Reverted to neutral expression.");
                }}
            }}
        }}

        // 初始化 Live2D
        document.addEventListener('DOMContentLoaded', initializeLive2D);

        // --- Gradio 和 JavaScript 之间的通信 ---
        // Gradio 会通过 `gr.JSON` 组件将表情指令发送到这里
        // 当 emotion_data 改变时，调用 setLive2DExpression
        // 这是 Gradio 1.x / 2.x 的旧式通信方式，通过在后端更新 gr.JSON，前端监听其值
        // 但 Gradio 4.x 通常不需要手动写 window.gradio_emotion_listener
        // 而是通过 gr.JSON(value=...) 更新后，在 Python 端定义一个 .change() 事件。
        // 然而，对于 HTML 组件内部的 JS，这种直接暴露全局函数的方式有时会奏效。
        // 在 app.py 中，我们将直接在 .submit() 的 output 中更新 gr.JSON 组件，
        // Gradio 会自动处理其值的传递和前端的更新，我们只需要确保前端 JS 能读到。
        // 为了确保前端 JS 能读取到 Gradio 更新的 JSON，通常 Gradio 会暴露一个 JS 钩子。
        // 更推荐的做法是让 `live2d_emotion_instruction` 这个 `gr.JSON` 组件的 `value` 更新时
        // Gradio 自动触发一个前端的更新，然后你在 HTML 模板的 JS 里监听这个更新。
        // 对于你目前的需求，我们假设 `gr.JSON` 的更新会自动触发 JS 的感知。
        // 通常 Gradio 4.x 配合其前端框架（如Svelte/Vue）会有更好的绑定。
        // 我们会通过自定义的 `on_event` 机制来桥接。

        // 用于 Gradio 调用的函数
        window.setLive2DExpressionFromGradio = function(emotionJson) {{
            console.log("Received emotion from Gradio:", emotionJson);
            if (emotionJson && emotionJson.emotion) {{
                setLive2DExpression(emotionJson.emotion);
            }}
        }};
    </script>
</body>
</html>
"""


# 验证 Live2D 资源路径的函数
def validate_live2d_resources():
    """验证 Live2D 模型和 JS 库文件是否存在。"""
    js_files = [
        'assets/live2d_js/live2dcubismcore.min.js',
        'assets/live2d_js/live2d.min.js'
    ]
    all_exist = True
    for js_file in js_files:
        full_path = get_resource_path(js_file)
        if not os.path.exists(full_path):
            print(f"Live2D SDK JS 文件未找到: {full_path}")
            all_exist = False

    model_full_path = get_resource_path(LIVE2D_MODEL_PATH)
    if not os.path.exists(model_full_path):
        print(f"Live2D 模型文件未找到: {model_full_path}")
        all_exist = False

    # 验证表情文件是否存在 (只检查在 expressionMap 中定义的)
    # 这个需要在 HTML 模板中读取 expressionMap，这里只是一个示例验证
    # 实际应从表情映射中获取路径，并遍历验证
    # For now, we trust the HTML template to handle missing expressions gracefully.

    return all_exist


if __name__ == "__main__":
    # 仅供测试
    print(f"Live2D Model Path: {get_resource_path(LIVE2D_MODEL_PATH)}")
    print(f"Live2D JS Path: {get_resource_path('assets/live2d_js/live2d.min.js')}")
    if validate_live2d_resources():
        print("所有 Live2D 资源文件都已找到。")
    else:
        print("部分 Live2D 资源文件缺失，请检查。")