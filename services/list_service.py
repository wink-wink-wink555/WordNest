"""
单词列表管理服务层
处理用户自己的单词列表
"""
from datetime import datetime

from flask_login import current_user
from sqlalchemy import func

from models import Word, WordList, db


class ListService:
    """单词列表服务类"""

    DEFAULT_LIST_NAME = 'words'

    @staticmethod
    def _resolve_user(user=None):
        resolved_user = user or current_user
        if not resolved_user or not getattr(resolved_user, 'is_authenticated', False):
            return None
        return resolved_user

    @staticmethod
    def sanitize_list_name(list_name):
        """清理并校验列表名称"""
        if not list_name:
            return ''

        cleaned_name = list_name.strip()
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            cleaned_name = cleaned_name.replace(char, '')
        return cleaned_name

    @staticmethod
    def get_list_by_name(list_name, user=None):
        """按名称获取当前用户的列表"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return None

        sanitized_name = ListService.sanitize_list_name(list_name)
        if not sanitized_name:
            return None

        return WordList.query.filter_by(user_id=resolved_user.id, name=sanitized_name).first()

    @staticmethod
    def ensure_user_default_list(user):
        """确保用户至少拥有默认列表"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return None

        default_list = WordList.query.filter_by(
            user_id=resolved_user.id,
            name=ListService.DEFAULT_LIST_NAME,
        ).first()
        if default_list:
            return default_list

        default_list = WordList(
            user_id=resolved_user.id,
            name=ListService.DEFAULT_LIST_NAME,
            created_at=datetime.utcnow(),
        )
        db.session.add(default_list)
        db.session.flush()
        return default_list

    @staticmethod
    def get_all_lists(user=None):
        """获取当前用户的所有单词列表"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return []

        ListService.ensure_user_default_list(resolved_user)
        db.session.flush()

        rows = db.session.query(
            WordList.name,
            func.count(Word.id).label('word_count'),
        ).outerjoin(Word, Word.list_id == WordList.id).filter(
            WordList.user_id == resolved_user.id
        ).group_by(WordList.id).order_by(WordList.name.asc()).all()

        return [
            {
                'name': row.name,
                'word_count': int(row.word_count or 0),
            }
            for row in rows
        ]

    @staticmethod
    def get_word_count_in_list(list_name, user=None):
        """获取当前用户指定列表中的单词数量"""
        word_list = ListService.get_list_by_name(list_name, user=user)
        if not word_list:
            return 0

        return Word.query.filter_by(list_id=word_list.id).count()

    @staticmethod
    def create_list(list_name, user=None):
        """创建新的单词列表"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return False

        sanitized_name = ListService.sanitize_list_name(list_name)
        if not sanitized_name:
            return False

        if ListService.get_list_by_name(sanitized_name, user=resolved_user):
            return False

        db.session.add(WordList(
            user_id=resolved_user.id,
            name=sanitized_name,
            created_at=datetime.utcnow(),
        ))
        db.session.commit()
        return True

    @staticmethod
    def rename_list(old_name, new_name, user=None):
        """重命名单词列表"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return False

        word_list = ListService.get_list_by_name(old_name, user=resolved_user)
        sanitized_new_name = ListService.sanitize_list_name(new_name)

        if not word_list or not sanitized_new_name:
            return False

        if word_list.name == sanitized_new_name:
            return True

        existing = ListService.get_list_by_name(sanitized_new_name, user=resolved_user)
        if existing:
            return False

        word_list.name = sanitized_new_name
        db.session.commit()
        return True

    @staticmethod
    def delete_list(list_name, user=None):
        """删除单词列表（只有空列表才能删除）"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return False

        word_list = ListService.get_list_by_name(list_name, user=resolved_user)
        if not word_list:
            return False

        if Word.query.filter_by(list_id=word_list.id).count() > 0:
            return False

        db.session.delete(word_list)
        db.session.commit()
        return True

    @staticmethod
    def list_exists(list_name, user=None):
        """检查当前用户的列表是否存在"""
        return ListService.get_list_by_name(list_name, user=user) is not None

    @staticmethod
    def get_default_list(user=None):
        """获取当前用户的默认列表名称"""
        resolved_user = ListService._resolve_user(user)
        if not resolved_user:
            return ListService.DEFAULT_LIST_NAME

        default_list = ListService.ensure_user_default_list(resolved_user)
        db.session.commit()
        return default_list.name
