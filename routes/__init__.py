"""路由模块"""

from .word_routes import word_bp
from .graph_routes import graph_bp
from .api_routes import api_bp
from .list_routes import list_bp
from .ai_routes import ai_bp


def register_blueprints(app):
    """注册所有蓝图到应用"""
    app.register_blueprint(word_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(list_bp)
    app.register_blueprint(ai_bp)

