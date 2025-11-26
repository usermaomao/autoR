"""
AI服务 - 处理AI模型调用
"""
import requests
import urllib3

# 全局禁用SSL警告（仅开发环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AIService:
    """AI服务类"""

    def __init__(self, config):
        """
        初始化AI服务

        Args:
            config: AIConfig 对象
        """
        self.config = config
        self.api_key = config.get_api_key()
        self.base_url = config.base_url.rstrip('/')
        self.model_name = config.model_name
        self.provider = config.provider
        # 根据任务类型动态调整参数
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.use_json_format = True  # 启用JSON格式输出

    def _call_api(self, messages):
        """
        调用AI API

        Args:
            messages: 消息列表

        Returns:
            API响应内容
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # 根据provider调整请求格式
        if self.provider in ['openai', 'local']:
            # OpenAI兼容格式
            url = f'{self.base_url}/chat/completions'
            data = {
                'model': self.model_name,
                'messages': messages,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
        elif self.provider == 'anthropic':
            # Claude API格式
            url = f'{self.base_url}/messages'
            headers['x-api-key'] = self.api_key
            headers['anthropic-version'] = '2023-06-01'
            del headers['Authorization']

            data = {
                'model': self.model_name,
                'messages': messages,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
        else:
            raise ValueError(f'不支持的provider: {self.provider}')

        # 创建自定义会话，配置SSL和重试策略
        session = requests.Session()

        # 配置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔倍数
            status_forcelist=[429, 500, 502, 503, 504],  # 遇到这些状态码时重试
            allowed_methods=["HEAD", "GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            response = session.post(
                url,
                headers=headers,
                json=data,
                timeout=60,  # 增加超时时间到60秒
                verify=False  # 禁用SSL证书验证（仅开发环境）
            )
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            raise Exception(f'SSL连接失败: {str(e)}. 请检查网络配置，或联系管理员配置SSL证书。')
        except requests.exceptions.Timeout:
            raise Exception('请求超时(60秒)，请检查网络连接或API服务状态。可能原因：网络慢、API服务响应慢。')
        except requests.exceptions.ConnectionError as e:
            raise Exception(f'网络连接失败: {str(e)}. 请检查API地址是否正确，网络是否可达。')
        except requests.exceptions.HTTPError as e:
            # 提取API错误信息
            try:
                error_detail = response.json()
                error_msg = error_detail.get('error', {}).get('message', str(e))
            except:
                error_msg = str(e)
            raise Exception(f'API返回错误(状态码{response.status_code}): {error_msg}')
        except requests.exceptions.RequestException as e:
            raise Exception(f'API请求失败: {str(e)}')
        finally:
            session.close()

        result = response.json()

        # 解析响应
        if self.provider in ['openai', 'local']:
            return result['choices'][0]['message']['content']
        elif self.provider == 'anthropic':
            return result['content'][0]['text']

    def test_connection(self):
        """
        测试API连接

        Returns:
            bool: 连接是否成功
        """
        messages = [
            {'role': 'user', 'content': 'Hello'}
        ]

        try:
            self._call_api(messages)
            return True
        except Exception as e:
            raise Exception(f'连接测试失败: {str(e)}')

    def summarize_word(self, word, card_type, context=''):
        """
        使用AI总结词汇

        Args:
            word: 单词或汉字
            card_type: 'en' 或 'zh'
            context: 额外上下文信息

        Returns:
            AI生成的总结内容
        """
        # 根据卡片类型调整参数
        if card_type == 'zh':
            self.temperature = 0.5  # 降低随机性,保证格式稳定
            self.max_tokens = 2800   # 汉字内容较多
        else:
            self.temperature = 0.5
            self.max_tokens = 600

        if card_type == 'en':
            prompt = self._build_english_prompt(word, context)
            messages = [
                {'role': 'system', 'content': '你是一个专业的语言学习助手，擅长帮助学生理解和记忆词汇。'},
                {'role': 'user', 'content': prompt}
            ]
        else:
            prompt = self._build_chinese_prompt(word, context)
            # 添加 few-shot 示例
            messages = [
                {'role': 'system', 'content': '你是一个专业的语言学习助手，擅长帮助学生理解和记忆词汇。请严格按照要求的格式输出。'},
                {'role': 'user', 'content': f'请为汉字「{word}」生成学习卡片'},
                {'role': 'assistant', 'content': self._get_chinese_example()},
                {'role': 'user', 'content': prompt}
            ]

        return self._call_api(messages)

    def _build_english_prompt(self, word, context):
        """构建英语单词总结提示词"""
        prompt = f"""请帮我总结英语单词 "{word}" 的学习要点，包括：

1. **核心含义**：最常用的1-2个中文释义
2. **词性与用法**：主要词性和典型用法
3. **记忆技巧**：词根词缀、联想记忆或谐音等
4. **常用搭配**：2-3个高频短语或搭配
5. **例句**：1-2个实用例句（中英对照）
6. **易混词**：容易混淆的相似单词（如果有）

{f'额外信息：{context}' if context else ''}

请用简洁、易懂的语言，帮助记忆和理解。"""
        return prompt

    def _build_chinese_prompt(self, char, context):
        """构建汉字记忆学习方案提示词（9节完整版，匹配前端解析）"""
        # 如果有自定义提示词,使用自定义提示词
        if hasattr(self.config, 'custom_chinese_prompt') and self.config.custom_chinese_prompt:
            # 使用自定义提示词,替换占位符
            custom_prompt = self.config.custom_chinese_prompt
            custom_prompt = custom_prompt.replace('{char}', char)
            if context:
                custom_prompt = custom_prompt.replace('{context}', context)
            else:
                # 如果没有context,移除{context}占位符
                custom_prompt = custom_prompt.replace('{context}', '')
            return custom_prompt

        # 使用9节结构的默认提示词（匹配前端解析逻辑）
        prompt = f"""你是一名专业记忆学家兼资深语文教师。请为汉字「{char}」生成学习卡片。

请严格按照以下9节结构输出（必须包含章节编号1-9）：

**1. 关键要点**
- 该字的核心特征（如：常用度、难度、特殊性）
- 学习重点（如：多音字、易错点）

**2. 核心卡片**
拼音与声调: [拼音]
部首/结构/笔画: [部首], [结构], [笔画数]
高频义项: [1-2个最常用的意思]
常见词: [4个高频词组，用顿号分隔]

**3. 构形拆解与联想**
- 字形拆解（如：左右结构、上下结构）
- 部件含义（如：氵表示水）
- 形象联想（如：森林的"森"三个木）

**4. 读音记忆**
- 声母韵母记忆法
- 谐音联想（如果适用）
- 与其他同音字的区别

**5. 书写与笔顺**
- 关键笔画顺序
- 易错笔画提醒
- 书写注意事项

**6. 易混辨析**
- 与 [近形字1] 区别：[关键差异]
- 与 [近形字2] 区别：[关键差异]
- 与 [近形字3] 区别：[关键差异]（如果有）

**7. 语境与搭配**
高频搭配: [常用词组或短语]
造句: [一个实用例句]

**8. 记忆方案设计**
- 第1步：[记忆步骤1]
- 第2步：[记忆步骤2]
- 第3步：[记忆步骤3]

**9. 一句话总结**
- [用一句话总结该字的核心要点和记忆方法]

{f'额外信息: {context}' if context else ''}

请严格按照上述格式输出，不要遗漏任何章节编号。"""
        return prompt

    def _get_chinese_example(self):
        """返回汉字学习卡片的标准示例（9节完整版，匹配前端解析）"""
        return """**1. 关键要点**
- 常用字，使用频率高
- 左右结构，木字旁
- 注意与"眠""绵"区分

**2. 核心卡片**
拼音与声调: mián
部首/结构/笔画: 木, 左右结构, 12画
高频义项: 棉花（植物）、棉制品
常见词: 棉花、棉被、棉衣、棉纺

**3. 构形拆解与联想**
- 左边"木"表示植物，右边"帛"表示丝织品
- 联想：木本植物产出的白色纤维，像丝绸一样柔软
- 记忆：木头旁边的白色丝绸就是棉花

**4. 读音记忆**
- 声母m，韵母ian，第二声
- 谐音"绵"，都是柔软的意思
- 与"眠"同音但意义不同

**5. 书写与笔顺**
- 先写左边"木"，再写右边"帛"
- 右边"帛"上面是"白"，下面是"巾"
- 注意右边不要写成"绵"的纟旁

**6. 易混辨析**
- 与"眠"区别：眠（目部）表示睡觉；棉（木部）表示植物
- 与"绵"区别：绵（纟部）表示丝绸、延续；棉（木部）表示棉花
- 与"面"区别：面（面部）表示脸；棉（木部+巾）表示棉花

**7. 语境与搭配**
高频搭配: 棉花田、棉纺织、纯棉制品
造句: 这条棉被非常暖和，适合冬天使用。

**8. 记忆方案设计**
- 第1步：记住"木"旁表示植物
- 第2步：联想棉花是木本植物的白色纤维
- 第3步：通过"棉被"等常用词强化记忆

**9. 一句话总结**
- 棉（mián）是木字旁，表示产棉花的植物，常用于棉被、棉衣等词。"""

    @staticmethod
    def get_default_chinese_prompt():
        """
        获取默认的汉字提示词模板（9节完整版）
        用于前端显示和编辑
        """
        return """你是一名专业记忆学家兼资深语文教师。请为汉字「{char}」生成学习卡片。

请严格按照以下9节结构输出（必须包含章节编号1-9）：

**1. 关键要点**
- 该字的核心特征（如：常用度、难度、特殊性）
- 学习重点（如：多音字、易错点）

**2. 核心卡片**
拼音与声调: [拼音]
部首/结构/笔画: [部首], [结构], [笔画数]
高频义项: [1-2个最常用的意思]
常见词: [4个高频词组，用顿号分隔]

**3. 构形拆解与联想**
- 字形拆解（如：左右结构、上下结构）
- 部件含义（如：氵表示水）
- 形象联想（如：森林的"森"三个木）

**4. 读音记忆**
- 声母韵母记忆法
- 谐音联想（如果适用）

**5. 书写与笔顺**
- 关键笔画顺序
- 易错笔画提醒

**6. 易混辨析**
- 与 [近形字1] 区别：[关键差异]
- 与 [近形字2] 区别：[关键差异]

**7. 语境与搭配**
高频搭配: [常用词组或短语]
造句: [一个实用例句]

**8. 记忆方案设计**
- 第1步：[记忆步骤1]
- 第2步：[记忆步骤2]

**9. 一句话总结**
- [用一句话总结该字的核心要点和记忆方法]

{context}

请严格按照上述格式输出，不要遗漏任何章节编号。"""
