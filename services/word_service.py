"""
单词服务层
处理单词相关的业务逻辑
"""
import random
from models import db, Word, Definition
from sqlalchemy import or_


class WordService:
    """单词服务类"""
    
    @staticmethod
    def find_word(word_str):
        """查找指定单词"""
        return Word.query.filter_by(word=word_str).first()
    
    @staticmethod
    def get_all_words():
        """获取所有单词"""
        return Word.query.all()
    
    @staticmethod
    def get_words_with_definitions():
        """获取所有单词及其定义"""
        words = []
        for word in Word.query.all():
            word_dict = word.to_dict()
            # 获取所有定义
            definitions = []
            for definition in Definition.query.filter_by(word_id=word.id).all():
                definitions.append(definition.to_dict())
            word_dict['definitions'] = definitions
            words.append(word_dict)
        return words
    
    @staticmethod
    def get_random_word(prev_word=None, marked_only=False):
        """
        获取随机单词
        
        Args:
            prev_word: 上一个单词，避免重复
            marked_only: 是否只从标注的单词中选择
            
        Returns:
            随机选择的单词对象，如果没有可用单词则返回None
        """
        # 筛选单词
        if marked_only:
            available_words = Word.query.filter_by(marked=True).all()
            if not available_words:
                return None
        else:
            available_words = Word.query.all()
        
        if not available_words:
            return None
        
        # 至少有两个单词时才需要避免重复
        if len(available_words) > 1 and prev_word:
            # 过滤掉上次选中的单词
            filtered_words = [w for w in available_words if w.word != prev_word]
            if not filtered_words and marked_only:
                filtered_words = available_words
            return random.choice(filtered_words) if filtered_words else None
        else:
            return random.choice(available_words)
    
    @staticmethod
    def add_word(word_str, definitions, marked=False):
        """
        添加新单词
        
        Args:
            word_str: 单词文本
            definitions: 定义列表
            marked: 是否标记
            
        Returns:
            添加成功返回True，单词已存在返回False
        """
        # 检查单词是否已存在
        if WordService.find_word(word_str):
            return False
        
        # 确保例句和笔记字段有值
        for definition in definitions:
            if 'example' not in definition or not definition.get('example', '').strip():
                definition['example'] = ""
            if 'note' not in definition or not definition.get('note', '').strip():
                definition['note'] = ""
        
        # 添加新单词
        word = Word.from_dict({
            'word': word_str,
            'definitions': definitions,
            'marked': marked
        })
        
        db.session.add(word)
        db.session.commit()
        return True
    
    @staticmethod
    def update_word(old_word_str, new_word_str, definitions):
        """
        更新单词
        
        Args:
            old_word_str: 原单词文本
            new_word_str: 新单词文本
            definitions: 定义列表
            
        Returns:
            更新成功返回True，单词不存在或新单词已被占用返回False
        """
        word_data = WordService.find_word(old_word_str)
        if not word_data:
            return False
        
        # 如果单词文本发生了变化，检查新单词是否与其他单词冲突
        if old_word_str != new_word_str:
            if WordService.find_word(new_word_str):
                return False
            word_data.word = new_word_str
        
        # 删除现有定义
        for definition in word_data.definitions:
            db.session.delete(definition)
        
        # 添加新定义
        for def_data in definitions:
            definition = Definition(
                part_of_speech=def_data['part_of_speech'],
                meaning=def_data['meaning'],
                example=def_data.get('example', ""),
                note=def_data.get('note', "")
            )
            word_data.definitions.append(definition)
        
        db.session.commit()
        return True
    
    @staticmethod
    def delete_word(word_str):
        """
        删除单词
        
        Args:
            word_str: 单词文本
            
        Returns:
            删除成功返回True，单词不存在返回False
        """
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False
        
        db.session.delete(word_data)
        db.session.commit()
        return True
    
    @staticmethod
    def mark_word(word_str, marked=True):
        """
        标记或取消标记单词
        
        Args:
            word_str: 单词文本
            marked: True标记，False取消标记
            
        Returns:
            操作成功返回True，单词不存在返回False
        """
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False
        
        word_data.marked = marked
        db.session.commit()
        return True
    
    @staticmethod
    def add_definition(word_str, definition_data):
        """
        为单词添加新定义
        
        Args:
            word_str: 单词文本
            definition_data: 定义数据字典
            
        Returns:
            添加成功返回True，单词不存在返回False
        """
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False
        
        definition = Definition(
            part_of_speech=definition_data['part_of_speech'],
            meaning=definition_data['meaning'],
            example=definition_data.get('example', ""),
            note=definition_data.get('note', "")
        )
        
        word_data.definitions.append(definition)
        db.session.commit()
        return True
    
    @staticmethod
    def get_word_details(word_str):
        """
        获取单词详情（包括前后单词）
        
        Args:
            word_str: 单词文本
            
        Returns:
            包含当前单词、前一个单词、后一个单词的字典
        """
        # 获取所有单词并排序
        all_words = [w.word for w in Word.query.order_by(Word.word).all()]
        
        # 检查单词是否存在
        if word_str not in all_words:
            return None
        
        current_index = all_words.index(word_str)
        
        # 确定前一个和后一个单词
        prev_word = all_words[current_index - 1] if current_index > 0 else None
        next_word = all_words[current_index + 1] if current_index < len(all_words) - 1 else None
        
        # 获取当前单词的详情
        word_data = WordService.find_word(word_str)
        
        return {
            'current': word_data.to_dict(),
            'prev': prev_word,
            'next': next_word
        }
    
    @staticmethod
    def get_filtered_words(marked_only=False, sort_alphabetically=False):
        """
        获取筛选和排序后的单词列表
        
        Args:
            marked_only: 是否只显示标注的单词
            sort_alphabetically: 是否按字母排序
            
        Returns:
            单词列表
        """
        words_query = Word.query
        
        # 如果需要只显示标注单词
        if marked_only:
            words_query = words_query.filter_by(marked=True)
        
        # 如果需要按字母排序
        if sort_alphabetically:
            words_query = words_query.order_by(Word.word)
        
        return words_query.all()

