"""
应用配置文件
"""
import os


class Config:
    """基础配置类"""
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'word_list_secret_key'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///words.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Deepseek API配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    
    # Ollama配置
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'qwen2.5:3b'
    
    # 应用配置
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

