"""
Flask应用主入口
使用应用工厂模式
"""
import os
from flask import Flask
from config import config
from models import db


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 ('development', 'production', 'default')
        
    Returns:
        Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    from routes import register_blueprints
    register_blueprints(app)
    
    # 初始化数据库（在应用上下文中）
    with app.app_context():
        db.create_all()
        
        # 如果数据库是空的，但JSON文件存在，则导入数据
        from models import Word
        if Word.query.count() == 0 and os.path.exists('words.json'):
            migrate_json_to_db()
    
    return app


def migrate_json_to_db():
    """从JSON文件迁移数据到数据库"""
    import json
    from models import Word
    
    with open('words.json', 'r', encoding='utf-8') as f:
        words_data = json.load(f)
        
    for word_data in words_data:
        word = Word.from_dict(word_data)
        db.session.add(word)
    
    db.session.commit()
    print(f"成功导入 {len(words_data)} 个单词到数据库")


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    # 从环境变量获取调试模式设置
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode)
