"""
SVG 卡片生成器

基于 svg.html 模板生成精美的双面卡片 SVG。
支持英语单词和汉字两种类型。
"""

from datetime import datetime
from typing import Dict, Tuple, List, Optional
import html


def generate_svg_card(word: str, card_type: str, metadata: Dict) -> Tuple[str, str]:
    """
    生成 SVG 卡片的正反面

    Args:
        word: 单词/汉字
        card_type: 'en' 或 'zh'
        metadata: 卡片元数据字典

    Returns:
        (svg_front, svg_back): 正面和反面的 SVG 字符串
    """
    if card_type == 'zh':
        return generate_chinese_svg(word, metadata)
    elif card_type == 'en':
        return generate_english_svg(word, metadata)
    else:
        raise ValueError(f"Unsupported card_type: {card_type}")


def generate_chinese_svg(word: str, metadata: Dict) -> Tuple[str, str]:
    """
    生成汉字卡片的 SVG

    数据映射:
    - word: 汉字
    - metadata.pinyin: 拼音(数组或字符串)
    - metadata.meaning_zh: 核心意思
    - metadata.radical: 部首
    - metadata.strokes: 笔画数
    - metadata.structure: 结构(左右/上下等)
    - metadata.examples: 高频词组/例句(数组)
    - metadata.memory_tips: 联想记忆法
    - metadata.confusion: 近形字辨析
    """
    # 提取和格式化数据
    pinyin = format_pinyin(metadata.get('pinyin', []))
    tone = extract_tone(pinyin)
    meaning_zh = metadata.get('meaning_zh', '暂无释义')
    meanings = parse_meanings(meaning_zh)

    radical = metadata.get('radical', '—')
    strokes = metadata.get('strokes', '—')
    structure = metadata.get('structure', '—')

    examples = metadata.get('examples', [])
    high_freq_words = examples[:4] if len(examples) > 0 else ['暂无', '词组', '数据', '']

    # 提取例句(从 examples 中找最长的一条作为例句)
    example_sentence = extract_example_sentence(examples, word)

    memory_tip = extract_memory_tip(metadata.get('memory_tips', ''))
    confusion_items = parse_confusion(metadata.get('confusion', ''), word)

    # 生成正面 SVG
    svg_front = f"""<svg width="800" height="500" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #f0f4f8; }}
    .card {{ fill: #ffffff; stroke: #d1d9e6; stroke-width: 2; rx: 15; ry: 15; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1)); }}
    .main-char {{ font-family: "KaiTi", "楷体", "STKaiti", serif; font-size: 100px; fill: #0066cc; font-weight: bold; }}
    .pinyin {{ font-family: Arial, sans-serif; font-size: 32px; fill: #555; }}
    .h2 {{ font-family: "SimHei", "黑体", sans-serif; font-size: 18px; fill: #0066cc; font-weight: bold; }}
    .text {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #333; }}
    .text-light {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #666; }}
    .line {{ stroke: #e0e0e0; stroke-width: 1; stroke-dasharray: 4; }}
  </style>

  <rect width="100%" height="100%" class="bg" />

  <g transform="translate(40, 40)">
    <rect width="720" height="420" class="card" />

    <path d="M 0 15 Q 0 0 15 0 L 705 0 Q 720 0 720 15 L 720 50 L 0 50 Z" fill="#0066cc" opacity="0.1"/>
    <text x="360" y="32" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#0066cc" font-weight="bold">正面：识记</text>

    <circle cx="360" cy="160" r="80" fill="#f9fcff" stroke="#e0efff" stroke-width="2" />
    <text x="360" y="200" text-anchor="middle" class="main-char">{html.escape(word)}</text>
    <text x="360" y="270" text-anchor="middle" class="pinyin">{html.escape(pinyin)}</text>
    <text x="360" y="300" text-anchor="middle" class="text-light">{html.escape(tone)}</text>

    <line x1="60" y1="330" x2="660" y2="330" class="line" />

    <g transform="translate(60, 355)">
      <text x="0" y="0" class="h2">📖 核心意思</text>
      {format_meanings_svg(meanings, y_start=25)}
    </g>
  </g>
</svg>"""

    # 生成反面 SVG
    svg_back = f"""<svg width="800" height="500" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #f0f4f8; }}
    .card {{ fill: #ffffff; stroke: #d1d9e6; stroke-width: 2; rx: 15; ry: 15; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1)); }}
    .h2 {{ font-family: "SimHei", "黑体", sans-serif; font-size: 18px; fill: #0066cc; font-weight: bold; }}
    .text {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #333; }}
    .text-light {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #666; }}
    .highlight {{ fill: #e63946; font-weight: bold; }}
    .box-bg {{ fill: #eef7ff; rx: 5; }}
    .line {{ stroke: #e0e0e0; stroke-width: 1; stroke-dasharray: 4; }}
  </style>

  <rect width="100%" height="100%" class="bg" />

  <g transform="translate(40, 40)">
    <rect width="720" height="420" class="card" />

    <path d="M 0 15 Q 0 0 15 0 L 705 0 Q 720 0 720 15 L 720 50 L 0 50 Z" fill="#28a745" opacity="0.1"/>
    <text x="360" y="32" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#28a745" font-weight="bold">反面：应用与联想</text>

    <g transform="translate(40, 70)">
      <text x="0" y="0" class="h2">✨ 高频词组</text>
      {format_high_freq_words_svg(high_freq_words, y_start=20)}
    </g>

    <g transform="translate(40, 130)">
      <text x="0" y="0" class="h2">🗣️ 经典例句</text>
      {format_example_sentence_svg(example_sentence, word, y_start=25, width=640)}
    </g>

    <line x1="40" y1="210" x2="680" y2="210" class="line" />

    <g transform="translate(40, 230)">
      <text x="0" y="0" class="h2">🧠 联想记忆法</text>
      {format_memory_tip_svg(memory_tip, y_start=25, width=640)}
    </g>

    <g transform="translate(40, 300)">
      <text x="0" y="0" class="h2">🔍 近形字辨析</text>
      {format_confusion_svg(confusion_items, y_start=20)}
    </g>
  </g>
</svg>"""

    return svg_front, svg_back


def generate_english_svg(word: str, metadata: Dict) -> Tuple[str, str]:
    """
    生成英语单词卡片的 SVG

    数据映射:
    - word: 英语单词
    - metadata.phonetic 或 ipa: 音标
    - metadata.meaning_zh: 中文释义
    - metadata.meaning_en: 英文释义
    - metadata.pos: 词性
    - metadata.examples: 例句数组
    """
    # 提取数据
    phonetic = metadata.get('phonetic') or metadata.get('ipa', '')
    meaning_zh = metadata.get('meaning_zh', '')
    meaning_en = metadata.get('meaning_en', '')
    pos = metadata.get('pos', '')
    examples = metadata.get('examples', [])

    # 格式化释义
    meaning_display = meaning_zh or meaning_en or '暂无释义'

    # 提取例句(最多2条)
    example_lines = examples[:2] if examples else []

    # 生成正面 SVG
    svg_front = f"""<svg width="800" height="500" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #f0f4f8; }}
    .card {{ fill: #ffffff; stroke: #d1d9e6; stroke-width: 2; rx: 15; ry: 15; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1)); }}
    .main-word {{ font-family: "Georgia", serif; font-size: 60px; fill: #0066cc; font-weight: bold; }}
    .phonetic {{ font-family: Arial, sans-serif; font-size: 24px; fill: #555; }}
    .h2 {{ font-family: "SimHei", "黑体", sans-serif; font-size: 18px; fill: #0066cc; font-weight: bold; }}
    .text {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #333; }}
    .line {{ stroke: #e0e0e0; stroke-width: 1; stroke-dasharray: 4; }}
  </style>

  <rect width="100%" height="100%" class="bg" />

  <g transform="translate(40, 40)">
    <rect width="720" height="420" class="card" />

    <path d="M 0 15 Q 0 0 15 0 L 705 0 Q 720 0 720 15 L 720 50 L 0 50 Z" fill="#0066cc" opacity="0.1"/>
    <text x="360" y="32" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#0066cc" font-weight="bold">Front: Recognition</text>

    <text x="360" y="200" text-anchor="middle" class="main-word">{html.escape(word)}</text>
    <text x="360" y="250" text-anchor="middle" class="phonetic">{html.escape(phonetic)}</text>
    {f'<text x="360" y="280" text-anchor="middle" class="text">({html.escape(pos)})</text>' if pos else ''}

    <line x1="60" y1="320" x2="660" y2="320" class="line" />

    <g transform="translate(60, 350)">
      <text x="0" y="0" class="h2">📖 释义</text>
      <text x="0" y="30" class="text">{html.escape(meaning_display[:100])}</text>
    </g>
  </g>
</svg>"""

    # 生成反面 SVG
    svg_back = f"""<svg width="800" height="500" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #f0f4f8; }}
    .card {{ fill: #ffffff; stroke: #d1d9e6; stroke-width: 2; rx: 15; ry: 15; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1)); }}
    .h2 {{ font-family: "SimHei", "黑体", sans-serif; font-size: 18px; fill: #0066cc; font-weight: bold; }}
    .text {{ font-family: "SimHei", "黑体", sans-serif; font-size: 14px; fill: #333; }}
    .highlight {{ fill: #e63946; font-weight: bold; }}
    .line {{ stroke: #e0e0e0; stroke-width: 1; stroke-dasharray: 4; }}
  </style>

  <rect width="100%" height="100%" class="bg" />

  <g transform="translate(40, 40)">
    <rect width="720" height="420" class="card" />

    <path d="M 0 15 Q 0 0 15 0 L 705 0 Q 720 0 720 15 L 720 50 L 0 50 Z" fill="#28a745" opacity="0.1"/>
    <text x="360" y="32" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#28a745" font-weight="bold">Back: Application</text>

    <g transform="translate(40, 80)">
      <text x="0" y="0" class="h2">🌟 单词</text>
      <text x="0" y="30" class="text" font-size="24" fill="#0066cc" font-weight="bold">{html.escape(word)}</text>
      <text x="0" y="60" class="text">{html.escape(phonetic)}</text>
    </g>

    <line x1="40" y1="170" x2="680" y2="170" class="line" />

    <g transform="translate(40, 190)">
      <text x="0" y="0" class="h2">📖 完整释义</text>
      {format_text_multiline(meaning_display, y_start=25, width=640, line_height=22)}
    </g>

    <g transform="translate(40, 280)">
      <text x="0" y="0" class="h2">📝 例句</text>
      {format_examples_svg(example_lines, y_start=25, width=640)}
    </g>
  </g>
</svg>"""

    return svg_front, svg_back


# ==================== 辅助函数 ====================

def format_pinyin(pinyin) -> str:
    """格式化拼音显示"""
    if isinstance(pinyin, list):
        return ', '.join(pinyin) if pinyin else '暂无拼音'
    return str(pinyin) if pinyin else '暂无拼音'


def extract_tone(pinyin: str) -> str:
    """从拼音中提取声调说明"""
    if not pinyin or pinyin == '暂无拼音':
        return ''

    # 简单的声调检测(基于拼音字符)
    tone_marks = {
        'ā': '第一声', 'á': '第二声', 'ǎ': '第三声', 'à': '第四声',
        'ē': '第一声', 'é': '第二声', 'ě': '第三声', 'è': '第四声',
        'ī': '第一声', 'í': '第二声', 'ǐ': '第三声', 'ì': '第四声',
        'ō': '第一声', 'ó': '第二声', 'ǒ': '第三声', 'ò': '第四声',
        'ū': '第一声', 'ú': '第二声', 'ǔ': '第三声', 'ù': '第四声',
        'ǖ': '第一声', 'ǘ': '第二声', 'ǚ': '第三声', 'ǜ': '第四声',
    }

    for char in pinyin:
        if char in tone_marks:
            return f"({tone_marks[char]})"

    return ''


def parse_meanings(meaning_zh: str) -> List[str]:
    """解析释义为列表(按顿号、分号、句号分割)"""
    if not meaning_zh:
        return ['暂无释义']

    # 按常见分隔符分割
    meanings = []
    for sep in ['；', ';', '。', '\n']:
        if sep in meaning_zh:
            meanings = [m.strip() for m in meaning_zh.split(sep) if m.strip()]
            break

    if not meanings:
        meanings = [meaning_zh]

    return meanings[:3]  # 最多取3条


def format_meanings_svg(meanings: List[str], y_start: int) -> str:
    """格式化释义为 SVG text 元素"""
    svg_lines = []
    for i, meaning in enumerate(meanings):
        y = y_start + i * 25
        svg_lines.append(f'<text x="0" y="{y}" class="text">{i+1}. {html.escape(meaning)}</text>')
    return '\n      '.join(svg_lines)


def extract_example_sentence(examples: List[str], word: str) -> str:
    """从 examples 中提取包含目标字的例句"""
    if not examples:
        return f'暂无例句。'

    # 找最长的一条作为例句
    sentences = [ex for ex in examples if len(ex) > 4 and word in ex]
    if sentences:
        return sentences[0][:50]  # 限制长度

    # 如果没有包含目标字的,返回第一条
    return examples[0][:50] if examples else '暂无例句。'


def format_high_freq_words_svg(words: List[str], y_start: int) -> str:
    """格式化高频词组为 SVG 矩形框"""
    svg_rects = []
    x_positions = [0, 100, 200, 300]

    for i, word in enumerate(words[:4]):
        x = x_positions[i]
        svg_rects.append(f'''
      <g transform="translate({x}, {y_start})">
        <rect x="0" y="0" width="90" height="35" class="box-bg" />
        <text x="45" y="22" text-anchor="middle" class="text">{html.escape(word)}</text>
      </g>''')

    return ''.join(svg_rects)


def format_example_sentence_svg(sentence: str, word: str, y_start: int, width: int) -> str:
    """格式化例句,高亮目标字"""
    if not sentence or sentence == '暂无例句。':
        return f'<text x="0" y="{y_start}" class="text">暂无例句。</text>'

    # 简单实现:不做复杂的高亮处理,直接显示文本
    lines = wrap_text(sentence, width // 10)
    svg_lines = []
    for i, line in enumerate(lines[:2]):  # 最多2行
        y = y_start + i * 22
        svg_lines.append(f'<text x="0" y="{y}" class="text">{html.escape(line)}</text>')

    return '\n      '.join(svg_lines)


def extract_memory_tip(memory_tips: str) -> str:
    """提取记忆法核心内容"""
    if not memory_tips:
        return '暂无记忆法提示。'

    # 提取第一行或前50字符
    lines = memory_tips.split('\n')
    first_line = lines[0].strip() if lines else memory_tips
    return first_line[:60]


def format_memory_tip_svg(tip: str, y_start: int, width: int) -> str:
    """格式化记忆法提示"""
    lines = wrap_text(tip, width // 10)
    svg_lines = []
    for i, line in enumerate(lines[:2]):  # 最多2行
        y = y_start + i * 22
        svg_lines.append(f'<text x="0" y="{y}" class="text">{html.escape(line)}</text>')

    return '\n      '.join(svg_lines)


def parse_confusion(confusion: str, target_word: str) -> List[Dict]:
    """解析近形字辨析"""
    if not confusion:
        return []

    items = []
    lines = confusion.split('\n')[:3]  # 最多3条

    for line in lines:
        if line.strip():
            items.append({'text': line.strip()[:40]})

    return items


def format_confusion_svg(items: List[Dict], y_start: int) -> str:
    """格式化近形字辨析"""
    if not items:
        return f'<text x="0" y="{y_start}" class="text">暂无辨析。</text>'

    svg_lines = []
    for i, item in enumerate(items[:3]):
        y = y_start + i * 22
        svg_lines.append(f'<text x="0" y="{y}" class="text">{i+1}. {html.escape(item["text"])}</text>')

    return '\n      '.join(svg_lines)


def format_examples_svg(examples: List[str], y_start: int, width: int) -> str:
    """格式化英语例句"""
    if not examples:
        return f'<text x="0" y="{y_start}" class="text">No examples available.</text>'

    svg_lines = []
    for i, example in enumerate(examples[:2]):
        y = y_start + i * 25
        wrapped = wrap_text(example, width // 9)
        for j, line in enumerate(wrapped[:2]):  # 每个例句最多2行
            line_y = y + j * 20
            svg_lines.append(f'<text x="0" y="{line_y}" class="text" font-size="13">{html.escape(line)}</text>')

    return '\n      '.join(svg_lines)


def format_text_multiline(text: str, y_start: int, width: int, line_height: int = 22) -> str:
    """格式化多行文本"""
    lines = wrap_text(text, width // 10)
    svg_lines = []
    for i, line in enumerate(lines[:4]):  # 最多4行
        y = y_start + i * line_height
        svg_lines.append(f'<text x="0" y="{y}" class="text">{html.escape(line)}</text>')

    return '\n      '.join(svg_lines)


def wrap_text(text: str, max_width: int) -> List[str]:
    """文本换行(简单字符数判断)"""
    if len(text) <= max_width:
        return [text]

    lines = []
    current_line = ''

    for char in text:
        if len(current_line) >= max_width:
            lines.append(current_line)
            current_line = char
        else:
            current_line += char

    if current_line:
        lines.append(current_line)

    return lines
