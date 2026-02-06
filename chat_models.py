"""
聊天记录数据库模型
用于存储AI Tutor的对话历史
"""
from models import db  # 使用相同的db实例
from datetime import datetime


class Conversation(db.Model):
    """对话会话模型"""
    __tablename__ = 'conversations'
    __bind_key__ = 'chat'  # 使用chat数据库
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # 对话标题
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联的消息
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.messages.count()
        }


class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    __bind_key__ = 'chat'  # 使用chat数据库
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
