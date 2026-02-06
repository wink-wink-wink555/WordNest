"""
单词列表管理路由
"""
from flask import Blueprint, jsonify, request, session
from services.list_service import ListService


list_bp = Blueprint('list', __name__)


@list_bp.route('/api/lists', methods=['GET'])
def get_lists():
    """获取所有单词列表"""
    try:
        lists = ListService.get_all_lists()
        current_list = session.get('current_list', ListService.get_default_list())
        
        return jsonify({
            'lists': lists,
            'current_list': current_list
        })
    except Exception as e:
        return jsonify({'error': f'获取列表失败: {str(e)}'}), 500


@list_bp.route('/api/lists/current', methods=['GET'])
def get_current_list():
    """获取当前选中的列表"""
    try:
        current_list = session.get('current_list', ListService.get_default_list())
        
        # 检查当前列表是否还存在
        if not ListService.list_exists(current_list):
            current_list = ListService.get_default_list()
            session['current_list'] = current_list
        
        return jsonify({'current_list': current_list})
    except Exception as e:
        return jsonify({'error': f'获取当前列表失败: {str(e)}', 'current_list': 'words'}), 500


@list_bp.route('/api/lists/switch', methods=['POST'])
def switch_list():
    """切换到指定的单词列表"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        list_name = data.get('list_name', '')
        
        if not list_name:
            return jsonify({'error': '列表名称不能为空'}), 400
        
        # 检查列表是否存在
        if not ListService.list_exists(list_name):
            return jsonify({'error': '列表不存在'}), 404
        
        # 切换列表
        session['current_list'] = list_name
        
        return jsonify({
            'success': True,
            'current_list': list_name
        })
    except Exception as e:
        return jsonify({'error': f'切换列表失败: {str(e)}'}), 500


@list_bp.route('/api/lists/create', methods=['POST'])
def create_list():
    """创建新的单词列表"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        list_name = data.get('list_name', '')
        auto_switch = data.get('auto_switch', True)  # 默认自动切换到新列表
        
        if not list_name or list_name.strip() == '':
            return jsonify({'error': '列表名称不能为空'}), 400
        
        # 创建列表
        if not ListService.create_list(list_name):
            return jsonify({'error': '列表已存在或名称无效'}), 400
        
        # 创建成功后，自动切换到新列表
        if auto_switch:
            session['current_list'] = list_name
        
        return jsonify({
            'success': True,
            'list_name': list_name,
            'switched': auto_switch
        })
    except Exception as e:
        return jsonify({'error': f'创建列表失败: {str(e)}'}), 500


@list_bp.route('/api/lists/rename', methods=['POST'])
def rename_list():
    """重命名单词列表"""
    try:
        # 获取JSON数据
        data = request.get_json(force=True, silent=False)
        
        # 打印调试信息
        print(f"收到重命名请求，数据: {data}")
        print(f"请求Content-Type: {request.content_type}")
        
        if not data:
            print("错误：请求数据为空")
            return jsonify({'error': '请求数据为空'}), 400
            
        old_name = data.get('old_name', '')
        new_name = data.get('new_name', '')
        
        print(f"old_name: '{old_name}', new_name: '{new_name}'")
        
        if not old_name or not new_name:
            print("错误：列表名称为空")
            return jsonify({'error': '列表名称不能为空'}), 400
        
        # 重命名列表
        result = ListService.rename_list(old_name, new_name)
        print(f"重命名结果: {result}")
        
        if not result:
            print("错误：重命名失败")
            return jsonify({'error': '重命名失败，可能是列表不存在或新名称已被占用'}), 400
        
        # 如果重命名的是当前列表，更新session
        current_list = session.get('current_list', '')
        if current_list == old_name:
            session['current_list'] = new_name
        
        print("重命名成功")
        return jsonify({
            'success': True,
            'old_name': old_name,
            'new_name': new_name
        })
    except Exception as e:
        print(f"重命名异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'重命名列表失败: {str(e)}'}), 500


@list_bp.route('/api/lists/delete', methods=['POST'])
def delete_list():
    """删除单词列表（只有空列表才能删除）"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        list_name = data.get('list_name', '')
        
        if not list_name:
            return jsonify({'error': '列表名称不能为空'}), 400
        
        # 获取列表中的单词数量
        word_count = ListService.get_word_count_in_list(list_name)
        if word_count > 0:
            return jsonify({'error': f'列表不为空，包含 {word_count} 个单词，无法删除'}), 400
        
        # 删除列表
        if not ListService.delete_list(list_name):
            return jsonify({'error': '删除失败，列表不存在'}), 404
        
        # 如果删除的是当前列表，切换到默认列表
        current_list = session.get('current_list', '')
        if current_list == list_name:
            new_current = ListService.get_default_list()
            session['current_list'] = new_current
            
            return jsonify({
                'success': True,
                'deleted_list': list_name,
                'new_current_list': new_current,
                'switched': True
            })
        
        return jsonify({
            'success': True,
            'deleted_list': list_name,
            'switched': False
        })
    except Exception as e:
        return jsonify({'error': f'删除列表失败: {str(e)}'}), 500

