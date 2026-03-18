"""
单词服务层
处理当前用户当前词表下的单词逻辑
"""
import random

from flask import session
from flask_login import current_user
from sqlalchemy.orm import joinedload

from models import Definition, Word, db
from services.list_service import ListService


class WordService:
    """单词服务类"""

    @staticmethod
    def _get_current_list():
        if not current_user.is_authenticated:
            return None

        list_name = session.get('current_list')
        word_list = ListService.get_list_by_name(list_name, user=current_user) if list_name else None
        if word_list:
            return word_list

        default_list_name = ListService.get_default_list(user=current_user)
        session['current_list'] = default_list_name
        return ListService.get_list_by_name(default_list_name, user=current_user)

    @staticmethod
    def _base_query():
        word_list = WordService._get_current_list()
        if not word_list:
            return Word.query.filter(False)

        return Word.query.options(joinedload(Word.definitions)).filter_by(list_id=word_list.id)

    @staticmethod
    def find_word(word_str):
        """查找指定单词"""
        return WordService._base_query().filter_by(word=word_str).first()

    @staticmethod
    def get_all_words():
        """获取所有单词"""
        return WordService._base_query().all()

    @staticmethod
    def get_words_with_definitions():
        """获取所有单词及其定义"""
        return [word.to_dict() for word in WordService._base_query().all()]

    @staticmethod
    def get_random_word(prev_word=None, marked_only=False):
        """获取随机单词"""
        query = WordService._base_query()
        if marked_only:
            query = query.filter_by(marked=True)

        available_words = query.all()
        if not available_words:
            return None

        if len(available_words) > 1 and prev_word:
            filtered_words = [word for word in available_words if word.word != prev_word]
            if filtered_words:
                return random.choice(filtered_words)

        return random.choice(available_words)

    @staticmethod
    def add_word(word_str, definitions, marked=False):
        """添加新单词"""
        current_list = WordService._get_current_list()
        if not current_list or WordService.find_word(word_str):
            return False

        normalized_definitions = []
        for definition in definitions:
            normalized_definitions.append({
                'part_of_speech': definition['part_of_speech'],
                'meaning': definition['meaning'],
                'example': definition.get('example', '').strip(),
                'note': definition.get('note', '').strip(),
            })

        word = Word.from_dict({
            'word': word_str,
            'definitions': normalized_definitions,
            'marked': marked,
        }, list_id=current_list.id)

        db.session.add(word)
        db.session.commit()
        return True

    @staticmethod
    def update_word(old_word_str, new_word_str, definitions):
        """更新单词"""
        word_data = WordService.find_word(old_word_str)
        if not word_data:
            return False

        if old_word_str != new_word_str and WordService.find_word(new_word_str):
            return False

        word_data.word = new_word_str

        for definition in list(word_data.definitions):
            db.session.delete(definition)

        for definition_data in definitions:
            word_data.definitions.append(Definition(
                part_of_speech=definition_data['part_of_speech'],
                meaning=definition_data['meaning'],
                example=definition_data.get('example', ''),
                note=definition_data.get('note', ''),
            ))

        db.session.commit()
        return True

    @staticmethod
    def delete_word(word_str):
        """删除单词"""
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False

        db.session.delete(word_data)
        db.session.commit()
        return True

    @staticmethod
    def mark_word(word_str, marked=True):
        """标记或取消标记单词"""
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False

        word_data.marked = marked
        db.session.commit()
        return True

    @staticmethod
    def add_definition(word_str, definition_data):
        """为单词添加新定义"""
        word_data = WordService.find_word(word_str)
        if not word_data:
            return False

        word_data.definitions.append(Definition(
            part_of_speech=definition_data['part_of_speech'],
            meaning=definition_data['meaning'],
            example=definition_data.get('example', ''),
            note=definition_data.get('note', ''),
        ))

        db.session.commit()
        return True

    @staticmethod
    def get_word_details(word_str):
        """获取单词详情（包括前后单词）"""
        all_words = [word.word for word in WordService._base_query().order_by(Word.word).all()]
        if word_str not in all_words:
            return None

        current_index = all_words.index(word_str)
        prev_word = all_words[current_index - 1] if current_index > 0 else None
        next_word = all_words[current_index + 1] if current_index < len(all_words) - 1 else None

        return {
            'current': WordService.find_word(word_str).to_dict(),
            'prev': prev_word,
            'next': next_word,
        }

    @staticmethod
    def get_filtered_words(marked_only=False, sort_alphabetically=False):
        """获取筛选和排序后的单词列表"""
        query = WordService._base_query()

        if marked_only:
            query = query.filter_by(marked=True)
        if sort_alphabetically:
            query = query.order_by(Word.word)

        return query.all()
