import gradio as gr

# 定义一个简单的函数，它将输入文本原样返回
def greet(name):
    return "你好，" + name + "！"

# 创建 Gradio 界面
# inputs 参数定义了输入组件，这里是一个文本框
# outputs 参数定义了输出组件，这里也是一个文本框
# title 和 description 用于给应用添加标题和描述
iface = gr.Interface(
    fn=greet, # 要调用的函数
    inputs=gr.Textbox(label="请输入你的名字"), # 输入组件：文本框
    outputs=gr.Textbox(label="问候语"), # 输出组件：文本框
    title="Gradio 测试应用", # 应用标题
    description="这是一个简单的 Gradio 应用，用于测试你的 Gradio 库是否正常工作。" # 应用描述
)

# 启动 Gradio 应用
# share=True 会生成一个公共链接，方便分享（可选）
iface.launch(share=False)