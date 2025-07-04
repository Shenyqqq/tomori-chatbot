import re

MOTION_KEYWORDS = {
    # 愤怒（弱气版）
    'angry01': ['那个……不行', '这样……太过分了', '讨厌……', '不要这样……', r'不要这样',r'够了！',r'不可以！'],
    'angry02': ['真的……生气了', '请……停下来', '太过分……了', r'太过分了'],

    # 告别（小声犹豫）
    'bye01': ['先……走了', '下次……再见', '拜拜……', '我……该走了', r'先走了', r'再见', r'拜拜', r'嗨', r'哈喽'],

    # 哭泣（脆弱感+断句）
    'cry01': ['呜……', '好难过……', '眼泪……停不下来', r'好难过', r'眼泪停不下来',r'不要这样'],
    # 注意：cry02 和 cry03 似乎更偏向“感动”或“惊喜”而不是纯粹的哭泣，这里保留，但在匹配时可能需要注意优先级
    'cry02': ['好厉害……', '太棒了……', '感动……', r'好厉害', r'太棒了'],
    'cry03': ['谢谢……！', '哽咽……说不出来', '眼泪……在打转', r'谢谢你', r'哽咽说不出来', r'眼泪在打转'],
    'cry04': [r'呜哇',r'唔呜'],
    'cry05': ['一定要', '为什么……总是我', r'为什么总是我'],

    # 发呆/沉默（非语言动作） - 优先匹配
    'idle01': [r'(沉默)', r'发呆', r'不知道说什么', r'沉默'],

    # 感动（含哭腔）
    'kandou01': ['谢谢你', '感动……', r'谢谢'],
    'kandou02': ['眼泪……流出来了', '心里……暖暖的', r'眼泪流出来了', r'心里暖暖的'],
    'kandou03': ['哭得……停不下来', '被彻底……感动了', r'哭得停不下来', r'被彻底感动了'],

    # 决心（但仍犹豫）
    'kime01': ['决定……好了', '就……这样吧', '选择……这个', r'决定好了', r'就这样吧', r'选择这个'],
    'kime02': ['必须……要做了', '这次……一定要', r'必须要做', r'这次一定要'],

    # 普通回应（简短停顿）
    'nf01': ['不是的', '不是哦', '不……不是', r'不是',r'不行'],
    'nf_left01': ['左边……有什么吗', '那边……好像……', r'左边', r'那边好像'],
    'nf_right01': ['右边……有声音', '看向……右侧', r'右边', r'右边好像'],

    # 无感情状态（肢体语言为主） - 优先匹配
    'nnf01': [r'<低头……>', r'<摆弄衣角……>', r'<沉默……>', r'低头', r'摆弄衣角'],  # 注意：<沉默...> 和 idle01 有重叠
    'nnf_left01': ['向左看'],
    'nnf_right01': ['向右看'],

    # 悲伤（抑郁倾向）
    'sad01': ['不开心……', '对不起……', r'不开心', r'对不起'],
    'sad02': ['对……对不起', r'对对不起'],
    'sad03': ['对、对不起', '做不到……', r'做不到'],

    # 严肃（但仍结巴）
    'serious01': ['认真', '这不是……开玩笑', r'这不是开玩笑',r'……！'],
    'serious02': ['非常重要……的事情', r'非常重要的事情'],

    # 害羞（脸红+退缩）
    'shame01': ['害羞……', '脸好烫……', '不要……看我', r'害羞', r'脸好烫', r'不要看我'],
    'shame02': ['不好意思', '不……不要', r'不好意思', r'不、不要'],

    # 唱歌（小声/颤抖）
    'sing01': ['小声……哼唱', '啦啦……啦', r'小声哼唱', r'啦啦啦'],
    'sing02': ['颤抖着……唱歌', '鼓起勇气……唱出来', r'颤抖着唱歌', r'鼓起勇气唱出来'],

    # 开心（收敛的笑）
    'smile01': ['哈哈', '嘿嘿……', r'嘿嘿'],
    'smile02': ['开心……', '高兴', r'开心', r'高兴'],
    'smile03': ['嘻嘻', '笑得……肚子痛', r'嘻嘻', r'笑得肚子痛'],
    'smile04': ['偷偷……笑了', r'偷偷笑了'],

    # 惊讶（被吓到）
    'surprised01': ['诶……？！', '啊……！', r'诶'],

    # 思考（犹豫不决）
    'thinking01': [r'…{4,}', '让我……想想', r'让我想想'],
    'thinking02': [r'…{4,}？', '纠结……', r'纠结']
}


# 为特殊符号和省略号创建更通用的正则表达式模式
def create_flexible_pattern(keyword):
    # 如果是纯粹的非语言动作（如 <发呆...>），则精确匹配，不需要复杂的正则处理
    if re.match(r'^<.*>$', keyword):
        return re.escape(keyword)  # 直接转义整个字符串，精确匹配

    # 先对整个关键词进行转义，确保所有特殊字符都被正确处理
    pattern = re.escape(keyword)

    # 替换中文省略号和英文点，使其匹配0个或多个点或中文省略号
    # 注意：这里的替换应该在 re.escape() 之后，并且确保替换的模式是正确的
    # 例如，原来被 re.escape 转义的 \. 才能被 \. 匹配
    pattern = pattern.replace(r'\.\.\.', r'(?:…|\.{3,})*')  # 匹配 "..." 或 "……" 0次或多次
    pattern = pattern.replace(r'…', r'(?:…|\.{3,})*')  # 匹配 "..." 或 "……" 0次或多次

    # 替换问号和感叹号，允许0个或多个
    pattern = pattern.replace(r'\?', r'[？?]*')  # 匹配中文问号或英文问号 0次或多次
    pattern = pattern.replace(r'!', r'[！!]*')  # 匹配中文感叹号或英文感叹号 0次或多次

    # 允许关键词内部的空格变为任意数量的空格或没有
    pattern = pattern.replace(r'\ ', r'\s*')

    return pattern


# 预处理 MOTION_KEYWORDS，将所有关键词转换为其灵活的正则表达式模式
# 并为纯粹的非语言动作设置更高的优先级
FLEXIBLE_MOTION_PATTERNS = {}
# 设定优先级：非语言动作 > 带有感叹号/问号的特定语气 > 一般关键词
PRIORITY_ORDER = {
    'idle01': 3, 'nnf01': 3, 'nnf_left01': 3, 'nnf_right01': 3,  # 非语言动作最高优先级
    'surprised01': 2, 'cry01': 2, 'angry01': 2, 'nf01': 2, 'shame02': 2 # 带有强烈语气的关键词次高优先级
    # 其他情绪为默认优先级 1
}

for emotion, keywords in MOTION_KEYWORDS.items():
    FLEXIBLE_MOTION_PATTERNS[emotion] = []
    for keyword in keywords:
        # 对于纯粹的非语言动作（如 <发呆...>），直接转义后作为模式
        if re.match(r'^<.*>$', keyword):
            FLEXIBLE_MOTION_PATTERNS[emotion].append((re.escape(keyword), PRIORITY_ORDER.get(emotion, 1)))
        else:
            FLEXIBLE_MOTION_PATTERNS[emotion].append((create_flexible_pattern(keyword), PRIORITY_ORDER.get(emotion, 1)))


def emotion_detect(text):
    text_lower = text.lower()

    # 存储每个情绪及其匹配到的最高优先级和得分
    matched_emotions = {}  # {'emotion': {'score': X, 'priority': Y}}

    for emotion, patterns_with_priority in FLEXIBLE_MOTION_PATTERNS.items():
        for pattern_str, priority in patterns_with_priority:
            # 尝试匹配模式
            matches = re.finditer(pattern_str, text_lower)
            count = sum(1 for _ in matches)

            if count > 0:
                current_score = count * priority
                # 如果这个情绪还没有被匹配过，或者当前的匹配得分更高（或优先级更高）
                if emotion not in matched_emotions or \
                        current_score > matched_emotions[emotion]['score'] or \
                        (current_score == matched_emotions[emotion]['score'] and priority > matched_emotions[emotion][
                            'priority']):
                    matched_emotions[emotion] = {'score': current_score, 'priority': priority}

    # 如果没有任何匹配，返回默认的 idle01
    if not matched_emotions:
        return "idle01"

    # 根据优先级和分数选择最可能的情绪
    # 先按优先级降序排序，优先级相同再按分数降序排序
    sorted_emotions = sorted(
        matched_emotions.items(),
        key=lambda item: (item[1]['priority'], item[1]['score']),
        reverse=True
    )

    most_likely_emotion = sorted_emotions[0][0]
    print(
        f"检测到情绪: {most_likely_emotion} (得分: {matched_emotions[most_likely_emotion]['score']}, 优先级: {matched_emotions[most_likely_emotion]['priority']})")
    return most_likely_emotion


if __name__ == '__main__':
    print("--- 情感检测测试开始 ---")

    test_cases = [
        "我真的好难过……眼泪停不下来。",  # 哭泣
        "谢谢你！我真的太感动了。",      # 感动 (cry03 或 kandou01/02)
        "那个……不行，太过分了！",      # 愤怒
        "先走了，拜拜！",               # 告别
        "嗯……让我想想……",             # 思考
        "<低头……>",                     # 非语言动作 (nnf01)
        "这，这不是开玩笑！",            # 严肃
        "脸好烫……好害羞啊。",           # 害羞
        "哈哈，今天真开心！",            # 开心
        "诶？！发生什么了？",            # 惊讶
        "左边好像有声音。",             # 方向 nf_left01
        "我只是在发呆。",                # 发呆 idle01
        "我不知道说什么。",               # 沉默 idle01
        "对、对不起，我做不到。",          # 悲伤/对不起 sad03
        "小声哼唱着歌。",                 # 唱歌 sing01
        "这句文本没有任何关键词。",        # 默认情绪
        "不要这样！呜……",                # 愤怒+哭泣 (angry01/cry01) - 看优先级和匹配逻辑
        "谢谢！我心里暖暖的。",           # 感动 kandou02
        "必须要做，这次一定要成功！",     # 决心 kime02
    ]

    for i, text in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1} ---")
        print(f"输入文本: \"{text}\"")
        detected_emotion = emotion_detect(text)
        print(f"最终检测结果: {detected_emotion}")
        print("-" * 20)

    print("\n--- 情感检测测试结束 ---")