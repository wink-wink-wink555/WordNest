"""
知识图谱服务层
处理单词关系图谱相关的业务逻辑
"""
import json
import requests
from flask import current_app
from utils.constants import RELATION_COLORS, RELATION_LABELS


class GraphService:
    """知识图谱服务类"""
    
    @staticmethod
    def get_relation_label(relation_type):
        """获取关系类型的中文标签"""
        return RELATION_LABELS.get(relation_type, '')
    
    @staticmethod
    def generate_word_relations_using_deepseek(focus_word, relation_type='all', depth=2):
        """
        使用Deepseek API生成单词关系
        
        Args:
            focus_word: 焦点单词
            relation_type: 关系类型 (all, synonym, antonym, related, topic)
            depth: 关系深度
            
        Returns:
            包含关系数据的字典
        """
        current_app.logger.info(
            f"开始为单词 '{focus_word}' 生成知识图谱关系 (类型: {relation_type}, 深度: {depth})"
        )
        
        # 准备API调用的headers
        api_key = current_app.config.get('DEEPSEEK_API_KEY')
        base_url = current_app.config.get('DEEPSEEK_BASE_URL')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构建提示词
        relation_type_desc = "所有类型的关系" if relation_type == 'all' else GraphService.get_relation_label(relation_type)
        
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
            prompt += f"\n\n只返回{GraphService.get_relation_label(relation_type)}类型的关系，其他类型返回空数组。"
        
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
            current_app.logger.info(f"正在发送请求到 Deepseek API: {base_url}/v1/chat/completions")
            
            # 禁用代理以解决连接问题
            response = requests.post(
                f"{base_url}/v1/chat/completions", 
                headers=headers, 
                json=data,
                proxies={"http": None, "https": None}
            )
            
            current_app.logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                current_app.logger.error(f"API响应错误: {response.text}")
                raise Exception(f"API请求失败，状态码: {response.status_code}")
            
            # 解析API响应
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 尝试提取JSON内容
            try:
                # 查找JSON内容的起始和结束位置
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    data = json.loads(json_content)
                else:
                    # 如果找不到JSON标记，尝试直接解析整个内容
                    data = json.loads(content)
                
                return data
                
            except json.JSONDecodeError as e:
                # 如果解析失败，返回备用数据
                current_app.logger.error(f"JSON解析错误: {str(e)}")
                return GraphService.generate_mock_graph_data(focus_word, relation_type)
                
        except Exception as e:
            current_app.logger.error(f"调用Deepseek API出错: {str(e)}")
            # 生成备用数据
            return GraphService.generate_mock_graph_data(focus_word, relation_type)
    
    @staticmethod
    def generate_mock_graph_data(focus_word, relation_type='all'):
        """
        当API调用失败时，生成模拟的知识图谱数据
        
        Args:
            focus_word: 焦点单词
            relation_type: 关系类型
            
        Returns:
            模拟的关系数据字典
        """
        current_app.logger.info(f"为单词'{focus_word}'生成模拟知识图谱数据")
        
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
        
        # 创建API响应格式的数据
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
        
        return mock_data
    
    @staticmethod
    def build_graph_data(focus_word, relations_data):
        """
        构建可视化图谱数据结构
        
        Args:
            focus_word: 焦点单词
            relations_data: 关系数据
            
        Returns:
            包含nodes和edges的字典
        """
        nodes = []
        edges = []
        
        # 添加中心节点
        nodes.append({
            'id': focus_word,
            'label': focus_word,
            'color': '#FF9800',
            'font': {'size': 20, 'color': '#333'},
            'size': 30,
            'marked': False,
            'isRoot': True,
            'group': 'root'
        })
        
        # 检查数据格式并处理
        if 'relations' in relations_data:
            # 旧格式处理方式
            for relation in relations_data['relations']:
                target_word = relation.get('word')
                rel_type = relation.get('type')
                
                if not target_word or target_word == focus_word:
                    continue
                
                relation_color = RELATION_COLORS.get(rel_type, '#2196F3')
                
                # 添加节点
                nodes.append({
                    'id': target_word,
                    'label': target_word,
                    'color': relation_color,
                    'size': 20,
                    'marked': False,
                    'group': rel_type
                })
                
                # 添加边
                edges.append({
                    'from': focus_word,
                    'to': target_word,
                    'label': GraphService.get_relation_label(rel_type),
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
            for rel_type, rel_color in RELATION_COLORS.items():
                if rel_type in relations_data and isinstance(relations_data[rel_type], list):
                    for target_word in relations_data[rel_type]:
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
                            'label': GraphService.get_relation_label(rel_type),
                            'color': {
                                'color': rel_color,
                                'highlight': '#FFB74D'
                            },
                            'width': 3,
                            'arrows': {
                                'to': {'enabled': True, 'scaleFactor': 0.5}
                            }
                        })
        
        return {'nodes': nodes, 'edges': edges}
    
    @staticmethod
    def group_relations_by_type(relations_data):
        """
        按类型分组关系数据
        
        Args:
            relations_data: 关系数据
            
        Returns:
            按类型分组的关系字典
        """
        grouped_relations = {
            'synonym': [],
            'antonym': [],
            'related': [],
            'topic': []
        }
        
        if 'relations' in relations_data:
            # 旧格式
            for relation in relations_data['relations']:
                rel_type = relation.get('type')
                target_word = relation.get('word')
                if rel_type in grouped_relations and target_word:
                    grouped_relations[rel_type].append(target_word)
        else:
            # 新格式
            for rel_type in grouped_relations.keys():
                if rel_type in relations_data and isinstance(relations_data[rel_type], list):
                    grouped_relations[rel_type] = relations_data[rel_type]
        
        return grouped_relations

