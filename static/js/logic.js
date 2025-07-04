
live2d_js_code = f"""
console.log("Script block started."); // 脚本开始执行

const modelPath = "{live2d_model_path}"; // 由 Python 注入的模型路径

console.log("Model Path derived from Python:", modelPath); // 打印从 Python 注入的模型路径
let app; // 声明为全局或更广作用域
let model; // 声明为全局或更广作用域

(async function() {{
    console.log("Async IIFE (Immediately Invoked Function Expression) started.");

    const canvasElement = document.getElementById('live2d-canvas');
    console.log("Canvas element check:", !!canvasElement ? "Found" : "Not Found");
    if (!canvasElement) {{
        console.error("Critical Error: Live2D canvas element 'live2d-canvas' not found in DOM.");
        return; 
    }}

    // *** IMPORTANT CHECK: Ensure PIXI and PIXI.live2d are loaded ***
    if (typeof PIXI === 'undefined') {{
        console.error("CRITICAL ERROR: PIXI.js library is not loaded or defined!");
        // Display error on canvas if PIXI is not there
        const ctx = canvasElement.getContext('2d');
        ctx.fillStyle = 'red';
        ctx.font = '16px Arial';
        ctx.fillText('PIXI.js 库未加载！', 10, 50);
        return;
    }}
    if (typeof PIXI.live2d === 'undefined') {{
        console.error("CRITICAL ERROR: PIXI.live2d-display library is not loaded or defined!");
        // Display error on canvas if PIXI.live2d is not there
        const ctx = canvasElement.getContext('2d');
        ctx.fillStyle = 'red';
        ctx.font = '16px Arial';
        ctx.fillText('Live2D Display 库未加载！', 10, 50);
        ctx.fillText("请检查'index.min.js'或'live2d-cubism-pixi.js'的引用", 10, 80);
        return;
    }}
    // *** END IMPORTANT CHECK ***


    app = new PIXI.Application({{
        view: canvasElement,
        autoStart: true,
        resizeTo: window,
        backgroundAlpha: 0,
    }});
    console.log("PIXI Application initialized successfully.");

    try {{
        console.log("Attempting to load Live2D model from:", modelPath);
        model = await PIXI.live2d.Live2DModel.from(modelPath);
        app.stage.addChild(model);
        console.log("Live2D Model loaded and added to stage.");

        // 调整模型大小和位置
        model.scale.set(0.25); // 根据你的模型大小调整
        model.anchor.set(0.5, 0.5);

        function onResize() {{
            if (model) {{
               model.position.set(window.innerWidth / 2, window.innerHeight / 1.8);
               console.log("Model position updated on resize.");
            }} else {{
                console.warn("Model not available for resize positioning.");
            }}
        }}
        window.addEventListener('resize', onResize);
        onResize();

        console.log("Live2D Model loading process initiated (PIXI level).");
        model.on('load', () => {{
            console.log("Live2D Model successfully loaded and parsed.", {{ motions: model.motions, expressions: model.expressions }});
            console.log("Available motion groups:", Object.keys(model.motions));
            console.log("Available expressions:", Object.keys(model.expressions));
        }});
        model.on('error', (error) => {{
            console.error("Live2D Model encountered an error AFTER initial loading/parsing:", error);
            const ctx = canvasElement.getContext('2d');
            ctx.fillStyle = 'red';
            ctx.font = '16px Arial';
            ctx.fillText('模型运行时错误：' + error.message, 10, 110);
        }});

        // 核心功能：监听来自 Gradio 的指令
        function handleCommand(command) {{
            console.log("handleCommand received:", command);
            if (!model) {{ // 检查模型是否已初始化
                console.warn("handleCommand: Live2D model is not initialized yet. Skipping command.");
                return;
            }}
            if (!command || typeof command.live2d_motion === 'undefined') {{
                console.warn("Received invalid command or missing 'live2d_motion' property:", command);
                if (model) {{ model.expression(null); }}
                return;
            }}

            console.log("Received command from Gradio:", command);
            const motionToPlay = command.live2d_motion;

            if (model) {{
                console.log(`Attempting to play motion: "${{motionToPlay}}"`);
                const played = model.motion(motionToPlay, 0, PIXI.live2d.MotionPriority.FORCE);
                if (played) {{
                    console.log(`Successfully playing Live2D motion: ${{motionToPlay}}`);
                }} else {{
                    console.warn(`Motion group '${{motionToPlay}}' not found or failed to play. Falling back to idle.`);
                    if (model.motions && model.motions.idle01) {{
                         console.log("Falling back to idle01 motion.");
                         model.motion('idle01', 0, PIXI.live2d.MotionPriority.NORMAL);
                    }} else {{
                        console.log("Falling back to default expression (null).");
                        model.expression(null);
                    }}
                }}
            }} else {{
                console.warn("Live2D model not yet loaded, cannot play motion:", motionToPlay);
            }}
        }}

        // 使用 MutationObserver 监听 Gradio UI 中隐藏元素的变化
        const targetNode = window.parent.document.querySelector('#live2d_command_stream');
        console.log("Attempting to find #live2d_command_stream:", !!targetNode ? "Found" : "Not Found");
        if (targetNode) {{
            const observer = new MutationObserver(mutationsList => {{
                for(let mutation of mutationsList) {{
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                        const commandText = mutation.addedNodes[0].textContent;
                        console.log("MutationObserver detected change. Raw command text:", commandText);
                        try {{
                            if(commandText){{
                                const command = JSON.parse(commandText);
                                handleCommand(command);
                            }} else {{
                                console.warn("MutationObserver: commandText was empty.");
                            }}
                        }} catch (e) {{
                            console.error("Failed to parse command (JSON error):", commandText, e);
                        }}
                    }}
                }}
            }});
            observer.observe(targetNode, {{ childList: true }});
            console.log("Observer successfully attached to #live2d_command_stream.");
        }} else {{
            console.error("#live2d_command_stream not found in parent document. Gradio communication might fail.");
        }}

    }} catch (error) {{
        console.error("CRITICAL ERROR: Failed to load Live2D model or PIXI/Live2D setup failed:", error);
        const canvas = document.getElementById('live2d-canvas');
        if (canvas) {{
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'red';
            ctx.font = '16px Arial';
            ctx.fillText('模型加载失败，请检查路径和网络连接', 10, 50);
            ctx.fillText(error.message, 10, 80);
            console.log("Error message displayed on canvas.");
        }}
    }}
}})();
"""
