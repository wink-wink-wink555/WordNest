"""
大语言模型服务层
处理与LLM相关的业务逻辑
"""
import json
import requests
from flask import current_app


class LLMService:
    """大语言模型服务类"""
    
    @staticmethod
    def _call_deepseek_api(messages, response_format=None):
        """
        调用DeepSeek API
        
        Args:
            messages: 消息列表
            response_format: 响应格式，可选 {"type": "json_object"}
            
        Returns:
            API响应内容，失败返回None
        """
        try:
            api_key = current_app.config.get('DEEPSEEK_API_KEY')
            base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
            
            if not api_key:
                current_app.logger.error("未配置DEEPSEEK_API_KEY")
                return None
            
            url = f"{base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            data = {
                'model': 'deepseek-chat',
                'messages': messages,
                'temperature': 0.7
            }
            
            if response_format:
                data['response_format'] = response_format
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return content
        except Exception as e:
            current_app.logger.error(f"调用DeepSeek API时出错: {str(e)}")
            return None
    
    @staticmethod
    def generate_example(word, part_of_speech, meaning):
        """
        使用DeepSeek API生成例句
        
        Args:
            word: 单词
            part_of_speech: 词性
            meaning: 释义
            
        Returns:
            生成的例句字符串，失败返回None
        """
        if not word or not meaning:
            return None
        
        try:
            prompt = f"""请为单词 '{word}' ({part_of_speech}) 生成一个自然、简单易懂且地道的英语例句，
要体现它的含义：'{meaning}'与常用用法。
直接输出句子与这句话的中文意思，不要有任何其它解释。"""

            messages = [
                {
                    'role': 'system',
                    'content': '你是一个英语学习助手，擅长生成简单易懂的例句。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            example = LLMService._call_deepseek_api(messages)
            
            if example:
                # 简单清理
                example = example.strip()
                example = example.replace('"', '').replace('"', '').replace('"', '')
                if example.startswith("'") and example.endswith("'"):
                    example = example[1:-1]
            
            return example
        except Exception as e:
            current_app.logger.error(f"生成例句时出错: {str(e)}")
            return None
    
    @staticmethod
    def generate_note(word, part_of_speech, meaning):
        """
        使用DeepSeek API生成学习笔记
        
        Args:
            word: 单词
            part_of_speech: 词性
            meaning: 释义
            
        Returns:
            生成的笔记字符串，失败返回None
        """
        if not word or not meaning:
            return None
        
        try:
            prompt = f"""请为英语单词 '{word}' ({part_of_speech}) 编写一个简短的学习笔记或记忆技巧，50字以内，包含：
1. 记忆技巧或联想方法
2. 常见用法提示（如固定搭配等）
3. 易混淆点提醒
帮助中国学生记住它的含义：'{meaning}'。
只返回笔记内容，不要有标题或任何其他说明。"""

            messages = [
                {
                    'role': 'system',
                    'content': '你是一个英语学习助手，擅长帮助中国学生记忆英语单词。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            note = LLMService._call_deepseek_api(messages)
            
            if note:
                # 简单清理
                note = note.strip()
                note = note.replace('"', '').replace('"', '').replace('"', '')
                if note.startswith("'") and note.endswith("'"):
                    note = note[1:-1]
            
            return note
        except Exception as e:
            current_app.logger.error(f"生成笔记时出错: {str(e)}")
            return None
    
    @staticmethod
    def generate_full_word_info(word):
        """
        使用DeepSeek API生成完整的单词信息（支持多重释义，同一词性的释义合并）
        
        Args:
            word: 单词
            
        Returns:
            包含完整单词信息的字典，包括多个词性的释义、例句、笔记
            格式：
            {
                "definitions": [
                    {
                        "part_of_speech": "n.",
                        "meaning": "释义1；释义2",
                        "example": "例句1（英文+中文）\n\n例句2（英文+中文）",
                        "note": "学习笔记"
                    },
                    ...
                ]
            }
            或包含错误信息：
            {
                "error": "错误信息"
            }
        """
        if not word:
            return {"error": "单词不能为空"}
        
        try:
            prompt = f"""请为英语单词 '{word}' 生成完整的学习信息。

可用的词性列表（共12个）：
- n. (名词)
- v. (动词)
- adj. (形容词)
- adv. (副词)
- prep. (介词)
- conj. (连词)
- pron. (代词)
- interj. (感叹词)
- num. (数词)
- art. (冠词)
- phr. (短语)

要求：
1. 首先验证输入是否为合法的英语单词或短语，如果不是（如中文、数字、乱码等），返回包含error字段的JSON
2. 按词性分组，每个词性一个definition对象
3. 同一词性如果有多个释义，用分号"；"分隔放在meaning字段中
4. 例句格式：英文句子\n中文翻译，自然、简单易懂且地道的英语例句，要体现它的释义含义与常用用法
5. 学习笔记要包含巧记技巧、常用搭配等，80字以内
6. 无论是释义还是词性，排在前面的一定是更常用的
7. 必须严格按照以下JSON格式返回：

成功时返回：
{{
    "definitions": [
        {{
            "part_of_speech": "词性（必须从上面12个中选择）",
            "meaning": "释义1；释义2；释义3",
            "example": "英文\\n例句",
            "note": "学习笔记（包括巧记技巧等）"
        }}
    ]
}}

失败时返回：
{{
    "error": "具体的错误原因"
}}"""

            messages = [
                {
                    'role': 'system',
                    'content': '你是一个专业的英语学习助手，擅长分析单词并生成完整的学习资料。你必须返回有效的JSON格式。请仔细验证输入是否为合法的英语单词。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # 使用JSON模式
            content = LLMService._call_deepseek_api(
                messages, 
                response_format={"type": "json_object"}
            )
            
            if not content:
                return {"error": "AI服务暂时不可用，请稍后重试"}
            
            # 解析JSON
            result = json.loads(content)
            
            # 检查是否有错误信息
            if 'error' in result:
                return result
            
            # 验证格式
            if 'definitions' not in result or not isinstance(result['definitions'], list):
                current_app.logger.error(f"DeepSeek返回的JSON格式不正确: {content}")
                return {"error": "AI返回格式错误，请重试"}
            
            # 验证definitions不为空
            if len(result['definitions']) == 0:
                return {"error": "未找到该单词的释义，请检查拼写"}
            
            # 确保每个definition都有必需的字段
            for definition in result['definitions']:
                if not all(key in definition for key in ['part_of_speech', 'meaning', 'example', 'note']):
                    current_app.logger.error(f"Definition缺少必需字段: {definition}")
                    return {"error": "AI返回数据不完整，请重试"}
            
            current_app.logger.info(f"成功生成单词 '{word}' 的完整信息，共 {len(result['definitions'])} 个词性")
            return result
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"解析DeepSeek返回的JSON时出错: {str(e)}, content: {content}")
            return {"error": "AI返回数据解析失败，请重试"}
        except Exception as e:
            current_app.logger.error(f"生成完整单词信息时出错: {str(e)}")
            return {"error": f"生成失败：{str(e)}"}

