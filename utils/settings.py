"""
设置管理工具
"""
from flask import session


def load_settings():
    """加载当前会话设置"""
    return {
        'marked_only': session.get('marked_only', False)
    }


def save_settings(settings):
    """保存当前会话设置"""
    session['marked_only'] = bool(settings.get('marked_only', False))

