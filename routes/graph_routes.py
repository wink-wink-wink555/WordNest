"""
知识图谱相关路由
"""
import json
from flask import Blueprint, render_template, request, current_app
from services import GraphService
from utils.constants import RELATION_COLORS


graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/knowledge_graph')
def knowledge_graph():
    """知识图谱页面"""
    # 获取URL参数
    focus_word = request.args.get('word', '')
    
    # 如果没有提供单词参数，只渲染基础页面
    if not focus_word:
        grouped_relations = {
            'synonym': [],
            'antonym': [],
            'related': [],
            'topic': []
        }
        return render_template(
            'knowledge_graph.html', 
            relation_colors=RELATION_COLORS, 
            grouped_relations=grouped_relations,
            has_graph_data=False
        )
    
    # 如果提供了单词参数，获取数据
    try:
        # 使用固定的默认值
        relation_type = 'all'
        depth = 2
        
        current_app.logger.info(f"准备为单词 '{focus_word}' 生成知识图谱并渲染页面")
        
        # 获取图谱数据
        graph_data = GraphService.generate_word_relations_using_deepseek(
            focus_word, relation_type, depth
        )
        
        # 创建节点和边的数据结构
        graph_structure = GraphService.build_graph_data(focus_word, graph_data)
        nodes = graph_structure['nodes']
        edges = graph_structure['edges']
        
        # 按类型分组关系
        grouped_relations = GraphService.group_relations_by_type(graph_data)
        
        # 准备图谱数据JSON
        graph_data_json = json.dumps({'nodes': nodes, 'edges': edges}, ensure_ascii=False)
        current_app.logger.info(f"生成的图谱数据: 节点数={len(nodes)}, 边数={len(edges)}")
        
        # 将图谱数据和请求参数一起传递给模板
        return render_template(
            'knowledge_graph.html', 
            focus_word=focus_word,
            grouped_relations=grouped_relations,
            relation_colors=RELATION_COLORS,
            graph_data_json=graph_data_json,
            has_graph_data=True,
            use_simple_view=False
        )
        
    except Exception as e:
        current_app.logger.error(f"生成知识图谱时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 出错时也渲染页面，但不包含图谱数据
        return render_template(
            'knowledge_graph.html', 
            error_message=str(e), 
            relation_colors=RELATION_COLORS,
            grouped_relations={
                'synonym': [],
                'antonym': [],
                'related': [],
                'topic': []
            },
            has_graph_data=False
        )


@graph_bp.route('/test_graph_data')
def test_graph_data():
    """测试路由，直接返回图谱数据JSON用于调试"""
    focus_word = request.args.get('word', 'test')
    relation_type = request.args.get('type', 'all')
    depth = int(request.args.get('depth', 2))
    
    try:
        # 获取原始图谱数据
        graph_data = GraphService.generate_word_relations_using_deepseek(
            focus_word, relation_type, depth
        )
        
        # 创建节点和边的数据
        graph_structure = GraphService.build_graph_data(focus_word, graph_data)
        nodes = graph_structure['nodes']
        edges = graph_structure['edges']
        
        # 检查数据格式
        is_old_format = 'relations' in graph_data
        is_new_format = all(key in graph_data for key in ['synonym', 'antonym', 'related', 'topic'])
        
        # 构造返回数据
        result = {
            'raw_data': graph_data,  # 原始API返回数据
            'graph_data': {
                'nodes': nodes,
                'edges': edges
            },
            'is_old_format': is_old_format,
            'is_new_format': is_new_format,
            'stats': {
                'nodes_count': len(nodes),
                'edges_count': len(edges),
                'relation_types': {
                    k: len(graph_data.get(k, [])) if isinstance(graph_data.get(k), list) else 0 
                    for k in RELATION_COLORS.keys()
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

