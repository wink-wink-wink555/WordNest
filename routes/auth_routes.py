"""用户认证路由"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserApiConfig
from services.list_service import ListService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('word.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            session['current_list'] = ListService.get_default_list(user=user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('word.index'))
        flash('用户名或密码错误', 'error')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('word.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
        elif len(username) < 3 or len(username) > 20:
            flash('用户名长度需在3-20个字符之间', 'error')
        elif len(password) < 6:
            flash('密码长度至少6个字符', 'error')
        elif password != password2:
            flash('两次输入的密码不一致', 'error')
        elif User.query.filter_by(username=username).first():
            flash('用户名已被注册', 'error')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            ListService.ensure_user_default_list(user)
            api_config = UserApiConfig(user=user)
            db.session.add(api_config)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('current_list', None)
    return redirect(url_for('auth.login'))


@auth_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')


@auth_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    config = current_user.api_config
    if not config:
        config = UserApiConfig(user=current_user)
        db.session.add(config)
        db.session.commit()
    return jsonify({
        'api_key': config.api_key or '',
        'api_base_url': config.api_base_url or 'https://api.deepseek.com',
        'model_name': config.model_name or 'deepseek-chat'
    })


@auth_bp.route('/api/settings', methods=['POST'])
@login_required
def save_settings_api():
    data = request.json
    config = current_user.api_config
    if not config:
        config = UserApiConfig(user=current_user)
        db.session.add(config)
    config.api_key = data.get('api_key', '').strip()
    config.api_base_url = data.get('api_base_url', 'https://api.deepseek.com').strip()
    config.model_name = data.get('model_name', 'deepseek-chat').strip()
    db.session.commit()
    return jsonify({'success': True, 'message': '配置已保存'})
