"""
API路由
提供RESTful API接口
"""
from flask import Blueprint, jsonify, request, current_app
from services import GraphService


api_bp = Blueprint('api', __name__)


@api_bp.route('/graph_data')
def graph_data():
    """API接口，返回知识图谱的JSON数据供前端异步加载"""
    try:
        # 获取URL参数
        focus_word = request.args.get('word', '')
        relation_type = request.args.get('type', 'all')
        depth = int(request.args.get('depth', 2))
        
        # 验证参数
        if not focus_word:
            return jsonify({'error': '缺少必要的word参数'}), 400
        
        current_app.logger.info(
            f"API请求知识图谱数据: 单词={focus_word}, 关系类型={relation_type}, 深度={depth}"
        )
        
        # 获取图谱数据
        graph_data = GraphService.generate_word_relations_using_deepseek(
            focus_word, relation_type, depth
        )
        
        # 创建节点和边的数据结构
        graph_structure = GraphService.build_graph_data(focus_word, graph_data)
        nodes = graph_structure['nodes']
        edges = graph_structure['edges']
        
        current_app.logger.info(f"API: 生成的图谱数据: 节点数={len(nodes)}, 边数={len(edges)}")
        
        return jsonify({'nodes': nodes, 'edges': edges})
        
    except Exception as e:
        current_app.logger.error(f"API生成知识图谱数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'nodes': [],
            'edges': []
        }), 500

