"""
Flask应用主入口
使用应用工厂模式
"""
import os
import sqlite3
from datetime import datetime

from flask import Flask, session
from flask_login import LoginManager, current_user

from config import Config, config
from models import db


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    value = str(value).replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def _sqlite_tables(db_path):
    if not os.path.exists(db_path):
        return set()
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    return {row[0] for row in rows}


def _sqlite_columns(db_path, table_name):
    if not os.path.exists(db_path):
        return set()
    with sqlite3.connect(db_path) as conn:
        try:
            rows = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
        except sqlite3.DatabaseError:
            return set()
    return {row[1] for row in rows}


def _backup_path(path):
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f'{path}.legacy_{timestamp}.bak'


def _collect_legacy_word_data(main_db_path, instance_folder):
    legacy_list_files = []
    for filename in sorted(os.listdir(instance_folder)):
        if not filename.endswith('.db'):
            continue
        db_path = os.path.join(instance_folder, filename)
        if 'word' in _sqlite_tables(db_path) and 'list_id' not in _sqlite_columns(db_path, 'word'):
            legacy_list_files.append(db_path)

    main_tables = _sqlite_tables(main_db_path)
    needs_main_migration = bool(legacy_list_files) and (
        'word_lists' not in main_tables or 'list_id' not in _sqlite_columns(main_db_path, 'word')
    )

    if not needs_main_migration:
        return {
            'needs_migration': False,
            'users': [],
            'api_configs': [],
            'lists': [],
            'legacy_files': [],
        }

    users = []
    api_configs = []
    if os.path.exists(main_db_path):
        with sqlite3.connect(main_db_path) as conn:
            conn.row_factory = sqlite3.Row
            if 'users' in main_tables:
                users = [dict(row) for row in conn.execute(
                    'SELECT id, username, password_hash, created_at FROM users ORDER BY id'
                ).fetchall()]
            if 'user_api_config' in main_tables:
                api_configs = [dict(row) for row in conn.execute(
                    'SELECT id, user_id, api_key, api_base_url, model_name, updated_at '
                    'FROM user_api_config ORDER BY id'
                ).fetchall()]

    lists = []
    for db_path in legacy_list_files:
        list_name = os.path.splitext(os.path.basename(db_path))[0]
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            word_rows = conn.execute(
                'SELECT id, word, marked FROM word ORDER BY id'
            ).fetchall()

            definitions_by_word_id = {}
            if 'definition' in _sqlite_tables(db_path):
                definition_rows = conn.execute(
                    'SELECT word_id, part_of_speech, meaning, example, note FROM definition ORDER BY id'
                ).fetchall()
                for row in definition_rows:
                    definitions_by_word_id.setdefault(row['word_id'], []).append({
                        'part_of_speech': row['part_of_speech'],
                        'meaning': row['meaning'],
                        'example': row['example'] or '',
                        'note': row['note'] or '',
                    })

        words = []
        for row in word_rows:
            words.append({
                'word': row['word'],
                'marked': bool(row['marked']),
                'definitions': definitions_by_word_id.get(row['id'], []),
            })

        lists.append({'name': list_name, 'words': words})

    return {
        'needs_migration': True,
        'users': users,
        'api_configs': api_configs,
        'lists': lists,
        'legacy_files': legacy_list_files,
    }


def _collect_legacy_chat_data(chat_db_path):
    tables = _sqlite_tables(chat_db_path)
    if 'conversations' not in tables:
        return {'needs_migration': False, 'conversations': []}

    conversation_columns = _sqlite_columns(chat_db_path, 'conversations')
    if 'user_id' in conversation_columns:
        return {'needs_migration': False, 'conversations': []}

    with sqlite3.connect(chat_db_path) as conn:
        conn.row_factory = sqlite3.Row
        conversations = []
        conversation_rows = conn.execute(
            'SELECT id, title, created_at, updated_at FROM conversations ORDER BY id'
        ).fetchall()
        for row in conversation_rows:
            messages = [dict(message) for message in conn.execute(
                'SELECT role, content, created_at FROM messages '
                'WHERE conversation_id = ? ORDER BY created_at ASC, id ASC',
                (row['id'],),
            ).fetchall()]
            conversations.append({
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'messages': messages,
            })

    return {'needs_migration': True, 'conversations': conversations}


def _prepare_legacy_migration(app):
    main_db_path = os.path.join(app.config['INSTANCE_FOLDER'], 'words.db')
    chat_db_path = os.path.join(app.config['CHAT_DATA_FOLDER'], 'chat.db')

    word_data = _collect_legacy_word_data(main_db_path, app.config['INSTANCE_FOLDER'])
    chat_data = _collect_legacy_chat_data(chat_db_path)

    if not word_data['needs_migration'] and not chat_data['needs_migration']:
        return

    app.config['_LEGACY_IMPORT_DATA'] = {
        'words': word_data,
        'chat': chat_data,
    }

    if word_data['needs_migration']:
        for legacy_path in word_data['legacy_files']:
            os.rename(legacy_path, _backup_path(legacy_path))

    if chat_data['needs_migration'] and os.path.exists(chat_db_path):
        os.rename(chat_db_path, _backup_path(chat_db_path))


def _import_legacy_data(app):
    legacy_data = app.config.pop('_LEGACY_IMPORT_DATA', None)
    if not legacy_data:
        return

    from chat_models import Conversation, Message
    from models import Definition, User, UserApiConfig, Word, WordList

    word_data = legacy_data['words']
    chat_data = legacy_data['chat']

    if word_data['needs_migration']:
        for user_data in word_data['users']:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                created_at=_parse_datetime(user_data.get('created_at')) or datetime.utcnow(),
            )
            db.session.add(user)

        db.session.flush()

        existing_user_ids = {user.id for user in User.query.all()}

        for api_config_data in word_data['api_configs']:
            if api_config_data['user_id'] not in existing_user_ids:
                continue
            config_record = UserApiConfig(
                id=api_config_data['id'],
                user_id=api_config_data['user_id'],
                api_key=api_config_data.get('api_key') or '',
                api_base_url=api_config_data.get('api_base_url') or 'https://api.deepseek.com',
                model_name=api_config_data.get('model_name') or 'deepseek-chat',
                updated_at=_parse_datetime(api_config_data.get('updated_at')) or datetime.utcnow(),
            )
            db.session.add(config_record)

        db.session.flush()

        all_users = User.query.order_by(User.id).all()
        for user in all_users:
            for legacy_list in word_data['lists']:
                word_list = WordList(
                    user_id=user.id,
                    name=legacy_list['name'],
                    created_at=datetime.utcnow(),
                )
                db.session.add(word_list)
                db.session.flush()

                for word_data_item in legacy_list['words']:
                    word = Word(
                        list_id=word_list.id,
                        word=word_data_item['word'],
                        marked=word_data_item.get('marked', False),
                    )
                    db.session.add(word)
                    db.session.flush()

                    for definition_data in word_data_item.get('definitions', []):
                        db.session.add(Definition(
                            word_id=word.id,
                            part_of_speech=definition_data['part_of_speech'],
                            meaning=definition_data['meaning'],
                            example=definition_data.get('example', ''),
                            note=definition_data.get('note', ''),
                        ))

        db.session.flush()

    from services.list_service import ListService

    for user in User.query.all():
        ListService.ensure_user_default_list(user)
        if not user.api_config:
            db.session.add(UserApiConfig(user=user))

    db.session.commit()

    if chat_data['needs_migration']:
        users = User.query.order_by(User.id).all()
        for user in users:
            for legacy_conversation in chat_data['conversations']:
                conversation = Conversation(
                    user_id=user.id,
                    title=legacy_conversation['title'],
                    created_at=_parse_datetime(legacy_conversation.get('created_at')) or datetime.utcnow(),
                    updated_at=_parse_datetime(legacy_conversation.get('updated_at')) or datetime.utcnow(),
                )
                db.session.add(conversation)
                db.session.flush()

                for message_data in legacy_conversation.get('messages', []):
                    db.session.add(Message(
                        conversation_id=conversation.id,
                        role=message_data['role'],
                        content=message_data['content'],
                        created_at=_parse_datetime(message_data.get('created_at')) or datetime.utcnow(),
                    ))

        db.session.commit()


def create_app(config_name=None):
    """
    应用工厂函数

    Args:
        config_name: 配置名称 ('development', 'production', 'default')

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    instance_folder = app.config.get('INSTANCE_FOLDER', Config.INSTANCE_FOLDER)
    chat_folder = app.config.get('CHAT_DATA_FOLDER', Config.CHAT_DATA_FOLDER)
    os.makedirs(instance_folder, exist_ok=True)
    os.makedirs(chat_folder, exist_ok=True)

    default_db_path = os.path.join(instance_folder, 'words.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{default_db_path}'
    app.config['SQLALCHEMY_BINDS'] = {'chat': config[config_name].get_chat_database_uri()}

    _prepare_legacy_migration(app)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User

        return User.query.get(int(user_id))

    @app.before_request
    def before_request():
        if not current_user.is_authenticated:
            session.pop('current_list', None)
            return

        from services.list_service import ListService

        current_list = session.get('current_list')
        if not current_list or not ListService.list_exists(current_list, user=current_user):
            session['current_list'] = ListService.get_default_list(user=current_user)

    from routes import register_blueprints

    register_blueprints(app)

    with app.app_context():
        from chat_models import Conversation, Message
        from models import User, UserApiConfig, Word, WordList

        db.create_all()
        _import_legacy_data(app)

        from services.list_service import ListService

        for user in User.query.all():
            ListService.ensure_user_default_list(user)
            if not user.api_config:
                db.session.add(UserApiConfig(user=user))

        db.session.commit()

        try:
            default_list = WordList.query.first()
            if default_list and Word.query.count() == 0 and os.path.exists('words.json'):
                migrate_json_to_db(default_list)
        except Exception as e:
            print(f"初始化数据库时出错: {e}")

    return app


def migrate_json_to_db(default_list):
    """从JSON文件迁移数据到数据库"""
    import json
    from models import Word

    with open('words.json', 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    for word_data in words_data:
        word = Word.from_dict(word_data, list_id=default_list.id)
        db.session.add(word)

    db.session.commit()
    print(f"成功导入 {len(words_data)} 个单词到数据库")


app = create_app()


if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode)
