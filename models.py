from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    api_config = db.relationship(
        'UserApiConfig',
        backref='user',
        uselist=False,
        cascade='all, delete-orphan',
    )
    word_lists = db.relationship(
        'WordList',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan',
    )
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserApiConfig(db.Model):
    """用户 API 配置"""

    __tablename__ = 'user_api_config'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    api_key = db.Column(db.String(256), default='')
    api_base_url = db.Column(db.String(256), default='https://api.deepseek.com')
    model_name = db.Column(db.String(100), default='deepseek-chat')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WordList(db.Model):
    """用户的单词列表"""

    __tablename__ = 'word_lists'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_word_lists_user_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    words = db.relationship(
        'Word',
        backref='word_list',
        lazy=True,
        cascade='all, delete-orphan',
    )


class Word(db.Model):
    """单词模型"""

    __tablename__ = 'word'
    __table_args__ = (
        db.UniqueConstraint('list_id', 'word', name='uq_word_list_word'),
    )

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('word_lists.id'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False)
    marked = db.Column(db.Boolean, default=False)

    definitions = db.relationship(
        'Definition',
        backref='word',
        lazy=True,
        cascade='all, delete-orphan',
    )

    def to_dict(self):
        """将单词转换为字典格式，与原JSON结构兼容"""
        return {
            'word': self.word,
            'marked': self.marked,
            'definitions': [definition.to_dict() for definition in self.definitions],
        }

    @staticmethod
    def from_dict(word_dict, list_id):
        """从字典创建单词对象"""
        word = Word(
            list_id=list_id,
            word=word_dict['word'],
            marked=word_dict.get('marked', False),
        )
        for def_dict in word_dict['definitions']:
            definition = Definition.from_dict(def_dict)
            word.definitions.append(definition)
        return word


class Definition(db.Model):
    """单词定义模型"""

    __tablename__ = 'definition'

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    part_of_speech = db.Column(db.String(20), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text, nullable=True)
    note = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """将定义转换为字典格式，与原JSON结构兼容"""
        return {
            'part_of_speech': self.part_of_speech,
            'meaning': self.meaning,
            'example': self.example or '',
            'note': self.note or '',
        }

    @staticmethod
    def from_dict(definition_dict):
        """从字典创建定义对象"""
        return Definition(
            part_of_speech=definition_dict['part_of_speech'],
            meaning=definition_dict['meaning'],
            example=definition_dict.get('example', ''),
            note=definition_dict.get('note', ''),
        )
