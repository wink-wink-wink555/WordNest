"""
Flask应用主入口
使用应用工厂模式
"""
import os
from flask import Flask, session, g
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
    
    # 确保instance文件夹存在
    instance_folder = app.config.get('INSTANCE_FOLDER', os.path.join(os.path.dirname(__file__), 'instance'))
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
    
    # 设置初始数据库 URI（使用默认的 words 列表）
    # 不使用 ListService.get_default_list()，因为此时还没有应用上下文
    default_db_path = os.path.join(instance_folder, 'words.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{default_db_path}'

    # 配置聊天数据库（使用BINDS功能，与单词数据库分开）
    # 重要：必须在 db.init_app(app) 之前设置 BINDS
    chat_db_uri = config[config_name].get_chat_database_uri()
    app.config['SQLALCHEMY_BINDS'] = {'chat': chat_db_uri}
    
    # 初始化单词数据库
    db.init_app(app)
    
    # 添加请求前处理函数，根据session中的当前列表动态切换数据库
    @app.before_request
    def before_request():
        """在每个请求之前，根据当前选中的列表切换数据库"""
        from services.list_service import ListService
        from sqlalchemy import create_engine
        
        # 获取当前列表名称
        current_list = session.get('current_list')
        
        # 如果没有设置当前列表，使用默认列表
        if not current_list:
            current_list = ListService.get_default_list()
            session['current_list'] = current_list
        
        # 检查列表是否存在
        if not ListService.list_exists(current_list):
            current_list = ListService.get_default_list()
            session['current_list'] = current_list
        
        # 动态设置数据库URI
        target_uri = config[config_name].get_database_uri(current_list)
        
        # 检查是否需要切换数据库
        current_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        
        if current_uri != target_uri:
            # 更新配置
            app.config['SQLALCHEMY_DATABASE_URI'] = target_uri
            
            # Flask-SQLAlchemy 3.x: 正确地切换数据库
            try:
                # 移除当前session
                db.session.remove()
                
                # 处理引擎切换 - Flask-SQLAlchemy 3.x 方式
                if hasattr(db, 'engines') and db.engines:
                    # dispose 所有旧引擎
                    for key in list(db.engines.keys()):
                        if db.engines[key]:
                            db.engines[key].dispose()
                    # 清空引擎字典，让 Flask-SQLAlchemy 自动重新创建
                    db.engines.clear()
                
                # 创建新引擎并添加到引擎字典
                # Flask-SQLAlchemy 3.x 使用 None 作为默认数据库的 key
                new_engine = create_engine(
                    target_uri,
                    echo=app.config.get('SQLALCHEMY_ECHO', False),
                    pool_pre_ping=True
                )
                db.engines[None] = new_engine
                
            except Exception as e:
                # 如果切换失败，记录错误
                print(f"数据库切换错误: {e}")
                import traceback
                traceback.print_exc()

    # 注册蓝图
    from routes import register_blueprints
    register_blueprints(app)
    
    # 初始化数据库（在应用上下文中）
    with app.app_context():
        # 导入所有模型（包括chat_models），确保Flask-SQLAlchemy知道所有表
        from models import Word
        from chat_models import Conversation, Message
        
        # 创建所有表（如果不存在）
        # db.create_all()会自动创建所有数据库中的表，包括bind='chat'的表
        db.create_all()
        
        # 如果数据库是空的，但JSON文件存在，则导入数据
        try:
            if Word.query.count() == 0 and os.path.exists('words.json'):
                migrate_json_to_db()
        except Exception as e:
            print(f"初始化数据库时出错: {e}")
            # 如果查询失败，可能是因为引擎还未正确初始化，忽略这个错误
    
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
