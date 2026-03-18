"""服务层模块"""

from .word_service import WordService
from .llm_service import LLMService
from .graph_service import GraphService
from .list_service import ListService

__all__ = [
    'WordService',
    'LLMService',
    'GraphService',
    'ListService'
]


def get_user_api_config():
    """获取当前用户的 API 配置，fallback 到全局配置"""
    from flask import current_app
    from flask_login import current_user
    config = {
        'api_key': current_app.config.get('DEEPSEEK_API_KEY', ''),
        'base_url': current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com').strip(),
        'model_name': 'deepseek-chat'
    }
    try:
        if current_user and current_user.is_authenticated and current_user.api_config:
            uc = current_user.api_config
            if uc.api_key:
                config['api_key'] = uc.api_key
            if uc.api_base_url:
                config['base_url'] = uc.api_base_url.strip()
            if uc.model_name:
                config['model_name'] = uc.model_name
    except Exception:
        pass
    return config

