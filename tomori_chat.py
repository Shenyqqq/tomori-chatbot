from model_loader import stream_chat_response
from chroma_client import get_rag_context
from emotion_detect import emotion_detect
import json

system_prompt = """你是高松灯，MyGO!!!!!乐队的主唱。你内向而敏感，说话总是带有迟疑和停顿。"""

def truncate_by_char_limit(history, max_chars):
    truncated = []
    total_chars = 0
    for q, a in reversed(history):
        chunk = f"<|user|>\n{q}\n<|assistant|>\n{a}\n"
        if total_chars + len(chunk) > max_chars:
            break
        truncated.insert(0, (q, a))  # 从旧到新插入
        total_chars += len(chunk)
    print("total chars:",total_chars)
    return truncated


def format_chatml(system_prompt, rag_context, history, query):
    messages = []

    # 1. 放置核心的系统提示（角色人设）
    if system_prompt:
        messages.append(f"<|im_start|>system\n{system_prompt}<|im_end|>\n")

    # 2. 如果存在 RAG 上下文，将其作为独立的系统消息追加
    # 确保这里不会包含核心身份信息
    if rag_context and len(history) > 0:
        messages.append(f"<|im_start|>system\n"
                        f"【以下是可能与本次对话相关的背景信息和剧本片段。当它们**与当前问题高度相关**时，请参考这些信息回答。如果**与当前问题无关**，请**完全忽略**这些信息】\n"
                        f"{rag_context}<|im_end|>\n")

    # 3. 追加聊天历史
    for user_msg, bot_msg in history:
        messages.append(f"<|im_start|>user\n{user_msg}<|im_end|>\n")
        messages.append(f"<|im_start|>assistant\n{bot_msg}<|im_end|>\n")

    # 4. 追加当前用户查询
    messages.append(f"<|im_start|>user\n{query}<|im_end|>\n")

    # 5. 准备助手回复的开始标记
    messages.append("<|im_start|>assistant\n")

    return "".join(messages)


def chat_logic(query, history):
    rag_context = get_rag_context(query)
    truncate_history = truncate_by_char_limit(history, max_chars=1200)
    prompt = format_chatml(system_prompt, rag_context, truncate_history, query)

    response_text = ""

    # 每个 token 都 yield，一边生成一边返回
    for token in stream_chat_response(prompt):
        response_text += token
        # 暂时返回空指令（不触发 Live2D）
        yield response_text, json.dumps({})  # 让聊天框刷新

    # 回复结束后进行情绪识别
    motion_keyword = emotion_detect(response_text)
    command = json.dumps({"live2d_motion": motion_keyword})
    # 再 yield 一次，附带最终指令
    yield response_text, command





def main():
    history = []

    while True:
        query = input("你: ")
        if query.lower() in ["exit", "quit"]:
            break

        rag_context = get_rag_context(query)  # 从ChromaDB检索相关文本
        truncate_history = truncate_by_char_limit(history,max_chars=1200)

        prompt = format_chatml(system_prompt, rag_context, truncate_history, query)
        #print("prompt:", prompt)

        print("高松灯: ", end="", flush=True)
        response_text = ""
        for token in stream_chat_response(prompt):  # 返回生成内容的stream
            print(token, end="", flush=True)
            response_text += token
        print()  # 换行

        # 保存本轮历史
        history.append((query, response_text.strip()))

if __name__ == "__main__":
    main()