# 示例以transformers为基础，你可替换为自己的推理代码
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
from threading import Thread
from peft import PeftModel

model_path = "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, pad_token="<|endoftext|>")
model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True)
model = PeftModel.from_pretrained(model, "./lora_model/checkpoint-70")


def stream_chat_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generate_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=128,
        do_sample=True,
        eos_token_id=tokenizer.convert_tokens_to_ids("<|im_end|>"),
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.2,
        no_repeat_ngram_size=10
    )

    thread = Thread(target=model.generate, kwargs=generate_kwargs)
    thread.start()

    for new_token in streamer:
        yield new_token
