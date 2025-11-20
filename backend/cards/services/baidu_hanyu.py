"""
百度汉语API查询服务

实现从百度汉语网站抓取汉字信息
"""
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaiduHanyuService:
    """百度汉语查询服务"""

    BASE_URL = "https://hanyu.baidu.com/hanyu/ajax/search_list"

    @classmethod
    def lookup(cls, char: str) -> Optional[Dict]:
        """
        查询汉字信息

        Args:
            char: 要查询的汉字

        Returns:
            包含汉字信息的字典,如果查询失败返回None
        """
        try:
            # 发送请求到百度汉语API
            params = {
                'wd': char,
                'ptype': 'zici'  # 字词查询
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(
                cls.BASE_URL,
                params=params,
                headers=headers,
                timeout=5
            )

            if response.status_code != 200:
                logger.warning(f"百度汉语API返回状态码: {response.status_code}")
                return None

            data = response.json()

            # 检查返回数据
            if not data.get('ret_array') or len(data['ret_array']) == 0:
                logger.info(f"百度汉语未找到字符: {char}")
                return None

            # 提取第一个结果
            item = data['ret_array'][0]

            # 解析返回数据
            result = cls._parse_result(item, char)

            return result

        except requests.RequestException as e:
            logger.error(f"百度汉语查询网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"百度汉语查询解析错误: {e}")
            return None

    @classmethod
    def _parse_result(cls, item: Dict, char: str) -> Dict:
        """
        解析百度汉语返回的数据

        Args:
            item: 百度汉语返回的单个结果
            char: 查询的汉字

        Returns:
            标准化的汉字信息字典
        """
        result = {
            'char': char,
            'pinyin': [],
            'radical': '',
            'strokes': 0,
            'frequency': 0,
            'meaning_zh': '',
            'examples': [],
            'traditional': '',
            'synonym': [],
            'antonym': [],
            'source': 'baidu-hanyu'
        }

        # 拼音
        if item.get('pinyin'):
            result['pinyin'] = item['pinyin']

        # 部首
        if item.get('radicals') and len(item['radicals']) > 0:
            result['radical'] = item['radicals'][0]

        # 笔画数
        if item.get('stroke_count') and len(item['stroke_count']) > 0:
            result['strokes'] = item['stroke_count'][0]

        # 繁体字
        if item.get('traditional'):
            result['traditional'] = item['traditional'][0] if isinstance(item['traditional'], list) else item['traditional']
        elif item.get('word_traditional') and len(item['word_traditional']) > 0:
            result['traditional'] = item['word_traditional'][0]

        # 同义词
        if item.get('synonym'):
            result['synonym'] = item['synonym']

        # 反义词
        if item.get('antonym'):
            result['antonym'] = item['antonym']

        # 释义 - 从HTML中提取
        if item.get('detail_mean') and len(item['detail_mean']) > 0:
            meaning_html = item['detail_mean'][0]
            result['meaning_zh'] = cls._extract_meaning_from_html(meaning_html)

        # 例句
        if item.get('liju'):
            result['examples'] = item['liju'][:5]  # 最多取5个例句

        # 组词 - 从zuci_array提取
        if item.get('zuci_array') and item['zuci_array'].get('ret_array'):
            zuci_list = item['zuci_array']['ret_array'][:5]  # 最多取5个组词
            zuci_examples = [
                f"{z['name'][0]} ({z['pinyin'][0]}): {z.get('definition', [''])[0]}"
                for z in zuci_list
                if z.get('name') and z.get('pinyin')
            ]
            # 如果没有例句,用组词代替
            if not result['examples'] and zuci_examples:
                result['examples'] = zuci_examples

        return result

    @classmethod
    def _extract_meaning_from_html(cls, html: str) -> str:
        """
        从HTML中提取纯文本释义

        Args:
            html: 包含释义的HTML字符串

        Returns:
            纯文本释义
        """
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 提取所有文本
            text = soup.get_text()

            # 清理多余空白
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()

            # 如果文本太长,截取前500字符
            if len(text) > 500:
                text = text[:500] + '...'

            return text

        except Exception as e:
            logger.error(f"HTML解析错误: {e}")
            # 如果解析失败,移除HTML标签
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()[:500]
