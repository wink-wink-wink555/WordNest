import json
import random
import csv
import os
import pyttsx3
import tempfile
from io import StringIO
from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, session, send_file
import ollama
import requests  # 用于deepseek API调用
from models import db, Word, Definition
app = Flask(__name__)
app.secret_key = 'word_list_secret_key'  # 添加密钥用于session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///words.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Deepseek API配置
DEEPSEEK_API_KEY = "sk-b63b5375c33c442ea93c210a1c20d9ce"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 初始化数据库
db.init_app(app)

# 鼓励性话语列表
ENCOURAGEMENT_MESSAGES = [
    "加油！今天也要元气满满地背单词哦 (ง •̀_•́)ง✧",
    "每天进步一点点，未来感谢现在的自己 ヾ(^▽^*)))",
    "坚持就是胜利！你已经很棒啦 (*•̀ᴗ•́*)و ̑̑",
    "不积跬步，无以至千里，你是最棒的！(๑•̀ㅂ•́)و✧",
    "今天的努力是明天的礼物，继续加油吧 (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "学习如逆水行舟，不进则退，冲鸭！╰(°▽°)╯",
    "知识就是力量，再来一个单词吧 ✿(ˆ◡ˆ)✿",
    "再苦再累，也要坚持，你一定行！(۶•̀ᴗ•́)۶",
    "脚踏实地，持之以恒，终会有所成 ᕙ(⇀‸↼‶)ᕗ",
    "一分耕耘，一分收获，相信自己！(๑˃̵ᴗ˂̵)و"
]

def load_settings():
    """加载系统设置"""
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认设置
        settings = {'marked_only': False}
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return settings

def save_settings(settings):
    """保存系统设置"""
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 如果数据库是空的，但JSON文件存在，则导入数据
        if Word.query.count() == 0 and os.path.exists('words.json'):
            migrate_json_to_db()

def migrate_json_to_db():
    """从JSON文件迁移数据到数据库"""
    with open('words.json', 'r', encoding='utf-8') as f:
        words_data = json.load(f)
        
    for word_data in words_data:
        word = Word.from_dict(word_data)
        db.session.add(word)
    
    db.session.commit()
    print(f"成功导入 {len(words_data)} 个单词到数据库")

def find_word(word_str):
    """查找指定单词"""
    return Word.query.filter_by(word=word_str).first()

# 获取所有单词及其定义的辅助函数
def get_words_with_definitions():
    """获取所有单词及其定义"""
    words = []
    for word in Word.query.all():
        word_dict = word.to_dict()
        # 获取所有定义
        definitions = []
        for definition in Definition.query.filter_by(word_id=word.id).all():
            definitions.append(definition.to_dict())
        word_dict['definitions'] = definitions
        words.append(word_dict)
    return words

@app.route('/')
def index():
    """主页"""
    # 随机选择一条鼓励话语
    encouragement = random.choice(ENCOURAGEMENT_MESSAGES)
    return render_template('index.html', encouragement=encouragement)

@app.route('/get_random_word')
def get_random_word():
    """获取随机单词"""
    # 获取上一次的单词
    prev_word = request.args.get('prev_word', '')
    
    # 加载设置，检查是否只抽查标注单词
    settings = load_settings()
    marked_only = settings.get('marked_only', False)
    
    # 筛选单词
    if marked_only:
        available_words = Word.query.filter_by(marked=True).all()
        if not available_words:
            return jsonify({
                'error': '没有标注的单词',
                'word': 'No marked words'
            })
    else:
        available_words = Word.query.all()
    
    # 至少有两个单词时才需要避免重复
    if len(available_words) > 1 and prev_word:
        # 过滤掉上次选中的单词，确保不会连续抽到同一个单词
        filtered_words = [w for w in available_words if w.word != prev_word]
        # 如果过滤后没有单词（可能在仅标注模式下只有一个标注单词且为上一次的单词）
        if not filtered_words and marked_only:
            filtered_words = available_words
        random_word = random.choice(filtered_words)
    else:
        random_word = random.choice(available_words)
    
    # 返回单词但不返回定义
    return jsonify({
        'word': random_word.word
    })

@app.route('/get_marked_only_status')
def get_marked_only_status():
    """获取是否只抽查标注单词的设置"""
    settings = load_settings()
    return jsonify({'marked_only': settings.get('marked_only', False)})

@app.route('/toggle_marked_only', methods=['POST'])
def toggle_marked_only():
    """切换是否只抽查标注单词的设置"""
    data = request.json
    settings = load_settings()
    settings['marked_only'] = data.get('marked_only', False)
    save_settings(settings)
    return jsonify({'success': True})

@app.route('/get_word_definition/<word>')
def get_word_definition(word):
    """获取指定单词的定义"""
    word_data = find_word(word)
    if word_data:
        return jsonify(word_data.to_dict())
    return jsonify({'error': '未找到该单词'}), 404

@app.route('/is_word_marked/<word>')
def is_word_marked(word):
    """检查单词是否被标记"""
    word_data = find_word(word)
    if word_data:
        return jsonify({'marked': word_data.marked})
    return jsonify({'error': '未找到该单词'}), 404

@app.route('/mark_word/<word>', methods=['POST'])
def mark_word(word):
    """标记单词"""
    word_data = find_word(word)
    if word_data:
        word_data.marked = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': '未找到该单词'}), 404

@app.route('/unmark_word/<word>', methods=['POST'])
def unmark_word(word):
    """取消标记单词"""
    word_data = find_word(word)
    if word_data:
        word_data.marked = False
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': '未找到该单词'}), 404

@app.route('/word_list')
def word_list():
    """单词列表页面"""
    words = get_words_with_definitions()
    return render_template('word_list.html', words=words)

@app.route('/knowledge_graph')
def knowledge_graph():
    # 获取URL参数
    focus_word = request.args.get('word', '')
    
    # 定义默认的关系颜色映射(在所有情况下都需要这个)
    relation_colors = {
        'synonym': '#4CAF50',
        'antonym': '#F44336',
        'related': '#2196F3',
        'topic': '#9C27B0'
    }
    
    # 如果没有提供单词参数，只渲染基础页面
    if not focus_word:
        # 初始化一个空的grouped_relations
        grouped_relations = {
            'synonym': [],
            'antonym': [],
            'related': [],
            'topic': []
        }
        return render_template('knowledge_graph.html', 
                               relation_colors=relation_colors, 
                               grouped_relations=grouped_relations,
                               has_graph_data=False)
    
    # 如果提供了单词参数，获取数据
    try:
        # 使用固定的默认值
        relation_type = 'all'
        depth = 2
        
        print(f"准备为单词 '{focus_word}' 生成知识图谱并渲染页面")
        
        # 获取图谱数据
        graph_data = generate_word_relations_using_deepseek(focus_word, relation_type, depth)
        
        # 打印完整的API响应数据，用于调试
        print("API返回的完整数据结构:")
        print(json.dumps(graph_data, indent=2, ensure_ascii=False))
        
        # 创建节点和边的数据结构(用于vis.js)
        nodes = []
        edges = []
        
        # 添加中心节点
        nodes.append({
            'id': focus_word,
            'label': focus_word,
            'color': '#FF9800',
            'font': {'size': 20, 'color': '#333'},
            'size': 30,
            'marked': False,  # 简化：不检查是否标记
            'isRoot': True,
            'group': 'root'  # 添加分组信息
        })
        
        # 将关系按类型分组，用于简易展示
        grouped_relations = {
            'synonym': [],
            'antonym': [],
            'related': [],
            'topic': []
        }
        
        # 检查API返回格式并处理数据
        if 'relations' in graph_data:
            print(f"处理图谱中的关系数据（旧格式），找到 {len(graph_data['relations'])} 个关系")
            # 旧格式处理方式
            for relation in graph_data['relations']:
                target_word = relation.get('word')
                rel_type = relation.get('type')
                
                if not target_word or target_word == focus_word:
                    continue
                
                # 将关系添加到分组中
                if rel_type in grouped_relations:
                    grouped_relations[rel_type].append(target_word)
                
                # 获取关系类型的颜色
                relation_color = relation_colors.get(rel_type, '#2196F3')
                
                # 添加节点
                nodes.append({
                    'id': target_word,
                    'label': target_word,
                    'color': relation_color,
                    'size': 20,
                    'marked': False,  # 简化：不检查是否标记
                    'group': rel_type  # 添加分组信息用于布局
                })
                
                # 添加边
                edges.append({
                    'from': focus_word,
                    'to': target_word,
                    'label': get_relation_label(rel_type),
                    'color': {
                        'color': relation_color,
                        'highlight': '#FFB74D'
                    },
                    'width': 3,
                    'arrows': {
                        'to': {'enabled': True, 'scaleFactor': 0.5}
                    }
                })
        else:
            # 新格式处理：按类型组织的数据
            print("处理按类型组织的图谱数据")
            
            # 遍历关系类型
            for rel_type, rel_color in relation_colors.items():
                # 如果这个类型在返回数据中存在
                if rel_type in graph_data and isinstance(graph_data[rel_type], list):
                    # 存储关系词到分组中（用于简易视图）
                    grouped_relations[rel_type] = graph_data[rel_type]
                    
                    print(f"处理 {rel_type} 类型的关系，找到 {len(graph_data[rel_type])} 个单词")
                    
                    # 为每个关系词创建节点和边
                    for target_word in graph_data[rel_type]:
                        if not target_word or target_word == focus_word:
                            continue
                            
                        # 添加节点
                        nodes.append({
                            'id': target_word,
                            'label': target_word,
                            'color': rel_color,
                            'size': 20,
                            'marked': False,
                            'group': rel_type
                        })
                        
                        # 添加边
                        edges.append({
                            'from': focus_word,
                            'to': target_word,
                            'label': get_relation_label(rel_type),
                            'color': {
                                'color': rel_color,
                                'highlight': '#FFB74D'
                            },
                            'width': 3,
                            'arrows': {
                                'to': {'enabled': True, 'scaleFactor': 0.5}
                            }
                        })
        
        # 验证节点数据格式
        for i, node in enumerate(nodes):
            if 'id' not in node or not node['id']:
                print(f"警告：第 {i} 个节点缺少id字段")
                node['id'] = f"node_{i}"
            if 'label' not in node:
                node['label'] = node['id']
        
        # 验证边数据格式
        for i, edge in enumerate(edges):
            if 'from' not in edge or not edge['from']:
                print(f"警告：第 {i} 个边缺少from字段")
                continue
            if 'to' not in edge or not edge['to']:
                print(f"警告：第 {i} 个边缺少to字段")
                continue
            
            # 确保引用的节点存在
            from_exists = any(node['id'] == edge['from'] for node in nodes)
            to_exists = any(node['id'] == edge['to'] for node in nodes)
            
            if not from_exists:
                print(f"警告：边 {i} 的源节点 '{edge['from']}' 不存在，将被忽略")
                edge['_invalid'] = True
            if not to_exists:
                print(f"警告：边 {i} 的目标节点 '{edge['to']}' 不存在，将被忽略")
                edge['_invalid'] = True
        
        # 调用调试函数
        debug_graph_data(graph_data, nodes, edges)
        
        # 过滤掉无效边
        edges = [edge for edge in edges if '_invalid' not in edge]
        
        # 打印每个节点和边的详细信息用于调试
        print("\n===== 节点详情 =====")
        for i, node in enumerate(nodes):
            print(f"节点 {i}: id={node.get('id')}, label={node.get('label')}, group={node.get('group')}")
        
        print("\n===== 边详情 =====")
        for i, edge in enumerate(edges):
            print(f"边 {i}: from={edge.get('from')}, to={edge.get('to')}, label={edge.get('label')}")
        
        # 准备图谱数据JSON (用于vis.js)
        graph_data_json = json.dumps({'nodes': nodes, 'edges': edges}, ensure_ascii=False)
        print(f"生成的图谱数据: 节点数={len(nodes)}, 边数={len(edges)}")
        print(f"JSON数据长度: {len(graph_data_json)} 字符")
        print(f"JSON数据前50个字符: {graph_data_json[:50]}...")
        
        # 将图谱数据和请求参数一起传递给模板
        return render_template(
            'knowledge_graph.html', 
            focus_word=focus_word,
            grouped_relations=grouped_relations,
            relation_colors=relation_colors,
            graph_data_json=graph_data_json,
            has_graph_data=True,
            use_simple_view=False  # 默认不使用简单表格视图，而是显示可视化图谱
        )
        
    except Exception as e:
        print(f"生成知识图谱时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        # 出错时也渲染页面，但不包含图谱数据，但需要传递relation_colors
        return render_template('knowledge_graph.html', 
                               error_message=str(e), 
                               relation_colors=relation_colors,
                               grouped_relations={
                                   'synonym': [],
                                   'antonym': [],
                                   'related': [],
                                   'topic': []
                               },
                               has_graph_data=False)

@app.route('/api/graph_data')
def api_graph_data():
    """API接口，返回知识图谱的JSON数据供前端异步加载"""
    try:
        # 获取URL参数
        focus_word = request.args.get('word', '')
        relation_type = request.args.get('type', 'all')
        depth = int(request.args.get('depth', 2))
        
        # 验证参数
        if not focus_word:
            return jsonify({'error': '缺少必要的word参数'}), 400
        
        print(f"API请求知识图谱数据: 单词={focus_word}, 关系类型={relation_type}, 深度={depth}")
        
        # 获取图谱数据
        graph_data = generate_word_relations_using_deepseek(focus_word, relation_type, depth)
        
        # 创建节点和边的数据结构(用于vis.js)
        nodes = []
        edges = []
        
        # 添加中心节点
        nodes.append({
            'id': focus_word,
            'label': focus_word,
            'color': '#FF9800',
            'font': {'size': 20, 'color': '#333'},
            'size': 30,
            'marked': False,  # 简化：不检查是否标记
            'isRoot': True,
            'group': 'root'
        })
        
        relation_colors = {
            'synonym': '#4CAF50',
            'antonym': '#F44336',
            'related': '#2196F3',
            'topic': '#9C27B0'
        }
        
        # 检查API返回格式并处理数据
        if 'relations' in graph_data:
            print(f"API: 处理图谱中的关系数据（旧格式），找到 {len(graph_data['relations'])} 个关系")
            # 旧格式处理方式
            for relation in graph_data['relations']:
                target_word = relation.get('word')
                rel_type = relation.get('type')
                
                if not target_word or target_word == focus_word:
                    continue
                
                # 获取关系类型的颜色
                relation_color = relation_colors.get(rel_type, '#2196F3')
                
                # 添加节点
                nodes.append({
                    'id': target_word,
                    'label': target_word,
                    'color': relation_color,
                    'size': 20,
                    'marked': False,
                    'group': rel_type  # 添加分组信息
                })
                
                # 添加边
                edges.append({
                    'from': focus_word,
                    'to': target_word,
                    'label': get_relation_label(rel_type),
                    'color': {
                        'color': relation_color,
                        'highlight': '#FFB74D'
                    },
                    'width': 3,
                    'arrows': {
                        'to': {'enabled': True, 'scaleFactor': 0.5}
                    }
                })
        else:
            # 新格式处理：按类型组织的数据
            print("API: 处理按类型组织的图谱数据")
            
            # 遍历关系类型
            for rel_type, rel_color in relation_colors.items():
                # 如果这个类型在返回数据中存在
                if rel_type in graph_data and isinstance(graph_data[rel_type], list):
                    print(f"API: 处理 {rel_type} 类型的关系，找到 {len(graph_data[rel_type])} 个单词")
                    
                    # 为每个关系词创建节点和边
                    for target_word in graph_data[rel_type]:
                        if not target_word or target_word == focus_word:
                            continue
                            
                        # 添加节点
                        nodes.append({
                            'id': target_word,
                            'label': target_word,
                            'color': rel_color,
                            'size': 20,
                            'marked': False,
                            'group': rel_type
                        })
                        
                        # 添加边
                        edges.append({
                            'from': focus_word,
                            'to': target_word,
                            'label': get_relation_label(rel_type),
                            'color': {
                                'color': rel_color,
                                'highlight': '#FFB74D'
                            },
                            'width': 3,
                            'arrows': {
                                'to': {'enabled': True, 'scaleFactor': 0.5}
                            }
                        })
        
        # 返回JSON数据
        result = {'nodes': nodes, 'edges': edges}
        print(f"API: 生成的图谱数据: 节点数={len(nodes)}, 边数={len(edges)}")
        
        # 调用调试函数
        debug_graph_data(graph_data, nodes, edges)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API生成知识图谱数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'nodes': [],
            'edges': []
        }), 500

def generate_fallback_graph_data(focus_word, relation_type, depth, words):
    """生成备用的图谱数据，当API调用失败或返回数据不足时使用"""
    # 关系类型和相应的颜色
    relation_types = [
        {'type': 'synonym', 'color': '#4CAF50'},
        {'type': 'antonym', 'color': '#F44336'},
        {'type': 'related', 'color': '#2196F3'},
        {'type': 'topic', 'color': '#9C27B0'}
    ]
    
    # 创建节点和边
    nodes = []
    edges = []
    
    # 添加中心节点
    is_marked = False
    for word in words:
        if word['word'] == focus_word:
            is_marked = word['marked']
            break
    
    nodes.append({
        'id': focus_word,
        'label': focus_word,
        'color': '#FF9800',
        'font': {'size': 20, 'color': '#333'},
        'size': 30,
        'marked': is_marked,
        'isRoot': True
    })
    
    # 为演示目的，创建一些随机关系
    processed_words = set([focus_word])
    all_word_texts = [word['word'] for word in words]
    
    # 添加关联节点和边
    level_words = [focus_word]
    
    for level in range(depth):
        current_level = list(level_words)
        level_words = []
        
        for source_word in current_level:
            # 每个单词选择1-3个关联词
            relation_count = min(len(all_word_texts), random.randint(1, 3))
            related_words = random.sample(all_word_texts, relation_count)
            
            for target_word in related_words:
                if target_word in processed_words or target_word == source_word:
                    continue
                
                # 随机选择关系类型
                relation = random.choice(relation_types)
                
                # 过滤关系类型
                if relation_type != 'all' and relation['type'] != relation_type:
                    continue
                
                processed_words.add(target_word)
                level_words.append(target_word)
                
                # 查找单词是否被标记
                is_target_marked = False
                for word in words:
                    if word['word'] == target_word:
                        is_target_marked = word['marked']
                        break
                
                # 添加节点
                nodes.append({
                    'id': target_word,
                    'label': target_word,
                    'color': relation['color'],
                    'size': 20 - level * 3,  # 层级越深，节点越小
                    'marked': is_target_marked
                })
                
                # 添加边
                edges.append({
                    'from': source_word,
                    'to': target_word,
                    'label': get_relation_label(relation['type']),
                    'color': {
                        'color': relation['color'],
                        'highlight': '#FFB74D'
                    },
                    'width': 3 - level * 0.5,  # 层级越深，边越细
                    'arrows': {
                        'to': {'enabled': True, 'scaleFactor': 0.5}
                    }
                })
    
    return jsonify({'nodes': nodes, 'edges': edges})

def get_relation_label(relation_type):
    """获取关系类型的中文标签"""
    labels = {
        'synonym': '同义',
        'antonym': '反义',
        'related': '相关',
        'topic': '主题'
    }
    return labels.get(relation_type, '')

def debug_graph_data(graph_data, nodes, edges):
    """
    调试图谱数据，确保数据结构正确
    """
    print("\n===== 调试图谱数据 =====")
    print(f"原始图谱数据结构: {type(graph_data)}")
    print(f"图谱数据键: {list(graph_data.keys()) if isinstance(graph_data, dict) else 'Not a dict'}")
    
    # 检查数据格式
    is_old_format = 'relations' in graph_data
    is_new_format = all(key in graph_data for key in ['synonym', 'antonym', 'related', 'topic'])
    
    print(f"是旧格式: {is_old_format}")
    print(f"是新格式: {is_new_format}")
    
    if not is_old_format and not is_new_format:
        print("警告：未识别的数据格式！")
        print(f"数据内容: {json.dumps(graph_data, indent=2, ensure_ascii=False)[:200]}...")
    
    # 检查节点和边
    print(f"生成的节点数: {len(nodes)}")
    print(f"生成的边数: {len(edges)}")
    
    # 检查节点
    node_groups = {}
    for node in nodes:
        group = node.get('group', 'unknown')
        if group not in node_groups:
            node_groups[group] = 0
        node_groups[group] += 1
    
    print("节点分组统计:")
    for group, count in node_groups.items():
        print(f"- {group}: {count}个节点")
    
    # 检查是否有效的图谱
    is_valid = len(nodes) > 0 and len(edges) > 0
    print(f"是否生成了有效图谱: {is_valid}")
    
    return is_valid

def generate_word_relations_using_deepseek(focus_word, relation_type='all', depth=2):
    """
    使用Deepseek API生成单词关系
    
    Args:
        focus_word: 焦点单词
        relation_type: 关系类型 (all, synonym, antonym, related, topic)
        depth: 关系深度
        
    Returns:
        包含节点和边的字典
    """
    print(f"开始为单词 '{focus_word}' 生成知识图谱关系 (类型: {relation_type}, 深度: {depth})")
    
    # 准备API调用的headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # 构建提示词，请求LLM生成词汇关系
    relation_type_desc = "所有类型的关系" if relation_type == 'all' else get_relation_label(relation_type)
    
    prompt = f"""请为英文单词"{focus_word}"生成一个知识图谱，包含与该单词相关的其他单词。

我需要以下{relation_type_desc}，请按类型组织返回结果:

请以JSON格式返回，格式如下:
{{
  "word": "{focus_word}",
  "synonym": ["同义词1", "同义词2", "同义词3"],
  "antonym": ["反义词1", "反义词2", "反义词3"],
  "related": ["相关词1", "相关词2", "相关词3"],
  "topic": ["主题词1", "主题词2", "主题词3"]
}}

请确保只返回JSON格式，不要包含额外解释。为每种类型生成3-5个单词，确保所有单词真实存在。
如果某种类型的关系找不到足够的单词，可以少于3个。"""

    if relation_type != 'all':
        # 如果指定了特定类型，只请求该类型的关系
        prompt += f"\n\n只返回{get_relation_label(relation_type)}类型的关系，其他类型返回空数组。"
    
    # 调用Deepseek API
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        print(f"正在发送请求到 Deepseek API: {DEEPSEEK_BASE_URL}/v1/chat/completions")
        print(f"Headers: Authorization: Bearer {DEEPSEEK_API_KEY[:5]}...{DEEPSEEK_API_KEY[-5:]}")
        print(f"请求数据: {data}")
        
        # 禁用代理以解决连接问题
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions", 
            headers=headers, 
            json=data,
            proxies={"http": None, "https": None}  # 禁用代理
        )
        
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API响应错误: {response.text}")
            raise Exception(f"API请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}")
        
        # 解析API响应
        result = response.json()
        print(f"API返回的JSON: {result}")
        
        content = result['choices'][0]['message']['content']
        print(f"API返回的内容: {content[:200]}...")
        
        # 尝试提取JSON内容
        try:
            # 查找JSON内容的起始和结束位置
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                print(f"提取的JSON内容: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # 如果找不到JSON标记，尝试直接解析整个内容
                print("未找到JSON标记，尝试直接解析整个内容")
                data = json.loads(content)
                
            print(f"解析后的数据: {data}")
            return data
            
        except json.JSONDecodeError as e:
            # 如果解析失败，返回一个基本结构
            print(f"JSON解析错误: {str(e)}")
            print(f"原始内容: {content}")
            print("使用默认备用数据")
            return generate_mock_graph_data(focus_word, relation_type)
            
    except Exception as e:
        print(f"调用Deepseek API出错: {str(e)}")
        # 生成备用数据
        print("由于API调用失败，正在生成备用的知识图谱数据")
        return generate_mock_graph_data(focus_word, relation_type)

def generate_mock_graph_data(focus_word, relation_type='all'):
    """
    当API调用失败时，生成模拟的知识图谱数据
    """
    print(f"为单词'{focus_word}'生成模拟知识图谱数据")
    
    # 为不同单词提供预定义的关系
    common_words = {
        "test": {
            "synonym": ["examination", "assessment", "evaluation", "check", "trial"],
            "antonym": ["guess", "assumption", "speculation", "ignorance"],
            "related": ["exam", "quiz", "experiment", "laboratory", "study"],
            "topic": ["education", "science", "measurement", "verification"]
        },
        "happy": {
            "synonym": ["joyful", "glad", "delighted", "cheerful", "pleased"],
            "antonym": ["sad", "unhappy", "miserable", "depressed", "gloomy"],
            "related": ["smile", "laugh", "joy", "pleasure", "content"],
            "topic": ["emotion", "feeling", "psychology", "mood"]
        },
        "good": {
            "synonym": ["excellent", "fine", "superior", "quality", "worthy"],
            "antonym": ["bad", "poor", "inferior", "substandard", "evil"],
            "related": ["satisfactory", "proper", "suitable", "beneficial", "useful"],
            "topic": ["morality", "ethics", "quality", "standard"]
        }
    }
    
    # 通用的备用关系
    default_relations = {
        "synonym": ["similar", "alike", "comparable"],
        "antonym": ["opposite", "contrary", "different"],
        "related": ["connected", "associated", "linked"],
        "topic": ["category", "field", "domain"]
    }
    
    # 获取单词的关系或使用默认关系
    word_relations = common_words.get(focus_word.lower(), default_relations)
    
    # 创建API响应格式的数据 - 新格式
    mock_data = {
        "word": focus_word,
        "synonym": [],
        "antonym": [],
        "related": [],
        "topic": []
    }
    
    # 根据relation_type添加关系
    relation_types = ["synonym", "antonym", "related", "topic"] if relation_type == 'all' else [relation_type]
    
    for rel_type in relation_types:
        if rel_type in word_relations:
            mock_data[rel_type] = word_relations[rel_type]
    
    print(f"生成的模拟数据: synonym={len(mock_data['synonym'])}, antonym={len(mock_data['antonym'])}, related={len(mock_data['related'])}, topic={len(mock_data['topic'])}个单词")
    return mock_data

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    """添加新单词"""
    if request.method == 'GET':
        return render_template('add_word.html')
    
    # 处理POST请求
    data = request.json
    
    # 检查单词是否为空
    if not data['word'] or data['word'].strip() == '':
        return jsonify({'error': '单词不能为空'}), 400
    
    # 检查单词是否已存在
    existing_word = find_word(data['word'])
    if existing_word:
            return jsonify({'error': '单词已存在'}), 400
    
    # 确保例句和笔记字段有值
    for definition in data['definitions']:
        if 'example' not in definition or not definition['example'].strip():
            definition['example'] = ""
        if 'note' not in definition or not definition['note'].strip():
            definition['note'] = ""
    
    # 添加新单词
    word = Word.from_dict({
        'word': data['word'],
        'definitions': data['definitions'],
        'marked': False
    })
    
    db.session.add(word)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/edit_word/<word>', methods=['GET', 'POST'])
def edit_word(word):
    """编辑单词"""
    if request.method == 'GET':
        word_data = find_word(word)
        if not word_data:
            return redirect(url_for('word_list'))
        return render_template('edit_word.html', word=word_data.to_dict())
    
    # 处理POST请求
    data = request.json
    word_data = find_word(word)
    
    if not word_data:
        return jsonify({'error': '未找到该单词'}), 404
    
    # 更新单词
    if word != data['word']:  # 如果单词文本发生了变化
        # 检查新单词是否与其他单词冲突
        if word != data['word'] and find_word(data['word']):
                        return jsonify({'error': '单词已存在'}), 400
        word_data.word = data['word']
    
    # 删除现有定义
    for definition in word_data.definitions:
        db.session.delete(definition)
    
    # 添加新定义
    for def_data in data['definitions']:
        definition = Definition(
            part_of_speech=def_data['part_of_speech'],
            meaning=def_data['meaning'],
            example=def_data.get('example', ""),
            note=def_data.get('note', "")
        )
        word_data.definitions.append(definition)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/add_definition/<word>', methods=['GET', 'POST'])
def add_definition(word):
    """为单词添加新的定义"""
    if request.method == 'GET':
        word_data = find_word(word)
        if not word_data:
            return redirect(url_for('word_list'))
        return render_template('add_definition.html', word=word_data.to_dict())
    
    # 处理POST请求
    data = request.json
    word_data = find_word(word)
    
    if not word_data:
        return jsonify({'error': '未找到该单词'}), 404
    
    # 添加新定义
    definition = Definition(
        part_of_speech=data['part_of_speech'],
        meaning=data['meaning'],
        example=data.get('example', ""),
        note=data.get('note', "")
    )
    
    word_data.definitions.append(definition)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_word/<word>', methods=['GET', 'POST'])
def delete_word(word):
    """删除单词"""
    word_data = find_word(word)
    
    if not word_data:
        return jsonify({'error': '未找到该单词'}), 404
    
    db.session.delete(word_data)
    db.session.commit()
    
    if request.method == 'GET':
        return redirect(url_for('word_list'))
    return jsonify({'success': True})

@app.route('/export_words')
def export_words():
    """导出单词列表为CSV，支持筛选和排序"""
    # 获取筛选和排序参数
    sort_alphabetically = request.args.get('sort', 'false') == 'true'
    show_marked_only = request.args.get('marked_only', 'false') == 'true'
    
    # 查询单词
    words_query = Word.query
    
    # 如果需要只显示标注单词
    if show_marked_only:
        words_query = words_query.filter_by(marked=True)
    
    # 如果需要按字母排序
    if sort_alphabetically:
        words_query = words_query.order_by(Word.word)
    
    # 获取最终的单词列表
    words = words_query.all()
    
    output = StringIO()
    # 添加BOM标记以确保Excel正确识别UTF-8编码
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['单词', '词性', '释义', '例句', '笔记', '是否标注'])
    
    # 写入单词数据
    for word in words:
        for definition in word.definitions:
            writer.writerow([
                word.word,
                definition.part_of_speech,
                definition.meaning,
                definition.example,
                definition.note,
                '是' if word.marked else '否'
            ])
    
    # 准备响应
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=words.csv"}
    )

@app.route('/generate_example', methods=['POST'])
def generate_example():
    """使用大模型生成例句"""
    data = request.json
    word = data.get('word', '')
    part_of_speech = data.get('part_of_speech', '')
    meaning = data.get('meaning', '')
        
    if not word or not meaning:
        return jsonify({'error': '参数不足'}), 400
    
    try:
        # 使用ollama本地调用大模型
        prompt = f"""
        请为单词 '{word}' ({part_of_speech}) 生成一个自然、简单易懂且地道的英语例句，
        要体现它的含义：'{meaning}'。
        直接输出句子与这句话的中文意思，不要有任何其它解释。"""

        response = ollama.chat(model='qwen2.5:3b', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        example = response['message']['content'].strip()
        
        # 简单清理，去除引号等
        example = example.replace('"', '').replace('"', '').replace('"', '')
        if example.startswith("'") and example.endswith("'"):
            example = example[1:-1]
        
        return jsonify({'example': example})
    except Exception as e:
        print(f"生成例句时出错: {str(e)}")
        return jsonify({'error': f'生成例句失败: {str(e)}'}), 500

@app.route('/generate_note', methods=['POST'])
def generate_note():
    """使用大模型生成笔记"""
    data = request.json
    word = data.get('word', '')
    part_of_speech = data.get('part_of_speech', '')
    meaning = data.get('meaning', '')
        
    if not word or not meaning:
        return jsonify({'error': '参数不足'}), 400
            
    try:
        # 使用ollama本地调用大模型
        prompt = f"""
        请为英语单词 '{word}' ({part_of_speech}) 编写一个简短的学习笔记或记忆技巧，50字以内，包含：
1. 记忆技巧或联想方法
        2. 常见用法提示（如固定搭配等）
3. 易混淆点提醒
        帮助中国学生记住它的含义：'{meaning}'。
        只返回笔记内容，不要有标题或任何其他说明。"""
        response = ollama.chat(model='qwen2.5:3b', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        note = response['message']['content'].strip()
        
        # 简单清理，去除引号等
        note = note.replace('"', '').replace('"', '').replace('"', '')
        if note.startswith("'") and note.endswith("'"):
            note = note[1:-1]
        
        return jsonify({'note': note})
    except Exception as e:
        print(f"生成笔记时出错: {str(e)}")
        return jsonify({'error': f'生成笔记失败: {str(e)}'}), 500

@app.route('/get_word_details/<word>')
def get_word_details(word):
    """获取单词详情（包括前后单词）"""
    # 获取所有单词并排序
    all_words = [w.word for w in Word.query.order_by(Word.word).all()]
    
    # 检查单词是否存在
    if word not in all_words:
        return jsonify({'error': '未找到该单词'}), 404
    
    current_index = all_words.index(word)
    
    # 确定前一个和后一个单词
    prev_word = all_words[current_index - 1] if current_index > 0 else None
    next_word = all_words[current_index + 1] if current_index < len(all_words) - 1 else None
    
    # 获取当前单词的详情
    word_data = find_word(word)
    
    return jsonify({
        'current': word_data.to_dict(),
        'prev': prev_word,
        'next': next_word
    })

@app.route('/test_graph_data')
def test_graph_data():
    """测试路由，直接返回图谱数据JSON用于调试"""
    focus_word = request.args.get('word', 'test')
    relation_type = request.args.get('type', 'all')
    depth = int(request.args.get('depth', 2))
    
    try:
        # 获取原始图谱数据
        graph_data = generate_word_relations_using_deepseek(focus_word, relation_type, depth)
        
        # 创建节点和边的数据
        nodes = []
        edges = []
        
        # 添加中心节点
        nodes.append({
            'id': focus_word,
            'label': focus_word,
            'color': '#FF9800',
            'size': 30,
            'group': 'root'
        })
        
        # 处理关系数据
        relation_colors = {
            'synonym': '#4CAF50',
            'antonym': '#F44336',
            'related': '#2196F3',
            'topic': '#9C27B0'
        }
        
        # 检查数据格式
        is_old_format = 'relations' in graph_data
        is_new_format = all(key in graph_data for key in ['synonym', 'antonym', 'related', 'topic'])
        
        if is_old_format:
            # 旧格式处理方式
            for relation in graph_data['relations']:
                target_word = relation.get('word')
                rel_type = relation.get('type')
                
                if not target_word or target_word == focus_word:
                    continue
                
                # 获取关系类型的颜色
                relation_color = relation_colors.get(rel_type, '#2196F3')
                
                # 添加节点
                nodes.append({
                    'id': target_word,
                    'label': target_word,
                    'color': relation_color,
                    'size': 20,
                    'group': rel_type
                })
                
                # 添加边
                edges.append({
                    'from': focus_word,
                    'to': target_word,
                    'label': get_relation_label(rel_type),
                    'color': relation_color,
                    'width': 2
                })
        elif is_new_format:
            # 新格式处理
            for rel_type, rel_color in relation_colors.items():
                if rel_type in graph_data and isinstance(graph_data[rel_type], list):
                    for target_word in graph_data[rel_type]:
                        if not target_word or target_word == focus_word:
                            continue
                            
                        # 添加节点
                        nodes.append({
                            'id': target_word,
                            'label': target_word,
                            'color': rel_color,
                            'size': 20,
                            'group': rel_type
                        })
                        
                        # 添加边
                        edges.append({
                            'from': focus_word,
                            'to': target_word,
                            'label': get_relation_label(rel_type),
                            'color': rel_color,
                            'width': 2
                        })
        
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
                'relation_types': {k: len(graph_data.get(k, [])) if isinstance(graph_data.get(k), list) else 0 for k in relation_colors.keys()}
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

@app.route('/speak_word/<word>')
def speak_word(word):
    """生成并返回单词语音"""
    try:
        # 初始化文本转语音引擎
        engine = pyttsx3.init()
        
        # 设置语音属性（可选）
        engine.setProperty('rate', 150)  # 语速
        engine.setProperty('volume', 1.0)  # 音量
        
        # 创建临时文件用于保存语音
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # 生成语音文件
        engine.save_to_file(word, temp_filename)
        engine.runAndWait()
        
        # 返回音频文件
        return send_file(
            temp_filename,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"{word}.mp3"
        )
    except Exception as e:
        print(f"生成语音时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 初始化数据库
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True) 