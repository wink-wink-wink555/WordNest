"""
大语言模型服务层
处理与LLM相关的业务逻辑
"""
import ollama
from flask import current_app


class LLMService:
    """大语言模型服务类"""
    
    @staticmethod
    def generate_example(word, part_of_speech, meaning):
        """
        使用本地大模型生成例句
        
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
            model = current_app.config.get('OLLAMA_MODEL', 'qwen2.5:3b')
            
            prompt = f"""
请为单词 '{word}' ({part_of_speech}) 生成一个自然、简单易懂且地道的英语例句，
要体现它的含义：'{meaning}'。
直接输出句子与这句话的中文意思，不要有任何其它解释。"""

            response = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            example = response['message']['content'].strip()
            
            # 简单清理，去除引号等
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
        使用本地大模型生成学习笔记
        
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
            model = current_app.config.get('OLLAMA_MODEL', 'qwen2.5:3b')
            
            prompt = f"""
请为英语单词 '{word}' ({part_of_speech}) 编写一个简短的学习笔记或记忆技巧，50字以内，包含：
1. 记忆技巧或联想方法
2. 常见用法提示（如固定搭配等）
3. 易混淆点提醒
帮助中国学生记住它的含义：'{meaning}'。
只返回笔记内容，不要有标题或任何其他说明。"""

            response = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            note = response['message']['content'].strip()
            
            # 简单清理，去除引号等
            note = note.replace('"', '').replace('"', '').replace('"', '')
            if note.startswith("'") and note.endswith("'"):
                note = note[1:-1]
            
            return note
        except Exception as e:
            current_app.logger.error(f"生成笔记时出错: {str(e)}")
            return None

